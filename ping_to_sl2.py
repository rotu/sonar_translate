import math
from pathlib import Path

import construct as c
import numpy as np

from schemas_navico import sl2_frame, SL2_HEADER, sl_file_header, Frequency, ChannelType
from schemas_ping2 import message_id_schema, parse_nmea, parse_nmea_rmc, \
    ping_schema, profile6_schema, get_ranges_db

MM_PER_FOOT = 304.8
SIDESCAN_PACKET_SIZE = 3200


def lat_long_to_northing_easting(latitude_n, longitude_e):
    POLAR_EARTH_RADIUS = 6356752.3142

    # NMEA: lat/long
    # SL2: easting northing
    # conversion as per: https://wiki.openstreetmap.org/wiki/SL2
    temp = latitude_n * math.pi / 180
    temp = math.tan((temp + math.pi / 2) / 2)
    temp = math.log(temp)
    northing = temp * POLAR_EARTH_RADIUS
    easting = longitude_e * math.pi / 180 * \
              POLAR_EARTH_RADIUS
    return northing, easting


def ping_to_sl2(in_path: Path, out_path: Path):
    ping2_packets = c.GreedyRange(ping_schema).parse_file(in_path)

    sl2_data = dict(
        flags={},
        channel_type=ChannelType.SidescanRight,

        frame_offset=0,
        previous_frame_size=0,
        frequency=Frequency.KHz455,

        altitude_ft=0.0,
        course_over_ground_radians=0.0,
        heading_radians=0.0,
        keel_depth_feet=0.0,
        water_depth_feet=0.0,
        water_speed_knots=0.0,
        water_temperature_c=0.0,
        gps_speed_knots=0.0,
        northing=0,
        easting=0,
    )
    first_timestamp_msec = None
    with out_path.open('wb') as out_fd:
        file_header = dict(
            version=2,
            hardware_version=1,
            block_size=3200,  # sometimes 1970 sometimes 3200
        )

        out_fd.write(sl_file_header.build(file_header))
        for pkt in ping2_packets:
            sl2_data['frame_offset'] = out_fd.tell()

            if pkt.message_id.value == message_id_schema.PROFILE6:
                sl2_data['last_frame_offset_right'] = out_fd.tell()

                p6 = profile6_schema.parse(pkt.payload.value)

                if first_timestamp_msec is None:
                    first_timestamp_msec = p6.timestamp_msec
                sl2_data['time_offset'] = p6.timestamp_msec - first_timestamp_msec
                sl2_data['frame_index'] = p6.ping_number
                sl2_data['upper_limit_feet'] = p6.start_mm / MM_PER_FOOT
                sl2_data['lower_limit_feet'] = (p6.start_mm + p6.length_mm) / MM_PER_FOOT
                sl2_data['packet_size'] = SIDESCAN_PACKET_SIZE
                db = get_ranges_db(p6)
                db2 = np.interp(
                    np.linspace(0, 1, 3200),
                    np.linspace(0, 1, len(db)),
                    db
                )
                db3 = (db2 - np.min(db2)) / np.max(db2) * (2 ** 8 - 1)
                # resample sounded data to the expected size
                sl2_data['sounded_data'] = np.round(db3).astype(np.uint8).tolist()
                pass
            elif pkt.message_id.value == message_id_schema.NMEA0183:
                nmea = parse_nmea(pkt.payload.value)
                if nmea.sentence_id == 'RMC':
                    rmc = parse_nmea_rmc(nmea.words)
                    if not rmc.is_status_ok:
                        print(f'ignoring NMEA RMC sentence with status=invalid')
                    sl2_data['heading_radians'] = rmc.track_made_good_degrees_true * math.pi / 180
                    sl2_data['water_speed_knots'] = rmc.speed_over_ground_knots
                    sl2_data['gps_speed_knots'] = rmc.speed_over_ground_knots
                    northing, easting = lat_long_to_northing_easting(
                        rmc.latitude_n, rmc.longitude_e)
                    sl2_data['northing'] = int(round(northing))
                    sl2_data['easting'] = int(round(easting))

                    sl2_data['flags']['PositionValid'] = 1
                    sl2_data['flags']['HeadingValid'] = 1
                    sl2_data['flags']['GPSSpeedValid'] = 1
                else:
                    pass
                    # print (f'ignoring NMEA sentence {nmea.sentence_id}')
            else:
                print(f'ignoring packet with message id {pkt.message_id.value}')

            if sl2_data.get('sounded_data'):
                sl2_data['packet_size'] = len(sl2_data['sounded_data'])
                sl2_data['frame_size'] = sl2_data['packet_size'] + 144
                out_fd.write(sl2_frame.build(sl2_data))
                sl2_data['flags'] = dict()
                sl2_data['previous_frame_size'] = sl2_data['frame_size']
                del sl2_data['sounded_data']


if __name__ == '__main__':
    in_files = list(Path('data').glob('Ping2*.ping_packets'))
    for i, in_path in enumerate(in_files):
        print(f'processing {i + 1}/{len(in_files)}: {in_path}')
        out_path = Path('out', in_path.name + '.sl2')
        out_path.parent.mkdir(exist_ok=True, parents=True)

        ping_to_sl2(in_path, out_path)

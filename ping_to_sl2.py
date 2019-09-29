import math
from pathlib import Path

import construct as c

from schemas_ping2 import message_id_schema, parse_nmea, parse_nmea_rmc, \
    ping_schema, profile6_schema

if __name__ == '__main__':
    # filename = Path('data','noise.ping_packets')
    filename = next(Path('data').glob('Ping2*.ping_packets'))
    b = filename.read_bytes()
    ping2_packets = c.GreedyRange(ping_schema).parse_file(filename)

    sl2_data = dict()
    for pkt in ping2_packets:
        if pkt.message_id.value == message_id_schema.PROFILE6:
            p6 = profile6_schema.parse(pkt.payload.value)
            pass
        elif pkt.message_id.value == message_id_schema.NMEA0183:
            nmea = parse_nmea(pkt.payload.value)
            if nmea.sentence_id == 'RMC':
                rmc = parse_nmea_rmc(nmea.words)
                if not rmc.is_status_ok:
                    print(f'ignoring NMEA RMC sentence with status=invalid')
                #todo: sl2_data['todo'] = rmc.track_made_good_degrees_true
                #todo: sl2_data['todo'] = rmc.speed_over_ground_knots
                # NMEA: lat/long
                # SL2: easting northing
                # conversion as per: https://wiki.openstreetmap.org/wiki/SL2
                POLAR_EARTH_RADIUS = 6356752.3142

                temp = rmc.latitude_n * math.pi / 180
                temp = math.tan((temp + math.pi / 2) / 2)
                temp = math.log(temp)
                sl2_data['northing'] = temp * POLAR_EARTH_RADIUS
                sl2_data['easting'] = rmc.longitude_e * math.pi / 180 * \
                                      POLAR_EARTH_RADIUS
                sl2_data['flags']['GPPSSpeedValid'] = 1
                sl2_data['flags']['PositionValid'] = 1
            else:
                pass
                # print (f'ignoring NMEA sentence {nmea.sentence_id}')

        else:
            print(f'ignoring packet with message id {pkt.message_id.value}')

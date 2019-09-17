import pathlib
from collections import Counter
from typing import Sequence
from datetime import datetime
from typing import Tuple

bdata = pathlib.Path('data.ping_packets').read_bytes()

import struct

from dataclasses import dataclass
import io

MESSAGE_ID_NMEA0183 = 9
MESSAGE_ID_PROFILE6 = 1308


@dataclass
class PingPacketRaw:
    message_id: int
    src_device_id: int
    dest_device_id: int
    payload: bytes


@dataclass
class NMEAPacket:
    talker_id: str
    sentence_id: str
    words: Tuple[str]


def nmea_datetime(datestr, timestr):
    assert timestr[6] == '.'
    return datetime(
        day=int(datestr[0:2]),
        month=int(datestr[2:4]),
        year=(int(datestr[4:6]) - 50) % 100 + 1950,
        hour=int(timestr[0:2]),
        minute=int(timestr[2:4]),
        second=int(timestr[4:6]),
        microsecond=int(timestr[7:9]) * 10000
    )


def parse_ns(ns):
    if ns == 'N':
        return +1
    elif ns == 'S':
        return -1
    raise ValueError()


def parse_ew(ew):
    if ew == 'E':
        return +1
    elif ew == 'W':
        return -1
    raise ValueError()


@dataclass
class NMEASentenceRMC:
    timestamp: datetime = None
    status_ok: bool = False
    latitude_n: float = 0.0
    longitude_e: float = 0.0
    speed_over_ground_knots: float = 0.0
    track_made_good_degrees_true: float = 0.0
    magnetic_variation_degrees_e: float = 0.0


def parse_nmea_rmc(words: Sequence[str]):
    assert words[1] in ('A', 'V')
    return NMEASentenceRMC(
        timestamp=nmea_datetime(datestr=words[8],
            timestr=words[0]),
        status_ok=(words[1] == 'A'),
        latitude_n=float(words[2]) * parse_ns(words[3]),
        longitude_e=float(words[4]) * parse_ew(words[5]),
        speed_over_ground_knots=float(words[6]),
        track_made_good_degrees_true=(
            None if words[7] == '' else float(words[7])),
        magnetic_variation_degrees_e=(
            None if words[9] == '' else (float(words[9]) * parse_ew(words[
                10]))),
    )


def parse_nmea(payload: bytes):
    payload_str = payload.decode('ascii')
    assert payload_str.startswith('$')
    assert payload_str.endswith('\r\n')
    assert payload_str[6] == ','

    return NMEAPacket(
        payload_str[1:3],
        payload_str[3:6],
        tuple(payload_str[7:-2].split(','))
    )


class Profile6Packet:
    ping_number: int
    start_mm: int
    length_mm: int
    start_ping_hz: int
    end_ping_hz: int
    adc_sample_hz: int
    timestep_ms: int
    ping_duration_s: float
    analog_gain: float
    max_power: float
    min_power: float
    step_db: float
    is_db: bool
    gain_index: int
    decimation: int
    num_results: int
    scaled_db_pwr_results: list[int]


def parse_profile6(payload: bytes):
    pass


BLOCK_SIZE = 'b207'  # ???
SL2_HEADER = bytes.fromhex('020000' + BLOCK_SIZE + '00000800')


class SL2BlockHeader:
    def __init__(self):
        this_frame_byte_offset = 0
        last_frame_byte_offset = 0
        blockSize = 0
        lastBlockSize = 0
        channel = 0
        packetSize = 0
        frameIndex = 0
        upperlimit_feet = 0.0
        lowerlimit_feet = 0.0
        frequency = 0
        time1 = 0
        waterdepth_feet = 0.0
        speed_knots = 0
        water_temperature_c = 0.0
        easting = 0
        northing = 0
        waterspeed_knots = 0.0
        course_over_ground_radians = 0.0
        altitude_ft = 0.0
        heading_radians = 0.0
        validity_bitmask = 0
        timeoffset = 0
        packetsize = 0



@dataclass
class PingPacketProfile6:
    pass


def ping_seek(b: bytes):
    return b.find(b'BR')


def ping_unpack_from(b: io.BytesIO):
    prelude_fmt = '2sHHBB'
    prelude_bytes = b.read(8)
    start, payload_len, message_id, src_device_id, dest_device_id = \
        struct.unpack(prelude_fmt, prelude_bytes)
    assert start == b'BR'
    payload_bytes = b.read(payload_len)
    checksum, = struct.unpack('H', b.read(2))
    expected_checksum = sum(prelude_bytes + payload_bytes) % 2 ** 16
    assert checksum == expected_checksum
    return PingPacketRaw(message_id=message_id, src_device_id=src_device_id,
        dest_device_id=dest_device_id, payload=payload_bytes)


if __name__ == '__main__':
    packets = []
    with pathlib.Path('data.ping_packets').open('rb') as f:
        while f.peek():
            try:
                packets.append(ping_unpack_from(f))
            except Exception as e:
                print("bad packet")
    talkers = Counter()
    sentences = Counter()
    talkersentences = Counter()
    for pkt in packets:
        if pkt.message_id == MESSAGE_ID_NMEA0183:
            nmea = parse_nmea(pkt.payload)
            talkers[nmea.talker_id] += 1
            sentences[nmea.sentence_id] += 1
            talkersentences[nmea.talker_id + nmea.sentence_id] += 1

            if nmea.sentence_id == 'RMC':
                print(parse_nmea_rmc(nmea.words))
        elif pkt.message_id == MESSAGE_ID_PROFILE6:
            pass
        else:
            print(f'skipping message id {pkt.message_id}')

    print(f'nmea talkers: {talkers}')
    print(f'nmea sentences: {sentences}')
    print(f'talker sentences: {talkersentences}')

    # nmea talkers: Counter({'GN': 13, 'GP': 9, 'GL': 6})
    # nmea sentences: Counter({'GSV': 15, 'GSA': 5, 'GLL': 2, 'RMC': 2, 'VTG': 2, 'GGA': 2})
    # GGA = Global Positioning System Fix Data. Time, Position and fix
    #       related data for a GPS receiver
    # GLL = Geographic Position – Latitude/Longitude
    #       useful!
    # GSV:  Satellites in view - don't care
    # RMC = Recommended Minimum Navigation Information
    #       useful!
    # GSA = GPS DOP and active satellites
    # VTG = Track Made Good and Ground Speed
    #       useful!

    # probably only need rmc

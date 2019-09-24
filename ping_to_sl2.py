import pathlib
from collections import Counter
from types import SimpleNamespace
from typing import Sequence
from datetime import datetime
from typing import Tuple

from nmea0183 import parse_nmea, parse_nmea_rmc

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


def ping_seek(b: bytes):
    return b.find(b'BR')


def ping_unpack_from(b: io.BytesIO):
    prelude_fmt = '2sHHBB'
    prelude_bytes = b.read(8)
    start, payload_len, message_id, src_device_id, dest_device_id = struct.unpack(
        prelude_fmt, prelude_bytes
    )
    assert start == b'BR'
    payload_bytes = b.read(payload_len)
    checksum, = struct.unpack('H', b.read(2))
    expected_checksum = sum(prelude_bytes + payload_bytes) % 2 ** 16
    assert checksum == expected_checksum
    return PingPacketRaw(
        message_id=message_id,
        src_device_id=src_device_id,
        dest_device_id=dest_device_id,
        payload=payload_bytes,
    )


def from_construct(a_construct):
    if isinstance(a_construct, c.ListContainer):
        return list(from_construct(i) for i in a_construct)
    if isinstance(a_construct, c.Container):
        if set(a_construct.keys()) == {
            'data', 'value', 'offset1', 'offset2', 'length'
        }:
            return from_construct(a_construct.value)
        return SimpleNamespace(**{
            k: from_construct(v) for k, v in a_construct.items() if k != '_io'
        })
    else:
        return a_construct


import construct as c
import dan_ping

if __name__ == '__main__':
    parsed = c.GreedyRange(dan_ping.ping_schema).parse_file(
        'data.ping_packets')

    ping_packets = from_construct(parsed)
    talkers = Counter()
    sentences = Counter()
    talkersentences = Counter()
    for pkt in ping_packets:
        if pkt.message_id == MESSAGE_ID_NMEA0183:
            nmea = parse_nmea(pkt.payload)
            talkers[nmea.talker_id] += 1
            sentences[nmea.sentence_id] += 1
            talkersentences[nmea.talker_id + nmea.sentence_id] += 1

            if nmea.sentence_id == 'RMC':
                print(parse_nmea_rmc(nmea.words))
        elif pkt.message_id == MESSAGE_ID_PROFILE6:
            p6 = from_construct(dan_ping.profile6_schema.parse(
                pkt.payload
            ))
            print('n_pings', len(p6.scaled_db_pwr_results))
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

# important stuff = position of boat
# Do I need to interpolate GPS? For now, no.
#


import warnings
import re

import construct as c

message_id_schema = c.Enum(
    c.Int16ul,
    NMEA0183=9,
    PROFILE6=1308,
)

ping_schema = c.Struct(
    start=c.RawCopy(c.Const(b'BR')),
    payload_length=c.RawCopy(c.Int16ul),
    message_id=c.RawCopy(message_id_schema),
    src_device_id=c.RawCopy(c.Int8ul),
    dest_device_id=c.RawCopy(c.Int8ul),
    payload=c.RawCopy(c.Bytes(c.this.payload_length.value)),
    checksum=c.Checksum(c.Int16ul, lambda b: sum(b) % (1 << 16),
        lambda cxt: b''.join(
            cxt[attr].data for attr in [
                'start', 'payload_length', 'message_id', 'src_device_id',
                'dest_device_id', 'payload'])
    ),
)

profile6_schema = c.Struct(
    ping_number=c.Int32ul,
    start_mm=c.Int32ul,
    length_mm=c.Int32ul,
    start_ping_hz=c.Int32ul,
    end_ping_hz=c.Int32ul,
    adc_sample_hz=c.Int32ul,
    timestamp_msec=c.Int32ul,
    spare2=c.Padding(4),
    ping_duration_sec=c.Float32l,
    analog_gain=c.Float32l,
    max_pwr=c.Float32l,
    min_pwr=c.Float32l,
    step_db=c.Float32l,
    padding_2=c.Padding(8),
    is_db=c.Int8ul,
    gain_index=c.Int8ul,
    decimation=c.Int8ul,
    padding_3=c.Padding(1),
    num_results=c.Int16ul,
    scaled_db_pwr_results=c.Array(c.this.num_results, c.Int16ul)
)

from typing import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class NMEAPacket:
    talker_id: str
    sentence_id: str
    words: Sequence[str]


def parse_nmea_datetime(datestr, timestr):
    assert timestr[6] == '.'
    return datetime(
        day=int(datestr[0:2]),
        month=int(datestr[2:4]),
        year=(int(datestr[4:6]) - 50) % 100 + 1950,
        hour=int(timestr[0:2]),
        minute=int(timestr[2:4]),
        second=int(timestr[4:6]),
        microsecond=int(timestr[7:9]) * 10000,
    )


def parse_nmea_degrees(degrees_str):
    degrees, minutes = re.match('(\d.*)(\d{2}\.\d+)',
        degrees_str).groups()
    return int(degrees) + float(minutes) / 60


def parse_latitude(degrees_str, ns_str):
    if degrees_str == '':
        return None
    return parse_nmea_degrees(degrees_str) * {'N': +1, 'S': -1}[ns_str]


def parse_longitude(degrees_str, ew_str):
    if degrees_str == '':
        return None
    return parse_nmea_degrees(degrees_str) * {'E': +1, 'W': -1}[ew_str]


@dataclass
class NMEASentenceRMC:
    timestamp: datetime = None
    is_status_ok: bool = False
    latitude_n: float = 0.0
    longitude_e: float = 0.0
    speed_over_ground_knots: float = 0.0
    track_made_good_degrees_true: float = 0.0
    magnetic_variation_degrees_e: Optional[float] = None


def parse_nmea_rmc(words: Sequence[str]):
    return NMEASentenceRMC(
        timestamp=parse_nmea_datetime(datestr=words[8], timestr=words[0]),
        is_status_ok={'A': True, 'V': False}[words[1]],
        latitude_n=parse_latitude(words[2], words[3]),
        longitude_e=parse_longitude(words[4], words[5]),
        speed_over_ground_knots=float(words[6]),
        track_made_good_degrees_true=(
            None if words[7] == '' else float(words[7])),
        magnetic_variation_degrees_e=parse_longitude(words[9], words[10]),
    )


def parse_nmea(payload: bytes):
    payload_str = payload.decode('ascii')
    assert payload_str.startswith('$')
    if not (payload_str.endswith('\r\n')):
        warnings.warn(
            f'NMEA0183 string {payload_str!r} did not end with \\r\\n')
    assert payload_str[6] == ','

    return NMEAPacket(
        talker_id=payload_str[1:3],
        sentence_id=payload_str[3:6],
        words=tuple(payload_str[7:].rstrip('\r\n').split(','))
    )

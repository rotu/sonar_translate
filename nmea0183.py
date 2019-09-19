from typing import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import dan_ping


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


def parse_latitude(degrees_str, ns_str):
    if degrees_str == '':
        return None
    return float(degrees_str) * {'N': +1, 'S': -1}[ns_str]


def parse_longitude(degrees_str, ew_str):
    if degrees_str == '':
        return None
    return float(degrees_str) * {'E': +1, 'W': -1}[ew_str]


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
        track_made_good_degrees_true=(None if words[7] == '' else float(words[7])),
        magnetic_variation_degrees_e=parse_longitude(words[9], words[10]),
    )


def parse_nmea(payload: bytes):
    payload_str = payload.decode('ascii')
    assert payload_str.startswith('$')
    assert payload_str.endswith('\r\n')
    assert payload_str[6] == ','

    return NMEAPacket(payload_str[1:3], payload_str[3:6], tuple(payload_str[7:-2].split(',')))

import struct
from array import array
from dataclasses import dataclass
from typing import Sequence
import sys
import brping


# important stuff = position of boat
# Do I need to interpolate GPS? For now, no.
#


class SerializationFormat:
    pass


@dataclass
class Profile6Packet:
    ping_number: int
    # distance you're looking
    start_mm: int
    length_mm: int
    # details of signals we're sending
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
    scaled_db_pwr_results: Sequence[int]

    def get_pwr_results(self):
        result = [
            self.min_power + (self.max_power - self.min_power) * i / (1 << 16 - 1)
            for i in self.scaled_db_pwr_results
        ]

    @classmethod
    def from_bytes(cls, b: bytes):
        fmt_profile6 = struct.Struct('<7I4x5f8x3BxHH')
        results = array('H', b[fmt_profile6.size :])
        if sys.byteorder == 'big':
            results.byteswap()
        *args, num_results = fmt_profile6.unpack_from(b)
        assert num_results == len(results)
        return cls(*args, scaled_db_pwr_results=results)

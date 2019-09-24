import functools
import struct
from array import array
from dataclasses import dataclass
from typing import Sequence
import sys
import construct
import brping

# important stuff = position of boat
# Do I need to interpolate GPS? For now, no.
#

import construct as c

ping_schema = c.Struct(
    start=c.RawCopy(c.Const(b'BR')),
    payload_length=c.RawCopy(c.Int16ul),
    message_id=c.RawCopy(c.Int16ul),
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
    scaled_db_pwr_results=c.PrefixedArray(c.Int16ul, c.Int16ul),
)

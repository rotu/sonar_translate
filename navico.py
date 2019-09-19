import enum
import struct
from dataclasses import dataclass


@dataclass
class FileHeader:
    version: int
    hardware_version: int
    block_size: int

    def to_bytes(self):
        fmt_header = struct.Struct('<3H')
        buffer = bytearray(self.blocksize)
        fmt_header.pack_into(buffer, 0, self.version, self.hardware_version, self.block_size)
        return buffer


SL2_HEADER = FileHeader(version=2, hardware_version=1, block_size=1970)


class ValidityFlag(enum.IntFlag):
    Track = 0
    Position = 1 << 3
    CourseOrSpeed = 1 << 5
    Speed = 1 << 6
    AltitudeOrCourseOrSpeed = 1 << 9
    Altitude = 1 << 14
    Heading = 1 << 15


@dataclass
class SL2FrameHeader:
    frame_offset = 0
    last_frame_offset_primary = 0
    last_frame_offset_secondary = 0
    last_frame_offset_down_scan = 0
    last_frame_offset_left = 0
    last_frame_offset_right = 0
    last_frame_offset_composite = 0

    frame_size = 0
    previous_frame_size = 0
    channel_type = 0
    packet_size = 0
    frame_index = 0
    upper_limit_feet = 0.0
    lower_limit_feet = 0.0
    frequency = 0

    time1 = 0
    water_depth_feet = 0.0
    keel_depth_feet = 0.0

    speed_knots = 0.0
    water_temperature_c = 0.0
    longitude = 0
    latitude = 0
    water_speed_knots = 0.0
    course_over_ground_radians = 0.0
    altitude_ft = 0.0
    heading_radians = 0.0

    validity_flags: ValidityFlag = ValidityFlag(0)
    time_offset = 0
    sounded_data = []

    def __init__(self):
        pass

    def to_bytes(self, frame_size: int):
        buffer = bytearray(frame_size)
        struct.pack_into(
            '<7I<4H<I<2fB',
            buffer,
            0,
            self.frame_offset,
            self.last_frame_offset_primary,
            self.last_frame_offset_secondary,
            self.last_frame_offset_down_scan,
            self.last_frame_offset_left,
            self.last_frame_offset_right,
            self.last_frame_offset_composite,
            self.frame_size,
            self.previous_frame_size,
            self.channel_type,
            self.packet_size,
            self.frame_index,
            self.upper_limit_feet,
            self.lower_limit_feet,
            self.frequency,
        )
        struct.pack_into(
            '<Iff', buffer, 60, self.time1, self.water_depth_feet, self.keel_depth_feet
        )
        struct.pack_into(
            '2f2I4fH',
            buffer,
            100,
            self.speed_knots,
            self.water_temperature_c,
            self.longitude,
            self.latitude,
            self.water_speed_knots,
            self.course_over_ground_radians,
            self.altitude_ft,
            self.heading_radians,
            int(self.validity_flags),
        )
        struct.pack_into('I', buffer, 140, self.time_offset)
        for i, depth_ft in enumerate(self.sounded_data):
            if depth_ft < self.lower_limit_feet:
                b = 0
            elif depth_ft > self.upper_limit_feet:
                b = 255
            else:
                b = round(
                    255
                    * (depth_ft - self.lower_limit_feet)
                    / (self.upper_limit_feet - self.lower_limit_feet)
                )
            buffer[144 + i] = b
        return buffer

import construct as c

sl_file_header = c.Struct(
    version=c.Enum(c.Int16ul, slg=1, sl2=2, sl3=3),
    hardware_version=c.Int16ul,
    block_size=c.Int16ul,
    p_=c.Padding(2)
)

SL2_HEADER = dict(
    version=2,
    hardware_version=1,
    block_size=3200,  # sometimes 1970 sometimes 3200
)

SL3_HEADER = dict(
    version=3,
    hardware_version=1,
    block_size=3200,
)

ValidFlags = c.FlagsEnum(
    c.Int16ul,
    GPSSpeedValid=1 << 1,
    WaterTemperatureValid=1 << 2,
    PositionValid=1 << 4,
    WaterSpeedValid=1 << 6,
    TrackValid=1 << 7,
    HeadingValid=1 << 8,
    AltitudeValid=1 << 9,
    **{f'Flag{i}': 1 << i for i in (0, 3, 5, 10, 11, 12, 13, 14, 15)}
)

ChannelType = c.Enum(
    c.Int16ul, Primary=0, Secondary=1, DownScan=2,
    Unknown1=3, Unknown2=4, SidescanComposite=5, SidescanStarboard=13, SidescanPort=14)

Frequency = c.Enum(
    c.Int8ul, KHz200=0, KHz50=1, KHz83=2, KHz455=3, KHz800=4,
    Khz38=5, KHz28=6, Khz130Khz210=7, Khz90Khz150=8, KHz40Khz60=9,
    KHz25KHz45=10)

sl2_frame = c.Struct(
    # 0
    frame_offset=c.Int32ul,
    last_frame_offset_primary=c.Default(c.Int32ul, 0),
    last_frame_offset_secondary=c.Default(c.Int32ul, 0),
    last_frame_offset_down_scan=c.Default(c.Int32ul, 0),
    last_frame_offset_left=c.Default(c.Int32ul, 0),
    last_frame_offset_right=c.Default(c.Int32ul, 0),
    last_frame_offset_composite=c.Default(c.Int32ul, 0),
    # 28
    frame_size=c.Int16ul,
    previous_frame_size=c.Int16ul,
    channel_type=ChannelType,
    packet_size=c.Int16ul,
    # 36
    frame_index=c.Int32ul,
    upper_limit_feet=c.Float32l,
    lower_limit_feet=c.Float32l,
    # 48
    _pad48=c.Padding(53 - 48),
    frequency=Frequency,
    _pad51=c.Padding(60 - 54),
    # 60
    creation_date_time=c.Default(c.Int32sl, -1),
    water_depth_feet=c.Float32l,
    keel_depth_feet=c.Float32l,
    # 68
    _pad2=c.Padding(100 - 72),
    # 100
    gps_speed_knots=c.Float32l,
    water_temperature_c=c.Float32l,
    easting=c.Int32sl,
    northing=c.Int32sl,
    water_speed_knots=c.Float32l,
    course_over_ground_radians=c.Float32l,
    altitude_ft=c.Float32l,
    heading_radians=c.Float32l,
    # 132
    flags=ValidFlags,
    # 134
    _pad3=c.Padding(140 - 134),
    # 140
    time_offset=c.Int32ul,
    sounded_data=c.Array(count=c.this.packet_size, subcon=c.Int8ul)
)

sl3_frame = c.Struct(
    # 0
    frame_offset=c.Int32ul,
    # 4
    _pad4=c.Padding(4),
    # 8
    frame_size=c.Rebuild(c.Int16ul, c.this.packet_size + 168),
    previous_frame_size=c.Int16ul,
    channel_type=ChannelType,
    # 14
    _pad14=c.Padding(2),
    # 16
    frame_index=c.Int32ul,
    upper_limit_feet=c.Float32l,
    lower_limit_feet=c.Float32l,
    # 28
    _pad28=c.Padding(40 - 28),
    # 40
    creation_date_time=c.Default(c.Int32sl, -1),
    packet_size=c.Int16ul,
    # 44
    _pad46=c.Padding(2),

    water_depth_feet=c.Float32l,
    frequency=Frequency,

    _pad53=c.Padding(80 - 53),

    gps_speed_knots=c.Float32l,
    water_temperature_c=c.Float32l,
    easting=c.Int32sl,
    northing=c.Int32sl,

    _pad100=c.Padding(4),

    track_radians=c.Float32l,
    altitude_ft=c.Float32l,
    heading_radians=c.Float32l,
    flags=ValidFlags,

    _pad116=c.Padding(122 - 116),

    time_offset=c.Int32ul,
    last_frame_offset_primary=c.Default(c.Int32ul, 0),
    last_frame_offset_secondary=c.Default(c.Int32ul, 0),
    last_frame_offset_down_scan=c.Default(c.Int32ul, 0),
    last_frame_offset_left=c.Default(c.Int32ul, 0),
    last_frame_offset_right=c.Default(c.Int32ul, 0),
    last_frame_offset_composite=c.Default(c.Int32ul, 0),

    _pad152=c.Padding(164 - 152),

    last_3d_scan_channel=c.Default(c.Int32ul, 0),
    sounded_data=c.Array(c.this.packet_size, c.Int8ul)
)

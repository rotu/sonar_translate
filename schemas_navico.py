import construct as c

sl_file_header = c.Struct(
    version=c.Enum(c.Int16ul, slg=1, sl2=2, sl3=3),
    hardware_version=c.Int16ul,
    block_size=c.Int16ul,
    p_=c.Padding(1)
)

SL2_HEADER = sl_file_header.build(dict(
    version=2,
    hardware_version=1,
    block_size=3200,  # sometimes 1970 sometimes 3200
))

SL3_HEADER = sl_file_header.build(dict(
    version=3,
    hardware_version=1,
    block_size=3200,
))
test = c.Struct(
    a=c.Int8ul,
    b=c.Padding(4),
    c=c.Int8ul
)

sl2_frame = c.Struct(
    # 0
    frame_offset=c.Int32ul,
    last_frame_offset_primary=c.Int32ul,
    last_frame_offset_secondary=c.Int32ul,
    last_frame_offset_down_scan=c.Int32ul,
    last_frame_offset_left=c.Int32ul,
    last_frame_offset_right=c.Int32ul,
    last_frame_offset_composite=c.Int32ul,
    # 28
    frame_size=c.Int16ul,
    previous_frame_size=c.Int16ul,
    channel_type=c.Enum(
        c.Int16ul, Primary=0, Secondary=1, DownScan=2,
        SidescanLeft=3, SidescanRight=4, SidescanComposite=5),
    packet_size=c.Int16ul,
    # 36
    frame_index=c.Int32ul,
    upper_limit_feet=c.Float32l,
    lower_limit_feet=c.Float32l,
    # 48
    # pad48=c.Bytes(50-48),
    # # 50
    # frequency=c.Enum(c.Int8ul, KHz200=0, KHz50=1, KHz83=2, KHz455=3, KHz800=4,
    # #     Khz38=5, KHz28=6, Khz130Khz210=7, Khz90Khz150=8, KHz40Khz60=9,
    # #     KHz25KHz45=10),
    pad51=c.Bytes(60 - 48),
    # 60
    time1=c.Int32ul,  # current unix epoch = 1569437027
    water_depth_feet=c.Float32l,
    keel_depth_feet=c.Float32l,
    # 68
    pad2=c.Bytes(100 - 72),
    # 100
    speed_knots=c.Float32l,
    water_temperature_c=c.Float32l,
    easting=c.Int32ul,
    northing=c.Int32ul,
    water_speed_knots=c.Float32l,
    course_over_ground_radians=c.Float32l,
    altitude_ft=c.Float32l,
    heading_radians=c.Float32l,
    # 132
    flags=c.FlagsEnum(
        c.Int16ul,
        GPSSpeedValid=1 << 1,
        WaterTemperatureValid=1 << 2,
        PositionValid=1 << 4,
        WaterSpeedValid=1 << 6,
        TrackValid=1 << 7,
        HeadingValid=1 << 8,
        AltitudeValid=1 << 9,
        **{f'Flag{i}': 1 << i for i in (0, 3, 5, 10, 11, 12, 13, 14, 15)}
    ),
    # 134
    _pad3=c.Bytes(140 - 134),
    # 140
    time_offset=c.Int32ul,
    sounded_data=c.Array(c.this.packet_size, c.Int8ul),
    # sounded_data=c.Array(get_block_size, c.Int8ul)
    #
)

sl2_file = c.Struct(
    header=sl_file_header,
    blocks=c.Array(10, c.FixedSized(2064, sl2_frame))
)

from pathlib import Path
import construct as c

from schemas_navico import sl_file_header, sl2_frame, sl3_frame

if __name__ == '__main__':
    frames = []
    with Path('data', 'Sonar0003.sl3').open('rb') as fd:
        file_header = sl_file_header.parse_stream(fd)

        while True:
            try:
                frame_start = fd.tell()
                frame_bytes = fd.read(3240)
                frame = sl3_frame.parse(frame_bytes)
                pkt_size = frame.packet_size
                fm_size = frame.frame_size
                print(frame.channel_type)
                print(frame.last_frame_offset_primary)
                print(frame.last_frame_offset_secondary)

                assert frame.frame_offset == frame_start
            except c.ConstructError as e:
                print(f'failed to parse block at for reason: {e}')
                break

            frames.append(frame)


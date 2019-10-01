from pathlib import Path
import construct as c

from schemas_navico import sl_file_header, sl2_frame
import matplotlib.pyplot as plt

if __name__ == '__main__':
    # file_bytes = Path('data', 'input.sl2').read_bytes()
    file_bytes = Path('data', 'Sonar_2019-09-30_14.42.31.sl2').read_bytes()

    # for i in range(len(file_bytes)):
    #     if c.Int32ul.parse(file_bytes[i:]) == i:
    #         print(i)

    # pprint(SL2_HEADER)
    # pprint(sl_file_header.parse(SL2_HEADER))
    header = sl_file_header.parse(file_bytes[:8])
    blocks = []

    i = 8
    while i < len(file_bytes):
        try:
            frame = sl2_frame.parse(file_bytes[i:])
            assert frame.frame_offset == i
            i += frame.frame_size
            blocks.append(frame)
            if str(frame.channel_type) == 'SidescanComposite':
                plt.hist(frame.sounded_data, 100)
                plt.show()
            # v in frame.flags.items() if v and k!='_flagsenum')))
        except c.ConstructError as e:
            print(f'failed to parse block at {i} for reason: {e}')

    pass

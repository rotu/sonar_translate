from pathlib import Path

import construct as c
import schemas_navico as n
from schemas_ping2 import ping_schema, message_id_schema, profile6_schema, \
    parse_nmea, parse_nmea_rmc

if __name__ == '__main__':
    # filename = Path('data','noise.ping_packets')
    filename = next(Path('data').glob('Ping2*.ping_packets'))
    b = filename.read_bytes()
    ping2_packets = c.GreedyRange(ping_schema).parse_file(filename)

    sl2_data = dict()
    for pkt in ping2_packets:
        if pkt.message_id.value == message_id_schema.PROFILE6:
            p6 = profile6_schema.parse(pkt.payload.value)
            pass
        elif pkt.message_id.value == message_id_schema.NMEA0183:
            nmea = parse_nmea(pkt.payload.value)
            if nmea.sentence_id == 'RMC':
                rmc = parse_nmea_rmc(nmea.words)
                if not rmc.is_status_ok:
                    print(f'ignoring NMEA sentence {nmea.sentence_id}')

            else:
                pass
                # print (f'ignoring NMEA sentence {nmea.sentence_id}')

        else:
            print(f'ignoring packet with message id {pkt.message_id.value}')

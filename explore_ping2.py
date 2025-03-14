import math
from collections import Counter
from math import log
from pathlib import Path
from types import SimpleNamespace

import construct as c
import schemas_ping2
from schemas_ping2 import parse_nmea, parse_nmea_rmc
import matplotlib.pyplot as plt
import numpy as np

def from_construct(a_construct):
    if isinstance(a_construct, c.ListContainer):
        return list(from_construct(i) for i in a_construct)
    if isinstance(a_construct, c.Container):
        if set(a_construct.keys()) == {
            'data', 'value', 'offset1', 'offset2', 'length'
        }:
            return from_construct(a_construct.value)
        return SimpleNamespace(**{
            k: from_construct(v) for k, v in a_construct.items() if k != '_io'
        })
    else:
        return a_construct


if __name__ == '__main__':
    # filename = Path('data','noise.ping_packets')
    # filename = Path('data', 'good barge at 25m.ping_packets')
    filename = Path('data', 'Ping2-Fri Sep 27 16-34-30 2019-10.ping_packets')

    parsed = c.GreedyRange(schemas_ping2.ping_schema).parse_file(filename)

    ping_packets = from_construct(parsed)
    # talkers = Counter()
    # sentences = Counter()
    # talker_sentences = Counter()
    #
    # for pkt in ping_packets:
    #     if pkt.message_id == schemas_ping2.message_id_schema.NMEA0183:
    #         nmea = parse_nmea(pkt.payload)
    #         talkers[nmea.talker_id] += 1
    #         sentences[nmea.sentence_id] += 1
    #         talker_sentences[nmea.talker_id + nmea.sentence_id] += 1
    #
    #         if nmea.sentence_id == 'RMC':
    #             print(parse_nmea_rmc(nmea.words))
    #
    # print(f'nmea talkers: {talkers}')
    # print(f'nmea sentences: {sentences}')
    # print(f'talker sentences: {talker_sentences}')

    # nmea talkers: Counter({'GN': 13, 'GP': 9, 'GL': 6})
    # nmea sentences: Counter({'GSV': 15, 'GSA': 5, 'GLL': 2, 'RMC': 2, 'VTG': 2, 'GGA': 2})
    # GGA = Global Positioning System Fix Data. Time, Position and fix
    #       related data for a GPS receiver
    # GLL = Geographic Position – Latitude/Longitude
    #       useful!
    # GSV:  Satellites in view - don't care
    # RMC = Recommended Minimum Navigation Information
    #       useful!
    # GSA = GPS DOP and active satellites
    # VTG = Track Made Good and Ground Speed
    #       useful!

    # probably only need rmc

    p6_packets = [from_construct(schemas_ping2.profile6_schema.parse(
        pkt.payload
    )) for pkt in ping_packets if
        pkt.message_id == schemas_ping2.message_id_schema.PROFILE6]

    min_time = p6_packets[0].timestamp_msec / 1000
    max_time = p6_packets[-1].timestamp_msec / 1000
    if not (min_time < max_time):
        min_time = 0
        max_time = 0.1 * len(p6_packets)
    n_time = len(p6_packets)
    min_dist_mm = min(p6.start_mm for p6 in p6_packets)
    max_dist_mm = max(p6.start_mm + p6.length_mm for p6 in p6_packets)
    n_dist = 1000

    imdata = []

    for p6 in p6_packets:
        db = schemas_ping2.get_ranges_db(p6)
        imrow = np.interp(
            np.linspace(min_dist_mm, max_dist_mm, n_dist),
            np.linspace(p6.start_mm, p6.start_mm + p6.length_mm, len(db)),
            db
        )
        imdata.append(imrow)
    x = np.shape(imdata)

    im = plt.pcolormesh(
        np.linspace(min_dist_mm, max_dist_mm, n_dist) / 1000,
        np.linspace(min_time, max_time, n_time),
        imdata,
        # cmap='ocean'
    )
    plt.title(filename)
    plt.colorbar().set_label('decibels')
    plt.xlabel('distance (meters)')
    plt.ylabel('time (seconds)')

    plt.show()

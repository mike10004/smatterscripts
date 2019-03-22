#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  ressample.py
#  
#  (c) 2015 Mike Chaberski
#  
#  MIT License

from __future__ import print_function
from _common import StreamContext
from argparse import ArgumentParser
import random
import errno
import logging
from operator import itemgetter
from typing import Iterator, List


_log = logging.getLogger(__name__)


# noinspection PyMethodMayBeStatic
class ReservoirSampler(object):

    preserve_order = False

    def __init__(self, rng: random.Random=None):
        self.rng = rng or random.SystemRandom()

    def _replace_item(self, item, s, subset):
        subset[s] = item

    def _append_item(self, item, subset):
        subset.append(item)

    def collect(self, iterator: Iterator, k: int) -> List:
        result = []
        for item in enumerate(iterator):
            n = item[0]
            if len(result) < k:
                self._append_item(item, result)
            else:
                s = int(self.rng.random() * (n + 1))
                if s < k:
                    self._replace_item(item, s, result)
        if self.preserve_order:
            result.sort(key=itemgetter(0))
        return list(map(itemgetter(1), result))


def main():
    parser = ArgumentParser(description="Samples lines from an input stream.", epilog="Bear in mind that the sample is collected in memory before being printed. Exits clean unless I/O error occurs or input is too small.")
    parser.add_argument("k", type=int, metavar="K", help="sample size")
    parser.add_argument("inputfile", nargs='?', help="input file; if absent or - then uses stdin")
    parser.add_argument("-p", "--preserve-order", action="store_true", help="preserve order from stream")
    args = parser.parse_args()
    sampler = ReservoirSampler(random.SystemRandom())
    for attr in ('preserve_order',):
        sampler.__setattr__(attr, args.__dict__[attr])
    with StreamContext(args.inputfile, 'r') as iterator:
        sample = sampler.collect(iterator, args.k)
    try:
        for s in sample:
            print(s, end="")
    except IOError as e:
        if errno.EPIPE == e.errno:
             _log.info("broken pipe; not all items from sample printed")
        else:
            raise
    if len(sample) < args.k:
        _log.warning("not enough items in input; sample contains only %s", len(sample))
        return 2
    return 0



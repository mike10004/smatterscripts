#!/usr/bin/env python3

from _common import StreamContext
import sys
from argparse import ArgumentParser
import itertools
from shelltools.ressample import ReservoirSampler
from typing import Sequence

def _has_dupes(items: Sequence):
    if len(items) <= 1:
        return False
    if len(items) == 2:
        return items[0] == items[1]
    # would len(set(items)) < len(items) be faster?
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i] == items[j]:
                return True
    return False

class Generator(object):

    avoid_dupes = False

    # noinspection PyMethodMayBeStatic
    def _uniques(self, iterator):
        for combo in iterator:
            if not _has_dupes(combo):
                yield combo

    def generate(self, input_args):
        iterables = []
        for input_arg in input_args:
            with StreamContext(input_arg, 'r') as ifile:
                iterables.append([line.rstrip("\r\n") for line in ifile])
        all_combos = itertools.product(*iterables)
        if self.avoid_dupes:
            return self._uniques(all_combos)
        else:
            return all_combos

def render(selection, delimiter, ofile=sys.stdout):
    print(*selection, sep=delimiter, file=ofile)

def main():
    parser = ArgumentParser(description="Print combinations of items from multiple streams.", epilog="Note that all input content is stored in memory.")
    parser.add_argument("input", nargs='+', metavar="FILE", help="multiple files from which product will be printed")
    parser.add_argument("-k", "--sample", type=int, metavar="K", help="sample size")
    parser.add_argument("-d", "--delimiter", default=' ', metavar="STR", help="set delimiter between items on each line")

    args = parser.parse_args()
    if len(args.input) == 1:
        print("streamproduct: n > 1 arguments required", file=sys.stderr)
        return 1
    # TODO remove this restriction by caching stdin if present more than once
    if len(list(filter(lambda x: x == '-' or x == '/dev/stdin', args.input))) > 1:
        print("streamproduct: at most one argument may specify standard input", file=sys.stderr)
        return 1
    g = Generator()
    if args.sample is not None:
        sampler = ReservoirSampler()
        combos = sampler.collect(g.generate(args.input), args.sample)
    else:
        combos = g.generate(args.input)
    for selection in combos:
        render(selection, args.delimiter)
    return 0
#!/usr/bin/env python3

from _common import StreamContext
import sys
from argparse import ArgumentParser
import itertools
from shelltools.ressample import ReservoirSampler

def generate(input_args):
    iterables = []
    for input_arg in input_args:
        with StreamContext(input_arg, 'r') as ifile:
            iterables.append([line.rstrip("\r\n") for line in ifile])
    return itertools.product(*iterables)

def render(selection, delimiter, ofile=sys.stdout):
    print(*selection, sep=delimiter, file=ofile)

def main():
    parser = ArgumentParser(epilog="Note that all input content is stored in memory.")
    parser.add_argument("input", nargs='+', metavar="FILE", help="multiple files from which product will be printed")
    parser.add_argument("-k", "--sample", type=int, metavar="K", help="sample size")
    parser.add_argument("--delimiter", default=' ')

    args = parser.parse_args()
    if len(args.input) == 1:
        print("streamproduct: n > 1 arguments required", file=sys.stderr)
        return 1
    # TODO remove this restriction by caching stdin if present more than once
    if len(list(filter(lambda x: x == '-' or x == '/dev/stdin', args.input))) > 1:
        print("streamproduct: at most one argument may specify standard input", file=sys.stderr)
        return 1
    if args.sample is not None:
        sampler = ReservoirSampler()
        combos = sampler.collect(generate(args.input), args.sample)
    else:
        combos = generate(args.input)
    for selection in combos:
        render(selection, args.delimiter)
    return 0
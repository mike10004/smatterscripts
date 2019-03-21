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
import sys
from typing import TypeVar, Iterator, List

T = TypeVar('T')

class ReservoirSampler(object):

    conserve = False
    preserve_order = False

    def __init__(self, rng: random.Random):
        self.rng = rng

    def _replace_item(self, item, n, s, subset):
        if self.conserve:
            subset[s] = n
        else:
            subset[s] = item

    def _append_item(self, item, n, subset):
        if self.conserve:
            subset.append(n)
        else:
            subset.append(item)

    def collect(self, iterator: Iterator, k: int) -> List:
        result = []
        n = 0
        for item in iterator:
            n += 1
            if len(result) < k:
                self._append_item(item, n, result)
            else:
                s = int(self.rng.random() * n)
                if s < k:
                    self._replace_item(item, n, s, result)
        return result


def get_reservoir_sample(iterator: Iterator, k, args) -> List:
    sampler = ReservoirSampler(random.SystemRandom())
    sampler.conserve = args.conserve
    return sampler.collect(iterator, k)

def _print_lines(ifile, subset, args):
    subset.sort(reverse=True)
    n = 0
    k = len(subset)
    for line in ifile:
        n += 1
        if subset[k - 1] == n:
            print(line, end="")
            del subset[k - 1]
            k = len(subset)

def main():
    parser = ArgumentParser()
    parser.add_argument("k", type=int, metavar="K", help="sample size")
    parser.add_argument("inputfile", nargs='?', 
            help="input file; if absent or - then uses stdin")
    parser.add_argument("--conserve", action="store_true", 
            help="conserve space at expense of time; only retains indices"
            +" of sampled items and iterates over input again to print")
    args = parser.parse_args()
    if args.conserve and args.inputfile is None:
        print("ressample: can't use stdin input with --conserve", file=sys.stderr)
        return 1
    with StreamContext(args.inputfile, 'r') as iterator:
        sample = get_reservoir_sample(iterator, args.k, args)
    if args.conserve:
        with open(args.inputfile, 'r') as ifile:
            _print_lines(ifile, sample, args)
    else:
        for s in sample:
            print(s, end="")
    if len(sample) < args.k:
        print("ressample: not enough items in input; sample contains only", len(sample), file=sys.stderr)
        return 2
    return 0



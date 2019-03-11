#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  ressample.py
#  
#  (c) 2015 Mike Chaberski
#  
#  MIT License

from __future__ import print_function
from argparse import ArgumentParser
import random
import sys

def _replace_item(item, n, s, subset, args):
    if args.conserve:
        subset[s] = n
    else:
        subset[s] = item

def _append_item(item, n, subset, args):
    if args.conserve:
        subset.append(n)
    else:
        subset.append(item)

def get_reservoir_sample(iterator, k, args=None):
    result = []
    n = 0
    sampled = 0
    for item in iterator:
        n += 1
        if len(result) < k:
            _append_item(item, n, result, args)
        else:
            s = int(random.random() * n)
            if s < k:
                _replace_item(item, n, s, result, args)
    return result

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
    if args.inputfile is None or args.inputfile == '-':
        iterator = sys.stdin
        sample = get_reservoir_sample(iterator, args.k, args)
    else:
        with open(args.inputfile, 'r') as iterator:
            sample = get_reservoir_sample(iterator, args.k, args)
    if args.conserve:
        n = 0
        with open(args.inputfile, 'r') as ifile:
            _print_lines(ifile, sample, args)
    else:
        for s in sample:
            print(s, end="")
    if len(sample) < args.k:
        print("ressample: not enough items in input; sample contains only", len(sample), file=sys.stderr)
        return 2
    return 0

if __name__ == '__main__':
    exit(main())


#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys


def main():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("files", nargs="*")
    parser.add_argument("--prefix", default=" * ")
    args = parser.parse_args()
    if args.files:
        raise NotImplementedError()
    print()
    for line in sys.stdin:
        print("{}{}".format(args.prefix, line.rstrip()))
    return 0
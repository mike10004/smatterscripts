#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  csvcoledit.py
#
#  (c) 2018 Mike Chaberski
#  
#  MIT License

import csv
from argparse import ArgumentParser
import logging
import _common
from typing import Collection, TextIO, List, Callable


_log = logging.getLogger(__name__)


class Swapper(object):

    def __init__(self, col1: int, col2: int):
        self.col1 = col1
        self.col2 = col2

    def __call__(self, row: list):
        try:
            tmp = row[self.col1]
            row[self.col1] = row[self.col2]
            row[self.col2] = tmp
        except IndexError:
            pass


class Deleter(object):

    def __init__(self, cols: Collection[int]):
        self.cols = cols

    def __call__(self, row):
        try:
            keep = filter(lambda col: col not in self.cols, range(len(row)))
            row_copy = [row[i] for i in keep]
            for i in range(len(row_copy)):
                row[i] = row_copy[i]
            for i in range(len(row) - 1, len(row_copy) - 1, -1):
                del row[i]
        except IndexError:
            pass


def _parse_colspec(spec: str) -> Collection[int]:
    cols = set()
    tokens = spec.split(',')
    for token in tokens:
        if '-' in token:
            raise NotImplementedError("column range specifications not yet supported")
        if token:
            cols.add(int(token))
    return frozenset(cols)


def operate(ifile: TextIO, ofile: TextIO, operations: List[Callable[[list], None]], writer_kwargs=None):
    reader = csv.reader(ifile)
    writer_kwargs = writer_kwargs or {}
    writer = csv.writer(ofile, **writer_kwargs)
    for row in reader:
        for operation in operations:
            operation(row)
        writer.writerow(row)
    return 0


def main():
    parser = ArgumentParser(description="Operate on CSV input. Currently supports column swap and delete only. Be careful when combining operations; delete always happens before swap.")
    _common.add_logging_options(parser)
    parser.add_argument("csvfile", nargs="?", help="input file (if absent, read from stdin)")
    parser.add_argument("--swap", nargs=2, type=int, help="operation: swap columns at zero-based indexes A and B", metavar=('A', 'B'))
    parser.add_argument("--delete", metavar="SPEC", help="delete one or more columns; SPEC is column-delimited list")
    parser.add_argument("-o", "--output", help="print output to file instead of stdout")
    args = parser.parse_args()
    _common.config_logging(args)
    operations = []
    if args.delete is not None:
        operations.append(Deleter(_parse_colspec(args.delete)))
    if args.swap is not None:
        operations.append(Swapper(args.swap[0], args.swap[1]))
    if not operations:
        _log.warning("no operations specified")
    if not args.csvfile:
        args.csvfile = '/dev/stdin'
    if not args.output:
        args.output = '/dev/stdout'
    with open(args.csvfile, 'r') as ifile:
        with open(args.ofile, 'w') as ofile:
            operate(ifile, ofile, operations)
    return 0

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  csvcoledit.py
#
#  (c) 2015 Mike Chaberski
#  
#  MIT License

import sys
import csv
from argparse import ArgumentParser
import logging
import _common

_log = logging.getLogger(__name__)


def _open_ofile_and_do(ifile, opfunction, args):
    if args.output is None or args.output == '-':
        ofile = sys.stdout
        return opfunction(ifile, ofile, args)
    else:
        with open(args.output, 'w') as ofile:
            return opfunction(ifile, ofile, args)

def do_swap(ifile, ofile, args):
    col1, col2 = args.swap
    reader = csv.reader(ifile)
    writer = csv.writer(ofile)
    for row in reader:
        if max(col1, col2) >= len(row):
            writer.writerow(row)
        else:
            tmp = row[col1]
            row[col1] = row[col2]
            row[col2] = tmp
            writer.writerow(row)
    return 0

def _has_operation(args):
    return not (args.swap is None)  # ...and args.other is None and args.another is None...

def main():
    parser = ArgumentParser(description="Operate on CSV input. Not all operations can be combined.")
    _common.add_logging_options(parser)
    parser.add_argument("csvfile", nargs="?", help="input file (if absent, read from stdin)")
    parser.add_argument("--swap", nargs=2, type=int, help="operation: swap columns at zero-based indices A and B", metavar=('A', 'B'))
    parser.add_argument("-o", "--output", help="print output to file instead of stdout")
    args = parser.parse_args()
    _common.config_logging(args)
    if not _has_operation(args):
        _log.warning("no operations specified")
    if args.swap is not None:
        opfunction = do_swap
    else:
        raise ValueError("unhandled absence of operation")
    if args.csvfile is None or args.csvfile == '-':
        ifile = sys.stdin
        return _open_ofile_and_do(ifile, opfunction, args)
    else:
        with open(args.csvfile, 'r') as ifile:
            return _open_ofile_and_do(ifile, opfunction, args)

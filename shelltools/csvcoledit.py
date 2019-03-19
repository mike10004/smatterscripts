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
    parser = ArgumentParser(description="Operate on CSV input. Must specify at least one operation. Not all operations can be combined.")
    parser.add_argument("csvfile", nargs="?", help="input file (if absent, read from stdin)")
    parser.add_argument("--swap", nargs=2, type=int, help="operation: swap columns at indices A and B (first column is zero)", metavar=('A', 'B'))
    parser.add_argument("-o", "--output", help="print output to file instead of stdout")
    args = parser.parse_args()
    if not _has_operation(args):
        parser.error("no operation specified")
        return 1 # parser.error calls sys.exit, but in case that changes
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





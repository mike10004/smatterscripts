#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  histo.py
#  
#  (c) 2015 Mike Chaberski
#  
#  MIT License

from __future__ import print_function
import csv
import re
import os
import sys
import errno
from shelltools import _common
from typing import Callable, Collection, TextIO, List, Any, Pattern
from argparse import ArgumentParser, Namespace
import logging

_log = logging.getLogger("histo")

def get_bin_spec(values, args):
    numbins = args.num_bins
    if args.bins is None:
        binmin = min(values)
        binstep = (max(values) + 1e-5 - binmin) / numbins
    else:
        binmin, binstep = [args.value_type(x) for x in args.bins]
    _log.debug(" bin spec: (%s, %s, %s) (%s, %s, %s); args.value_type = %s" % 
            (str(binmin), str(binstep), str(numbins), 
            str(type(binmin)), str(type(binstep)), str(type(numbins)), str(args.value_type)))
    return binmin, binstep, numbins

def format_float(value, args):
    if args.relative_precision < 1 or args.relative_precision > 255:
        print("histo: invalid relative precision value:", args.relative_precision, file=sys.stderr)
        args.relative_precision = 4
    fmt = "%" + str(args.relative_precision) + "f"
    return fmt % value

def write_histo_row(writer, binlabel, count, total, args):
    if isinstance(binlabel, float) and args.bin_precision is not None:
        if args.bin_precision < 0 or args.bin_precision > 20:
            raise ValueError("invalid bin precision")
        fmt = "%." + str(args.bin_precision) + "f"
        binlabel = fmt % binlabel
    if args.relative:
        rel = format_float(float(count) / float(total), args)
        row = [binlabel, count, rel]
    else:
        row = [binlabel, count]
    writer.writerow(row)

def print_categorical_histo(values, args):
    writer = csv.writer(sys.stdout)
    values.sort()
    prev = None
    n = 0
    for value in values:
        if prev is None:
            prev = value
        else:
            if value != prev:
                writer.writerow([prev, n])
                n = 0
        prev = value
        n += 1
    return 0


_ALWAYS_TRUE = lambda x: True


def _remove_suffix(s: str, suffix: str, other_suffixes: Collection[str]=None):
    all_suffixes = [suffix]
    if other_suffixes:
        all_suffixes += other_suffixes
    all_suffixes.sort(key=len, reverse=True)
    for suffix_ in filter(lambda x: len(x) > 0, all_suffixes):
        if s.endswith(suffix_):
            return s[:-len(suffix_)]
    return s


def _read_pattern_file(ifile: TextIO) -> List[Pattern]:
    patterns = []
    for line in ifile:
        line = _remove_suffix(line, "\r\n", ("\n", "\r\r"))
        if line and not line.lstrip().startswith("#"):
            p = re.compile(line)
            patterns.append(p)
    return patterns


def _load_implicit_pattern_files() -> List[Pattern]:
    pathnames = [
        os.path.join(os.getenv('HOME'), '.config', 'smatterscripts', 'historc'),
        os.path.join(os.getcwd(), '.historc'),
    ]
    patterns = []
    for pathname in pathnames:
        try:
            with open(pathname, 'r') as ifile:
                patterns += _read_pattern_file(ifile)
        except IOError as e:
            if errno.ENOENT != e.errno:
                _log.warning("failed to load patterns from %s due to IOError: %s", pathname, e)
    return patterns



def build_value_filter(args: Namespace) -> Callable[[List[str]], bool]:
    patterns = _load_implicit_pattern_files()
    if args.redact is not None:
        patterns.append(re.compile(args.redact))
    if args.redact_patterns is not None:
        with open(args.redact_patterns, 'r') as ifile:
            patterns += _read_pattern_file(ifile)
    return build_filter_from_patterns(patterns)


def build_filter_from_patterns(patterns: List[Pattern]) -> Callable[[List[str]], bool]:
    if not patterns:
        return _ALWAYS_TRUE
    def do_filter(row):
        for cell in row:
            for pattern in patterns:
                if pattern.search(cell) is not None:
                    return False
        return True
    return do_filter



def build_parse_value(args: Namespace) -> Callable[[str], Any]:
    _log.debug(" reading values as type %s" % args.value_type)
    return args.value_type


class ValueParser(object):

    def __init__(self, parse_value: Callable[[str], Any], value_filter: Callable[[List[str]], bool], ignore_errors: bool=False):
        self.parse_value = parse_value
        self.value_filter = value_filter
        self.ignore_errors = ignore_errors

    def read_values(self, ifile: TextIO, skip: int=0, values_col: int=0) -> List[Any]:
        values = []
        reader = csv.reader(ifile)
        nskipped = 0
        for row in reader:
            if nskipped < skip:
                nskipped += 1
                continue
            try:
                if self.value_filter(row):
                    v = self.parse_value(row[values_col])
                    values.append(v)
            except ValueError:
                if not self.ignore_errors:
                    raise
        return values




def print_histo(args: Namespace):
    parse_value = build_parse_value(args)
    value_filter = build_value_filter(args)
    value_parser = ValueParser(parse_value, value_filter, args.ignore)
    if args.valuesfile is None or args.valuesfile == '-':
        print("histo: reading values from standard input", file=sys.stderr)
        values = value_parser.read_values(sys.stdin, args.skip, args.values_col)
    else:
        with open(args.valuesfile, 'r') as ifile:
            values = value_parser.read_values(ifile, args.skip, args.values_col)
    if len(values) < 1 and args.bins is None:
        _log.error(" no values read from file; can't guess bins")
        return 2
    if args.value_type == str:
        return print_categorical_histo(values, args)
    if len(values) > 0:
        _log.debug(" value[0] = %s (%s)" % (str(values[0]), type(values[0])))
    else:
        _log.debug(" values list is empty")
    binmin, binstep, numbins = get_bin_spec(values, args)
    if numbins < 1:
        _log.error(" num bins specification is invalid: " + numbins)
        return 1
    values.sort()
    n = 0
    total = len(values)
    writer = csv.writer(sys.stdout, delimiter=args.delim)
    if len(values) > 0:
        while values[n] < binmin and n < len(values):
            n += 1
        if not args.exclude_extremes and (n > 0 or args.include_extremes):
            write_histo_row(writer, "Less", n, total, args)
        values = values[n:]
    bottom = binmin
    top = bottom + binstep
    for b in range(0, numbins):
        n = 0
        while n < len(values) and values[n] < top:
            n += 1
        _log.debug(" bin[%d]: [%s, %s) -> %d (%d remaining)" % (b, bottom, top, n, len(values)))
        write_histo_row(writer, bottom, n, total, args)
        bottom += binstep
        top += binstep
        values = values[n:]
    if not args.exclude_extremes and (len(values) > 0 or args.include_extremes):
        write_histo_row(writer, "More", len(values), total, args)
    return 0


def main():
    parser = ArgumentParser()
    parser.add_argument("valuesfile", nargs='?', default='/dev/stdin', help="file to read values from; if not present, stdin is read")
    parser.add_argument("-d", "--delim", action="store", metavar="CHAR", help="set output delimiter (use 'TAB' for tab; default is ',')", default=",")
    _common.add_logging_options(parser)
    parser.add_argument("-v", "--verbose", action="store_const", const='DEBUG', dest='log_level', help="set log level DEBUG")
    parser.add_argument("-c", "--values-col", default=0, type=int, metavar="K", help="column containing values to be counted (default 0)")
    parser.add_argument("-s", "--skip", default=0, type=int, metavar="N", help="rows to skip at beginning of file (default 0)")
    parser.add_argument("-b", "--bins", default=None, nargs=2, metavar=("MIN","STEP"), type=str, help="bin specification")
    parser.add_argument("-n", "--num-bins", default=10, type=int, metavar="N", help="if --bins is not specified, divide into this many bins (default 10)")
    parser.add_argument("-t", "--value-type", choices=(int, float, str), default=float, type=type, metavar="TYPE", help="value type (default float)")
    parser.add_argument("-x", "--include-extremes", help="include Less and More bins even if empty", action="store_true", default=False)
    parser.add_argument("-X", "--exclude-extremes", help="exclude Less and More bins even if nonempty", action="store_true", default=False)
    parser.add_argument("--bin-precision", type=int, metavar="N", choices=tuple(range(32)), help="print float bin labels with specified precision")
    parser.add_argument("--ignore", action="store_true", help="ignore un-parseable values", default=False)
    parser.add_argument("--relative", help="also print relative frequency", action="store_true")
    parser.add_argument("--relative-precision", type=int, default=4, help="specify precision for formatting relative frequency values")
    parser.add_argument("--redact", metavar='REGEX', help="redact rows from input that match regex")
    parser.add_argument("--redact-patterns", metavar="FILE", help="redact rows from input that match regex on any line of in FILE")
    args = parser.parse_args()
    if args.delim == 'TAB': args.delim = '\t'
    _common.config_logging(args)
    return print_histo(args)

if __name__ == '__main__':
    exit(main())


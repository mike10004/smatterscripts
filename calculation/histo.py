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
import json
import errno
import logging
import _common
import calculation
from _common import redaction
from typing import Callable, TextIO, List, Any, Pattern, Dict, Sequence, Tuple, Optional
from argparse import ArgumentParser, Namespace
from . import ValueParser, Ignorer


_log = logging.getLogger(__name__)
_IDENTITY = calculation._IDENTITY
_ACCUM_NONE = 'none'
_ACCUM_INCREASE = 'increase'
_ACCUM_COMPLEMENT = 'complement'
_ACCUM_MODES = (_ACCUM_NONE, _ACCUM_INCREASE, _ACCUM_COMPLEMENT)


def get_bin_spec(values, args):
    numbins = args.num_bins
    if args.bins is None:
        binmin = min(values)
        binstep = ((max(values) + args.epsilon) - binmin) / numbins
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


# noinspection PyUnusedLocal
def read_config(args: Namespace) -> Dict[str, Any]:
    pathnames = [
        os.path.join(os.getenv('HOME'), '.config', 'smatterscripts', 'historc'),
        os.path.join(os.getcwd(), '.historc'),
    ]
    config = {}
    for pathname in pathnames:
        try:
            with open(pathname, 'r') as ifile:
               config.update(json.load(ifile))
        except IOError as e:
            if errno.ENOENT != e.errno:
                _log.warning("failed to load patterns from %s due to IOError: %s", pathname, e)
    return config


def _load_implicit_patterns(config) -> List[Pattern]:
    pattern_tokens = config.get('redact_patterns', None) or tuple()
    patterns = map(re.compile, pattern_tokens)
    return list(patterns)


def _build_row_filter(patterns: List[Pattern]) -> Callable[[List[str]], bool]:
    cell_filter = redaction.build_filter_from_patterns(patterns)
    def do_filter(row):
        return all(map(cell_filter, row))
    return do_filter


def build_value_filter(config: Dict, args: Namespace) -> Callable[[List[str]], bool]:
    patterns = _load_implicit_patterns(config)
    if args.redact is not None:
        patterns.append(re.compile(args.redact))
    if args.redact_patterns is not None:
        with open(args.redact_patterns, 'r') as ifile:
            patterns += redaction.read_pattern_file(ifile)
    return _build_row_filter(patterns)


def _include_overflow_bin(setting: str, bin_count: int):
    return (setting == 'include') or ((setting == 'auto') and (bin_count > 0))



def _make_mal_decision(setting: str) -> Callable:
    def raise_error(row_index, input_value, exception):
        _log.info(" raising error due to value at row %d", row_index)
        raise exception
    if setting == 'ignore':
        return Ignorer()
    if setting == 'error':
        return raise_error
    m = re.fullmatch(r'^replace:(\S+)$', setting)
    if m is None:
        raise ValueError("--malformed parameter does not match expected syntax")
    replacement = m.group(1)
    def replace_value(*args, **kwargs):
        return replacement
    return replace_value


def _to_freq(n: int, accumulation: int, total: int, mode: str):
    if mode == _ACCUM_NONE:
        return n
    if mode == _ACCUM_INCREASE:
        return accumulation + n
    if mode == _ACCUM_COMPLEMENT:
        return total - (accumulation + n)
    raise ValueError(f"unrecognized mode: {mode}")


def print_histo(args: Namespace, ofile: TextIO=sys.stdout):
    config = read_config(args)
    parse_value = calculation.build_parse_value(args.value_type, args.invert)
    value_filter = build_value_filter(config, args)
    mal_decision = _make_mal_decision(args.malformed)
    clamp = calculation.make_clamp(args.clamp, args.value_type)
    value_parser = ValueParser(parse_value, value_filter, mal_decision, clamp)
    if args.valuesfile is None or args.valuesfile == '-':
        print("histo: reading values from standard input", file=sys.stderr)
        values = value_parser.read_values(sys.stdin, args.skip, args.values_col)
    else:
        with open(args.valuesfile, 'r') as ifile:
            values = value_parser.read_values(ifile, args.skip, args.values_col)
    if value_parser.num_ignored > 0:
        _log.info(" %d value(s) ignored", value_parser.num_ignored)
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
    writer = csv.writer(ofile, delimiter=args.delim)
    if len(values) > 0:
        while values[n] < binmin and n < len(values):
            n += 1
        if _include_overflow_bin(args.overflow, n):
            write_histo_row(writer, "Less", n, total, args)
        values = values[n:]
    bottom = binmin
    top = bottom + binstep
    accumulation = 0
    for b in range(0, numbins):
        n = 0
        while n < len(values) and values[n] < top:
            n += 1
        _log.debug(" bin[%d]: [%s, %s) -> %d (%d remaining)" % (b, bottom, top, n, len(values)))
        frequency = _to_freq(n, accumulation, total, args.accumulate)
        write_histo_row(writer, bottom, frequency, total, args)
        bottom += binstep
        top += binstep
        values = values[n:]
        accumulation += n
    n = len(values)
    accumulation += n
    frequency = _to_freq(n, accumulation, total, args.accumulate)
    if _include_overflow_bin(args.overflow, n):
        write_histo_row(writer, "More", frequency, total, args)
    return 0


def _create_arg_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Compiles and prints a histogram of values in input.",
                            epilog="Reads config settings from JSON-formatted file named `.historc` in working "
                                   + "directory and `$HOME/.config/smatterscripts/historc`.")
    parser.add_argument("valuesfile", nargs='?', default='/dev/stdin', help="file to read values from; uses stdin if absent")
    parser.add_argument("-d", "--delim", "--output-delimiter", dest="delim", metavar="CHAR", help="set output delimiter (use TAB for tab; default is ',')", default=",")
    _common.add_logging_options(parser)
    parser.add_argument("-v", "--verbose", action="store_const", const='DEBUG', dest='log_level', help="set log level DEBUG")
    parser.add_argument("-c", "--values-col", default=0, type=int, metavar="K", help="column containing values to be counted (default 0)")
    parser.add_argument("-s", "--skip", default=0, type=int, metavar="N", help="rows to skip at beginning of file (default 0)")
    parser.add_argument("-b", "--bins", default=None, nargs=2, metavar=("MIN","STEP"), type=str, help="set bin minimum and bin increment")
    parser.add_argument("-n", "--num-bins", default=10, type=int, metavar="N", help="assign values to N bins (default 10)")
    parser.add_argument("-t", "--value-type", choices=(int, float, str), default=float, type=type, metavar="TYPE", help="value type (default float)")
    parser.add_argument("--overflow", choices=('include', 'exclude', 'auto'), default='auto', help="include/exclude Less and More bins; 'auto' means include if nonempty")
    parser.add_argument("--bin-precision", type=int, metavar="P", choices=tuple(range(32)), help="print bin labels with P decimal places")
    parser.add_argument("--malformed", "-m", default="ignore", help="action on un-parseable values; default is 'ignore'; options include 'error' or 'replace:X' to replace such values with X")
    parser.add_argument("--relative", help="also print relative frequency", action="store_true")
    parser.add_argument("--relative-precision", type=int, default=4, metavar="P", help="print relative frequency out to P decimal places")
    parser.add_argument("--redact", metavar='REGEX', help="redact rows from input where any cell matches REGEX")
    parser.add_argument("--redact-patterns", metavar="FILE", help="redact rows from input where any cell matches regex on any line in FILE")
    parser.add_argument("--clamp", nargs=2, metavar=("min", "max"), help="clamp values into range [X,Y]")
    parser.add_argument("--invert", action='store_true', help="invert parsed values")
    parser.add_argument("--epsilon", type=float, metavar="E", default=1e-5, help="set pad value for automatic bin size calculation")
    parser.add_argument("--accumulate", default=_ACCUM_NONE, metavar='MODE', choices=_ACCUM_MODES, help="set frequency accumulation mode; choices are " + str(set(_ACCUM_MODES)))
    return parser


def main(argl: Sequence[str]=None, ofile: TextIO=sys.stdout):
    parser = _create_arg_parser()
    args = parser.parse_args(argl)
    if args.delim == 'TAB': args.delim = '\t'
    _common.config_logging(args)
    return print_histo(args, ofile)


#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  histo.py
#  
#  (c) 2015 Mike Chaberski
#  
#  MIT License

import csv
import sys
from argparse import ArgumentParser
import logging

_log = logging.getLogger("histo")

#~ def pokethru(valuetype):
    #~ if valuetype == int:
        #~ return 1
    #~ elif valuetype == float:
        #~ return 

def get_bin_spec(values, args):
    numbins = args.num_bins
    if args.bins is None:
        binmin = min(values)
        binstep = max(values) - binmin / args.num_bins
    else:
        binmin, binstep = tuple([args.value_type(x) for x in args.bins])
    _log.debug(" bin spec: (%s, %s, %s) (%s, %s, %s); args.value_type = %s" % 
            (str(binmin), str(binstep), str(numbins), 
            str(type(binmin)), str(type(binstep)), str(type(numbins)), str(args.value_type)))
    return binmin, binstep, numbins

def format_float(value, args):
    if args.relative_precision < 1 or args.relative_precision > 255:
        print >> sys.stderr, "invalid relative precision value:", args.relative_precision
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
        if prev is None: prev = value
        else:
            if value != prev:
                writer.writerow([prev, n])
                n = 0
        prev = value
        n += 1
    return 0

def read_values(ifile, args):
    _log.debug(" reading values as type %s" % args.value_type)
    values = []
    reader = csv.reader(ifile)
    nskipped = 0
    for row in reader:
        if nskipped < args.skip:
            nskipped += 1
            continue
        try:
            v = args.value_type(row[args.values_col])
            values.append(v)
        except ValueError:
            if not args.ignore:
                raise
    return values

def print_histo(args):
    if args.valuesfile is None:
        values = read_values(sys.stdin, args)
    else:
        with open(args.valuesfile, 'r') as ifile:
            values = read_values(ifile, args)
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
    #cumul_n = 0
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
    for b in xrange(0, numbins):
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

def _parse_value_type(args):
    if args.value_type == 'int':
        args.value_type = int
    elif args.value_type == 'float':
        args.value_type = float
    elif args.value_type == 'str':
        args.value_type = str
    else:
        raise ValueError("bad value type: " + str(args.value_type))

def main():
    parser = ArgumentParser()
    parser.add_argument("valuesfile", nargs='?', help="file to read values from; if not present, stdin is read")
    parser.add_argument("-d", "--delim", action="store", help="set output delimiter (use 'TAB' for tab)", default=",")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-c", "--values-col", default=0, type=int, help="column containing values to be counted (default 0)")
    parser.add_argument("-s", "--skip", default=0, type=int, help="rows to skip at beginning of file (default 0)")
    parser.add_argument("-b", "--bins", default=None, nargs=2, metavar=("MIN","STEP"), type=str, help="bin specification")
    parser.add_argument("-n", "--num-bins", default=10, type=int, help="if --bins is not specified, divide into this many bins (default 10)")
    parser.add_argument("-t", "--value-type", choices=['int', 'float', 'str'], default='float', help="value type (default float)")
    parser.add_argument("-x", "--include-extremes", help="include Less and More bins even if empty", action="store_true", default=False)
    parser.add_argument("-X", "--exclude-extremes", help="exclude Less and More bins even if nonempty", action="store_true", default=False)
    parser.add_argument("--bin-precision", type=int, help="print float bin labels with specified precision")
    parser.add_argument("--ignore", action="store_true", help="ignore un-parseable values", default=False)
    parser.add_argument("--relative", help="also print relative frequency", action="store_true")
    parser.add_argument("--relative-precision", type=int, default=4, help="specify precision for formatting relative frequency values")
    args = parser.parse_args()
    _parse_value_type(args)
    if args.delim == 'TAB': args.delim = '\t'
    logging.basicConfig(level=logging.INFO)
    if args.verbose:
        _log.setLevel(logging.DEBUG)
    return print_histo(args)

if __name__ == '__main__':
    exit(main())


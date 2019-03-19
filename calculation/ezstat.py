# -*- coding: utf-8 -*-
#
#  ezstat.py
#  
#  (c) 2015 Mike Chaberski
#  
#  MIT License

from __future__ import print_function
from argparse import ArgumentParser
import csv
import sys
import scipy.stats as stats

_COMMANDS = ['describe']

def _get_num_fmt(value, args):
    fmt = "%.4f"
    if isinstance(value, int):
        fmt = "%d"
    return fmt

def _to_formatted_values(d, args):
    lengths = []
    svalues = []
    for k, v in d:
        fmt = _get_num_fmt(v, args)
        s = fmt % v
        lengths.append(len(s))
        svalues.append((k, s))
    lenmax = max(lengths)
    sfmt = "%" + str(lenmax) + "s"
    for i in range(len(svalues)):
        k, v = svalues[i]
        v = sfmt % v
        svalues[i] = (k, v)
    return svalues

def do_describe(values, args):
    d = [
     ("min", min(values)), 
     ("median", stats.nanmedian(values)),
     ("mean", stats.nanmean(values)),
     ("max", max(values)),
     ("stdev", stats.nanstd(values))
    ]
    d = _to_formatted_values(d, args)
    for value, name in d:
        print(name, value)
    return 0

def read_values(ifile, datatype, args):
    if args.not_csv:
        values = [datatype(line.strip()) for line in ifile]
        return values
    else:
        reader = csv.reader(ifile)
        values = []
        for row in reader:
            v = datatype(row[args.column])
            values.append(v)
        return values

def main():
    parser = ArgumentParser()
    parser.add_argument("command", choices=_COMMANDS)
    parser.add_argument("datafile", nargs="?", default="-")
    parser.add_argument("--not-csv", help="turn off CSV parsing, assume each line is a value", action="store_true", default=False)
    parser.add_argument("-c", "--column", default=0, type=int)
    parser.add_argument("-t", "--datatype", choices={"int", "float"}, default="float")
    args = parser.parse_args()
    datatype = eval(args.datatype)
    if args.datafile == '-' or args.datafile is None:
        values = read_values(sys.stdin, datatype, args)
    else:
        with open(args.datafile, 'r') as ifile:
            values = read_values(ifile, datatype, args)
    if len(values) == 0:
        print("no values in datafile", file=sys.stderr)
        return 2
    fcn = eval('do_' + args.command)
    rv = fcn(values, args)
    return rv

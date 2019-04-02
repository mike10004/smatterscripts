#!/usr/bin/env python3

"""Program that reads a CSV file and prints text suitable for GNU `sort`."""

import sys
import csv
import errno
from argparse import ArgumentParser


def transform(input_delimiter, output_delimiter, ifile=sys.stdin, ofile=sys.stdout):
    writer = csv.writer(ofile, delimiter=output_delimiter)
    try:
        for row in csv.reader(ifile, delimiter=input_delimiter):
            writer.writerow(row)
    except IOError as e:
        if e.errno != errno.EPIPE:  # broken pipe often means output was piped to `head` or `tail`
            raise
    return 0


def main(argl=None):
    parser = ArgumentParser(description="Transform delimited input to delimited output.", epilog="By default, comma-delimited input is transformed to tab-delimited output suitable for the `sort` command. Use 'TAB' to specify a tab character as argument.")
    parser.add_argument("--input-delimiter", "-i", default=",", help="set input delimiter (default ',')")
    parser.add_argument("--output-delimiter", "-o", default="TAB", help="set output delimiter (default TAB)")
    args = parser.parse_args(argl)
    if args.output_delimiter == 'TAB':
        args.output_delimiter = "\t"
    if args.input_delimiter == 'TAB':
        args.input_delimiter = "\t"
    transform(args.input_delimiter, args.output_delimiter, sys.stdin, sys.stdout)


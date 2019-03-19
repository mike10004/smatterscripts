#!/usr/bin/env python3

"""Program that reads a CSV file and prints text suitable for GNU `sort`."""

import sys
import csv
import errno


def main():
    outdelim = "\t"
    indelim = ","
    ofile = sys.stdout
    try:
        for row in csv.reader(sys.stdin, delimiter=indelim):
            print(outdelim.join(row), file=ofile)
    except IOError as e:
        if e.errno != errno.EPIPE:  # broken pipe often means we passed output to `head` or `tail`
            raise
    return 0

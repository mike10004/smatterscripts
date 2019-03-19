#!/usr/bin/env python3

"""Program that reads a CSV file and prints text suitable for GNU `sort`."""

import sys
import csv

def main():
    outdelim = "\t"
    indelim = ","
    ofile = sys.stdout
    for row in csv.reader(sys.stdin, delimiter=indelim):
        print(outdelim.join(row), file=ofile)
    return 0

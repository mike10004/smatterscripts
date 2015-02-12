#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  makepairslist.py
#  
#  (c) 2015 Mike Chaberski
#  
#  MIT License

import sys
import csv
from argparse import ArgumentParser
import os.path

def make_pairs_list(probelist, gallerylist, args):
    if not os.path.isfile(probelist):
        print >> sys.stderr, "makepairslist: file not found:", probelist
        return 1
    if gallerylist is not None and not os.path.isfile(gallerylist):
        print >> sys.stderr, "makepairslist: file not found:", gallerylist
        return 1
    writer = None
    if args.mode == 'csv':
        writer = csv.writer(sys.stdout)
    n = 0
    if gallerylist is None:
        with open(probelist, 'r') as pfile:
            files = [x.strip() for x in pfile.readlines()]
        for i in xrange(0, len(files)):
            for j in xrange(i+1, len(files)):
                n += 1
                p, g = files[i], files[j]
                _writepg(p, g, args, writer)
    else:
        with open(gallerylist, 'r') as gfile:
            gallery = [g.strip() for g in gfile.readlines()]
        with open(probelist, 'r') as pfile:
            for p in pfile:
                p = p.strip()
                for g in gallery:
                    _writepg(p, g, args, writer)
                    n += 1
    print >> sys.stderr, n, "rows written"
    return 0

def _writepg(p, g, args, writer):
    if args.mode == 'csv':
        writer.writerow([p, g])
    elif args.mode == 'mates':
        print p
        print g
    else:
        raise ValueError("unrecognized mode: " + str(args.mode))

def _convert_input(inputpath, args):
    if args.convert == 'mates':
        with open(inputpath, 'r') as ifile:
            reader = csv.reader(ifile)
            for row in reader:
                print row[0]
                print row[1]
        return 0
    elif args.convert == 'csv':
        with open(inputpath, 'r') as ifile:
            p, g = None, None
            writer = csv.writer(sys.stdout)
            for line in ifile:
                if p is None: p = line.strip()
                elif g is None: 
                    g = line.strip()
                    csv.writerow((p, g))
                    p, g = None, None
        return 0
    else:
        print >> sys.stdout, "invalid convert mode:", args.convert
        return 1

def main():
    parser = ArgumentParser()
    parser.add_argument("probelist", nargs=1)
    parser.add_argument("gallerylist", nargs='?')
    parser.add_argument("--mode", choices=['csv', 'mates'], default='csv')
    parser.add_argument("--convert", choices=['csv', 'mates'], metavar="DESTMODE",
            help="converts a CSV pairs list to a mates file or vice versa")
    args = parser.parse_args()
    probelist = args.probelist[0]
    if args.convert is not None:
        return _convert_input(probelist, args)
    gallerylist = None
    if args.gallerylist is not None:
        gallerylist = args.gallerylist
    return make_pairs_list(probelist, gallerylist, args)

if __name__ == '__main__':
    exit(main())


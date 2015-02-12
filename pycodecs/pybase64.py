#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  pybase64.py
#  
#
#  (c) 2015 Mike Chaberski
#  
#  MIT License

from argparse import ArgumentParser
import base64
import sys, os, os.path
import logging
import md5

_log = logging.getLogger('pyb64')

def writefile(args, outdata, ofile=sys.stdout):
    ofile.write(outdata)

def code_one(args, indata, tocode):
    outdata = tocode(indata)
    _log.debug(" %s: len(output) = %d" % (args.mode, len(outdata)))
    if args.output == '-' or (len(args.pathnames) == 0 and args.output is None): 
        writefile(args, outdata, sys.stdout)
        return 0
    if args.output is None:
        pn = os.path.basename(args.pathnames[0])
        stem, ext = os.path.splitext(pn)
        if ext == ".b64": args.output = stem
        else: args.output = pn + "." + args.mode + "d"
    _log.debug(" writing to %s" % args.output)
    with open(args.output, 'wb') as ofile:
        writefile(args, outdata, ofile)
    if args.verbose and args.mode == 'decode':
        with open(args.output, 'rb') as dfile:
            hasher = md5.new(dfile.read())
            _log.debug(" MD5: %s" % hasher.hexdigest())
    return 0

def encode_all(args):
    decoded = read_from_pathname(args)
    code_one(args, decoded, base64.b64encode)
    return 0

def read_from_pathname(args):
    if len(args.pathnames) == 0:
        stuff = sys.stdin.read()
    else:
        with open(args.pathnames[0], 'rb') as ifile:
            stuff = ifile.read()
    _log.debug(" %s: len(input) = %d" % (args.mode, len(stuff)))
    return stuff

def decode_all(args):
    encoded = read_from_pathname(args)
    code_one(args, encoded, base64.b64decode)
    return 0

def main():
    parser = ArgumentParser()
    parser.add_argument("mode", choices=['encode', 'decode'])
    parser.add_argument("pathnames", nargs="+")
    parser.add_argument("-o", "--output")
    parser.add_argument("-e", "--encoding", default="utf8")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    if args.mode == 'decode':
        return decode_all(args)
    elif args.mode == 'encode':
        return encode_all(args)
    else:
        raise ValueError("mode must be 'decode' or 'encode'")

if __name__ == '__main__':
    exit(main())


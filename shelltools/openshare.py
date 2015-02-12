#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  openshare.py
#  
#  (c) 2015 Mike Chaberski
#  
#  MIT License

from argparse import ArgumentParser
import subprocess
from subprocess import PIPE
import StringIO
from urllib import pathname2url
import sys
import re
import logging

_OPEN_CMD = '/usr/bin/nautilus'
#_OPEN_CMD = '/usr/bin/gnome-open'

def create_cmd(smbpath):
    return [_OPEN_CMD, smbpath]

_loc_pathcomps_pattern = re.compile(r'/([^/]+)')

def translate_location(winpath, args=None):
    smbpath = winpath.replace('\\', '/')
    smbpath = pathname2url(smbpath)
    if args is not None and args.verbose:
        print >> sys.stderr, "smb:" + smbpath
    return "smb:" + smbpath

def open_location(location, args=None):
    smbloc = translate_location(location, args)
    if args is not None and args.verbose: 
        print "opening", smbloc
    cmd = create_cmd(smbloc)
    rv = subprocess.call(cmd, stdout=None, stderr=sys.stderr)
    if rv != 0: 
        print >> sys.stderr, "nautilus returned", rv

def open_locations(locations, args=None):
    for location in locations:
        open_location(location, args)
    return 0

_loc_pattern = re.compile(r'\\\\(?:[^\\]+)\\(?:[^\\]+)(?:\\(?:[^\\]+))*\\?.*$')

def is_valid_location(location):
    if not location.startswith(r'\\'):
        print >> sys.stderr, "invalid:", location, "(does not start with \\\\)"
        return False
    if _loc_pattern.match(location) is None:
        print >> sys.stderr, "invalid:", location
        return False
    return True

def check_locations(locations):
    allgood = True
    for location in locations:
        if not is_valid_location(location):
            allgood=False
    return allgood

def preclean_location(location):
    return location.strip().lower()

def main():
    parser = ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="print details on stdout")
    parser.add_argument("location", nargs="+", help="Windows network addresses")
    args = parser.parse_args()
    args.location = [preclean_location(x) for x in args.location]
    if not check_locations(args.location):
        print >> sys.stderr, "one or more invalid locations in", str(args.location)
        return 1
    return open_locations(args.location, args)

if __name__ == '__main__':
    exit(main())


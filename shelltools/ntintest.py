#!/usr/bin/env python3
#
#  (c) 2015 Mike Chaberski
#  
#  MIT License

from ._common import NullTerminatedInput


def main():
    nti = NullTerminatedInput()
    for line in nti:
        print("[%3d] '%s'" % (len(line),  line))
    return 0




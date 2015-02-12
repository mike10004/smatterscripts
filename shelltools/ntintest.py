#!/usr/bin/env python
#
#  (c) 2015 Mike Chaberski
#  
#  MIT License

import sys
import logging
from _common import NullTerminatedInput

if __name__ == '__main__':
    #logging.basicConfig(level=logging.DEBUG)
    nti = NullTerminatedInput()
    for line in nti:
        print "[%3d] '%s'" % (len(line),  line)

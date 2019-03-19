#!/usr/bin/python
#
#  (c) 2015 Mike Chaberski
#  
#  MIT License

from __future__ import with_statement
import logging
from . import texttools
import sys
import os
from . import _common


_log = logging.getLogger(__name__)


def _parse_args():
    from optparse import OptionParser
    parser = OptionParser(usage="""\n\
    %prog PATHNAME...
Print contents side-by-side for each text file at one or more argument
pathnames. Useful to combine multiple files containing lists of single
values into one CSV file where each column contains the contents of 
one file. Column headers by default are the pathnames. Note that specifying
only one argument pathname is probably pointless.""")
    parser.add_option("-N", "--null", 
                        action="store",
                        metavar="TEXT",
                        help="specify text for null cells")
    parser.add_option("-d", "--delim", 
                    metavar="CHAR",
                    help="set output delimiter to CHAR instead of TAB",
                    action="store")
    #parser.add_option("-s", "--small", action="store_true")
    parser.add_option("-k", "--skip", 
                    action="store",
                    metavar="INTEGER", type='int',
                    help="skip INTEGER header rows in each file")
    parser.add_option("-H", "--noheader",
                    dest="header",
                    action="store_false",
                    help="do not print header row with pathnames in output")
    _common.add_logging_options(parser)
    _common.add_output_option(parser)
    _common.add_sort_option(parser, help="order columns alphabetically " + 
                            "by pathname")
    parser.set_defaults(skip=0, delim='\t', null='None', header=True)
    return parser.parse_args()

def main():
    options, args = _parse_args()
    logging.basicConfig(level=options.log_level)
    inpaths = [os.path.normpath(arg) for arg in args]
    if options.sort: inpaths.sort()
    if options.output is None or options.output is sys.stdout:
        texttools.juxfiles(inpaths, sys.stdout, 
                            delim=options.delim, 
                                skipheaderrows=options.skip, 
                                printheader=options.header)
    else:
        with open(options.output, 'wb') as ofile:
            texttools.juxfiles(inpaths, ofile, 
                                delim=options.delim, 
                                skipheaderrows=options.skip, 
                                printheader=options.header)
    return 0

    

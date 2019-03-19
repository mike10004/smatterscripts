#!/usr/bin/python
#
#  (c) 2015 Mike Chaberski
#  
#  MIT License

from __future__ import print_function
from optparse import OptionParser
from subprocess import Popen, PIPE
import re
from sys import stderr
import logging
#~ IMSIZE_RE = re.compile('\d+x\d+')
#~ FILENAME_RE = re.compile('^\S+')
#~ FILESIZE_RE = re.compile('\S+\s*$')
DEFAULT_DELIM = " "

def clean(filename):
    try:
        garbage = re.findall('\[\d+\]\s*$', filename)[0]
        cleanname = filename[:-len(garbage)]
    except IndexError:
        cleanname = filename
    return cleanname

def main():
    logging.basicConfig(level=logging.DEBUG)
    parser = OptionParser()
    parser.add_option("-s", "--size", 
                    action="store_true",
                    help="print image size WxH only")
    parser.set_defaults(size=False)
    options, args = parser.parse_args()
    idproc = Popen(["identify"] + args, stdout=PIPE)
    delim = DEFAULT_DELIM
    for line in idproc.stdout:
        try:
            #~ imsize = IMSIZE_RE.findall(line)[0]
            #~ filename = FILENAME_RE.findall(line)[0]
            #~ filesize = (FILESIZE_RE.findall(line)[0]).strip()
            tokens = re.split(' ', line.rstrip())
            #~ logging.debug("%d %s", len(tokens), str(tokens))
            props = tokens[-6:]
            #~ logging.debug("props = %s", str(props))
            filename = line.rstrip()[:-len(' '.join(props))]
            imsize = props[1]
            filesize = props[5]
        except IndexError:
            print('line invalidly formatted: ', line.strip(), file=stderr)
        else:
            if options.size:
                print(imsize)
            else:
                print ("%s%s%s%s%s" %
                    (clean(filename), delim, imsize, delim, filesize))
    return 0

#!/usr/bin/python
#
#  (c) 2015 Mike Chaberski
#  
#  MIT License

from optparse import OptionParser
from subprocess import Popen, PIPE
import re
from sys import stderr
import logging
#~ IMSIZE_RE = re.compile('\d+x\d+')
#~ FILENAME_RE = re.compile('^\S+')
#~ FILESIZE_RE = re.compile('\S+\s*$')
DEFAULT_DELIM = " "

_IDENTIFY_FORMAT =  "%i %m %w %h %z %n %k %[size]"
_NUM_PROPS = 7

_FORMAT = 0
_WIDTH = 1
_HEIGHT = 2
_DEPTH = 3
_NUM_SCENES = 4
_UNIQUE_COLORS = 5
_FILE_LENGTH = 6

outs = {'filename': None, 
        '

def clean(filename):
    try:
        garbage = re.findall('\[\d+\]\s*$', filename)[0]
        cleanname = filename[:-len(garbage)]
    except IndexError:
        cleanname = filename
    return cleanname

def outline(filename, props, options):
    objs = list()
    if options.filename:
        objs.append(filename)
    if options.format:
        objs.append(props[_FORMAT])
    if options.size:
        objs.append("%sx%s" % (props[_WIDTH], props[_HEIGHT]))
    if options.num_scenes:
        objs.append("n=%s" % props[_NUM_SCENES])
    if options.unique_colors:
        objs.append("c=%s" % props[_UNIQUE_COLORS])
    if options.length:
        objs.append(props[_FILE_LENGTH])
    return options.delim.join(objs)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    parser = OptionParser()
    parser.add_option("-s", "--size", 
                    action="store_true",
                    help="print image size WxH only")
    parser.add_option("-d", "--delim", action="store",
                    metavar="STR",
                    help="set output delimiter")
    
    parser.set_defaults(size=False)
    options, args = parser.parse_args()
    idproc = Popen(["identify", "-format", _IDENTIFY_FORMAT] + args, 
                    stdout=PIPE)
    delim = DEFAULT_DELIM
    nprops_out = _NUM_PROPS + 1 # num inprops + filename
    for line in idproc.stdout:
        try:
            tokens = re.split(' ', line.rstrip())
            #~ logging.debug("%d %s", len(tokens), str(tokens))
            props = tokens[-_NUM_PROPS:]
            #~ logging.debug("props = %s", str(props))
            filename = line.rstrip()[:-len(' '.join(props))]
        except IndexError:
            print >> stderr, ('invalid output: "%s"' % line.strip())
        else:
            print outline(clean(filename), 
                        props, 
                        options)
    exit(idproc.wait())

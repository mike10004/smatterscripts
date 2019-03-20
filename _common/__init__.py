#!/usr/bin/env python3
#
# module _common
#
#  (c) 2015 Mike Chaberski
#
#  MIT License

import sys
import logging
from argparse import Namespace, ArgumentParser
from typing import TextIO


_log = logging.getLogger(__name__)
_LOG_LEVEL_CHOICES = ('DEBUG', 'INFO', 'WARNING', 'ERROR')
NULLCHAR = "\0"


def parse_args_with_logging(parser: ArgumentParser):
    assert isinstance(parser, ArgumentParser), "expect argparse.ArgumentParser; optparse is no longer supported"
    add_logging_options(parser)
    args = parser.parse_args()
    config_logging(args)
    return args


def config_logging(args: Namespace):
    """Configures logging based on an options object. The options object
    must be one that was created from a parser passed to the
    add_log_level_option function.
    """
    try:
        level = logging.__dict__[args.log_level]
    except KeyError:
        print("_common: error parsing log level", file=sys.stderr)
        level = logging.INFO
    logging.basicConfig(level=level)


def add_logging_options(parser: ArgumentParser):
    """Add log destination and log level options to a parser. The log
    level option sets the log_level attribute of the options object
    returned by parser.parse_args() to a logging.LEVEL value (not a
    string), and has default value logging.INFO.
    """
    # parser.add_argument("-L", "--log-file",
    #                     metavar="FILE",
    #                     help="print log messages to file")
    parser.add_argument("-l", "--log-level", dest="log_level",
                        metavar="LEVEL",
                        default='INFO',
                        help="set log level to one of " + str(_LOG_LEVEL_CHOICES))


def add_output_option(parser: ArgumentParser, shortopt="-o", longopt="--output"):
    """Adds an -o/--output option to a parser with a single string argument.
    """
    parser.add_argument(shortopt, longopt, dest="output", metavar="FILE", help="write output to FILE")


class NullTerminatedInput(object):
    """An iterator over null-terminated lines (terminated by '\0') in
    a file. File must be opened before construction and should be
    closed by the caller afterward.
    """
    # members
    #    log = logging.getLogger('ntinput')
    sizehint = 8 * 1024  # 8k
    ifile = None
    buff = ''

    def __init__(self, ifile: TextIO=sys.stdin):
        """Constructs the object to iterate over null-terminated lines
        in the input file argument.
        """
        self.ifile = ifile

    #        self.log.debug(" initialized with file object: %s",  str(self.ifile))

    def __iter__(self):
        return self

    def readlines(self):
        """Read all lines in the input file and return them as a sequence.
        """
        lines = list()
        for line in self:
            lines.append(line)
        return lines

    def __next__(self):
        busplitpt = self.buff.find(NULLCHAR)
        #        self.log.debug(" current buff split point: %d", busplitpt)
        if busplitpt >= 0:  # then buff contains a null-term char
            nextstr = self.buff[:busplitpt]
            self.buff = self.buff[busplitpt + 1:]
            #            self.log.debug(" len(buff) now %d; returning str with len=%d", len(self.buff), len(nextstr))
            return nextstr
        # invariant: buff contains no null-term chars
        my_bytes = ''
        bysplitpt = -1
        while bysplitpt < 0:
            my_bytes = self.ifile.read(self.sizehint)
            #            self.log.debug(" read %d bytes from file",  len(bytes))
            if len(my_bytes) == 0:
                break  # ...and return what's in buff, or if len(buff)==0 then StopIteration
            self.buff += my_bytes  # implied else: len(bytes) > 0
            bysplitpt = my_bytes.find(NULLCHAR)
        #            self.log.debug(" bysplitpt=%d; len(buff)=%d",  bysplitpt,  len(self.buff))
        # invariant: (bysplitpt >= 0 and len(bytes) > 0) or (len(bytes)==0)
        #        self.log.debug(" post-loop: bysplitpt=%d, len(bytes)=%d",  bysplitpt,  len(bytes))
        if len(my_bytes) == 0:
            if len(self.buff) == 0:
                raise StopIteration()
            else:
                return self.buff
        # invariant: bysplitpt >= 0 and len(my_bytes) > 0
        prevbufflen = len(self.buff) - len(my_bytes)
        nextstr = self.buff[:prevbufflen + bysplitpt]
        self.buff = self.buff[prevbufflen + bysplitpt + 1:]
        #        self.log.debug(" returning str with len=%d; len(buff)=%d",  len(nextstr),  len(self.buff))
        return nextstr

# module _common
#
#  (c) 2015 Mike Chaberski
#  
#  MIT License

import sys
import logging
import argparse


_log = logging.getLogger(__name__)
_LOG_LEVEL_CHOICES=('DEBUG', 'INFO', 'WARNING', 'ERROR')
NULLCHAR = "\0"


def parse_args_with_logging(parser: argparse.ArgumentParser):
    assert isinstance(parser, argparse.ArgumentParser), "expect argparse.ArgumentParser; optparse is no longer supported"
    add_logging_options(parser)
    args = parser.parse_args()
    config_logging(args)
    return args

def add_log_level_option(parser, default_level='INFO'):
    """DEPRECATED: use add_logging_options instead.
    Add a string-based --log-level option to an OptionParser object
    and sets the default level to the argument level (or 'INFO' if none
    is specified).
    """
    parser.add_option("-L", "--log-level", dest="log_level",
                        metavar="LEVEL",
                        choices=_LOG_LEVEL_CHOICES,
                        default=default_level,
                        help="set log level to one of " + str(_LOG_LEVEL_CHOICES))

def config_logging(options):
    """Configures logging based on an options object. The options object
    must be one that was created from a parser passed to the
    add_log_level_option function.
    """
    try:
        level = logging.__dict__[options.log_level]
    except KeyError:
        print("_common: error parsing log level", file=sys.stderr)
        level = logging.INFO
    logging.basicConfig(level=level)

def add_logging_options(parser: argparse.ArgumentParser):
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

def add_output_option(parser, shortopt="-o", longopt="--output"):
    """Adds an -o/--output option to a parser with a single string
    argument.
    """
    parser.add_option(shortopt, longopt, 
                    dest="output",
                    action="store",
                    metavar="FILE",
                    help="write output to FILE")

def add_sort_option(parser, shortopt="-s", longopt="--sort", arg_help="perform sorting"):
    """Adds a -s/--sort option to a parser that stores a True/False
    value in the options.sort attribute."""
    parser.add_option(shortopt, longopt, action="store_true", help=arg_help)


class NullTerminatedInput(object):
    """An iterator over null-terminated lines (terminated by '\0') in
    a file. File must be opened before construction and should be 
    closed by the caller afterward.
    """
    # members
#    log = logging.getLogger('ntinput')
    sizehint = 8 * 1024 # 8k
    ifile = None
    buff = ''
    
    def __init__(self, ifile=sys.stdin):
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
    
    def next(self):
        busplitpt = self.buff.find(NULLCHAR)
#        self.log.debug(" current buff split point: %d", busplitpt)
        if busplitpt >= 0: # then buff contains a null-term char
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
                break # ...and return what's in buff, or if len(buff)==0 then StopIteration
            self.buff += my_bytes # implied else: len(bytes) > 0
            bysplitpt = my_bytes.find(NULLCHAR)
#            self.log.debug(" bysplitpt=%d; len(buff)=%d",  bysplitpt,  len(self.buff))
        # invariant: (bysplitpt >= 0 and len(bytes) > 0) or (len(bytes)==0)
#        self.log.debug(" post-loop: bysplitpt=%d, len(bytes)=%d",  bysplitpt,  len(bytes))
        if len(my_bytes) == 0:
            if len(self.buff) == 0: raise StopIteration()
            else: return self.buff
        # invariant: bysplitpt >= 0 and len(my_bytes) > 0
        prevbufflen = len(self.buff) - len(my_bytes)
        nextstr = self.buff[:prevbufflen + bysplitpt]
        self.buff = self.buff[prevbufflen + bysplitpt + 1:]
#        self.log.debug(" returning str with len=%d; len(buff)=%d",  len(nextstr),  len(self.buff))
        return nextstr

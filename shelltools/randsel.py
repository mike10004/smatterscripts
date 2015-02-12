#!/usr/bin/python
#
#  (c) 2015 Mike Chaberski
#  
#  MIT License

import random
import sys
import logging

from os import linesep
from combinadic import get_random_subset
from _common import NullTerminatedInput
#_LINESEP = linesep

_log = logging.getLogger('randsel')

_DEFAULT_MAX_LINES_PER_FILE=100000



def random_subset(n, k):
    if n < 0: raise ValueError("need a nonnegative number, not n=" + str(n))
    if n == n+1: raise ValueError("overflow on n: " + str(n))
    if k < 0: raise ValueError("need a nonnegative number, not k=" + str(k))
    if k == k+1: raise ValueError("overflow on k: " + str(k))
    if n < k: raise ValueError("n >= k required; %d < %d" % (n, k))
    all = range(n)
    if n == k: return all
    if k == 0: return list()
    some = [None] * k
    for i in xrange(k):
        index = random.randint(0, len(all) - 1)
        some[i] = all[index]
        del all[index]
    return some

def truncate(lines, maxlines=_DEFAULT_MAX_LINES_PER_FILE):
    """Truncate the sequence to the specified number of lines. If the
    maxlines argument is None, the sequence is not truncated.
    """
#    _log.debug("maxlines input: %d", maxlines)
    maxlines = maxlines or len(lines)
    maxlines = min(maxlines, len(lines))
    _log.debug("truncating %d lines to <= %d", len(lines), maxlines)
    return lines[:maxlines]

def load_items(infiles=(sys.stdin,), maxlinesperfile=_DEFAULT_MAX_LINES_PER_FILE,  null_in=False):
    _log.debug("loading <= %d lines from each of %d files (null-term %s)", 
               maxlinesperfile,  len(infiles),  str(null_in))
    item_list = list()
    if null_in:
        infiles = [NullTerminatedInput(infile) for infile in infiles]
    for infile in infiles:
        item_list += truncate(infile.readlines(), maxlinesperfile)
    return item_list

#def print_items(item_list, max_items=1, outfile=sys.stdout, 
#                strip_output=True, delim=linesep):
#    _log.debug("len(item_list) = %s, max_items = %s, outfile = %s", 
#                    len(item_list), max_items, outfile)
#    num_popped = 0
#    list_len = len(item_list)
#    while ((num_popped < max_items) and (list_len > 0)):
#        index = random.randint(0,list_len-1)
#        item = item_list.pop(index)
#        if strip_output:
#            s = item.strip()
#        else:
#            s = item
#        outfile.write(s)
#        outfile.write(delim)
#        num_popped += 1
#        list_len -= 1
#        logging.debug("(%d) popped index %d of %d", 
#                        num_popped, index, list_len)

def parse_args():
    from optparse import OptionParser
    usage = ("""
    %prog [options] [PATHNAME...]
Randomly selects lines from input and prints them to file or standard 
output. By default, a single line is selected and printed. The -a and -n 
options provide control over the amount of output and the selection process.
If no arguments pathnames are provided, input is read from standard input.

One '-' argument meaning 'read from standard input' is permitted, and any 
other '-' arguments are ignored. At most """ + 
    str(_DEFAULT_MAX_LINES_PER_FILE) + """ lines per file are read, 
but the limit on number of files depends on the shell. 

Providing one or more PATHNAME arguments uses input lines aggregated from the
files at the provided pathnames. That is, lines are randomly selected from 
the whole collection of lines in all input files.""")
    parser = OptionParser(usage=usage)
    import _common
    _common.add_log_level_option(parser)
    parser.add_option("-a", "--approx", action="store",
                    metavar="[0.0,1.0)",
                    help="proportion of items to echo " + 
                    "(use instead of -n to avoid reading " + 
                    "all input lines in before printing)",
                    type="float")
    parser.add_option("-o", "--output", action="store", metavar="PATHNAME",
                    help="Print lines to file at PATHNAME." +
                    "Use - to print to standard output (or omit option).")
    parser.add_option("-n", "--num-items", action="store", metavar="INTEGER",
                        dest="num_items", type="int",
                        help="Number of lines to print. Default is 1." + 
                        " Program exits successfully after printing INTEGER "+ 
                        "items or reaching end of input.")
    parser.add_option("-N", "--input-lines", 
                    action="store", type="int", metavar="INTEGER",
                    help="with -n, choose from only the first INTEGER lines "+
                    "in each " + 
                    "input file; default is " + 
                    str(_DEFAULT_MAX_LINES_PER_FILE))
    parser.add_option("-S", "--unsorted",
                    help="do not (necessarily) print output items in the " + 
                    "order they came in",
                    action="store_false",
                    dest="sorted")
    parser.add_option("--null-out",
                    help="print items null-terminated",
                    action="store_const",
                    dest="outdelim",
                    const="\0")
    parser.add_option("--null-in",
                    help="read null-terminated input items",
                    action="store_true",
                    dest="null_in")
    parser.add_option("-0", "--null-term",
                    help="like both --null-in and --null-out",
                    action="store_true",
                    dest="null_term")
##    parser.add_option("-M", "--log-mode", action="store",
##                    metavar="(w|a)",
##                    dest="log_mode",
##                    help="Log file write mode: w=write, a=append")
##    parser.add_option("-D", "--log_dest", action="store", metavar="PATHNAME",
##                    dest="log_dest",
##                    help="Log file destination (default is stderr)")
    parser.set_defaults(num_items=1, 
                        #null_term=False, 
                        #delim=linesep,
                        sorted=True,
                        outdelim=linesep,
                        input_lines=_DEFAULT_MAX_LINES_PER_FILE,
                        null_in=False,
                        null_term=False
                        )
    options, args = parser.parse_args()
    if options.null_in and options.outdelim == '\0':
        options.null_term = True
    if options.null_term:
        options.null_in = True
        options.outdelim = '\0'
    return options, args

def _cleanup(ofile, ifiles):
    for ifile in ifiles:
        ifile.__exit__()
    ofile.__exit__()

def printline(ofile=sys.stdout, line=None, delim=linesep, strip=True):
    if line is not None: 
        if strip:
            ofile.write(line.strip())
        else:
            ofile.write(line)
    ofile.write(linesep)

if __name__ == '__main__':
    _log.debug("args: %s", sys.argv)
    options, args = parse_args()
    logging.basicConfig(level=eval('logging.' + options.log_level))
    _log.debug("parsed options: %s", options)
    if options.output:
        raise NotImplementedError('not yet implemented')
    strip = (options.outdelim != '\0')
    _log.debug("args: %s", str(args))
    ipaths = [p for p in args]
    ifiles = list()
    stdinarg = False
    for i in xrange(len(ipaths)):
        if ipaths[i] == '-' and not stdinarg:
            ifiles.append(sys.stdin)
            _log.debug("input file %d is stdin", i)
        elif ipaths[i] != '-':
            ifiles.append(open(ipaths[i], 'rb'))
    if len(ifiles) == 0: ifiles.append(sys.stdin)
    _log.debug("%d input files open; beginning selection...", len(ifiles))
    try:
        if options.output == '_' or options.output is None:
            ofile = sys.stdout
        else:
            ofile = open(options.output, 'w')
        if options.approx is not None:
            _log.debug("in approximate mode, p=%.4f", float(options.approx))
            for i in xrange(len(ifiles)):
                ifile = ifiles[i]
                if null_in: ifile = NullTerminatedInput(ifile)
                _log.debug("scanning input file %d...", i)
                for line in ifile:
                    if random.random() < options.approx:
                        printline(ofile, line, options.outdelim, strip)
                _log.debug("done scanning input file %d", i)
        else:
            item_list = load_items(ifiles, options.input_lines, options.null_in)
            nitems = len(item_list)
            _log.debug("loaded %d items", nitems)
            k = min(nitems, options.num_items)
            if k != options.num_items:
                _log.info(" num items to select reduced to %d", k)
            isubset = random_subset(nitems, k)
            if options.sorted: isubset.sort()
            _log.debug("got random subset of %d items", len(isubset))
            for i in xrange(len(isubset)):
                printline(ofile, item_list[isubset[i]], options.outdelim, strip)
        _log.debug("closing all i/o files")
        if ofile != sys.stdin: ofile.close()
        for ifile in ifiles: 
            if ifile != sys.stdin: ifile.close()
        _log.debug("mission accomplished")
    except:
        _log.info("closing all file handles due to exception")
        _cleanup(ofile, ifiles)
        raise

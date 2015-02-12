#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  graybmpify.py
#  
#
#  (c) 2015 Mike Chaberski
#  
#  MIT License

from PIL import Image
from optparse import OptionParser
import tempfile
import os
import os.path
import logging
import platform
import shutil
import sys
from StringIO import StringIO

_log = logging.getLogger('graypngify')

ERR_OUTFILE_EXISTS = 200
ERR_SOME_ERRORS = 255
ERR_IO = 201
ERR_UNDEFINED = 202

_LOG_LEVEL_CHOICES=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'),

def parse_args_with_logging(parser):
    add_logging_options(parser)
    options, args = parser.parse_args()
    config_logging(options)
    return options, args

def config_logging(options):
    """Configures logging based on an options object. The options object
    must be one that was created from a parser passed to the
    add_log_level_option function.
    """
    logging.basicConfig(logfile=options.logfile, level=options.log_level)    

def add_logging_options(parser):
    """Add log destination and log level options to a parser. The log 
    level option sets the log_level attribute of the options object
    returned by parser.parse_args() to a logging.LEVEL value (not a 
    string), and has default value logging.INFO.
    """
    parser.add_option("-L", "--logfile", dest="logfile",
                        metavar="PATHNAME",
                        action="store",
                        help="print log messages to specified file instead" + 
                        " of standard error")
    parser.add_option("-l", "--log-level", dest="log_level",
                        metavar="LEVEL",
                        nargs=1,
                        action="callback",
                        type="str",
                        callback=_eval_level,
                        help="set log level to one of " + 
                            str(_LOG_LEVEL_CHOICES))
    parser.set_defaults(log_level=logging.INFO)

def _eval_level(option, opt_str, value, parser):
    parser.values.log_level = eval('logging.' + value)

def add_output_option(parser, shortopt="-o", longopt="--output"):
    """Adds an -o/--output option to a parser with a single string
    argument.
    """
    parser.add_option(shortopt, longopt, 
                    dest="output",
                    action="store",
                    metavar="PATHNAME",
                    help="write output to PATHNAME")


def write_image(im, pathname, options=None):
    outname = options.output
    if outname == '-':
        savebmp(im, sys.stdout)
    else:
        _log.debug(" output filename: %s" % options.output)
        fd, tmpname = tempfile.mkstemp(".png", 
                prefix=os.path.splitext(os.path.basename(pathname))[0], 
                dir=os.path.dirname(pathname))
        with os.fdopen(fd, 'w') as ofile:
            savebmp(im, ofile)
        if options.no_clobber is True and os.path.isfile(outname):
            _log.info(" not overwriting " + outname)
            os.remove(tmpname)
            return ERR_OUTFILE_EXISTS
        if not options.no_clobber and platform.system() == 'Windows' and os.path.exists(outname):
            os.remove(outname) # fails on directories, appropriately
        shutil.move(tmpname, outname)
        if pathname != '-': shutil.copymode(pathname, outname)
        _log.debug(" wrote to %s" % outname)
    return 0

def get_im_props(im):
    return ("Image{format=%s,mode=%s,size=%s}" %
            (im.format, im.mode, im.size))

def savebmp(im, f):
    im.save(f, 'png', mode='L')

def togray(im):
    oldmode = im.mode
    im = im.convert('L')
    _log.debug(" converted from %s to %s", oldmode, im.mode)
    return im

def main():
    parser = OptionParser(usage="""
    %prog [options] IMAGE [IMAGE...]
where IMAGE is the pathname of an image file or - to use standard input. 
Output filename is by default the input filename plus .bmp suffix, unless the
input is standard input, in which case output is written to standard output.
Exit code is zero on success, nonzero on failure. If multiple input files are
provided, the exit code is 255 when more than one fails, or the original 
error code if only one fails.""")
    parser.add_option("-n", "--no-clobber", action="store_true", 
            help="do not overwrite output file")
    parser.add_option("-o", "--output", 
            help="write output image to PATHNAME (use - for " 
            + "stdout); instances of %F will be replaced by input " 
            + "filename", metavar="PATHNAME")
    parser.add_option("-s", "--swap-extension", action="store_true",
            help="swap input filename extension for .bmp (instead " 
            + "of appending)")
    options, args = parse_args_with_logging(parser)
    if len(args) < 1: parser.error("must specify input file(s)")
    if len(args) > 1:
        if options.output is not None and options.output.find('%F') != -1:
            parser.error("if multiple input files are provided, " + 
            "--output must contain %F placeholder for input filename")
    status = 0
    for pathname in args:
        ret = ERR_UNDEFINED
        tmpinfile = None
        try:
            if pathname == '-': 
                fd, tmpinfile = tempfile.mkstemp()
                with os.fdopen(fd, 'w') as ofile:
                    ofile.write(sys.stdin.read())
                im = Image.open(tmpinfile)
                if options.output is None:
                    options.output = "-"
            else: im = Image.open(pathname)
            im.draft('L', im.size)
            _log.debug(" input = %s; %s" % (pathname, get_im_props(im)))
            if im.mode != 'L': im = togray(im)
            if options.output is None:
                if options.swap_extension is True:
                    options.output = os.path.splitext(pathname)[0] + ".png"
                else: 
                    options.output = pathname + ".png"
            elif options.output != '-':
                options.output = options.output.replace("%F", pathname)
            ret = write_image(im, pathname, options)
        except IOError as ioe:
            _log.info(" IOError on %s: %s" % (pathname, ioe))
            ret = ERR_IO
        finally:
            if tmpinfile is not None: os.remove(tmpinfile)
        if ret != 0: 
            if status == 0: status = ret
            else: status = ERR_SOME_ERRORS
    return status

if __name__ == '__main__':
    exit(main())


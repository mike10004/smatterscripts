#!/usr/bin/env python
#
#  (c) 2015 Mike Chaberski
#  
#  MIT License

from __future__ import with_statement
import os
import subprocess
import platform
import sys
import logging

_log = logging.getLogger('immag')

_CONVERT_EXECUTABLE_LINUX = 'convert'
_CONVERT_EXECUTABLE_WINDOWS = 'imconvert.exe'
_USE_FULL_EXEC_PATH = True

_CONVEXEC_MAP = { 'Linux': _CONVERT_EXECUTABLE_LINUX,
		'Windows': _CONVERT_EXECUTABLE_WINDOWS }

(_system, _nodename, _release, _version, _machine, _processor) = platform.uname()

class NonzeroExitError(Exception):
    pass

 
def find_executable(executable, path=None):
    """Try to find 'executable' in the directories listed in 'path' (a
    string listing directories separated by 'os.pathsep'; defaults to
    os.environ['PATH']).  Returns the complete filename or None if not
    found
    """
    if path is None:
        path = os.environ['PATH']
    paths = path.split(os.pathsep)
    extlist = ['']
    if os.name == 'os2':
        (base, ext) = os.path.splitext(executable)
        # executable files on OS/2 can have an arbitrary extension, but
        # .exe is automatically appended if no dot is present in the name
        if not ext:
            executable = executable + ".exe"
    elif sys.platform == 'win32':
        pathext = os.environ['PATHEXT'].lower().split(os.pathsep)
        (base, ext) = os.path.splitext(executable)
        if ext.lower() not in pathext:
            extlist = pathext
    for ext in extlist:
        execname = executable + ext
        if os.path.isfile(execname):
            return execname
        else:
            for p in paths:
                f = os.path.join(p, execname)
                if os.path.isfile(f):
                    return f
    else:
        return None


def put_density(inpath, outpath, density, convexec, units='PixelsPerInch'
                ):
    args = (
            convexec, 
                inpath, 
                    '-density', str(density),
                    '-units', units,
                outpath
            )
##    _log.debug("exec: %s", ' '.join(args))
##    retcode = subprocess.call(' '.join(args), executable=convexec)
    _log.debug("exec: %s", str(args))
    retcode = subprocess.call(args, executable=convexec)
    if retcode != 0:
        raise NonzeroExitError("returned %d" % retcode)

def _parse_args():
    from optparse import OptionParser
    parser = OptionParser(usage="""
    (1) %prog [options] PATHNAME DENSITY
    (2) %prog [options] -f PATHNAME DENSITY
where DENSITY is the new density and in the first case, PATHNAME is the 
image to convert, and in the second case, PATHNAME is a text file containing
one image pathname per line. By default, the file at PATHNAME is overwritten 
with the new file. 

Examples:
    %prog myimage.png 500
    %prog --units PixelsPerCentimeter myimage.bmp 196.85
    %prog input.jpg 72 output.jpg
    %prog -f filelist.txt 96
    find . -type f -name "*.png" | %prog --file - 300"""
)
    parser.add_option("-f", "--file", metavar="PATHNAME",
            help="read pathnames from file at PATHNAME; use - for stdin",
            action="store_true")
    parser.add_option("-o", "--output", metavar="PATHNAME",
            help="write output to new file at PATHNAME",
            action="store")
    parser.add_option("-u", "--units", metavar="UNITS",
            help="set density units to UNITS, e.g. PixelsPerCentimeter, " +
            "instead of default (PixelsPerInch)",
            action="store")
    parser.add_option("--level", metavar="LEVEL",
            help="set log level to LEVEL", action="store")
    parser.set_defaults(units="PixelsPerInch", file=False, level='INFO'
            )
    options, args = parser.parse_args()
    if len(args) != 2: parser.error("Invalid number of args; must be 2")
    if options.file and options.output is not None:
        parser.error("Conflict: --file and --output would write all output" + 
                    " files to the same pathname")
    return options, args
    

def main():
    options, args = _parse_args()
    logging.basicConfig(level=eval('logging.'+options.level))
    if _USE_FULL_EXEC_PATH:
        convexec = find_executable(_CONVEXEC_MAP[_system])
    else:
        convexec = _CONVEXEC_MAP[_system]
    _log.debug("using convert executable: %s", convexec)
    inpath, density = args[0], args[1]
    units = options.units
    if options.file:
        try:
            if inpath == '-':
                ifile = sys.stdin
            else:
                ifile = open(inpath, 'rt')
            for line in ifile:
                pathname = line.strip()
                put_density(pathname, pathname, 
                            density, convexec, units)
        except IOError:
            ifile.close()
            raise
    else:
        if options.output is None: outpath = inpath
        else: outpath = options.output
        put_density(inpath, outpath, density, convexec, units)
    return 0

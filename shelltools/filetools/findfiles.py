#!/usr/bin/python3
#
#  (c) 2015 Mike Chaberski
#  
#  MIT License

import sys
import os
import logging

LOG_FILENAME = '/tmp/py-findfiles.log'

def print_pathnames(topdir=os.getcwd(), outfile=sys.stdout, recursive=True, dry_run=False):
    logging.debug("print_pathnames: topdir=%s, outfile=%s (%s), recursive=%s, dry_run=%s", topdir, outfile, os.path.abspath(outfile.name), recursive, dry_run)
    if not dry_run:
        for root, dirs, files in os.walk(topdir):
            for filename in files:
                if filename[0] != '.':
                    print(os.path.join(root, filename), file=outfile)
            if recursive:
                for subdir in dirs:
                    print_pathnames(subdir, outfile)


def parse_args():
    """ Parses command line arguments to script.
    
    Syntax allows (non-option) argument constructions:
            (no args)
                 - output directed to stdout unless otherwise specified
                 - current directory as top unless otherwise specified
            "pathname"
                 - if pathname exists and is a directory, it is assigned to topdir
                    and output directed to stdout
                 - if pathname exists and is a file, it is overwritten as outpathname
                    and current directory assigned to topdir
                 - if pathname does not exist, it is created and written to as outpathname
                    and current directory assigned to topdir
            "pathname1 pathname2"
                 - if pathname1 exists and is a directory, it is assigned to topdir and
                     - if pathname2 does not exist or is an existing file, it 
                        is (over)written to as outputhname
                     - if pathname2 exists and is a directory, usage error raised
                 - if pathname1 exists and is a file, it is assigned to outpathname, and
                     - if pathname2 exists and is a directory, it is assigned to topdir
                     - if pathname2 does not exist or exists and is a file, usage error is raised
                 - if pathname1 does not exist, it is assigned to outpathname and
                     - if pathname2 does not exist or exists and is a file, usage error is raised
                     - if pathname2 exists and is a directory, it is assigned to topdir
    """
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-o", "--output", dest="outpathname", metavar="FILE")
    parser.add_option("-t", "--top", dest="topdir", metavar="DIR")
    #parser.add_option("-p", "--pattern", dest="pattern", metavar="PATTERN")
    parser.add_option("-s", "--non-recursive", dest="recursive", action="store_false")
    parser.add_option("-r", "--recursive", dest="recursive", action="store_true")
    #parser.add_option("-a", "--append", dest="write_mode", action="store_const", const='a')
    parser.add_option("-d", "--dry-run", dest="dry_run", action="store_true")
    
    #parser.set_defaults(recursive=True, topdir=os.getcwd(), write_mode='w', dry_run=False);
    parser.set_defaults(recursive=True, topdir=os.getcwd(), dry_run=False)
    (options, args) = parser.parse_args()
    
    if len(args) == 0:
        pass
    elif len(args) == 1:
        if os.path.isdir(args[0]):
            options.topdir = args[0]
        elif os.path.isfile(args[0]) or os.path.exists(args[0]) == False:
            options.outpathname = args[0]
        else:
            assert False, "pathname must be non-existent, file, or dir; what happened?"
    elif len(args) == 2:
        pathname1 = args[0]
        pathname2 = args[1]
        if os.path.isdir(pathname1):
            options.topdir = pathname1
            if (os.path.exists(pathname2) == False) or os.path.isfile(pathname2):
                options.outpathname = pathname2
            else:
                parser.error("invalid argument: " + pathname2 + " must not be a directory")
        elif os.path.isfile(pathname1):
            options.outpathname = pathname1
            if os.path.isdir(pathname2):
                options.topdir = pathname2
            else:
                parser.error("invalid argument: " + pathname2 + " (should be a directory)")
        elif not os.path.exists(pathname1):
            options.outpathname = pathname1
            if os.path.isdir(pathname2):
                options.topdir = pathname2
            else:
                parser.error("invalid argument: " + pathname2 + " (should be a directory)")
        else:
            assert False, "pathname must be non-existent, file, or dir; what happened?"
    else:
        parser.error("invalid syntax -- too many args")
    
    #if options.outpathname:
    #    outfile = open(options.outpathname, options.write_mode)
    
    return options

def main():
    logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG, filemode='w',)
    logging.debug("args: %s", sys.argv)
    options = parse_args()
    if options.outpathname:
        outfile = open(options.outpathname, 'w')
    else:
        outfile = sys.stdout
    print_pathnames(options.topdir, outfile, options.recursive, options.dry_run)
    if outfile != sys.stdout:
        outfile.close()
    return 0



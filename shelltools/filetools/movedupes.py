#!/usr/bin/python3
#
#  (c) 2015 Mike Chaberski
#  
#  MIT License

from __future__ import print_function
from __future__ import with_statement
import sys
import tempfile
import logging
from . import findfiles
from . import getdupes
from . import hashall
from . import movefiles
import os

def parse_args():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("src_dir")
    parser.add_argument("dst_dir")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true")
    args = parser.parse_args()
    srcdir = args.src_dir
    destdir = args.dst_dir
    return args, srcdir, destdir

def main():
    logging.basicConfig(filename='/tmp/py-movedupes.log', level=logging.DEBUG, filemode='w',)
    logging.debug("args: %s", sys.argv)
    
    options, srcdir, destdir = parse_args()
    
    pathnames_fd, pathnames_file_pathname = tempfile.mkstemp(text=True)
    with os.fdopen(pathnames_fd, 'w') as pathnames_file:
        logging.debug("pathnames file pathname: %s", pathnames_file_pathname)
        findfiles.print_pathnames(topdir=srcdir, outfile=pathnames_file)
    logging.debug("pathnames file stat: %s", os.stat(pathnames_file_pathname))
    
    hashes_fd, hashes_file_pathname = tempfile.mkstemp(text=True)
    logging.debug("hashes file pathname: %s", hashes_file_pathname)
    with open(pathnames_file_pathname, 'r') as pathnames_file:
        with os.fdopen(hashes_fd, 'w') as hashes_file:
            hashall.print_hashes(pathnamelistfile=pathnames_file, hashesfile=hashes_file)
    logging.debug("hashes file stat: %s", os.stat(hashes_file_pathname))
    
    hashtuples = None
    with open(hashes_file_pathname, 'r') as hashes_file:
        hashtuples = getdupes.get_hash_tuples(hashes_file)
    hashtuples.sort()
    dupes = getdupes.get_dupes_list(hashtuples)
    movefiles.move_files(dupepathnames=dupes, newroot=destdir)
    return 0
    


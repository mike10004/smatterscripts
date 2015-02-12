#!/usr/bin/python
#
#  (c) 2015 Mike Chaberski
#  
#  MIT License

from __future__ import with_statement
import sys
import tempfile
import logging
import findfiles
import getdupes
import hashall
import movefiles
import os

def parse_args():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-v", "--verbose",
                    dest="verbose", action="store_true")
    parser.set_defaults(verbose=False)
    
    (options, args) = parser.parse_args()
    
    if len(args) != 2:
        parser.error("Invalid syntax: two arguments required")
    srcdir = args[0]
    destdir = args[1]
    
    return options, srcdir, destdir

if __name__ == '__main__':
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
    
    #with open(pathnames_file.name, 'r') as pathnames_file:
    #    for line in pathnames_file:
    #        print line

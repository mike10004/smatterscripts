#!/usr/bin/python3
#
#  (c) 2015 Mike Chaberski
#  
#  MIT License

from __future__ import print_function
from __future__ import with_statement
import os
import sys
import hashlib
import logging
from optparse import OptionParser

LOG_FILENAME='/tmp/py-hashall.log'
CHUNK_LENGTH = 1024 * 1024

def print_hashes(pathnamelistfile=sys.stdin, hashesfile=sys.stdout, hashtype='md5', silent_on_errors=False):
	logging.debug( "computing hashes for all files listed in %s", pathnamelistfile)
	for line in pathnamelistfile:
		pathname = os.path.normpath(line.strip())
		if os.path.isfile(pathname):
			the_hash = hashlib.new(hashtype)
			with open(pathname, 'rb') as f:
				chunk = 'tmp'
				while chunk != '':
					chunk = f.read(CHUNK_LENGTH)
					the_hash.update(chunk)
			print(the_hash.hexdigest(), pathname, file=hashesfile)
		elif not silent_on_errors:
			print('pathname is not a file', pathname, file=sys.stderr)

def parse_args():
	parser = OptionParser()
	parser.add_option("-f", "--filelist",
					dest="filelist_pathname", metavar="PATHNAME")
	parser.add_option("-o", "--output",
					dest="out_pathname", metavar="PATHNAME")
	parser.add_option("-q", "--quiet",
					dest="silent_on_errors", action="store_true")
	parser.add_option("-H", "--hash",
					dest="hashtype", action="store", metavar="ALGORITHM")
	# future: add -a option to append to hashlist
	parser.set_defaults(silent_on_errors=False,hashtype='md5');
	(options, args) = parser.parse_args()
	return options

def main():
	logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG, filemode='w',)
	options = parse_args()

	filelist_file = sys.stdin
	hashesfile = sys.stdout

	if options.filelist_pathname is not None:
		filelist_file = open(options.filelist_pathname, 'r')
	if options.out_pathname is not None:
		hashesfile = open(options.out_pathname, 'w')

	print_hashes(filelist_file,
					hashesfile,
					hashtype=options.hashtype,
					silent_on_errors=options.silent_on_errors)
	if filelist_file != sys.stdin:
		filelist_file.close()
	if hashesfile != sys.stdout:
		hashesfile.close()
	return 0


if __name__ == '__main__':
	exit(main())
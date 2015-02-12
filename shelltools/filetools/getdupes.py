#!/usr/bin/python
#
#  (c) 2015 Mike Chaberski
#  
#  MIT License

from __future__ import with_statement
import sys
import re
import logging
import dm_common
import tempfile
import os

LOG_FILENAME='/tmp/py-getdupes.log'


TUPLE_HASHCODE_INDEX = 0
TUPLE_PATHNAME_INDEX = 1
# Sets the buffer limit for how many hashcode-pathname tuples
# are loaded into memory to be sorted.
# The check for buffer size could be optimized by `wc -l`ing 
# the file before actually loading the tuples.
DEFAULT_BUFFER_SIZE = 10000

SEARCH_MODES = {'auto':0, 'sort':1, 'brute':2}
BRUTE_SEARCH_MODE = SEARCH_MODES['brute']
AUTO_SEARCH_MODE = SEARCH_MODES['auto']
SORT_SEARCH_MODE = SEARCH_MODES['sort']

def extract_pathname(digest_file_line, stripped_code_len, normpath=False):
    logging.debug("extracting pathname from '%s'[%d:]", 
                digest_file_line.strip(), stripped_code_len)
    pathname = digest_file_line[stripped_code_len:]
    pathname = pathname.strip()
    # for binary files as listed in sha1sum output:
    pathname = pathname.strip('*') 
    if normpath:
        pathname = os.path.normpath(pathname)    
    return pathname

def parse_hash_tuple(digest_file_line, normpath=False):
    code = re.search("\A\w+\s", digest_file_line).group(0)
    #logging.debug("matched hex digest '%s'", code)
    pathname = extract_pathname(digest_file_line, len(code.strip()), normpath)
    return (code, pathname)
    
def load_hash_tuples(hashes_file=sys.stdin, normpath=False):
    hashtuples = []
    for line in hashes_file:
        hashtuple = parse_hash_tuple(line, normpath)
        logging.debug("parsed tuple: %s", hashtuple)
        hashtuples.append(hashtuple)
        assert len(hashtuples) < DEFAULT_BUFFER_SIZE, \
                ("Buffer limit reached; increase buffer in getdupes" +
                "module or limit file set")
    logging.debug('returning %s hash tuples', len(hashtuples))
    return hashtuples

def scan_rest_of_file(infile, query_tuple, outfile, normpath=False):
    logging.debug('scanning %s for matches to %s', infile, query_tuple)
    for line in infile:
        if re.match(query_tuple[TUPLE_HASHCODE_INDEX], line):
            dupe_code = re.search(query_tuple[TUPLE_HASHCODE_INDEX], 
                        line).group(0).strip()
            pathname = extract_pathname(line, len(dupe_code), normpath)
            if pathname != query_tuple[TUPLE_PATHNAME_INDEX]:
                print >> outfile, pathname  

def print_matches_for_line(hashes_file_pathname, start_line=0, 
                dupes_file=sys.stdout, normpath=False):
    line_index = 0
    query_tuple = None
    with open(hashes_file_pathname, 'r') as hashes_file:
        for line_index in range(0, start_line - 1):
            hashes_file.readline()  # skip line
        # read line
        query_tuple = parse_hash_tuple(hashes_file.readline(), normpath)
        scan_rest_of_file(hashes_file, query_tuple, dupes_file, normpath)

def count_lines(text_file_pathname):
    num_lines = 0
    with open(text_file_pathname, 'r') as f:
        for line in f:
            num_lines += 1
    return num_lines
    
def print_matches(hashes_file_pathname, num_lines, dupes_file, normpath=False):
    logging.debug('in brute mode, printing matches in hashcodes from %s' + 
                ' with %d lines to %s (normpath=%s)',
                hashes_file_pathname, num_lines, dupes_file, normpath)
    for start_line in range(0, num_lines):
        print_matches_for_line(hashes_file_pathname,
                                start_line,
                                dupes_file)

def print_dupes_list(sorted_hashtuples, outfile=sys.stdout):
    logging.debug('printing dupes list for %d hashtuples to %s', 
                len(sorted_hashtuples), outfile)
    # stop at last index minus 1
    for i in range(0, len(sorted_hashtuples)-2):
        if (sorted_hashtuples[i][TUPLE_HASHCODE_INDEX] == 
            sorted_hashtuples[i+1][TUPLE_HASHCODE_INDEX]):
            print >> outfile, sorted_hashtuples[i][TUPLE_PATHNAME_INDEX]

def parse_args():
    from optparse import OptionParser
    parser = OptionParser()
    #parser.add_option("-m", "--mac-osx", 
    #                dest="mac_input", action="store_true")
    parser.add_option("-f", "--file", 
                    metavar="PATHNAME", dest="hashes_file_pathname")
    parser.add_option("-o", "--output", 
                    metavar="PATHNAME", dest="dupes_file_pathname")
    parser.add_option("-s", "--sort-mode", dest="search_mode",
                    action="store_const", const=SORT_SEARCH_MODE)
    parser.add_option("-b", "--brute-mode", dest="search_mode",
                    action="store_const", const=BRUTE_SEARCH_MODE)
    parser.add_option("-A", "--auto-mode", dest="search_mode",
                    action="store_const", const=AUTO_SEARCH_MODE)
    parser.add_option("-z", "--buffer-size", dest="buffer_size",
                    action="store")
    parser.set_defaults(search_mode=AUTO_SEARCH_MODE, 
                        buffer_size=DEFAULT_BUFFER_SIZE)
    
    (options, args) = parser.parse_args()
    #print options
    if len(args) > 2:
        parser.error("max num args: 2")
#    assert options.mac_input == False, "OSX openssl-style input not supported"
    return options

def execute_sort_search(hashes_file_pathname=None, dupes_file=sys.stdout):
    if options.hashes_file_pathname:
        hashes_file = open(options.hashes_file_pathname, 'r')
    else:
        hashes_file = sys.stdin
    hash_tuples = load_hash_tuples(hashes_file)
    dm_common.safe_close_input(hashes_file)
    
    logging.debug('loaded %d hash tuples', len(hash_tuples))
    hash_tuples.sort()
    print_dupes_list(hash_tuples, outfile=dupes_file)
    

def execute_search(hashes_file_pathname=None, num_lines=-1,
                    dupes_file_pathname=None, 
                    search_mode=BRUTE_SEARCH_MODE):
    assert search_mode == BRUTE_SEARCH_MODE or search_mode == SORT_SEARCH_MODE
    logging.debug('executing search; in=%s num_lines=%d, out=%s, mode=%s',
                    hashes_file_pathname, num_lines,
                    dupes_file_pathname, search_mode)
                    
    if options.dupes_file_pathname:
        dupes_file = open(options.dupes_file_pathname, 'w')
    else:
        dupes_file = sys.stdout
    logging.debug("printing to %s", dupes_file)
    
    if search_mode == SORT_SEARCH_MODE:
        execute_sort_search(hashes_file_pathname, dupes_file)
    else:
        assert hashes_file_pathname
        assert num_lines >= 0
        print_matches(hashes_file_pathname, num_lines, dupes_file, normpath=False)
    dm_common.safe_close_output(dupes_file)


if __name__ == '__main__':
    logging.basicConfig(filename=LOG_FILENAME, 
                        level=logging.DEBUG, 
                        filemode='w',)
    options = parse_args()
    logging.debug('parsed options: %s', options)
    
    num_lines = 0
    if (options.search_mode == AUTO_SEARCH_MODE):
        # Count lines to determine best search mode.
        # If input is stdin, must write temp file from stdin
        if options.hashes_file_pathname is None:
            hashes_file_desc, hashes_file_pathname = tempfile.mkstemp(text=True)
            with os.fdopen(hashes_file_desc, 'w') as hashes_file:
                logging.debug('created temp file %s at %s', 
                            hashes_file, os.path.abspath(hashes_file_pathname))
                for line in sys.stdin:
                    print >> hashes_file, line,
                    num_lines += 1
            options.hashes_file_pathname = hashes_file_pathname
        else:
            num_lines = count_lines(options.hashes_file_pathname)
        logging.debug('num_lines = %d', num_lines)
        if num_lines > DEFAULT_BUFFER_SIZE:
            options.search_mode = BRUTE_SEARCH_MODE
        else:
            options.search_mode = SORT_SEARCH_MODE
    
    execute_search(hashes_file_pathname=options.hashes_file_pathname, 
                    num_lines=num_lines, 
                    dupes_file_pathname=options.dupes_file_pathname,
                    search_mode=options.search_mode)

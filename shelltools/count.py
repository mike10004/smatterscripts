#!/usr/bin/python3

import os
from glob import glob

def countmatches(patterns, asdirs=False):
    subtotals = [0] * len(patterns)
    for i in range(len(patterns)): #pattern in patterns:
        pattern = patterns[i]
        if os.path.isdir(pattern):
            if asdirs: subtotals[i] += len(os.listdir(pattern))
            else: subtotals[i] += 1
        else:
            subtotals[i] += len(glob(pattern))
    return subtotals

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser(usage="""
    %prog [OPTIONS] PATTERN...
Prints the number of file and directories that match the patterns provided as
arguments. Patterns are UNIX-style globbing patterns, where * matches zero or 
more characters and ? matches a single character. 

Examples:
    count "*.txt"
    count -d /tmp
    
Note that the shell may expand unquoted patterns before passing them as 
arguments. This may have no effect on the output, if the number of matching 
files and directories is small, but if a large number of files or directories 
match, the count may be incorrect or performance can suffer. For instance,
on some systems, before executing
    count *.txt 
the shell would convert the *.txt to the filenames of all files in the current
working directory that match the pattern. Some shells place limits on the 
number of arguments that can be passed to a program, and either crap out
or truncate the argument list. To be safe, quote the pattern as shown in the
first example.""")
    parser.add_option("-d", "--dir", action="store_true",
        help="in each directory specified " + 
        "by a PATTERN argument, non-recursively count the files and " + 
        "directories it contains instead of the argument itself")
    parser.add_option("-a", "--args", action="store_true",
            help="print argument(s) one tab space after count")
    parser.add_option("-i", "--indiv", action="store_true",
            help="print subtotals for each argument")
    parser.set_defaults(dir=False, args=False)
    options, args = parser.parse_args()
    subtotals = countmatches(args, options.dir)
    if options.indiv:
        for i in range(len(args)):
            print(subtotals[i], end=' ')
            if options.args:
                print("\t%s" % args[i])
            else:
                print()
    print(sum(subtotals), end=' ')  # do not end line yet
    if options.args:
        print('\tTotal')  # end line
    else:
        print()

#!/usr/bin/env python
#
#  (c) 2015 Mike Chaberski
#  
#  MIT License

from __future__ import with_statement
import logging
import csv
import texttools

_log = logging.getLogger('texttools')

def _parse_args():
    from optparse import OptionParser
    parser = OptionParser(usage="""
    %prog [options] PATHNAME1 PATHNAME2
Concatenate corresponding rows from CSV files PATHNAME1 and PATHNAME2,
where correspondence is defined as string-equivalence of a particular
cell value in each row. Similar to a join operation on database tables.

For each "left" row in PATHNAME1, search "right" rows R in PATHNAME2, 
and if the value of a particular cell in the left row equals the value 
of a particular cell in the right row, print all the cells from both 
rows on the same line. By default the first cell in each of the left 
and right rows is the cell that is compared.
    """)
    parser.add_option("-L", "--left-col", dest="left_col",
            action="store", metavar="INTEGER",type="int",
            help="use column INTEGER in the rows in PATHNAME1 as the key" + 
            " to join on (first cell is 0)")
    parser.add_option("-R", "--right-col", dest="right_col",
            action="store", metavar="INTEGER", type="int",
            help="use column INTEGER in the rows in PATHNAME2 as the key" + 
            " to join on")
    parser.add_option("--level", action="store", dest="level",
            help="set log level to LEVEL", metavar="LEVEL")
    parser.add_option("-d", "--in-delim", action="store", dest="indelim",
            metavar="CHAR", help="set input delimiter to CHAR instead " + 
            "of comma") 
    parser.add_option("-D", "--out-delim", action="store", dest="outdelim",
            metavar="CHAR",help="set output delimiter to CHAR instead of " + 
            "comma")
    parser.add_option("-t", "--tabin", action="store_const", dest="indelim",
            const="\t", help="set input delimiter to TAB instead of comma")
    parser.add_option("-T", "--tabout", action="store_const", dest="outdelim",
            const="\t", help="set output delimiter to TAB instead of comma")
    parser.add_option("-u", "--uniq", action="store_true", dest="uniq",
            help="rows in both files are unique (if true, speeds processing;"+
            "if specified as true but not actually true, behavior is " +
            "undefined")
    parser.set_defaults(indelim=',', outdelim=',', level='INFO',
            left_col=0, right_col=0, uniq=False)
    options, args = parser.parse_args()
    if len(args) != 2: parser.error('must have 2 arguments')
    return options, args

if __name__ == '__main__':
    import sys
    options, args = _parse_args()
    logging.basicConfig(level=eval('logging.'+options.level))
    ofile = sys.stdout
    pathname1, pathname2 = args[0], args[1]
    with open(pathname2, 'rb') as ifile2:
        rightlines = [row for 
                row in csv.reader(ifile2, delimiter=options.indelim)]
        _log.debug("len(rightlines) = %d", len(rightlines))
    with open(pathname1, 'rb') as ifile1:
        leftreader = csv.reader(ifile1, delimiter=options.indelim)
        writer = csv.writer(ofile, delimiter=options.outdelim)
        texttools.join_on(leftreader, rightlines, writer, options.left_col,
                options.right_col, bothuniq=options.uniq)

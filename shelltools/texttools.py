from __future__ import with_statement

import sys
import csv
import logging

_log = logging.getLogger('texttools')

def _getval(seq, index, nullcellval=None):
    try: return seq[index]
    except IndexError: return nullcellval

def _dispval(val, nulldispval=str(None)):
    if val is None: return nulldispval
    else: return val

def simplejux(seqs, csvwriter=None, nullcelldisp=str(None)):
    #if not isinstance(ifiles, list): ifiles = list(ifiles)
    if csvwriter is None: 
        csvwriter = csv.writer(sys.stdout, delim='\t')
    nfiles = len(seqs)
    gave_embedded_seq_warning = False
    # The statement "for row in map" with None as the function argument 
    # performs a transpose, filling in "empty" cells in the matrix with None
    # values. The seqs argument must be passed as *seqs in order to pass
    # each element of seqs as an argument to map().
    for row in map(None, *seqs):
        rowtodisp = [_dispval(v, nullcelldisp) for v in row]
        #if True in [isinstance(seq)
        csvwriter.writerow(rowtodisp)

def juxfiles(inpaths, ofile=sys.stdout, delim='\t',
            skipheaderrows=0, printheader=True):
    _log.debug("reading from files: %s", str(inpaths))
    _log.debug("skipping %d row(s) in each input file", skipheaderrows)
    ifiles = []
    try:
        for inp in inpaths:
            ifiles.append(open(inp, 'rb'))
        inlists = [map(str.strip, ifile.readlines()) for ifile in ifiles]
        _log.debug("input lengths: %s", str([len(s) for s in inlists]))
        for ifile in ifiles: ifile.close()
        writer = csv.writer(ofile, delimiter=delim)
        if printheader: writer.writerow(inpaths)
        if skipheaderrows: 
            inlists = [inlist[skipheaderrows:] for inlist in inlists]
        simplejux(inlists, writer)
    except IOError as inst:
        _log.debug("error reading from file: %s", inst)
        for ifile in ifiles:
            try:
                ifile.__exit__()
            except Exception as close_error:
                _log.debug("error closing input file: %s", close_error)


def join_on(leftreader, rightlines, writer, 
            leftcol=0, rightcol=0,
            bothuniq=False, printnonmatches=True):
    leftlines = 0
    linesout = 0
    for leftrow in leftreader:
        foundmatch = False
        i = 0
        while i < len(rightlines):
            rightrow = rightlines[i]
            if leftrow[leftcol] == rightrow[rightcol]:
                if not foundmatch: foundmatch = True
                writer.writerow(leftrow + rightrow)
                linesout += 1
                if bothuniq: del rightlines[i]
            i += 1
        if not foundmatch and printnonmatches: 
            writer.writerow(leftrow)
            linesout += 1
        leftlines += 1
    _log.debug("lines (in, out) = (%d, %d)", leftlines, linesout)
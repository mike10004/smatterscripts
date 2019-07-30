from __future__ import with_statement

import logging
from typing import Iterable

_log = logging.getLogger(__name__)


def join_on(leftreader: Iterable, rightlines: list, writer,
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
                if not foundmatch:
                    foundmatch = True
                writer.writerow(leftrow + rightrow)
                linesout += 1
                if bothuniq:
                    del rightlines[i]
            i += 1
        if not foundmatch and printnonmatches: 
            writer.writerow(leftrow)
            linesout += 1
        leftlines += 1
    _log.debug("lines (in, out) = (%d, %d)", leftlines, linesout)

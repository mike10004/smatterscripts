#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  distdraw.py
#
#  (c) 2015 Mike Chaberski
#  
#  MIT License

import re
import sys
import argparse
import os
import tempfile
import shutil
import os.path
from operator import itemgetter, attrgetter
import subprocess

_dpi_suffixes = ('ldpi', 'mdpi', 'hdpi', 'xhdpi')

_DRAWABLE_SELECTOR_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<selector xmlns:android="http://schemas.android.com/apk/res/android">
     <item android:state_enabled="false"
        android:drawable="@drawable/%s_gray"/>
    <item android:drawable="@drawable/%s_default" />
</selector>"""

def write_text_to_file(text, pathname):
    with open(pathname, 'w') as ofile:
        print >> ofile, text

def fill_selector_template(family):
    return _DRAWABLE_SELECTOR_TEMPLATE % (family, family)

def make_disabled_version(inpath, outpath):
    subprocess.check_call(["/usr/bin/convert", inpath, "-modulate", "100,0", outpath])
    subprocess.check_call(["/usr/bin/mogrify", "-modulate", "600", outpath])

def _maybe_do(fcn, src, dest, args):
    destdir = os.path.dirname(dest)
    if args.dry_run or args.verbose:
        print os.path.basename(src), "->", dest
    if not args.dry_run:
        if args.makedirs and not os.path.isdir(destdir):
            os.makedirs(destdir)
        fcn(src, dest)

class Unit:
    
    def __init__(self, pathname, family, size):
        self.pathname = pathname
        self.family = family
        self.size = size
    
    def getSize(self):
        return self.size

    def __repr__(self):
        return repr((self.pathname, self.family, self.age))
    
class Organizer:
    
    def __init__(self, args):
        self.families = dict()
        self.outsuffix = ".png"
        self.args = args

    def add(self, pathname):
        filename = os.path.basename(pathname)
        m = re.search('(\S+)[-_](\d+)\.png', filename)
        family = m.group(1)
        size = int(m.group(2))
        unit = Unit(pathname, family, size)
        if family not in self.families:
            self.families[family] = list()
        unitlist = self.families[family]
        unitlist.append(unit)
        unitlist.sort(key=attrgetter('size'))
    
    def printFamilies(self, ofile=sys.stdout):
        for family in self.families:
            print >> ofile, family + ": ",
            units = self.families[family]
            for unit in units:
                print >> ofile, os.path.basename(unit.pathname),
            print >> ofile

    def copyFamily(self, family, units):
        if self.args.statelistify:
            destdir = os.path.join(self.args.outdir, "res", "drawable")
            drawablepath = os.path.join(destdir, family + ".xml")
            drawabletext = fill_selector_template(family)
            fd, tempname = tempfile.mkstemp(".xml")
            with os.fdopen(fd, 'w') as ofile:
                print >> ofile, drawabletext
            _maybe_do(shutil.copy, tempname, drawablepath, self.args)
            os.remove(tempname)
        for i in xrange(min(len(_dpi_suffixes), len(units))):
            destdir = os.path.join(self.args.outdir, "res", "drawable-" + _dpi_suffixes[i])
            unit = units[i]
            if self.args.statelistify:
                dfoutpathname = os.path.join(destdir, unit.family + '_default' + self.outsuffix)
                grayoutpathname = os.path.join(destdir, unit.family + '_gray' + self.outsuffix)
                _maybe_do(shutil.copy, unit.pathname, dfoutpathname, self.args)
                _maybe_do(make_disabled_version, unit.pathname, grayoutpathname, self.args)
            else:
                outpathname = os.path.join(destdir, unit.family + self.outsuffix)
                _maybe_do(shutil.copy, unit.pathname, outpathname, self.args)

    def copyFamilies(self):
        for family in self.families:
            self.copyFamily(family, self.families[family])
        

def main():
    parser = argparse.ArgumentParser(description="copy image files to Android drawable resource directories")
    parser.add_argument("imagefiles", metavar="FILE", type=str, nargs='+', help="an image pathname")
    parser.add_argument("--dry-run", action="store_true", default=False, help="just show what would happen")
    parser.add_argument("-v", "--verbose", action="store_true", default=False, help="print verbose messages")
    parser.add_argument("--statelistify", action="store_true", default=False, help="make a state-list drawable out of each image")
    parser.add_argument("-D", "--no-makedirs", dest="makedirs", action="store_false", default=True, help="do not create any new directories")
    parser.add_argument("-o", "--outdir", type=str, default=".", help="copy image files to this Android project directory")
    args = parser.parse_args()
    org = Organizer(args)
    for arg in args.imagefiles: 
        org.add(arg)
    org.copyFamilies()
    return 0

if __name__ == '__main__':
    exit(main())


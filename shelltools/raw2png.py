#!/usr/bin/python
#
#  (c) 2015 Mike Chaberski
#  
#  MIT License

from __future__ import with_statement
import os.path
from PIL import Image
import argparse
import csv
import sys
from math import sqrt
MAX_INPUT_LENGTH = 16 * 1024 * 1024   # 16 MB in bytes

def guess_dims(rawfile_pathname, input_width=None, warnaboutguess=False):
    if input_width is None and not warnaboutguess:
        print >> sys.stderr, "raw2png: guessing image width by assuming square: ", rawfile_pathname
    rawfile_length = os.path.getsize(rawfile_pathname)
    assert rawfile_length < MAX_INPUT_LENGTH, \
                ('input exceeds max length: ' + 
                str(rawfile_length) +' > ' + str(MAX_INPUT_LENGTH))
    if input_width is None:
        input_width = int(sqrt(rawfile_length))
    image_height = rawfile_length / input_width
    if input_width * image_height != rawfile_length:
        print >> sys.stderr, ("raw2png: bad guess: product width*height != file length; " + 
                        "%d * %d = %d != %d" % (input_width, image_height,
                        input_width * image_height, rawfile_length))
    return input_width, image_height

def create_widths_map(args):
    m = dict()
    with open(args.widths_from, 'r') as ifile:
        reader = csv.reader(ifile, delimiter=' ')
        for row in reader:
            #print >> sys.stderr, row
            if args.wholenames: imname = row[0]
            else: imname = os.path.basename(row[0])
            w = int(row[1])
            m[imname] = w
    return m

def convert(raw_pathname, png_pathname, width, height, args):
    with open(raw_pathname, 'rb') as rawfile:
        data = rawfile.read()
    im = Image.fromstring(mode='L', size=(width, height), data=data)
    im.save(png_pathname, 'PNG')
    if args.verbose:
        print >> sys.stderr, "%s -> %s (%d x %d)" % (raw_pathname, png_pathname, width, height)

def main(args):
    if len(args.rawfile) > 1 and args.output is not None:
        print >> sys.stderr, "raw2png: can't specify output for multiple files"
        return 1
    widthmap = None
    specwidth = args.width
    if args.widths_from is not None:
        widthmap = create_widths_map(args)
    for rawfile in args.rawfile:
        imname = rawfile
        if not args.wholenames: imname = os.path.basename(rawfile)
        if widthmap is not None:
            if imname in widthmap: specwidth = widthmap[imname]
            elif args.width is not None: specwidth = args.width
        image_width, image_height = guess_dims(rawfile, specwidth, True)
        outname = args.output
        if outname is None:
            outname = os.path.splitext(rawfile)[0] + ".png"
        convert(rawfile, outname, image_width, image_height, args)
    return 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("rawfile", nargs='+', default=list(), 
            help="raw grayscale image file to convert to PNG format")
    parser.add_argument("-v", "--verbose", action="store_true", default=False)
    parser.add_argument("-o", "--output", metavar="PATHNAME", dest="output")
    parser.add_argument("--wholenames", action="store_true", default=False, 
            help="use whole pathnames when creating map from --widths-from" 
            + " file (default is to use basenames only)")
    parser.add_argument("-w", "--width", metavar="WIDTH", type=int, 
            help="image width (if not square)")
    parser.add_argument("--widths-from", metavar="WIDTHSFILE", 
            help="specify file to get raw image widths from; file should "
            + "contain image filenames and widths, separated by a space")
    args = parser.parse_args()
    exit(main(args))

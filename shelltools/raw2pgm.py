#!/usr/bin/python
#
#  (c) 2015 Mike Chaberski
#  
#  MIT License

from __future__ import with_statement
from math import sqrt
import os.path

DEFAULT_MAGIC_NO = 'P5'
PGM_EXTENSION = 'pgm'
DEFAULT_MAXVAL = 255

MAX_INPUT_LENGTH = 16 * 1024 * 1024   # 16 MB in bytes
CHUNK_LENGTH = 1024

def copy_bytes(infile, outfile, chunk_length=CHUNK_LENGTH):
    chunk = infile.read(chunk_length)
    while chunk != '':
        outfile.write(chunk)
        chunk = infile.read(chunk_length)

def guess_dims(rawfile_pathname, input_width=None):
    rawfile_length = os.path.getsize(rawfile_pathname)
    assert rawfile_length < MAX_INPUT_LENGTH, \
                ('input exceeds max length: ' + 
                str(rawfile_length) +' > ' + str(MAX_INPUT_LENGTH))
    if input_width is None:
        input_width = int(sqrt(rawfile_length))
    image_height = rawfile_length / input_width
    if input_width * image_height != rawfile_length:
        raise ValueError("product width*height != file length; " + 
                        "%d * %d = %d != %d" % (input_width, image_height,
                        input_width * image_height, rawfile_length))
    return input_width, image_height


def parse_args(outext='out'):
    from optparse import OptionParser
    parser = OptionParser(usage="""
    %%prog [options] RAWFILE [OUTFILE]
Converts RAWFILE to %s format. If OUTFILE is not specified, then the 
output pathname is input pathname with the extension .%s appended."""
        % (outext, outext))
    parser.add_option("-w", "--width", 
                    dest="image_width", metavar="INTEGER",
                    type="int");
    (options, args) = parser.parse_args()
    rawfile_pathname = args[0]
    if len(args) > 1:
        outfile_pathname = args[1]
    else:
        outfile_pathname = rawfile_pathname + '.' + outext
    return options, rawfile_pathname, outfile_pathname


def write_header(outfile, width, height, 
                maxval=DEFAULT_MAXVAL, 
                magic_no=DEFAULT_MAGIC_NO):
    print >> outfile, magic_no
    print >> outfile, str(width), str(height)
    print >> outfile, str(maxval)


def convert(rawfile, pgmfile, width, height):
    write_header(pgmfile, width, height)
    copy_bytes(rawfile, pgmfile)

def guess_dims(rawfile_pathname, input_width=None):
    rawfile_length = os.path.getsize(rawfile_pathname)
    assert rawfile_length < MAX_INPUT_LENGTH, \
                ('input exceeds max length: ' + 
                str(rawfile_length) +' > ' + str(MAX_INPUT_LENGTH))
    if input_width is None:
        input_width = int(sqrt(rawfile_length))
    image_height = rawfile_length / input_width
    if input_width * image_height != rawfile_length:
        raise ValueError("product width*height != file length; " + 
                        "%d * %d = %d != %d" % (input_width, image_height,
                        input_width * image_height, rawfile_length))
    return input_width, image_height

if __name__ == '__main__':
    import os.path
    options, rawfile_pathname, pgmfile_pathname = parse_args(PGM_EXTENSION)
    image_width, image_height = guess_dims(rawfile_pathname, options.image_width)
    with open(rawfile_pathname, 'rb') as rawfile:
        with open(pgmfile_pathname, 'wb') as pgmfile:
            convert(rawfile, pgmfile, options.image_width, image_height)

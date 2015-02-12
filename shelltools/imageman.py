# imageman function library 
#
#  (c) 2015 Mike Chaberski
#  
#  MIT License

import os.path

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


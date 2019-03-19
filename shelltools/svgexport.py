#!/usr/bin/env python
#
#  svgexport.py
#
#  Copyright 2015 Mike Chaberski
#  
#  MIT License
#  

import subprocess
from optparse import OptionParser
import tempfile
import os
import sys
import os.path
import logging
import _common
#from PIL import Image
import shutil

_log = logging.getLogger("svgexport")
_DEFAULT_SIZES = (16, 24, 32, 48, 72)
_DEFAULT_SIZES_MORE = (16, 24, 32, 36, 48, 64, 72, 96, 128, 256)
_ANDROID_PROJ_RELDIRS = (os.path.join('res', 'drawable-ldpi-v5'), 
        os.path.join('res', 'drawable-mdpi-v5'),
        os.path.join('res', 'drawable-hdpi-v5'))

# http://developer.android.com/guide/practices/ui_guidelines/icon_design.html
_ANDROID_SIZES_BY_STYLE = {
    # http://developer.android.com/guide/practices/ui_guidelines/icon_design_launcher.html
    'android-launcher': {
        36: 'res/drawable-ldpi-v5',
        48: 'res/drawable-mdpi-v5',
        72: 'res/drawable-hdpi-v5',
        96: 'res/drawable-xhdpi',
    }
}

_LINUX_SIZES = (16, 24, 32, 48, 64, 72)
_LINUX_SIZES_MORE = (16, 20, 22, 24, 32, 36, 40, 48, 64, 72, 96, 128, 192, 256)

class ExportParams:
    
    def __init__(self, options, sizes=None):
        self.outroot = options.outdir or os.getcwd()
        #print >> sys.stderr, "outroot will be", self.outroot
        self.options = options
        if sizes is None and options.sizes is not None:
            sizes = [int(s) for s in options.sizes.split(',')]
            _log.debug(" parsed specified sizes '%s' into %s", options.sizes, sizes)
        self.sizes = sizes or _DEFAULT_SIZES
    
    def do_post_export(self, svg_pn):
        pass
    
    def create_outname(self, svg_pn, sz):
        """Create the output pathname based on the input SVG pathname
        and the output size."""
        outfnstem, inext = os.path.splitext(svg_pn)
        outfnstem = os.path.basename(outfnstem)
        outfn = outfnstem + self.options.infix + str(sz) + ".png"
        outpath = os.path.join(self.outroot, outfn)
        #print >> sys.stderr, "outpath = ", (self.outroot, outfn)
        return outpath

class LinuxExportParams(ExportParams):
    
    def __init__(self, options, sizes=None):
        if sizes is None:
            if options.more_sizes is True:
                sizes = _LINUX_SIZES_MORE
            else:
                sizes = _LINUX_SIZES
        ExportParams.__init__(self, options, sizes)

    def do_post_export(self, svg_pn):
        outdir = os.path.join(self.outroot, 
            self.options.linux_theme, 
            "scalable", 
            self.options.linux_icontype)
        outfn = os.path.basename(svg_pn)
        if not os.path.isdir(outdir):
            os.makedirs(outdir)
        shutil.copy(svg_pn, os.path.join(outdir, outfn))

    def create_outname(self, svg_pn, sz):
        subdir = self.options.linux_icontype
        outdir = os.path.join(self.outroot, 
            self.options.linux_theme, 
            "%dx%d" % (sz, sz), 
            self.options.linux_icontype)
        outfnstem, inext = os.path.splitext(os.path.basename(svg_pn))
        outfn = outfnstem + ".png"
        outpn = os.path.join(outdir, outfn)
        return outpn
        
class AndroidExportParams(ExportParams):
    
    size2dir = None
    
    def __init__(self, options, sizes=None):
        self.size2dir = _ANDROID_SIZES_BY_STYLE[options.style]
        ExportParams.__init__(self, options, self.size2dir.keys())
    
    def create_outname(self, svg_pn, sz):
        outdir = os.path.join(self.outroot, self.size2dir[sz])
        outfnstem, inext = os.path.splitext(os.path.basename(svg_pn))
        outfn = outfnstem + ".png"
        outpn = os.path.join(outdir, outfn)
        return outpn

def create_export_params(options):
    if options.style.startswith('android'):
        return AndroidExportParams(options)
    elif options.style == 'linux':
        return LinuxExportParams(options)
    return ExportParams(options)

def _squareify(inpn, indims, outpn):
    cmdline = ("composite", "-gravity", "center", inpn, 
        "-size", "%dx%d" % (max(indims), max(indims)), 
        "canvas:none", outpn)
    _log.debug(" %s", ' '.join(cmdline))
    return subprocess.call(cmdline)

def _export_one(inpn, outpn, sz, square=False):
    if square:
        fd, pngname = tempfile.mkstemp(".png", ("rectpng-%dxH-" % sz))
        os.close(fd)
    else:
        pngname = outpn
    cmdline = ("rsvg", 
            "--format", "png", 
            "-w", str(sz), # width argument
            inpn, pngname);
    _log.debug(" %s", ' '.join(cmdline))
    ret = subprocess.call(cmdline)
    if ret == 0 and square:
        im = Image.open(pngname)
        w, h = im.size
        if w == h: 
            shutil.move(pngname, outpn)
        else:
            ret = _squareify(pngname, (w, h), outpn)
            os.remove(pngname)
    return ret

def export_all(svg_pn, exparams):
    n = 0
    for sz in exparams.sizes:
        outname = exparams.create_outname(svg_pn, sz)
        if not os.path.isdir(os.path.dirname(outname)):
            os.makedirs(os.path.dirname(outname))
        ret = _export_one(svg_pn, outname, sz, exparams.options.square)
        if ret == 0:
            n += 1
        else:
            _log.warn(" convert exited %d" % ret)
    return n

def _parse_args():
    parser = OptionParser(usage="""
    %prog [options] SVGFILE [SVGFILES...]
By default, the vector file will be exported as png images whose 
filenames contain the image dimensions. This is the 'filename' style.
Other 'styles' of export can be specified with the --style option. In 
'android' style, three images are exported for each input .svg, and the
exported images are created in the res/drawable-* subdirectories of the 
output directory. In 'linux' style, the icons are exported into a 
directory structure like that which is under /usr/share/icons.""")
    parser.add_option("--sizes", metavar="SIZE[,SIZE...]", 
        action="store", nargs=1,
        help="export at specified sizes (comma-delimited)")
    parser.add_option("--infix", metavar="CHAR", nargs=1, action="store",
        help="if style=filename, use CHAR as infix between filename stem" 
        + " and size (default is -)")
    parser.add_option("--outdir", metavar="DIRNAME", nargs=1, action="store",
        help="use DIRNAME as output directory (default is current working" 
        + " directory)")
    parser.add_option("-s", "--square", action="store_true",
        help="square-ify output image dimensions")
    parser.add_option("--style", metavar="STYLE", nargs=1, action="store",
        help="set export style to one of 'android', 'linux', or 'filename'")
    parser.add_option("--more-sizes", action="store_true", 
        help="for some --style options, this will increase the number "
        +"of sizes at which images are exported")
    parser.add_option("--linux-icontype", metavar="TYPE", action="store", 
        help="in --style=linux mode, specify the icon type; default " + 
        "is emblems; check /usr/share/icons/NxN for some valid choices")
    parser.add_option("--linux-theme", metavar="THEME", action="store",
        help="in --style=linux mode, specify the theme directory " 
        + "(see /usr/share/icons for good choices; default is 'gnome')")
    parser.add_option("--skip-check", action="store_true", 
        help="for some --style options, this will skip the check that "
        + " the destination directory is a reasonable place to export to")
    _common.add_logging_options(parser)
    parser.set_defaults(infix='-', style='filename', 
            linux_icontype='emblems', linux_theme='gnome')
    options, args = parser.parse_args()
    return parser, options, args

def check_android_proj(options):
    projdir = options.outdir
    if not os.path.isfile(os.path.join(projdir, '.project')):
        _log.info("specified directory does not appear to be " 
                + "a project directory: should have '.project' file: " + projdir)
        return False
    if not os.path.isdir(os.path.join(projdir, 'res')):
        _log.info("specified directory does not appear to be " 
                + "a project directory: should have 'res' subdirectory: " + projdir)
        return False
    return True

def main():
    parser, options, args = _parse_args()
    if len(args) == 0:
        parser.error("must specify filename(s) to be exported")
    _common.config_logging(options)
    if options.style == 'android' and options.skip_check is not True:
        if not check_android_proj(options):
            _log.info(" output directory doesn't look like an Android " 
            + "project directory: no .project file or res/ subdirectory; "
            + "no files will be exported")
            return 1
    exparams = create_export_params(options)
    n = 0
    for svg_pn in args:
        n += export_all(svg_pn, exparams)
        exparams.do_post_export(svg_pn)
    _log.debug("%s: %d images successfully exported" % (svg_pn, n))
    return 0




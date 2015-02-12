#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  graybmpify_simple.py
#
#  (c) 2015 Mike Chaberski
#  
#  MIT License

import sys
from PIL import Image

infile, outfile = sys.argv[1], sys.argv[2]
im = Image.open(infile)
im = im.convert('L')
im.save(outfile, 'bmp')

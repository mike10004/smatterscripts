#!/usr/bin/python3

import pathlib
import sys
import os
import os.path
import html
import jinja2
import csv
from typing import Iterable, List, TextIO, Dict, Optional, Callable
from argparse import ArgumentParser, Namespace
import logging

_log = logging.getLogger(__name__)

DEFAULT_TEMPLATE = """<!DOCTYPE html>
<html>
    <head>
        <style>
.row {
    padding: 15px;
}

.images {
    
}

.image {
    margin: 5px;
    display: inline-block;
    text-align: center;
}

.caption {
    float: left;
}


        </style>
    </head>
    <body>
    <div>
        {% for row in rows %}
        <div class="row">
            <div class="images">
                {% for image in row.images %}
                <div class="image">
                    <img src="{{image.url}}">
                    <div class="image-title">{{image.filename}}</div>
                </div>
                {% endfor %}
            </div>
            <div class="caption">
                {{ row.caption }}
            </div>
        </div>
        {% endfor %}
    </div>
    </body>
</html>
"""

class Image(object):

    def __init__(self, url, filename):
        self.url = url
        self.filename = filename


class Row(object):

    def __init__(self, caption, images):
        self.caption = caption
        self.images = images


class PageModel(object):

    def __init__(self, rows: List[Row]):
        self.rows = rows


class Renderer(object):

    def __init__(self, template: jinja2.Template):
        self.template = template

    def render(self, page_model):
        return self.template.render(**(vars(page_model)))


_IDENTITY = lambda x: x


class Extractor(object):

    def __init__(self, caption_column: int, image_pathname_columns: Optional[Iterable[int]], parent_dir=None, pathname_transform: Optional[Callable[[str], str]]=None):
        self.caption_column = caption_column
        self.image_pathname_columns = image_pathname_columns
        self.parent_dir = parent_dir or os.getcwd()
        self.pathname_transform = pathname_transform or _IDENTITY

    def to_image(self, pathname):
        pathname = self.pathname_transform(pathname)
        if not os.path.isabs(pathname):
            pathname = os.path.join(self.parent_dir, pathname)
        url = pathlib.Path(pathname).as_uri()
        filename = os.path.basename(pathname)
        return Image(url, filename)

    def extract(self, ifile: TextIO, csv_args: Dict):
        rows = []
        for row in csv.reader(ifile, **csv_args):
            caption = row[self.caption_column]
            if self.image_pathname_columns is None:
                image_columns = [row[i] for i in range(len(row)) if i != self.caption_column]
            else:
                image_columns = [row[i] for i in self.image_pathname_columns]
            images = list(map(lambda pathname: self.to_image(pathname), image_columns))
            rows.append(Row(caption, images))
        return rows

def main():
    parser = ArgumentParser()
    parser.add_argument("input", default="/dev/stdin", help="input CSV file", metavar="FILE")
    parser.add_argument("--caption", type=int, default=0, help="set caption column", metavar="K")
    parser.add_argument("--images", help="set image columns (comma-delimited)", metavar="KEYDEF")
    parser.add_argument("--template")
    parser.add_argument("--delimiter", "--delim", "-d", metavar="CHAR", help="set input delimiter")
    parser.add_argument("--image-root", help="set parent directory for relative paths")
    parser.add_argument("--remove-suffix", help="remove suffix from each image pathname")
    parser.add_argument("--remove-prefix", help="remove prefix from each image pathname")
    args = parser.parse_args()
    csv_args = {
        'delimiter': ("\t" if args.delimiter=='TAB' else None)
    }
    if args.images is None:
        image_columns = None
    else:
        image_columns = list(map(int, args.images.split(",")))
    def p_transform(filename):
        if args.remove_prefix and filename.startswith(args.remove_prefix):
            filename = filename[len(args.remove_prefix):]
        if args.remove_suffix and filename.endswith(args.remove_suffix):
            filename = filename[:-len(args.remove_suffix)]
        return filename
    extractor = Extractor(args.caption, image_columns, args.image_root, p_transform)
    with open(args.input, 'r') as ifile:
        perform(ifile, extractor, args.template, csv_args)
    return 0

def perform(ifile: TextIO, extractor: Extractor, template: str=None, csv_args: Dict=None, ofile: TextIO=sys.stdout):
    csv_args = csv_args or {}
    rows = extractor.extract(ifile, csv_args)
    page_model = PageModel(rows)
    env = jinja2.Environment(
        autoescape=jinja2.select_autoescape(['html', 'xml'])
    )
    if template is None:
        template = env.from_string(DEFAULT_TEMPLATE)
    else:
        raise NotImplementedError("custom template")
    renderer = Renderer(template)
    rendering = renderer.render(page_model)
    print(rendering, file=ofile)

#!/usr/bin/python3

"""
Program that generates an HTML file to juxtapose images. The image pathnames
are parsed from a CSV file.
"""

import pathlib
import urllib.parse
import sys
import os
import os.path
import jinja2
import csv
from typing import Iterable, List, TextIO, Dict, Optional, Callable, Sequence
from argparse import ArgumentParser, Namespace
import logging
from _common import predicates

_log = logging.getLogger(__name__)
_IDENTITY = lambda x: Image(pathlib.Path(x).as_uri(), os.path.basename(os.path.normpath(x)))

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
                    <div class="image-title">{{image.title}}</div>
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

    def __init__(self, url, title):
        self.url = url
        self.title = title


class Row(object):

    def __init__(self, caption, images):
        self.caption = caption or ''
        self.images = images


class PageModel(object):

    def __init__(self, rows: List[Row]):
        self.rows = rows


class Renderer(object):

    def __init__(self, template: jinja2.Template):
        self.template = template

    def render(self, page_model):
        page_attrs = vars(page_model)
        return self.template.render(**page_attrs)


class Extractor(object):

    def __init__(self, caption_column: Optional[int], image_pathname_columns: Optional[Iterable[int]], csv_args: Dict=None, src_transform: Optional[Callable[[str], Image]]=None):
        self.caption_column = caption_column
        self.image_pathname_columns = image_pathname_columns
        self.csv_args = csv_args or {}
        self.src_transform = src_transform or _IDENTITY

    def _transform_cell(self, i, value):
        try:
            return self.src_transform(value)
        except Exception as e:
            _log.debug("failed to transform value on row %d due to %s", i, e)
            return None

    def extract(self, ifile: TextIO, predicate: Optional[Callable[[int, List[str]], bool]]=None):
        predicate = predicate or predicates.always_true()
        rows = []
        for i, row in enumerate(csv.reader(ifile, **self.csv_args)):
            if not predicate(i, row):
                continue
            caption=None
            if self.caption_column is not None:
                caption = row[self.caption_column]
            if self.image_pathname_columns is None:
                image_columns = [row[i] for i in range(len(row)) if i != self.caption_column]
            else:
                image_columns = [row[i] for i in self.image_pathname_columns]
            images = list(filter(predicates.not_none(), map(lambda v: self._transform_cell(i, v), image_columns)))
            rows.append(Row(caption, images))
        return rows


def make_cell_value_transform(args: Namespace) -> Callable[[str], Image]:
    """Returns a function that maps CSV cell values to Image instances with file URIs."""
    parent_dir = args.image_root or os.getcwd()
    def transform(cell_value):
        if args.remove_prefix and cell_value.startswith(args.remove_prefix):
            cell_value = cell_value[len(args.remove_prefix):]
        if args.remove_suffix and cell_value.endswith(args.remove_suffix):
            cell_value = cell_value[:-len(args.remove_suffix)]
        if args.scheme == 'file':
            if not os.path.isabs(cell_value):
                cell_value = os.path.join(parent_dir, cell_value)
            url = pathlib.Path(cell_value).as_uri()
            title = os.path.basename(cell_value)
        elif args.scheme == 'http' or args.scheme == 'https':
            url = args.scheme + '://' + cell_value
            title = os.path.basename(urllib.parse.urlparse(url).path)
        else:
            url = cell_value
            title = cell_value
        return Image(url, title)
    return transform


def perform(ifile: TextIO, extractor: Extractor, predicate: Optional[Callable], template: str=None, ofile: TextIO=sys.stdout):
    rows = extractor.extract(ifile, predicate)
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


def main(args: Sequence[str]=None, stdout: TextIO=sys.stdout, stderr: TextIO=sys.stderr):
    parser = ArgumentParser(description="Generate an HTML page from rows of image pathnames in a CSV file.", epilog="All row/column indexes are zero-based.")
    parser.add_argument("input", nargs='?', default="/dev/stdin", help="input CSV file", metavar="FILE")
    parser.add_argument("--caption", type=int, help="set caption column", metavar="K")
    parser.add_argument("--images", help="column indexes of cell values to transform to image URIs (comma-delimited)", metavar="COLS")
    parser.add_argument("--template", metavar="FILE", help="set HTML template")
    parser.add_argument("--delimiter", "--delim", "-d", metavar="CHAR",  help="set input delimiter")
    parser.add_argument("--image-root", metavar="DIR", help="prepend parent directory to cell values")
    parser.add_argument("--remove-suffix", metavar="STR", help="remove suffix from cell values")
    parser.add_argument("--remove-prefix", metavar="STR", help="remove prefix from cell values")
    parser.add_argument("--print-template", action='store_true', help="print the default template on stdout and exit")
    parser.add_argument("--skip", type=int, default=0, metavar="N", help="skip first N rows of input")
    parser.add_argument("--limit", "-n", type=int, metavar="N", help="generate markup for at most N rows of input")
    parser.add_argument("--scheme", choices=('file', 'http', 'https', 'none'), default='file', metavar='SCHEME', help="set scheme for img src attribute value; choices are file, http[s], and none; default is file")
    args = parser.parse_args(args)
    if args.print_template:
        print(DEFAULT_TEMPLATE, end="", file=stdout)
        return 0
    csv_args = {}
    if args.delimiter is not None:
        csv_args['delimiter'] = ("\t" if args.delimiter=='TAB' else args.delimiter)
    if args.images is None:
        image_columns = None
    else:
        try:
            image_columns = tuple(map(int, args.images.split(",")))
        except ValueError:
            parser.print_usage(stderr)
            return 1
    if not image_columns:
        print(f"{__name__}: at least one column index must be specified", file=stderr)
        return 1
    p_transform = make_cell_value_transform(args)
    extractor = Extractor(args.caption, image_columns, csv_args, p_transform)
    predicate = predicates.always_true()
    if args.skip:
        predicate = predicates.And(predicate, lambda i, row: i >= args.skip)
    if args.limit:
        predicate =  predicates.And(predicate, lambda i, row: i < args.limit)
    with open(args.input, 'r') as ifile:
        perform(ifile, extractor, predicate, args.template)
    return 0

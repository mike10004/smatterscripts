#!/usr/bin/python3

"""
Program that generates an HTML file to juxtapose images. The image pathnames
are parsed from a CSV file.
"""

import urllib.parse
import operator
import logging
import pathlib
import os.path
import jinja2
import math
import sys
import csv
import re
import os
from typing import Iterable, List, TextIO, Dict, Optional, Callable, Sequence, Tuple
from argparse import ArgumentParser, Namespace
from _common import predicates

_log = logging.getLogger(__name__)
_DEFAULT_IMAGE_XFORM = lambda x: Image(pathlib.Path(x).as_uri(), os.path.basename(os.path.normpath(x)))
_IDENTITY = lambda x: x

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

    def __init__(self, caption_column: Optional[int]=None,
                 image_pathname_columns: Optional[Iterable[int]]=None,
                 csv_args: Dict=None,
                 src_transform: Optional[Callable[[str], Image]]=None):
        self.caption_column = caption_column
        self.image_pathname_columns = image_pathname_columns
        self.csv_args = csv_args or {}
        self.src_transform = src_transform or _DEFAULT_IMAGE_XFORM

    def _transform_cell(self, i, value):
        try:
            return self.src_transform(value)
        except Exception as e:
            _log.debug("failed to transform value on row %d due to %s", i, e)
            return None

    def _enumerate_rows(self, ifile: TextIO, sort_spec, predicate):
        sort_key, reverse = sort_spec or (None, False)
        predicate = predicate or predicates.always_true()
        row_iterator = csv.reader(ifile, **self.csv_args)
        if sort_key is not None:
            row_iterator = sorted(row_iterator, key=sort_key, reverse=reverse)
        return filter(predicate, enumerate(row_iterator))

    def extract(self, ifile: TextIO, sort_spec: Tuple, predicate: Optional[Callable[[int, List[str]], bool]]=None):
        rows = []
        for i, row in self._enumerate_rows(ifile, sort_spec, predicate):
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


def _try_float(token: str):
    """Parses a string to a float and returns NaN if not parseable."""
    try:
        return float(token)
    except ValueError:
        return math.nan


def make_sort_key(sort_key_def: Optional[str], caption_column: Optional[int]) -> Optional[Tuple[Callable, bool]]:
    if sort_key_def is None:
        return None
    m = re.fullmatch(r'([-+])?(\w+)(:\d+)?', sort_key_def)
    if m is None:
        raise ValueError("sort key definition syntax is incorrect; should be '[-]mode[:K]'")
    rev = m.group(1) == '-'
    mode = m.group(2)
    column = (m.group(3) or '')[1:]
    if column:
        column = int(column)
    else:
        column = caption_column
    if mode == 'numeric':
        if column is None:
            raise ValueError("must specify sort column in numeric mode")
        sort_key = lambda row: _try_float(row[column])
    else:
        if column is None:
            sort_key = tuple
        else:
            sort_key = operator.itemgetter(column)
    return sort_key, rev


def perform(ifile: TextIO, extractor: Extractor, sort_spec=None, predicate: Optional[Callable]=None, template: str=None, ofile: TextIO=sys.stdout):
    rows = extractor.extract(ifile, sort_spec, predicate)
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


def make_row_predicate(skip: int, limit:int):
    predicate = predicates.always_true()
    if skip is not None:
        predicate = predicates.And(predicate, lambda erow: erow[0] >= skip)
    if limit is not None:
        predicate =  predicates.And(predicate, lambda erow: erow[0] < limit)
    return predicate


def main(args: Sequence[str]=None, stdout: TextIO=sys.stdout, stderr: TextIO=sys.stderr):
    parser = ArgumentParser(description="Generate an HTML page from rows of image pathnames in a CSV file.",
                            epilog="""All row/column indexes are zero-based.
Syntax of --sort argument is MODE[:K] where MODE is 'numeric', or 'lexicographical'
and K is column index. Caption column is the default index for sorting. Sort is
performed *before* --skip and --limit are applied.""",
                            allow_abbrev=False)
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
    parser.add_argument("--sort", metavar="[-]MODE[:K]", help="sort rows")
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
    sort_key = make_sort_key(args.sort, args.caption)
    predicate = make_row_predicate(args.skip, args.limit)
    with open(args.input, 'r') as ifile:
        perform(ifile, extractor, sort_key, predicate, args.template)
    return 0

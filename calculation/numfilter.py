#!/usr/bin/env python3

"""Filter an input CSV by applying a threshold to a certain column."""

import csv
import re
import os
import sys
import json
import errno
import logging
import _common
import calculation
from _common import StreamContext
from typing import Callable, TextIO, List, Any, Pattern, Dict, Sequence, Tuple, Optional, Union, Iterable, Iterator
from argparse import ArgumentParser, Namespace
from . import ValueParser, Ignorer


_log = logging.getLogger(__name__)


class Filter(object):

    def __init__(self, reference: float, operator: str, epsilon: float=None):
        self.callable = {
            'ge': lambda x: x >= reference,
            'gt': lambda x: x > reference,
            'le': lambda x: x <= reference,
            'lt': lambda x: x < reference,
            'eq': lambda x: abs(reference - x) <= epsilon,
            'ne': lambda x: abs(reference - x) > epsilon
        }[operator]

    def __call__(self, query):
        return self.callable(query)

    @classmethod
    def from_args(cls, args: Namespace):
        reference = 0 if args.threshold is None else args.threshold
        epsilon = 0 if args.epsilon is None else args.epsilon
        operator = 'ge' if args.operator is None else args.operator
        f = Filter(reference, operator, epsilon)
        return f

def _transform_value(value_str: str):
    return float(value_str)


def do_filter(ifile: TextIO, filterer: Filter, ofile: TextIO, value_column=0, input_delimiter=',', output_delimiter=',', error_reaction='auto'):
    output = csv.writer(ofile, delimiter=output_delimiter)
    nrows, nerrors = 0, 0
    for row in csv.reader(ifile, delimiter=input_delimiter):
        nrows += 1
        parse_ok = False
        try:
            value = _transform_value(row[value_column])
            parse_ok = True
            if filterer(value):
                output.writerow(row)
        except Exception as e:
            _log.debug("failed to parse value on row %s due to: %s", nrows, e)
            if error_reaction == 'include' or (error_reaction == 'auto' and parse_ok):
                output.writerow(row)
    if nerrors > 0:
        _log.info("%d errors encountered; use --log-level=DEBUG to view them", nerrors)
    return 0 if (nerrors != nrows) else 2




def main(argl=None, ofile=sys.stdout):
    parser = ArgumentParser(description="Filter rows from an input CSV by applying a threshold to a column.")
    _common.add_logging_options(parser)
    parser.add_argument("input", nargs='?', help="input CSV file")
    parser.add_argument("--threshold", "-t", type=float, metavar='T', help="set threshold")
    parser.add_argument("--operator", "-p", choices=('ge', 'gt', 'le', 'lt', 'eq', 'ne'), help="set operator to use with threshold")
    parser.add_argument("--epsilon", "-e", type=float, metavar='E', help="tolerance for 'eq' and 'ne' operators")
    parser.add_argument("--input-delimiter", default=',', help="set input delimiter")
    parser.add_argument("--output-delimiter", default=',', help="set output delimiter")
    parser.add_argument("--column", "-c", default=0, type=int, help="set value column")
    parser.add_argument("--errors", choices=('exclude', 'include', 'auto'), help="set reaction to errors")
    args = parser.parse_args(argl)
    _common.config_logging(args)
    input_delimiter = "\t" if args.input_delimiter is 'TAB' else args.input_delimiter
    output_delimiter = "\t" if args.output_delimiter is 'TAB' else args.output_delimiter
    f = Filter.from_args(args)
    with StreamContext(args.input, 'r') as ifile:
        return do_filter(ifile, f, ofile, args.column, input_delimiter, output_delimiter, args.errors)

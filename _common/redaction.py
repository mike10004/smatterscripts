"""
Module that provides functions for redaction.
"""

import re
from . import predicates
from typing import TextIO, List, Pattern, Callable
from argparse import ArgumentParser, Namespace


def read_pattern_file(ifile: TextIO) -> List[Pattern]:
    patterns = []
    for line in ifile:
        line = line.strip()
        if line and not line.lstrip().startswith("#"):
            p = re.compile(line.strip())
            patterns.append(p)
    return patterns


def build_filter_from_patterns(patterns: List[Pattern]) -> Callable[[str], bool]:
    """Build a blacklist filter that returns false if a value matches any of a list of patterns."""
    if not patterns:
        return predicates.always_true()
    def do_filter(value):
        for pattern in patterns:
            if pattern.search(value) is not None:
                return False
        return True
    return do_filter


def support_pattern_args(parser: ArgumentParser, option_string: str='--redact-patterns'):
    parser.add_argument(option_string, metavar="FILE", help="redact items that match patterns listed in FILE")


def build_filter_from_args(args: Namespace, option_string='--redact_patterns'):
    patterns = None
    pattern_file = args.__dict__.get(option_string.lstrip('-'))
    if pattern_file:
        with open(pattern_file, 'r') as ifile:
            patterns = read_pattern_file(ifile)
    return build_filter_from_patterns(patterns)

#!/usr/bin/env python3

"""Perform receiver-operating characteristic transform on input values."""

import csv
import sys
import logging
import _common
from _common import predicates
from typing import Callable, TextIO, List, Any, Pattern, Dict, Sequence, Tuple, Optional, Union, Iterable, Iterator
from argparse import ArgumentParser, Namespace
from shelltools import csvutils
from shelltools.csvutils import ValueParser, Ignorer


_log = logging.getLogger(__name__)


class Element(object):

    def __init__(self, evaluator: Callable[[Any], bool], ground_truthist: Union[bool, Callable[[], bool]]):
        self.evaluator = evaluator
        self.ground_truthist = ground_truthist
        self._ground_truth = ground_truthist if isinstance(ground_truthist, bool) else None

    def evaluate(self, threshold):
        return self.evaluator(threshold)

    def ground_truth(self):
        if self._ground_truth is None:
            self._ground_truth = self.ground_truthist()
        return self._ground_truth

    @classmethod
    def list(cls, values: Iterator, ground_truth: bool):
        return list(map(lambda v: Element(_make_evaluator(v), ground_truth), values))


def roc_transform(elements: Sequence[Element], threshold_domain: Iterable) -> Dict[float, Tuple[float, float]]:
    known_positives = sum(element.ground_truth() for element in elements)
    known_negatives = sum(not element.ground_truth() for element in elements)
    if known_positives == 0 or known_negatives == 0:
        _log.warning("known positives = %d, known negatives = %d", known_positives, known_negatives)
    roc = {}
    for threshold in threshold_domain:
        false_positives, false_negatives = 0, 0
        for element in elements:
            expected = element.ground_truth()
            actual = element.evaluate(threshold)
            if expected and not actual:  ## known positives
                false_negatives += 1
            elif not expected and actual:  ## known negative
                false_positives += 1
        roc[threshold] = (false_positives / known_negatives, false_negatives / known_positives)
    return roc


def decide_domain(values: Iterator[float], domain_size: int=None, epsilon=1e-5) -> Iterator[float]:
    sorted_vals = sorted(values)
    assert len(sorted_vals) > 0, "zero elements in input"
    min_value, max_value = sorted_vals[0], sorted_vals[-1]
    width = max_value - min_value
    if width == 0:
        if domain_size is not None and domain_size != 1:
            raise ValueError("only one element in threshold domain")
        return [min_value].__iter__()
    domain_size = 100 if domain_size is None else domain_size
    step = (width + epsilon) / domain_size
    return map(lambda i: min_value + (i * step), range(domain_size))


def _make_evaluator(value):
    return lambda threshold: value >= threshold


def main(argl: Sequence[str]=None, ofile: TextIO=sys.stdout) -> 0:
    parser = ArgumentParser()
    parser.add_argument("known_positives")
    parser.add_argument("known_negatives")
    parser.add_argument("--invert", action='store_true', help="invert input values")
    parser.add_argument("--domain", type=float, nargs=2, metavar=("MIN", "STEP"), help="threshold domain")
    parser.add_argument("--domain-size", "-n", type=int, default=100, metavar="N", help="threshold domain size")
    _common.add_logging_options(parser)
    args = parser.parse_args(argl)
    _common.config_logging(args)
    value_type = float
    invert = args.invert
    parse_fn = csvutils.build_parse_value(value_type, invert)
    value_parser = ValueParser(parse_fn, predicates.always_true())
    with open(args.known_positives, 'r') as ifile:
        known_positives = value_parser.read_values(ifile)
    with open(args.known_negatives, 'r') as ifile:
        known_negatives = value_parser.read_values(ifile)
    _log.debug(" parsed %d known positives and %d known negatives", len(known_positives), len(known_negatives))
    positive_elements = Element.list(known_positives, True)
    negative_elements = Element.list(known_negatives, False)
    all_elements = positive_elements + negative_elements
    if args.domain is None:
        threshold_domain = decide_domain(known_positives + known_negatives, args.domain_size)
    else:
        t_min, t_step = args.domain
        threshold_domain = [t_min + i * t_step for i in range(args.domain_size)]
    roc = roc_transform(all_elements, threshold_domain)
    roc_keys = sorted(roc.keys())
    writer = csv.writer(ofile, delimiter="\t")
    for threshold in roc_keys:
        false_pos_rate, false_neg_rate = roc[threshold]
        row = [threshold, false_pos_rate, false_neg_rate]
        writer.writerow(row)
    return 0

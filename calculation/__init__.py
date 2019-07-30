from typing import Callable, TextIO, List, Any, Pattern, Dict, Sequence, Tuple, Optional
import csv
import logging


_log = logging.getLogger(__name__)


def _IDENTITY(x):
    return x


class Ignorer(object):

    num_ignores = 0
    max_notices = 10

    def __call__(self, row_index, input_value, exception):
        if self.num_ignores < self.max_notices:
            _log.debug(" ignored value at row %d", row_index)
        elif self.num_ignores == self.max_notices:
            _log.debug(" ignored %d values; suppressing ignore notices from now on", self.num_ignores)
        self.num_ignores += 1
        return None


class ValueParser(object):

    def __init__(self, parse_value: Callable[[str], Any], value_filter: Callable[[List[str]], bool], mal_decision: Callable=None, clamp: Callable=None):
        self.parse_value = parse_value
        self.value_filter = value_filter
        self.mal_decision = mal_decision or Ignorer()
        self.num_ignored = 0
        self.clamp = clamp or _IDENTITY

    def _handle_bad(self, v_str: str, r: int, e: Exception, values: list):
        u = self.mal_decision(r, v_str, e)
        if u is not None:
            v = self.parse_value(u)
            values.append(self.clamp(v))
        else:
            self.num_ignored += 1

    def read_values(self, ifile: TextIO, skip: int=0, values_col: int=0) -> List[Any]:
        values = []
        reader = csv.reader(ifile)
        nskipped = 0
        for r, row in enumerate(reader):
            if nskipped < skip:
                nskipped += 1
                continue
            if self.value_filter(row):
                try:
                    v_str = row[values_col]
                except IndexError as e:
                    self._handle_bad('', r, e, values)
                    continue
                try:
                    v = self.parse_value(v_str)
                    values.append(self.clamp(v))
                except ValueError as e:
                    self._handle_bad(v_str, r, e, values)
        return values


def make_clamp(bounds: Optional[Tuple[str, str]], value_type: type) -> Callable:
    if bounds is None:
        return _IDENTITY
    value_min, value_max = tuple(map(value_type, bounds))
    assert value_min <= value_max

    def clamp(x):
        if x < value_min:
            return value_min
        if x > value_max:
            return value_max
        return x
    return clamp


def build_parse_value(value_type: type, invert: bool) -> Callable[[str], Any]:
    _log.debug(" reading values as type %s with invert=%s", value_type, invert)
    if invert:
        return lambda x: -(value_type(x))
    return value_type

from calculation import histo
from calculation.histo import ValueParser
from unittest import TestCase
import io
import re


class ValueParserTest(TestCase):

    def test_read_values(self):
        text = """\
1,a,b
2,a,c
3,b,c
4,c,d
5,e,f
"""
        ifile = io.StringIO(text)
        vf = histo._build_row_filter([re.compile('b'), re.compile('x')])
        instance = ValueParser(int, vf)
        values = instance.read_values(ifile)
        self.assertListEqual([2, 4, 5], values)


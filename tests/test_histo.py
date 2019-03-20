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
        vf = histo.build_filter_from_patterns([re.compile('b'), re.compile('x')])
        instance = ValueParser(int, vf)
        values = instance.read_values(ifile)
        self.assertListEqual([2, 4, 5], values)


class ModuleTest(TestCase):

    def test__remove_suffix(self):
        test_cases = [
            ('abcd', 'd', None, 'abc'),
            ('', '', None, ''),
            ('abcd', 'e', None, 'abcd'),
            ('abc', '', None, 'abc'),
            ('abcd', 'c', ['d'], 'abc'),
        ]
        for string, suffix, suffixes, expected in test_cases:
            with self.subTest():
                actual = histo._remove_suffix(string, suffix, suffixes)
                self.assertEqual(expected, actual)

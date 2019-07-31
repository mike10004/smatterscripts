import logging
from unittest import TestCase

from shelltools import csvutils

_log = logging.getLogger(__name__)


class ModuleMethodsTest(TestCase):

    def test__IDENTITY(self, identity=csvutils._IDENTITY, test_cases=(None, 0, -1, 1, float('inf'), -0.5, 0.5, 'x')):
        with self.subTest():
            for x in test_cases:
                y = identity(x)
                self.assertIs(x, y)

    def test__make_clamp_None(self):
        actual = csvutils.make_clamp(None, float)
        self.assertIs(csvutils._IDENTITY, actual)

    def test__make_clamp_inf(self):
        bounds = '0', 'inf'
        test_cases = [
            (0, 0),
            (0.001, 0.001),
            (-0.001, 0.0),
            (1, 1),
            (-1, 0),
            (100, 100),
            (float('-inf'), 0),
            (float('inf'), float('inf')),
        ]
        clamp = csvutils.make_clamp(bounds, float)
        for val, expected in test_cases:
            actual = clamp(val)
            self.assertEqual(expected, actual)

    def test__make_clamp_negative_inf(self):
        bounds = '-inf', '0'
        test_cases = [
            (0, 0),
            (0.001, 0),
            (-0.001, -0.001),
            (1, 0),
            (-1, -1),
            (100, 0),
            (-100, -100),
            (float('inf'), 0),
            (float('-inf'), float('-inf')),
        ]
        clamp = csvutils.make_clamp(bounds, float)
        for val, expected in test_cases:
            actual = clamp(val)
            self.assertEqual(expected, actual)

    def test__make_clamp_closed(self):
        bounds = '-0.5', '0.5'
        test_cases = [
            (0, 0),
            (-0.5, -0.5),
            (-0.6, -0.5),
            (0.5, 0.5),
            (0.6, 0.5),
        ]
        clamp = csvutils.make_clamp(bounds, float)
        for val, expected in test_cases:
            actual = clamp(val)
            self.assertEqual(expected, actual)

    def test_build_parse_value(self):
        test_cases = [
            (float, None, '1.5', 1.5),
            (float, True, '1.5', -1.5),
            (float, None, '0', 0),
            (float, True, '0', 0),
            (int, True, '-1', 1),
        ]
        for value_type, invert, token, expected in test_cases:
            parse_value = csvutils.build_parse_value(value_type, invert)
            actual = parse_value(token)
            self.assertEqual(expected, actual)
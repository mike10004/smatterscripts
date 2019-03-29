from unittest import TestCase
from _common import strings

class ModuleTest(TestCase):

    def test_remove_suffix(self):
        test_cases = [
            ('abcd', 'd', None, 'abc'),
            ('', '', None, ''),
            ('abcd', 'e', None, 'abcd'),
            ('abc', '', None, 'abc'),
            ('abcd', 'c', ['d'], 'abc'),
        ]
        for string, suffix, suffixes, expected in test_cases:
            with self.subTest():
                actual = strings.remove_suffix(string, suffix, suffixes)
                self.assertEqual(expected, actual)

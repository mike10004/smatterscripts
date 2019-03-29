from unittest import TestCase
from _common import redaction
import re
import io


class ModuleTest(TestCase):

    def test_read_patterns(self):
        text = """\
# This is a comment of the whole line
\d+_\w+
        # this is a comment with preceding whitespace
12345    

abcdef 
"""
        file = io.StringIO(text)
        patterns = redaction.read_pattern_file(file)
        # noinspection PyTypeChecker
        expected = list(map(re.compile, [r'\d+_\w+', r'12345', r'abcdef']))
        self.assertListEqual(expected, patterns)
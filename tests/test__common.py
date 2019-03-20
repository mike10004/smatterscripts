from unittest import TestCase
from _common import NullTerminatedInput
import io

class NullTerminatedInputTest(TestCase):

    def test_read(self, x=None):
        x = x if x is not None else "a\0b\0c\0"
        nti = NullTerminatedInput(io.StringIO(x))
        lines = [line for line in nti]
        self.assertListEqual(['a', 'b', 'c'], lines)

    def test_bytesin(self):
        bits = b"a\0b\0c\0"
        chars = bits.decode('utf8')
        self.test_read(chars)
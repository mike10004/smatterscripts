from unittest import TestCase
from _common import NullTerminatedInput, StreamContext
import io
import os
import sys
import _common
import logging
import os.path
import tempfile


_log = logging.getLogger(__name__)


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


# noinspection PyMethodMayBeStatic
class StreamContextTest(TestCase):

    def setUp(self):
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.tempdir = self._temporary_directory.name

    def tearDown(self):
        self._temporary_directory.cleanup()

    def test_write_file(self):
        pathname = os.path.join(self.tempdir, 'hello.txt')
        with StreamContext(pathname, 'w') as ofile:
            print("hello, world", file=ofile)
        with open(pathname, 'r') as ifile:
            text = ifile.read().strip()
        self.assertEqual("hello, world", text)

    def test_read_file(self):
        pathname = os.path.join(self.tempdir, 'hello.txt')
        with open(pathname, 'w') as ofile:
            print("hello, world", file=ofile)
        with StreamContext(pathname, 'r') as ifile:
            text = ifile.read().strip()
        self.assertEqual("hello, world", text)

    def test_write_stdout_None(self):
        with StreamContext(None, 'w') as ofile:
            print("printing on stdout", file=ofile)
        self.assertTrue(sys.stdout.writable())

    def test_write_stdout_hyphen(self):
        with StreamContext('-', 'w') as ofile:
            print("printing on stdout", file=ofile)
        self.assertTrue(sys.stdout.writable())


class LoggingTest(TestCase):

    def test_level_strs(self):
        levels = list(map(lambda s: logging.__dict__[s], _common._LOG_LEVEL_CHOICES))
        self.assertEqual(len(levels), len(set(levels)))

import os
import os.path
from shelltools import streamproduct
from shelltools.streamproduct import Generator
from unittest import TestCase
import tempfile
import itertools
import logging


_log = logging.getLogger(__name__)


def write_items(iterator, pathname):
    with open(pathname, 'w') as ofile:
        for item in iterator:
            print(item, file=ofile)
    return pathname


class ModuleTest(TestCase):

    def test__has_dupes(self):
        test_cases = [
            ("", False),
            ("a", False),
            ("aa", True),
            ("ab", False),
            ("abc", False),
            ("aba", True),
            ("abcd", False),
        ]
        for seq, expected in test_cases:
            seq = tuple(seq)
            with self.subTest():
                actual = streamproduct._has_dupes(seq)
                self.assertEqual(expected, actual, str(seq))


class GeneratorTest(TestCase):

    def test_generate_twofiles(self):
        self._generate("abc", "de")

    def test_generate_twofiles_avoid_dupes(self):
        self._generate("abc", "dbe", avoid_dupes=True)

    def test_generate_samefile(self):
        chars = "abcd"
        with tempfile.TemporaryDirectory() as tempdir:
            pathname = os.path.join(tempdir, "file.txt")
            write_items(chars, pathname)
            self._generate_from_files([chars, chars], [pathname, pathname])

    def _generate(self, *iterables, avoid_dupes=False):
        with tempfile.TemporaryDirectory() as tempdir:
            pathnames = []
            for i, iterable in enumerate(iterables):
                pathname = os.path.join(tempdir, f"file{i}.txt")
                write_items(iterable, pathname)
                pathnames.append(pathname)
                _log.debug("wrote file %s", pathname)
            self._generate_from_files(iterables, pathnames, avoid_dupes)

    def _generate_from_files(self, iterables, pathnames, avoid_dupes=False):
        g = Generator()
        g.avoid_dupes = avoid_dupes
        generated = list(g.generate(pathnames))
        expected = set(itertools.product(*iterables))
        if avoid_dupes:
            expected = set(filter(lambda combo: len(combo) == len(set(combo)), expected))
        self.assertSetEqual(expected, set(generated))

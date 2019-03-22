import os
import os.path
from shelltools import streamproduct
from unittest import TestCase
import tempfile
import itertools


class ModuleTest(TestCase):

    def test_generate(self):
        c1, c2 = "abc", "de"
        with tempfile.TemporaryDirectory() as tempdir:
            p1 = os.path.join(tempdir, "f1.txt")
            p2 = os.path.join(tempdir, "f2.txt")
            with open(p1, 'w') as ofile:
                print(os.linesep.join(c1), end="", file=ofile)
            with open(p2, 'w') as ofile:
                print(os.linesep.join(c2), file=ofile)
            generated = list(streamproduct.generate([p1, p2]))
        expected = set(itertools.product(c1, c2))
        self.assertSetEqual(expected, set(generated))
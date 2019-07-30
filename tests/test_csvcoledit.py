from unittest import TestCase
from shelltools import csvcoledit
# noinspection PyProtectedMember
from shelltools.csvcoledit import Swapper, Deleter, _parse_colspec
import io


class SwapperTest(TestCase):

    def test___call__(self):
        swap = Swapper(2, 3)
        row = list('abcdef')
        swap(row)
        self.assertEqual(''.join(row), 'abdcef')


class DeleterTest(TestCase):

    def test___call__(self):
        delete = Deleter({1, 4})
        row = list('abcdefghij')
        delete(row)
        self.assertEqual(''.join(row), 'acdfghij')


class ModuleTest(TestCase):

    def test__parse_colspec_2(self):
        self.assertEqual(_parse_colspec('4,5'), {4, 5})

    def test__parse_colspec_1(self):
        self.assertEqual(_parse_colspec('4'), {4})

    def test__parse_colspec_1_malf(self):
        self.assertEqual(_parse_colspec('4,'), {4})

    def test__parse_colspec_2_malf(self):
        self.assertEqual(_parse_colspec('4,,7'), {4, 7})

    def test__parse_colspec_3(self):
        self.assertEqual(_parse_colspec('4,5,8'), {4, 5, 8})

    def test_operate(self):
        ifile = io.StringIO("""\
a,b,c,d,e,f
g,h,i,j,k,l
m,n,o,p,q,r
""")
        ofile = io.StringIO()
        operations = [
            Deleter({2}),
            Swapper(0, 4)
        ]
        expected = """\
f,b,d,e,a
l,h,j,k,g
r,n,p,q,m
"""
        csvcoledit.operate(ifile, ofile, operations, writer_kwargs={'lineterminator': "\n"})
        actual = ofile.getvalue()
        self.assertEqual(expected, actual)


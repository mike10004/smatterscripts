import io
import re
import os.path
import logging
import operator
import tempfile
from argparse import Namespace
from unittest import TestCase
from _common import redaction
from shelltools import htmljux
from operator import itemgetter

_log = logging.getLogger(__name__)



def make_transform(**kwargs):
    kwargs_ = dict(image_root=None, scheme='file', remove_prefix=None, remove_suffix=None)
    kwargs_.update(kwargs)
    args = Namespace(**kwargs_)
    return htmljux.make_cell_value_transform(args)


class MakeCellValueTransformTest(TestCase):

    def test_urlencode(self):
        unsafe_path = 'foo/bar:baz~gaw.xyz'
        t = make_transform(image_root='/x/y')
        actual = t(unsafe_path).url
        try:
            self.assertEqual("file:///x/y/foo/bar%3Abaz%7Egaw.xyz", actual)
        except AssertionError:
            self.assertEqual("file:///x/y/foo/bar%3Abaz~gaw.xyz", actual)

    def test_scheme_http(self):
        cell_value = 'example.com/foo.bar'
        t = make_transform(scheme='http')
        actual = t(cell_value)
        self.assertEqual("http://example.com/foo.bar", actual.url)
        self.assertEqual("foo.bar", actual.title)


class PerformTest(TestCase):

    def test_perform(self):
        csv_text = """\
1,/foo/bar.jpg,/baz/g:url-unsafe:aw.jpg
2,rel/path/c.jpg,/abs/path/d.gif
"""
        buffer = io.StringIO()
        transform = make_transform(image_root='/x/y')
        extractor = htmljux.Extractor(0, None, None, transform)
        htmljux.perform(io.StringIO(csv_text), extractor, ofile=buffer)
        html = buffer.getvalue()
        _log.debug(html)
        html = html or None
        self.assertIsNotNone(html)
        self.assertTrue('file:///baz/g%3Aurl-unsafe%3Aaw.jpg' in html, "URL not found in html")

    def test_perform_tab(self):
        csv_text = """\
1\t/foo/bar.jpg\t/baz/g:url-unsafe:aw.jpg
caption,with,commas\trel/path/c.jpg\t/abs/pa,t,h/d.gif
"""
        buffer = io.StringIO()
        transform = make_transform(image_root='/x/y')
        extractor = htmljux.Extractor(0, None, {'delimiter': "\t"}, transform)
        htmljux.perform(io.StringIO(csv_text), extractor, ofile=buffer)
        html = buffer.getvalue()
        _log.debug(html)
        html = html or None
        self.assertIsNotNone(html)
        self.assertTrue('/abs/pa%2Ct%2Ch/d.gif' in html, "URL not found in html")
        self.assertTrue('>d.gif<' in html, "title not found in html")
        self.assertTrue('caption,with,commas' in html, "caption not found in html")


class ModuleTest(TestCase):

    def test_main(self):
        stderr = io.StringIO()
        exit_code = htmljux.main(['--images', '3,a,5'], stderr=stderr)
        self.assertEqual(1, exit_code)
        content = stderr.getvalue()
        self.assertTrue(content or False)

    def test_main_print_template(self):
        stdout = io.StringIO()
        exit_code = htmljux.main(['--print-template'], stdout=stdout)
        self.assertEqual(0, exit_code)
        content = stdout.getvalue()
        self.assertEqual(htmljux.DEFAULT_TEMPLATE, content)

    def test_lots_of_options(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_file = os.path.join(tmpdir, "input.csv")
            with open(csv_file, 'w') as ofile:
                ofile.write("""\
A,B,C,D,E,F,G,H,I
1,2,ab,cd,ef.xyz,gh,ij,kl.xyz
1,5,mn,op,qr.xyz,st,uv,wx.xyz
2,2,ab,cd,ef.xyz,gh,ij,kl.xyz
3,5,mn,op,qr.xyz,st,uv,wx.xyz
4,2,ab,cd,ef.xyz,gh,yolo,kl.xyz
5,5,mn,op,qr.xyz,st,uv,wx.xyz
1,2,ab,cd,ef.xyz,gh,ij,kl.xyz
3,5,mn,op,yolo.xyz,st,uv,wx.xyz
6,2,ab,cd,ef.xyz,gh,ij,kl.xyz
1,5,mn,op,qr.xyz,st,uv,wx.xyz
""")
            redactions_file = os.path.join(tmpdir, "redactions.txt")
            with open(redactions_file, 'w') as ofile:
                print("yolo", file=ofile)
            argl = ["--caption", "0", "--images", "4,7", "--skip", "1",
                    "--image-root", "/path/to/images",
                    "--remove-suffix", '.xyz', "--redact-patterns", redactions_file,
                    "--limit", "5", "--sort=-numeric", csv_file]
            buffer = io.StringIO()
            exit_code = htmljux.main(argl, stdout=buffer)
            html = buffer.getvalue()
            print(html)
            self.assertIsNotNone(html)
            self.assertEqual(0, exit_code)


class RowFiltersTest(TestCase):

    def setUp(self):
        self.all_rows = [
            ['3', 'abc', 'def'],
            ['1', '234', 'xyz'],
            ['0', 'ert', '41231'],
            ['8'],
            [''],
            ['x', 'y'],
            ['oxo', '123', 'yuio'],
        ]

    def _filter_rows(self, predicate, rows=None):
        if rows is None:
            rows = self.all_rows
        return list(map(itemgetter(1), filter(predicate, enumerate(rows))))

    def test_make_row_pre_filter_redactor(self):
        redactor = redaction.build_filter_from_patterns([re.compile(r'123'), re.compile('^8$'), re.compile('3,abc')])
        predicate = htmljux.make_row_pre_filter(None, redactor)
        expected = [self.all_rows[i] for i in (0, 1, 4, 5)]
        actual = self._filter_rows(predicate)
        self.assertListEqual(expected, actual)

    def test_make_row_filters_slice(self):
        original_rows = list(self.all_rows)
        n = len(original_rows)
        test_cases = [
            # skip, offset, indexes of expected rows
            (None, None, range(n)),
            (None, 3, range(3)),
            (None, 0, []),
            (None, 1000, range(n)),
            (4, None, range(4, n)),
            (4, 1000, range(4, n)),
            (2, 3, range(2, 5)),
        ]
        for skip, limit, indexes in test_cases:
            with self.subTest():
                rows = list(self.all_rows)
                expected = [original_rows[i] for i in indexes]
                pre_predicate = htmljux.make_row_pre_filter(skip, None)
                post_predicate = htmljux.make_row_post_filter(limit)
                rows = self._filter_rows(pre_predicate, rows)
                rows = self._filter_rows(post_predicate, rows)
                self.assertListEqual(expected, rows)

    def test_make_row_predicate_redactor_and_limit(self):
        redactor = redaction.build_filter_from_patterns([re.compile(r'x')])
        pre_predicate = htmljux.make_row_pre_filter(None, redactor)
        post_predicate = htmljux.make_row_post_filter(2)
        expected = [self.all_rows[i] for i in (0, 2)]
        rows = self.all_rows[:4]
        rows = self._filter_rows(pre_predicate, rows)
        rows = self._filter_rows(post_predicate, rows)
        self.assertListEqual(expected, rows)


class MakeSortKeyTest(TestCase):

    def test_blah(self):
        items = [('10',), ('1',), ('5',)]
        sorted_items = sorted(items, key=lambda x: int(x[0]))
        self.assertEqual([('1',), ('5',), ('10',)], sorted_items)


    def test_make_sort_key(self):
        items = ['10', '1', '5']
        test_cases = [
            # sort_key_def, caption_column, expected
            (None, None, ['1', '10', '5']),
            (None, 0, ['1', '10', '5']),
            ('lex', 0, ['1', '10', '5']),
            ('lexicographical', 0, ['1', '10', '5']),
            ('numeric', 0, ['1', '5', '10']),
            ('lex:0', None, ['1', '10', '5']),
            ('-lex:0', None, reversed(['1', '10', '5'])),
            ('lexicographical:0', None, ['1', '10', '5']),
            ('numeric:0', None, ['1', '5', '10']),
            ('-numeric:0', None, ['10', '5', '1']),
        ]
        to_rows = lambda items_: list(map(lambda x: tuple([x]), items_))
        for sort_key_def, caption_column, expected in test_cases:
            with self.subTest():
                rows = to_rows(items)
                sort_key, reverse = htmljux.make_sort_key(sort_key_def, caption_column) or (None, False)
                sorted_items = sorted(rows, key=sort_key, reverse=reverse)
                expected = to_rows(expected)
                self.assertListEqual(expected, sorted_items)


class ExtractorTest(TestCase):

    def test__enumerate_rows_sort_numeric(self):
        csv_text = """\
10,a,b
1,x,y
5,j,k
"""
        sort_key = htmljux.make_sort_key("numeric:0", None)
        sorted_rows = list(map(operator.itemgetter(1), htmljux.Extractor()._enumerate_rows(io.StringIO(csv_text), None, sort_key, None)))
        self.assertListEqual([['1', 'x', 'y'], ['5', 'j', 'k'], ['10', 'a', 'b']], sorted_rows)

    def test__enumerate_rows_sort_and_limit(self):
        csv_text = """\
10,a,b
1,x,y
5,j,k
"""
        sort_key = htmljux.make_sort_key("-numeric:0", None)
        pre_predicate = htmljux.make_row_pre_filter(0, None)
        post_predicate = htmljux.make_row_post_filter(2)
        sorted_rows = list(
            map(operator.itemgetter(1), htmljux.Extractor()._enumerate_rows(io.StringIO(csv_text), pre_predicate, sort_key, post_predicate)))
        self.assertListEqual([['10', 'a', 'b'], ['5', 'j', 'k']], sorted_rows)


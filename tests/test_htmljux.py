import io
import logging
import operator
from argparse import Namespace
from unittest import TestCase

from shelltools import htmljux

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
        self.assertEqual("file:///x/y/foo/bar%3Abaz%7Egaw.xyz", actual)

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
        htmljux.perform(io.StringIO(csv_text), extractor, None, None, ofile=buffer)
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
        htmljux.perform(io.StringIO(csv_text), extractor, None, None, ofile=buffer)
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
        exit_code = htmljux.main(['foo', '--images', '3,a,5'], stderr=stderr)
        self.assertEqual(1, exit_code)
        content = stderr.getvalue()
        self.assertTrue(content or False)

    def test_main_print_template(self):
        stdout = io.StringIO()
        exit_code = htmljux.main(['foo', '--print-template'], stdout=stdout)
        self.assertEqual(0, exit_code)
        content = stdout.getvalue()
        self.assertEqual(htmljux.DEFAULT_TEMPLATE, content)


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

    def test__enumerate_rows(self):
        csv_text = """\
10,a,b
1,x,y
5,j,k
"""
        sort_key = htmljux.make_sort_key("numeric:0", None)
        sorted_rows = list(map(operator.itemgetter(1), htmljux.Extractor()._enumerate_rows(io.StringIO(csv_text), sort_key, None)))
        self.assertListEqual([['1', 'x', 'y'], ['5', 'j', 'k'], ['10', 'a', 'b']], sorted_rows)

    def test__enumerate_rows_sort_and_limit(self):
        csv_text = """\
10,a,b
1,x,y
5,j,k
"""
        sort_key = htmljux.make_sort_key("-numeric:0", None)
        predicate = htmljux.make_row_predicate(0, 2)
        sorted_rows = list(
            map(operator.itemgetter(1), htmljux.Extractor()._enumerate_rows(io.StringIO(csv_text), sort_key, predicate)))
        self.assertListEqual([['10', 'a', 'b'], ['5', 'j', 'k']], sorted_rows)


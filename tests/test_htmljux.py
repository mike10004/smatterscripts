import io
import logging
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
        htmljux.perform(io.StringIO(csv_text), extractor, None, ofile=buffer)
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
        htmljux.perform(io.StringIO(csv_text), extractor, None, ofile=buffer)
        html = buffer.getvalue()
        _log.debug(html)
        html = html or None
        self.assertIsNotNone(html)
        self.assertTrue('/abs/pa%2Ct%2Ch/d.gif' in html, "URL not found in html")
        self.assertTrue('>d.gif<' in html, "title not found in html")
        self.assertTrue('caption,with,commas' in html, "caption not found in html")
        #self.assertEqual(expected, html)


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
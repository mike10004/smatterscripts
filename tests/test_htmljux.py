from unittest import TestCase
import io
from shelltools import htmljux

class PerformTest(TestCase):

    def test_perform(self):
        csv_text = """\
1,/foo/bar.jpg,/baz/g:url-unsafe:aw.jpg
2,rel/path/c.jpg,/abs/path/d.gif
"""
        buffer = io.StringIO()
        extractor = htmljux.Extractor(0, None, parent_dir='/x/y')
        htmljux.perform(io.StringIO(csv_text), extractor, ofile=buffer)
        html = buffer.getvalue()
        print(html)
        html = html or None
        self.assertIsNotNone(html)
        self.assertTrue('file:///baz/g%3Aurl-unsafe%3Aaw.jpg')
        #self.assertEqual(expected, html)

    def test_perform_tab(self):
        csv_text = """\
1\t/foo/bar.jpg\t/baz/g:url-unsafe:aw.jpg
caption,with,commas\trel/path/c.jpg\t/abs/pa,t,h/d.gif
"""
        buffer = io.StringIO()
        extractor = htmljux.Extractor(0, None, parent_dir='/x/y')
        htmljux.perform(io.StringIO(csv_text), extractor, csv_args={'delimiter': "\t"}, ofile=buffer)
        html = buffer.getvalue()
        print(html)
        html = html or None
        self.assertIsNotNone(html)
        self.assertTrue('/abs/pa%2Ct%2Ch/d.gif' in html)
        self.assertTrue('caption,with,commas' in html)
        #self.assertEqual(expected, html)


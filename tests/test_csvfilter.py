#!/usr/bin/env python3

from unittest import TestCase

import csv
import io
from shelltools import csvfilter


class ModuleMethodsTest(TestCase):

    def test_do_filter(self):
        input_rows = [
            ['0.2',  'a'],
            ['-0.2',  'b'],
            ['0.4',  'c'],
            ['0.1',  'd'],
            ['-0.3',  'e'],
            ['0.11', 'f'],
        ]
        input_text = "\n".join(",".join(row) for row in input_rows)
        buffer = io.StringIO()
        f = csvfilter.Filter(0.05, 'ge', None)
        exit_code = csvfilter.do_filter(io.StringIO(input_text), f, buffer)
        self.assertEqual(0, exit_code)
        output_rows = [row for row in csv.reader(io.StringIO(buffer.getvalue()))]
        self.assertSetEqual({'a', 'c', 'd', 'f'}, set(row[1] for row in output_rows))



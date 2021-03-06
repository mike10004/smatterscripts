from calculation import histo
from calculation.histo import ValueParser
from unittest import TestCase
from argparse import Namespace
import io
import re
import os
import csv
import random
import os.path
import logging
import tempfile


_log = logging.getLogger(__name__)


class ValueParserTest(TestCase):

    def test_read_values(self):
        text = """\
1,a,b
2,a,c
3,b,c
4,c,d
5,e,f
"""
        ifile = io.StringIO(text)
        vf = histo._build_row_filter([re.compile('b'), re.compile('x')])
        instance = ValueParser(int, vf)
        values = instance.read_values(ifile)
        self.assertListEqual([2, 4, 5], values)


class ModuleMethodsTest(TestCase):

    def test_read_config(self):
        args = histo._create_arg_parser().parse_args(["/tmp/somefile.txt"])
        config = histo.read_config(args)
        self.assertIsInstance(config, dict)

    def test__load_implicit_patterns_emptyconfig(self):
        config = {}
        patterns = histo._load_implicit_patterns(config)
        self.assertListEqual([], patterns)

    def test_print_histo_basic(self):
        rng = random.Random(0xdeadbeef)
        with tempfile.TemporaryDirectory() as tempdir:
            data = [[rng.normalvariate(0, 1), chr(65 + (i%26))] for i in range(1000)]
            datafile = os.path.join(tempdir, 'data.csv')
            with open(datafile, 'w') as ofile:
                for row in data:
                    print(",".join(map(str, row)), file=ofile)
            num_bins = 12
            args = histo._create_arg_parser().parse_args(list(map(str, ["--bins", -3, 0.5, "--bin-precision", 1, "-n", num_bins, datafile])))
            buffer = io.StringIO()
            histo.print_histo(args, buffer)
            histo_text = buffer.getvalue()
            _log.debug("\n\n%s\n\n", histo_text)
            self.assertTrue(histo_text and True)
            histo_rows = list(csv.reader(io.StringIO(histo_text)))
            self.assertEqual(num_bins, len(histo_rows))
            total_freq = 0
            for r, histo_row in enumerate(histo_rows):
                label, freq = histo_row
                try:
                    float(label)  # bin should not be 'Less' or 'More'
                except ValueError:
                    self.fail(f"expect parseable float at row {r} (label {label}; frequency {freq})")
                total_freq += int(freq)
            self.assertEqual(len(data), total_freq)


#!/usr/bin/env python3

from shelltools import ressample
from unittest import TestCase
from argparse import Namespace
import random


class ModuleTest(TestCase):

    def test_partial(self):
        n, k = 100, 10
        sample = ressample.get_reservoir_sample(range(n), k, Namespace(conserve=False))
        self.assertEqual(k, len(sample))
        self.assertEqual(len(sample), len(set(sample)))
        container = set(range(n))
        for item in sample:
            self.assertIn(item, container)

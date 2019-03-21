#!/usr/bin/env python3

import random
from unittest import TestCase

from shelltools.ressample import ReservoirSampler

_TEST_SEED = 0xDeadBeef


class ReservoirSamplerTest(TestCase):

    def setUp(self):
        self.rng = random.Random(_TEST_SEED)
        self.expected10 = [37, 1, 60, 3, 75, 28, 42, 40, 81, 29]

    def test_partial(self):
        n, k = 100, 10
        sampler = ReservoirSampler(self.rng)
        sample = sampler.collect(range(n), k)
        self.assertListEqual(self.expected10, sample)

    def test_preserve_order(self):
        k = 5
        items = "zyxwvutsrqponmlkjihgfedcba"
        sampler = ReservoirSampler(self.rng)
        sampler.preserve_order = True
        sample = sampler.collect(items.__iter__(), k)
        self.assertListEqual(sorted(['a', 'c', 'u', 'x', 'y'], reverse=True), sample)

    def test_samesize(self):
        n = 25
        k = n
        sampler = ReservoirSampler(self.rng)
        sample = sampler.collect(range(n), k)
        self.assertSetEqual(set(range(n)), set(sample))

    def test_notenough(self):
        n, k = 5, 20
        sampler = ReservoirSampler(self.rng)
        sample = sampler.collect(range(n), k)
        self.assertListEqual(list(range(n)), sample)


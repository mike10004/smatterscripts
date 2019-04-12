#!/usr/bin/env python3

from unittest import TestCase

from calculation import roc
from calculation.roc import Element
import random


class ModuleMethodsTest(TestCase):

    def setUp(self):
        self.rng = random.Random(0xbad1dea)

    def test_roc_transform(self):
        n = 1000
        domain_size = 100
        known_negatives = [self.rng.normalvariate(0.35, 0.1) for _ in range(n)]
        known_positives = [self.rng.normalvariate(0.7, 0.05) for _ in range(n)]
        elements = Element.list(known_negatives, False) + Element.list(known_positives, True)
        domain = [i / 100 for i in range(domain_size)]
        curve = roc.roc_transform(elements, domain)
        self.assertEqual(len(curve), domain_size)


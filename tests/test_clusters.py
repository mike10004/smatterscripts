from unittest import TestCase
import io
from shelltools import clusters
import logging



class UndirectedEdgeTest(TestCase):

    def test_create(self):
        edge = clusters.UndirectedEdge('a', 'b', 3.0)
        self.assertIsInstance(edge, frozenset)
        self.assertEqual(2, len(edge))
        self.assertEqual(3.0, edge.weight)
        self.assertIn('a', edge)
        self.assertIn('b', edge)

from unittest import TestCase
import io
from shelltools.clusters import UndirectedEdge, UndirectedAdjacencySetGraph, EdgeParser
import logging


_log = logging.getLogger(__name__)

class UndirectedEdgeTest(TestCase):

    def test_create(self):
        edge = UndirectedEdge('a', 'b', 3.0)
        self.assertIsInstance(edge, frozenset)
        self.assertEqual(2, len(edge))
        self.assertEqual(3.0, edge.weight)
        self.assertIn('a', edge)
        self.assertIn('b', edge)
        self.assertEqual(frozenset({'a', 'b'}), edge)
        self.assertEqual(frozenset({'b', 'a'}), edge)
        self.assertEqual(UndirectedEdge('a', 'b'), edge)
        self.assertEqual(UndirectedEdge('a', 'b', 0), edge)


class GraphTest(TestCase):

    def test_neighbors(self):
        edges = [
            UndirectedEdge('a', 'b'),
            UndirectedEdge('c', 'b'),
            UndirectedEdge('a', 'd'),
            UndirectedEdge('e', 'f'),
            UndirectedEdge('g', 'f'),
            UndirectedEdge('a', 'x'),
        ]
        g = UndirectedAdjacencySetGraph(edges)
        neighbors = g.neighbors('a')
        self.assertSetEqual({'b', 'd', 'x'}, set(neighbors))

    def test_reachable_from(self):
        edges = [
            UndirectedEdge('a', 'b'),
            UndirectedEdge('c', 'b'),
            UndirectedEdge('a', 'd'),
            UndirectedEdge('e', 'f'),
            UndirectedEdge('e', 'g'),
            UndirectedEdge('y', 'f'),
            UndirectedEdge('g', 'f'),
            UndirectedEdge('c', 'x'),
        ]
        g = UndirectedAdjacencySetGraph(edges)
        reachables = set(g.reachable_from('a'))
        self.assertSetEqual({'b', 'c', 'd', 'x'}, reachables)

    def test_connected_subgraphs(self):
        edges = [
            UndirectedEdge('a', 'b'),
            UndirectedEdge('c', 'b'),
            UndirectedEdge('a', 'd'),
            UndirectedEdge('e', 'f'),
            UndirectedEdge('e', 'g'),
            UndirectedEdge('y', 'f'),
            UndirectedEdge('g', 'f'),
            UndirectedEdge('c', 'x'),
            UndirectedEdge('k', 'j'),
            UndirectedEdge('k', 'm'),
            UndirectedEdge('p', 'n'),
        ]
        g = UndirectedAdjacencySetGraph(edges)
        subgraphs = set(g.connected_subgraphs())
        self.assertSetEqual({
            frozenset({'a', 'b', 'c', 'd', 'x'}),
            frozenset({'e', 'f', 'g', 'y'}),
            frozenset({'j', 'k', 'm'}),
            frozenset({'p', 'n'}),
        }, subgraphs)

    def test_vertexes(self):
        edges = [
            UndirectedEdge('a', 'b'),
            UndirectedEdge('c', 'b'),
            UndirectedEdge('a', 'd'),
            UndirectedEdge('e', 'f'),
            UndirectedEdge('e', 'g'),
            UndirectedEdge('y', 'f'),
            UndirectedEdge('g', 'f'),
            UndirectedEdge('c', 'x'),
            UndirectedEdge('k', 'j'),
            UndirectedEdge('k', 'm'),
            UndirectedEdge('p', 'n'),
        ]
        g = UndirectedAdjacencySetGraph(edges)
        vertexes = set(g.vertexes())
        self.assertSetEqual(set("abcdefgyxjkmnp"), vertexes)


class EdgeParserTest(TestCase):

    def test_parse_edges(self):
        weights = {
            ('a', 'b'): 2,
            ('b', 'c'): 5,
            ('c', 'd'): 2,
            ('b', 'e'): -9,
            ('d', 'e'): 14,
        }
        text = "\n".join([','.join(map(str, (v, k[0], k[1]))) for k, v in weights.items()])
        p = EdgeParser(0, 1, 2, int)
        edges = p.parse_edges(io.StringIO(text))
        for pair in map(frozenset, ["ab", "bc", "cd", "be", "de"]):
            self.assertIn(pair, edges)
        for pair, weight in weights.items():
            edge = list(filter(lambda e: e == frozenset(pair), edges))[0]
            self.assertEqual(weight, edge.weight)


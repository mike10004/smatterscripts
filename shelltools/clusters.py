#!/usr/bin/env python3

import sys
import csv
import argparse
import logging
import _common
from typing import TextIO, Callable, Any, Set, List, FrozenSet, Collection, Iterator, Iterable


_log = logging.getLogger(__name__)
_ALWAYS_TRUE = lambda x: True


class UndirectedEdge(frozenset):

    """Class that represents a graph edge with mutable weight."""

    weight = None

    # noinspection PyUnusedLocal
    def __init__(self, a, b, weight=None):
        super().__init__()

    def __new__(cls, a, b, weight=None):
        instance = super(UndirectedEdge, cls).__new__(cls, [a, b])
        instance.weight = weight
        return instance

    def other(self, c):
        if c not in self:
            raise ValueError("vertex not one of this edge's endpoints")
        return tuple(filter(lambda x: x != c, self))[0]


class UndirectedAdjacencySetGraph(object):

    """Graph implementation. Does not accommodate unconnected vertexes."""

    def __init__(self, edges: Iterable[UndirectedEdge]):
        self.edge_set = set(edges)

    def vertexes(self) -> Iterator:
        seen = set()
        for edge in self.edges():
            a, b = edge
            if a not in seen:
                seen.add(a)
                yield a
            if b not in seen:
                seen.add(b)
                yield b

    def edges(self, edge_filter: Callable[[UndirectedEdge], bool]=None) -> Iterator[UndirectedEdge]:
        edge_filter = edge_filter or _ALWAYS_TRUE
        return filter(edge_filter, self.edge_set)

    def neighbors(self, v) -> Iterator:
        """Return an iterable of neighbors of a vertex."""
        return map(lambda edge: edge.other(v), self.edges(lambda edge: v in edge))

    def reachable_from(self, origin) -> Iterable:
        """Return a depth-first iterable of vertexes reachable from a given origin.
        Returned iterable does not include the origin."""
        accum = set()
        return self._reachable_from(origin, origin, accum)

    def _reachable_from(self, v, origin, accum: Set) -> Iterable:
        to_do = []
        for u in self.neighbors(v):
            if u not in accum and u != origin:
                accum.add(u)
                to_do.append(u)
        for u in to_do:
            self._reachable_from(u, origin, accum)
        return accum

    def connected_subgraphs(self, include_trivial: bool=False) -> Iterator[FrozenSet]:
        """Find all connected subgraphs and return the vertex set of each."""
        if include_trivial:
            yield frozenset()
        vertexes_seen = set()
        for v in self.vertexes():
            # Each vertex is part of exactly one connected subgraph, because if it
            # were part of two then those two subgraphs would be connected to each
            # other through that vertex. Therefore we can skip vertexes we've
            # already seen in a previously constructed subgraph.
            if v in vertexes_seen:
                continue
            connecteds = frozenset([v] + list(self.reachable_from(v)))
            vertexes_seen.update(connecteds)
            # support implementations with unconnected vertexes
            if include_trivial or len(connecteds) >= 2:
                yield connecteds


class EdgeParser(object):

    def __init__(self, weight_col=0, u_col=1, v_col=2, parse_weight: Callable[[str], Any]=float):
        self.weight_col = weight_col
        self.u_col = u_col
        self.v_col = v_col
        self.parse_weight = parse_weight

    def parse_edges(self, ifile: TextIO) -> List[UndirectedEdge]:
        edges = []
        for row in csv.reader(ifile):
            weight, u, v = self.parse_weight(row[self.weight_col]), row[self.u_col], row[self.v_col]
            edges.append(UndirectedEdge(u, v, weight))
        return edges


def process(ifile: TextIO, edge_parser: EdgeParser, weight_filter: Callable[[Any], bool]) -> Iterator[FrozenSet]:
    edges = edge_parser.parse_edges(ifile)
    edge_filter = lambda e: weight_filter(e.weight)
    graph = UndirectedAdjacencySetGraph(filter(edge_filter, edges))
    return graph.connected_subgraphs()


def render_subgraphs(subgraphs: Iterable[Collection], min_size: int=None, max_print: int=10, ofile: TextIO=sys.stdout):
    max_subgraph_size = max(map(len, subgraphs))
    subgraphs = sorted(subgraphs, key=len, reverse=True)
    _log.debug("%d connected subgraphs sastify criterion; max size = %d", len(subgraphs), max_subgraph_size)
    num_printed = 0
    for subgraph in subgraphs:
        if min_size is None and (len(subgraph) < max_subgraph_size):
            break
        if num_printed > max_print:
            break
        if min_size is not None and len(subgraph) < min_size:
            break
        rendering = ' '.join(subgraph)
        print(f"{len(subgraph)}: {rendering}", file=ofile)
        num_printed += 1


def make_weight_filter(operator: str, threshold: Any) -> Callable[[Any], bool]:
    return {
        'ge': lambda x: x >= threshold,
        'gt': lambda x: x >  threshold,
        'le': lambda x: x <= threshold,
        'lt': lambda x: x <  threshold,
        'eq': lambda x: x == threshold,
    }[operator]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--threshold", type=float, default=0.0, help="set connectedness threshold")
    parser.add_argument("-c", "--comparison", choices=('ge', 'gt', 'lt', 'le', 'eq'), help="operator to use when comparing weight to threshold")
    _common.add_logging_options(parser)
    parser.add_argument("--weight-col", type=int, default=0)
    parser.add_argument("--label-cols", type=int, nargs=2, default=(1, 2), help="indexes of columns containing vertex labels")
    parser.add_argument("--max-print", type=int, default=10)
    parser.add_argument("--min-size", type=int, metavar="N", help="show all clusters of size at least N; default is to show only the largest cluster")
    args = parser.parse_args()
    _common.config_logging(args)
    edge_parser = EdgeParser(args.weight_col, args.label_cols[0], args.label_cols[1])
    weight_filter = make_weight_filter(args.comparison, args.threshold)
    subgraphs = process(sys.stdin, edge_parser, weight_filter)
    render_subgraphs(subgraphs)
    return 0

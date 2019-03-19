#!/usr/bin/env python3

import sys
import csv
import argparse
import logging
from typing import TextIO, Callable, Any, Set, List


class UndirectedEdge(frozenset):

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


_ALWAYS_TRUE = lambda x: True


class UndirectedAdjacencySetGraph(object):

    def __init__(self, edges):
        self.edge_set = set(edges)

    def vertexes(self, edge_filter: Callable[[UndirectedEdge], bool]=None):
        edge_filter = edge_filter or _ALWAYS_TRUE
        seen = set()
        for edge in filter(edge_filter, self.edge_set):
            a, b = edge
            if a not in seen:
                seen.add(a)
                yield a
            if b not in seen:
                seen.add(b)
                yield b

    def edges(self, edge_filter: Callable[[UndirectedEdge], bool]=None):
        return filter(edge_filter, self.edge_set)

    def neighbors(self, v):
        return map(lambda edge: edge.other(v), self.edges(lambda edge: v in edge))

    def reachable_from(self, v, accum: Set=None):
        if accum is None:
            accum = set()
            accum.add(v)
        to_do = []
        for u in self.neighbors(v):
            if u not in accum:
                accum.add(u)
                to_do.append(u)
        for u in to_do:
            self.reachable_from(u, accum)
        return accum


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


def process(ifile: TextIO, edge_parser: EdgeParser, threshold: Any=0.0):
    edges = edge_parser.parse_edges(ifile)
    edge_filter = lambda e: e.weight >= threshold
    graph = UndirectedAdjacencySetGraph(filter(edge_filter, edges))
    # find all connected subgraphs (represented as sets of vertexes; edges are implicit)
    subgraphs = set()
    for v in graph.vertexes():
        # Each vertex is part of exactly one connected subgraph, because if it were part of two then those two
        # subgraphs would be connected to each other.
        # Therefore we can skip vertexes we've already collected in a previously constructed subgraph.
        already_seen = len([s for s in subgraphs if v in s]) > 0
        if already_seen:
            continue
        connecteds = frozenset(graph.reachable_from(v))
        if len(connecteds) >= 2:  ## only count nontrivial connected subgraphs
            subgraphs.add(connecteds)
    num_subgraphs = len(subgraphs)
    max_subgraph_size = max(map(len, subgraphs))
    print(f"{num_subgraphs} connected subgraphs at threshold {threshold}; max size = {max_subgraph_size}")
    return sorted(subgraphs, key=len, reverse=True)


def render(vertex_set):
    return ' '.join(vertex_set)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--threshold", type=float, default=0.0, help="set connectedness threshold")
    parser.add_argument("-l", "--log-level", choices=('DEBUG', 'INFO', 'WARNING', 'ERROR'), default='INFO', help="set log level", metavar="LEVEL")
    parser.add_argument("--weight-col", type=int, default=0)
    parser.add_argument("--u-col", type=int, default=1)
    parser.add_argument("--v-col", type=int, default=2)
    parser.add_argument("--max-print", type=int, default=10)
    parser.add_argument("--min-size", type=int, metavar="N", help="show all clusters of size at least N; default is to show only the largest cluster")
    args = parser.parse_args()
    logging.basicConfig(level=logging.__dict__[args.log_level])
    edge_parser = EdgeParser(args.weight_col, args.u_col, args.v_col)
    subgraphs = process(sys.stdin, edge_parser, threshold=args.threshold)
    num_printed = 0
    for subgraph in subgraphs:
        if args.min_size is None and (len(subgraph) < max(map(len, subgraphs))):
            break
        if num_printed > args.max_print:
            break
        if args.min_size is not None and len(subgraph) < args.min_size:
            break
        rendering = render(subgraph)
        print(f"{len(subgraph)}: {rendering}")
        num_printed += 1
    return 0

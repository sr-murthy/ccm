__all__ = [
    'XBytecodeGraph'
]

import inspect

from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Coroutine,
    Generator,
    Iterable,
    Optional,
    Type,
    Union,
)

from collections import OrderedDict
from itertools import (
    product,
    tee,
)

import networkx as nx
import numpy as np
import pygraphviz as pvz
import scipy as sp

from networkx import DiGraph

from .exceptions import (
    CCMError,
    CCMException,
)
from .xdis import XBytecode


class XBytecodeGraph(DiGraph):

    @classmethod
    def get_edges(
        cls,
        code: Optional[Union[str, Callable, Generator, AsyncGenerator, Coroutine, Type]] = None,
        instr_map: Optional[OrderedDict] = None
    ) -> Generator:
        """
        Generates edges corresponding to linked instructions in a map of
        ``XInstruction`` objects, either directly from code or a code-like
        object, or from a ``XInstruction`` map.
        """

        _instr_map = XBytecode(code) if code else instr_map

        instr_pairs = (
            (a, b) for a, b, in product(_instr_map.values(), _instr_map.values())
            if b.offset > a.offset
        )

        for instr_a, instr_b in instr_pairs:
            if instr_b.offset - 2 == instr_a.offset and not instr_a.is_exit_point: 
                yield (instr_a.offset, instr_b.offset) 
            if instr_b.is_jump_target and instr_a.arg == instr_b.offset: 
                yield (instr_a.offset, instr_b.offset)
            if instr_a.is_exit_point:
                yield (instr_a.offset, 0)
            if instr_b.is_exit_point:
                yield (instr_b.offset, 0)

    def get_subgraph(
        self,
        nodes: Optional[Iterable] = None,
        edges: Optional[Iterable] = None
    ) -> DiGraph:
        """
        Gets a subgraph of ``self`` containing only those nodes or edges
        provided by the corresponding optional arguments, and with an
        ``XInstruction`` map (attribute of the ``XBytecode`` attribute of
        ``self``) that only contains the given nodes or edges.
        """
        if not (edges or nodes):
            raise CCMException('Either a subset of nodes or edges must be provided')

        H = self.__class__(code=self.code)

        _nodes = nodes or [n for e in edges for n in e]

        to_remove = set(H.nodes).difference(_nodes)
        H.remove_nodes_from(to_remove)

        H.xbytecode.instr_map = {
            offset: instr
            for offset, instr in H.xbytecode.instr_map.items()
            if offset not in to_remove
        }

        it1, it2, it3, it4 = tee(H.xbytecode.instr_map.values(), 4)
        H._number_entry_points = sum(1 for instr in it1 if instr.is_entry_point)
        H._number_decision_points = sum(1 for instr in it2 if instr.is_decision_point)
        H._number_branch_points = sum(1 for instr in it3 if instr.is_branch_point)
        H._number_exit_points = sum(1 for instr in it4 if instr.is_exit_point)

        return H

    @classmethod
    def get_source_code_graph(
        cls,
        code: Optional[Union[str, Callable, Generator, Coroutine, AsyncGenerator, Type]] = None,
        xbytecode_graph: Optional[DiGraph] = None
    ):
        if not (code or xbytecode_graph):
            raise CCMException(
                'No code or XBytecodeGraph object available - this is required to '
                'construct a source code graph'
            )

        G = xbytecode_graph or self.__class__(code=code)
        instr_map = G.xbytecode.instr_map
        src_map = OrderedDict(
            (i, '{}\n'.format(l))
            for i, l in enumerate((l for l in inspect.getsource(G.code).split('\n') if l), start=1)
        )

        same_source_line = lambda i, j: instr_map[i].starts_line == instr_map[j].starts_line
        block_to_block = lambda B, C: any(edge in G.edges for edge in product(B, C))

        Q = nx.quotient_graph(G, same_source_line, edge_relation=block_to_block)
        block_relabelling = {B: instr_map[min(B)].starts_line for B in Q.nodes}
        nx.relabel_nodes(Q, block_relabelling, copy=False)
        for n, di in Q.nodes.items():
            Q.nodes[n].update({'src_line': src_map.get(n)})

        return Q

    def __init__(
        self,
        graph_data: Optional[Union[list, dict, nx.Graph, np.ndarray, np.matrix, sp.sparse.spmatrix, pvz.AGraph]] = None,
        code: Optional[Union[str, Callable, Generator, Coroutine, AsyncGenerator, Type]] = None,
        **graph_attrs: Any
    ) -> None:
        """
        A CPython "bytecode"-aware directed graph representing the CPython
        bytecode instruction stack of a Python method, generator, asynchronous
        generator, coroutine, class, string of source code, or code
        object (as returned by compile()).
        """
        self._code = self._xbytecode = self._source_code_graph = None
        self._number_entry_points = 0
        self._number_decision_points = 0
        self._number_branch_points = 0
        self._number_exit_points = 0

        if not (graph_data or code):
            super(self.__class__, self).__init__()
            return

        if graph_data:
            try:
                super(self.__class__, self).__init__(graph_data, **graph_attrs)
            except nx.NetworkXError:
                raise CCMError(
                    'Invalid graph data type for constructing an '
                    'XBytecodeGraph object '
                    '- acceptable types must be either a list, dict, '
                    'networkx.Graph, numpy.ndarray, numpy.matrix, '
                    'scipy.sparse.spmatrix, pygraphviz.AGraph'
                )
            return

        super(self.__class__, self).__init__()

        self._code = code
        try:
            self._xbytecode = XBytecode(self._code)
        except CCMError as e:
            raise

        self.add_edges_from(self.__class__.get_edges(instr_map=self._xbytecode.instr_map))

        it1, it2, it3, it4 = tee(self._xbytecode.instr_map.values(), 4)
        self._number_entry_points = sum(1 for instr in it1 if instr.is_entry_point)
        self._number_decision_points = sum(1 for instr in it2 if instr.is_decision_point)
        self._number_branch_points = sum(1 for instr in it3 if instr.is_branch_point)
        self._number_exit_points = sum(1 for instr in it4 if instr.is_exit_point)

        self._source_code_graph = self.__class__.get_source_code_graph(xbytecode_graph=self)

    @property
    def code(self):
        return self._code

    @property
    def xbytecode(self):
        return self._xbytecode

    @property
    def source_code_graph(self):
        return self._source_code_graph

    @source_code_graph.setter
    def source_code_graph(self, graph):
        self._source_code_graph = graph

    @property
    def number_entry_points(self):
        return self._number_entry_points

    @number_entry_points.setter
    def number_entry_points(self, n):
        self._number_entry_points = n

    @property
    def number_decision_points(self):
        return self._number_decision_points

    @number_decision_points.setter
    def number_decision_points(self, n):
        self._number_decision_points = n

    @property
    def number_branch_points(self):
        return self._number_branch_points

    @number_branch_points.setter
    def number_branch_points(self, n):
        self._number_branch_points = n

    @property
    def number_exit_points(self):
        return self._number_exit_points

    @number_exit_points.setter
    def number_exit_points(self, n):
        self._number_exit_points = n

__all__ = [
    'XBytecodeGraph'
]

import inspect

from types import CodeType

from typing import (
    Any,
    Callable,
    Dict as DictType,
    Generator,
    Iterable,
    Optional,
    Tuple,
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
from .xdis import (
    XBytecode,
    XInstruction,
)


class XBytecodeGraph(DiGraph):

    @classmethod
    def get_edges(
        cls,
        code: Optional[Union[str, CodeType, Callable]] = None,
        instr_map: Optional[DictType[Tuple[int, int], XInstruction]] = None
    ) -> Generator:
        """
        Generates edges corresponding to linked instructions in a map of
        ``XInstruction`` objects, either directly from code or a code-like
        object, or from a ``XInstruction`` map.
        """
        if not (code or instr_map):
            raise ValueError(
                'Either a code object or '
                'an XBytecode instruction map '
                'must be provided'
            )

        _instr_map = XBytecode(code).instr_map if code else instr_map

        instr_iter = iter(_instr_map.values())

        instr = next(instr_iter)
        offset = instr.offset
        src_line_no = instr.starts_line

        prev_instr = None
        prev_offset = None
        prev_src_line_no = None

        while offset is not None:
            if instr.is_exit_point:
                if prev_offset is not None:
                    yield (prev_offset, offset)
                yield (offset, 0)
            elif instr.is_branch_point:
                yield (offset, instr.arg)
            elif prev_offset is not None and not prev_instr.is_exit_point:
                yield (prev_offset, offset)

            prev_instr = instr
            prev_offset = offset
            prev_src_line_no = src_line_no

            try:
                instr = next(instr_iter)
                offset = instr.offset
                src_line_no = instr.starts_line
            except StopIteration:
                return

            if prev_instr.is_decision_point and instr.is_branch_point:
                yield (prev_offset, offset)

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
        code: Union[str, CodeType, Callable]
    ):
        instr_map = XBytecode(code).instr_map

        G = DiGraph()
        G.add_edges_from(cls.get_edges(instr_map=instr_map))

        src_map = OrderedDict(
            (i, '{}\n'.format(l))
            for i, l in enumerate((l for l in inspect.getsource(code).split('\n') if l), start=1)
        )

        def get_source_line(offset):
            try:
                src_line_no = [
                    (_src_line_no, _offset) for
                    (_src_line_no, _offset) in instr_map.keys()
                    if offset == _offset
                ][0][0]
            except IndexError:
                return
            else:
                return src_line_no

        def same_source_line(offset_1, offset_2):
            src_line_1 = get_source_line(offset_1)
            if src_line_1 is None:
                return False

            src_line_2 = get_source_line(offset_2)
            if src_line_2 is None:
                return False

            return (
                instr_map[(src_line_1, offset_1)].starts_line == 
                instr_map[(src_line_2, offset_2)].starts_line
            )

        def block_to_block(block_A, block_B):
            return any(edge in G.edges for edge in product(block_A, block_B))

        Q = nx.quotient_graph(G, same_source_line, edge_relation=block_to_block)

        # Refactor this - raises ``KeyError`` because ``instr_map`` is keyed by
        # offset pairs, not individual offsets
        block_relabelling = {
            B: instr_map[(get_source_line(min(B)), min(B))].starts_line
            for B in Q.nodes
        }
        nx.relabel_nodes(Q, block_relabelling, copy=False)
        for n, di in Q.nodes.items():
            Q.nodes[n].update({'src_line': src_map.get(n)})

        return Q

    def __init__(
        self,
        graph_data: Optional[Union[list, dict, nx.Graph, np.ndarray, np.matrix, sp.sparse.spmatrix, pvz.AGraph]] = None,
        code: Optional[Union[str, CodeType, Callable]] = None,
        **graph_attrs: Any
    ) -> None:
        """
        A CPython "bytecode"-aware directed graph representing the CPython
        bytecode instruction stack of a Python method, generator, asynchronous
        generator, coroutine, class, string of source code, or code
        object (as returned by compile()).
        """
        self._code = None
        self._xbytecode = None
        self._source_code_graph = None
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

        self.add_edges_from(self.get_edges(instr_map=self.xbytecode.instr_map))

        it1, it2, it3, it4 = tee(self.xbytecode.instr_map.values(), 4)
        self._number_entry_points = sum(1 for instr in it1 if instr.is_entry_point)
        self._number_decision_points = sum(1 for instr in it2 if instr.is_decision_point)
        self._number_branch_points = sum(1 for instr in it3 if instr.is_branch_point)
        self._number_exit_points = sum(1 for instr in it4 if instr.is_exit_point)

        self._source_code_graph = self.__class__.get_source_code_graph(code=self.code)

    @property
    def code(self):
        return self._code

    @property
    def xbytecode(self):
        return self._xbytecode

    @property
    def source_code_graph(self):
        return self._source_code_graph

    @property
    def number_entry_points(self):
        return self._number_entry_points

    @property
    def number_decision_points(self):
        return self._number_decision_points

    @property
    def number_branch_points(self):
        return self._number_branch_points

    @property
    def number_exit_points(self):
        return self._number_exit_points

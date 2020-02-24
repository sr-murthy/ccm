__all__ = [
    'XBytecodeGraph'
]


from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Coroutine,
    Generator,
    Optional,
    TypeVar,
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

from .xdis import XBytecode


class XBytecodeGraph(DiGraph):


    @classmethod
    def get_graph(cls, code):
        xbytecode = XBytecode(code)

        instr_map = xbytecode.instr_map
        instr_pairs = (
            (a, b) for a, b, in product(instr_map.values(), instr_map.values())
            if b.offset > a.offset
        )
        for instr_a, instr_b in instr_pairs:
            if instr_b.offset - 2 == instr_a.offset and not instr_a.is_exit_point: 
                self.add_edge(instr_a.offset, instr_b.offset) 
            if instr_b.is_jump_target and instr_a.arg == instr_b.offset: 
                self.add_edge(instr_a.offset, instr_b.offset)
            if instr_a.is_exit_point:
                self.add_edge(instr_a.offset, 0)
            if instr_b.is_exit_point:
                self.add_edge(instr_b.offset, 0)

    def __init__(
        self,
        incoming_graph_data: Optional[Union[list, dict, nx.Graph, np.ndarray, np.matrix, sp.sparse.spmatrix, pvz.AGraph]] = None,
        code: Optional[Union[str, Callable, Generator, Coroutine, AsyncGenerator, TypeVar]] = None,
        **attr: Any
    ) -> None:
        """
        A CPython "bytecode"-aware directed graph representing the CPython
        bytecode instruction stack of a Python method, generator, asynchronous
        generator, coroutine, class, string of source code, or code
        object (as returned by compile()).
        """
        if incoming_graph_data:
            super(self.__class__, self).__init__(incoming_graph_data, **attr)
            return

        super(self.__class__, self).__init__()

        self._code = code
        if self._code:
            self._xbytecode = XBytecode(self._code)
            self._number_decision_points = self._number_branch_points = self._number_exit_points = 0

            instr_map = self._xbytecode.instr_map
            instr_pairs = (
                (a, b) for a, b, in product(instr_map.values(), instr_map.values())
                if b.offset > a.offset
            )
            for instr_a, instr_b in instr_pairs:
                if instr_b.offset - 2 == instr_a.offset and not instr_a.is_exit_point: 
                    self.add_edge(instr_a.offset, instr_b.offset) 
                if instr_b.is_jump_target and instr_a.arg == instr_b.offset: 
                    self.add_edge(instr_a.offset, instr_b.offset)
                if instr_a.is_exit_point:
                    self.add_edge(instr_a.offset, 0)
                if instr_b.is_exit_point:
                    self.add_edge(instr_b.offset, 0)

            it_a, it_b, it_c = tee(instr_map.values(), 3)
            self._number_decision_points = sum(1 for instr in it_a if instr.is_decision_point)
            self._number_branch_points = sum(1 for instr in it_b if instr.is_branch_point)
            self._number_exit_points = sum(1 for instr in it_c if instr.is_exit_point)

    @property
    def code(self):
        return self._code

    @property
    def xbytecode(self):
        return self._xbytecode

    @property
    def number_decision_points(self):
        return self._number_decision_points

    @property
    def number_branch_points(self):
        return self._number_branch_points

    @property
    def number_exit_points(self):
        return self._number_exit_points

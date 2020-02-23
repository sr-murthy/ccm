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
from itertools import product

import networkx as nx
import numpy as np
import pygraphviz as pvz
import scipy as sp

from networkx import DiGraph

from .xdis import XBytecode


class XBytecodeGraph(DiGraph):

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

            instr_map = self._xbytecode.instr_map

            for instr_a, instr_b in product(instr_map.values(), instr_map.values()): 
                if instr_b.offset - 2 == instr_a.offset and not instr_a.is_exit_point: 
                    self.add_edge(instr_a.offset, instr_b.offset) 
                if instr_b.is_jump_target and instr_a.arg == instr_b.offset: 
                    self.add_edge(instr_a.offset, instr_b.offset)
                if instr_a.is_exit_point:
                    self.add_edge(instr_a.offset, 0)

    @property
    def code(self):
        return self.code

    @property
    def xbytecode(self):
        return self._xbytecode

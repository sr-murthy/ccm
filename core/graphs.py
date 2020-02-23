__all__ = [
    'XBytecodeGraph'
]


from typing import (
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

from networkx import DiGraph

from .xdis import XBytecode


class XBytecodeGraph(DiGraph):

    def __init__(
        self,
        x: Optional[Union[str, Callable, Generator, Coroutine, AsyncGenerator, TypeVar]] = None
    ) -> None:
        """
        A CPython "bytecode"-aware directed graph representing the CPython
        bytecode instruction stack of a Python method, generator, asynchronous
        generator, coroutine, class, string of source code, or code
        object (as returned by compile()).
        """
        super(self.__class__, self).__init__()

        self._x = x
        if self._x is not None:
            self._xbytecode = XBytecode(x)

            instr_map = self._xbytecode.instr_map

            for instr_a, instr_b in product(instr_map.values(), instr_map.values()): 
                if instr_b.offset - 2 == instr_a.offset and not instr_a.is_exit_point: 
                    self.add_edge(instr_a.offset, instr_b.offset) 
                if instr_b.is_jump_target and instr_a.arg == instr_b.offset: 
                    self.add_edge(instr_a.offset, instr_b.offset)
                if instr_a.is_exit_point:
                    self.add_edge(instr_a.offset, 0)

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, _x):
        self._x = _x
        if self._x is not None:
            self._xbytecode = XBytecode(x)

    @property
    def xbytecode(self):
        return self._xbytecode

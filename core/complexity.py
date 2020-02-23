__all__ = [
    'BytecodeGraph',
    'mccabe_complexity',
    'henderson_sellers_complexity',
    'feghali_watson_complexity'
]

import dis
import typing

from dis import (
    Bytecode,
)
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Coroutine,
    Generator,
    Tuple,
    TypeVar,
    Union,
)

from collections import OrderedDict
from itertools import product

import networkx as nx

from networkx import DiGraph


class BytecodeGraph(DiGraph):

    def __init__(
        self,
        x: Union[str, Callable, Generator, Coroutine, AsyncGenerator, TypeVar]
    ) -> None:
        """
        A CPython "bytecode"-aware directed graph representing the CPython
        bytecode instruction stack of a Python method, generator, asynchronous
        generator, coroutine, class, string of source code, or code
        object (as returned by compile()).
        """
        super(self.__class__, self).__init__()

        self._bytecode = Bytecode(x)
        self._instr_map = OrderedDict((instr.offset, instr) for instr in self._bytecode)

        for offset_a, offset_b in product(self._instr_map, self._instr_map): 
            instr_a, instr_b = self._instr_map[offset_a], self._instr_map[offset_b] 
            if offset_b - 2 == offset_a and instr_a.opname != 'RETURN_VALUE': 
                self.add_edge(offset_a, offset_b) 
            if instr_b.is_jump_target and instr_a.arg == offset_b: 
                self.add_edge(offset_a, offset_b)
            if instr_a.opname == 'RETURN_VALUE':
                self.add_edge(offset_a, 0)

    @property
    def bytecode(self):
        return self._bytecode
    
    @property
    def instr_map(self):
        return self._instr_map


def mccabe_complexity(x: Union[str, Callable, Generator, Coroutine, AsyncGenerator, TypeVar]) -> int:
    """
    Returns the McCabe cyclomatic complexity ``V`` of a Python method,
    generator, asynchronous generator, coroutine, class, string of source code,
    or code object (as returned by compile()), given by the formula

        V(G) = e - n + 1

    where ``G`` is the strongly connected graph (with one connected component)
    of the bytecode instruction stack of the input, ``n`` is the nunber of
    nodes of ``G``, and ``e`` is  the number of edges of ``G``.
    """

    G = BytecodeGraph(x)

    p = nx.number_strongly_connected_components(G)
    if p > 1:
        raise TypeError('The bytecode graph of the input is not connected')

    return self.number_of_edges() - self.number_of_nodes() + 1


def henderson_sellers_complexity(x: Union[str, Callable, Generator, Coroutine, AsyncGenerator, TypeVar]) -> int:
    """
    Returns the Henderson-Sellers cyclomatic complexity ``V`` of a Python
    method, generator, asynchronous generator, coroutine, class, string of
    source code, or code object (as returned by compile()), given by the
    formula

        V(G) = e - n + p + 1

    where ``G`` is the directed graph (with one or more strongly connected
    components) of the bytecode instruction stack of the input, ``n`` is the
    nunber of nodes of ``G``, ``e`` is  the number of edges of ``G``, and ``p``
    is the number of strongly connected components of ``G``.
    """
    G = BytecodeGraph(x)

    n, e = G.number_of_nodes(), G.number_of_edges()
    p = nx.number_strongly_connected_components(G)
    
    return e - n + p + 1


def feghali_watson_complexity(x: Union[str, Callable, Generator, Coroutine, AsyncGenerator, TypeVar]) -> int:
    """
    Returns the Feghali & Watson cyclomatic complexity ``V`` of a Python
    method, generator, asynchronous generator, coroutine, class, string of
    source code, or code object (as returned by compile()), given by the
    formula

        V(G) = e - n + 2 * p

    where ``G`` is the directed graph (with one or more strongly connected
    components) of the bytecode instruction stack of the input, ``n`` is the
    nunber of nodes of ``G``, ``e`` is  the number of edges of ``G``, and ``p``
    is the number of strongly connected components of ``G``.
    """
    G = BytecodeGraph(x)

    n, e = G.number_of_nodes(), G.number_of_edges()
    p = nx.number_strongly_connected_components(G)
    
    return e - n + 2 * p

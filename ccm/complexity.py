"""
Cyclomatic complexity (CC) measures of Python source code or code objects, including

::

    1. McCabe complexity (CC(G) = #{edges} - #{nodes} + 1)
    2. Generalised McCabe complexity (CC(G) = #{edges} - #{nodes} + 2 * #{connected components})
    3. Henderson-Sellers complexity (CC(G) = #{edges} - #{nodes} + #{connected components} + 1)
    4. Henderson-Sellers & Tegarden complexity (CC(G) = #{edges} - #{nodes} + #{connected components})
    5. Generalised Henderson-Sellers & Tegarden complexity (CC(G) = #{edges} - #{nodes} + #{exit points per component} + 2)
    6. Harrison complexity (CC(G) = #{decision points} - #{exit points} + 2)
"""

__all__ = [
    'harrison_complexity',
    'henderson_sellers_complexity',
    'henderson_sellers_tegarden_complexity',
    'henderson_sellers_tegarden_generalised_complexity',
    'mccabe_complexity',
    'mccabe_generalised_complexity',
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

import networkx as nx

from .graphs import XBytecodeGraph


def mccabe_complexity(code: Union[str, Callable, Generator, Coroutine, AsyncGenerator, TypeVar]) -> int:
    """
    Returns the McCabe cyclomatic complexity of a Python method,
    generator, asynchronous generator, coroutine, class, string of source code,
    or code object (as returned by compile()), given by the formula

        CC(G) = e - n + 2

    where ``G`` is the strongly connected graph (with one connected component)
    of the bytecode instruction stack of the input, ``n`` is the nunber of
    nodes of ``G``, and ``e`` is  the number of edges of ``G``.

    Reference: 'A Critical Re-examination of Cyclomatic Complexity Measures',
    B. Henderson-Sellers & D. Tegarden, Software Quality and Productivity,
    M. Lee et. al. (eds.), Springer, Dordrecht, 1995, pp.328-335.
    """

    G = XBytecodeGraph(code=code)

    p = nx.number_strongly_connected_components(G)
    if p > 1:
        raise TypeError('The bytecode graph of the input is not connected')

    return G.number_of_edges() - G.number_of_nodes() + 2


def mccabe_generalised_complexity(code: Union[str, Callable, Generator, Coroutine, AsyncGenerator, TypeVar]) -> int:
    """
    Returns the generalised McCabe cyclomatic complexity of a Python
    method, generator, asynchronous generator, coroutine, class, string of
    source code, or code object (as returned by compile()), given by the
    formula

    ::

        CC(G) = e - n + 2 * p

    where ``G`` is the directed graph (with one or more strongly connected
    components) of the bytecode instruction stack of the input, ``n`` is the
    nunber of nodes of ``G``, ``e`` is  the number of edges of ``G``, and ``p``
    is the number of strongly connected components of ``G``.

    Reference: 'A Critical Re-examination of Cyclomatic Complexity Measures',
    B. Henderson-Sellers & D. Tegarden, Software Quality and Productivity,
    M. Lee et. al. (eds.), Springer, Dordrecht, 1995, pp.328-335.
    """
    G = XBytecodeGraph(code=code)

    n, e = G.number_of_nodes(), G.number_of_edges()
    p = nx.number_strongly_connected_components(G)

    return e - n + 2 * p


def henderson_sellers_complexity(code: Union[str, Callable, Generator, Coroutine, AsyncGenerator, TypeVar]) -> int:
    """
    Returns the Henderson-Sellers cyclomatic complexity of a Python
    method, generator, asynchronous generator, coroutine, class, string of
    source code, or code object (as returned by compile()), given by the
    formula

    ::

        CC(G) = e - n + p + 1

    where ``G`` is the directed graph (with one or more strongly connected
    components) of the bytecode instruction stack of the input, ``n`` is the
    nunber of nodes of ``G``, ``e`` is  the number of edges of ``G``, and ``p``
    is the number of strongly connected components of ``G``.

    Reference: 'A Critical Re-examination of Cyclomatic Complexity Measures',
    B. Henderson-Sellers & D. Tegarden, Software Quality and Productivity,
    M. Lee et. al. (eds.), Springer, Dordrecht, 1995, pp.328-335.
    """
    G = XBytecodeGraph(code=code)

    n, e = G.number_of_nodes(), G.number_of_edges()
    p = nx.number_strongly_connected_components(G)
    
    return e - n + p + 1


def henderson_sellers_tegarden_complexity(code: Union[str, Callable, Generator, Coroutine, AsyncGenerator, TypeVar]) -> int:
    """
    Returns the Henderson-Sellers cyclomatic complexity of a Python
    method, generator, asynchronous generator, coroutine, class, string of
    source code, or code object (as returned by compile()), given by the
    formula

    ::

        CC(G) = e - n + p

    where ``G`` is the directed graph (with one or more strongly connected
    components) of the bytecode instruction stack of the input, ``n`` is the
    nunber of nodes of ``G``, ``e`` is  the number of edges of ``G``, and ``p``
    is the number of strongly connected components of ``G``.

    Reference: 'A Critical Re-examination of Cyclomatic Complexity Measures',
    B. Henderson-Sellers & D. Tegarden, Software Quality and Productivity,
    M. Lee et. al. (eds.), Springer, Dordrecht, 1995, pp.328-335.
    """
    G = XBytecodeGraph(code=code)

    n, e = G.number_of_nodes(), G.number_of_edges()
    p = nx.number_strongly_connected_components(G)

    return e - n + p


def henderson_sellers_tegarden_generalised_complexity(code: Union[str, Callable, Generator, Coroutine, AsyncGenerator, TypeVar]) -> int:
    """
    Returns the generalised Henderson-Sellers & Tegarden cyclomatic complexity
    of a Python method, generator, asynchronous generator, coroutine,
    class, string of source code, or code object (as returned by compile()),
    given by the formula

    ::

        CC(G) = e - n + X + 2

    where ``G`` is the directed graph (with one or more strongly connected
    components) of the bytecode instruction stack of the input, ``d`` is the
    number of decision points of ``G``, and ``X`` is  the total of number of
    exit points over all (strongly) connected components of ``G``.

    Reference: 'A Critical Re-examination of Cyclomatic Complexity Measures',
    B. Henderson-Sellers & D. Tegarden, Software Quality and Productivity,
    M. Lee et. al. (eds.), Springer, Dordrecht, 1995, pp.328-335.
    """
    G = XBytecodeGraph(code=code)

    n, e = G.number_of_nodes(), G.number_of_edges()
    X = sum(
        G.get_subgraph(G, comp).number_exit_points
        for comp in nx.strongly_connected_components(G)
    )

    return e - n + X + 2


def harrison_complexity(code: Union[str, Callable, Generator, Coroutine, AsyncGenerator, TypeVar]) -> int:
    """
    Returns the Harrison cyclomatic complexity of a Python
    method, generator, asynchronous generator, coroutine, class, string of
    source code, or code object (as returned by compile()), given by the
    formula

    ::

        CC(G) = d - x + 2

    where ``G`` is the directed graph (with one or more strongly connected
    components) of the bytecode instruction stack of the input, ``d`` is the
    number of decision points of ``G``, and ``x`` is  the number of exit points
    of ``G``.

    Reference: 'Applying Mccabe's complexity measure to multiple‐exit programs',
    W. A. Harrison, Journal of Software: Practice and Experience, 14:10, 10/1984.
    """
    G = XBytecodeGraph(code=code)

    d, x = G.number_decision_points, G.number_exit_points

    return d - x + 2

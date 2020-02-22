__all__ = [
    'get_bytecode_graph'
]


import dis
import typing

from dis import (
    dis as _dis,
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

import matplotlib as mp
import matplotlib.pyplot as plt
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout

from networkx import DiGraph


def get_bytecode_graph(
    x: Union[str, Callable, Generator, Coroutine, AsyncGenerator, TypeVar],
    **draw_options: Any
) -> Union[nx.DiGraph, Tuple[nx.DiGraph, mp.figure.Figure]]:
    """
    Analyse the bytecode corresponding to a function, generator, asynchronous
    generator, coroutine, method, or a string of source code compilable by
    the built-in ``compile``.
    """
    code_obj = Bytecode(x)

    instr_map = OrderedDict((instr.offset, instr) for instr in code_obj)

    G, fig = DiGraph(), None

    for offset_a, offset_b in product(instr_map, instr_map): 
        instr_a, instr_b = instr_map[offset_a], instr_map[offset_b] 
        if offset_b - 2 == offset_a and instr_a.opname != 'RETURN_VALUE': 
            G.add_edge(offset_a, offset_b) 
        if instr_b.is_jump_target and instr_a.arg == offset_b: 
            G.add_edge(offset_a, offset_b)

    if not draw_options:
        return G

    labels = OrderedDict(
        (offset, f'#{instr.starts_line or ""}: {instr.opname} ({instr.argrepr})')
        for offset, instr in instr_map.items()
    )

    draw_options = {
        **{
            'layout': 'spectral_layout',
            'node_shape': 's',
            'node_color': 'skyblue',
            'node_size': 1000,
            'font_size': 6,
            'labels': labels,
            'edge_color': 'black',
            'arrows': True
        },
        **draw_options
    }

    pos = (
        graphviz_layout(G, prog='dot') if draw_options['layout'] == 'graphviz'
        else getattr(nx, draw_options['layout'])(G)
    )

    nx.draw_networkx_nodes(G, pos, **draw_options)
    nx.draw_networkx_labels(G, pos, **draw_options)
    nx.draw_networkx_edges(G, pos, **draw_options)

    plt.draw()
    fig = plt.gcf()

    return G, fig

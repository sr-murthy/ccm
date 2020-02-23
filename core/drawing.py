__all__ = [
    'draw_graph'
]


from collections import OrderedDict
from typing import Any

import matplotlib as mp
import matplotlib.pyplot as plt
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout

from .complexity import BytecodeGraph


def draw_graph(
    G: BytecodeGraph,
    **draw_options: Any
) -> mp.figure.Figure:
    """
    Draws the figure of the given bytecode graph (``code_complexity.core.complexity.BytecodeGraph``)
    using ``matplotlib.pyplot``, and also returns the figure.
    """
    labels = OrderedDict(
        (offset, f'#{instr.starts_line or ""}: {instr.opname} ({instr.argrepr})')
        for offset, instr in G.instr_map.items()
    )

    draw_options = {
        **{
            'layout': 'graphviz',
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

    return fig

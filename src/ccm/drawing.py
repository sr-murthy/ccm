__all__ = [
    'draw_graph'
]


from collections import OrderedDict
from typing import (
    Any,
    Union,
)

import matplotlib as mp
import matplotlib.pyplot as plt
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout

from .graphs import XBytecodeGraph


def draw_graph(
    G: nx.DiGraph,
    **draw_options: Any
) -> mp.figure.Figure:
    """
    Draws the figure of a given ``networkx.DiGraph`` using
    ``matplotlib.pyplot``, and also returns the figure.
    """
    labels = (
        draw_options.get('labels') or
        OrderedDict(
            (offset, f'({instr.offset}, {instr.starts_line}): {instr.opname} ({instr.argrepr})')
            for offset, instr in G.xbytecode.instr_map.items()
        ) if isinstance(G, XBytecodeGraph) and G.xbytecode else OrderedDict((n, str(n)) for n in G.nodes)
    )

    draw_options = {
        **{
            'layout': 'graphviz',
            'node_shape': 's',
            'node_color': 'skyblue',
            'node_size': 50,
            'font_size': 6,
            'labels': labels,
            'edge_color': 'black',
            'arrows': True,
            'connectionstyle': 'arc3, rad = 0.05'
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
    plt.show()

    fig = plt.gcf()

    return fig

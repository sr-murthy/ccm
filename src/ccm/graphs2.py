__all__ = [
    'BytecodeGraph',
    'CodeGraph',
    'SourceCodeGraph',
]


import json
import os

from abc import ABCMeta
from json import JSONDecodeError

from .exceptions import CCMError
from .utils import create_property


class CodeGraph(metaclass=ABCMeta):
    """
    Abstract base class defining basic properties and functionality of a code
    digraph, which is intended to serve as a template for bytecode digraphs
    and source code digraphs.
    """


class SourceCodeGraph(CodeGraph):
    """
    Source code graph
    """


class BytecodeGraph(CodeGraph):
    """
    Bytecode graph
    """

__all__ = [
    'BaseSource',
    'ClassSource',
    'get_bytecode_instructions_by_source_line',
    'get_source_lines',
    'SourceLine',
    'Source'
]


import inspect
import io
import itertools
import json
import operator
import os

from abc import (
    ABCMeta,
    abstractmethod,
)

from collections import (
    defaultdict,
    namedtuple,
    OrderedDict,
)
from typing import (
    AsyncGenerator,
    Callable,
    Coroutine,
    Generator,
    Optional,
    OrderedDict as OrderedDictType,
    Tuple,
    Type,
    Union,
)

from .exceptions import CCMError
from .utils import create_property
from .xdis import (
    XBytecode,
    XInstruction,
)


_SourceLine = namedtuple(
    "_SourceLine",
    (
        "lineno text bytecode is_entry_point is_decision_point "
        "is_branch_point is_jump_target is_exit_point"
    )
)

_SourceLine.lineno.__doc__ = "Line number in the source code object/block"
_SourceLine.text.__doc__ = "Exact text of the line (including the newline char.)"
_SourceLine.bytecode.__doc__ = "The bytecode for the line, as an ordered dict. of (offset, XInstruction) pairs"
_SourceLine.is_entry_point.__doc__ = "True if the bytecode for this line contains an entry point, otherwise False"
_SourceLine.is_decision_point.__doc__ = "True if the bytecode for this line contains a decision point, otherwise False"
_SourceLine.is_branch_point.__doc__ = "True if the bytecode for this line contains a branch point, otherwise False"
_SourceLine.is_jump_target.__doc__ = "True if the bytecode code for this line contains a jump target, otherwise False"
_SourceLine.is_exit_point.__doc__ = "True if the bytecode for this line contains an exit point, otherwise False"


class SourceLine(_SourceLine):
    """
    Represents a single (physical) source line of code in a method or
    callable, generator or async. generator, coroutine, or string of
    source code compilable via ``compile``. Fields are inherited from
    ``_SourceLine`` above.
    """
    pass


def get_bytecode_instructions_by_source_line(
    bytecode: XBytecode
) -> OrderedDictType[int, OrderedDictType[int, XInstruction]]:
    """
    Returns an ordered dict. of source line numbers (keys) and the
    corresponding bytecode, where the bytecode is represented as an
    ordered dict of offsets and ``XInstruction`` objects.
    """
    return defaultdict(
        OrderedDict,
        OrderedDict(
            (lineno, OrderedDict((offset, instr) for offset, instr in instrs))
            for lineno, instrs in itertools.groupby(
                bytecode.instr_map.items(), key=lambda t: t[1].starts_line
            )
        )
    )


def get_source_lines(
    bytecode: XBytecode,
    code: Optional[Union[str, Callable, Generator, AsyncGenerator, Coroutine, Type]] = None,
    source: Optional[str] = None
) -> Generator[Tuple[int, SourceLine], None, None]:
    """
    Generates source line numbers and corresponding ``SourceLine`` objects
    in order of source line number.
    """
    instrs_by_line = get_bytecode_instructions_by_source_line(bytecode)

    _source = source or inspect.getsource(code)

    for i, l in enumerate((_l for _l in source.split('\n') if _l), start=1):
        l += '\n'
        no = i
        text = l
        bytecode = instrs_by_line[i]
        ep, dp, bp, jt, xp = operator.attrgetter(
            'is_entry_point', 'is_decision_point', 'is_branch_point',
            'is_jump_target', 'is_exit_point'
        )(instrs_by_line[2][0])

        yield i, SourceLine(
            lineno=i, text=l, bytecode=instrs_by_line[i],
            is_entry_point=ep, is_decision_point=dp,
            is_branch_point=bp, is_jump_target=jt,
            is_exit_point=xp
        )


class BaseSource(metaclass=ABCMeta):
    """
    Abstract base class for source code objects, including methods, callables,
    classes, generators and async. generators, coroutines, and string of
    compilable source code.
    """

    @abstractmethod
    def __init__(
        self,
        code: Union[str, Callable, Generator, AsyncGenerator, Coroutine, Type],
        bytecode: Optional[XBytecode] = None,
        first_line: Optional[int] = 1,
        bytecode_offset: Optional[int] = None
    ) -> None:
        """
        Source initialisation - implementations must use this to set the source
        class properties as defined in ``ccm/static/source.json``, with the
        values set ac
        """
        pass


class Source(BaseSource):

    def __init__(
        self,
        code: Union[str, Callable, Generator, AsyncGenerator, Coroutine, Type],
        bytecode: Optional[XBytecode] = None,
        first_line: Optional[int] = 1,
        bytecode_offset: Optional[int] = None
    ) -> None:
        """
        Source initialisation.
        """
        self._code = code
        setattr(
            self.__class__,
            'code',
            create_property('code', attr_prefix='_', writable=True)
        )

        self._source = inspect.getsource(self.code)
        setattr(
            self.__class__,
            'source',
            create_property('source', attr_prefix='_', writable=True)
        )

        self._bytecode = bytecode or XBytecode(self.code, first_line=first_line, current_offset=bytecode_offset)
        setattr(
            self.__class__,
            'bytecode',
            create_property('bytecode', attr_prefix='_', writable=True)
        )

        self._source_map = defaultdict(
            None,
            OrderedDict((i, source_line) for i, source_line in get_source_lines(self.bytecode, source=self.source))
        )
        setattr(
            self.__class__,
            'source_map',
            create_property('source_map', attr_prefix='_', writable=True)
        )

    def __repr__(self) -> str:
        strep = namedtuple(self.__class__.__name__, "code source")
        return str(strep(code=self.code, source=self.source[:50] + '...'))


class ClassSource(BaseSource):
    pass

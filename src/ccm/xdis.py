"""
    Extension of the ``dis`` module in the Python standard library.
    Disassembler of Python byte code into mnemonics - uses a custom extension
    ``XInstruction`` of the ``dis.Instruction`` class to add properties of
    whether an instruction represents a decision point, a branching point or
    an exit point, and a custom extension ``XBytecode`` of the ``dis.Bytecode``
    class to process ``XInstruction`` instances. Instances of ``XBytecode``
    have an additional map/dict of the ``XInstruction`` objects with the
    keys being offsets.
"""

import sys
import types
import collections
import io
import types

from opcode import *
from opcode import __all__ as _opcodes_all

from .exceptions import CCMError
from .utils import pairwise


__all__ = [
    "BRANCH_OPS",
    "CALL_OPS",
    "code_info",
    "DECISION_OPS",
    "dis",
    "disassemble",
    "distb",
    "disco",
    "EXIT_OPS",
    "findlinestarts",
    "findlabels",
    "get_instructions",
    "show_code",
    "XBytecode",
    "XInstruction"
] + _opcodes_all

del _opcodes_all

_have_code = (types.MethodType, types.FunctionType, types.CodeType,
              classmethod, staticmethod, type)

FORMAT_VALUE = opmap['FORMAT_VALUE']
FORMAT_VALUE_CONVERTERS = (
    (None, ''),
    (str, 'str'),
    (repr, 'repr'),
    (ascii, 'ascii'),
)
MAKE_FUNCTION = opmap['MAKE_FUNCTION']
MAKE_FUNCTION_FLAGS = ('defaults', 'kwdefaults', 'annotations', 'closure')

CALL_OPS = {i: _opname for i, _opname in zip(range(len(opname)), opname) if _opname.startswith('CALL')}
DECISION_OPS = {i: _opname for i, _opname in zip(range(len(opname)), opname) if opmap.get(_opname, None) in hascompare}
BRANCH_OPS = {i: _opname for i, _opname in zip(range(len(opname)), opname) if opmap.get(_opname, None) in hasjabs + hasjrel}
EXIT_OPS = {i: _opname for i, _opname in zip(range(len(opname)), opname) if _opname in ['RETURN_VALUE', 'RAISE_VARARGS']}


def _try_compile(source, name):
    """Attempts to compile the given source, first as an expression and
       then as a statement if the first approach fails.

       Utility function to accept strings in functions that otherwise
       expect code objects
    """
    try:
        c = compile(source, name, 'eval')
    except SyntaxError:
        c = compile(source, name, 'exec')
    return c


def dis(x=None, *, file=None, depth=None):
    """Disassemble classes, methods, functions, and other compiled objects.

    With no argument, disassemble the last traceback.

    Compiled objects currently include generator objects, async generator
    objects, and coroutine objects, all of which store their code object
    in a special attribute.
    """
    if x is None:
        distb(file=file)
        return
    # Extract functions from methods.
    if hasattr(x, '__func__'):
        x = x.__func__
    # Extract compiled code objects from...
    if hasattr(x, '__code__'):  # ...a function, or
        x = x.__code__
    elif hasattr(x, 'gi_code'):  #...a generator object, or
        x = x.gi_code
    elif hasattr(x, 'ag_code'):  #...an asynchronous generator object, or
        x = x.ag_code
    elif hasattr(x, 'cr_code'):  #...a coroutine.
        x = x.cr_code
    # Perform the disassembly.
    if hasattr(x, '__dict__'):  # Class or module
        items = sorted(x.__dict__.items())
        for name, x1 in items:
            if isinstance(x1, _have_code):
                print("Disassembly of %s:" % name, file=file)
                try:
                    dis(x1, file=file, depth=depth)
                except TypeError as msg:
                    print("Sorry:", msg, file=file)
                print(file=file)
    elif hasattr(x, 'co_code'): # Code object
        _disassemble_recursive(x, file=file, depth=depth)
    elif isinstance(x, (bytes, bytearray)): # Raw bytecode
        _disassemble_bytes(x, file=file)
    elif isinstance(x, str):    # Source code
        _disassemble_str(x, file=file, depth=depth)
    else:
        raise TypeError("don't know how to disassemble %s objects" %
                        type(x).__name__)


def distb(tb=None, *, file=None):
    """Disassemble a traceback (default: last traceback)."""
    if tb is None:
        try:
            tb = sys.last_traceback
        except AttributeError:
            raise RuntimeError("no last traceback to disassemble") from None
        while tb.tb_next: tb = tb.tb_next
    disassemble(tb.tb_frame.f_code, tb.tb_lasti, file=file)

# The inspect module interrogates this dictionary to build its
# list of CO_* constants. It is also used by pretty_flags to
# turn the co_flags field into a human readable list.
COMPILER_FLAG_NAMES = {
     1: "OPTIMIZED",
     2: "NEWLOCALS",
     4: "VARARGS",
     8: "VARKEYWORDS",
    16: "NESTED",
    32: "GENERATOR",
    64: "NOFREE",
   128: "COROUTINE",
   256: "ITERABLE_COROUTINE",
   512: "ASYNC_GENERATOR",
}


def pretty_flags(flags):
    """Return pretty representation of code flags."""
    names = []
    for i in range(32):
        flag = 1<<i
        if flags & flag:
            names.append(COMPILER_FLAG_NAMES.get(flag, hex(flag)))
            flags ^= flag
            if not flags:
                break
    else:
        names.append(hex(flags))
    return ", ".join(names)


def _get_code_object(x):
    """Helper to handle methods, compiled or raw code objects, and strings."""
    # Extract functions from methods.
    if hasattr(x, '__func__'):
        x = x.__func__
    # Extract compiled code objects from...
    if hasattr(x, '__code__'):  # ...a function, or
        x = x.__code__
    elif hasattr(x, 'gi_code'):  #...a generator object, or
        x = x.gi_code
    elif hasattr(x, 'ag_code'):  #...an asynchronous generator object, or
        x = x.ag_code
    elif hasattr(x, 'cr_code'):  #...a coroutine.
        x = x.cr_code
    # Handle source code.
    if isinstance(x, str):
        x = _try_compile(x, "<disassembly>")
    # By now, if we don't have a code object, we can't disassemble x.
    if hasattr(x, 'co_code'):
        return x
    raise TypeError("don't know how to disassemble %s objects" %
                    type(x).__name__)


def code_info(x):
    """Formatted details of methods, functions, or code."""
    return _format_code_info(_get_code_object(x))


def _format_code_info(co):
    lines = []
    lines.append("Name:              %s" % co.co_name)
    lines.append("Filename:          %s" % co.co_filename)
    lines.append("Argument count:    %s" % co.co_argcount)
    try:
        lines.append("Positional-only arguments: %s" % co.co_posonlyargcount)
    except AttributeError:
        lines.append("Positional-only arguments: %s" % 0)
    
    try:
        lines.append("Kw-only arguments: %s" % co.co_kwonlyargcount)
    except AttributeError:
        lines.append("Kw-only arguments: %s" % 0)

    lines.append("Number of locals:  %s" % co.co_nlocals)
    lines.append("Stack size:        %s" % co.co_stacksize)
    lines.append("Flags:             %s" % pretty_flags(co.co_flags))
    if co.co_consts:
        lines.append("Constants:")
        for i_c in enumerate(co.co_consts):
            lines.append("%4d: %r" % i_c)
    if co.co_names:
        lines.append("Names:")
        for i_n in enumerate(co.co_names):
            lines.append("%4d: %s" % i_n)
    if co.co_varnames:
        lines.append("Variable names:")
        for i_n in enumerate(co.co_varnames):
            lines.append("%4d: %s" % i_n)
    if co.co_freevars:
        lines.append("Free variables:")
        for i_n in enumerate(co.co_freevars):
            lines.append("%4d: %s" % i_n)
    if co.co_cellvars:
        lines.append("Cell variables:")
        for i_n in enumerate(co.co_cellvars):
            lines.append("%4d: %s" % i_n)
    return "\n".join(lines)


def show_code(co, *, file=None):
    """Print details of methods, functions, or code to *file*.

    If *file* is not provided, the output is printed on stdout.
    """
    print(code_info(co), file=file)


_XInstruction = collections.namedtuple(
    "_XInstruction",
    """
    opname
    opcode
    arg
    argval
    argrepr
    offset
    starts_line
    is_entry_point
    is_jump_target
    is_decision_point
    is_branch_point
    is_exit_point
    """
)


_XInstruction.opname.__doc__ = "Human readable name for operation"
_XInstruction.opcode.__doc__ = "Numeric code for operation"
_XInstruction.arg.__doc__ = "Numeric argument to operation (if any), otherwise None"
_XInstruction.argval.__doc__ = "Resolved arg value (if known), otherwise same as arg"
_XInstruction.argrepr.__doc__ = "Human readable description of operation argument"
_XInstruction.offset.__doc__ = "Start index of operation within bytecode sequence"
_XInstruction.starts_line.__doc__ = "Source code line started by this opcode (if any), otherwise None"
_XInstruction.is_entry_point.__doc__ = "True if this is an entry point for the code, otherwise False"
_XInstruction.is_jump_target.__doc__ = "True if other code jumps to here, otherwise False"
_XInstruction.is_decision_point.__doc__ = "True if this instruction is a comparison, otherwise False"
_XInstruction.is_branch_point.__doc__ = "True if this instruction is a branching point, otherwise False"
_XInstruction.is_exit_point.__doc__ = "True if this instruction is an exit point, otherwise False"

_OPNAME_WIDTH = 20
_OPARG_WIDTH = 5


class XInstruction(_XInstruction):
    """Details for a bytecode operation

       Defined fields:
         opname - human readable name for operation
         opcode - numeric code for operation
         arg - numeric argument to operation (if any), otherwise None
         argval - resolved arg value (if known), otherwise same as arg
         argrepr - human readable description of operation argument
         offset - start index of operation within bytecode sequence
         starts_line - line started by this opcode (if any), otherwise None
         is_entry_point - True if this is an entry point for the code, otherwise False
         is_jump_target - True if other code jumps to here, otherwise False
         is_decision_point - True if this instruction is a branching point, otherwise False
         is_branch_point - True if this instruction is a branching point, otherwise False
         is_exit_point - True if this instruction is an exit point, otherwise False
    """

    @property
    def dis_line(self) -> str:
        return self._disassemble()

    def _disassemble(self, lineno_width=3, mark_as_current=False, offset_width=4, print_start_line=True):
        """Format instruction details for inclusion in disassembly output

        *lineno_width* sets the width of the line number field (0 omits it)
        *mark_as_current* inserts a '-->' marker arrow as part of the line
        *offset_width* sets the width of the instruction offset field
        """
        fields = []
        # Column: Source code line number
        if lineno_width:
            if self.starts_line and print_start_line:
                lineno_fmt = "%%%dd" % lineno_width
                fields.append(lineno_fmt % self.starts_line)
            else:
                fields.append(' ' * lineno_width)
        # Column: Current instruction indicator
        if mark_as_current:
            fields.append('-->')
        else:
            fields.append('   ')
        # Column: Jump target marker
        if self.is_jump_target:
            fields.append('>>')
        else:
            fields.append('  ')
        # Column: XInstruction offset from start of code sequence
        fields.append(repr(self.offset).rjust(offset_width))
        # Column: Opcode name
        fields.append(self.opname.ljust(_OPNAME_WIDTH))
        # Column: Opcode argument
        if self.arg is not None:
            fields.append(repr(self.arg).rjust(_OPARG_WIDTH))
            # Column: Opcode argument details
            if self.argrepr:
                fields.append('(' + self.argrepr + ')')
        return ' '.join(fields).rstrip()


def get_instructions(x, *, first_line=None):
    """Iterator for the opcodes in methods, functions or code

    Generates a series of XInstruction named tuples giving the details of
    each operations in the supplied code.

    If *first_line* is not None, it indicates the line number that should
    be reported for the first source line in the disassembled code.
    Otherwise, the source line information (if any) is taken directly from
    the disassembled code object.
    """
    co = _get_code_object(x)
    cell_names = co.co_cellvars + co.co_freevars
    linestarts = dict(findlinestarts(co))
    if first_line is not None:
        line_offset = first_line - co.co_firstlineno
    else:
        line_offset = 0
    return _get_instructions_bytes(co.co_code, co.co_varnames, co.co_names,
                                   co.co_consts, cell_names, linestarts,
                                   line_offset)


def _get_const_info(const_index, const_list):
    """Helper to get optional details about const references

       Returns the dereferenced constant and its repr if the constant
       list is defined.
       Otherwise returns the constant index and its repr().
    """
    argval = const_index
    if const_list is not None:
        argval = const_list[const_index]
    return argval, repr(argval)


def _get_name_info(name_index, name_list):
    """Helper to get optional details about named references

       Returns the dereferenced name as both value and repr if the name
       list is defined.
       Otherwise returns the name index and its repr().
    """
    argval = name_index
    if name_list is not None:
        argval = name_list[name_index]
        argrepr = argval
    else:
        argrepr = repr(argval)
    return argval, argrepr


def _get_instructions_bytes(code, varnames=None, names=None, constants=None,
                      cells=None, linestarts=None, first_line=None, line_offset=0,
                      is_function=None):
    """Iterate over the instructions in a bytecode string.

    Generates a sequence of XInstruction namedtuples giving the details of each
    opcode.  Additional information about the code's runtime environment
    (e.g. variable names, constants) can be specified using optional
    arguments.

    """
    labels = findlabels(code)
    starts_line = None
    last_four = []
    for (offset, op, arg), succ in pairwise(_unpack_opargs(code)):
        if linestarts is not None:
            starts_line = linestarts.get(offset, starts_line)
            if starts_line is not None:
                starts_line += line_offset
        is_entry_point = (offset == 0)
        is_jump_target = (offset in labels)
        argval = None
        argrepr = ''
        if arg is not None:
            #  Set argval to the dereferenced value of the argument when
            #  available, and argrepr to the string representation of argval.
            #    _disassemble_bytes needs the string repr of the
            #    raw name index for LOAD_GLOBAL, LOAD_CONST, etc.
            argval = arg
            if op in hasconst:
                argval, argrepr = _get_const_info(arg, constants)
            elif op in hasname:
                argval, argrepr = _get_name_info(arg, names)
            elif op in hasjrel:
                argval = offset + 2 + arg
                argrepr = "to " + repr(argval)
            elif op in haslocal:
                argval, argrepr = _get_name_info(arg, varnames)
            elif op in hascompare:
                argval = cmp_op[arg]
                argrepr = argval
            elif op in hasfree:
                argval, argrepr = _get_name_info(arg, cells)
            elif op == FORMAT_VALUE:
                argval, argrepr = FORMAT_VALUE_CONVERTERS[arg & 0x3]
                argval = (argval, bool(arg & 0x4))
                if argval[1]:
                    if argrepr:
                        argrepr += ', '
                    argrepr += 'with format'
            elif op == MAKE_FUNCTION:
                argrepr = ', '.join(s for i, s in enumerate(MAKE_FUNCTION_FLAGS)
                                    if arg & (1<<i))

        is_decision_point = DECISION_OPS.get(op) is not None
        if not is_decision_point:
            try:
                is_decision_point = (BRANCH_OPS.get(succ[1]) is not None and CALL_OPS.get(op) is not None)
            except (IndexError, KeyError, TypeError):
                pass
        is_branch_point = BRANCH_OPS.get(op) is not None
        is_exit_point = EXIT_OPS.get(op) is not None
        if not is_exit_point:
            try:
                is_exit_point = (
                    (opname[op]  == 'POP_TOP') and
                    ((opname[last_four[0][1]] == 'LOAD_GLOBAL' and _get_name_info(last_four[0][2], names)[0] == 'sys') and
                    (opname[last_four[1][1]] == 'LOAD_METHOD' and _get_name_info(last_four[1][2], names)[0] == 'exit')) or
                    ((opname[last_four[1][1]] == 'LOAD_GLOBAL' and _get_name_info(last_four[1][2], names)[0] == 'sys') and
                    (opname[last_four[2][1]] == 'LOAD_METHOD' and _get_name_info(last_four[2][2], names)[0] == 'exit'))
                )
            except IndexError:
                pass

        yield XInstruction(
            opname=opname[op],
            opcode=op,
            arg=arg,
            argval=argval,
            argrepr=argrepr,
            offset=offset,
            starts_line=starts_line,
            is_entry_point=is_entry_point,
            is_jump_target=is_jump_target,
            is_decision_point=is_decision_point,
            is_branch_point=is_branch_point,
            is_exit_point=is_exit_point
        )

        last_four.append((offset, op, arg))
        last_four = last_four[-4:]


def disassemble(co, lasti=-1, *, file=None):
    """Disassemble a code object."""
    cell_names = co.co_cellvars + co.co_freevars
    linestarts = dict(findlinestarts(co))
    _disassemble_bytes(co.co_code, lasti, co.co_varnames, co.co_names,
                       co.co_consts, cell_names, linestarts, file=file)


def _disassemble_recursive(co, *, file=None, depth=None):
    disassemble(co, file=file)
    if depth is None or depth > 0:
        if depth is not None:
            depth = depth - 1
        for x in co.co_consts:
            if hasattr(x, 'co_code'):
                print(file=file)
                print("Disassembly of %r:" % (x,), file=file)
                _disassemble_recursive(x, file=file, depth=depth)


def _disassemble_bytes(code, lasti=-1, varnames=None, names=None,
                       constants=None, cells=None, linestarts=None,
                       *, file=None, line_offset=0, start_line_by_block=True):
    # Omit the line number column entirely if we have no line number info
    show_lineno = linestarts is not None
    if show_lineno:
        maxlineno = max(linestarts.values()) + line_offset
        if maxlineno >= 1000:
            lineno_width = len(str(maxlineno))
        else:
            lineno_width = 3
    else:
        lineno_width = 0
    maxoffset = len(code) - 2
    if maxoffset >= 10000:
        offset_width = len(str(maxoffset))
    else:
        offset_width = 4
    last_line = None
    for i, instr in enumerate(_get_instructions_bytes(code, varnames, names,
                                         constants, cells, linestarts,
                                         line_offset=line_offset)):
        new_source_line = (show_lineno and
                           last_line != instr.starts_line and
                           instr.offset > 0)
        print_start_line = (i == 0 or new_source_line) if start_line_by_block else True
        if new_source_line:
            print(file=file)
        is_current_instr = instr.offset == lasti
        print(instr._disassemble(lineno_width, is_current_instr, offset_width,
            print_start_line=print_start_line), file=file)
        last_line = instr.starts_line


def _disassemble_str(source, **kwargs):
    """Compile the source string, then disassemble the code object."""
    _disassemble_recursive(_try_compile(source, '<dis>'), **kwargs)

disco = disassemble                     # XXX For backwards compatibility


def _unpack_opargs(code):
    extended_arg = 0
    for i in range(0, len(code), 2):
        op = code[i]
        if op >= HAVE_ARGUMENT:
            arg = code[i+1] | extended_arg
            extended_arg = (arg << 8) if op == EXTENDED_ARG else 0
        else:
            arg = None
        yield (i, op, arg)


def findlabels(code):
    """Detect all offsets in a byte code which are jump targets.

    Return the list of offsets.

    """
    labels = []
    for offset, op, arg in _unpack_opargs(code):
        if arg is not None:
            if op in hasjrel:
                label = offset + 2 + arg
            elif op in hasjabs:
                label = arg
            else:
                continue
            if label not in labels:
                labels.append(label)
    return labels


def findlinestarts(code):
    """Find the offsets in a byte code which are start of lines in the source.

    Generate pairs (offset, lineno) as described in Python/compile.c.

    """
    byte_increments = code.co_lnotab[0::2]
    line_increments = code.co_lnotab[1::2]
    bytecode_len = len(code.co_code)

    lastlineno = None
    lineno = code.co_firstlineno
    addr = 0
    for byte_incr, line_incr in zip(byte_increments, line_increments):
        if byte_incr:
            if lineno != lastlineno:
                yield (addr, lineno)
                lastlineno = lineno
            addr += byte_incr
            if addr >= bytecode_len:
                # The rest of the lnotab byte offsets are past the end of
                # the bytecode, so the lines were optimized away.
                return
        if line_incr >= 0x80:
            # line_increments is an array of 8-bit signed integers
            line_incr -= 0x100
        lineno += line_incr
    if lineno != lastlineno:
        yield (addr, lineno)


class XBytecode(object):
    """The bytecode operations of a piece of code

    Instantiate this with a function, method, other compiled object, string of
    code, or a code object (as returned by compile()).

    Iterating over this yields the bytecode operations as XInstruction instances.
    """
    def __init__(self, x, *, first_line=None, current_offset=None):
        try:
            self.codeobj = co = _get_code_object(x)
        except (TypeError, ValueError):
            raise CCMError(
                'Invalid type for code argument - must be either a method, class '
                'or callable, sychronous or asychronous generator, coroutine, '
                'a string of source code or code object compiled from source '
                'code'
            )
        if first_line is None:
            self.first_line = co.co_firstlineno
            self._line_offset = 0
        else:
            self.first_line = first_line
            self._line_offset = first_line - co.co_firstlineno
        self._cell_names = co.co_cellvars + co.co_freevars
        self._linestarts = dict(findlinestarts(co))
        self._original_object = x
        self.current_offset = current_offset
        self._instr_map = collections.OrderedDict(
            ((instr.starts_line, instr.offset), instr)
            for instr in _get_instructions_bytes(
                co.co_code,
                co.co_varnames,
                co.co_names,
                co.co_consts,
                self._cell_names,
                self._linestarts,
                first_line=self.first_line,
                line_offset=self._line_offset,
                is_function=isinstance(x, types.FunctionType)
            )
        )

    def __iter__(self):
        co = self.codeobj

        return _get_instructions_bytes(
            co.co_code,
            co.co_varnames,
            co.co_names,
            co.co_consts,
            self._cell_names,
            self._linestarts,
            line_offset=self._line_offset
        )

    def __repr__(self):
        return "{}({!r})".format(self.__class__.__name__,
                                 self._original_object)

    @property
    def instr_map(self):
        return self._instr_map

    @classmethod
    def from_traceback(cls, tb):
        """ Construct an XBytecode from the given traceback """
        while tb.tb_next:
            tb = tb.tb_next
        return cls(tb.tb_frame.f_code, current_offset=tb.tb_lasti)

    def info(self):
        """Return formatted information about the code object."""
        return _format_code_info(self.codeobj)

    def dis(self):
        """Return a formatted view of the bytecode operations."""
        co = self.codeobj
        if self.current_offset is not None:
            offset = self.current_offset
        else:
            offset = -1
        with io.StringIO() as output:
            _disassemble_bytes(co.co_code, varnames=co.co_varnames,
                               names=co.co_names, constants=co.co_consts,
                               cells=self._cell_names,
                               linestarts=self._linestarts,
                               line_offset=self._line_offset,
                               file=output,
                               lasti=offset)
            return output.getvalue()


def _test():
    """Simple test program to disassemble a file."""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('infile', type=argparse.FileType(), nargs='?', default='-')
    args = parser.parse_args()
    with args.infile as infile:
        source = infile.read()
    code = compile(source, args.infile.name, "exec")
    dis(code)

if __name__ == "__main__":
    _test()

README
======

This is an **experimental project** for calculating cyclomatic complexity measures (CCM) for Python source code by representing the associated `CPython bytecode instructions <https://docs.python.org/3/library/dis.html#python-bytecode-instructions>`_ as a `connected digraph <https://en.wikipedia.org/wiki/Connectivity_(graph_theory)>`_.

Method
------

The calculation of the measures is made possible using the following method:

* From the given source code object - which could be a source fragment (string), or a `code object <https://docs.python.org/3.7/c-api/code.html>`_, or a function or callable - the (CPython) bytecode object is obtained using a `modifed version <https://github.com/sr-murthy/ccm/blob/master/src/ccm/xdis.py>`_ of the `dis library <https://docs.python.org/3.7/library/dis.html>`_ (an old version from Python 3.7), and the bytecode object is then disassembled into an instruction map of individual CPython bytecode instructions.
* Each instruction is classified as follows: an **entry point** if the instruction is the very first bytecode step of the callable, a **branch point** if the instruction is a branching instruction to another instruction (e.g. :code:`JUMP`), a **decision point** if the instruction involves a comparison (e.g. :code:`COMPARE_OP`), or an **exit point** if the instruction stops or interrupts execution of the callable and returns control flow back to the caller (e.g. :code:`RETURN_VALUE`, :code:`RAISE_VARARGS`).
* Using the `networkx library <https://networkx.org/>`_ the bytecode instruction map is represented as a **directed graph**, called the **bytecode graph**, with nodes representing individual bytecode instructions, edges representing (explicit or implicit) transitions between instructions. Additionally, derived edges are added between all exit points and the (unique) entry point in order to make the graph **connected**.

The (connected, directed) bytecode graph will have all of the structural information about the number of nodes, edges, connected components and the like, in order to calculate the CCMs.

There are six CCMs that can be calculated with this approach:

1. McCabe complexity (CC(G) - :code:`#{edges} - #{nodes} + 2)`
2. Generalised McCabe complexity (CC(G): :code:`#{edges} - #{nodes} + 2 * #{connected components})`
3. Henderson-Sellers complexity (CC(G): :code:`#{edges} - #{nodes} + #{connected components} + 1)`
4. Henderson-Sellers & Tegarden complexity (CC(G): :code:`#{edges} - #{nodes} + #{connected components})`
5. Generalised Henderson-Sellers & Tegarden complexity (CC(G): :code:`#{edges} - #{nodes} + #{exit points per component} + 2)`
6. Harrison complexity (CC(G): :code:`#{decision points} - #{exit points} + 2)`

Example
-------

An example: consider the following simple Python implementation of the `sign function <https://en.wikipedia.org/wiki/Sign_function>`_, for determining whether a given number (integer or float) is negative, zero, or positive:

.. code-block:: python

   def sign(x: int | float) -> typing.Literal[-1, 0, 1]:
       if x < 0:
           return -1
       if x == 0:
           return 0
       return 1

Using :code:`dis.dis` this function can be disassembled into the following (CPython) bytecode:

.. code-block:: python

   2           0 LOAD_FAST                0 (x)
               2 LOAD_CONST               1 (0)
               4 COMPARE_OP               0 (<)
               6 POP_JUMP_IF_FALSE       12

   3           8 LOAD_CONST               2 (-1)
              10 RETURN_VALUE

   4     >>   12 LOAD_FAST                0 (x)
              14 LOAD_CONST               1 (0)
              16 COMPARE_OP               2 (==)
              18 POP_JUMP_IF_FALSE       24

   5          20 LOAD_CONST               1 (0)
              22 RETURN_VALUE

   6     >>   24 LOAD_CONST               3 (1)
              26 RETURN_VALUE

For more information on the details of the bytecode instructions, as displayed to the console, refer to the `dis documentation (3.7) <https://docs.python.org/3.7/library/dis.html>`_, but in essence, each line prints out the following values in order from left to right:

* the first value is an integer representing the (unique) number of the source line of code (sloc) associated with the bytecode instruction (block)
* the second value is an integer, called the `instruction offset <https://docs.python.org/3.7/library/dis.html#dis.Instruction.offset>`_, representing the (unique) index of the bytecode instruction relative to the starting point of the complete sequence of bytecode instructions
* the third value, called the `opname <https://docs.python.org/3.7/library/dis.html#dis.Instruction.opname>`_ is the human readable name of the associated bytecode operation
* the (possibly null) fourth value is the `argument <https://docs.python.org/3.7/library/dis.html#dis.Instruction.arg>`_ to the bytecode operation (if any)
* the (possibly null) fifth value, in parentheses if not null, is a human readable `description <https://docs.python.org/3.7/library/dis.html#dis.Instruction.argrepr>`_ of the operational argument.

**Note**: instructions which are jump targets have offsets prefixed by :code:`>>` (refer `here <https://github.com/python/cpython/blob/3.7/Lib/dis.py#L234>`_).

The bytecode can be represented as the following `directed acyclic graph <https://en.wikipedia.org/wiki/Directed_acyclic_graph>`_:

.. figure:: sign-func-bytecode-dag.png
   :align: left
   :alt: Python sign function as a directed acyclic graph (DAG)

The unique entry point, and the branch points, decision points and exit points are clear from this representation, but are also stored at the level of bytecode instruction as attributes.

The key point here is that in order to compute the cyclomatic complexity measures for a directed graph it must be connected, i.e. there must be a path between any two nodes, in any direction. Thus, it is necessary to add edges to this representation from all the exit points back to the entry point. Once this is done, computing the measures is relatively easy using `networkx <networkx.org>`_.

Here's an iPython session showing how the function can used to calculate the various CCMs.

.. code-block:: python

   In [1]: from ccm.complexity import *

   In [2]: def sign(x):
      ...:     if x < 0:
      ...:         return -1
      ...:     if x == 0:
      ...:         return 0
      ...:     return 1
      ...: 

   In [3]: mccabe_complexity(sign)
   Out[3]: 4

   In [4]: mccabe_generalised_complexity(sign)
   Out[5]: 4

   In [5]: henderson_sellers_complexity(sign)
   Out[5]: 4

   In [6]: henderson_sellers_tegarden_complexity(sign)
   Out[6]: 3

   In [7]: henderson_sellers_tegarden_generalised_complexity(sign)
   Out[7]: 7

   In [8]: harrison_complexity(sign)
   Out[8]: 1

References
----------
1. Henderson-Sellers, B., Tegarden, D. (1995). A Critical Re-examination of Cyclomatic Complexity Measures. In: Lee, M., Barta, BZ., Juliff, P. (eds) Software Quality and Productivity. IFIP Advances in Information and Communication Technology. Springer, Boston, MA. https://doi.org/10.1007/978-0-387-34848-3_51
2. Harrison, W. A. (1984), Applying Mccabe's complexity measure to multiple-exit programs. Softw: Pract. Exper., 14: 1004-1007. https://doi.org/10.1002/spe.4380141009
3. dis - Disassembler for Python bytecode. https://docs.python.org/3.7/library/dis.html

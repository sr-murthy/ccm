README
======

This is an **experimental project** for calculating cyclomatic complexity measures (CCM) for Python source code using `CPython bytecode instructions <https://docs.python.org/3/library/dis.html#python-bytecode-instructions>`_.

The calculation of the measures is made possible using the following approach:

* From the given callable the CPython bytecode object is obtained using a `modifed version <https://github.com/sr-murthy/ccm/blob/master/src/ccm/xdis.py>`_ of the `dis library <https://docs.python.org/3/library/dis.html>`_ (an old version from Python 3.7), and the bytecode object is then disassembled into an instruction map of individual CPython bytecode instructions, which includes linking each bytecode instruction with its associated source line of code and bytecode block offset.
* Each instruction is classified as follows: an **entry point** if the instruction is the very first bytecode step of the callable, **branch point** if the instruction is a branching instruction to another instruction (e.g. :code:`JUMP`), a **decision point** if the instruction involves a comparison (e.g. :code:`COMPARE_OP`), or an **exit point** if the instruction stops execution of the callable and returns control flow back to the caller.
* Using the `networkx library <https://networkx.org/>`_ the bytecode instruction map is represented as a **directed graph**, called the **bytecode graph**, with nodes representing individual bytecode instructions, edges representing (explicit or implicit) transitions between instructions. Additionally, derived edges are added between all exit points and the (unique) entry point in order to make the graph **connected**.

The connected bytecode graph will have all of the structural information about the number of nodes, edges, connected components and the like, in order to calculate the CCMs.

There are six CCMs that can be calculated with this approach:

1. McCabe complexity (CC(G) - :code:`#{edges} - #{nodes} + 2)`
2. Generalised McCabe complexity (CC(G): :code:`#{edges} - #{nodes} + 2 * #{connected components})`
3. Henderson-Sellers complexity (CC(G): :code:`#{edges} - #{nodes} + #{connected components} + 1)`
4. Henderson-Sellers & Tegarden complexity (CC(G): :code:`#{edges} - #{nodes} + #{connected components})`
5. Generalised Henderson-Sellers & Tegarden complexity (CC(G): :code:`#{edges} - #{nodes} + #{exit points per component} + 2)`
6. Harrison complexity (CC(G): :code:`#{decision points} - #{exit points} + 2)`

An example: consider the following simple Python function for determining whether a given number (integer or float) is negative, zero, or positive:

.. code-block:: python

   def sign(x: int | float) -> typing.Literal[-1, 0, 1]:
       if x < 0:
           return -1
       if x == 0:
           return 0
       return 1

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
1. A Critical Re-examination of Cyclomatic Complexity Measures, B. Henderson-Sellers & D. Tegarden, Software Quality and Productivity, M. Lee et. al. (eds.), Springer, Dordrecht, 1995, pp.328-335.
2. Applying Mccabe's complexity measure to multiple‐exit programs, W. A. Harrison, Journal of Software: Practice and Experience, 14:10, 10/1984.
3. dis - Disassembler for Python bytecode, https://docs.python.org/3.7/library/dis.html

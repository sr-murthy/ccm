README
======

Cyclomatic complexity measures for CPython bytecode and Python source code.

Based on representing the incoming code object or representation as a graph, the following cyclomatic complexity measures can be computed:

1. McCabe complexity (CC(G) = `#{edges} - #{nodes} + 1)`
2. Generalised McCabe complexity (CC(G) = `#{edges} - #{nodes} + 2 * #{connected components})`
3. Henderson-Sellers complexity (CC(G) = `#{edges} - #{nodes} + #{connected components} + 1)`
4. Henderson-Sellers & Tegarden complexity (CC(G) = `#{edges} - #{nodes} + #{connected components})`
5. Generalised Henderson-Sellers & Tegarden complexity (CC(G) = `#{edges} - #{nodes} + #{exit points per component} + 2)`
6. Harrison complexity (CC(G) = #{decision points} - `#{exit points} + 2)`

References
----------
1. A Critical Re-examination of Cyclomatic Complexity Measures, B. Henderson-Sellers & D. Tegarden, *Software Quality and Productivity*, M. Lee et. al. (eds.), Springer, Dordrecht, 1995, pp.328-335.
2. Applying Mccabe's complexity measure to multiple‐exit programs, W. A. Harrison, *Journal of Software: Practice and Experience*, 14:10, 10/1984.

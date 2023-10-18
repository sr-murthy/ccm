README
======

Cyclomatic complexity measures for CPython bytecode and Python source code.

1. McCabe complexity (CC(G) = #{edges} - #{nodes} + 1)
2. Generalised McCabe complexity (CC(G) = #{edges} - #{nodes} + 2 * #{connected components})
3. Henderson-Sellers complexity (CC(G) = #{edges} - #{nodes} + #{connected components} + 1)
4. Henderson-Sellers & Tegarden complexity (CC(G) = #{edges} - #{nodes} + #{connected components})
5. Generalised Henderson-Sellers & Tegarden complexity (CC(G) = #{edges} - #{nodes} + #{exit points per component} + 2)
6. Harrison complexity (CC(G) = #{decision points} - #{exit points} + 2)

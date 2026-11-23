# ML Compiler Pass: Producer-Consumer Pointwise Fusion

Given an SSA computation graph as a topologically sorted list of node dicts:
```python
{"id": str, "op": str, "inputs": list[str], "kind": "compute" | "elementwise" | "io"}
```
Implement `fuse_elementwise_chains(nodes: list[dict]) -> list[list[str]]`:
- Group consecutive `elementwise` nodes into fused kernel groups (lists of node IDs) whenever:
  1. A producer `u` (`elementwise`) is consumed **exclusively** by a single consumer `v` (`elementwise`) (fan-out of `u` is 1), OR
  2. A `compute` node (e.g., `matmul`) feeds directly into a single-consumer `elementwise` epilogue (e.g., `bias_add` -> `gelu`), fusing the compute node + its linear elementwise epilogue chain!
- Never fuse two `compute` nodes together, and never fuse `io` nodes.
- Return the list of fused groups in topological order.

# Causal Concept Erasure (Orthogonal Projection Ablation)

Given hidden activations `H` of shape `(N, D)` and a learned linear concept direction `v` of shape `(D,)`:

Implement `erase_concept_direction(H: np.ndarray, v: np.ndarray) -> np.ndarray`:
1. Normalize $u = v / \|v\|_2$.
2. Project every row of `H` onto the orthogonal complement of $u$:
   $$H_{\text{erased}} = H - (H u) u^\top$$
3. Return `H_erased` of shape `(N, D)`. If $\|v\|_2 == 0$, raise `ValueError`.

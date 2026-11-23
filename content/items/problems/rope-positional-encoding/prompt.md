# Rotary Position Embeddings (RoPE)

Implement `apply_rope(x: np.ndarray, base: float = 10000.0) -> np.ndarray` for input `x` of shape `(B, T, D)` (where `D` is even).
For each adjacent pair `(2i, 2i+1)` and sequence position `m in [0, T-1]`:
- Frequency: $\theta_i = \text{base}^{-2i / D}$
- Angle: $\phi_{m,i} = m \cdot \theta_i$
- Apply 2D rotation:
  - $x'_{2i} = x_{2i}\cos\phi - x_{2i+1}\sin\phi$
  - $x'_{2i+1} = x_{2i}\sin\phi + x_{2i+1}\cos\phi$

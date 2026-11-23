# Blocked (Tiled) Matrix Multiplication (GEMM)

Implement `tiled_gemm(A: np.ndarray, B: np.ndarray, tile_size: int = 16) -> np.ndarray` that computes $C = A B$ for 2D float matrices $A \in \mathbb{R}^{M \times K}$ and $B \in \mathbb{R}^{K \times N}$ using **explicit 3-level tiling** over `(i0, j0, k0)` with block size `tile_size`.

### Constraints
- Do **not** call `np.matmul`, `np.dot`, `np.einsum`, `np.tensordot`, or use the `@` operator (checked statically by AST guard!).
- Handle arbitrary matrix dimensions $M, K, N$ that are **not** multiples of `tile_size`.
- Raise `ValueError` if `A.shape[1] != B.shape[0]`.

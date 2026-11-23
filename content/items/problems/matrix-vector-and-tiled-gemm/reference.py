import numpy as np

def tiled_gemm(A: np.ndarray, B: np.ndarray, tile_size: int = 16) -> np.ndarray:
    A = np.asarray(A, dtype=np.float64)
    B = np.asarray(B, dtype=np.float64)
    if A.ndim != 2 or B.ndim != 2 or A.shape[1] != B.shape[0]:
        raise ValueError("Incompatible shapes for matrix multiplication")
    M, K = A.shape
    _, N = B.shape
    C = np.zeros((M, N), dtype=np.float64)
    for i0 in range(0, M, tile_size):
        i1 = min(i0 + tile_size, M)
        for k0 in range(0, K, tile_size):
            k1 = min(k0 + tile_size, K)
            for j0 in range(0, N, tile_size):
                j1 = min(j0 + tile_size, N)
                # Accumulate tile product explicitly
                for i in range(i0, i1):
                    for k in range(k0, k1):
                        aik = A[i, k]
                        C[i, j0:j1] += aik * B[k, j0:j1]
    return C

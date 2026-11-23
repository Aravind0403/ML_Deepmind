import numpy as np

def gcn_layer(A: np.ndarray, X: np.ndarray, W: np.ndarray) -> np.ndarray:
    A = np.asarray(A, dtype=np.float64)
    X = np.asarray(X, dtype=np.float64)
    W = np.asarray(W, dtype=np.float64)
    N = A.shape[0]
    A_tilde = A + np.eye(N)
    deg = A_tilde.sum(axis=1)
    d_inv_sqrt = np.where(deg > 0, deg ** -0.5, 0.0)
    A_hat = (d_inv_sqrt[:, None] * A_tilde) * d_inv_sqrt[None, :]
    return np.maximum(0.0, A_hat @ X @ W)

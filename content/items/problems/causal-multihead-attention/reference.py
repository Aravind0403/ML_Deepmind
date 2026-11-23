import numpy as np

def causal_mha(
    X: np.ndarray,
    W_q: np.ndarray,
    W_k: np.ndarray,
    W_v: np.ndarray,
    W_o: np.ndarray,
    num_heads: int,
) -> np.ndarray:
    B, T, D = X.shape
    d_h = D // num_heads
    Q = (X @ W_q).reshape(B, T, num_heads, d_h).transpose(0, 2, 1, 3)
    K = (X @ W_k).reshape(B, T, num_heads, d_h).transpose(0, 2, 1, 3)
    V = (X @ W_v).reshape(B, T, num_heads, d_h).transpose(0, 2, 1, 3)

    scores = (Q @ K.transpose(0, 1, 3, 2)) / np.sqrt(d_h)
    mask = np.triu(np.ones((T, T), dtype=bool), k=1)
    scores = np.where(mask, -1e9, scores)
    scores = scores - np.max(scores, axis=-1, keepdims=True)
    weights = np.exp(scores)
    weights = weights / np.sum(weights, axis=-1, keepdims=True)

    ctx = (weights @ V).transpose(0, 2, 1, 3).reshape(B, T, D)
    return ctx @ W_o

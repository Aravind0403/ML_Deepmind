import numpy as np

def online_softmax_attention(
    q: np.ndarray, K: np.ndarray, V: np.ndarray, block_size: int = 4
) -> np.ndarray:
    q = np.asarray(q, dtype=np.float64)
    K = np.asarray(K, dtype=np.float64)
    V = np.asarray(V, dtype=np.float64)
    N, D = K.shape
    scale = 1.0 / np.sqrt(D)
    m = -np.inf
    l = 0.0
    acc = np.zeros(D, dtype=np.float64)
    for start in range(0, N, block_size):
        k_blk = K[start:start + block_size]
        v_blk = V[start:start + block_size]
        scores = (k_blk @ q) * scale
        m_blk = float(np.max(scores))
        m_new = max(m, m_blk)
        alpha = np.exp(m - m_new) if np.isfinite(m) else 0.0
        p_blk = np.exp(scores - m_new)
        l = l * alpha + float(np.sum(p_blk))
        acc = acc * alpha + (p_blk @ v_blk)
        m = m_new
    return acc / l

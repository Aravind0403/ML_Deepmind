import numpy as np

def stable_causal_attention_fp16(Q: np.ndarray, K: np.ndarray, V: np.ndarray) -> np.ndarray:
    Q32 = np.asarray(Q, dtype=np.float32)
    K32 = np.asarray(K, dtype=np.float32)
    V32 = np.asarray(V, dtype=np.float32)
    T, D = Q32.shape
    scores = (Q32 @ K32.T) / np.sqrt(float(D))
    mask = np.triu(np.ones((T, T), dtype=bool), k=1)
    scores = np.where(mask, -1e9, scores)
    scores = scores - np.max(scores, axis=-1, keepdims=True)
    exp_s = np.exp(scores)
    weights = exp_s / np.sum(exp_s, axis=-1, keepdims=True)
    return (weights @ V32).astype(np.float16)

import numpy as np

def stable_causal_attention_fp16(Q: np.ndarray, K: np.ndarray, V: np.ndarray) -> np.ndarray:
    T, D = Q.shape
    scores = Q @ K.T                                  # BUG: no 1/sqrt(D), stays fp16
    mask = np.tril(np.ones((T, T), dtype=bool), k=-1) # BUG: masks past instead of future!
    scores = np.where(mask, np.float16(-1e4), scores)
    exp_s = np.exp(scores)                            # BUG: overflows fp16 -> inf -> NaN!
    weights = exp_s / np.sum(exp_s, axis=-1, keepdims=True)
    return (weights @ V).astype(np.float16)

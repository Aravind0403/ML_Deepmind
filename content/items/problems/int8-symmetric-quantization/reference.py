import numpy as np

def quantize_per_channel_int8(W: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    W = np.asarray(W, dtype=np.float32)
    max_abs = np.max(np.abs(W), axis=1, keepdims=True)
    scales = np.where(max_abs > 0, max_abs / 127.0, 1.0).astype(np.float32)
    q = np.clip(np.round(W / scales), -127, 127).astype(np.int8)
    w_deq = (q.astype(np.float32) * scales).astype(np.float32)
    return q, scales, w_deq

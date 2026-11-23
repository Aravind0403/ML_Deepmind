import numpy as np

def apply_rope(x: np.ndarray, base: float = 10000.0) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    B, T, D = x.shape
    half = D // 2
    freqs = base ** (-2.0 * np.arange(half) / D)
    pos = np.arange(T)[:, None]
    angles = pos * freqs[None, :]  # (T, half)
    cos_a = np.cos(angles)[None, :, :]
    sin_a = np.sin(angles)[None, :, :]
    x_even = x[..., 0::2]
    x_odd = x[..., 1::2]
    out = np.empty_like(x)
    out[..., 0::2] = x_even * cos_a - x_odd * sin_a
    out[..., 1::2] = x_even * sin_a + x_odd * cos_a
    return out

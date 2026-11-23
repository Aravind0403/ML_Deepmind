import numpy as np

def erase_concept_direction(H: np.ndarray, v: np.ndarray) -> np.ndarray:
    H = np.asarray(H, dtype=np.float64)
    v = np.asarray(v, dtype=np.float64)
    norm = float(np.linalg.norm(v))
    if norm == 0.0:
        raise ValueError("Concept direction vector cannot be zero")
    u = v / norm
    proj = np.outer(H @ u, u)
    return H - proj

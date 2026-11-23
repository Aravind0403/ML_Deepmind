import numpy as np

def dpo_loss(
    pi_chosen: np.ndarray,
    pi_rejected: np.ndarray,
    ref_chosen: np.ndarray,
    ref_rejected: np.ndarray,
    beta: float = 0.1,
) -> tuple[float, float]:
    raise NotImplementedError

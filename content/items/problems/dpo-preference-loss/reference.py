import numpy as np

def dpo_loss(
    pi_chosen: np.ndarray,
    pi_rejected: np.ndarray,
    ref_chosen: np.ndarray,
    ref_rejected: np.ndarray,
    beta: float = 0.1,
) -> tuple[float, float]:
    h = beta * ((np.asarray(pi_chosen) - np.asarray(ref_chosen)) - (np.asarray(pi_rejected) - np.asarray(ref_rejected)))
    loss = float(np.mean(np.logaddexp(0.0, -h)))
    return loss, float(np.mean(h))

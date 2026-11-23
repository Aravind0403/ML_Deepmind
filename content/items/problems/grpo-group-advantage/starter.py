import numpy as np

def grpo_loss(
    rewards: np.ndarray,
    logp_new: np.ndarray,
    logp_old: np.ndarray,
    logp_ref: np.ndarray,
    eps: float = 0.2,
    beta: float = 0.04,
) -> float:
    raise NotImplementedError

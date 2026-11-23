import numpy as np

def grpo_loss(
    rewards: np.ndarray,
    logp_new: np.ndarray,
    logp_old: np.ndarray,
    logp_ref: np.ndarray,
    eps: float = 0.2,
    beta: float = 0.04,
) -> float:
    r = np.asarray(rewards, dtype=np.float64)
    ln = np.asarray(logp_new, dtype=np.float64)
    lo = np.asarray(logp_old, dtype=np.float64)
    lr = np.asarray(logp_ref, dtype=np.float64)

    adv = (r - np.mean(r)) / (np.std(r) + 1e-8)
    ratio = np.exp(ln - lo)
    clipped = np.clip(ratio, 1.0 - eps, 1.0 + eps)
    surr = np.minimum(ratio * adv, clipped * adv)
    delta = lr - ln
    kl = np.exp(delta) - delta - 1.0
    return float(-np.mean(surr - beta * kl))

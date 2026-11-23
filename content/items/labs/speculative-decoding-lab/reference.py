import numpy as np

def speculative_step(
    p_target: np.ndarray,
    q_draft: np.ndarray,
    draft_token: int,
    rng: np.random.Generator,
) -> int:
    p = np.asarray(p_target, dtype=np.float64)
    q = np.asarray(q_draft, dtype=np.float64)
    accept_prob = min(1.0, float(p[draft_token]) / max(float(q[draft_token]), 1e-12))
    if rng.random() < accept_prob:
        return int(draft_token)
    residual = np.maximum(0.0, p - q)
    total = float(residual.sum())
    if total <= 1e-12:
        return int(rng.choice(len(p), p=p))
    residual /= total
    return int(rng.choice(len(p), p=residual))

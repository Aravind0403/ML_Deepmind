import numpy as np

def speculative_step(
    p_target: np.ndarray,
    q_draft: np.ndarray,
    draft_token: int,
    rng: np.random.Generator,
) -> int:
    # Naive bug: always accepts draft token (distorts distribution!)
    return draft_token

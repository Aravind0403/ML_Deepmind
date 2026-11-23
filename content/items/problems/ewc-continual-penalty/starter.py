import numpy as np

def ewc_penalty_and_grad(
    theta: np.ndarray,
    theta_star: np.ndarray,
    fisher: np.ndarray,
    lam: float,
) -> tuple[float, np.ndarray]:
    raise NotImplementedError

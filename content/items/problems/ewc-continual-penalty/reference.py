import numpy as np

def ewc_penalty_and_grad(
    theta: np.ndarray,
    theta_star: np.ndarray,
    fisher: np.ndarray,
    lam: float,
) -> tuple[float, np.ndarray]:
    diff = np.asarray(theta, dtype=np.float64) - np.asarray(theta_star, dtype=np.float64)
    F = np.asarray(fisher, dtype=np.float64)
    penalty = 0.5 * lam * float(np.sum(F * (diff ** 2)))
    grad = lam * F * diff
    return penalty, grad

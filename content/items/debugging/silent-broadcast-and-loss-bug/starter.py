import numpy as np

def train_linear_sgd(X: np.ndarray, y: np.ndarray, lr: float = 0.05, steps: int = 300):
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)  # shape (N,)
    N, D = X.shape
    w = np.zeros((D, 1), dtype=np.float64)
    b = 0.0
    grad_w = np.zeros_like(w)
    grad_b = 0.0

    for _ in range(steps):
        pred = X @ w + b            # BUG 1: shape (N, 1) while y is (N,) -> err is (N, N)!
        err = pred - y
        grad_w += (2.0 / N) * (X.T @ err.mean(axis=1, keepdims=True))  # BUG 2: never zeroed!
        grad_b += (2.0 / N) * float(np.sum(err)) / N
        w -= lr * grad_w
        b -= lr * grad_b

    final_pred = (X @ w).reshape(-1) + b
    final_mse = float(np.mean((final_pred - y) ** 2))
    return w.reshape(-1), float(b), final_mse

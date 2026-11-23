import numpy as np

def train_linear_sgd(X: np.ndarray, y: np.ndarray, lr: float = 0.05, steps: int = 300):
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64).reshape(-1)
    N, D = X.shape
    w = np.zeros(D, dtype=np.float64)
    b = 0.0

    for _ in range(steps):
        pred = X @ w + b
        err = pred - y  # shape (N,)
        grad_w = (2.0 / N) * (X.T @ err)
        grad_b = (2.0 / N) * float(np.sum(err))
        w -= lr * grad_w
        b -= lr * grad_b

    final_pred = X @ w + b
    final_mse = float(np.mean((final_pred - y) ** 2))
    return w, float(b), final_mse

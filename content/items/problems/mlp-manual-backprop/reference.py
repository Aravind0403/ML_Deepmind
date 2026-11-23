import numpy as np

def mlp_forward_backward(X, W1, b1, W2, b2, Y):
    Z1 = X @ W1 + b1
    A1 = np.maximum(0.0, Z1)
    Y_hat = A1 @ W2 + b2
    diff = Y_hat - Y
    loss = float(np.mean(diff ** 2))

    dY = (2.0 / diff.size) * diff
    dW2 = A1.T @ dY
    db2 = np.sum(dY, axis=0)
    dA1 = dY @ W2.T
    dZ1 = dA1 * (Z1 > 0)
    dW1 = X.T @ dZ1
    db1 = np.sum(dZ1, axis=0)
    return loss, {"W1": dW1, "b1": db1, "W2": dW2, "b2": db2}

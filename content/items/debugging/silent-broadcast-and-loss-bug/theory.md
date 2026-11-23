## Why Silent Broadcasting Bugs Kill Real ML Runs

In NumPy/PyTorch, subtracting `(N, 1)` from `(N,)` silently broadcasts to `(N, N)` — `loss.mean()` still returns a scalar float so nothing crashes, while gradients are completely corrupted! Always assert explicit shapes (`assert pred.shape == y.shape`).

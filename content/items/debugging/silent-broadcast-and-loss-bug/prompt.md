# Authentic ML Debugging Arena — Bug Hunt #1

The linear regression SGD training loop below runs without raising any exceptions — **yet the loss diverges or converges to the wrong weights!**

There are **two classic real-world ML bugs** hidden in `train_linear_sgd(X, y, lr=0.05, steps=300)`:
1. A silent NumPy broadcasting bug where `(N, 1) - (N,)` produces an `(N, N)` pairwise difference matrix instead of `(N,)` residuals.
2. A gradient accumulator bug where `grad_w` and `grad_b` are accumulated across steps without resetting (`+=` instead of fresh per-step gradient), causing momentum explosion.

**Fix both bugs** so `train_linear_sgd` returns `(w, b, final_mse)` with `final_mse < 1e-4` and `w` recovering the ground-truth weights cleanly.

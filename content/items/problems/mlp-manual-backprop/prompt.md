# 2-Layer MLP Forward & Manual Backpropagation

Given `X: (N, D_in)`, `W1: (D_in, H)`, `b1: (H,)`, `W2: (H, D_out)`, `b2: (D_out,)`, and target `Y: (N, D_out)`:
- Forward: `Z1 = X @ W1 + b1`, `A1 = ReLU(Z1)`, `Y_hat = A1 @ W2 + b2`
- Loss: Mean Squared Error $L = \frac{1}{N \cdot D_{\text{out}}} \sum (\hat{Y} - Y)^2$.

Implement `mlp_forward_backward(X, W1, b1, W2, b2, Y)` returning `(loss, grads)` where `grads` is a dict with keys `"W1", "b1", "W2", "b2"`.

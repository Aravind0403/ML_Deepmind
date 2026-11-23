# Causal Multi-Head Self-Attention from Scratch

Implement `causal_mha(X, W_q, W_k, W_v, W_o, num_heads)` in pure NumPy:
- `X`: shape `(B, T, D)`
- `W_q, W_k, W_v, W_o`: shape `(D, D)`
- Split `D` into `num_heads` heads of dimension `d_h = D // num_heads`.
- Compute scaled dot-product attention with a **strict causal mask** (position `t` may only attend to `<= t`), using numerically stable softmax.
- Recombine heads and project with `W_o`, returning shape `(B, T, D)`.

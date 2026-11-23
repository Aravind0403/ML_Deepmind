# FlashAttention Online Softmax Rescaling

Implement `online_softmax_attention(q: np.ndarray, K: np.ndarray, V: np.ndarray, block_size: int = 4) -> np.ndarray`:
- `q`: single query vector `(D,)`
- `K`: keys `(N, D)`
- `V`: values `(N, D)`
- Process `(K, V)` strictly in streaming blocks of size `block_size` without ever materializing the full `(N,)` attention weight vector!
- Maintain running `(m, l, acc)` where `m` is running max logit, `l` is running denominator sum, and `acc` is running unnormalized weighted value sum.
- Return the exact attention output `(D,)` matching standard scaled dot-product attention.

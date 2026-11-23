## Mixed-Precision Softmax Rule

`float16` max finite value is `65504`, so `exp(x)` overflows for `x > 11.09`. Production kernels (PyTorch SDPA, FlashAttention, Triton) ALWAYS accumulate softmax in `float32` even when `Q, K, V` are `fp16` or `bf16`.

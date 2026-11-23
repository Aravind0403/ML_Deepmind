# Per-Channel Symmetric INT8 Quantization

Implement `quantize_per_channel_int8(W: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]` for a 2D weight matrix `W` of shape `(C_out, C_in)`:
- For each output channel `c`, compute scale $s_c = \max(|W_c|) / 127.0$ (if a channel is all zeros, set $s_c = 1.0$ to avoid division by zero).
- Quantize: $Q_c = \mathrm{clip}(\mathrm{round}(W_c / s_c), -127, 127)$ as `np.int8`.
- Dequantize: $\hat{W}_c = Q_c \cdot s_c$ as `np.float32`.
- Return `(Q, scales, W_dequant)` where `scales` has shape `(C_out, 1)`.

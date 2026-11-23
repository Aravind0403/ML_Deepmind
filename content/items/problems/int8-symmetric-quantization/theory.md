## Per-Channel vs Per-Tensor Quantization

A single outlier weight in one output channel ruins the dynamic range of an entire tensor under per-tensor scaling. Per-channel scales isolate outliers to their own row with negligible storage overhead (`1 float` per row).

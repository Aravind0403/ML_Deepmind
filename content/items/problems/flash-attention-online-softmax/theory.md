## Online Softmax Is the Heart of FlashAttention

When a new tile yields max $m_{\text{new}} = \max(m, m_{\text{tile}})$, rescaling prior accumulators by $e^{m - m_{\text{new}}}$ allows streaming $K, V$ tiles through GPU SRAM in $O(N)$ HBM reads instead of $O(N^2)$.

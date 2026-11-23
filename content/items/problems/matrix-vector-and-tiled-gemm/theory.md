## Why Tiling Matters for ML Infra & GPU Kernels

Naive matrix multiply streams $B$ out of L1/SRAM repeatedly for every row of $A$, giving poor **arithmetic intensity**.
Blocking into $T \times T$ tiles keeps three small sub-blocks ($A_{ik}, B_{kj}, C_{ij}$) hot in fast cache/SRAM, increasing data reuse by a factor of $\mathcal{O}(T)$ — the exact same principle behind FlashAttention and CUTLASS shared-memory GEMM.

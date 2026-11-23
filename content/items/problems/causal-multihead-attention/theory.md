## Causal Multi-Head Attention

For each head $h$, with $Q_h, K_h, V_h \in \mathbb{R}^{B \times T \times d_h}$:
$$\mathrm{Attn}(Q_h, K_h, V_h) = \mathrm{softmax}\!\left(\frac{Q_h K_h^\top}{\sqrt{d_h}} + M\right) V_h$$
where $M_{ij} = 0$ if $j \le i$ else $-\infty$. Subtract `max` before `exp` for numerical stability.

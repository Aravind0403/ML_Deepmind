# Worked Example: Why Scaled Dot-Product Attention Divides by $\sqrt{d_k}$

Suppose query $q \in \mathbb{R}^{d_k}$ and key $k \in \mathbb{R}^{d_k}$ have i.i.d. entries with mean $0$ and variance $1$:
$$\mathbb{E}[q_i] = 0, \quad \mathrm{Var}(q_i) = 1, \quad \mathbb{E}[k_i] = 0, \quad \mathrm{Var}(k_i) = 1$$

Because $q_i$ and $k_i$ are independent:
$$\mathrm{Var}(q_i k_i) = \mathbb{E}[q_i^2]\mathbb{E}[k_i^2] - (\mathbb{E}[q_i]\mathbb{E}[k_i])^2 = 1 \cdot 1 - 0 = 1$$

Summing $d_k$ independent terms gives:
$$\mathrm{Var}(q^\top k) = \sum_{i=1}^{d_k} \mathrm{Var}(q_i k_i) = d_k$$

Scaling by $\frac{1}{\sqrt{d_k}}$ restores unit variance:
$$\mathrm{Var}\left(\frac{q^\top k}{\sqrt{d_k}}\right) = \frac{1}{d_k} \cdot d_k = 1$$

Without this scaling, large $d_k$ pushes logits into the saturated tails of softmax where gradients vanish.

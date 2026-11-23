# Lab: Distribution-Preserving Speculative Decoding

Implement `speculative_step(p_target: np.ndarray, q_draft: np.ndarray, draft_token: int, rng: np.random.Generator) -> int`:
- `p_target` and `q_draft` are 1D probability distributions over vocabulary size `V`.
- `draft_token` was already sampled from `q_draft`.
- Accept `draft_token` with probability $\min\left(1, \frac{p(x)}{q(x)}\right)$.
- If rejected, sample a replacement token from the **normalized residual distribution**:
  $$p_{\text{res}}(x) = \frac{\max(0, p(x) - q(x))}{\sum_j \max(0, p(j) - q(j))}$$

### Lab Evaluation Gate
The harness runs 40,000 Monte Carlo trials across skewed draft/target distributions and verifies Total Variation Distance `TV(empirical, p_target) <= 0.02`.

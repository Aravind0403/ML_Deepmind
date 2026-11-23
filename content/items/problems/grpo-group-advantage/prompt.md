# Group Relative Policy Optimization (GRPO)

Given a group of $G$ rollouts for one prompt:
- `rewards`: shape `(G,)`
- `logp_new`: shape `(G,)` (sum or mean token log-probs under current policy $\pi_\theta$)
- `logp_old`: shape `(G,)` (log-probs under behavior policy $\pi_{\text{old}}$)
- `logp_ref`: shape `(G,)` (log-probs under reference policy $\pi_{\text{ref}}$)
- `eps`: clip parameter (default `0.2`), `beta`: KL weight (default `0.04`)

Implement `grpo_loss(rewards, logp_new, logp_old, logp_ref, eps=0.2, beta=0.04) -> float`:
1. Group-normalized advantage: $A_i = \frac{r_i - \mathrm{mean}(r)}{\mathrm{std}(r) + 10^{-8}}$.
2. Importance ratio: $\rho_i = \exp(\log\pi_\theta - \log\pi_{\text{old}})$.
3. Clipped surrogate: $s_i = \min(\rho_i A_i, \mathrm{clip}(\rho_i, 1-\epsilon, 1+\epsilon) A_i)$.
4. Unbiased Schulman KL estimator: $\mathrm{KL}_i = \exp(\log\pi_{\text{ref}} - \log\pi_\theta) - (\log\pi_{\text{ref}} - \log\pi_\theta) - 1$.
5. Return scalar loss to **minimize**: $-\frac{1}{G}\sum_i (s_i - \beta \cdot \mathrm{KL}_i)$.

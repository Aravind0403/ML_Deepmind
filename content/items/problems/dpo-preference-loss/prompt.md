# Direct Preference Optimization (DPO)

Given batch arrays of shape `(B,)`:
- `pi_chosen`, `pi_rejected`: policy log-probabilities $\log\pi_\theta(y_w|x), \log\pi_\theta(y_l|x)$
- `ref_chosen`, `ref_rejected`: reference log-probabilities $\log\pi_{\text{ref}}(y_w|x), \log\pi_{\text{ref}}(y_l|x)$
- `beta`: temperature parameter (default `0.1`)

Implement `dpo_loss(pi_chosen, pi_rejected, ref_chosen, ref_rejected, beta=0.1) -> tuple[float, float]`:
- Implicit reward margin: $h_i = \beta [(\log\pi_\theta(y_w) - \log\pi_{\text{ref}}(y_w)) - (\log\pi_\theta(y_l) - \log\pi_{\text{ref}}(y_l))]$.
- Loss: $\mathcal{L}_{\text{DPO}} = -\mathrm{mean}(\log\sigma(h_i)) = \mathrm{mean}(\log(1 + e^{-h_i}))$ (use numerically stable `logaddexp`).
- Return `(loss: float, mean_margin: float)`.

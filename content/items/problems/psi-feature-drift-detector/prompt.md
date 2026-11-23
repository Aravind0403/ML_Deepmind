# Population Stability Index (PSI) for Production Drift

Implement `compute_psi(expected: np.ndarray, actual: np.ndarray, num_bins: int = 10, eps: float = 1e-6) -> tuple[float, str]`:
1. Compute quantile bin edges from `expected` (from `0` to `100` percentiles, with `-inf` and `+inf` outer edges so out-of-range production values are captured).
2. Compute bin proportions $e_i, a_i$ for `expected` and `actual`, clamping any zero proportion to `eps`.
3. Compute $\mathrm{PSI} = \sum_i (a_i - e_i) \ln(a_i / e_i)$.
4. Return `(psi, status)` where `status` is `"ok"` if `psi < 0.1`, `"moderate_drift"` if `0.1 <= psi < 0.25`, else `"severe_drift"`.

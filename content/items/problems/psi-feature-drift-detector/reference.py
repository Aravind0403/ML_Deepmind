import numpy as np

def compute_psi(
    expected: np.ndarray,
    actual: np.ndarray,
    num_bins: int = 10,
    eps: float = 1e-6,
) -> tuple[float, str]:
    exp = np.asarray(expected, dtype=np.float64)
    act = np.asarray(actual, dtype=np.float64)
    quantiles = np.linspace(0, 100, num_bins + 1)
    edges = np.percentile(exp, quantiles)
    edges[0] = -np.inf
    edges[-1] = np.inf
    edges = np.unique(edges)

    e_counts, _ = np.histogram(exp, bins=edges)
    a_counts, _ = np.histogram(act, bins=edges)
    e_pct = np.clip(e_counts / max(len(exp), 1), eps, None)
    a_pct = np.clip(a_counts / max(len(act), 1), eps, None)

    psi = float(np.sum((a_pct - e_pct) * np.log(a_pct / e_pct)))
    if psi < 0.1:
        status = "ok"
    elif psi < 0.25:
        status = "moderate_drift"
    else:
        status = "severe_drift"
    return psi, status

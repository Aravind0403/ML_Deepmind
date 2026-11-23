import numpy as np

def evaluate_lab(user_mod):
    rng = np.random.default_rng(2026)
    p = np.array([0.45, 0.25, 0.15, 0.10, 0.05], dtype=np.float64)
    q = np.array([0.15, 0.45, 0.25, 0.05, 0.10], dtype=np.float64)
    V = len(p)
    counts = np.zeros(V, dtype=np.float64)
    trials = 25000
    draft_tokens = rng.choice(V, size=trials, p=q)
    for dt in draft_tokens:
        tok = user_mod.speculative_step(p, q, int(dt), rng)
        counts[int(tok)] += 1
    emp = counts / trials
    tv = 0.5 * float(np.sum(np.abs(emp - p)))
    passed = tv <= 0.02
    return {
        "passed": passed,
        "metric": round(tv, 5),
        "threshold": 0.02,
        "details": f"Total Variation Distance = {tv:.5f} (target <= 0.02; exact target match preserved)"
    }

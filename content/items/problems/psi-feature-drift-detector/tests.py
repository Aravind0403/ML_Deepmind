import numpy as np

def test_no_drift_vs_severe_drift(user_mod):
    rng = np.random.default_rng(10)
    base = rng.normal(0.0, 1.0, size=2000)
    same = rng.normal(0.0, 1.0, size=2000)
    shifted = rng.normal(1.5, 1.0, size=2000)

    psi_ok, st_ok = user_mod.compute_psi(base, same)
    assert psi_ok < 0.1 and st_ok == "ok"

    psi_bad, st_bad = user_mod.compute_psi(base, shifted)
    assert psi_bad >= 0.25 and st_bad == "severe_drift"

import numpy as np

def test_recovers_exact_weights_and_low_mse(user_mod):
    rng = np.random.default_rng(12)
    X = rng.standard_normal((120, 4))
    true_w = np.array([2.5, -1.3, 0.7, 4.0])
    true_b = -0.8
    y = X @ true_w + true_b
    w, b, mse = user_mod.train_linear_sgd(X, y, lr=0.05, steps=350)
    assert w.shape == (4,)
    assert np.isfinite(mse) and mse < 1e-4
    np.testing.assert_allclose(w, true_w, atol=1e-2)
    np.testing.assert_allclose(b, true_b, atol=1e-2)

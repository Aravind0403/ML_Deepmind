import numpy as np

def test_causality_no_future_leak(user_mod):
    rng = np.random.default_rng(7)
    B, T, D, H = 2, 6, 8, 2
    X = rng.standard_normal((B, T, D))
    Wq, Wk, Wv, Wo = [rng.standard_normal((D, D)) * 0.2 for _ in range(4)]
    out1 = user_mod.causal_mha(X, Wq, Wk, Wv, Wo, H)
    X2 = X.copy()
    X2[:, -1, :] += 50.0  # Perturb last token heavily
    out2 = user_mod.causal_mha(X2, Wq, Wk, Wv, Wo, H)
    assert out1.shape == (B, T, D)
    np.testing.assert_allclose(out1[:, :-1, :], out2[:, :-1, :], atol=1e-6)

def test_matches_reference_values(user_mod):
    rng = np.random.default_rng(11)
    B, T, D, H = 1, 4, 4, 2
    X = rng.standard_normal((B, T, D))
    Wq = np.eye(D); Wk = np.eye(D); Wv = np.eye(D); Wo = np.eye(D)
    out = user_mod.causal_mha(X, Wq, Wk, Wv, Wo, H)
    # First token can only attend to itself -> output at t=0 equals X[:,0,:]
    np.testing.assert_allclose(out[:, 0, :], X[:, 0, :], atol=1e-6)

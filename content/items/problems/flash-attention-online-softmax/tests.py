import numpy as np

def test_matches_full_attention_exact(user_mod):
    rng = np.random.default_rng(17)
    N, D = 23, 16
    q = rng.standard_normal(D)
    K = rng.standard_normal((N, D))
    V = rng.standard_normal((N, D))
    out = user_mod.online_softmax_attention(q, K, V, block_size=5)
    scores = (K @ q) / np.sqrt(D)
    scores -= scores.max()
    w = np.exp(scores) / np.exp(scores).sum()
    expected = w @ V
    np.testing.assert_allclose(out, expected, rtol=1e-6, atol=1e-6)

import numpy as np

def test_norm_preservation(user_mod):
    rng = np.random.default_rng(3)
    x = rng.standard_normal((2, 10, 16))
    y = user_mod.apply_rope(x)
    np.testing.assert_allclose(np.linalg.norm(y, axis=-1), np.linalg.norm(x, axis=-1), atol=1e-6)

def test_relative_dot_product_invariance(user_mod):
    rng = np.random.default_rng(5)
    q = rng.standard_normal((1, 1, 8))
    k = rng.standard_normal((1, 1, 8))
    Q = np.repeat(q, 10, axis=1)
    K = np.repeat(k, 10, axis=1)
    Qr = user_mod.apply_rope(Q)
    Kr = user_mod.apply_rope(K)
    # Dot(m=2, n=5) must equal Dot(m=4, n=7) since relative offset is 3
    d1 = float(np.dot(Qr[0, 2], Kr[0, 5]))
    d2 = float(np.dot(Qr[0, 4], Kr[0, 7]))
    np.testing.assert_allclose(d1, d2, atol=1e-6)

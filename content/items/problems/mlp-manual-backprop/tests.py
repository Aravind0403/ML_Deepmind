import numpy as np

def test_gradients_match_finite_diff(user_mod):
    rng = np.random.default_rng(21)
    X = rng.standard_normal((5, 4))
    W1 = rng.standard_normal((4, 6)) * 0.5
    b1 = rng.standard_normal(6) * 0.1
    W2 = rng.standard_normal((6, 3)) * 0.5
    b2 = rng.standard_normal(3) * 0.1
    Y = rng.standard_normal((5, 3))

    loss, grads = user_mod.mlp_forward_backward(X, W1, b1, W2, b2, Y)
    assert np.isfinite(loss)
    eps = 1e-6
    for name, arr in [("W1", W1), ("b1", b1), ("W2", W2), ("b2", b2)]:
        num = np.zeros_like(arr)
        it = np.nditer(arr, flags=["multi_index"])
        while not it.finished:
            idx = it.multi_index
            orig = arr[idx]
            arr[idx] = orig + eps
            lp, _ = user_mod.mlp_forward_backward(X, W1, b1, W2, b2, Y)
            arr[idx] = orig - eps
            lm, _ = user_mod.mlp_forward_backward(X, W1, b1, W2, b2, Y)
            arr[idx] = orig
            num[idx] = (lp - lm) / (2 * eps)
            it.iternext()
        np.testing.assert_allclose(grads[name], num, rtol=1e-4, atol=1e-5)

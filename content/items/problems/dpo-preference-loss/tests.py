import numpy as np

def test_dpo_zero_margin_is_log2(user_mod):
    a = np.array([-1.0, -2.0])
    loss, margin = user_mod.dpo_loss(a, a, a, a, beta=0.1)
    np.testing.assert_allclose(loss, np.log(2.0), atol=1e-6)
    np.testing.assert_allclose(margin, 0.0, atol=1e-6)

def test_dpo_numerical_stability_extreme_margin(user_mod):
    loss, margin = user_mod.dpo_loss(np.array([-1000.0]), np.array([0.0]), np.array([0.0]), np.array([0.0]), beta=1.0)
    assert np.isfinite(loss)
    np.testing.assert_allclose(loss, 1000.0, atol=1e-4)

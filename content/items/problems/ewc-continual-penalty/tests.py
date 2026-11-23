import numpy as np

def test_ewc_values_and_finite_diff(user_mod):
    theta = np.array([1.2, -0.5, 2.0])
    star = np.array([1.0, 0.0, 1.5])
    F = np.array([10.0, 2.0, 0.5])
    lam = 4.0
    pen, grad = user_mod.ewc_penalty_and_grad(theta, star, F, lam)
    expected_pen = 0.5 * 4.0 * (10.0 * 0.04 + 2.0 * 0.25 + 0.5 * 0.25)
    np.testing.assert_allclose(pen, expected_pen, atol=1e-6)
    # Finite difference check
    eps = 1e-6
    for i in range(len(theta)):
        t_plus = theta.copy(); t_plus[i] += eps
        t_minus = theta.copy(); t_minus[i] -= eps
        p_plus, _ = user_mod.ewc_penalty_and_grad(t_plus, star, F, lam)
        p_minus, _ = user_mod.ewc_penalty_and_grad(t_minus, star, F, lam)
        np.testing.assert_allclose(grad[i], (p_plus - p_minus) / (2 * eps), atol=1e-5)

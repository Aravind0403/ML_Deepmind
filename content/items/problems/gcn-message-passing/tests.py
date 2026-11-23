import numpy as np

def test_gcn_simple_chain(user_mod):
    A = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=float)
    X = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    W = np.eye(2)
    out = user_mod.gcn_layer(A, X, W)
    assert out.shape == (3, 2)
    assert np.all(out >= 0.0)
    # Node 0 has deg_tilde=2, node 1 has deg_tilde=3 -> entry (0,0) = 1/2
    np.testing.assert_allclose(out[0, 0], 0.5, atol=1e-6)
    np.testing.assert_allclose(out[0, 1], 1.0 / np.sqrt(6.0), atol=1e-6)

import numpy as np

def test_outlier_isolation_and_zero_row(user_mod):
    W = np.array([
        [0.01, -0.02, 0.03, 0.04],
        [100.0, -50.0, 25.0, 0.0],
        [0.0, 0.0, 0.0, 0.0],
    ], dtype=np.float32)
    q, scales, w_deq = user_mod.quantize_per_channel_int8(W)
    assert q.dtype == np.int8
    assert scales.shape == (3, 1)
    # Row 0 should retain high precision despite row 1's 100.0 outlier
    np.testing.assert_allclose(w_deq[0], W[0], atol=5e-4)
    np.testing.assert_allclose(w_deq[1], W[1], atol=1.0)
    np.testing.assert_allclose(w_deq[2], np.zeros(4), atol=1e-7)

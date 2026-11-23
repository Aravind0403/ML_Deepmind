import numpy as np
import pytest

def test_square_exact_tile(user_mod):
    rng = np.random.default_rng(0)
    A = rng.standard_normal((16, 16))
    B = rng.standard_normal((16, 16))
    out = user_mod.tiled_gemm(A, B, tile_size=8)
    np.testing.assert_allclose(out, A @ B, rtol=1e-5, atol=1e-6)

def test_non_multiple_rectangular(user_mod):
    rng = np.random.default_rng(42)
    A = rng.standard_normal((19, 13))
    B = rng.standard_normal((13, 23))
    out = user_mod.tiled_gemm(A, B, tile_size=4)
    np.testing.assert_allclose(out, A @ B, rtol=1e-5, atol=1e-6)

def test_shape_mismatch_raises(user_mod):
    A = np.ones((4, 5))
    B = np.ones((6, 3))
    with pytest.raises(ValueError):
        user_mod.tiled_gemm(A, B, tile_size=2)

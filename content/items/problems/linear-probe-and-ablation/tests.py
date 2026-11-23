import numpy as np
import pytest

def test_erasure_orthogonality_and_idempotence(user_mod):
    rng = np.random.default_rng(99)
    H = rng.standard_normal((20, 8))
    v = rng.standard_normal(8)
    He = user_mod.erase_concept_direction(H, v)
    # Projection onto v must be zero
    np.testing.assert_allclose(He @ v, np.zeros(20), atol=1e-6)
    # Idempotence: erasing twice equals erasing once
    He2 = user_mod.erase_concept_direction(He, v)
    np.testing.assert_allclose(He2, He, atol=1e-6)

def test_zero_vector_raises(user_mod):
    with pytest.raises(ValueError):
        user_mod.erase_concept_direction(np.ones((4, 3)), np.zeros(3))

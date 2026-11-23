import numpy as np

def test_no_nan_on_large_fp16_logits(user_mod):
    rng = np.random.default_rng(55)
    Q = (rng.standard_normal((8, 16)) * 6.0).astype(np.float16)
    K = (rng.standard_normal((8, 16)) * 6.0).astype(np.float16)
    V = rng.standard_normal((8, 16)).astype(np.float16)
    out = user_mod.stable_causal_attention_fp16(Q, K, V)
    assert out.dtype == np.float16
    assert np.all(np.isfinite(out)), "Output contains NaN or Inf!"

def test_strict_causality(user_mod):
    rng = np.random.default_rng(88)
    Q = rng.standard_normal((6, 8)).astype(np.float16)
    K = rng.standard_normal((6, 8)).astype(np.float16)
    V = rng.standard_normal((6, 8)).astype(np.float16)
    out1 = user_mod.stable_causal_attention_fp16(Q, K, V)
    K2 = K.copy(); V2 = V.copy()
    K2[-1] += np.float16(20.0); V2[-1] += np.float16(20.0)
    out2 = user_mod.stable_causal_attention_fp16(Q, K2, V2)
    np.testing.assert_allclose(out1[:-1].astype(np.float32), out2[:-1].astype(np.float32), atol=1e-3)

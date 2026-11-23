# Authentic ML Debugging Arena — Bug Hunt #2

A mixed-precision (`float16`) attention kernel returns **`NaN`** on large logits AND leaks future tokens!

Inspect `stable_causal_attention_fp16(Q, K, V)` (`Q, K, V` are `np.float16` of shape `(T, D)`):
1. **Bug 1 (Mask Direction):** `np.tril(..., k=-1)` masks the *past* instead of the *future* (`np.triu(..., k=1)`).
2. **Bug 2 (FP16 Overflow):** Computing `np.exp(scores)` directly in `float16` overflows to `inf` whenever a logit exceeds ~11.0 (`exp(12) > 65504`), turning `inf / inf` into `NaN`!
3. **Bug 3 (Missing Scale):** Forgets to divide by $\sqrt{D}$.

**Fix all three bugs** by upcasting softmax accumulation to `float32`, subtracting row max before `exp`, applying the upper-triangular causal mask (`-1e9` in `float32`), and casting the final output cleanly back to `float16`.

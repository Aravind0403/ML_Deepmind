# Authentic ML Debugging Arena — Bug Hunt #3 (Inspired by vLLM Issue #40004 / PR #45558)

In `schedule_iteration(running, waiting, token_budget)`:
- `running`: list of dicts `{"id": str, "remaining_decode": int}` (each active decode needs **1 token** of compute budget this step).
- `waiting`: list of dicts `{"id": str, "prompt_tokens": int}` (each waiting prefill needs `prompt_tokens` of compute budget, or can be **chunked** down to remaining budget if > 0!).
- `token_budget`: total compute tokens allowed in this GPU iteration.

### The Production Bug
The buggy scheduler admits `waiting` prefills **BEFORE** reserving 1 token for every active `running` decode request! When a large prompt arrives, it eats the entire `token_budget`, starving active decodes and spiking **TPOT (Time Per Output Token)**!

### Your Fix
Enforce the **vLLM V1 Decode-First Phase Separation Invariant**:
1. Reserve 1 token for every `running` request first (up to `token_budget`).
2. Spend only the **leftover budget** on `waiting` prefills (chunking a prompt if leftover budget `< prompt_tokens`, reducing its remaining `prompt_tokens` instead of dropping it, and moving it to `admitted_prefills` with `chunk_tokens`).
3. Return `{"scheduled_decodes": [...ids], "scheduled_prefills": [(id, chunk_tokens), ...], "budget_used": int}`.

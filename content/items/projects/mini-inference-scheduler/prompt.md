# Capstone Project: Mini Continuous-Batching LLM Scheduler

Build a working iteration-level inference scheduler `ContinuousBatchScheduler(max_kv_tokens: int, max_batch_size: int)`:
- `add_request(req_id: str, prompt_len: int, max_new_tokens: int) -> None`: Adds a waiting request to FIFO queue.
- `step() -> dict`: Executes **one engine iteration**:
  1. **Running Decode:** Each currently running request generates 1 token (increasing its `kv_used` by 1 and `generated` by 1). If total KV across running requests exceeds `max_kv_tokens`, **preempt** the most recently admitted running request back to the front of the waiting queue (freeing its KV and resetting `generated = 0`) until KV fits!
  2. **Admit Waiting Requests:** While `len(running) < max_batch_size` and waiting queue is non-empty, admit the next request if `total_kv + req.prompt_len <= max_kv_tokens` (Prefill consumes `prompt_len` KV tokens immediately).
  3. **Evict Finished:** Any running request with `generated >= max_new_tokens` is moved to `finished` and its KV is freed.
  4. Return `{"running": [...ids], "finished_this_step": [...ids], "kv_used": int, "waiting": int}`.

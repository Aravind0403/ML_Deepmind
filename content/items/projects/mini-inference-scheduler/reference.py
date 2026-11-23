from collections import deque

class ContinuousBatchScheduler:
    def __init__(self, max_kv_tokens: int, max_batch_size: int):
        self.max_kv_tokens = max_kv_tokens
        self.max_batch_size = max_batch_size
        self.waiting = deque()
        self.running: list[dict] = []

    def add_request(self, req_id: str, prompt_len: int, max_new_tokens: int) -> None:
        self.waiting.append({
            "id": req_id,
            "prompt_len": prompt_len,
            "max_new_tokens": max_new_tokens,
            "generated": 0,
            "kv": 0,
        })

    def _kv_used(self) -> int:
        return sum(r["kv"] for r in self.running)

    def step(self) -> dict:
        # 1. Decode step for currently running requests
        for r in self.running:
            r["generated"] += 1
            r["kv"] += 1

        # Preempt newest running requests if KV budget exceeded
        while self._kv_used() > self.max_kv_tokens and self.running:
            victim = self.running.pop()
            victim["generated"] = 0
            victim["kv"] = 0
            self.waiting.appendleft(victim)

        # 2. Evict completed requests before admitting new ones (or after decode)
        finished_now = []
        still_running = []
        for r in self.running:
            if r["generated"] >= r["max_new_tokens"]:
                finished_now.append(r["id"])
            else:
                still_running.append(r)
        self.running = still_running

        # 3. Admit waiting requests (prefill)
        while self.waiting and len(self.running) < self.max_batch_size:
            nxt = self.waiting[0]
            if self._kv_used() + nxt["prompt_len"] <= self.max_kv_tokens:
                self.waiting.popleft()
                nxt["kv"] = nxt["prompt_len"]
                nxt["generated"] = 0
                self.running.append(nxt)
            else:
                break

        return {
            "running": [r["id"] for r in self.running],
            "finished_this_step": finished_now,
            "kv_used": self._kv_used(),
            "waiting": len(self.waiting),
        }

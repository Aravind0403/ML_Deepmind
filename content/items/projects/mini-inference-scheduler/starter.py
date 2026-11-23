from collections import deque

class ContinuousBatchScheduler:
    def __init__(self, max_kv_tokens: int, max_batch_size: int):
        raise NotImplementedError

    def add_request(self, req_id: str, prompt_len: int, max_new_tokens: int) -> None:
        raise NotImplementedError

    def step(self) -> dict:
        raise NotImplementedError

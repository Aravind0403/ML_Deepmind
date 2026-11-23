import math

class BlockManager:
    def __init__(self, num_blocks: int, block_size: int):
        raise NotImplementedError

    def num_free_blocks(self) -> int:
        raise NotImplementedError

    def allocate_seq(self, seq_id: str, num_tokens: int) -> list[int]:
        raise NotImplementedError

    def fork_seq(self, src_seq_id: str, dst_seq_id: str) -> None:
        raise NotImplementedError

    def append_token(self, seq_id: str) -> int:
        raise NotImplementedError

    def free_seq(self, seq_id: str) -> None:
        raise NotImplementedError

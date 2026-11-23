import pytest

def test_cow_fork_and_free(user_mod):
    bm = user_mod.BlockManager(num_blocks=6, block_size=4)
    b_src = bm.allocate_seq("s1", 6)  # uses 2 blocks (2nd block half full)
    assert len(b_src) == 2
    assert bm.num_free_blocks() == 4

    bm.fork_seq("s1", "s2")  # zero new blocks!
    assert bm.num_free_blocks() == 4

    # Appending to s2 triggers Copy-on-Write on the shared partial block
    cow_bid = bm.append_token("s2")
    assert cow_bid != b_src[-1]
    assert bm.num_free_blocks() == 3

    # Freeing s1 releases only blocks whose ref_count hits 0 (s2 still holds b_src[0])
    bm.free_seq("s1")
    assert bm.num_free_blocks() == 4

    bm.free_seq("s2")
    assert bm.num_free_blocks() == 6

def test_oom_raises(user_mod):
    bm = user_mod.BlockManager(num_blocks=2, block_size=4)
    with pytest.raises(MemoryError):
        bm.allocate_seq("big", 12)

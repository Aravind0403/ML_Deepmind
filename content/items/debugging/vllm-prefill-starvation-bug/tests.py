def test_decodes_never_starved_by_large_prefill(user_mod):
    running = [{"id": "d1", "remaining_decode": 10}, {"id": "d2", "remaining_decode": 5}, {"id": "d3", "remaining_decode": 8}]
    waiting = [{"id": "p_huge", "prompt_tokens": 512}]
    out = user_mod.schedule_iteration(running, waiting, token_budget=64)
    # All 3 running decodes MUST be scheduled
    assert out["scheduled_decodes"] == ["d1", "d2", "d3"]
    # Remaining 61 tokens go to chunked prefill of p_huge!
    assert out["scheduled_prefills"] == [("p_huge", 61)]
    assert out["budget_used"] == 64

def test_multiple_prefills_fit_after_decodes(user_mod):
    running = [{"id": "d1", "remaining_decode": 4}]
    waiting = [{"id": "p1", "prompt_tokens": 10}, {"id": "p2", "prompt_tokens": 20}]
    out = user_mod.schedule_iteration(running, waiting, token_budget=25)
    assert out["scheduled_decodes"] == ["d1"]
    assert out["scheduled_prefills"] == [("p1", 10), ("p2", 14)]
    assert out["budget_used"] == 25

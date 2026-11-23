def test_milestone_1_admission_and_budget(user_mod):
    s = user_mod.ContinuousBatchScheduler(max_kv_tokens=20, max_batch_size=2)
    s.add_request("r1", prompt_len=12, max_new_tokens=2)
    s.add_request("r2", prompt_len=10, max_new_tokens=2)
    st = s.step()
    assert st["running"] == ["r1"]
    assert st["kv_used"] == 12
    assert st["waiting"] == 1

def test_milestone_2_eviction_and_continuous_refill(user_mod):
    s = user_mod.ContinuousBatchScheduler(max_kv_tokens=20, max_batch_size=2)
    s.add_request("r1", prompt_len=12, max_new_tokens=2)
    s.add_request("r2", prompt_len=10, max_new_tokens=1)
    s.step()  # admit r1 (kv=12)
    st2 = s.step()  # r1 gen=1, kv=13
    assert st2["running"] == ["r1"]
    st3 = s.step()  # r1 gen=2 -> finished & evicted, r2 admitted!
    assert "r1" in st3["finished_this_step"]
    assert "r2" in st3["running"]

def test_milestone_3_preemption_under_pressure(user_mod):
    s = user_mod.ContinuousBatchScheduler(max_kv_tokens=10, max_batch_size=2)
    s.add_request("r1", prompt_len=5, max_new_tokens=3)
    s.add_request("r2", prompt_len=5, max_new_tokens=3)
    st1 = s.step()  # both admitted, kv=10
    assert st1["kv_used"] == 10
    st2 = s.step()  # decode would need 12 > 10 -> r2 preempted!
    assert st2["kv_used"] <= 10
    assert st2["running"] == ["r1"]
    assert st2["waiting"] == 1

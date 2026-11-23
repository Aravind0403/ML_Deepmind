import numpy as np

def test_grpo_on_policy_zero_kl(user_mod):
    r = np.array([1.0, 0.0, 1.0, 0.0])
    lp = np.array([-2.0, -3.0, -2.5, -1.5])
    # On-policy (logp_new == logp_old == logp_ref): ratio=1, kl=0, mean(adv)=0 -> loss=0
    loss = user_mod.grpo_loss(r, lp, lp, lp)
    np.testing.assert_allclose(loss, 0.0, atol=1e-6)

def test_grpo_rewards_increasing_good_rollout(user_mod):
    r = np.array([1.0, 0.0, 0.0, 0.0])
    lo = np.array([-2.0, -2.0, -2.0, -2.0])
    ln_better = np.array([-1.85, -2.0, -2.0, -2.0])
    loss_better = user_mod.grpo_loss(r, ln_better, lo, lo, beta=0.01)
    assert loss_better < 0.0

## Why GRPO Scales Reasoning RL

By normalizing rewards within a group of $G$ rollouts sampled for the *same* prompt, GRPO removes the learned critic network (cutting ~50% of training memory in PPO) while using the non-negative $k_3$ KL estimator $\exp(\Delta) - \Delta - 1 \ge 0$.

# Elastic Weight Consolidation (EWC)

To mitigate catastrophic forgetting when training on Task B after Task A, EWC adds a quadratic anchor weighted by Task A's diagonal Fisher Information $F$:
$$L_{\text{EWC}}(\theta) = \frac{\lambda}{2} \sum_i F_i (\theta_i - \theta^*_{A,i})^2$$

Implement `ewc_penalty_and_grad(theta, theta_star, fisher, lam)` returning `(penalty: float, grad: np.ndarray)` where `grad` is $\nabla_\theta L_{\text{EWC}}(\theta)$.

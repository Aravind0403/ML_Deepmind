## Relative Position Property of RoPE

Because 2D rotation matrices satisfy $R(m\theta)^\top R(n\theta) = R((n-m)\theta)$, the dot product between rotated queries and keys depends **only on relative distance $(n-m)$** while preserving vector norms $\|R(m\theta)x\|_2 = \|x\|_2$.

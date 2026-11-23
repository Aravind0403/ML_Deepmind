# Invent a Typical-Value Estimator

You are given a list of numbers `xs` representing incomes of people in a cafe.
Write **any** Python function `typical_value(xs: list[float]) -> float` that returns one representative number for the group.

No formula is given. Your function will be attacked by adversarial counterexamples using your own outputs:
1. **Constant consensus**: If everyone earns `$c`, you must return `c`.
2. **Shift equivariance**: If everyone gets a `+$10` raise, your estimate must rise by `$10`.
3. **Scale equivariance**: If incomes double, your estimate must double.
4. **Billionaire attack (Breakdown Point)**: If 1 out of 9 people becomes a billionaire (`1e9`), your estimate must NOT jump by more than 20%.

# Real-Dataset Lab: Surviving Extreme Multicollinearity

You are given a strongly collinear regression dataset `(X_train, y_train, X_val)` (40 correlated features, 200 training samples, heavy feature collinearity where unregularized OLS explodes with validation RMSE > 4.0).

Implement `fit_predict(X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray) -> np.ndarray`:
- Standardize features cleanly (using **training statistics only** — no data leakage!).
- Select an L2 penalty $\lambda$ (via closed-form Ridge + K-fold CV or GCV) and solve the regularized normal equations / SVD cleanly.
- **Target Metric:** Validation `RMSE <= 0.85` on the hidden held-out test set.

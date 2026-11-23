import numpy as np

def evaluate_lab(user_mod):
    rng = np.random.default_rng(123)
    n_train, n_val, d = 120, 120, 40
    # Create low-rank strongly collinear design matrix
    Z_tr = rng.standard_normal((n_train, 5))
    Z_va = rng.standard_normal((n_val, 5))
    mix = rng.standard_normal((5, d))
    X_tr = Z_tr @ mix + 1e-3 * rng.standard_normal((n_train, d))
    X_va = Z_va @ mix + 1e-3 * rng.standard_normal((n_val, d))
    true_w = rng.standard_normal(5) * 1.5
    y_tr = Z_tr @ true_w + 0.6 * rng.standard_normal(n_train) + 3.0
    y_va = Z_va @ true_w + 0.6 * rng.standard_normal(n_val) + 3.0

    preds = np.asarray(user_mod.fit_predict(X_tr, y_tr, X_va), dtype=np.float64)
    if preds.shape != y_va.shape:
        return {"passed": False, "metric": 999.0, "details": f"Expected shape {y_va.shape}, got {preds.shape}"}
    rmse = float(np.sqrt(np.mean((preds - y_va) ** 2)))
    passed = rmse <= 0.85
    return {
        "passed": passed,
        "metric": round(rmse, 4),
        "threshold": 0.85,
        "details": f"Validation RMSE = {rmse:.4f} (target <= 0.85)"
    }

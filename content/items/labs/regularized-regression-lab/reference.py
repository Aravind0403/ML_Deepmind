import numpy as np

def fit_predict(X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray) -> np.ndarray:
    mu = X_train.mean(axis=0, keepdims=True)
    sd = X_train.std(axis=0, keepdims=True) + 1e-8
    Xtr = (X_train - mu) / sd
    Xva = (X_val - mu) / sd
    y_mean = y_train.mean()
    ytr = y_train - y_mean

    n, d = Xtr.shape
    folds = 5
    idx = np.arange(n)
    best_lam, best_mse = 1.0, float("inf")
    for lam in np.logspace(-3, 3, 25):
        mses = []
        for f in range(folds):
            va_mask = (idx % folds) == f
            tr_mask = ~va_mask
            Xf, yf = Xtr[tr_mask], ytr[tr_mask]
            w = np.linalg.solve(Xf.T @ Xf + lam * np.eye(d), Xf.T @ yf)
            pred = Xtr[va_mask] @ w
            mses.append(np.mean((pred - ytr[va_mask]) ** 2))
        m = float(np.mean(mses))
        if m < best_mse:
            best_mse, best_lam = m, float(lam)

    w_final = np.linalg.solve(Xtr.T @ Xtr + best_lam * np.eye(d), Xtr.T @ ytr)
    return Xva @ w_final + y_mean

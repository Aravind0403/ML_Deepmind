import numpy as np

def fit_predict(X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray) -> np.ndarray:
    # Naive OLS blows up under collinearity — replace with standardized Ridge + CV
    w, *_ = np.linalg.lstsq(X_train, y_train, rcond=None)
    return X_val @ w

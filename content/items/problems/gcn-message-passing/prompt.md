# Kipf & Welling Graph Convolutional Layer

Implement `gcn_layer(A: np.ndarray, X: np.ndarray, W: np.ndarray) -> np.ndarray`:
1. Add self-loops: $\tilde{A} = A + I_N$.
2. Compute symmetric degree normalization: $\hat{A} = \tilde{D}^{-1/2} \tilde{A} \tilde{D}^{-1/2}$ where $\tilde{D}_{ii} = \sum_j \tilde{A}_{ij}$.
3. Propagate and apply ReLU: $H = \mathrm{ReLU}(\hat{A} X W)$.

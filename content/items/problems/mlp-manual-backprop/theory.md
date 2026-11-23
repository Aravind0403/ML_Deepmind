## Analytical Matrix Gradients

With $d\hat{Y} = \frac{2}{N D_{\text{out}}} (\hat{Y} - Y)$:
- $dW_2 = A_1^\top d\hat{Y}$, $db_2 = \sum_n d\hat{Y}_n$
- $dA_1 = d\hat{Y} W_2^\top$, $dZ_1 = dA_1 \odot \mathbb{1}[Z_1 > 0]$
- $dW_1 = X^\top dZ_1$, $db_1 = \sum_n dZ_{1,n}$

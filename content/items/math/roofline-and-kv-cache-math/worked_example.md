# Worked Example: Sizing KV-Cache & Roofline Ridge Point

For a Transformer with $L$ layers, $H_{kv}$ KV heads (GQA), head dimension $d_h$, precision $b$ bytes/element, sequence length $S$, and batch size $B$:
$$\text{KV Bytes} = 2 \cdot L \cdot H_{kv} \cdot d_h \cdot b \cdot S \cdot B$$
*(The factor of $2$ accounts for both Keys and Values.)*

On an accelerator with peak compute $F_{\text{peak}}$ (FLOP/s) and HBM bandwidth $BW$ (bytes/s), the **Roofline Ridge Point** is:
$$I_{\text{ridge}} = \frac{F_{\text{peak}}}{BW} \quad [\text{FLOP/byte}]$$
An operation with arithmetic intensity $I < I_{\text{ridge}}$ is **memory-bandwidth bound**; $I > I_{\text{ridge}}$ is **compute bound**.

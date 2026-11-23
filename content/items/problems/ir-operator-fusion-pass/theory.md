## Why Epilogue Fusion Eliminates HBM Round-Trips

In `torch.compile` (Inductor) and XLA, fusing `matmul -> bias_add -> gelu` keeps the intermediate tensor in GPU registers instead of writing and re-reading tens of megabytes to HBM between separate kernel launches.

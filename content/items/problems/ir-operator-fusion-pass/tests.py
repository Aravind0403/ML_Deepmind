def test_matmul_epilogue_fusion(user_mod):
    graph = [
        {"id": "x", "op": "input", "inputs": [], "kind": "io"},
        {"id": "mm", "op": "matmul", "inputs": ["x"], "kind": "compute"},
        {"id": "add", "op": "bias_add", "inputs": ["mm"], "kind": "elementwise"},
        {"id": "gelu", "op": "gelu", "inputs": ["add"], "kind": "elementwise"},
        {"id": "mm2", "op": "matmul", "inputs": ["gelu"], "kind": "compute"},
    ]
    groups = user_mod.fuse_elementwise_chains(graph)
    assert groups == [["x"], ["mm", "add", "gelu"], ["mm2"]]

def test_branching_stops_fusion(user_mod):
    graph = [
        {"id": "mm", "op": "matmul", "inputs": [], "kind": "compute"},
        {"id": "r1", "op": "relu", "inputs": ["mm"], "kind": "elementwise"},
        {"id": "r2", "op": "sigmoid", "inputs": ["mm"], "kind": "elementwise"},
    ]
    groups = user_mod.fuse_elementwise_chains(graph)
    # mm has fan-out 2 -> cannot fuse exclusively into r1 or r2
    assert groups == [["mm"], ["r1"], ["r2"]]

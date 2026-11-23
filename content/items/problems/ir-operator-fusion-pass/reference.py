def fuse_elementwise_chains(nodes: list[dict]) -> list[list[str]]:
    consumers: dict[str, list[str]] = {n["id"]: [] for n in nodes}
    node_map = {n["id"]: n for n in nodes}
    for n in nodes:
        for inp in n.get("inputs", []):
            if inp in consumers:
                consumers[inp].append(n["id"])

    visited = set()
    groups: list[list[str]] = []

    for n in nodes:
        nid = n["id"]
        if nid in visited:
            continue
        kind = n["kind"]
        if kind == "io":
            visited.add(nid)
            groups.append([nid])
            continue
        # Start a group from compute or elementwise
        group = [nid]
        visited.add(nid)
        cur = nid
        while len(consumers[cur]) == 1:
            nxt_id = consumers[cur][0]
            nxt = node_map[nxt_id]
            if nxt_id in visited or nxt["kind"] != "elementwise":
                break
            # Only fuse if all non-io/graph inputs of nxt are already in this group or not a second unfused compute branch
            group.append(nxt_id)
            visited.add(nxt_id)
            cur = nxt_id
        groups.append(group)
    return groups

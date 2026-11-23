def schedule_iteration(running: list[dict], waiting: list[dict], token_budget: int) -> dict:
    used = 0
    decodes = []
    prefills = []
    # 1. Decode-first invariant: guarantee active running requests never starve
    for req in running:
        if used + 1 <= token_budget:
            decodes.append(req["id"])
            used += 1
    # 2. Pack remaining budget with chunked prefills
    for req in waiting:
        rem = token_budget - used
        if rem <= 0:
            break
        chunk = min(req["prompt_tokens"], rem)
        if chunk > 0:
            prefills.append((req["id"], chunk))
            used += chunk
    return {"scheduled_decodes": decodes, "scheduled_prefills": prefills, "budget_used": used}

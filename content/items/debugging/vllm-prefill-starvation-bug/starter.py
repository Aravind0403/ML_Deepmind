def schedule_iteration(running: list[dict], waiting: list[dict], token_budget: int) -> dict:
    # BUG: Schedules waiting prefills first -> starves active decodes!
    used = 0
    prefills = []
    decodes = []
    for req in waiting:
        need = req["prompt_tokens"]
        if used + need <= token_budget:
            prefills.append((req["id"], need))
            used += need
    for req in running:
        if used + 1 <= token_budget:
            decodes.append(req["id"])
            used += 1
    return {"scheduled_decodes": decodes, "scheduled_prefills": prefills, "budget_used": used}

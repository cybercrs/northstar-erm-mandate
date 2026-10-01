from northstar.board_case import REQUESTS
from northstar.board_progress import check_commission, check_roles, commit, defaults, submit_brief


def complete_state(mandate=0, tracker=0, ownership=0, scope=0, provider=0):
    state = defaults(1234)
    state["c"]["roles"] = [request["category"] for request in REQUESTS]
    state = check_roles(state)
    state = commit(state, 1)
    state["c"].update({"mandate": mandate, "tracker": tracker, "ownership": ownership})
    state = check_commission(state)
    state = commit(state, 2)
    state = commit(state, 3)
    state["c"].update({
        "citations": [0, 1, 2, 3, 6, 7],
        "network_tenths": 977,
        "headline": 1,
        "continuity": 1,
        "work_claim": 0,
        "communication": 0,
        "authority": 0,
        "scope": scope,
        "provider": provider,
    })
    state = submit_brief(state)
    return state

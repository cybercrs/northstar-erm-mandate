"""Anonymous, bounded URL progress for the board-briefing activity."""

import base64
from copy import deepcopy
import json
import re
import secrets
import zlib

from .board_case import BRIEF_FIELDS, BRIEF_OPTIONS, MANDATES, RECORDS, REQUESTS
from .board_logic import ready

VERSION = 5
MAX_TOKEN = 6000
MAX_BYTES = 16000
FIRST_FIELDS = ("mandate", "tracker", "ownership") + BRIEF_FIELDS + ("citations",)
SIMPLE_FIELDS = ("mandate", "tracker", "ownership") + BRIEF_FIELDS


class SnapshotError(ValueError):
    pass


def defaults(seed: int | None = None) -> dict:
    return {
        "v": VERSION,
        "seed": secrets.randbits(31) if seed is None else seed,
        "stage": 0,
        "committed": [],
        "roles_checked": False,
        "commission_checked": False,
        "brief_submitted": False,
        "first_brief": None,
        "c": {
            "roles": [-1] * len(REQUESTS),
            "mandate": -1,
            "tracker": -1,
            "ownership": -1,
            "citations": [],
            **{field: -1 for field in BRIEF_FIELDS},
        },
    }


def strict_int(value, lo: int, hi: int) -> bool:
    return type(value) is int and lo <= value <= hi


def validate_choices(c: dict) -> None:
    if type(c) is not dict or set(c) != set(defaults(0)["c"]):
        raise SnapshotError("Unknown or missing decisions.")
    roles = c["roles"]
    if type(roles) is not list or len(roles) != len(REQUESTS) or any(not strict_int(v, -1, 2) for v in roles):
        raise SnapshotError("Invalid request triage.")
    if type(c["mandate"]) is not int or c["mandate"] not in (-1, *MANDATES):
        raise SnapshotError("Invalid mandate.")
    for field in ("tracker", "ownership"):
        if type(c[field]) is not int or c[field] not in (-1, 0, 1, 2):
            raise SnapshotError("Invalid agreement.")
    for field in BRIEF_FIELDS:
        if field == "network_tenths":
            if not strict_int(c[field], -1, 1000):
                raise SnapshotError("Invalid delivery figure.")
            continue
        if field == "work_claim":
            if type(c[field]) is not int or c[field] not in (-1, 0, 1, 2):
                raise SnapshotError("Invalid work-product claim.")
            continue
        if type(c[field]) is not int or c[field] not in (-1, *BRIEF_OPTIONS[field]):
            raise SnapshotError("Invalid briefing decision.")
    citations = c["citations"]
    if type(citations) is not list or len(citations) > len(RECORDS) or citations != sorted(set(citations)):
        raise SnapshotError("Invalid record list.")
    if any(type(v) is not int or v not in RECORDS for v in citations):
        raise SnapshotError("Unknown record.")


def validate(state: dict) -> dict:
    if type(state) is not dict or set(state) != set(defaults(0)):
        raise SnapshotError("Unsupported progress link.")
    if type(state["v"]) is not int or state["v"] != VERSION:
        raise SnapshotError("Incompatible progress version.")
    if not strict_int(state["seed"], 0, 2**31 - 1) or not strict_int(state["stage"], 0, 5):
        raise SnapshotError("Invalid navigation.")
    if any(type(state[field]) is not bool for field in ("roles_checked", "commission_checked", "brief_submitted")):
        raise SnapshotError("Invalid review state.")
    validate_choices(state["c"])
    committed = state["committed"]
    if (
        type(committed) is not list
        or len(committed) > 4
        or any(type(v) is not int for v in committed)
        or committed != list(range(1, len(committed) + 1))
    ):
        raise SnapshotError("Stages must be completed in order.")
    if state["stage"] > len(committed) + 1 or any(not ready(state, step) for step in committed):
        raise SnapshotError("Saved stage skips unfinished work.")
    if state["roles_checked"] and any(v == -1 for v in state["c"]["roles"]):
        raise SnapshotError("Incomplete checked triage.")
    if state["commission_checked"] and any(state["c"][field] == -1 for field in ("mandate", "tracker", "ownership")):
        raise SnapshotError("Incomplete checked commission.")
    if state["brief_submitted"] and not (
        0 <= state["c"]["network_tenths"] <= 1000
        and state["c"]["work_claim"] in (0, 1, 2)
        and all(state["c"][field] in BRIEF_OPTIONS[field] for field in BRIEF_FIELDS if field not in ("network_tenths", "work_claim"))
        and state["c"]["citations"]
    ):
        raise SnapshotError("Incomplete submitted briefing.")
    first = state["first_brief"]
    if first is not None:
        if type(first) is not dict or set(first) != set(FIRST_FIELDS):
            raise SnapshotError("Invalid initial briefing.")
        candidate = deepcopy(state["c"])
        candidate.update(first)
        validate_choices(candidate)
        if not candidate["citations"] or any(candidate[field] == -1 for field in BRIEF_FIELDS):
            raise SnapshotError("Incomplete initial briefing.")
    if state["brief_submitted"] and first is None:
        raise SnapshotError("Initial briefing is missing.")
    if (4 in committed) != state["brief_submitted"]:
        raise SnapshotError("Briefing review state is inconsistent.")
    if state["stage"] == 4 and committed not in ([1, 2, 3], [1, 2, 3, 4]):
        raise SnapshotError("Board briefing opened too early.")
    if state["stage"] == 5 and (committed != [1, 2, 3, 4] or not state["brief_submitted"]):
        raise SnapshotError("Feedback opened before a briefing was submitted.")
    return deepcopy(state)


def encode(state: dict) -> str:
    payload = json.dumps(validate(state), separators=(",", ":"), sort_keys=True).encode()
    token = base64.urlsafe_b64encode(zlib.compress(payload)).decode().rstrip("=")
    if len(token) > MAX_TOKEN:
        raise SnapshotError("Progress link is too large.")
    return token


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise SnapshotError("Duplicate saved field.")
        result[key] = value
    return result


def decode(token: str) -> dict:
    try:
        if type(token) is not str or not 1 <= len(token) <= MAX_TOKEN or not re.fullmatch(r"[A-Za-z0-9_-]+", token):
            raise SnapshotError("Invalid progress link.")
        raw = base64.b64decode(token + "=" * (-len(token) % 4), altchars=b"-_", validate=True)
        inflater = zlib.decompressobj()
        payload = inflater.decompress(raw, MAX_BYTES + 1)
        if len(payload) > MAX_BYTES or inflater.unconsumed_tail or inflater.unused_data or not inflater.eof:
            raise SnapshotError("Invalid or oversized payload.")
        return validate(json.loads(payload, object_pairs_hook=unique_object))
    except (ValueError, TypeError, KeyError, zlib.error, UnicodeError, RecursionError) as error:
        raise SnapshotError("The saved progress could not be restored safely.") from error


def navigate(state: dict, stage: int) -> dict:
    result = deepcopy(state)
    if type(stage) is not int or not 0 <= stage <= min(5, len(result["committed"]) + 1):
        raise SnapshotError("That section is not available yet.")
    result["stage"] = stage
    return validate(result)


def check_roles(state: dict) -> dict:
    result = deepcopy(state)
    if any(value == -1 for value in result["c"]["roles"]):
        raise SnapshotError("Classify every request first.")
    result["roles_checked"] = True
    return validate(result)


def check_commission(state: dict) -> dict:
    result = deepcopy(state)
    if result["stage"] != 2 or any(result["c"][field] == -1 for field in ("mandate", "tracker", "ownership")):
        raise SnapshotError("Complete the commission decisions first.")
    result["commission_checked"] = True
    return validate(result)


def submit_brief(state: dict) -> dict:
    result = deepcopy(state)
    if result["stage"] != 4 or not result["c"]["citations"] or any(result["c"][field] == -1 for field in BRIEF_FIELDS):
        raise SnapshotError("Complete and cite the board briefing first.")
    result["brief_submitted"] = True
    if result["first_brief"] is None:
        result["first_brief"] = {field: deepcopy(result["c"][field]) for field in FIRST_FIELDS}
    result["committed"] = [1, 2, 3, 4]
    result["stage"] = 5
    return validate(result)


def commit(state: dict, stage: int) -> dict:
    result = deepcopy(state)
    if stage not in (1, 2, 3) or stage > len(result["committed"]) + 1 or not ready(result, stage):
        raise SnapshotError("Complete this section before continuing.")
    result["committed"] = list(range(1, stage + 1))
    result["stage"] = stage + 1
    return validate(result)


def edit_choice(state: dict, field: str, value, role_index: int | None = None) -> dict:
    result = deepcopy(state)
    if field == "roles":
        if role_index is None or not 0 <= role_index < len(REQUESTS) or value not in (0, 1, 2):
            raise SnapshotError("Invalid request decision.")
        result["c"]["roles"][role_index] = value
        result["roles_checked"] = False
        result["commission_checked"] = False
        result["brief_submitted"] = False
        changed_stage = 1
    else:
        if field not in SIMPLE_FIELDS + ("citations",):
            raise SnapshotError("Unknown decision.")
        result["c"][field] = sorted(value) if field == "citations" else value
        changed_stage = 2 if field in ("mandate", "tracker", "ownership") else 4
        if changed_stage == 2:
            result["commission_checked"] = False
        result["brief_submitted"] = False
    result["committed"] = [step for step in result["committed"] if step < changed_stage]
    result["stage"] = min(result["stage"], changed_stage)
    return validate(result)

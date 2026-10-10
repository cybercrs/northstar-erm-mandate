"""A viewed page is separate from the existing validated lesson frontier."""

from copy import deepcopy
from northstar.board_progress import SnapshotError, validate

VIEW_KEY = "ns_browser_view"
VIEW_PARAM = "view"


def restore_view(state, raw):
    try:
        view = int(raw) if isinstance(raw, str) else -1
    except ValueError:
        view = -1
    return view if 0 <= view <= state["stage"] else state["stage"]


def move(state, view, direction):
    if type(direction) is not int or direction not in (-1, 1):
        raise SnapshotError("Direction must be Back or Forward.")
    return min(state["stage"], max(0, view + direction))


def resume_saved(state):
    """Earlier server bookmarks open in review of the furthest earned page."""
    result = deepcopy(state)
    if result["committed"]:
        result["stage"] = max(result["stage"], min(5, len(result["committed"]) + 1))
    return validate(result)


def require_current(state, view):
    if view != state["stage"]:
        raise SnapshotError("Earlier pages are view only.")


def revise(state, view):
    require_current(state, view)
    if state["stage"] != 5:
        raise SnapshotError("Submit the briefing before revising it.")
    result = deepcopy(state)
    result["stage"] = 4
    result["brief_submitted"] = False
    result["committed"] = [1, 2, 3]
    return validate(result)

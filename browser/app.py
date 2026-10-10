"""Browser driver; the live server source and its progress schema stay unchanged."""

from html import escape
from pathlib import Path
import runpy
import streamlit as st

from browser.navigation import (
    VIEW_KEY,
    VIEW_PARAM,
    move,
    require_current,
    restore_view,
    resume_saved,
    revise,
)
from northstar.board_case import STAGES
from northstar.board_progress import (
    SnapshotError,
    decode,
    defaults,
    encode,
    navigate,
    commit,
)

# Re-execute renderer declarations each rerun (no cached module or patched server).
app = runpy.run_path(str(Path(__file__).resolve().parents[1] / "board_app.py"))
g = app["main"].__globals__


def sync():
    token = encode(st.session_state.ns)
    if st.query_params.get("progress") != token:
        st.query_params["progress"] = token
    view = str(st.session_state[VIEW_KEY])
    if st.query_params.get(VIEW_PARAM) != view:
        st.query_params[VIEW_PARAM] = view


def use(updated, *, scroll=False):
    require_current(st.session_state.ns, st.session_state[VIEW_KEY])
    st.session_state.ns = updated
    st.session_state[VIEW_KEY] = updated["stage"]
    if scroll:
        st.session_state.ns_scroll = True
    sync()


def browse(target):
    if type(target) is int and 0 <= target <= st.session_state.ns["stage"]:
        st.session_state[VIEW_KEY] = target
        st.session_state.ns_scroll = True
        sync()


def arrow(direction):
    browse(move(st.session_state.ns, st.session_state[VIEW_KEY], direction))


def go(target):
    state = st.session_state.ns
    require_current(state, st.session_state[VIEW_KEY])
    if state["stage"] == 0 and target == 1:
        use(navigate(state, 1), scroll=True)
    elif state["stage"] == 5 and target == 4:
        use(revise(state, st.session_state[VIEW_KEY]), scroll=True)
    else:
        browse(target)


def advance(stage):
    require_current(st.session_state.ns, st.session_state[VIEW_KEY])
    if stage != st.session_state.ns["stage"]:
        raise SnapshotError("Continue from the current page.")
    use(commit(st.session_state.ns, stage), scroll=True)


def reset():
    require_current(st.session_state.ns, st.session_state[VIEW_KEY])
    st.session_state.ns = defaults()
    st.session_state[VIEW_KEY] = 0
    st.session_state.ns_notice = ""
    st.session_state.ns_scroll = True
    for key in list(st.session_state):
        if key.startswith("widget_"):
            del st.session_state[key]
    sync()


def guarded(callback):
    def action(*args, **kwargs):
        require_current(st.session_state.ns, st.session_state[VIEW_KEY])
        return callback(*args, **kwargs)

    return action


def navigation(stage, next_label):
    if st.session_state[VIEW_KEY] < st.session_state.ns["stage"]:
        return
    st.divider()
    st.button(
        next_label,
        type="primary",
        disabled=not app["ready"](st.session_state.ns, stage),
        on_click=advance,
        args=(stage,),
        width="stretch",
    )


class ReviewUI:
    """No mutations or newly requested feedback from earlier pages."""

    def __getattr__(self, name):
        return getattr(st, name)

    def button(self, *args, **kwargs):
        return False

    def frozen(self, name, *args, **kwargs):
        kwargs.update(disabled=True, on_change=None, args=None, kwargs=None)
        return getattr(st, name)(*args, **kwargs)

    def radio(self, *args, **kwargs):
        return self.frozen("radio", *args, **kwargs)

    def selectbox(self, *args, **kwargs):
        return self.frozen("selectbox", *args, **kwargs)

    def number_input(self, *args, **kwargs):
        return self.frozen("number_input", *args, **kwargs)

    def multiselect(self, *args, **kwargs):
        return self.frozen("multiselect", *args, **kwargs)


g.update(sync=sync, use=use, go=go, reset=reset, advance=advance, navigation=navigation)
for name in ("save", "check_inbox", "check_plan", "send_brief"):
    g[name] = guarded(app[name])

st.set_page_config(
    page_title="Northstar Cold Chain | The ERM Mandate",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed",
)
if "ns" not in st.session_state:
    try:
        values = st.query_params.get_all("progress")
        if len(values) > 1:
            raise SnapshotError("Multiple progress values.")
        saved = decode(values[0]) if values else defaults()
        saved_view = saved["stage"]
        st.session_state.ns = resume_saved(saved)
        raw_views = st.query_params.get_all(VIEW_PARAM)
        raw_view = (
            raw_views[0]
            if len(raw_views) == 1
            else str(saved_view)
            if not raw_views
            else None
        )
        st.session_state[VIEW_KEY] = restore_view(st.session_state.ns, raw_view)
        st.session_state.ns_notice = ""
    except SnapshotError:
        st.session_state.ns = defaults()
        st.session_state[VIEW_KEY] = 0
        st.session_state.ns_notice = (
            "This link could not restore your choices. A new case has started."
        )
    try:
        import json, sys
        from js import console
        import pyodide

        console.log(
            "BROWSER_VERSIONS="
            + json.dumps(
                {
                    "streamlit": st.__version__,
                    "python": sys.version.split()[0],
                    "pyodide": pyodide.__version__,
                    "iframe": hasattr(st, "iframe"),
                }
            )
        )
    except ImportError:
        pass

st.markdown(app["CSS"], unsafe_allow_html=True)
st.markdown(
    """<style>
.st-key-browser_navigation button {width:44px;height:44px;min-width:44px;min-height:44px;position:relative;padding:0;border:1px solid #C5CCD8;border-radius:6px;background:transparent;color:#59677A;box-shadow:none;}
.st-key-browser_navigation button::before {content:"";position:absolute;width:20px;height:20px;top:50%;left:50%;transform:translate(-50%,-50%);background:center / contain no-repeat url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%2359677A' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M19 12H5m0 0 7-7m-7 7 7 7'/%3E%3C/svg%3E");}
.st-key-browser_forward button::before {transform:translate(-50%,-50%) rotate(180deg);}
.st-key-browser_navigation button p {position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap;border:0;}
.st-key-browser_navigation button:hover:not(:disabled) {background:#E6EAF1;border-color:#A7B2C3;}
.st-key-browser_navigation button:focus-visible {outline:2px solid #003087!important;outline-offset:2px;}
.st-key-browser_navigation button:disabled {opacity:.55;}
.st-key-browser_navigation [data-testid="stCaptionContainer"] p {color:#59677A;font-size:.75rem;margin:0;}
</style>""",
    unsafe_allow_html=True,
)
app["md"](
    '<div class="hero"><div class="kicker">ENTERPRISE RISK MANAGEMENT</div><h1>Northstar Cold Chain</h1><p>The ERM Mandate · Prepare the CAE for the board.</p></div>',
    html=True,
)
view = st.session_state[VIEW_KEY]
frontier = st.session_state.ns["stage"]
reviewing = view < frontier
with st.container(
    key="browser_navigation",
    horizontal=True,
    horizontal_alignment="right",
    vertical_alignment="center",
    gap="xsmall",
):
    st.caption(f"Page {view + 1} of {len(STAGES)}", width="content")
    st.button(
        "Back",
        width=44,
        key="browser_back",
        help="Back: review the previous reached page. Earlier pages are read-only.",
        disabled=view == 0,
        on_click=arrow,
        args=(-1,),
    )
    st.button(
        "Forward",
        width=44,
        key="browser_forward",
        help="Forward: review the next reached page. Use the existing action on your current page to continue.",
        disabled=view == frontier,
        on_click=arrow,
        args=(1,),
    )
app["md"](
    '<div class="rail">'
    + "".join(
        f'<div class="step {"active" if i == view else "done" if i < frontier else ""}">{escape(label)}</div>'
        for i, label in enumerate(STAGES)
    )
    + "</div>",
    html=True,
)
if st.session_state.get("ns_notice"):
    st.warning(st.session_state.ns_notice)
if reviewing:
    st.info("Review only. Return to your current page to continue the activity.")
with st.sidebar:
    st.header("Your decision trail")
    for i, label in enumerate(STAGES):
        st.button(
            label,
            key=f"nav_{i}",
            disabled=i > frontier,
            on_click=browse,
            args=(i,),
            width="stretch",
            type="primary" if i == view else "secondary",
        )
    st.divider()
    app["md"](
        "**Approved delivery criterion**\n\nAt least 98% monthly on-time delivery across existing and new shipments."
    )
    app["md"](
        "**Available internal-audit capacity**\n\n60 hours committed to access-control assurance; 20 available for ERM advice."
    )
    st.button("Start over", on_click=reset, disabled=reviewing, width="stretch")
if reviewing:
    g["st"] = ReviewUI()
try:
    app[
        (
            "assignment",
            "inbox",
            "commission",
            "board_packet",
            "board_brief",
            "board_feedback",
        )[view]
    ]()
finally:
    g["st"] = st
    sync()
app["scroll_to_top"]()

"""Interactive Northstar Cold Chain board-briefing exercise."""

from html import escape
import random

import streamlit as st

from northstar.board_case import (
    BRIEF_FIELDS, BRIEF_OPTIONS, CATEGORIES, MANDATES, OWNERSHIP_CHOICES,
    RECORDS, REQUESTS, STAGES, TRACKER_CHOICES, WORK_CLAIMS,
)
from northstar.board_logic import (
    brief_markdown, briefing_consequences, capacity, commission_review, findings,
    first_brief_changes, ready, request_order, role_review, work_product,
)
from northstar.board_progress import (
    SnapshotError, check_commission, check_roles, commit, decode, defaults, edit_choice, encode,
    navigate, submit_brief,
)

CSS = """
<style>
 :root { --red:#CE0037; --blue:#003087; --navy:#14213D; --muted:#526177; }
 .stApp { background:#F3F6FB; }
 [data-testid="stDecoration"] { background:var(--red); }
 .block-container { max-width:1160px; padding-top:4.4rem; padding-bottom:3rem; }
 h1,h2,h3 { color:var(--navy); letter-spacing:-.025em; }
 .hero { position:relative; overflow:hidden; background:linear-gradient(115deg,#001C51,#003087 72%,#164B96); border-top:6px solid var(--red); border-radius:17px; padding:1.8rem 2rem; margin-bottom:1rem; box-shadow:0 12px 34px #00308722; }
 .hero:after { content:''; position:absolute; width:420px; height:420px; right:-100px; top:-125px; border:1px solid #ffffff30; border-radius:50%; box-shadow:0 0 0 36px #ffffff0b,0 0 0 72px #ffffff0b,0 0 0 108px #ffffff0b; transform:rotate(-24deg); pointer-events:none; }
 .hero h1 { color:white; font-size:clamp(2rem,4.5vw,3.2rem); margin:.2rem 0; position:relative; z-index:1; }
 .hero p { color:#EDF3FF; max-width:820px; margin:.4rem 0; position:relative; z-index:1; font-size:1.07rem; }
 .kicker { color:#E4ECFF; font-size:.76rem; font-weight:800; letter-spacing:.14em; }
 .rail { display:grid; grid-template-columns:repeat(6,1fr); gap:.35rem; margin:.65rem 0 1.3rem; }
 .step { padding:.55rem .25rem; border-radius:8px; text-align:center; background:#E7EBF3; color:#536177; font-size:.74rem; font-weight:700; border:1px solid #D3DBE7; }
 .step.active { background:#003087; color:white; border-color:#003087; }
 .step.done { background:#E9F2EE; color:#176144; border-color:#B3D3C2; }
 .case-card { padding:1.15rem 1.25rem; background:white; border:1px solid #D6DFEB; border-left:5px solid var(--blue); border-radius:12px; margin:.6rem 0 .8rem; }
 .case-card h3 { margin:0 0 .45rem; font-size:1.12rem; }
 .case-card p { margin:0; color:#34445C; line-height:1.55; }
 .eyebrow { color:var(--red); text-transform:uppercase; letter-spacing:.08em; font-size:.73rem; font-weight:800; margin-bottom:.3rem; }
 .metric-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:.7rem; margin:.8rem 0 1rem; }
 .metric { padding:.9rem; border:1px solid #D6DFEB; border-radius:11px; background:white; }
 .metric strong { color:var(--blue); font-size:1.45rem; display:block; font-variant-numeric:tabular-nums; }
 .metric span { color:var(--muted); font-size:.83rem; }
 .result { border:1px solid #D6DFEB; border-left:5px solid #003087; border-radius:11px; background:white; padding:1.1rem; margin:.7rem 0; }
 .result h3 { font-size:1.13rem; margin:0 0 .35rem; }
 .result .status { color:var(--blue); font-weight:750; margin:.15rem 0 .45rem; }
 .result .verdict { display:inline-block; border-radius:5px; padding:.12rem .42rem; margin-right:.35rem; font-size:.85rem; font-weight:800; }
 .result .verdict.correct { color:#176144; background:#E1F2E7; }
 .result .verdict.partial { color:#785100; background:#FFF1C9; }
 .result .verdict.incorrect { color:#A31932; background:#FCE6EB; }
 .result p { color:#34445C; margin:0 0 .4rem; line-height:1.5; }
 .result small { color:#59677B; line-height:1.45; display:block; }
 .dashboard { padding:1.4rem 1.6rem; background:linear-gradient(130deg,#EBF6EF,#F7FBF8); border:1px solid #A9D3BA; border-radius:14px; margin:.6rem 0 1rem; }
 .dashboard strong { display:block; color:#176144; font-size:clamp(2.6rem,6vw,4rem); line-height:1.08; font-variant-numeric:tabular-nums; }
 .dashboard p { margin:.35rem 0 .1rem; font-weight:700; color:#244831; }
 .dashboard small { color:#425F4B; }
 .memo { background:#FFF; border:1px solid #CAD5E4; border-top:5px solid var(--blue); border-radius:12px; padding:1.2rem 1.4rem; margin:1rem 0; }
 .memo h3 { margin-top:0; }
 [data-testid="stPopover"] button { width:100%; min-height:4.4rem; text-align:left; justify-content:space-between; padding:.8rem 1rem; background:#FFF; border:1px solid #CBD6E5; border-left:5px solid var(--blue); border-radius:11px; color:var(--navy); font-weight:750; box-shadow:0 3px 10px #14213D0D; }
 [data-testid="stPopover"] button:hover { border-color:var(--blue); background:#F8FAFE; }
 .stButton button:focus-visible, [data-testid="stPopover"] button:focus-visible, [data-testid="stRadio"] input:focus-visible { outline:3px solid #CE0037 !important; outline-offset:2px; }
 @media(max-width:700px) { .block-container { padding-left:1rem; padding-right:1rem; } .hero { padding:1.3rem 1.1rem; } .rail { grid-template-columns:repeat(3,1fr); } .metric-grid { grid-template-columns:1fr; } }
 @media(prefers-reduced-motion:reduce) { * { scroll-behavior:auto !important; } }
</style>
"""


def md(value: str, *, html: bool = False):
    return st.markdown(str(value).replace("$", "&#36;" if html else r"\$"), unsafe_allow_html=html)


def card(title: str, body: str, eyebrow: str = ""):
    md(
        f'<div class="case-card"><div class="eyebrow">{escape(eyebrow)}</div>'
        f"<h3>{escape(title)}</h3><p>{escape(body)}</p></div>",
        html=True,
    )


def metric_grid(items: list[tuple[str, str]]):
    md(
        '<div class="metric-grid">'
        + "".join(f'<div class="metric"><strong>{escape(v)}</strong><span>{escape(label)}</span></div>' for v, label in items)
        + "</div>",
        html=True,
    )


def show_finding(item):
    tone = {"Correct": "correct", "Partly correct": "partial", "Incorrect": "incorrect"}[item.verdict]
    md(
        f'<div class="result"><h3>{escape(item.title)}</h3>'
        f'<div class="status"><span class="verdict {tone}">{escape(item.verdict)}</span>{escape(item.status)}</div>'
        f'<p>{escape(item.explanation)}</p></div>', html=True,
    )


def state() -> dict:
    return st.session_state.ns


def sync():
    token = encode(state())
    if st.query_params.get("progress") != token:
        st.query_params["progress"] = token


def use(updated: dict, *, scroll: bool = False):
    st.session_state.ns = updated
    if scroll:
        st.session_state.ns_scroll = True
    sync()


def go(stage: int):
    use(navigate(state(), stage), scroll=True)


def reset():
    st.session_state.ns = defaults()
    st.session_state.ns_notice = ""
    st.session_state.ns_scroll = True
    for key in list(st.session_state):
        if key.startswith("widget_"):
            del st.session_state[key]
    sync()


def save(field: str, key: str, role_index: int | None = None):
    value = st.session_state[key]
    if field == "network_tenths":
        value = -1 if value is None else round(value * 10)
    use(edit_choice(state(), field, -1 if value is None else value, role_index))


def check_inbox():
    use(check_roles(state()))


def check_plan():
    use(check_commission(state()))


def send_brief():
    use(submit_brief(state()), scroll=True)


def advance(stage: int):
    use(commit(state(), stage), scroll=True)


def order_for(field: str, values) -> list:
    options = list(values)
    random.Random(f"{state()['seed']}:{field}").shuffle(options)
    return options


def choose(field: str, label: str, options: dict, *, help_text: str | None = None):
    key = f"widget_{field}"
    value = state()["c"][field]
    st.session_state[key] = value if value != -1 else None
    st.radio(
        label, order_for(field, options), index=None,
        format_func=lambda i: options[i].replace("$", r"\$"),
        key=key, on_change=save, args=(field, key), help=help_text,
    )


def navigation(stage: int, next_label: str):
    st.divider()
    left, right = st.columns([1, 2])
    left.button("Back", on_click=go, args=(stage - 1,), width="stretch")
    right.button(
        next_label, type="primary", disabled=not ready(state(), stage),
        on_click=advance, args=(stage,), width="stretch",
    )


def scroll_to_top():
    if not st.session_state.pop("ns_scroll", False):
        return
    st.iframe(
        """<script>
        (()=>{const root=window.parent, main=root.document.querySelector('section[data-testid="stMain"]');
        if(main)root.requestAnimationFrame(()=>root.requestAnimationFrame(()=>main.scrollTo({top:0,left:0,behavior:'auto'})));})();
        </script>""",
        height=1, tab_index=-1,
    )


def assignment():
    st.header("The CAE has a board meeting to prepare for")
    md(
        "Northstar management conditionally launched two new regions with dispatch training, an independent-carrier continuity plan, and claims insurance. "
        "The board is due to review performance eight weeks after launch. Your team advises the chief audit executive (CAE) on the internal-audit work that can be done before that meeting, then prepares a briefing when new records arrive."
    )
    card(
        "The earlier decision",
        "The launch forecast was 98.2% on-time delivery across the network, $265,000 in expected incremental annual net profit, $55,000 for first-year safeguards, and $40,000 in expected annual unreimbursed claims. Those were forecasts at the time of the launch decision.",
        "Prior launch exercise",
    )
    card(
        "The board's standing boundaries",
        "At least 98% monthly on-time delivery across existing and new shipments; expected annual unreimbursed claims no more than $50,000; first-year safeguards no more than $60,000; no intentional product-integrity shortcuts.",
        "Approved criteria",
    )
    md(
        "The CFO owns enterprise risk management (ERM), the COO owns dispatch and responses, and the board oversees risk appetite. "
        "Over the next six weeks, internal audit has 80 hours. Sixty are committed to an approved access-control audit, leaving 20 for one bounded ERM advisory service. "
        "One additional request concerns the companywide risk tracker (risk register): management's list of risks, ratings, owners, and actions."
    )
    md("You will first triage requests, then commission work. At the board meeting, you will inspect records and prepare a briefing that your earlier choices can actually support.")
    st.button("Open the CAE inbox", type="primary", on_click=go, args=(1,), width="stretch")


def inbox():
    st.header("Which requests can internal audit accept?")
    md(
        "The CAE has 20 hours available for ERM advisory work before the board meeting. Six requests have arrived as possible assignments for internal audit, "
        "but not every request belongs in an advisory mandate or fits the available hours. Classify each request by the action internal audit would perform and who would own the decision. "
        "Check the role map to see feedback before moving on."
    )
    ordered = request_order(state()["seed"])
    for row in range(0, len(ordered), 2):
        columns = st.columns(2)
        for position, (column, request_id) in enumerate(zip(columns, ordered[row:row + 2]), start=row + 1):
            with column:
                card(f"Request {position}", REQUESTS[request_id]["text"])
                key = f"widget_role_{request_id}"
                value = state()["c"]["roles"][request_id]
                st.session_state[key] = value if value != -1 else None
                st.selectbox(
                    f"Service category for request {position}",
                    order_for(f"role:{request_id}", CATEGORIES),
                    index=None, format_func=lambda i: CATEGORIES[i],
                    key=key, on_change=save, args=("roles", key, request_id),
                )
    complete = all(value != -1 for value in state()["c"]["roles"])
    st.button("Check the role map", disabled=not complete, on_click=check_inbox, width="stretch")
    if state()["roles_checked"]:
        st.subheader("What the verbs and ownership tell you")
        for position, item in enumerate(role_review(state()["c"], state()["seed"]), start=1):
            chosen = CATEGORIES[item["selected"]]
            status = "Correct" if item["selected"] == item["expected"] else "Incorrect"
            tone = "correct" if status == "Correct" else "incorrect"
            md(
                f'<div class="result"><h3>Request {position}</h3>'
                f'<div class="status"><span class="verdict {tone}">{status}</span>You selected {escape(chosen)}</div>'
                f'<p>{escape(item["reason"])}</p></div>',
                html=True,
            )
        md("The 30-hour tracker request, if pursued, will require arrangements beyond the 20 available advisory hours.")
    navigation(1, "Commission the advisory work")


def commission():
    st.header("Commission one bounded service")
    md(
        "The inbox contained three requests that could be advisory in principle: facilitate managers' risk workshop, train and coach managers on response criteria, "
        "and consolidate the companywide risk tracker. The workshop and coaching requests have been scoped below as 20-hour and 16-hour services, so either can fit the CAE's available 20 hours. "
        "The tracker request is estimated at 30 hours and cannot fit this authorization; you will decide separately how to handle it. "
        "Read what each feasible service would do, who would receive its work, and what it would leave for management to decide."
    )
    columns = st.columns(2)
    for column, (id_, item) in zip(columns, MANDATES.items()):
        with column:
            card(f"{item['name']} · {item['hours']} hours", item["work"])
    choose("mandate", "Which service will the CAE commission?", {i: f"{v['name']} — {v['hours']} hours" for i, v in MANDATES.items()})
    st.subheader("The separate tracker request")
    md(
        "The CFO also asks internal audit to consolidate the companywide risk tracker for six weeks. Managers would validate entries and the CFO would accept handover, "
        "but this request is estimated at 30 hours. Decide whether to leave it with management, seek a separate approval, or change the work actually performed."
    )
    choose("tracker", "What happens to the 30-hour tracker request?", TRACKER_CHOICES)
    choose("ownership", "Who will hold the ongoing decisions and responsibility?", OWNERSHIP_CHOICES)
    c = state()["c"]
    complete = all(c[field] != -1 for field in ("mandate", "tracker", "ownership"))
    st.button("Review the commission plan", disabled=not complete, on_click=check_plan, width="stretch")
    if state()["commission_checked"]:
        st.subheader("Commission review")
        for item in commission_review(c):
            show_finding(item)
        used = capacity(c)
        st.subheader("Capacity under this decision")
        metric_grid([
            (str(used["advisory_hours"]), "Hours assigned to ERM work"),
            (str(used["protected_hours"]), "Hours left on approved access-control audit"),
            ("To be requested" if used["tracker_pending"] else "Not needed now" if c["tracker"] == 0 else "Not obtained", "Tracker approval"),
        ])
        md("**Agreement on responsibility:** " + OWNERSHIP_CHOICES[c["ownership"]])
        md("The record of work actually completed at the six-week handover will appear in the later board packet.")
    navigation(2, "Open the board packet")


def board_packet():
    st.header("The board packet arrives")
    md(
        "Eight weeks after launch, the CAE is preparing for the board's performance review. The CFO's team sent a green delivery dashboard, "
        "the COO supplied a continuity file, and both executives sent requests that would affect what the CAE says or does. "
        "The CAE has gathered the records below to prepare an internal-audit briefing. The six-week handover record has now arrived. "
        "Open each record box to see why it is available and what it says. "
        "The records will remain available in your case notebook while you prepare the briefing."
    )
    for heading, ids in (
        ("Delivery criterion and performance records", (1, 0, 2)),
        ("Continuity and risk context", (3, 4, 5)),
        ("Six-week advisory work product", (7,)),
        ("Executive requests requiring a response", (6,)),
    ):
        st.subheader(heading)
        for start in range(0, len(ids), 2):
            columns = st.columns(2)
            for column, id_ in zip(columns, ids[start:start + 2]):
                record = RECORDS[id_]
                title = work_product(state()["c"])[0] if id_ == 7 else record["title"]
                with column, st.popover(title, width="stretch"):
                    st.caption(record["type"])
                    md("**Why this record is here:** " + record["context"])
                    md("**Record:** " + (work_product(state()["c"])[1] if id_ == 7 else record["body"]))
    md("The CAE must respond to the CFO's labeling request and the COO's authorization request in the briefing. Neither request can be left unresolved.")
    navigation(3, "Prepare the board briefing")


def select_citations():
    c = state()["c"]
    available = list(RECORDS)
    key = "widget_citations"
    st.session_state[key] = c["citations"][:]
    st.multiselect(
        "Which records directly support statements in this briefing?",
        available, format_func=lambda i: work_product(c)[0] if i == 7 else RECORDS[i]["title"],
        key=key, on_change=save, args=("citations", key),
        help="Choose exhibits for the statements you are making, not every record that might be useful in a later engagement.",
    )


def case_notebook():
    c = state()["c"]
    with st.popover("Open case notebook", width="stretch"):
        st.subheader("Case notebook")
        md("This notebook contains the complete board packet and your earlier engagement decisions. It collects facts without assessing your conclusions.")
        md("**Commissioned service:** " + MANDATES[c["mandate"]]["name"])
        md("**Tracker decision:** " + TRACKER_CHOICES[c["tracker"]])
        md("**Ownership agreement:** " + OWNERSHIP_CHOICES[c["ownership"]])
        for id_ in RECORDS:
            record = RECORDS[id_]
            title = work_product(c)[0] if id_ == 7 else record["title"]
            with st.expander(title, expanded=False):
                md(record["context"])
                md(work_product(c)[1] if id_ == 7 else record["body"])


def enter_network_result():
    key = "widget_network_tenths"
    value = state()["c"]["network_tenths"]
    st.session_state[key] = value / 10 if value != -1 else None
    st.number_input(
        "Monthly on-time delivery (%)",
        min_value=0.0, max_value=100.0, value=None, step=0.1, format="%.1f",
        key=key, on_change=save, args=("network_tenths", key),
    )


def board_brief():
    st.header("Prepare the CAE's board briefing")
    md(
        "The chair needs a clear account of delivery performance, continuity readiness, and the confidence internal audit can claim. "
        "Build one coherent briefing from the board packet and the work your team commissioned. Your notebook keeps every record available while you decide. "
        "Submitting takes you to a separate review of the briefing; revision is optional."
    )
    case_notebook()
    st.subheader("1. What do the records say?")
    enter_network_result()
    choose("headline", "Delivery headline", BRIEF_OPTIONS["headline"])
    choose("continuity", "Continuity status", BRIEF_OPTIONS["continuity"])
    st.subheader("2. What can internal audit say and do?")
    route = 2 if state()["c"]["tracker"] == 2 else state()["c"]["mandate"]
    choose("work_claim", "What does your completed advisory work support?", WORK_CLAIMS[route])
    choose("communication", "How will the CAE respond to the CFO's request to retitle the work as independent assurance?", BRIEF_OPTIONS["communication"])
    choose("authority", "How will the CAE respond to the COO's request for temporary operating authorization?", BRIEF_OPTIONS["authority"])
    st.subheader("3. What independent work should follow?")
    choose("scope", "Propose one assurance subject", BRIEF_OPTIONS["scope"])
    choose("provider", "Propose a provider for that subject", BRIEF_OPTIONS["provider"])
    st.subheader("4. Choose the exhibits for this briefing")
    md("Your packet contains more than a board briefing should cite. Include records that directly support the statements you selected above; keep other records in the notebook for later work.")
    select_citations()
    c = state()["c"]
    complete = bool(c["citations"]) and all(c[field] != -1 for field in BRIEF_FIELDS)
    if complete:
        md('<div class="memo"><h3>Your draft</h3></div>', html=True)
        md(brief_markdown(c))
    st.button("Submit briefing for feedback", disabled=not complete, type="primary", on_click=send_brief, width="stretch")


def board_feedback():
    st.header("Board briefing review")
    md("Your briefing has been submitted. Review what the evidence supports, how your earlier mandate shaped the result, and what the board can do with this communication. You do not have to revise it; you may return to the briefing if you want to test a different conclusion.")
    with st.expander("View your submitted briefing", expanded=False):
        md(brief_markdown(state()["c"]))
    st.subheader("Decision-by-decision feedback")
    for item in findings(state()["c"]):
        show_finding(item)
    st.subheader("What did your briefing make possible?")
    md("The consequences below follow from the mandate, evidence, and board statements you actually selected. They distinguish what the board can act on now from work that still needs management or a future independent engagement.")
    for title, body in briefing_consequences(state()["c"]):
        card(title, body)
    changed = first_brief_changes(state())
    if changed:
        md("**Changes since your first submission:** " + ", ".join(field.replace("_", " ") for field in changed) + ".")
    left, right = st.columns(2)
    left.button("Review board packet", on_click=go, args=(3,), width="stretch")
    right.button("Revise briefing (optional)", on_click=go, args=(4,), width="stretch")
    st.button("Start a new case", on_click=reset, width="stretch")


def main():
    st.set_page_config(
        page_title="Northstar Cold Chain | The ERM Mandate",
        page_icon="🧭", layout="wide", initial_sidebar_state="collapsed",
    )
    if "ns" not in st.session_state:
        try:
            values = st.query_params.get_all("progress")
            if len(values) > 1:
                raise SnapshotError("Multiple progress values.")
            st.session_state.ns = decode(values[0]) if values else defaults()
            st.session_state.ns_notice = ""
        except SnapshotError:
            st.session_state.ns = defaults()
            st.session_state.ns_notice = "This link could not restore your choices. A new case has started."
    md(CSS, html=True)
    md(
        '<div class="hero"><div class="kicker">ENTERPRISE RISK MANAGEMENT</div>'
        '<h1>Northstar Cold Chain</h1><p>The ERM Mandate · Prepare the CAE for the board.</p></div>',
        html=True,
    )
    stage = state()["stage"]
    md(
        '<div class="rail">'
        + "".join(
            f'<div class="step {"active" if i == stage else "done" if i in state()["committed"] or (i == 0 and stage > 0) else ""}">{escape(label)}</div>'
            for i, label in enumerate(STAGES)
        )
        + "</div>",
        html=True,
    )
    if st.session_state.get("ns_notice"):
        st.warning(st.session_state.ns_notice)
    with st.sidebar:
        st.header("Your decision trail")
        for i, label in enumerate(STAGES):
            st.button(
                label, key=f"nav_{i}", disabled=i > len(state()["committed"]) + 1,
                on_click=go, args=(i,), width="stretch",
                type="primary" if i == stage else "secondary",
            )
        st.divider()
        md("**Approved delivery criterion**\n\nAt least 98% monthly on-time delivery across existing and new shipments.")
        md("**Available internal-audit capacity**\n\n60 hours committed to access-control assurance; 20 available for ERM advice.")
        st.button("Start over", on_click=reset, width="stretch")
    (assignment, inbox, commission, board_packet, board_brief, board_feedback)[stage]()
    sync()
    scroll_to_top()

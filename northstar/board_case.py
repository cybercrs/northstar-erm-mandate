"""Northstar board-briefing case. Fictional continuation of the paper case."""

STAGES = (
    "Assignment",
    "CAE inbox",
    "Commission the work",
    "Board packet",
    "Board briefing",
    "Feedback",
)

CATEGORIES = {
    0: "Assurance",
    1: "Advisory",
    2: "Management responsibility",
}

# The order on screen is shuffled once per anonymous progress link.
REQUESTS = (
    {
        "text": "Assess whether key-risk reports are complete and use the board-approved delivery criterion.",
        "category": 0,
        "reason": "Assessing management's reporting against criteria is assurance. Management still owns the reports.",
    },
    {
        "text": "Facilitate a workshop in which managers identify, score, and own dispatch risks.",
        "category": 1,
        "reason": "Internal audit facilitates; managers make and own the risk judgments.",
    },
    {
        "text": "Train managers on risk criteria and compare response alternatives; the COO selects the response.",
        "category": 1,
        "reason": "Education and recommendations can be advisory because the COO retains the decision.",
    },
    {
        "text": "Set Northstar's risk appetite and approve exceptions to the delivery tolerance.",
        "category": 2,
        "reason": "Setting appetite and approving exceptions are governance and management decisions, not internal-audit decisions.",
    },
    {
        "text": "Consolidate the companywide risk tracker for six weeks. Managers validate entries; the CFO owns it and accepts handover. The work is estimated at 30 hours.",
        "category": 1,
        "reason": "With CFO ownership and manager validation, consolidation can be advisory in principle. Its 30-hour cost is a separate authorization question.",
    },
    {
        "text": "Choose and implement the continuity response, then sign the launch authorization.",
        "category": 2,
        "reason": "Selecting, operating, and authorizing the response makes internal audit responsible for management's action.",
    },
)

MANDATES = {
    0: {
        "name": "Risk-alignment workshop",
        "hours": 20,
        "work": "Internal audit prepares a comparison of how dispatch, sales, and operations currently score delivery risks. It facilitates a cross-functional workshop in which those managers identify shared dependencies, discuss inconsistent ratings, and validate a summary for the CFO and COO. The managers decide the ratings and responses. The 20 hours cover preparation (4), workshop (6), drafting and validation (6), and handover (4).",
        "artifact_title": "Manager-validated workshop summary",
        "artifact": "The CFO and COO record that divisions used different scoring scales. Existing customers and both new regions rely on the primary dispatch system. The CFO will reconcile risk reporting; the COO will document the selected response and its owner.",
    },
    1: {
        "name": "Criteria training and response coaching",
        "hours": 16,
        "work": "Internal audit trains dispatch and regional managers to apply the board's delivery, claims, safeguard-cost, and product-integrity limits to proposed responses. It then compares response alternatives with them and gives the COO an agreed coaching memo; the COO selects and owns any response. The 16 hours cover training (8), response discussion (4), and the memo (4), leaving four advisory hours unassigned.",
        "artifact_title": "Training and coaching memo",
        "artifact": "Managers worked through the board's delivery, claims, safeguard, and product-integrity boundaries. The memo compares response alternatives for the COO, who will record the selection. Attendance and the agreed discussion points are attached.",
    },
}

TRACKER_CHOICES = {
    0: "Keep the six-week tracker consolidation with the CFO for now; discuss a narrower future scope.",
    1: "Seek separate approval for a 30-hour tracker engagement; do not start it under this mandate.",
    2: "Begin the 30-hour tracker consolidation now, move 10 hours from the approved access-control audit, and seek ratification at the next committee meeting.",
}

OWNERSHIP_CHOICES = {
    0: "CFO owns ERM and the risk tracker; COO owns dispatch and its responses; internal audit advises.",
    1: "To keep the tracker on schedule, internal audit maintains ERM scoring until the CFO can take handover.",
    2: "To resolve dispatch exceptions quickly, internal audit selects continuity and signs temporary authorization before handing operation to the COO.",
}

RECORDS = {
    0: {
        "title": "Board dashboard",
        "type": "New Evidence",
        "context": "The CFO's board-preparation team assembled this monthly performance dashboard from the launch reporting feed. Management wants the CAE to use its green status in the board discussion.",
        "body": "Green status. On-time delivery: 98.6%. Reporting population: new-contract shipments only. Reporting month: the first full month after launch.",
    },
    1: {
        "title": "Approved delivery criterion",
        "type": "Existing case record",
        "context": "The board approved this measure when management authorized the launch. It is the benchmark for interpreting any later delivery result.",
        "body": "At least 98% monthly on-time delivery across existing and new shipments. The board has not approved a change to the measure or its population.",
    },
    2: {
        "title": "Monthly delivery source report",
        "type": "New Evidence",
        "context": "Operations produced this report for the same reporting month as the dashboard. It contains both the new-contract figure used in the dashboard and the complete-network result.",
        "body": "On-time delivery for the same month: 98.6% for new-contract shipments; 97.7% for the complete network of existing and new shipments. The dashboard draws only from the first population.",
    },
    3: {
        "title": "Continuity readiness file",
        "type": "New Evidence",
        "context": "The COO supplied this file in response to a board-preparation question about the independent carrier and temperature control. It is the available record of continuity preparation at the review date.",
        "body": "The independent carrier's controlled simulation used separate credentials, a queue, and reserved capacity. Northstar has not supplied its own end-to-end exercise or complete temperature-hold records.",
    },
    4: {
        "title": "Routing override sample",
        "type": "Existing case record",
        "context": "Internal audit retained this ten-item documentation sample from its earlier launch review. The CAE has it available when considering whether to make a broader dispatch claim.",
        "body": "Six of ten sampled manual routing overrides have no reason code. The supplied sample does not identify the shipments' outcomes or establish a network-wide error rate.",
    },
    5: {
        "title": "Management risk tracker",
        "type": "Existing case record",
        "context": "The CFO's team updated its list of risks, ratings, owners, and actions for the board cycle. It reflects management's current view of dispatch risk and provides context for the advisory work.",
        "body": "Dispatch is marked green. Divisions used incompatible scoring scales. The CFO owns ERM; the COO owns dispatch and its responses. The green rating is management's assessment.",
    },
    6: {
        "title": "Executive requests to the CAE",
        "type": "New Evidence",
        "context": "The CFO and COO sent these requests while the CAE was drafting the board communication. The CAE must decide how to respond to each request before the briefing is issued.",
        "body": "The CFO asks whether the advisory product can be retitled 'independent assurance' before the board meeting. The COO asks the CAE to sign temporary operating authorization while managers address delivery exceptions.",
    },
    7: {
        "title": "Six-week work product",
        "type": "Your engagement record",
        "context": "This is the six-week handover record for the work that was actually performed. Its content depends on the service and capacity decisions made earlier.",
        "body": "The completed work product is shown below.",
    },
}

WORK_CLAIMS = {
    0: {
        0: "Managers validated a shared summary of inconsistent scoring and the dispatch dependency.",
        1: "Managers demonstrated consistent application of the board's limits after formal training.",
        2: "Northstar's own continuity process operated effectively.",
    },
    1: {
        0: "Managers practiced applying the board's limits and discussed response alternatives for the COO's decision.",
        1: "Managers validated one enterprise-wide dispatch risk rating and dependency map.",
        2: "Northstar's own continuity process operated effectively.",
    },
    2: {
        0: "The CFO validated the consolidated tracker entries for handover.",
        1: "A completed workshop reconciled inconsistent ratings across divisions.",
        2: "Northstar's own continuity process operated effectively.",
    },
}

BRIEF_OPTIONS = {
    "headline": {
        0: "Monthly on-time delivery meets the board's criterion.",
        1: "Monthly on-time delivery falls below the board's criterion.",
        2: "The supplied records do not permit a comparison with the criterion.",
    },
    "continuity": {
        0: "The available record is sufficient to conclude that Northstar's continuity operated effectively.",
        1: "The available record raises a readiness question but does not support an operating-effectiveness conclusion.",
        2: "No relevant continuity information is available.",
    },
    "communication": {
        0: "Present the supported observations as advisory work and propose separately scoped testing for independent assurance.",
        1: "Retitle the advisory product as an independent assurance conclusion for the board.",
        2: "Withhold all observations until a full assurance engagement is complete.",
    },
    "authority": {
        0: "Management evaluates correction and authorization; the board receives the exception and any proposed tolerance change.",
        1: "The CAE signs temporary dispatch authorization so management can move quickly.",
        2: "Management retains the green status and waits to tell the board until the delivery result improves.",
    },
    "scope": {
        0: "Completeness and reliability of risk reporting and dispatch exceptions.",
        1: "Design and operation of independent continuity and temperature-hold arrangements.",
    },
    "provider": {
        0: "Internal audit after a documented objectivity and competence assessment, with qualified specialist help where needed.",
        1: "A separately commissioned, suitably qualified independent provider.",
        2: "The same advisory team, relying on a general independence pledge.",
        3: "The financial auditor's existing financial-statement opinion.",
    },
}

BRIEF_FIELDS = ("network_tenths", "headline", "continuity", "work_claim", "communication", "authority", "scope", "provider")

"""Transparent consequences for the board-briefing exercise, not a grade."""

from dataclasses import dataclass

from .board_case import BRIEF_FIELDS, BRIEF_OPTIONS, MANDATES, RECORDS, REQUESTS, WORK_CLAIMS


@dataclass(frozen=True)
class Finding:
    title: str
    status: str
    explanation: str
    prompt: str

    @property
    def verdict(self) -> str:
        if self.status in {
            "Supported", "Appropriately qualified", "Claim matches work performed",
            "Advisory work identified", "Preserved", "Credible route proposed",
            "Focused and sufficient", "Defensible priority", "Defensible scope", "Correct figure", "Authorized path",
            "Management ownership preserved",
        }:
            return "Correct"
        if self.status in {"Important source omitted"}:
            return "Partly correct"
        return "Incorrect"


def request_order(seed: int) -> list[int]:
    import random

    order = list(range(len(REQUESTS)))
    random.Random(f"{seed}:inbox").shuffle(order)
    return order


def ready(state: dict, stage: int) -> bool:
    c = state["c"]
    if stage == 1:
        return state["roles_checked"] and all(v in (0, 1, 2) for v in c["roles"])
    if stage == 2:
        return state["commission_checked"] and all(c[k] in options for k, options in (
            ("mandate", MANDATES),
            ("tracker", (0, 1, 2)),
            ("ownership", (0, 1, 2)),
        ))
    if stage == 3:
        return True
    if stage == 4:
        return (
            state["brief_submitted"]
            and 0 <= c["network_tenths"] <= 1000
            and c["work_claim"] in WORK_CLAIMS[work_route(c)]
            and all(c[k] in BRIEF_OPTIONS[k] for k in BRIEF_FIELDS if k not in ("network_tenths", "work_claim"))
            and bool(c["citations"])
        )
    return False


def capacity(c: dict) -> dict:
    displaced = c["tracker"] == 2
    return {
        "advisory_hours": 30 if displaced else MANDATES[c["mandate"]]["hours"],
        "protected_hours": 50 if displaced else 60,
        "chosen_service_delivered": not displaced,
        "tracker_pending": c["tracker"] == 1,
    }


def work_product(c: dict) -> tuple[str, str]:
    if c["tracker"] == 2:
        return (
            "Consolidated risk-tracker draft",
            "Internal audit compiled managers' entries for the CFO's six-week tracker. "
            "The CFO validated the entries for handover. The selected workshop or coaching service was not performed.",
        )
    mandate = MANDATES[c["mandate"]]
    return mandate["artifact_title"], mandate["artifact"]


def work_route(c: dict) -> int:
    return 2 if c["tracker"] == 2 else c["mandate"]


def role_review(c: dict, seed: int) -> list[dict]:
    return [
        {
            "id": i,
            "selected": c["roles"][i],
            "expected": REQUESTS[i]["category"],
            "reason": REQUESTS[i]["reason"],
        }
        for i in request_order(seed)
    ]


def commission_review(c: dict) -> list[Finding]:
    mandate = MANDATES[c["mandate"]]
    if c["mandate"] == 0:
        priority = (
            "A cross-functional comparison is a defensible use of the full 20 hours when inconsistent ratings and shared dispatch dependencies are the immediate problem. "
            "Managers must validate the summary and decide what to change."
        )
    else:
        priority = (
            "Training and coaching are a defensible 16-hour choice when managers need to apply the board's limits consistently before the COO selects a response. "
            "The four unused advisory hours do not authorize the separate 30-hour tracker request."
        )
    result = [Finding("Advisory priority", "Defensible priority", priority, "")]
    if c["tracker"] == 2:
        result.append(Finding(
            "Tracker request and capacity", "Unapproved substitution",
            "Starting 30 hours of tracker consolidation would replace your chosen service and take 10 hours from the approved access-control audit, leaving only 50 of its 60 approved hours. "
            "A request for later ratification is not prior authorization. The board packet will contain a tracker draft, not the workshop or coaching product you selected.", "",
        ))
    elif c["tracker"] == 1:
        result.append(Finding(
            "Tracker request and capacity", "Authorized path",
            "Seeking separate approval is appropriate, but no tracker consolidation begins under this 20-hour mandate. "
            f"The {mandate['name'].lower()} proceeds, and the 60 approved assurance hours remain protected.", "",
        ))
    else:
        result.append(Finding(
            "Tracker request and capacity", "Authorized path",
            "Leaving tracker consolidation with the CFO for now and discussing a smaller future scope stays within current approval. "
            f"The {mandate['name'].lower()} proceeds, and the 60 approved assurance hours remain protected.", "",
        ))
    if c["ownership"] == 0:
        result.append(Finding(
            "Decision ownership", "Management ownership preserved",
            "The CFO keeps ERM and the tracker; the COO keeps dispatch responses and authorization. Internal audit can facilitate, train, compare, and report without operating those decisions.", "",
        ))
    else:
        subject = "ERM scoring and the tracker" if c["ownership"] == 1 else "continuity response and operating authorization"
        result.append(Finding(
            "Decision ownership", "Management responsibility accepted",
            f"The agreement makes internal audit responsible for {subject}. A later handover does not erase that responsibility or the resulting self-review threat for assurance over that subject. Return the decision to management before commissioning.", "",
        ))
    return result


def owns_assurance_subject(c: dict) -> bool:
    return (
        (c["scope"] == 0 and c["ownership"] == 1)
        or (c["scope"] == 1 and c["ownership"] == 2)
    )


def findings(c: dict) -> list[Finding]:
    cited = set(c["citations"])
    result = []

    if c["network_tenths"] == 977:
        result.append(Finding(
            "Complete-network figure", "Correct figure",
            "You entered 97.7%, the complete-network monthly result in the operations source report. The dashboard's 98.6% is a different, narrower population.", "",
        ))
    else:
        result.append(Finding(
            "Complete-network figure", "Source value needs checking",
            "The operations source report gives 97.7% for all existing and new shipments in this month. The dashboard's 98.6% applies only to new-contract shipments; it cannot be entered as the complete-network result.", "",
        ))

    if c["headline"] == 1 and c["network_tenths"] == 977:
        result.append(Finding(
            "Delivery reporting", "Supported",
            "The dashboard reports 98.6% for new contracts only. The same month's complete-network result is 97.7%, below the approved 98% all-network criterion.",
            "What would the board misunderstand if it saw only the green dashboard?",
        ))
    elif c["network_tenths"] != 977:
        result.append(Finding(
            "Delivery reporting", "Source value needs checking",
            "The complete-network monthly source report states 97.7%, while the dashboard's 98.6% covers new contracts only. Recheck the figure entered for the complete network before interpreting it.",
            "Which record contains the complete population for this month?",
        ))
    else:
        result.append(Finding(
            "Delivery reporting", "Revise the headline",
            "The green 98.6% figure covers only new contracts. The all-network source report is 97.7% for the same month, below the board's 98% all-network criterion.",
            "Which population is in each measure?",
        ))

    if c["continuity"] == 1:
        result.append(Finding(
            "Continuity evidence", "Appropriately qualified",
            "The carrier simulation informs planning, but the file lacks Northstar's own end-to-end exercise and complete temperature-hold records.",
            "What testing would be needed before claiming operating effectiveness?",
        ))

    else:
        result.append(Finding(
            "Continuity evidence", "Inference exceeds the record",
            "A carrier simulation exists, so there is some planning evidence. It does not demonstrate Northstar's own end-to-end operation; the supplied file lacks that exercise and complete temperature-hold records.",
            "What is known, and what remains to be tested?",
        ))

    core = {0, 1, 2, 3, 6, 7}
    optional = ({4} if c["scope"] == 0 else set()) | ({5} if work_route(c) in (0, 2) else set())
    missing = core - cited
    extra = cited - core - optional
    if not missing and not extra:
        qualified = []
        if 4 in cited:
            qualified.append("The routing sample can motivate a proposed reporting or dispatch-exception scope, but its ten items do not establish shipment outcomes or a network error rate.")
        if 5 in cited:
            qualified.append("The management tracker can provide context for the workshop or tracker product, but its green rating is not independent corroboration.")
        result.append(Finding(
            "Evidence selection", "Focused and sufficient",
            "Your exhibit set is complete and focused for the topics in this briefing: the dashboard, approved benchmark, complete-network source, continuity file, management requests, and actual work product. This assesses source selection, not whether every conclusion you drew is correct. "
            + (" ".join(qualified) if qualified else "You left other packet records out of the exhibit list because the submitted statements did not need them."), "",
        ))
    else:
        details = []
        if missing:
            details.append("Add records directly supporting your submitted statements: " + ", ".join(RECORDS[i]["title"] for i in sorted(missing)) + ".")
        if extra:
            details.append("These exhibits are not tied to a distinct statement or proposed subject in this draft: " + ", ".join(RECORDS[i]["title"] for i in sorted(extra)) + ". An exhibit belongs in the brief only when you can name the limited claim it supports; keep other records in the notebook for later scoping.")
        result.append(Finding(
            "Evidence selection", "Important source omitted" if missing and not extra else "Selection needs editing",
            " ".join(details), "",
        ))

    if c["tracker"] == 2:
        result.append(Finding(
            "Mandate and capacity", "Unapproved substitution",
            "The selected workshop or coaching service was displaced by 30 hours of tracker work. Ten of the already approved access-control audit's 60 hours were used without approval; only 50 remain. Do not present the displaced service as completed.",
            "What approval and rescoping would be needed before that work could proceed?",
        ))
    route = work_route(c)
    if c["work_claim"] == 0:
        result.append(Finding(
            "Advisory work product", "Claim matches work performed",
            "The proposed observation describes the product actually completed. It remains an advisory observation, not an independent conclusion about operating effectiveness.",
            "What management action remains after this product is handed over?",
        ))
    elif c["work_claim"] == 2:
        result.append(Finding(
            "Advisory work product", "Operating claim unsupported",
            "Neither the workshop, coaching memo, nor tracker consolidation independently tested Northstar's own continuity operation.",
            "Which test and records would be needed for that claim?",
        ))
    else:
        result.append(Finding(
            "Advisory work product", "Claim does not match this mandate",
            f"The completed work was: {work_product(c)[0].lower()}. The selected statement describes a different product. The statement supported by this route is: {WORK_CLAIMS[route][0]}",
            "Which part of the completed product supports the sentence you plan to use?",
        ))

    if c["communication"] == 0:
        result.append(Finding(
            "Mandate and confidence", "Advisory work identified",
            "Declining the CFO's requested assurance label is appropriate. The work performed is advisory, not an independent test of ERM or continuity operation. Separate assurance would need its own scope, evidence, competence, and approval.",
            "Which sentences in your brief come from the advisory product, and which from source records?",
        ))
    elif c["communication"] == 1:
        result.append(Finding(
            "Mandate and confidence", "Assurance overstated",
            "The CFO's requested title does not add independent testing or change the work performed. The board should hear supported observations with their actual confidence level.",
            "What work would have to change before the CAE could issue assurance?",
        ))
    else:
        result.append(Finding(
            "Mandate and confidence", "Useful observation withheld",
            "Rejecting the CFO's assurance label does not require silence. Internal audit may communicate supported observations and limitations without claiming that a full assurance engagement has been completed.",
            "How could the CAE report the scope mismatch without overstating confidence?",
        ))

    if c["authority"] == 0 and c["ownership"] == 0:
        result.append(Finding(
            "Management accountability", "Preserved",
            "Declining the COO's request that the CAE sign operating authorization preserves the agreement: the CFO and COO retain ERM, response, correction, and authorization decisions. Internal audit can advise and report the exception.",
            "Which decision must remain with management even when time is short?",
        ))
    elif c["authority"] == 0:
        result.append(Finding(
            "Management accountability", "Agreement contradicts briefing",
            "The proposed board sentence declines the COO's authorization request, but the earlier agreement gave internal audit ownership of ERM scoring or continuity operation. The agreement itself must be corrected; a later sentence cannot undo it.",
            "Can a later sentence undo a responsibility internal audit already accepted?",
        ))
    elif c["authority"] == 1:
        result.append(Finding(
            "Management accountability", "Boundary crossed",
            "Accepting the COO's request to have the CAE sign temporary operating authorization makes internal audit responsible for management's response. The COO must authorize and operate correction; the board receives the relevant exception.",
            "Who owns corrective action, authorization, and any proposed change to the criterion?",
        ))
    else:
        result.append(Finding(
            "Management accountability", "Exception concealed",
            "Waiting to tell the board until the delivery result improves would leave a supported exception out of the review. Management must address the result and communicate it; the CAE should not preserve an unsupported green status.", "",
        ))

    if c["scope"] == 0:
        scope_reason = (
            "Risk reporting and dispatch exceptions are a defensible next subject because the board needs to know whether its measures, populations, and exception controls are complete and reliable. "
            "A new engagement would need criteria and testing; the advisory work did not supply that opinion."
        )
    else:
        scope_reason = (
            "Continuity and temperature-hold arrangements are a defensible next subject because the available file leaves Northstar's own end-to-end operation unresolved. "
            "A new engagement would need appropriate recovery expertise and operating evidence."
        )
    result.append(Finding("Future assurance subject", "Defensible scope", scope_reason, ""))

    if c["provider"] == 2:
        result.append(Finding(
            "Future independent view", "Provider not credible",
            "Assigning the same advisory team and asking for a general independence pledge does not resolve the actual objectivity threat. A separately approved engagement needs a documented assessment of responsibility, competence, and staffing—or a suitably qualified independent provider.",
            "What subject would a new engagement actually test?",
        ))
    elif c["provider"] == 3:
        result.append(Finding(
            "Future independent view", "Provider not credible",
            "The financial auditor's existing financial-statement opinion did not examine this dispatch subject. A new scope and suitably qualified provider are needed before the board can receive an independent view of it.",
            "What subject would a new engagement actually test?",
        ))
    elif owns_assurance_subject(c) and c["provider"] == 0:
        result.append(Finding(
            "Future independent view", "Self-review unresolved",
            "The earlier agreement gave the internal-audit function responsibility for the subject now proposed for assurance. Another internal-audit team cannot independently assure the function's own responsibility; use a suitably qualified independent provider.",
            "Would a different team remove a function-level responsibility?",
        ))
    else:
        note = (
            "An independent provider can be proposed for this subject, with separate approval and suitable competence."
            if c["provider"] == 1
            else "Internal audit could be considered only after a documented objectivity and competence assessment, appropriate staffing, and separate approval."
        )
        result.append(Finding(
            "Future independent view", "Credible route proposed",
            note + (" Specialist recovery competence is needed for continuity work." if c["scope"] == 1 else ""),
            "What evidence would this future engagement need that today's advisory work did not collect?",
        ))

    return result


def brief_markdown(c: dict) -> str:
    title, _ = work_product(c)
    sources = ", ".join(title if i == 7 else RECORDS[i]["title"] for i in c["citations"]) or "None selected"
    return (
        "### Proposed board briefing\n\n"
        f"**Work performed:** {title}.\n\n"
        f"**Delivery:** The monthly on-time delivery figure you entered is {c['network_tenths'] / 10:.1f}%. "
        f"{BRIEF_OPTIONS['headline'][c['headline']]}\n\n"
        f"**Records cited:** {sources}.\n\n"
        f"**Continuity:** {BRIEF_OPTIONS['continuity'][c['continuity']]}\n\n"
        f"**Observation from our completed work:** {WORK_CLAIMS[work_route(c)][c['work_claim']]}\n\n"
        f"**How we communicate:** {BRIEF_OPTIONS['communication'][c['communication']]}\n\n"
        f"**Decisions and authority:** {BRIEF_OPTIONS['authority'][c['authority']]}\n\n"
        f"**Proposed independent follow-up:** {BRIEF_OPTIONS['scope'][c['scope']]} "
        f"Provider: {BRIEF_OPTIONS['provider'][c['provider']]}"
    )


def briefing_consequences(c: dict) -> list[tuple[str, str]]:
    """Explain what the submitted decisions make possible, not merely repeat them."""
    cited = set(c["citations"])
    delivery_supported = c["network_tenths"] == 977 and c["headline"] == 1 and {0, 1, 2}.issubset(cited)
    if delivery_supported and c["communication"] != 2 and c["authority"] != 2:
        delivery = (
            "The board can now see that the green 98.6% dashboard covers only new-contract shipments, while the approved all-network measure is 97.7% for the same month. "
            "That comparison gives management a specific exception to investigate and a basis for a corrective response; it does not by itself identify the cause or prove which shipments were harmed."
        )
    elif delivery_supported:
        delivery = (
            "Your evidence and headline identify the 97.7% all-network result below the approved 98% measure, but your communication choice would keep that exception from reaching the board in a usable form. "
            "The analysis could support a management response only if the CAE communicates it rather than withholding the observations or preserving the unsupported green status."
        )
    else:
        delivery = (
            "The briefing does not yet give the board a fully supported account of the delivery exception. The dashboard's 98.6% covers only new contracts; the approved criterion applies to the 97.7% complete-network result. "
            "Until the figure, headline, and three supporting records agree, a green label could delay management's investigation or misstate whether the approved limit was met."
        )
    if c["continuity"] == 1 and 3 in cited:
        delivery += " Your continuity statement also separates the carrier's simulation from Northstar's still-unverified end-to-end operation, leaving a concrete testing question for later work."
    else:
        delivery += " The continuity conclusion also needs to be qualified against the readiness file before the board can distinguish preparation from demonstrated operation."

    if c["tracker"] == 2:
        mandate = (
            "The board packet contains a CFO-validated tracker draft because the 30-hour request displaced the selected service. The workshop or coaching product was not delivered. "
            "Ten hours were taken from the approved access-control audit, leaving 50 of its 60 hours; the CAE must disclose that unauthorized tradeoff and seek a fresh decision rather than implying both jobs were completed."
        )
    elif c["mandate"] == 0:
        mandate = (
            "The manager-validated workshop summary gives the CFO a starting point for reconciling incompatible risk scales and gives the COO a shared picture of dispatch dependencies. "
            "It uses all 20 available advisory hours. Managers still have to reconcile ratings, select responses, and operate them; a requested tracker engagement has not begun."
        )
    else:
        mandate = (
            "The training and coaching memo gives managers a common way to apply the board's limits and gives the COO alternatives to compare before selecting a response. "
            "It uses 16 advisory hours, leaving four unassigned. Those four hours cannot cover or authorize the separate 30-hour tracker request, and management still owns the response."
        )
    if c["work_claim"] != 0:
        mandate += " The selected statement about that work goes beyond or differs from the product actually completed, so it would need to be corrected before issue."
    if c["ownership"] != 0:
        mandate += " The earlier agreement also assigned a management decision to internal audit; a later board sentence cannot undo that role without changing the engagement agreement."

    if c["communication"] == 0:
        governance = (
            "The CAE can decline the CFO's request to relabel advice as independent assurance while still giving the board the supported observations and their limits. "
            "That preserves the distinction between a useful advisory product and testing that has not been performed."
        )
    elif c["communication"] == 1:
        governance = (
            "Accepting the CFO's requested assurance label would cause the board to place independent confidence in work that consisted of facilitation, training, or tracker consolidation. "
            "Changing the title cannot create testing or objectivity; the CAE would need to correct the communication."
        )
    else:
        governance = (
            "Withholding every observation would leave the board without a timely, qualified view of the reporting exception. The CAE can communicate supported facts now and reserve an independent opinion for separately authorized testing."
        )
    if c["authority"] == 0:
        governance += " The COO, not the CAE, can authorize and operate a correction; the board can receive the exception and consider any formally proposed change to tolerance."
    elif c["authority"] == 1:
        governance += " Signing the COO's requested temporary operating authorization would make internal audit part of management's response and compromise later assurance over that response. The COO must sign it."
    else:
        governance += " Keeping the exception from the board while waiting for improvement would defeat the purpose of the review. Management should address the result and communicate the exception, not preserve an unsupported green status."

    subject = "risk reporting and dispatch exceptions" if c["scope"] == 0 else "continuity and temperature-hold arrangements"
    if c["provider"] == 2:
        assurance = (
            f"The proposed future subject—{subject}—could be tested, but the selected provider does not supply a credible independent view. "
            "A general pledge from the same advisory team does not resolve objectivity. A new engagement and a documented assessment or suitably qualified independent provider are needed."
        )
    elif c["provider"] == 3:
        assurance = (
            f"The proposed future subject—{subject}—could be tested, but the existing financial-statement opinion does not cover it. "
            "The board would need a newly scoped engagement and a suitably qualified provider."
        )
    elif c["provider"] == 0 and owns_assurance_subject(c):
        assurance = (
            f"The proposed subject—{subject}—is one for which internal audit accepted management responsibility in the earlier agreement. "
            "A different internal-audit team would still review the function's own work. A separately commissioned, qualified independent provider is the credible route unless that responsibility and its effects are resolved."
        )
    else:
        assurance = (
            f"The proposed next engagement could examine {subject}, but it requires separate approval, defined criteria, new evidence, and a qualified provider. "
            + ("Internal audit would first need a documented objectivity and competence assessment. " if c["provider"] == 0 else "The proposed independent provider would need relevant expertise. ")
            + ("For continuity, that means evidence from Northstar's own end-to-end exercise and temperature-hold operation, not only the carrier's simulation." if c["scope"] == 1 else "For reporting, that means testing completeness, population definitions, exception handling, and controls behind the board measures.")
        )
    if 4 in cited and c["scope"] == 0:
        assurance += " The routing sample helps motivate that proposed scope, but its missing reason codes do not prove shipment outcomes or a network error rate."
    if 5 in cited and work_route(c) in (0, 2):
        assurance += " The management tracker adds context to the completed advisory product, but its green status remains management's assessment."
    if (4 in cited and c["scope"] != 0) or (5 in cited and work_route(c) == 1):
        assurance += " One or more extra exhibits are not tied to a statement or proposed subject in this draft; keeping them in the notebook would avoid implying broader support."
    return [
        ("What the board can act on", delivery),
        ("What the work and capacity decisions changed", mandate),
        ("How the CAE handles management pressure", governance),
        ("What remains for independent work", assurance),
    ]


def first_brief_changes(state: dict) -> list[str]:
    first = state.get("first_brief")
    fields = ("mandate", "tracker", "ownership") + BRIEF_FIELDS + ("citations",)
    return [field for field in fields if first[field] != state["c"][field]] if first else []

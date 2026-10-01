# Northstar Cold Chain — The ERM Mandate

A zero-stakes, team-based Streamlit case in which students advise the chief audit executive (CAE) and prepare a board briefing. The app replaces the earlier question-chain version; that version is preserved in the dated QA archive. The existing presentation deck, deck guide, and paper activity have not been changed.

## Learning sequence

1. **CAE inbox:** Connect six incoming requests to the 20-hour advisory allocation; classify each as assurance, advisory, or management responsibility. Students receive request-by-request feedback after checking the role map.
2. **Commission the work:** The three advisory-capable requests map to two services that fit the current hours and a separate 30-hour tracker request requiring a resource decision. Students compare the 20- and 16-hour services, decide what happens to the tracker request, assign ownership, and review capacity feedback before moving on. The completed work product is not revealed yet.
3. **Board packet:** Eight weeks after launch, the CAE reviews records grouped by delivery, continuity/risk, the six-week advisory product, and executive requests. Every item is a named clickable box containing its context and full record. The monthly source report contains the 97.7% complete-network result. All records remain available in the briefing notebook.
4. **Board briefing:** Students consult the complete case notebook, resolve the CFO's assurance-label request and COO's authorization request, and assemble a briefing on delivery, continuity, the actual advisory work, and future independent work.
5. **Feedback:** Submission moves to a dedicated screen with explicit correct/partly correct/incorrect feedback, a separate exhibit-selection assessment, and a choice-dependent account of what the briefing made possible. A correct conclusion remains correct even if its citation set is incomplete. Revision is optional.

The reporting discovery is a scope mismatch: the green dashboard covers new-contract shipments only, while the approved monthly criterion covers the complete network. The underlying complete-network result is available in the packet, not announced during the mandate stage. The two advisory services can both be defensible. An unauthorized 30-hour tracker substitution displaces the selected service and leaves 50 of the 60 protected audit hours; it does not magically deliver both products.

“Companywide risk tracker” is the student-facing name for the ERM risk register: management's list of risks, ratings, owners, and actions. It is not the general ledger or a transaction log.

## Run locally

Python 3.12 is the tested runtime. From this directory:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run streamlit_app.py --server.address 127.0.0.1
```

A localhost address is for preview on the same computer. Student devices need a separately approved shared hosting arrangement.

## Test

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m py_compile streamlit_app.py board_app.py northstar/board_case.py northstar/board_logic.py northstar/board_progress.py
```

Tests cover both defensible mandates, commission-review gating, product-specific board claims, capacity substitution, evidence availability and selection, role-specific future assurance, dedicated feedback timing, revision, reset, and invalid progress links. The live app also needs a browser check before classroom use.

## Progress and privacy

Choices save immediately in a compact, versioned `progress` page-address parameter. Refresh restores the case; sharing the address shares choices. The app asks for no names, IDs, or free-text personal information. It uses no account, database, external API, LLM, or analytics service. Saved links are conveniences, not authenticated submissions. The old version's progress links start a fresh case with a notice because the activity structure has changed.

## Source boundary

The current paper case and instructor activity guide remain the source for the launch decision, board criteria, 80/60/20-hour capacity, 20- and 16-hour advisory services, separate 30-hour tracker request, management roles, and known evidence limitations. The eight-week dashboard, complete-network source report, executive requests to the CAE, and six-week work products are fictional app continuations. They do not alter the paper case. The first-launch `$265,000` figure is labeled expected incremental net profit, not an undefined “contribution.” No hidden worksheet instructions are used by the app.

## Visual approach

The blue `#003087`, red `#CE0037`, and neutral theme retains the prior visual identity without naming an institution. Abstract routing rings in the header suggest linked decisions. The interface uses text labels in addition to color, visible focus, responsive layouts, and reduced-motion support.

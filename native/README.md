# Northstar Cold Chain — The ERM Mandate

This final student-facing app uses native HTML, CSS and JavaScript. Its seven application files have no Python, Streamlit, Pyodide, WebAssembly runtime, installation step, external library, remote asset, account, database, analytics, or central saving service. The existing app at the repository root remains available; the native student route is `/northstar-erm-mandate/js/`.

The source branch is `native/northstar-erm-mandate`, based on `browser/stlite-northstar` at `7b5055f2f4e5c0dc73e797da0c5c8517409b342e`. Original Python teaching files, the existing browser implementation, server requirements/configuration, and original workflows are unchanged. Publication adds only `js/` on the existing `stlite-preview` branch. No Pages settings, credentials, redirects, repositories, other applications, or root hosting files are changed.

## Teaching and branching

`export.py` reads the unchanged Python case and captures its six actual rendering functions. The generated `content.js` contains the original assignment, criteria, forecasts, requests, commission instructions, record contexts/bodies, notebook, choices, draft briefing, feedback, and consequence language. Conditional feedback sentences are exported directly from the Python functions; native decision logic chooses and combines the appropriate records. Independent Python oracles check the results of JavaScript's choices and calculations.

Both 20-hour workshop and 16-hour training/coaching mandates remain defensible. The separate 30-hour tracker substitution displaces the selected service and leaves 50 protected audit hours. All three work products, ownership/self-review conflicts, possible future assurance subjects/providers, CFO/COO pressures, monthly scope mismatch, source-selection assessment, and first-brief comparison are retained. Correct conclusions stay correct when their evidence set is incomplete; evidence selection has its own feedback. No teaching changes from Receivables are applied here.

Native disclosures replace record popovers with clickable, keyboard-operable boxes containing the complete original records. All available records remain in the briefing notebook. Future packet content and assessment are never rendered before their original validation gates. The case remains zero-stakes and uses criterion-based feedback, not numeric points or an attempt counter. There were no app-owned image assets or download controls in the original; none are removed or replaced with new products.

## Progress and review

Small Back/Forward arrow boxes retain accessible labels, explanatory tooltips, focus outlines and 44-pixel touch targets. Back and the section trail review earlier reached pages without answer inputs, submissions, checks, revision, new feedback, or reset. Previously available source records and previously received feedback remain readable. Forward traverses reached pages only and stops at actual current progress, even after a valid answer. Original Open, Check, Review, Continue and Submit controls advance the lesson through its normal gates.

Actions enforce the same restriction independently of their HTML controls. The optional **Revise briefing (optional)** action exists only on the current feedback page. It keeps choices and the first submission, reopens an editable current briefing, and requires a new submission before feedback is available again. No facilitator-only alternative flow existed in this case.

The native app keeps the existing compressed version-5 `progress` URL schema. Old Python and stlite snapshots restore; native snapshots are readable by the unchanged Python validator. To open an old bookmark, retain `progress`/`view` while changing its path to `/northstar-erm-mandate/js/`. The old root remains available without a redirect. Earlier server bookmarks with later committed work open as read-only review of the highest earned page. Unsupported earlier schema versions, duplicate fields/parameters, invalid types, fabricated completion, oversize data and corrupt compressed tokens start a new case with a notice. Invalid future views return to current progress.

Request and answer order exactly match Python's string-seeded MT19937 shuffle, including imported seeds. Network percentages use Python-compatible ties-to-even `round(value * 10)` to save integer tenths. A bounded numeric-only `draft` parameter preserves literal valid or incomplete input, such as `97.`, without extending the original snapshot or accepting personal/free-form text. Old apps ignore this extra parameter and can restore the saved integer choice. An incomplete or invalid current numeric draft prevents submission. All other choices save immediately in the original state.

Refresh and copied bookmarks preserve drafts, reviews, selections, first submissions and shuffled order. Independent plain-address tabs/contexts start separately with no localStorage. Reset is available only at current progress and creates a new case/seed; previously copied bookmarks still describe their saved case. Existing fragments and unrelated URL parameters are retained. Sharing the address shares its anonymous choices; it is not an authenticated submission or central recovery system.

## Build and verification

From the repository root in Accounting Teaching Apps:

```bash
PY=/workspace/.cloud-setup/venvs/main/bin/python
"$PY" native/export.py
node --test native/tests/*.test.mjs
"$PY" -m unittest discover -s tests -v
"$PY" native/build.py
"$PY" native/tests/audit.py
"$PY" native/tests/browser.py
```

Python and Node are development tools only. `build.py --output PATH` copies the seven approved native files and writes a hash/byte manifest. It neither publishes nor modifies an existing site. Serve its output over ordinary HTTP/HTTPS; opening `file://` is unsupported. Browsers need ES modules, Web Crypto, BigInt and Compression Streams. Playwright uses `/usr/bin/chromium` when installed, otherwise its installed Chromium; `--chromium` selects an explicit executable.

The accepted native Receivables commit `a9dd736614db779b75389222ed8c251dc4d8db8f` informed the guarded-navigation, native-control and standard compression patterns. Northstar retains its own string-seeding and teaching rules.

See [VALIDATION.md](VALIDATION.md), [review/](review/) and the CI artifacts for independent comparisons, complete browser routes, branding checks and measurements. Local results do not establish network speed, school-device performance, broader browser compatibility, or capacity for 40–45 or 80–135 learners. Hosted browser QA remains blocked by the known Pages-host cloud restriction; publication is verified separately through GitHub deployment evidence, without using an alternate access route.

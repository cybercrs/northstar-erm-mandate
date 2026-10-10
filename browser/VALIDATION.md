# Northstar browser validation

## Scope and protection

Repository: `cybercrs/northstar-erm-mandate` (ID 1398888035). Audited main baseline: `11d3064dd429c0f2cf4c6a7255c3eaf61cd75dc5`. Remote branch inspection initially found only `main`; `browser/stlite-northstar` and `stlite-preview` were unused. No applicable AGENTS.md or local skill instructions were present in the repository or selected workspace. The saved environment's test/start instructions were followed.

The initial audit found only Streamlit plus Python standard-library dependencies, URL progress, and no external storage or services. Native `requirements.txt` pins Streamlit 1.64.0. No fundamental stlite incompatibility was found. `board_app.py`, `streamlit_app.py`, every `northstar/` module, server requirements, `.streamlit/`, and the original workflow remain byte-for-byte identical to main. No merge into main, server deployment change, repository creation, credential change, or access expansion occurred.

The runtime lock exactly matches the accepted Dock to Dollar static commit `80067eb6a77b6eba7f5f6c8974389301f8c7747c`. The build and review UI follow source `8a0f25a2bff6f9f1eacbc8ab132ababc94974c87`, with Northstar-specific progress and revision handling. The static application packages eight Python files under their original import paths, a dedicated worker per tab, and all local runtime assets.

## Native checks

- 40 original tests passed before changes under the saved Streamlit 1.60.0 runtime.
- 48 unit/AppTest checks passed after changes under native Streamlit 1.60.0, unpatched Streamlit 1.57.0, and the server's exact Streamlit 1.64.0 pin. The additional eight checks cover read-only review, mutation guards, forward limits, old bookmarks, future-view rejection, hidden future content, explicit revision and refresh.
- All Python source/tests compile; `git diff --check` passes.
- Ruff 0.15.0 fatal/error checks (`E9,F63,F7,F82`) pass for browser code and the added tests. New Python files use Ruff formatting.
- The build validates npm SHA-512 integrity and every fetched SHA-256 asset, using verified HTTPS. Static verification checks every packaged source, every locked runtime asset, and hashes for every generated static file. Server Streamlit is never installed into stlite.

## Actual browser evidence

The final local Chromium/Playwright run serves the generated build over loopback HTTP and blocks all external traffic with the browser test proxy. It verifies actual runtime versions from the worker: stlite 1.8.1 / patched Streamlit 1.57.0 / Python 3.13.2 / Pyodide 0.29.3. No TLS bypass, GitHub Pages proxy bypass, synthetic external submissions, or central saving is involved.

See `evidence/browser-results.json` for the final 13-check result and measured geometry; accompanying viewport screenshots cover the assignment, packet, deliberately wrong feedback, corrected feedback, both alternate routes, and narrow layouts. Screenshots capture Streamlit's visible scrolling viewport.

The walkthrough exercises all six pages, deliberately incorrect triage and briefing choices, repeated checks, each validation gate, commission drafts, full records/popovers, notebook access, first submission retention, optional correction and resubmission, every earlier read-only page, unchanged URL progress during repeated review, stable request ordering, refresh and copied bookmarks, invalid/duplicate progress links, future-view rejection, independent tabs and browser contexts, reset with a new seed, keyboard navigation/focus/tooltips, 44-pixel touch targets, 390-pixel and desktop layouts, and hosting under `/northstar-erm-mandate/`. It completes the workshop, training/coaching, and unauthorized tracker-substitution routes.

Earlier harness iterations failed on locator assumptions for selected selectboxes, hidden popovers, and citation-remove controls. Those assertions were corrected to inspect visible content and use keyboard citation removal; they did not produce application exceptions. The final report is the acceptance evidence. A pre-publication integrity check also detected native bytecode caches created by compile checks; the build now excludes those generated caches from the static manifest and publication.

## Publication and limits

GitHub connector repository metadata returned `has_pages: false` before publishing. Tools support Git pushes and CI reads but expose no Pages activation action; direct GitHub REST calls are blocked by the environment proxy. The separate static branch is prepared for manual Settings → Pages → Deploy from a branch → `stlite-preview` → `/(root)` activation. Recheck for an existing site before saving and stop if one appears.

Public deployment/hosted browser testing is not verified. The known cloud restriction on `cybercrs.github.io` is respected. CI links and exact remote source/static commits are reported separately at delivery.

This case has no numeric points or attempt counter; its original criterion-based feedback and initial briefing comparison are preserved. Browser review is view-only, while explicit revision remains available from current feedback and requires resubmission. Bookmarks are anonymous convenience snapshots, not authenticated submissions.

No classroom concurrency, capacity, mobile device fleet, school-network performance, or central recovery test was run. Local results do not establish capacity for 40–45 or 80–135 learners. The approximately 57 MiB runtime download and device-dependent Wasm startup remain classroom evaluation considerations.

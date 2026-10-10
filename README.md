# Northstar browser classroom edition

The activity runs in a dedicated Python/WebAssembly worker in each browser tab. It has no Python server, account, database, external API, central saving, or grade store. Decisions save in the existing anonymous `progress` URL parameter; sharing a bookmark shares the choices encoded in it. A new plain-address tab starts a separate case.

The live Streamlit app, `requirements.txt`, `.streamlit/`, and its existing test workflow are unchanged. The browser driver re-executes the unmodified `board_app.py` renderer and packages every `northstar/` module under its original path. It wraps navigation and review behavior without changing the source case or engine.

## Build and test

From the repository root in the saved Accounting Teaching Apps environment:

```bash
PY=/workspace/.cloud-setup/venvs/main/bin/python
"$PY" -m unittest discover -s tests -v
"$PY" -m browser.build
"$PY" -m browser.test_browser
"$PY" -m http.server 8765 --bind 127.0.0.1 --directory browser/dist
```

The loopback preview is for local development. Serve `browser/dist/` over HTTP or HTTPS; `file://` is unsupported. Playwright and Chromium are optional native test tools, not application dependencies. The harness defaults to `/usr/bin/chromium` if installed, otherwise Playwright's installed Chromium; `--chromium` selects an explicit executable.

The build uses certificate-verified HTTPS, the pilot's exact runtime lock, and hash checks on the npm archive and every fetched runtime asset. All JavaScript, fonts, CSS, WebAssembly, standard library and wheels are local in the output. No CDN or PyPI request is needed during execution. Optional `--runtime-archive` and `--asset-cache` inputs are still hash checked. The manifest records the hashes of all eight Python files.

## Runtime

This follows the accepted Dock to Dollar source `8a0f25a2bff6f9f1eacbc8ab132ababc94974c87` and static runtime `80067eb6a77b6eba7f5f6c8974389301f8c7747c`: stlite 1.8.1, bundled patched Streamlit 1.57.0, Pyodide 0.29.3, Python 3.13.2. Northstar's server pins Streamlit 1.64.0; server requirements are never installed into stlite. Actual browser execution checks the APIs used by the renderer, including `st.iframe`, popovers, numeric input, widget callbacks, URL parameters, and responsive layout. Licenses and third-party notices accompany the static build.

## Navigation and revision

The discreet boxed Back and Forward arrows at the upper right have native accessible names, explanatory tooltips, visible keyboard focus and 44-pixel touch targets. The six meaningful pages are assignment, inbox, commission, packet, briefing, and feedback.

Back and the sidebar trail open earlier reached pages in view-only mode: answer controls are disabled, and checking, submissions, revisions and reset are unavailable. Callback guards also reject mutations from review. Already received feedback and already available records remain readable. Forward visits reached pages only and stops at the actual current page. Existing Open, Check, Review, Continue and Submit controls retain the original validation gates. No navigation shortcut reveals the future handover record or briefing assessment.

The `view` URL parameter records only the viewed page; the existing version-5 `progress` schema keeps earned progress and choices. Drafts, shuffled request order, commission feedback and the initial submitted briefing survive review, refresh and bookmarks. Invalid future views return to the current page. Invalid progress links start a new case with the existing notice. Earlier server bookmarks with completed later work open as review of the highest earned page.

On the current feedback page, **Revise briefing (optional)** deliberately reopens an editable current briefing and requires resubmission before feedback becomes available again. It retains every choice and the original first submission. Review arrows never initiate a revision. Reset is available only on the actual current page and creates a new seed; old copied bookmarks still restore their saved case.

## Publishing

Use the separate `stlite-preview` branch in this same repository, root folder `/`. Do not merge the browser source branch into `main` or change the server deployment. Repository metadata reported `has_pages: false` during preparation; recheck Pages settings before activation. If an existing site appears, stop and report it instead of replacing it.

The exposed GitHub connector does not provide Pages activation, and direct `api.github.com` access is denied by the cloud proxy. Open repository **Settings → Pages → Build and deployment**; choose **Deploy from a branch**, select **stlite-preview** and **/(root)**, then **Save**. Wait for the Pages workflow to succeed before treating the advertised address as deployed. This environment's known `cybercrs.github.io` restriction must be respected; it cannot establish a hosted browser pass.

See [VALIDATION.md](VALIDATION.md) and `evidence/` for the local checks and screenshots. They establish local functional behavior, not classroom capacity for 40–45 or 80–135 simultaneous learners. The first visit downloads about 57 MiB of packaged runtime files; device performance and school-network caching need separate classroom evaluation.

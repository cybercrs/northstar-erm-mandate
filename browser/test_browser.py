"""Actual local stlite/Chromium lesson walkthroughs; no external traffic allowed."""

from __future__ import annotations
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import time
import traceback
import urllib.parse
from playwright.sync_api import sync_playwright, expect
from northstar.board_case import (
    CATEGORIES,
    REQUESTS,
    MANDATES,
    TRACKER_CHOICES,
    OWNERSHIP_CHOICES,
    BRIEF_OPTIONS,
    WORK_CLAIMS,
    RECORDS,
)
from northstar.board_logic import request_order, work_product
from northstar.board_progress import SnapshotError, decode

ROOT = Path(__file__).resolve().parents[1]
CHECKS = (
    "Actual Wasm runtime and desktop navigation",
    "Inbox wrong answers, repeats, validation gate",
    "Read-only review, keyboard, drafts, refresh, bookmarks",
    "Commission review gate and hidden future work product",
    "Complete packet records and briefing draft",
    "Wrong briefing and first submission",
    "Full read-only review with unchanged progress",
    "Explicit revision and correct feedback",
    "Second defensible mandate and unauthorized tracker route",
    "Independent tabs/contexts and reset",
    "Invalid links and future views",
    "Narrow viewport and subdirectory hosting",
    "No external traffic or execution errors",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chromium", default="/usr/bin/chromium")
    parser.add_argument("--dist", type=Path, default=ROOT / "browser/dist")
    parser.add_argument("--results", type=Path, default=ROOT / "browser/test-results")
    args = parser.parse_args()
    args.results.mkdir(parents=True, exist_ok=True)
    requests = []

    class Handler(SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            requests.append(self.path)
            if self.path.startswith("/northstar-erm-mandate/"):
                self.path = self.path[len("/northstar-erm-mandate") :]
            if self.path == "/favicon.ico":
                self.send_response(204)
                self.end_headers()
            else:
                super().do_GET()

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), partial(Handler, directory=str(args.dist))
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}"
    results = {
        "transport": "Actual generated static files; external traffic blocked by test proxy",
        "checks": [{"name": name, "status": "not-run"} for name in CHECKS],
        "console_errors": [],
        "page_errors": [],
        "external_requests": [],
    }
    active = 0

    def passed(i):
        results["checks"][i]["status"] = "passed"
        print("PASSED:", CHECKS[i], flush=True)

    def loaded(page):
        page.get_by_role("button", name="Back", exact=True).wait_for(timeout=120000)

    def wait_state(page, predicate, timeout=30):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            assert page.locator('[data-testid="stException"]').count() == 0, (
                page.locator("body").inner_text()
            )
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(page.url).query)
            try:
                state = decode(query.get("progress", [""])[0])
            except SnapshotError:
                state = None
            view = query.get("view", [None])[0]
            idle = page.locator('[data-test-script-state="notRunning"]').count() > 0
            if state is not None and idle and predicate(state, view):
                return state
            page.wait_for_timeout(50)
        raise AssertionError(f"Expected saved progress not rendered: {page.url}")

    def at_view(page, view):
        state = wait_state(page, lambda s, v: v == str(view))
        page.get_by_text(f"Page {view + 1} of 6", exact=True).wait_for()
        return state

    def click(page, label):
        page.locator('[data-testid="stMain"]').get_by_role(
            "button", name=label, exact=True
        ).click()

    def disabled(page, label):
        expect(page.get_by_role("button", name=label, exact=True)).to_be_disabled()

    def select(page, answer):
        radio = page.get_by_role("radio", name=answer, exact=True)
        page.locator("label").filter(has=radio).click()

    def set_role(page, position, value):
        page.locator('[data-testid="stSelectbox"]').filter(
            has=page.get_by_text(f"Service category for request {position}", exact=True)
        ).get_by_role("combobox").click()
        page.get_by_role("option", name=CATEGORIES[value], exact=True).click()

    def readonly(page):
        expect(
            page.get_by_text(
                "Review only. Return to your current page to continue the activity.",
                exact=True,
            )
        ).to_be_visible()
        for kind in ("radio", "combobox", "spinbutton"):
            for widget in (
                page.locator('[data-testid="stMain"]').get_by_role(kind).all()
            ):
                expect(widget).to_be_disabled()
        for label in (
            "Check the role map",
            "Review the commission plan",
            "Submit briefing for feedback",
            "Revise briefing (optional)",
            "Start a new case",
            "Open the CAE inbox",
        ):
            assert (
                page.locator('[data-testid="stMain"]')
                .get_by_role("button", name=label, exact=True)
                .count()
                == 0
            ), label
        disabled(page, "Start over")

    def layout(page, label):
        nav = page.locator(".st-key-browser_navigation")
        boxes = [
            nav.get_by_role("button", name=name, exact=True).bounding_box()
            for name in ("Back", "Forward")
        ]
        assert all(
            b and 44 <= b["width"] <= 45 and 44 <= b["height"] <= 45 for b in boxes
        ), boxes
        assert abs(boxes[0]["y"] - boxes[1]["y"]) <= 1, boxes
        main = page.locator(".block-container").bounding_box()
        assert boxes[0]["x"] > main["x"] + main["width"] / 2, (boxes, main)
        assert page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth"
        )
        results.setdefault("navigation_layout", {})[label] = boxes

    def commission(page, mandate, tracker):
        for field, options, value in (
            (
                "mandate",
                {i: f"{m['name']} — {m['hours']} hours" for i, m in MANDATES.items()},
                mandate,
            ),
            ("tracker", TRACKER_CHOICES, tracker),
            ("ownership", OWNERSHIP_CHOICES, 0),
        ):
            select(page, options[value])
            wait_state(page, lambda s, v: s["c"][field] == value)

    def citations(page, ids, route):
        box = page.locator('[data-testid="stMultiSelect"]').get_by_role("combobox")
        selected = at_view(page, 4)["c"]["citations"]
        for remaining in range(len(selected) - 1, -1, -1):
            box.focus()
            box.press("Backspace")
            wait_state(page, lambda s, v: len(s["c"]["citations"]) == remaining)
        wait_state(page, lambda s, v: s["c"]["citations"] == [])
        for id_ in ids:
            box.click()
            name = (
                work_product(
                    {
                        "mandate": route if route != 2 else 0,
                        "tracker": 2 if route == 2 else 0,
                    }
                )[0]
                if id_ == 7
                else RECORDS[id_]["title"]
            )
            page.get_by_role("option", name=name, exact=True).click()
            page.keyboard.press("Escape")
        wait_state(page, lambda s, v: s["c"]["citations"] == sorted(ids))

    def brief(page, route, wrong=False):
        number = page.get_by_role(
            "spinbutton", name="Monthly on-time delivery (%)", exact=True
        )
        number.fill("98.6" if wrong else "97.7")
        number.press("Enter")
        wait_state(
            page, lambda s, v: s["c"]["network_tenths"] == (986 if wrong else 977)
        )
        fields = {
            "headline": 0 if wrong else 1,
            "continuity": 0 if wrong else 1,
            "work_claim": 2 if wrong else 0,
            "communication": 1 if wrong else 0,
            "authority": 1 if wrong else 0,
            "scope": 0,
            "provider": 3 if wrong else 0,
        }
        for field, value in fields.items():
            select(
                page,
                (WORK_CLAIMS[route] if field == "work_claim" else BRIEF_OPTIONS[field])[
                    value
                ],
            )
            wait_state(page, lambda s, v: s["c"][field] == value)
        citations(page, [0] if wrong else [0, 1, 2, 3, 6, 7], route)

    def triage(page):
        state = at_view(page, 1)
        for position, id_ in enumerate(request_order(state["seed"]), start=1):
            set_role(page, position, REQUESTS[id_]["category"])
            wait_state(
                page, lambda s, v: s["c"]["roles"][id_] == REQUESTS[id_]["category"]
            )
        click(page, "Check the role map")
        wait_state(page, lambda s, v: s["roles_checked"])
        click(page, "Commission the advisory work")
        at_view(page, 2)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=args.chromium if Path(args.chromium).is_file() else None,
            headless=True,
            proxy={"server": "http://127.0.0.1:9", "bypass": "127.0.0.1,localhost"},
        )
        context = browser.new_context(viewport={"width": 1280, "height": 900})

        def watch(page):
            page.on("pageerror", lambda e: results["page_errors"].append(str(e)))

            def console(msg):
                if msg.text.startswith("BROWSER_VERSIONS="):
                    results["runtime"] = json.loads(msg.text.split("=", 1)[1])
                if msg.type == "error":
                    results["console_errors"].append(msg.text)

            page.on("console", console)
            page.on(
                "request",
                lambda r: (
                    results["external_requests"].append(r.url)
                    if r.url.startswith("http") and not r.url.startswith(url)
                    else None
                ),
            )
            return page

        page = watch(context.new_page())
        try:
            start = time.monotonic()
            page.goto(url)
            loaded(page)
            at_view(page, 0)
            results["initial_render_seconds"] = round(time.monotonic() - start, 2)
            assert results["runtime"]["streamlit"] == "1.57.0", results.get("runtime")
            assert results["runtime"]["iframe"]
            disabled(page, "Back")
            disabled(page, "Forward")
            layout(page, "desktop")
            page.screenshot(path=str(args.results / "assignment.png"), full_page=True)
            passed(0)
            active = 1
            click(page, "Open the CAE inbox")
            state = at_view(page, 1)
            disabled(page, "Forward")
            disabled(page, "Commission the advisory work")
            assert "97.7" not in page.locator('[data-testid="stMain"]').inner_text()
            ordered = request_order(state["seed"])
            for position, id_ in enumerate(ordered, start=1):
                set_role(page, position, (REQUESTS[id_]["category"] + 1) % 3)
                wait_state(
                    page,
                    lambda s, v: (
                        s["c"]["roles"][id_] == (REQUESTS[id_]["category"] + 1) % 3
                    ),
                )
            click(page, "Check the role map")
            wrong = wait_state(page, lambda s, v: s["roles_checked"])
            assert page.get_by_text("Incorrect", exact=True).count() == 6
            click(page, "Check the role map")
            assert at_view(page, 1) == wrong
            for position, id_ in enumerate(ordered, start=1):
                set_role(page, position, REQUESTS[id_]["category"])
                wait_state(
                    page, lambda s, v: s["c"]["roles"][id_] == REQUESTS[id_]["category"]
                )
            disabled(page, "Commission the advisory work")
            saved = at_view(page, 1)
            passed(1)
            active = 2
            order = page.locator(".case-card p").all_text_contents()
            click(page, "Back")
            assert at_view(page, 0) == saved
            readonly(page)
            bookmark = page.url
            page.reload()
            loaded(page)
            assert at_view(page, 0) == saved
            readonly(page)
            clone = watch(context.new_page())
            clone.goto(bookmark)
            loaded(clone)
            assert at_view(clone, 0) == saved
            readonly(clone)
            click(clone, "Forward")
            assert at_view(clone, 1) == saved
            expect(clone.locator(".case-card p")).to_have_text(order)
            clone.close()
            forward = page.get_by_role("button", name="Forward", exact=True)
            forward.focus()
            expect(forward).to_be_focused()
            assert forward.evaluate('e=>e.matches(":focus-visible")')
            assert forward.evaluate("e=>getComputedStyle(e).outlineWidth") == "2px"
            page.keyboard.press("Enter")
            assert at_view(page, 1) == saved
            back = page.get_by_role("button", name="Back", exact=True)
            back.focus()
            expect(back).to_be_focused()
            page.keyboard.press("Enter")
            at_view(page, 0)
            readonly(page)
            forward.focus()
            page.keyboard.press("Enter")
            assert at_view(page, 1) == saved
            back.hover()
            page.get_by_text(
                "Back: review the previous reached page. Earlier pages are read-only.",
                exact=True,
            ).wait_for()
            page.mouse.move(0, 0)
            passed(2)
            active = 3
            click(page, "Check the role map")
            wait_state(page, lambda s, v: s["roles_checked"])
            click(page, "Commission the advisory work")
            at_view(page, 2)
            commission(page, 0, 0)
            draft = at_view(page, 2)
            disabled(page, "Open the board packet")
            disabled(page, "Forward")
            assert (
                "Manager-validated workshop summary"
                not in page.locator('[data-testid="stMain"]').inner_text()
            )
            click(page, "Back")
            assert at_view(page, 1) == draft
            readonly(page)
            page.get_by_role("button", name="Back", exact=True).focus()
            page.keyboard.press("Tab")
            expect(
                page.get_by_role("button", name="Forward", exact=True)
            ).to_be_focused()
            page.keyboard.press("Enter")
            assert at_view(page, 2) == draft
            page.reload()
            loaded(page)
            assert at_view(page, 2) == draft
            click(page, "Review the commission plan")
            checked = wait_state(page, lambda s, v: s["commission_checked"])
            click(page, "Review the commission plan")
            assert at_view(page, 2) == checked
            passed(3)
            active = 4
            click(page, "Open the board packet")
            at_view(page, 3)
            for id_ in (1, 0, 2, 3, 4, 5, 7, 6):
                title = (
                    work_product(checked["c"])[0] if id_ == 7 else RECORDS[id_]["title"]
                )
                click(page, title)
                expect(
                    page.get_by_text("Why this record is here:", exact=False).filter(
                        visible=True
                    )
                ).to_be_visible()
                if id_ == 2:
                    expect(
                        page.get_by_text(
                            "97.7% for the complete network", exact=False
                        ).filter(visible=True)
                    ).to_be_visible()
                page.keyboard.press("Escape")
            page.screenshot(path=str(args.results / "packet.png"), full_page=True)
            click(page, "Prepare the board briefing")
            at_view(page, 4)
            disabled(page, "Submit briefing for feedback")
            disabled(page, "Forward")
            click(page, "Open case notebook")
            expect(
                page.get_by_role("heading", name="Case notebook", exact=True)
            ).to_be_visible()
            page.keyboard.press("Escape")
            brief(page, 0, wrong=True)
            draft = at_view(page, 4)
            assert draft["first_brief"] is None
            click(page, "Back")
            assert at_view(page, 3) == draft
            readonly(page)
            bookmark = page.url
            page.reload()
            loaded(page)
            assert at_view(page, 3) == draft
            click(page, "Forward")
            assert at_view(page, 4) == draft
            expect(
                page.get_by_role("spinbutton", name="Monthly on-time delivery (%)")
            ).to_have_value("98.6")
            passed(4)
            active = 5
            click(page, "Submit briefing for feedback")
            wrong = at_view(page, 5)
            assert wrong["first_brief"]["network_tenths"] == 986
            expect(
                page.get_by_role("heading", name="Board briefing review", exact=True)
            ).to_be_visible()
            assert page.get_by_text("Incorrect", exact=True).count() >= 5
            page.screenshot(
                path=str(args.results / "wrong-feedback.png"), full_page=True
            )
            passed(5)
            active = 6
            for target in range(4, -1, -1):
                click(page, "Back")
                assert at_view(page, target) == wrong
                readonly(page)
            for target in range(1, 6):
                click(page, "Forward")
                assert at_view(page, target) == wrong
            disabled(page, "Forward")
            page.reload()
            loaded(page)
            assert at_view(page, 5) == wrong
            passed(6)
            active = 7
            click(page, "Revise briefing (optional)")
            revision = at_view(page, 4)
            assert (
                not revision["brief_submitted"]
                and revision["first_brief"] == wrong["first_brief"]
            )
            disabled(page, "Forward")
            page.reload()
            loaded(page)
            assert at_view(page, 4) == revision
            brief(page, 0)
            click(page, "Submit briefing for feedback")
            final = at_view(page, 5)
            assert final["first_brief"] == wrong["first_brief"]
            assert final["c"]["network_tenths"] == 977
            assert page.get_by_text("Incorrect", exact=True).count() == 0
            page.screenshot(path=str(args.results / "completed.png"), full_page=True)
            final_bookmark = page.url
            passed(7)
            active = 8
            for mandate, tracker in ((1, 1), (0, 2)):
                route = 2 if tracker == 2 else mandate
                extra = watch(context.new_page())
                extra.goto(url)
                loaded(extra)
                click(extra, "Open the CAE inbox")
                triage(extra)
                commission(extra, mandate, tracker)
                click(extra, "Review the commission plan")
                wait_state(extra, lambda s, v: s["commission_checked"])
                if tracker == 2:
                    assert "50" in extra.locator('[data-testid="stMain"]').inner_text()
                click(extra, "Open the board packet")
                at_view(extra, 3)
                click(extra, "Prepare the board briefing")
                at_view(extra, 4)
                brief(extra, route)
                click(extra, "Submit briefing for feedback")
                done = at_view(extra, 5)
                assert (
                    done["c"]["mandate"] == mandate and done["c"]["tracker"] == tracker
                )
                results.setdefault("completed_routes", []).append(
                    {
                        "mandate": mandate,
                        "tracker": tracker,
                        "first_brief": done["first_brief"],
                    }
                )
                extra.screenshot(
                    path=str(args.results / f"route-{mandate}-{tracker}.png"),
                    full_page=True,
                )
                extra.close()
            passed(8)
            active = 9
            fresh = watch(context.new_page())
            fresh.goto(url)
            loaded(fresh)
            clean = at_view(fresh, 0)
            assert clean["c"]["roles"] == [-1] * 6 and clean["seed"] != final["seed"]
            fresh.close()
            other_context = browser.new_context()
            other = watch(other_context.new_page())
            other.goto(url)
            loaded(other)
            clean = at_view(other, 0)
            assert clean["seed"] != final["seed"]
            click(page, "Start a new case")
            reset = at_view(page, 0)
            assert (
                reset["first_brief"] is None
                and reset["c"]["roles"] == [-1] * 6
                and reset["seed"] != final["seed"]
            )
            page.reload()
            loaded(page)
            assert at_view(page, 0) == reset
            other.goto(final_bookmark)
            loaded(other)
            assert at_view(other, 5) == final
            other_context.close()
            passed(9)
            active = 10
            for suffix in (
                "?progress=invalid!&view=999",
                "?progress=a&progress=b&view=5",
            ):
                page.goto(url + "/" + suffix)
                loaded(page)
                assert at_view(page, 0)["c"]["roles"] == [-1] * 6
                expect(
                    page.get_by_text(
                        "This link could not restore your choices. A new case has started.",
                        exact=True,
                    )
                ).to_be_visible()
            click(page, "Open the CAE inbox")
            fresh = at_view(page, 1)
            page.goto(page.url.replace("view=1", "view=999"))
            loaded(page)
            assert at_view(page, 1) == fresh
            disabled(page, "Forward")
            passed(10)
            active = 11
            page.set_viewport_size({"width": 390, "height": 844})
            layout(page, "narrow")
            page.screenshot(path=str(args.results / "narrow-inbox.png"), full_page=True)
            page.goto(final_bookmark.replace(url, url + "/northstar-erm-mandate"))
            loaded(page)
            assert at_view(page, 5) == final
            layout(page, "narrow-feedback")
            page.screenshot(
                path=str(args.results / "narrow-feedback.png"), full_page=True
            )
            page.reload()
            loaded(page)
            assert at_view(page, 5) == final
            click(page, "Back")
            assert at_view(page, 4) == final
            readonly(page)
            assert urllib.parse.urlsplit(page.url).path == "/northstar-erm-mandate/"
            passed(11)
            active = 12
            assert not results["page_errors"], results["page_errors"]
            assert not results["console_errors"], results["console_errors"]
            assert not results["external_requests"], results["external_requests"]
            assert all(not path.startswith("/_stcore/") for path in requests)
            passed(12)
        except Exception:
            results["checks"][active].update(
                status="failed", error=traceback.format_exc()
            )
            results["body_on_failure"] = page.locator("body").inner_text()
            page.screenshot(path=str(args.results / "failure.png"), full_page=True)
        browser.close()
    server.shutdown()
    results["static_requests"] = sorted(set(requests))
    (args.results / "browser-results.json").write_text(
        json.dumps(results, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                k: v
                for k, v in results.items()
                if k not in ("static_requests", "body_on_failure")
            },
            indent=2,
        ),
        flush=True,
    )
    return 1 if any(check["status"] != "passed" for check in results["checks"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())

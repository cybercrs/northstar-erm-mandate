from copy import deepcopy
from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest
from helpers import complete_state
from browser.navigation import move, require_current, restore_view, resume_saved, revise
from northstar.board_progress import SnapshotError, defaults, decode, encode

APP = Path(__file__).resolve().parents[1] / "browser" / "app.py"


class BrowserNavigationTests(unittest.TestCase):
    def app(self, state=None, view=None):
        at = AppTest.from_file(str(APP), default_timeout=20)
        if state is not None:
            at.query_params["progress"] = encode(state)
        if view is not None:
            at.query_params["view"] = str(view)
        at.run()
        self.assertFalse(at.exception, list(at.exception))
        return at

    def click(self, at, label):
        next(b for b in at.button if b.label == label).click().run()
        self.assertFalse(at.exception, list(at.exception))

    def saved(self, at):
        return decode(at.query_params["progress"][0])

    def test_navigation_never_changes_progress(self):
        state = complete_state()
        original = deepcopy(state)
        view = 5
        for _ in range(3):
            for direction in (-1, 1):
                for _ in range(6):
                    view = move(state, view, direction)
        self.assertEqual(state, original)
        self.assertEqual(view, 5)
        for raw in ("6", "-1", "999", "invalid", None):
            self.assertEqual(restore_view(state, raw), 5)
        for raw in (True, 0, 2):
            with self.assertRaises(SnapshotError):
                move(state, 5, raw)

    def test_mutations_rejected_in_review(self):
        state = complete_state()
        for view in range(5):
            with self.assertRaises(SnapshotError):
                require_current(state, view)
            with self.assertRaises(SnapshotError):
                revise(state, view)
        self.assertEqual(state, complete_state())

    def test_revision_keeps_first_submission_and_requires_resubmission(self):
        state = complete_state()
        changed = revise(state, 5)
        self.assertEqual(changed["first_brief"], state["first_brief"])
        self.assertEqual(changed["c"], state["c"])
        self.assertEqual(changed["committed"], [1, 2, 3])
        self.assertFalse(changed["brief_submitted"])
        self.assertEqual(resume_saved(changed), changed)
        self.assertEqual(decode(encode(changed)), changed)
        self.assertEqual(restore_view(changed, "5"), 4)

    def test_legacy_server_bookmark_is_review_of_earned_progress(self):
        state = complete_state()
        state["stage"] = 1
        restored = resume_saved(state)
        self.assertEqual(restored["stage"], 5)
        self.assertEqual(restored["c"], state["c"])
        self.assertEqual(restore_view(restored, "1"), 1)
        self.assertEqual(resume_saved(defaults(2)), defaults(2))

    def test_all_review_pages_are_read_only_and_progress_is_exact(self):
        state = complete_state()
        for view in range(5):
            with self.subTest(view=view):
                at = self.app(state, view)
                self.assertEqual(self.saved(at), state)
                self.assertTrue(any("Review only" in info.value for info in at.info))
                for group in (at.radio, at.selectbox, at.number_input, at.multiselect):
                    self.assertTrue(all(widget.disabled for widget in group))
                labels = [b.label for b in at.button]
                for forbidden in (
                    "Open the CAE inbox",
                    "Check the role map",
                    "Review the commission plan",
                    "Submit briefing for feedback",
                    "Revise briefing (optional)",
                    "Start a new case",
                ):
                    self.assertNotIn(forbidden, labels)
                self.assertTrue(
                    next(b for b in at.button if b.label == "Start over").disabled
                )
                self.click(at, "Forward")
                self.assertEqual(self.saved(at), state)
                self.assertEqual(at.query_params["view"], [str(view + 1)])

    def test_frontier_arrow_does_not_advance_lesson(self):
        at = self.app(defaults(2), 999)
        self.assertEqual(at.query_params["view"], ["0"])
        self.assertTrue(next(b for b in at.button if b.label == "Forward").disabled)
        self.click(at, "Open the CAE inbox")
        saved = self.saved(at)
        self.assertEqual(saved["stage"], 1)
        self.assertTrue(next(b for b in at.button if b.label == "Forward").disabled)
        self.click(at, "Back")
        self.assertEqual(self.saved(at), saved)
        self.click(at, "Forward")
        self.assertEqual(self.saved(at), saved)
        self.assertEqual(at.query_params["view"], ["1"])

    def test_explicit_revision_only_from_feedback_and_refreshable(self):
        at = self.app(complete_state())
        self.click(at, "Revise briefing (optional)")
        saved = self.saved(at)
        self.assertEqual(saved["stage"], 4)
        self.assertFalse(saved["brief_submitted"])
        self.assertTrue(next(b for b in at.button if b.label == "Forward").disabled)
        restored = self.app(saved, 4)
        self.assertTrue(all(not radio.disabled for radio in restored.radio))
        self.click(restored, "Back")
        self.assertEqual(self.saved(restored), saved)
        self.click(restored, "Forward")
        self.click(restored, "Submit briefing for feedback")
        self.assertEqual(self.saved(restored)["stage"], 5)

    def test_no_future_results_on_incomplete_or_review_pages(self):
        at = self.app(defaults(2), 5)
        text = " ".join(m.value for m in at.markdown)
        self.assertNotIn("97.7", text)
        self.assertNotIn("Decision-by-decision feedback", text)
        state = complete_state()
        state["stage"] = 2
        state["committed"] = [1]
        state["brief_submitted"] = False
        at = self.app(state, 2)
        text = " ".join(m.value for m in at.markdown)
        self.assertNotIn("97.7", text)
        self.assertNotIn("Manager-validated workshop summary", text)


if __name__ == "__main__":
    unittest.main()

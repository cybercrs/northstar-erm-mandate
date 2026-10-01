from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest

from helpers import complete_state
from northstar.board_case import REQUESTS
from northstar.board_progress import decode, defaults, encode

APP = Path(__file__).resolve().parents[1] / "streamlit_app.py"


class AppTests(unittest.TestCase):
    def app(self, state=None, token=None):
        at = AppTest.from_file(str(APP), default_timeout=20)
        if state is not None:
            at.query_params["progress"] = encode(state)
        if token is not None:
            at.query_params["progress"] = token
        at.run()
        self.assertFalse(at.exception, list(at.exception))
        return at

    def button(self, at, label):
        next(button for button in at.button if button.label == label).click().run()
        self.assertFalse(at.exception, list(at.exception))

    def test_assignment_and_begin(self):
        at = self.app()
        self.assertIn("board meeting", at.header[0].value)
        self.button(at, "Open the CAE inbox")
        self.assertEqual(decode(at.query_params["progress"][0])["stage"], 1)

    def test_all_stages_render(self):
        final = complete_state()
        for stage in range(6):
            with self.subTest(stage=stage):
                state = final.copy()
                state["stage"] = stage
                self.app(state)

    def test_role_feedback_is_not_delayed_until_the_end(self):
        state = defaults(12)
        state["stage"] = 1
        at = self.app(state)
        text = " ".join(item.value for item in at.markdown)
        self.assertNotIn("different order", text.lower())
        self.assertIn("Check the role map to see feedback", text)
        self.assertIn("20 hours available for ERM advisory work", text)
        self.assertTrue(next(button for button in at.button if button.label == "Commission the advisory work").disabled)
        for id_, request in enumerate(REQUESTS):
            at.selectbox(key=f"widget_role_{id_}").select(request["category"]).run()
            self.assertFalse(at.exception, list(at.exception))
        self.button(at, "Check the role map")
        text = " ".join(item.value for item in at.markdown)
        self.assertIn("Request 1", text)
        self.assertNotIn("Model:", text)
        self.assertNotIn("Message 1", text)
        self.assertFalse(next(button for button in at.button if button.label == "Commission the advisory work").disabled)

    def test_commission_details_and_feedback_gate(self):
        state = complete_state()
        state["stage"] = 2
        state["committed"] = [1]
        state["commission_checked"] = False
        state["brief_submitted"] = False
        at = self.app(state)
        copy = " ".join(item.value for item in at.markdown)
        self.assertIn("three requests that could be advisory in principle", copy)
        self.assertIn("30 hours and cannot fit this authorization", copy)
        self.assertIn("dispatch, sales, and operations", copy)
        self.assertIn("four advisory hours unassigned", copy)
        self.assertTrue(next(button for button in at.button if button.label == "Open the board packet").disabled)
        self.button(at, "Review the commission plan")
        review = " ".join(item.value for item in at.markdown)
        self.assertIn("Correct", review)
        self.assertNotIn("Manager-validated workshop summary", review)
        self.assertIn("six-week handover will appear in the later board packet", review)
        self.assertFalse(next(button for button in at.button if button.label == "Open the board packet").disabled)

    def test_interactive_path_through_source_reconciliation(self):
        at = self.app()
        self.button(at, "Open the CAE inbox")
        for id_, request in enumerate(REQUESTS):
            at.selectbox(key=f"widget_role_{id_}").select(request["category"]).run()
        self.button(at, "Check the role map")
        self.button(at, "Commission the advisory work")
        at.radio(key="widget_mandate").set_value(1).run()
        at.radio(key="widget_tracker").set_value(1).run()
        at.radio(key="widget_ownership").set_value(0).run()
        self.button(at, "Review the commission plan")
        self.assertIn("Correct", " ".join(item.value for item in at.markdown))
        self.button(at, "Open the board packet")
        self.button(at, "Prepare the board briefing")
        at.number_input(key="widget_network_tenths").set_value(97.7).run()
        self.assertFalse(at.exception, list(at.exception))
        at.radio(key="widget_headline").set_value(1).run()
        at.multiselect(key="widget_citations").set_value([0, 1, 2, 3, 6, 7]).run()
        for field, value in (("continuity", 1), ("work_claim", 0), ("communication", 0), ("authority", 0), ("scope", 0), ("provider", 0)):
            at.radio(key=f"widget_{field}").set_value(value).run()
            self.assertFalse(at.exception, list(at.exception))
        self.button(at, "Submit briefing for feedback")
        saved = decode(at.query_params["progress"][0])
        self.assertEqual(saved["c"]["network_tenths"], 977)
        self.assertTrue(saved["brief_submitted"])
        self.assertEqual(saved["stage"], 5)
        self.assertIn("Board briefing review", at.header[0].value)
        self.assertEqual(len(at.radio), 0)
        self.assertEqual(len(at.number_input), 0)
        self.assertTrue(any(button.label == "Revise briefing (optional)" for button in at.button))
        self.assertIn("What did your briefing make possible?", " ".join(item.value for item in at.subheader))

    def test_packet_records_are_complete_and_available(self):
        state = complete_state()
        state["stage"] = 3
        state["committed"] = [1, 2]
        state["brief_submitted"] = False
        at = self.app(state)
        text = " ".join(item.value for item in at.markdown)
        self.assertEqual(len(at.get("popover")), 8)
        headings = " ".join(item.value for item in at.subheader)
        self.assertIn("Delivery criterion and performance records", headings)
        self.assertIn("Continuity and risk context", headings)
        self.assertIn("Six-week advisory work product", headings)
        self.assertIn("Executive requests requiring a response", headings)
        self.assertNotIn("Prepared for this board meeting", headings)
        self.assertNotIn("Source and reference records", headings)
        self.assertIn("Why this record is here", text)
        self.assertIn("97.7% for the complete network", text)
        self.assertIn("Neither request can be left unresolved", " ".join(item.value for item in at.markdown))
        self.assertNotIn("opened", decode(at.query_params["progress"][0])["c"])

    def test_briefing_does_not_tip_the_delivery_measure(self):
        state = complete_state()
        state["stage"] = 4
        at = self.app(state)
        self.assertFalse(any(button.label == "Return to the board packet" for button in at.button))
        self.assertEqual(at.number_input(key="widget_network_tenths").label, "Monthly on-time delivery (%)")
        self.assertFalse(at.number_input(key="widget_network_tenths").help)
        headline = at.radio(key="widget_headline")
        self.assertTrue(all("all-network" not in option.lower() for option in headline.options))
        self.assertNotIn("complete-network monthly figure you entered", " ".join(item.value for item in at.markdown))

    def test_network_result_is_discoverable_but_not_in_earlier_answers(self):
        state = complete_state()
        state["stage"] = 2
        at = self.app(state)
        self.assertNotIn("97.7", " ".join(item.value for item in at.markdown))
        state["stage"] = 4
        state["committed"] = [1, 2, 3]
        state["brief_submitted"] = False
        state["first_brief"] = None
        state["c"]["citations"] = []
        state["c"]["network_tenths"] = -1
        at = self.app(state)
        self.assertIn("97.7", " ".join(item.value for item in at.markdown))
        self.assertTrue(all("97.7" not in item.label for item in at.radio))

    def test_feedback_after_submission_not_before(self):
        state = complete_state()
        state["stage"] = 4
        state["committed"] = [1, 2, 3]
        state["brief_submitted"] = False
        state["first_brief"] = None
        at = self.app(state)
        self.assertNotIn("Delivery reporting", " ".join(item.value for item in at.markdown))
        self.button(at, "Submit briefing for feedback")
        self.assertEqual(decode(at.query_params["progress"][0])["stage"], 5)
        self.assertIn("Delivery reporting", " ".join(item.value for item in at.markdown))
        self.assertIn("Evidence selection", " ".join(item.value for item in at.markdown))
        self.assertIn("What did your briefing make possible?", " ".join(item.value for item in at.subheader))
        self.assertNotIn("No briefing decisions have changed", " ".join(item.value for item in at.markdown))
        self.assertTrue(decode(at.query_params["progress"][0])["brief_submitted"])

    def test_revision_requires_new_submission(self):
        at = self.app(complete_state())
        self.button(at, "Revise briefing (optional)")
        at.radio(key="widget_headline").set_value(0).run()
        self.assertFalse(at.exception, list(at.exception))
        saved = decode(at.query_params["progress"][0])
        self.assertFalse(saved["brief_submitted"])
        self.assertEqual(saved["first_brief"]["headline"], 1)
        self.assertNotIn("What did your briefing make possible?", " ".join(item.value for item in at.subheader))

    def test_invalid_old_progress_resets(self):
        at = self.app(token="invalid!")
        self.assertTrue(at.warning)
        self.assertEqual(decode(at.query_params["progress"][0])["stage"], 0)

    def test_reset_is_restorable(self):
        at = self.app(complete_state())
        self.button(at, "Start a new case")
        restored = self.app(token=at.query_params["progress"][0])
        self.assertIn("board meeting", restored.header[0].value)
        self.assertEqual(decode(restored.query_params["progress"][0])["c"]["roles"], [-1] * len(REQUESTS))


if __name__ == "__main__":
    unittest.main()

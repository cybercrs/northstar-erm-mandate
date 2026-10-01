import unittest

from helpers import complete_state
from northstar.board_case import MANDATES, RECORDS, REQUESTS
from northstar.board_logic import (
    briefing_consequences, capacity, commission_review, findings, first_brief_changes,
    owns_assurance_subject, request_order, work_product,
)


def outcome(state, title):
    return next(item for item in findings(state["c"]) if item.title == title)


class BoardLogicTests(unittest.TestCase):
    def test_inbox_to_commission_and_packet_source_chain(self):
        self.assertEqual([i for i, request in enumerate(REQUESTS) if request["category"] == 1], [1, 2, 4])
        self.assertEqual({item["hours"] for item in MANDATES.values()}, {16, 20})
        self.assertIn("30 hours", REQUESTS[4]["text"])
        self.assertIn("98.6%", RECORDS[0]["body"])
        self.assertIn("existing and new shipments", RECORDS[1]["body"])
        self.assertIn("97.7% for the complete network", RECORDS[2]["body"])
        self.assertIn("end-to-end exercise", RECORDS[3]["body"])
        self.assertIn("independent assurance", RECORDS[6]["body"])
        self.assertTrue(all(record["context"] and record["body"] for record in RECORDS.values()))

    def test_request_order_is_stable_and_complete(self):
        first = request_order(123)
        self.assertEqual(first, request_order(123))
        self.assertEqual(sorted(first), list(range(6)))
        self.assertNotEqual(first, request_order(456))

    def test_both_advisory_mandates_can_be_defended(self):
        for mandate in (0, 1):
            state = complete_state(mandate=mandate)
            self.assertEqual(outcome(state, "Mandate and confidence").status, "Advisory work identified")
            self.assertIn(("workshop", "coaching")[mandate], work_product(state["c"])[0].lower())
            self.assertEqual(commission_review(state["c"])[0].verdict, "Correct")

    def test_commission_feedback_marks_resource_and_role_crossings(self):
        state = complete_state(tracker=2, ownership=1)
        review = commission_review(state["c"])
        self.assertEqual([item.verdict for item in review], ["Correct", "Incorrect", "Incorrect"])
        self.assertIn("50", review[1].explanation)
        self.assertIn("self-review", review[2].explanation)

    def test_unauthorized_tracker_displaces_selected_service_and_audit_capacity(self):
        state = complete_state(tracker=2)
        self.assertEqual(capacity(state["c"])["protected_hours"], 50)
        self.assertFalse(capacity(state["c"])["chosen_service_delivered"])
        self.assertIn("not performed", work_product(state["c"])[1])
        self.assertEqual(outcome(state, "Mandate and capacity").status, "Unapproved substitution")

    def test_future_tracker_approval_does_not_start_work(self):
        state = complete_state(tracker=1)
        self.assertEqual(capacity(state["c"])["protected_hours"], 60)
        self.assertTrue(capacity(state["c"])["chosen_service_delivered"])
        self.assertTrue(capacity(state["c"])["tracker_pending"])

    def test_dashboard_headline_is_scored_separately_from_citations(self):
        state = complete_state()
        self.assertEqual(outcome(state, "Delivery reporting").status, "Supported")
        state["c"]["citations"] = [0, 1, 3]
        self.assertEqual(outcome(state, "Delivery reporting").status, "Supported")
        self.assertEqual(outcome(state, "Delivery reporting").verdict, "Correct")
        self.assertEqual(outcome(state, "Evidence selection").status, "Important source omitted")
        state["c"]["headline"] = 0
        self.assertEqual(outcome(state, "Delivery reporting").status, "Revise the headline")
        state["c"]["network_tenths"] = 986
        self.assertEqual(outcome(state, "Delivery reporting").status, "Source value needs checking")

    def test_continuity_claim_is_scored_separately_from_citations(self):
        state = complete_state()
        self.assertEqual(outcome(state, "Continuity evidence").status, "Appropriately qualified")
        state["c"]["citations"] = [0, 1, 2]
        self.assertEqual(outcome(state, "Continuity evidence").status, "Appropriately qualified")
        self.assertEqual(outcome(state, "Continuity evidence").verdict, "Correct")
        self.assertEqual(outcome(state, "Evidence selection").status, "Important source omitted")
        state["c"]["continuity"] = 0
        self.assertEqual(outcome(state, "Continuity evidence").status, "Inference exceeds the record")

    def test_evidence_selection_distinguishes_sufficient_missing_and_extra(self):
        state = complete_state()
        self.assertEqual(outcome(state, "Evidence selection").status, "Focused and sufficient")
        self.assertEqual(outcome(state, "Evidence selection").verdict, "Correct")
        state["c"]["citations"].remove(7)
        self.assertEqual(outcome(state, "Evidence selection").status, "Important source omitted")
        state = complete_state(mandate=1, scope=1)
        state["c"]["citations"].append(4)
        self.assertEqual(outcome(state, "Evidence selection").status, "Selection needs editing")
        state = complete_state(mandate=0, scope=0)
        state["c"]["citations"].extend((4, 5))
        self.assertEqual(outcome(state, "Evidence selection").status, "Focused and sufficient")

    def test_consequence_debrief_changes_with_decisions(self):
        sound = " ".join(body for _, body in briefing_consequences(complete_state()["c"]))
        self.assertIn("board can now see", sound)
        self.assertIn("manager-validated workshop", sound)
        self.assertIn("decline the CFO's request", sound)
        compromised = complete_state(mandate=1, tracker=2, ownership=2, scope=1, provider=0)
        compromised["c"]["communication"] = 1
        compromised["c"]["authority"] = 1
        text = " ".join(body for _, body in briefing_consequences(compromised["c"]))
        self.assertIn("not delivered", text)
        self.assertIn("50 of its 60", text)
        self.assertIn("Accepting the CFO's", text)
        self.assertIn("Signing the COO's", text)
        self.assertIn("different internal-audit team", text)
        withheld = complete_state()
        withheld["c"]["communication"] = 2
        blocked = briefing_consequences(withheld["c"])[0][1]
        self.assertIn("keep that exception from reaching the board", blocked)
        self.assertNotIn("board can now see", blocked)

    def test_relabeling_and_silence_are_both_unhelpful(self):
        state = complete_state()
        state["c"]["communication"] = 1
        self.assertEqual(outcome(state, "Mandate and confidence").status, "Assurance overstated")
        state["c"]["communication"] = 2
        self.assertEqual(outcome(state, "Mandate and confidence").status, "Useful observation withheld")

    def test_work_claim_depends_on_the_service_actually_delivered(self):
        for mandate in (0, 1):
            state = complete_state(mandate=mandate)
            self.assertEqual(outcome(state, "Advisory work product").status, "Claim matches work performed")
            state["c"]["work_claim"] = 1
            self.assertEqual(outcome(state, "Advisory work product").status, "Claim does not match this mandate")
        state = complete_state(tracker=2)
        self.assertEqual(outcome(state, "Advisory work product").status, "Claim matches work performed")
        state["c"]["work_claim"] = 2
        self.assertEqual(outcome(state, "Advisory work product").status, "Operating claim unsupported")

    def test_debrief_detects_changed_mandate_even_when_claim_index_is_same(self):
        state = complete_state()
        state["c"]["mandate"] = 1
        self.assertIn("mandate", first_brief_changes(state))

    def test_management_ownership_conflicts_with_later_assurance_by_subject(self):
        reporting = complete_state(ownership=1, scope=0, provider=0)
        self.assertTrue(owns_assurance_subject(reporting["c"]))
        self.assertEqual(outcome(reporting, "Future independent view").status, "Self-review unresolved")
        reporting["c"]["provider"] = 1
        self.assertEqual(outcome(reporting, "Future independent view").status, "Credible route proposed")
        continuity = complete_state(ownership=2, scope=1, provider=0)
        self.assertTrue(owns_assurance_subject(continuity["c"]))
        self.assertEqual(outcome(continuity, "Future independent view").status, "Self-review unresolved")
        continuity["c"]["scope"] = 0
        self.assertFalse(owns_assurance_subject(continuity["c"]))

    def test_board_sentence_does_not_undo_earlier_ownership(self):
        state = complete_state(ownership=1)
        self.assertEqual(outcome(state, "Management accountability").status, "Agreement contradicts briefing")

    def test_existing_financial_opinion_is_not_dispatch_assurance(self):
        state = complete_state(provider=3)
        self.assertEqual(outcome(state, "Future independent view").status, "Provider not credible")


if __name__ == "__main__":
    unittest.main()

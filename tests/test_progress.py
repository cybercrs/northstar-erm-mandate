import base64
from copy import deepcopy
import json
import unittest
import zlib

from helpers import complete_state
from northstar.board_case import REQUESTS
from northstar.board_logic import ready
from northstar.board_progress import (
    SnapshotError, check_commission, check_roles, commit, decode, defaults, edit_choice, encode,
    navigate, submit_brief, validate,
)


def unchecked(value):
    return base64.urlsafe_b64encode(zlib.compress(json.dumps(value).encode())).decode().rstrip("=")


class ProgressTests(unittest.TestCase):
    def test_fresh_and_completed_round_trip(self):
        for state in (defaults(0), complete_state()):
            self.assertEqual(decode(encode(state)), state)

    def test_role_order_and_partial_choice_survive_refresh(self):
        state = defaults(22)
        state["stage"] = 1
        state = edit_choice(state, "roles", 1, 2)
        self.assertEqual(decode(encode(state)), state)

    def test_checking_role_map_requires_every_answer(self):
        with self.assertRaises(SnapshotError):
            check_roles(defaults())
        state = defaults()
        state["stage"] = 1
        state["c"]["roles"] = [request["category"] for request in REQUESTS]
        self.assertTrue(check_roles(state)["roles_checked"])

    def test_commission_review_required_before_advancing(self):
        state = defaults(9)
        state["stage"] = 2
        state["committed"] = [1]
        state["roles_checked"] = True
        state["c"]["roles"] = [request["category"] for request in REQUESTS]
        state["c"].update(mandate=1, tracker=0, ownership=0)
        with self.assertRaises(SnapshotError):
            commit(state, 2)
        state = check_commission(state)
        self.assertTrue(ready(state, 2))
        self.assertFalse(edit_choice(state, "tracker", 2)["commission_checked"])

    def test_packet_records_can_be_cited_without_extra_opening_step(self):
        state = complete_state()
        state = navigate(state, 4)
        self.assertEqual(edit_choice(state, "citations", [0, 5])["c"]["citations"], [0, 5])
        with self.assertRaises(SnapshotError):
            edit_choice(state, "citations", [0, 0])

    def test_revision_invalidates_later_commit_but_preserves_initial_brief(self):
        state = complete_state()
        first = deepcopy(state["first_brief"])
        state = edit_choice(state, "mandate", 1)
        self.assertEqual(state["committed"], [1])
        self.assertEqual(state["stage"], 2)
        self.assertEqual(state["first_brief"], first)
        self.assertFalse(state["commission_checked"])
        self.assertFalse(state["brief_submitted"])
        state = check_commission(state)
        state = commit(state, 2)
        self.assertEqual(state["stage"], 3)

    def test_brief_edit_requires_resubmission(self):
        state = navigate(complete_state(), 4)
        state = edit_choice(state, "headline", 0)
        self.assertFalse(state["brief_submitted"])
        self.assertEqual(state["committed"], [1, 2, 3])
        self.assertEqual(state["first_brief"]["headline"], 1)
        self.assertFalse(ready(state, 4))
        resubmitted = submit_brief(state)
        self.assertTrue(resubmitted["brief_submitted"])
        self.assertEqual(resubmitted["stage"], 5)

    def test_reject_unknown_fields_and_bad_types(self):
        for mutate in (
            lambda s: s.update(name="student"),
            lambda s: s.update(seed=True),
            lambda s: s.update(stage=6),
            lambda s: s.update(v=2),
            lambda s: s["c"].update(headline=True),
            lambda s: s["c"].update(opened=[0, 6]),
            lambda s: s["c"].update(citations=[1, 1]),
        ):
            state = defaults()
            mutate(state)
            with self.assertRaises(SnapshotError):
                decode(unchecked(state))

    def test_reject_skipped_and_fabricated_completion(self):
        state = defaults()
        state["stage"] = 5
        with self.assertRaises(SnapshotError):
            validate(state)
        state = defaults()
        state["committed"] = [1]
        with self.assertRaises(SnapshotError):
            validate(state)

    def test_reject_corrupt_links(self):
        for token in ("", "not a token", "x" * 6001, "AAAA", encode(defaults()) + "="):
            with self.subTest(token=token[:20]), self.assertRaises(SnapshotError):
                decode(token)

    def test_reject_decompression_bomb_and_duplicate_keys(self):
        bomb = base64.urlsafe_b64encode(zlib.compress(b" " * 100000)).decode().rstrip("=")
        with self.assertRaises(SnapshotError):
            decode(bomb)
        raw = json.dumps(defaults())[:-1] + ',"stage":0}'
        duplicate = base64.urlsafe_b64encode(zlib.compress(raw.encode())).decode().rstrip("=")
        with self.assertRaises(SnapshotError):
            decode(duplicate)

    def test_no_scores_or_identity_in_snapshot(self):
        token = encode(complete_state())
        self.assertLess(len(token), 1200)
        saved = decode(token)
        self.assertNotIn("score", saved)
        self.assertNotIn("name", saved)


if __name__ == "__main__":
    unittest.main()

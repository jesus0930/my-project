import unittest
from acceptance_gate import evaluate, REQUIRED


def all_goals(state="NOT_VERIFIED"):
    return {"goals": {name: {"state": state, "evidence": []} for name in REQUIRED}}


class GoalGateTests(unittest.TestCase):
    def test_missing_goal_blocks(self):
        with self.assertRaisesRegex(ValueError, "Goal set"):
            evaluate({"goals": {}})

    def test_all_missing(self):
        r = evaluate(all_goals())
        self.assertEqual(r["overall"], "NOT_COMPLETED")
        self.assertEqual(len(r["unmet_goals"]), len(REQUIRED))

    def test_mixed_partial(self):
        v = all_goals()
        v["goals"][REQUIRED[0]]["state"] = "PARTIAL"
        self.assertEqual(evaluate(v)["overall"], "NOT_COMPLETED")

    def test_no_verified_without_evidence(self):
        with self.assertRaisesRegex(ValueError, "requires evidence"):
            evaluate(all_goals("VERIFIED"))

    def test_all_verified_still_not_certified(self):
        s = all_goals("VERIFIED")
        for v in s["goals"].values():
            v["evidence"] = ["self-reported"]
        self.assertEqual(evaluate(s)["overall"], "REVIEW_REQUIRED")

    def test_self_asserted_approval_does_not_certify(self):
        s = all_goals("VERIFIED")
        for v in s["goals"].values():
            v["evidence"] = ["self-reported"]
        self.assertEqual(evaluate(s, {"decision": "APPROVED", "reviewer": "self"})["overall"], "REVIEW_REQUIRED")

    def test_invalid_evidence(self):
        s = all_goals()
        s["goals"][REQUIRED[0]]["evidence"] = [None]
        with self.assertRaisesRegex(ValueError, "Invalid evidence"):
            evaluate(s)


if __name__ == "__main__":
    unittest.main()

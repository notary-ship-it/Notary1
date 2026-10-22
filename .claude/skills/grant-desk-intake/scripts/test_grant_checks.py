#!/usr/bin/env python3
"""Regression tests for grant_checks.

The example budget carries three deliberate defects, and the fourth
finding is the column error the first one cascades into. If this file
stops passing, the arithmetic layer has drifted from the page's.

    python3 test_grant_checks.py
"""
import sys
import unittest

from grant_checks import check_budget, check_narrative, parse_delimited, to_num

EXAMPLE_BUDGET = "\n".join([
    "Line item,Category,Federal request,Non-federal match,Total",
    "Program Director 0.50 FTE,Personnel,42000,0,42000",
    "Literacy Coordinator 1.00 FTE,Personnel,52000,0,52000",
    "Family Case Manager 1.00 FTE,Personnel,48000,6000,54000",
    "Fringe benefits at 22%,Fringe,31240,1320,32560",
    "Curriculum and student materials,Supplies,18500,0,19500",   # planted: cross-foot
    "Staff mileage,Travel,3200,0,3200",
    "Evaluation consultant,Contractual,24000,0,24000",
    "Space and utilities (donated),Other,0,22000,22000",
    "Volunteer tutor time (in-kind),Other,0,14000,14000",
    "Total direct costs,,218940,43320,262260",
    "Indirect costs at 12%,Indirect,26273,0,26273",              # planted: over cap
    "TOTAL PROJECT COST,,245213,43320,288533",                   # planted: 15% match
])

NOTICE = dict(cap=10, match_pct=25, ceiling=500000, floor=150000)


def claims(findings, severity=None):
    return [f["claim"] for f in findings
            if severity is None or f["severity"] == severity]


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.rows = parse_delimited(EXAMPLE_BUDGET)
        self.findings = check_budget(self.rows, **NOTICE)

    def test_parses_shape(self):
        self.assertEqual(len(self.rows), 13)

    def test_row_cross_foot_caught(self):
        hits = [c for c in claims(self.findings, "fix") if "cross-foot" in c]
        self.assertEqual(len(hits), 1)
        self.assertIn("$18,500", hits[0])
        self.assertIn("$19,500", hits[0])
        self.assertIn("$1,000", hits[0])

    def test_column_footing_caught(self):
        hits = [c for c in claims(self.findings, "blocker") if "does not foot" in c]
        self.assertEqual(len(hits), 1)
        self.assertIn("$263,260", hits[0])
        self.assertIn("$262,260", hits[0])

    def test_indirect_over_cap(self):
        hits = [c for c in claims(self.findings, "blocker") if "Indirect costs are" in c]
        self.assertEqual(len(hits), 1)
        self.assertIn("12%", hits[0])
        self.assertIn("10%", hits[0])

    def test_match_shortfall(self):
        hits = [c for c in claims(self.findings, "blocker") if "non-federal match" in c]
        self.assertEqual(len(hits), 1)
        self.assertIn("15%", hits[0])
        self.assertIn("25%", hits[0])

    def test_request_inside_award_range(self):
        hits = [c for c in claims(self.findings, "clean") if "award range" in c]
        self.assertEqual(len(hits), 1)
        self.assertIn("$245,213", hits[0])

    def test_fringe_base_excludes_travel(self):
        """22% of personnel is exactly right; a base that swept in mileage
        would report a false discrepancy."""
        self.assertEqual([c for c in claims(self.findings) if "Fringe" in c], [])

    def test_exactly_three_blockers(self):
        self.assertEqual(len(claims(self.findings, "blocker")), 3)


class NumberTests(unittest.TestCase):
    def test_money_cells(self):
        self.assertEqual(to_num("$1,234.50"), 1234.5)
        self.assertEqual(to_num("(500)"), -500)
        self.assertEqual(to_num("12%"), 12)
        self.assertIsNone(to_num("Personnel"))
        self.assertIsNone(to_num(""))


class NarrativeTests(unittest.TestCase):
    def test_over_page_limit(self):
        text = "word " * 9000  # ~36 pages double-spaced
        hits = [c for c in claims(check_narrative(text, page_limit=30), "blocker")]
        self.assertTrue(any("36 pages" in c for c in hits))

    def test_placeholder_is_a_blocker(self):
        f = check_narrative("The evaluator will be TBD.", page_limit=30)
        self.assertTrue(any("Placeholder" in c for c in claims(f, "blocker")))

    def test_within_limit_is_clean(self):
        f = check_narrative("word " * 1000, page_limit=30)
        self.assertTrue(any("headroom" in c for c in claims(f, "clean")))
        self.assertEqual(claims(f, "blocker"), [])

    def test_missing_sub_elements_noted(self):
        f = check_narrative("We will track attendance.", page_limit=30,
                            sub_elements=["baseline values", "data collection methods"])
        self.assertTrue(any("word scan" in c for c in claims(f, "note")))


if __name__ == "__main__":
    unittest.main(verbosity=2)

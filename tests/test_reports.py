"""Tests for the ticket report totals and category breakdowns."""

import unittest

from campusflow.reports import generate_report


def make_ticket(status, priority):
    """Build the minimal ticket shape a report needs."""
    return {"status": status, "priority": priority}


class ReportTests(unittest.TestCase):
    def test_total_count(self):
        tickets = [
            make_ticket("open", "critical"),
            make_ticket("resolved", "low"),
            make_ticket("open", "critical"),
        ]
        self.assertEqual(generate_report(tickets)["total"], 3)

    def test_breakdown_by_status(self):
        tickets = [
            make_ticket("open", "low"),
            make_ticket("open", "low"),
            make_ticket("in_progress", "low"),
            make_ticket("resolved", "low"),
        ]

        report = generate_report(tickets)

        self.assertEqual(
            report["by_status"],
            {"open": 2, "in_progress": 1, "resolved": 1},
        )

    def test_breakdown_by_priority(self):
        tickets = [
            make_ticket("open", "critical"),
            make_ticket("open", "high"),
            make_ticket("open", "high"),
            make_ticket("open", "medium"),
            make_ticket("open", "low"),
        ]

        report = generate_report(tickets)

        self.assertEqual(
            report["by_priority"],
            {"critical": 1, "high": 2, "medium": 1, "low": 1},
        )

    def test_empty_report_keeps_every_category(self):
        report = generate_report([])

        self.assertEqual(report["total"], 0)
        self.assertEqual(
            report["by_status"],
            {"open": 0, "in_progress": 0, "resolved": 0},
        )
        self.assertEqual(
            report["by_priority"],
            {"critical": 0, "high": 0, "medium": 0, "low": 0},
        )

    def test_zero_categories_are_still_reported(self):
        report = generate_report([make_ticket("open", "low")])

        self.assertIn("in_progress", report["by_status"])
        self.assertEqual(report["by_status"]["in_progress"], 0)
        self.assertIn("critical", report["by_priority"])
        self.assertEqual(report["by_priority"]["critical"], 0)


if __name__ == "__main__":
    unittest.main()

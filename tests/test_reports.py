
import unittest

from campusflow.reports import generate_report


class ReportTests(unittest.TestCase):
    # Verify report totals and empty-state handling.
    def test_empty_report(self):
        report = generate_report([])

        self.assertEqual(report["total"], 0)
        self.assertEqual(report["by_status"]["open"], 0)
        self.assertEqual(report["by_priority"]["critical"], 0)

    def test_report_counts(self):
        tickets = [
            {"status": "open", "priority": "critical"},
            {"status": "resolved", "priority": "low"},
            {"status": "open", "priority": "critical"},
        ]

        report = generate_report(tickets)

        self.assertEqual(report["total"], 3)
        self.assertEqual(report["by_status"]["open"], 2)
        self.assertEqual(report["by_status"]["resolved"], 1)
        self.assertEqual(report["by_priority"]["critical"], 2)
        self.assertEqual(report["by_priority"]["low"], 1)


if __name__ == "__main__":
    unittest.main()


import unittest

from campusflow.workflow import (
    assign_ticket,
    update_status,
    reopen_ticket,
    get_work_queue,
)


def make_ticket(ticket_id, priority="low", status="open", assigned_to=None):
    # Build a ticket fixture for workflow tests.
    return {
        "id": ticket_id,
        "title": "Test ticket",
        "category": "Software",
        "urgency": "low",
        "affected_users": 1,
        "priority": priority,
        "status": status,
        "assigned_to": assigned_to,
    }


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tickets = [make_ticket("T001")]

    def test_assign_ticket(self):
        ticket = assign_ticket(self.tickets, "T001", "Ada")
        self.assertEqual(ticket["assigned_to"], "Ada")

    def test_reject_blank_staff_name(self):
        with self.assertRaises(ValueError):
            assign_ticket(self.tickets, "T001", " ")

    def test_unassigned_ticket_cannot_start(self):
        with self.assertRaises(ValueError):
            update_status(self.tickets, "T001", "in_progress")
        self.assertEqual(self.tickets[0]["status"], "open")

    def test_valid_lifecycle(self):
        assign_ticket(self.tickets, "T001", "Ada")
        update_status(self.tickets, "T001", "in_progress")
        update_status(self.tickets, "T001", "resolved")
        self.assertEqual(self.tickets[0]["status"], "resolved")

    def test_resolved_ticket_requires_reopening(self):
        ticket = self.tickets[0]
        ticket["status"] = "resolved"

        with self.assertRaises(ValueError):
            assign_ticket(self.tickets, "T001", "Ada")

        reopen_ticket(self.tickets, "T001")
        self.assertEqual(ticket["status"], "open")

    def test_unknown_ticket_rejected(self):
        with self.assertRaises(ValueError):
            assign_ticket(self.tickets, "T999", "Ada")

    def test_queue_priority_and_numeric_id_order(self):
        self.tickets = [
            make_ticket("T010", "high"),
            make_ticket("T002", "critical"),
            make_ticket("T001", "high"),
            make_ticket("T003", "low", "in_progress"),
        ]

        queue = get_work_queue(self.tickets)

        self.assertEqual(
            [ticket["id"] for ticket in queue],
            ["T002", "T001", "T010"],
        )


if __name__ == "__main__":
    unittest.main()

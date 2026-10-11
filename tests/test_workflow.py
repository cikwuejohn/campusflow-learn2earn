"""Tests for ticket assignment, status lifecycle, and the work queue."""

import unittest

from campusflow.workflow import (
    assign_ticket,
    update_status,
    reopen_ticket,
    get_work_queue,
)


def make_ticket(ticket_id, priority="low", status="open", assigned_to=None):
    """Build a ticket fixture for workflow tests."""
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


class AssignmentTests(unittest.TestCase):
    def setUp(self):
        self.tickets = [make_ticket("T001")]

    def test_assign_ticket_sets_staff(self):
        ticket = assign_ticket(self.tickets, "T001", "Ada")
        self.assertEqual(ticket["assigned_to"], "Ada")

    def test_assign_ticket_trims_whitespace(self):
        ticket = assign_ticket(self.tickets, "T001", "  Ada Lovelace  ")
        self.assertEqual(ticket["assigned_to"], "Ada Lovelace")

    def test_assign_rejects_empty_staff_name(self):
        with self.assertRaises(ValueError):
            assign_ticket(self.tickets, "T001", "")
        self.assertIsNone(self.tickets[0]["assigned_to"])

    def test_assign_rejects_whitespace_only_staff_name(self):
        with self.assertRaises(ValueError):
            assign_ticket(self.tickets, "T001", "   ")
        self.assertIsNone(self.tickets[0]["assigned_to"])

    def test_assign_rejects_non_string_staff_name(self):
        with self.assertRaises(ValueError):
            assign_ticket(self.tickets, "T001", None)
        with self.assertRaises(ValueError):
            assign_ticket(self.tickets, "T001", 42)

    def test_assign_unknown_ticket_raises(self):
        with self.assertRaises(ValueError):
            assign_ticket(self.tickets, "T999", "Ada")

    def test_assign_resolved_ticket_requires_reopening(self):
        self.tickets[0]["status"] = "resolved"
        with self.assertRaises(ValueError):
            assign_ticket(self.tickets, "T001", "Ada")
        self.assertIsNone(self.tickets[0]["assigned_to"])


class StatusLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tickets = [make_ticket("T001")]

    def test_new_ticket_starts_open(self):
        self.assertEqual(self.tickets[0]["status"], "open")

    def test_valid_lifecycle(self):
        assign_ticket(self.tickets, "T001", "Ada")
        update_status(self.tickets, "T001", "in_progress")
        self.assertEqual(self.tickets[0]["status"], "in_progress")

        update_status(self.tickets, "T001", "resolved")
        self.assertEqual(self.tickets[0]["status"], "resolved")

    def test_unassigned_ticket_cannot_start(self):
        with self.assertRaises(ValueError):
            update_status(self.tickets, "T001", "in_progress")
        self.assertEqual(self.tickets[0]["status"], "open")

    def test_cannot_skip_from_open_to_resolved(self):
        assign_ticket(self.tickets, "T001", "Ada")
        with self.assertRaises(ValueError):
            update_status(self.tickets, "T001", "resolved")
        self.assertEqual(self.tickets[0]["status"], "open")

    def test_cannot_move_backwards(self):
        assign_ticket(self.tickets, "T001", "Ada")
        update_status(self.tickets, "T001", "in_progress")
        with self.assertRaises(ValueError):
            update_status(self.tickets, "T001", "open")
        self.assertEqual(self.tickets[0]["status"], "in_progress")

    def test_invalid_status_value_rejected(self):
        assign_ticket(self.tickets, "T001", "Ada")
        with self.assertRaises(ValueError):
            update_status(self.tickets, "T001", "closed")

    def test_unknown_ticket_status_change_raises(self):
        with self.assertRaises(ValueError):
            update_status(self.tickets, "T999", "in_progress")

    def test_resolved_ticket_cannot_change_status(self):
        assign_ticket(self.tickets, "T001", "Ada")
        update_status(self.tickets, "T001", "in_progress")
        update_status(self.tickets, "T001", "resolved")

        with self.assertRaises(ValueError):
            update_status(self.tickets, "T001", "open")
        self.assertEqual(self.tickets[0]["status"], "resolved")


class ReopenTests(unittest.TestCase):
    def setUp(self):
        self.tickets = [make_ticket("T001", status="resolved")]

    def test_reopen_resolved_ticket(self):
        ticket = reopen_ticket(self.tickets, "T001")
        self.assertEqual(ticket["status"], "open")

    def test_reopen_unknown_ticket_raises(self):
        with self.assertRaises(ValueError):
            reopen_ticket(self.tickets, "T999")

    def test_reopen_non_resolved_ticket_raises(self):
        self.tickets.append(make_ticket("T002", status="open"))
        with self.assertRaises(ValueError):
            reopen_ticket(self.tickets, "T002")

    def test_reopened_ticket_can_be_modified_again(self):
        reopen_ticket(self.tickets, "T001")
        ticket = assign_ticket(self.tickets, "T001", "Ada")
        self.assertEqual(ticket["assigned_to"], "Ada")

        update_status(self.tickets, "T001", "in_progress")
        self.assertEqual(ticket["status"], "in_progress")


class WorkQueueTests(unittest.TestCase):
    def test_queue_is_ordered_by_priority(self):
        tickets = [
            make_ticket("T001", "low"),
            make_ticket("T002", "critical"),
            make_ticket("T003", "medium"),
            make_ticket("T004", "high"),
        ]

        queue = get_work_queue(tickets)

        self.assertEqual(
            [ticket["id"] for ticket in queue],
            ["T002", "T004", "T003", "T001"],
        )

    def test_equal_priorities_sort_by_numeric_id(self):
        tickets = [
            make_ticket("T010", "high"),
            make_ticket("T002", "high"),
            make_ticket("T001", "high"),
        ]

        queue = get_work_queue(tickets)

        self.assertEqual(
            [ticket["id"] for ticket in queue],
            ["T001", "T002", "T010"],
        )

    def test_queue_excludes_in_progress_and_resolved(self):
        tickets = [
            make_ticket("T001", "critical"),
            make_ticket("T002", "high", "in_progress"),
            make_ticket("T003", "high", "resolved"),
        ]

        queue = get_work_queue(tickets)

        self.assertEqual([ticket["id"] for ticket in queue], ["T001"])

    def test_queue_is_empty_when_nothing_is_open(self):
        tickets = [
            make_ticket("T001", "high", "in_progress"),
            make_ticket("T002", "low", "resolved"),
        ]

        self.assertEqual(get_work_queue(tickets), [])

    def test_empty_ticket_list_gives_empty_queue(self):
        self.assertEqual(get_work_queue([]), [])

    def test_queue_does_not_modify_original_list(self):
        tickets = [
            make_ticket("T010", "low"),
            make_ticket("T002", "critical"),
            make_ticket("T001", "high"),
        ]
        original_order = [ticket["id"] for ticket in tickets]

        get_work_queue(tickets)

        self.assertEqual([ticket["id"] for ticket in tickets], original_order)

    def test_malformed_id_does_not_crash_the_queue(self):
        # "²" passes str.isdigit() but int() rejects it; the queue must cope.
        tickets = [
            make_ticket("T002", "high"),
            make_ticket("T²", "high"),
        ]

        queue = get_work_queue(tickets)

        self.assertEqual([ticket["id"] for ticket in queue], ["T²", "T002"])

    def test_unrecognised_priority_raises_value_error(self):
        tickets = [make_ticket("T001", "urgent")]

        with self.assertRaises(ValueError):
            get_work_queue(tickets)


if __name__ == "__main__":
    unittest.main()

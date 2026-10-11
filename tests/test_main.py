"""Tests for the CampusFlow command-line interface."""

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import main


def run_cli(inputs, tickets=None, load_error=None):
    """Run main() with scripted input and return (output, save_tickets mock)."""
    output = io.StringIO()
    loader = patch.object(
        main,
        "load_tickets",
        side_effect=load_error
        if load_error is not None
        else None,
        return_value=[] if tickets is None else tickets,
    )

    with loader, patch.object(main, "save_tickets") as save_mock, patch(
        "builtins.input", side_effect=inputs
    ), redirect_stdout(output):
        main.main()

    return output.getvalue(), save_mock


def make_ticket(
    ticket_id="T001",
    priority="low",
    status="open",
    assigned_to=None,
):
    """Build a valid ticket fixture for CLI tests."""
    return {
        "id": ticket_id,
        "title": "Wi-Fi is down",
        "category": "Network",
        "urgency": "high",
        "affected_users": 12,
        "priority": priority,
        "status": status,
        "assigned_to": assigned_to,
    }


class CreateAndListTests(unittest.TestCase):
    def test_create_ticket_shows_id_and_priority_and_saves(self):
        output, save_mock = run_cli(
            ["1", "Wi-Fi is down", "Network", "high", "12", "8"]
        )

        self.assertIn("T001", output)
        self.assertIn("critical", output)
        save_mock.assert_called_once()

        saved_tickets = save_mock.call_args.args[0]
        self.assertEqual(saved_tickets[0]["id"], "T001")
        self.assertEqual(saved_tickets[0]["priority"], "critical")

    def test_invalid_creation_reports_error_without_saving(self):
        tickets = []
        output, save_mock = run_cli(
            ["1", "Wi-Fi is down", "Electricity", "high", "5", "8"],
            tickets=tickets,
        )

        self.assertIn("Error:", output)
        self.assertEqual(tickets, [])
        save_mock.assert_not_called()

    def test_non_numeric_affected_users_reports_error_without_saving(self):
        tickets = []
        output, save_mock = run_cli(
            ["1", "Wi-Fi is down", "Network", "high", "many", "8"],
            tickets=tickets,
        )

        self.assertIn("Error:", output)
        self.assertEqual(tickets, [])
        save_mock.assert_not_called()

    def test_list_shows_existing_tickets(self):
        output, _ = run_cli(["2", "8"], tickets=[make_ticket()])

        self.assertIn("T001", output)
        self.assertIn("Wi-Fi is down", output)

    def test_list_with_no_tickets(self):
        output, _ = run_cli(["2", "8"])

        self.assertIn("No tickets found", output)


class AssignTests(unittest.TestCase):
    def test_assign_ticket_saves_and_reports(self):
        tickets = [make_ticket()]
        output, save_mock = run_cli(["3", "T001", "Ada", "8"], tickets=tickets)

        self.assertIn("assigned to Ada", output)
        save_mock.assert_called_once()
        self.assertEqual(tickets[0]["assigned_to"], "Ada")

    def test_assign_unknown_ticket_reports_error_without_saving(self):
        tickets = [make_ticket()]
        output, save_mock = run_cli(["3", "T999", "Ada", "8"], tickets=tickets)

        self.assertIn("Error:", output)
        save_mock.assert_not_called()
        self.assertIsNone(tickets[0]["assigned_to"])

    def test_assign_blank_staff_name_reports_error(self):
        tickets = [make_ticket()]
        output, save_mock = run_cli(["3", "T001", "   ", "8"], tickets=tickets)

        self.assertIn("Error:", output)
        save_mock.assert_not_called()


class StatusTests(unittest.TestCase):
    def test_update_status_saves_and_reports(self):
        tickets = [make_ticket(assigned_to="Ada")]
        output, save_mock = run_cli(
            ["4", "T001", "in_progress", "8"], tickets=tickets
        )

        self.assertIn("now in_progress", output)
        save_mock.assert_called_once()
        self.assertEqual(tickets[0]["status"], "in_progress")

    def test_update_status_accepts_spaced_status(self):
        tickets = [make_ticket(assigned_to="Ada")]
        output, _ = run_cli(["4", "T001", "In Progress", "8"], tickets=tickets)

        self.assertIn("now in_progress", output)

    def test_invalid_transition_reports_error_without_saving(self):
        tickets = [make_ticket()]
        output, save_mock = run_cli(
            ["4", "T001", "resolved", "8"], tickets=tickets
        )

        self.assertIn("Error:", output)
        save_mock.assert_not_called()
        self.assertEqual(tickets[0]["status"], "open")

    def test_reopen_resolved_ticket_saves_and_reports(self):
        tickets = [make_ticket(status="resolved", assigned_to="Ada")]
        output, save_mock = run_cli(["5", "T001", "8"], tickets=tickets)

        self.assertIn("reopened", output)
        save_mock.assert_called_once()
        self.assertEqual(tickets[0]["status"], "open")


class QueueAndReportTests(unittest.TestCase):
    def test_work_queue_lists_only_open_tickets(self):
        tickets = [
            make_ticket("T001", priority="high"),
            make_ticket("T002", priority="low", status="resolved"),
        ]
        output, _ = run_cli(["6", "8"], tickets=tickets)

        self.assertIn("Work queue", output)
        self.assertIn("T001", output)
        self.assertNotIn("T002", output)

    def test_empty_work_queue(self):
        output, _ = run_cli(["6", "8"])

        self.assertIn("Work queue is empty", output)

    def test_report_shows_totals_and_breakdowns(self):
        tickets = [
            make_ticket("T001", priority="critical"),
            make_ticket("T002", priority="low", status="resolved"),
        ]
        output, _ = run_cli(["7", "8"], tickets=tickets)

        self.assertIn("Total tickets: 2", output)
        self.assertIn("By status:", output)
        self.assertIn("By priority:", output)

    def test_report_on_empty_storage(self):
        output, _ = run_cli(["7", "8"])

        self.assertIn("Total tickets: 0", output)


class MenuTests(unittest.TestCase):
    def test_invalid_menu_option_is_reported(self):
        output, _ = run_cli(["99", "8"])

        self.assertIn("Invalid option", output)

    def test_exit_ends_the_program(self):
        output, _ = run_cli(["8"])

        self.assertIn("Goodbye", output)

    def test_load_error_is_reported_without_crashing(self):
        output, _ = run_cli([], load_error=ValueError("bad storage file"))

        self.assertIn("Could not load tickets", output)


if __name__ == "__main__":
    unittest.main()

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


VALID_TICKET = {
    "id": "T001",
    "title": "Wi-Fi is down",
    "category": "Network",
    "urgency": "high",
    "affected_users": 12,
    "priority": "critical",
    "status": "open",
    "assigned_to": None,
}


class CliTests(unittest.TestCase):
    def test_create_ticket_shows_id_and_priority_and_saves(self):
        output, save_mock = run_cli(
            ["1", "Wi-Fi is down", "Network", "high", "12", "3"]
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
            ["1", "Wi-Fi is down", "Electricity", "high", "5", "3"],
            tickets=tickets,
        )

        self.assertIn("Error:", output)
        self.assertEqual(tickets, [])
        save_mock.assert_not_called()

    def test_non_numeric_affected_users_reports_error_without_saving(self):
        tickets = []
        output, save_mock = run_cli(
            ["1", "Wi-Fi is down", "Network", "high", "many", "3"],
            tickets=tickets,
        )

        self.assertIn("Error:", output)
        self.assertEqual(tickets, [])
        save_mock.assert_not_called()

    def test_list_shows_existing_tickets(self):
        output, _ = run_cli(["2", "3"], tickets=[VALID_TICKET])

        self.assertIn("T001", output)
        self.assertIn("Wi-Fi is down", output)

    def test_list_with_no_tickets(self):
        output, _ = run_cli(["2", "3"])

        self.assertIn("No tickets found", output)

    def test_invalid_menu_option_is_reported(self):
        output, _ = run_cli(["99", "3"])

        self.assertIn("Invalid option", output)

    def test_exit_ends_the_program(self):
        output, _ = run_cli(["3"])

        self.assertIn("Goodbye", output)

    def test_load_error_is_reported_without_crashing(self):
        output, _ = run_cli([], load_error=ValueError("bad storage file"))

        self.assertIn("Could not load tickets", output)


if __name__ == "__main__":
    unittest.main()

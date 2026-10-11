"""Tests for JSON ticket storage."""

import json
import tempfile
import unittest
from pathlib import Path

from campusflow.storage import DEFAULT_STORAGE_PATH, load_tickets, save_tickets
from campusflow.tickets import create_ticket


def make_ticket(**overrides):
    """Build a valid stored ticket record, with optional field overrides."""
    ticket = {
        "id": "T001",
        "title": "Wi-Fi is down",
        "category": "Network",
        "urgency": "high",
        "affected_users": 12,
        "priority": "critical",
        "status": "open",
        "assigned_to": None,
    }
    ticket.update(overrides)
    return ticket


class StorageTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name)
        self.path = self.folder / "tickets.json"

    def write(self, content):
        self.path.write_text(content, encoding="utf-8")

    def test_missing_file_returns_empty_list(self):
        self.assertEqual(load_tickets(self.path), [])

    def test_save_and_load_round_trip(self):
        tickets = [make_ticket(), make_ticket(id="T002", title="Broken laptop")]

        save_tickets(tickets, self.path)

        self.assertEqual(load_tickets(self.path), tickets)

    def test_saved_file_is_a_json_list(self):
        save_tickets([make_ticket()], self.path)

        stored = json.loads(self.path.read_text(encoding="utf-8"))

        self.assertIsInstance(stored, list)

    def test_malformed_json_raises_clear_error(self):
        self.write("{not valid json")

        with self.assertRaises(ValueError) as context:
            load_tickets(self.path)

        self.assertIn("Invalid JSON", str(context.exception))

    def test_malformed_json_is_not_erased(self):
        original = "{not valid json"
        self.write(original)

        with self.assertRaises(ValueError):
            load_tickets(self.path)

        self.assertEqual(self.path.read_text(encoding="utf-8"), original)

    def test_non_list_storage_is_rejected(self):
        self.write(json.dumps({"id": "T001"}))

        with self.assertRaises(ValueError):
            load_tickets(self.path)

    def test_non_object_record_is_rejected(self):
        self.write(json.dumps(["T001"]))

        with self.assertRaises(ValueError):
            load_tickets(self.path)

    def test_record_missing_a_field_is_rejected(self):
        ticket = make_ticket()
        del ticket["priority"]
        self.write(json.dumps([ticket]))

        with self.assertRaises(ValueError):
            load_tickets(self.path)

    def test_malformed_record_values_are_rejected(self):
        bad_values = [
            ("id", ""),
            ("id", 1),
            ("title", "   "),
            ("category", "Electricity"),
            ("urgency", "urgent"),
            ("affected_users", 0),
            ("affected_users", -3),
            ("affected_users", 2.5),
            ("affected_users", "many"),
            ("priority", "urgent"),
            ("status", "closed"),
            ("assigned_to", ""),
        ]
        for field, value in bad_values:
            with self.subTest(field=field, value=value):
                self.write(json.dumps([make_ticket(**{field: value})]))
                with self.assertRaises(ValueError):
                    load_tickets(self.path)

    def test_duplicate_ids_are_rejected(self):
        self.write(json.dumps([make_ticket(), make_ticket()]))

        with self.assertRaises(ValueError):
            load_tickets(self.path)

    def test_save_rejects_non_list(self):
        with self.assertRaises(ValueError):
            save_tickets({"id": "T001"}, self.path)

    def test_default_storage_path_matches_design_decision(self):
        self.assertEqual(Path(DEFAULT_STORAGE_PATH), Path("data") / "tickets.json")

    def test_save_creates_missing_data_directory(self):
        nested = self.folder / "data" / "tickets.json"

        save_tickets([make_ticket()], nested)

        self.assertEqual(load_tickets(nested), [make_ticket()])

    def test_ids_continue_after_reload(self):
        save_tickets([make_ticket()], self.path)

        loaded = load_tickets(self.path)
        ticket = create_ticket(loaded, "Broken laptop", "Hardware", "medium", 3)

        self.assertEqual(ticket["id"], "T002")


if __name__ == "__main__":
    unittest.main()

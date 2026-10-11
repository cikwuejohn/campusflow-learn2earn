"""Tests for ticket creation, validation, and priority calculation."""

import unittest

from campusflow.tickets import calculate_priority, create_ticket, next_ticket_id


class PriorityTests(unittest.TestCase):
    """Priority rules and their boundary values."""

    def test_high_urgency_with_ten_or_more_users_is_critical(self):
        self.assertEqual(calculate_priority("high", 10), "critical")
        self.assertEqual(calculate_priority("high", 12), "critical")

    def test_high_urgency_with_fewer_users_is_high(self):
        self.assertEqual(calculate_priority("high", 9), "high")
        self.assertEqual(calculate_priority("high", 2), "high")

    def test_ten_users_without_high_urgency_is_high(self):
        self.assertEqual(calculate_priority("medium", 10), "high")
        self.assertEqual(calculate_priority("low", 10), "high")

    def test_medium_urgency_is_medium(self):
        self.assertEqual(calculate_priority("medium", 1), "medium")
        self.assertEqual(calculate_priority("medium", 2), "medium")

    def test_three_users_is_medium(self):
        self.assertEqual(calculate_priority("low", 3), "medium")
        self.assertEqual(calculate_priority("low", 4), "medium")
        self.assertEqual(calculate_priority("low", 9), "medium")

    def test_low_urgency_with_few_users_is_low(self):
        self.assertEqual(calculate_priority("low", 1), "low")
        self.assertEqual(calculate_priority("low", 2), "low")

    def test_urgency_is_normalized(self):
        self.assertEqual(calculate_priority("  HIGH  ", 12), "critical")
        self.assertEqual(calculate_priority("MEDIUM", 1), "medium")

    def test_invalid_urgency_is_rejected(self):
        for urgency in ("urgent", "", "   ", None, 5):
            with self.subTest(urgency=urgency):
                with self.assertRaises(ValueError):
                    calculate_priority(urgency, 5)

    def test_invalid_user_counts_are_rejected(self):
        for affected_users in (0, -1, 2.5, "five", None, True):
            with self.subTest(affected_users=affected_users):
                with self.assertRaises(ValueError):
                    calculate_priority("low", affected_users)


class TicketCreationTests(unittest.TestCase):
    """Ticket creation, normalization, and rejection of invalid input."""

    def test_create_ticket_normalizes_and_sets_defaults(self):
        tickets = []
        ticket = create_ticket(tickets, "  Wi-Fi is down  ", "network", "HIGH", 12)

        self.assertEqual(ticket["id"], "T001")
        self.assertEqual(ticket["title"], "Wi-Fi is down")
        self.assertEqual(ticket["category"], "Network")
        self.assertEqual(ticket["urgency"], "high")
        self.assertEqual(ticket["affected_users"], 12)
        self.assertEqual(ticket["priority"], "critical")
        self.assertEqual(ticket["status"], "open")
        self.assertIsNone(ticket["assigned_to"])
        self.assertEqual(tickets, [ticket])

    def test_every_valid_category_is_accepted(self):
        for category in ("Network", "Hardware", "Software", "Other"):
            with self.subTest(category=category):
                tickets = []
                ticket = create_ticket(tickets, "Problem", category, "low", 1)
                self.assertEqual(ticket["category"], category)

    def test_blank_and_whitespace_titles_are_rejected(self):
        for title in ("", " ", "   ", "\t\n", None, 5):
            with self.subTest(title=title):
                tickets = []
                with self.assertRaises(ValueError):
                    create_ticket(tickets, title, "Network", "low", 1)
                self.assertEqual(tickets, [])

    def test_invalid_category_is_rejected(self):
        tickets = []
        with self.assertRaises(ValueError):
            create_ticket(tickets, "Problem", "Electricity", "low", 1)
        self.assertEqual(tickets, [])

    def test_invalid_urgency_is_rejected(self):
        for urgency in ("urgent", "", None, 5):
            with self.subTest(urgency=urgency):
                tickets = []
                with self.assertRaises(ValueError):
                    create_ticket(tickets, "Problem", "Network", urgency, 1)
                self.assertEqual(tickets, [])

    def test_invalid_affected_users_are_rejected(self):
        for affected_users in (0, -1, 2.5, "five", None, True):
            with self.subTest(affected_users=affected_users):
                tickets = []
                with self.assertRaises(ValueError):
                    create_ticket(
                        tickets, "Problem", "Network", "low", affected_users
                    )
                self.assertEqual(tickets, [])

    def test_invalid_ticket_does_not_modify_the_list(self):
        tickets = []
        create_ticket(tickets, "Working ticket", "Network", "low", 1)

        with self.assertRaises(ValueError):
            create_ticket(tickets, "   ", "Network", "low", 1)

        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0]["id"], "T001")


class TicketIdTests(unittest.TestCase):
    """Sequential, unique, and reload-safe ticket IDs."""

    def test_ids_are_sequential(self):
        tickets = []
        ids = [
            create_ticket(tickets, "Ticket", "Network", "low", 1)["id"]
            for _ in range(3)
        ]
        self.assertEqual(ids, ["T001", "T002", "T003"])

    def test_ids_are_unique_when_existing_ids_have_gaps(self):
        tickets = [{"id": "T001"}, {"id": "T003"}]
        ticket = create_ticket(tickets, "New ticket", "Network", "low", 1)
        self.assertEqual(ticket["id"], "T004")

    def test_ids_continue_after_loading_saved_tickets(self):
        tickets = [
            {
                "id": "T001",
                "title": "Wi-Fi issue",
                "category": "Network",
                "urgency": "high",
                "affected_users": 5,
                "priority": "high",
                "status": "open",
                "assigned_to": None,
            }
        ]

        ticket = create_ticket(tickets, "Broken laptop", "Hardware", "medium", 3)

        self.assertEqual(ticket["id"], "T002")

    def test_next_ticket_id_ignores_malformed_entries(self):
        tickets = [{"id": "T007"}, {"title": "no id"}, "junk", {"id": "X123"}, {}]
        self.assertEqual(next_ticket_id(tickets), "T008")


if __name__ == "__main__":
    unittest.main()

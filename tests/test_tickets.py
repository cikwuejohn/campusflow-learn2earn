
import unittest

from campusflow.tickets import calculate_priority, create_ticket


class TicketTests(unittest.TestCase):
    # Verify priority boundaries and input validation.
    def test_priority_rules(self):
        self.assertEqual(calculate_priority("high", 12), "critical")
        self.assertEqual(calculate_priority("high", 2), "high")
        self.assertEqual(calculate_priority("low", 4), "medium")
        self.assertEqual(calculate_priority("low", 1), "low")

    def test_zero_users_rejected(self):
        with self.assertRaises(ValueError):
            calculate_priority("low", 0)

    def test_invalid_urgency_rejected(self):
        with self.assertRaises(ValueError):
            calculate_priority("urgent", 5)

    def test_create_ticket(self):
        tickets = []
        ticket = create_ticket(
            tickets, "Wi-Fi is down", "network", "HIGH", 12
        )
        self.assertEqual(ticket["id"], "T001")
        self.assertEqual(ticket["category"], "Network")
        self.assertEqual(ticket["priority"], "critical")
        self.assertEqual(len(tickets), 1)

    def test_blank_title_does_not_change_tickets(self):
        tickets = []
        with self.assertRaises(ValueError):
            create_ticket(tickets, " ", "Network", "low", 1)
        self.assertEqual(tickets, [])

    def test_invalid_users_do_not_change_tickets(self):
        tickets = []
        with self.assertRaises(ValueError):
            create_ticket(tickets, "Broken laptop", "Hardware", "low", 0)
        self.assertEqual(tickets, [])

    def test_ids_remain_unique(self):
        tickets = [
            {"id": "T001"},
            {"id": "T003"},
        ]
        ticket = create_ticket(
            tickets, "Broken laptop", "Hardware", "medium", 1
        )
        self.assertEqual(ticket["id"], "T004")


if __name__ == "__main__":
    unittest.main()


VALID_CATEGORIES = ("Network", "Hardware", "Software", "Other")
VALID_URGENCIES = ("low", "medium", "high")


def calculate_priority(urgency, affected_users):
    # Validate inputs before calculating priority.
    if not isinstance(urgency, str) or urgency.strip().lower() not in VALID_URGENCIES:
        raise ValueError("Urgency must be low, medium, or high")

    if type(affected_users) is not int or affected_users <= 0:
        raise ValueError("Affected users must be a positive integer")

    urgency = urgency.strip().lower()

    # Check rules in the required order.
    if urgency == "high" and affected_users >= 10:
        return "critical"
    if urgency == "high" or affected_users >= 10:
        return "high"
    if urgency == "medium" or affected_users >= 3:
        return "medium"
    return "low"


def create_ticket(tickets, title, category, urgency, affected_users):
    # Validate and normalize all inputs before modifying the ticket list.
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Title cannot be blank")

    if not isinstance(category, str):
        raise ValueError("Invalid category")

    category_lookup = {item.lower(): item for item in VALID_CATEGORIES}
    category = category_lookup.get(category.strip().lower())
    if category is None:
        raise ValueError("Category must be Network, Hardware, Software, or Other")

    if not isinstance(urgency, str):
        raise ValueError("Invalid urgency")

    urgency = urgency.strip().lower()
    if urgency not in VALID_URGENCIES:
        raise ValueError("Urgency must be low, medium, or high")

    # Calculate priority also validates affected_users.
    priority = calculate_priority(urgency, affected_users)

    # Find the highest existing numeric ID to avoid duplicates after reload.
    highest_id = 0
    for ticket in tickets:
        ticket_id = ticket.get("id", "")
        if isinstance(ticket_id, str) and ticket_id.startswith("T"):
            number = ticket_id[1:]
            if number.isdigit():
                highest_id = max(highest_id, int(number))

    ticket = {
        "id": f"T{highest_id + 1:03d}",
        "title": title.strip(),
        "category": category,
        "urgency": urgency,
        "affected_users": affected_users,
        "priority": priority,
        "status": "open",
        "assigned_to": None,
    }

    tickets.append(ticket)
    return ticket

"""Ticket creation, input validation, and priority calculation."""

VALID_CATEGORIES = ("Network", "Hardware", "Software", "Other")
VALID_URGENCIES = ("low", "medium", "high")
VALID_PRIORITIES = ("critical", "high", "medium", "low")


def calculate_priority(urgency, affected_users):
    """Return the priority for a validated urgency level and user count."""
    # Validate both inputs before applying any rule.
    if not isinstance(urgency, str) or urgency.strip().lower() not in VALID_URGENCIES:
        raise ValueError("Urgency must be low, medium, or high")

    if type(affected_users) is not int or affected_users <= 0:
        raise ValueError("Affected users must be a positive integer")

    urgency = urgency.strip().lower()

    # Apply the rules in order and return the first match.
    if urgency == "high" and affected_users >= 10:
        return "critical"
    if urgency == "high" or affected_users >= 10:
        return "high"
    if urgency == "medium" or affected_users >= 3:
        return "medium"
    return "low"


def next_ticket_id(tickets):
    """Return the next sequential ticket ID based on the existing tickets."""
    # Find the highest numeric ID so numbering continues after a reload.
    highest_id = 0
    for ticket in tickets:
        if not isinstance(ticket, dict):
            continue
        ticket_id = ticket.get("id")
        if not isinstance(ticket_id, str):
            continue
        number = ticket_id[1:]
        if ticket_id[:1] == "T" and number.isdigit():
            highest_id = max(highest_id, int(number))

    return f"T{highest_id + 1:03d}"


def create_ticket(tickets, title, category, urgency, affected_users):
    """Validate and normalize the input, then append a new ticket."""
    # Validate and normalize everything before touching the ticket list, so an
    # invalid request can never leave a partial ticket behind.
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

    # calculate_priority also validates affected_users.
    priority = calculate_priority(urgency, affected_users)

    ticket = {
        "id": next_ticket_id(tickets),
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

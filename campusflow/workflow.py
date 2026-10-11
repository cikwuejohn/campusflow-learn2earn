"""Ticket assignment, status lifecycle, and work queue ordering."""

# Priority ranking used for work queue ordering (lower sorts first).
PRIORITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}

# The only forward transitions the workflow allows.
ALLOWED_TRANSITIONS = {
    "open": "in_progress",
    "in_progress": "resolved",
}

VALID_STATUSES = ("open", "in_progress", "resolved")


def find_ticket(tickets, ticket_id):
    """Return the ticket with the given ID, or raise ValueError."""
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            return ticket
    raise ValueError(f"Ticket {ticket_id} was not found")


def ticket_number(ticket):
    """Return the numeric part of a ticket ID for stable ordering.

    Ticket IDs follow the T001 format, but malformed IDs must not crash the
    queue, so anything without a numeric suffix sorts first.
    """
    ticket_id = ticket.get("id", "")
    suffix = str(ticket_id)[1:]
    return int(suffix) if suffix.isdigit() else 0


def assign_ticket(tickets, ticket_id, staff_name):
    """Assign a ticket to a staff member and return the ticket."""
    # Validate everything before changing the ticket.
    ticket = find_ticket(tickets, ticket_id)

    if ticket["status"] == "resolved":
        raise ValueError("Reopen the ticket before modifying it")

    if not isinstance(staff_name, str) or not staff_name.strip():
        raise ValueError("Staff name cannot be blank")

    ticket["assigned_to"] = staff_name.strip()
    return ticket


def update_status(tickets, ticket_id, new_status):
    """Move a ticket through the open -> in_progress -> resolved lifecycle."""
    ticket = find_ticket(tickets, ticket_id)

    if new_status not in VALID_STATUSES:
        raise ValueError("Invalid status")

    # A resolved ticket is frozen until it is explicitly reopened.
    if ticket["status"] == "resolved":
        raise ValueError("Reopen the ticket before modifying it")

    if ALLOWED_TRANSITIONS.get(ticket["status"]) != new_status:
        raise ValueError(
            f"Cannot change status from {ticket['status']} to {new_status}"
        )

    # Work can only start once someone owns the ticket.
    if new_status == "in_progress" and not ticket["assigned_to"]:
        raise ValueError("Assign the ticket before starting work")

    ticket["status"] = new_status
    return ticket


def reopen_ticket(tickets, ticket_id):
    """Reopen a resolved ticket so it can be worked on again."""
    ticket = find_ticket(tickets, ticket_id)

    if ticket["status"] != "resolved":
        raise ValueError("Only resolved tickets can be reopened")

    ticket["status"] = "open"
    return ticket


def get_work_queue(tickets):
    """Return open tickets ordered by priority then numeric ticket ID.

    Tickets that are in_progress or resolved are excluded, and the input list
    is left untouched (sorted() builds a new list).
    """
    open_tickets = [
        ticket for ticket in tickets
        if ticket["status"] == "open"
    ]

    return sorted(
        open_tickets,
        key=lambda ticket: (
            PRIORITY_ORDER[ticket["priority"]],
            ticket_number(ticket),
        ),
    )

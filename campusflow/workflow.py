
PRIORITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}


def find_ticket(tickets, ticket_id):
    # Find a ticket or reject an unknown ID.
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            return ticket
    raise ValueError(f"Ticket {ticket_id} was not found")


def assign_ticket(tickets, ticket_id, staff_name):
    # Validate everything before changing the ticket.
    ticket = find_ticket(tickets, ticket_id)

    if ticket["status"] == "resolved":
        raise ValueError("Reopen the ticket before modifying it")

    if not isinstance(staff_name, str) or not staff_name.strip():
        raise ValueError("Staff name cannot be blank")

    ticket["assigned_to"] = staff_name.strip()
    return ticket


def update_status(tickets, ticket_id, new_status):
    # Allow only the specified forward workflow.
    ticket = find_ticket(tickets, ticket_id)

    if new_status not in ("open", "in_progress", "resolved"):
        raise ValueError("Invalid status")

    if ticket["status"] == "resolved":
        raise ValueError("Reopen the ticket before modifying it")

    allowed_transitions = {
        "open": "in_progress",
        "in_progress": "resolved",
    }

    if allowed_transitions.get(ticket["status"]) != new_status:
        raise ValueError(
            f"Cannot change status from {ticket['status']} to {new_status}"
        )

    if new_status == "in_progress" and not ticket["assigned_to"]:
        raise ValueError("Assign the ticket before starting work")

    ticket["status"] = new_status
    return ticket


def reopen_ticket(tickets, ticket_id):
    # Reopening is the explicit way to modify a resolved ticket again.
    ticket = find_ticket(tickets, ticket_id)

    if ticket["status"] != "resolved":
        raise ValueError("Only resolved tickets can be reopened")

    ticket["status"] = "open"
    return ticket


def get_work_queue(tickets):
    # Return open tickets ordered by priority and numeric ticket ID.
    open_tickets = [
        ticket for ticket in tickets
        if ticket["status"] == "open"
    ]

    return sorted(
        open_tickets,
        key=lambda ticket: (
            PRIORITY_ORDER[ticket["priority"]],
            int(ticket["id"][1:]),
        ),
    )

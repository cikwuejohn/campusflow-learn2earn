"""JSON persistence for CampusFlow tickets."""

import json
from pathlib import Path

from campusflow.tickets import VALID_CATEGORIES, VALID_PRIORITIES, VALID_URGENCIES

DEFAULT_FILENAME = "tickets.json"

# Statuses follow the lifecycle agreed with Engineer B (open -> in_progress ->
# resolved). Update this tuple together if that lifecycle ever changes.
VALID_STATUSES = ("open", "in_progress", "resolved")

REQUIRED_FIELDS = (
    "id",
    "title",
    "category",
    "urgency",
    "affected_users",
    "priority",
    "status",
    "assigned_to",
)


def _validate_ticket(ticket, position):
    """Raise ValueError when a stored ticket record is malformed."""
    if not isinstance(ticket, dict):
        raise ValueError(f"Ticket at position {position} must be an object.")

    missing = [field for field in REQUIRED_FIELDS if field not in ticket]
    if missing:
        raise ValueError(
            f"Ticket at position {position} is missing: {', '.join(missing)}"
        )

    if not isinstance(ticket["id"], str) or not ticket["id"].strip():
        raise ValueError(f"Ticket at position {position} has an invalid id.")

    if not isinstance(ticket["title"], str) or not ticket["title"].strip():
        raise ValueError(f"Ticket at position {position} has an invalid title.")

    if ticket["category"] not in VALID_CATEGORIES:
        raise ValueError(f"Ticket at position {position} has an invalid category.")

    if ticket["urgency"] not in VALID_URGENCIES:
        raise ValueError(f"Ticket at position {position} has an invalid urgency.")

    if type(ticket["affected_users"]) is not int or ticket["affected_users"] <= 0:
        raise ValueError(
            f"Ticket at position {position} has an invalid affected_users value."
        )

    if ticket["priority"] not in VALID_PRIORITIES:
        raise ValueError(f"Ticket at position {position} has an invalid priority.")

    if ticket["status"] not in VALID_STATUSES:
        raise ValueError(f"Ticket at position {position} has an invalid status.")

    assigned_to = ticket["assigned_to"]
    if assigned_to is not None and (
        not isinstance(assigned_to, str) or not assigned_to.strip()
    ):
        raise ValueError(
            f"Ticket at position {position} has an invalid assigned_to value."
        )


def _validate_tickets(tickets):
    """Validate every stored record and reject duplicate ticket IDs."""
    seen_ids = set()
    for position, ticket in enumerate(tickets, start=1):
        _validate_ticket(ticket, position)
        ticket_id = ticket["id"]
        if ticket_id in seen_ids:
            raise ValueError(f"Duplicate ticket id found in storage: {ticket_id}")
        seen_ids.add(ticket_id)


def save_tickets(tickets, filename=DEFAULT_FILENAME):
    """Save tickets to a JSON file, writing atomically to avoid corruption."""
    if not isinstance(tickets, list):
        raise ValueError("Tickets to save must be a list.")

    path = Path(filename)
    # Write to a temporary file first so a crash cannot truncate the real file.
    temp_path = path.with_name(f"{path.name}.tmp")

    with temp_path.open("w", encoding="utf-8") as file:
        json.dump(tickets, file, indent=4)

    temp_path.replace(path)


def load_tickets(filename=DEFAULT_FILENAME):
    """Load and validate tickets from a JSON file."""
    path = Path(filename)

    # A missing file is a fresh start, not an error.
    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8") as file:
            tickets = json.load(file)
    except json.JSONDecodeError as error:
        # Surface the problem clearly; never overwrite the corrupt file.
        raise ValueError(f"Invalid JSON in {path}: {error}") from error

    if not isinstance(tickets, list):
        raise ValueError(f"Ticket storage in {path} must contain a JSON list.")

    _validate_tickets(tickets)
    return tickets

"""CampusFlow command-line interface."""

from campusflow.reports import generate_report
from campusflow.storage import load_tickets, save_tickets
from campusflow.tickets import create_ticket
from campusflow.workflow import (
    assign_ticket,
    get_work_queue,
    reopen_ticket,
    update_status,
)

MENU = """
=== CampusFlow ===
1. Create ticket
2. List tickets
3. Assign ticket
4. Update ticket status
5. Reopen ticket
6. View work queue
7. View report
8. Exit
"""


def read_affected_users():
    """Read a positive whole number of affected users from the user."""
    raw_value = input("Number of affected users: ").strip()
    if not raw_value.isdigit():
        raise ValueError("Affected users must be a whole number")
    return int(raw_value)


def read_ticket_id():
    """Read a non-empty ticket ID from the user."""
    ticket_id = input("Ticket ID: ").strip()
    if not ticket_id:
        raise ValueError("Ticket ID cannot be blank")
    return ticket_id


def create_ticket_from_input(tickets):
    """Collect ticket details, create the ticket, and save it."""
    title = input("Ticket title: ")
    category = input("Category (Network, Hardware, Software, Other): ")
    urgency = input("Urgency (low, medium, high): ")
    affected_users = read_affected_users()

    ticket = create_ticket(tickets, title, category, urgency, affected_users)
    save_tickets(tickets)

    print(f"Ticket {ticket['id']} created successfully!")
    print(f"Priority: {ticket['priority']}")
    return ticket


def list_tickets(tickets):
    """Print a one-line summary of every stored ticket."""
    if not tickets:
        print("No tickets found.")
        return

    for ticket in tickets:
        print(
            f"{ticket['id']} | {ticket['title']} | "
            f"{ticket['priority']} | {ticket['status']} | "
            f"assigned to: {ticket['assigned_to'] or 'nobody'}"
        )


def assign_ticket_from_input(tickets):
    """Assign a ticket to a staff member and save the change."""
    ticket_id = read_ticket_id()
    staff_name = input("Staff name: ")

    ticket = assign_ticket(tickets, ticket_id, staff_name)
    save_tickets(tickets)

    print(f"Ticket {ticket['id']} assigned to {ticket['assigned_to']}.")
    return ticket


def update_status_from_input(tickets):
    """Move a ticket to a new status and save the change."""
    ticket_id = read_ticket_id()
    # Accept "In Progress" as well as "in_progress".
    new_status = input("New status (in_progress or resolved): ")
    new_status = new_status.strip().lower().replace(" ", "_")

    ticket = update_status(tickets, ticket_id, new_status)
    save_tickets(tickets)

    print(f"Ticket {ticket['id']} is now {ticket['status']}.")
    return ticket


def reopen_ticket_from_input(tickets):
    """Reopen a resolved ticket and save the change."""
    ticket_id = read_ticket_id()

    ticket = reopen_ticket(tickets, ticket_id)
    save_tickets(tickets)

    print(f"Ticket {ticket['id']} reopened.")
    return ticket


def show_work_queue(tickets):
    """Print the open tickets ordered by priority."""
    queue = get_work_queue(tickets)

    if not queue:
        print("Work queue is empty.")
        return

    print("Work queue (open tickets, highest priority first):")
    for position, ticket in enumerate(queue, start=1):
        print(
            f"  {position}. {ticket['id']} | {ticket['priority']} | "
            f"{ticket['title']}"
        )


def show_report(tickets):
    """Print totals grouped by status and priority."""
    report = generate_report(tickets)

    print(f"Total tickets: {report['total']}")

    print("By status:")
    for status, count in report["by_status"].items():
        print(f"  {status}: {count}")

    print("By priority:")
    for priority, count in report["by_priority"].items():
        print(f"  {priority}: {count}")


def main():
    # Load previously saved tickets, or start fresh when there is no file yet.
    try:
        tickets = load_tickets()
    except (ValueError, OSError) as error:
        print(f"Could not load tickets: {error}")
        return

    while True:
        print(MENU)

        try:
            choice = input("Choose an option: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        # Each action may raise ValueError for invalid input; catching it here
        # keeps the program running and reports the problem clearly.
        try:
            if choice == "1":
                create_ticket_from_input(tickets)
            elif choice == "2":
                list_tickets(tickets)
            elif choice == "3":
                assign_ticket_from_input(tickets)
            elif choice == "4":
                update_status_from_input(tickets)
            elif choice == "5":
                reopen_ticket_from_input(tickets)
            elif choice == "6":
                show_work_queue(tickets)
            elif choice == "7":
                show_report(tickets)
            elif choice == "8":
                print("Goodbye!")
                break
            else:
                print("Invalid option. Please choose 1-8.")
        except ValueError as error:
            # Invalid input must never modify the ticket list.
            print(f"Error: {error}")
        except OSError as error:
            print(f"Could not save tickets: {error}")


if __name__ == "__main__":
    main()

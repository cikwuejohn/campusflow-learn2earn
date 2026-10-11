"""CampusFlow command-line interface."""

from campusflow.tickets import create_ticket
from campusflow.storage import load_tickets, save_tickets

MENU = """
=== CampusFlow ===
1. Create ticket
2. List tickets
3. Exit
"""


def read_affected_users():
    """Read a positive whole number of affected users from the user."""
    raw_value = input("Number of affected users: ").strip()
    if not raw_value.isdigit():
        raise ValueError("Affected users must be a whole number")
    return int(raw_value)


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
            f"{ticket['priority']} | {ticket['status']}"
        )


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

        if choice == "1":
            try:
                create_ticket_from_input(tickets)
            except ValueError as error:
                # Invalid input must never modify the ticket list.
                print(f"Error: {error}")
            except OSError as error:
                print(f"Could not save tickets: {error}")

        elif choice == "2":
            list_tickets(tickets)

        elif choice == "3":
            print("Goodbye!")
            break

        else:
            print("Invalid option. Please choose 1, 2, or 3.")


if __name__ == "__main__":
    main()

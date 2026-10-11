
STATUSES = ("open", "in_progress", "resolved")
PRIORITIES = ("critical", "high", "medium", "low")


def generate_report(tickets):
    # Count every ticket by status and priority, including empty categories.
    return {
        "total": len(tickets),
        "by_status": {
            status: sum(1 for t in tickets if t["status"] == status)
            for status in STATUSES
        },
        "by_priority": {
            priority: sum(
                1 for t in tickets if t["priority"] == priority
            )
            for priority in PRIORITIES
        },
    }

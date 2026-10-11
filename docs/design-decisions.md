# CampusFlow — Design Decisions

## 1. Project Overview
CampusFlow is a Python command-line helpdesk system for creating, assigning, prioritizing, tracking and reporting campus support tickets.

## 2. Team Responsibilities
- Engineer A: Ticket creation, validation, priority calculation and related tests.
- Engineer B: Assignment, status workflow, queue, reports and related tests.
- Both: JSON persistence, CLI integration, code reviews and documentation.

## 3. Data Structure
We will use a list of dictionaries. Each dictionary represents a ticket containing the eight required fields.

## 4. Function Contracts
- Business functions receive their data through parameters.
- Creation and update functions return the created or updated ticket.
- Invalid inputs and transitions raise ValueError.
- The CLI catches errors and displays understandable messages.
- Functions must not partially modify tickets when validation fails.

## 5. Ticket IDs
Ticket IDs follow T001, T002, T003, etc. New IDs are generated using the highest existing numeric ticket ID plus one.

## 6. Priority Rules
1. High urgency and 10+ affected users: critical.
2. High urgency or 10+ affected users: high.
3. Medium urgency or 3+ affected users: medium.
4. Otherwise: low.

## 7. Status Workflow
- open → in_progress → resolved
- Tickets must be assigned before entering in_progress.
- Resolved tickets require an explicit reopen operation before modification.

## 8. Persistence
The storage module uses Python's json library. Tickets are saved in data/tickets.json and reloaded at startup. Missing files start with an empty collection. Malformed JSON must raise an error.

## 9. Testing
We will use unittest. Each engineer writes tests for their own features. Tests will cover successful operations, invalid inputs, boundary cases and persistence.

## 10. GitHub Collaboration
Both engineers use separate feature branches, create PRs, review each other's changes, resolve blocking comments and merge only after approval.
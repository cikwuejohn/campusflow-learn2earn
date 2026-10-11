# CampusFlow

A command-line helpdesk ticket manager for Learn2Earn campus staff.

Campus staff report technical problems every day — Wi-Fi outages, faulty laptops, broken
development environments, inaccessible platforms. Reported informally, these requests get lost:
nobody knows which problem is most urgent, who owns it, or whether it is being worked on.

CampusFlow records each request as a **ticket**, calculates its **priority** from the urgency and
the number of people affected, **assigns** it to a staff member, tracks it through a
**lifecycle** (`open → in_progress → resolved`), and reports on the whole queue. Tickets are
saved to **JSON**, so the list survives a restart.

Built with the Python standard library only — no framework, database, or API key required.

---

## Table of contents

- [Features](#features)
- [Ticket model](#ticket-model)
- [Priority rules](#priority-rules)
- [Status workflow](#status-workflow)
- [Requirements](#requirements)
- [Getting started](#getting-started)
- [Using the CLI](#using-the-cli)
- [Running the tests](#running-the-tests)
- [Where tickets are stored](#where-tickets-are-stored)
- [Project structure](#project-structure)
- [Design decisions](#design-decisions)
- [Team and contributions](#team-and-contributions)
- [Known limitations](#known-limitations)
- [License](#license)

---

## Features

| # | Feature | Description |
|---|---------|-------------|
| F1 | **Create** | Collect ticket details, validate and normalize every field, calculate priority, allocate a unique ID, and store the record. |
| F2 | **List / view** | Print a one-line summary of all stored tickets. |
| F3 | **Assign** | Assign a ticket to a non-empty staff name; reject unknown ticket IDs and blank names. |
| F4 | **Workflow** | Move a ticket `open → in_progress → resolved`. An unassigned ticket cannot start work, and a resolved ticket must be explicitly reopened before it can be changed again. |
| F5 | **Work queue** | Show open tickets in `critical → high → medium → low` order, breaking ties by the earlier numeric ticket ID. |
| F6 | **Reports** | Total ticket count plus breakdowns by status and by priority, including zero counts for empty categories. |
| F7 | **Persistence** | Save to JSON and reload on startup. A missing file starts fresh; malformed JSON produces a clear error instead of erasing data. IDs stay unique after a reload. |

Invalid input is rejected with a readable message and never leaves a partially modified ticket
behind. The menu keeps running until you choose **Exit**.

## Ticket model

Every ticket is a dictionary with eight fields:

```json
{
  "id": "T001",
  "title": "Campus Wi-Fi is down",
  "category": "Network",
  "urgency": "high",
  "affected_users": 15,
  "priority": "critical",
  "status": "open",
  "assigned_to": null
}
```

- **`id`** — generated automatically and sequentially: `T001`, `T002`, `T003`, … Numbering
  continues from the highest stored ID, so IDs remain unique after a reload.
- **`category`** — one of `Network`, `Hardware`, `Software`, `Other`.
- **`urgency`** — one of `low`, `medium`, `high`.
- **`title`** — must not be blank.
- **`affected_users`** — a positive whole number. Zero, negatives, decimals, and text are rejected.
- **`assigned_to`** — `null` until the ticket is assigned.

Valid values are accepted case-insensitively and stored in their normalized form (for example
`"NETWORK"` is stored as `"Network"`, `" High "` as `"high"`).

## Priority rules

Priority is ordinary Python business logic, evaluated **in order** — the first matching rule wins:

| Rule | Condition | Priority |
|------|-----------|----------|
| 1 | high urgency **and** 10 or more affected users | `critical` |
| 2 | high urgency **or** 10 or more affected users | `high` |
| 3 | medium urgency **or** 3 or more affected users | `medium` |
| 4 | all remaining valid tickets | `low` |

Worked examples:

| Urgency | Affected users | Priority | Matching rule |
|---------|----------------|----------|---------------|
| high | 12 | critical | 1 |
| high | 2 | high | 2 |
| low | 10 | high | 2 |
| medium | 1 | medium | 3 |
| low | 4 | medium | 3 |
| low | 1 | low | 4 |

## Status workflow

```
open ──► in_progress ──► resolved
  ▲                          │
  └──────── reopen ──────────┘
```

- A ticket must be **assigned** before it can enter `in_progress`.
- Transitions cannot be skipped (`open` → `resolved` is rejected) or reversed.
- A `resolved` ticket is frozen: it cannot be reassigned or restatused until it is explicitly
  **reopened**, which sets it back to `open`.

## Requirements

- **Python 3.8 or newer** (developed and tested on Python 3.12)
- No third-party packages — the standard library only

## Getting started

```bash
git clone https://github.com/cikwuejohn/campusflow-learn2earn.git
cd campusflow-learn2earn

# Optional: use a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

There are no dependencies to install. Run the app from the repository root:

```bash
python3 main.py
```

> Run `main.py` from the project root. The package resolves correctly because the working
> directory is on `sys.path`; the ticket file is likewise written relative to the working
> directory.

## Using the CLI

```
=== CampusFlow ===
1. Create ticket
2. List tickets
3. Assign ticket
4. Update ticket status
5. Reopen ticket
6. View work queue
7. View report
8. Exit
```

| Option | What it does | Notes |
|--------|--------------|-------|
| **1** | Create ticket | Prompts for title, category, urgency, and affected users. Prints the new ID and the calculated priority. |
| **2** | List tickets | One line per ticket: ID, title, priority, status, assignee. |
| **3** | Assign ticket | Prompts for ticket ID and staff name. |
| **4** | Update ticket status | Prompts for ticket ID and the new status. `In Progress` and `in_progress` are both accepted. |
| **5** | Reopen ticket | Reopens a resolved ticket back to `open`. |
| **6** | View work queue | Open tickets in priority order. |
| **7** | View report | Totals by status and by priority. |
| **8** | Exit | Saves nothing further and quits. |

Changes are written to disk as soon as they succeed, so exiting never loses completed work.
Errors are reported as `Error: <message>` and return you to the menu with your tickets intact.

### Example session

```
Choose an option: 1
Ticket title: Campus Wi-Fi is down
Category (Network, Hardware, Software, Other): network
Urgency (low, medium, high): HIGH
Number of affected users: 15
Ticket T001 created successfully!
Priority: critical

Choose an option: 3
Ticket ID: T001
Staff name: Ama Mensah
Ticket T001 assigned to Ama Mensah.

Choose an option: 4
Ticket ID: T001
New status (in_progress or resolved): in_progress
Ticket T001 is now in_progress.
```

## Running the tests

```bash
python3 -m unittest discover -s tests -v
```

The suite contains **85 tests** and currently passes on `main`:

```
Ran 85 tests in 0.040s

OK
```

Coverage by module:

| Test file | Tests | Covers |
|-----------|-------|--------|
| `tests/test_tickets.py` | 20 | Priority rules and boundaries, input normalization, every valid category, blank titles, invalid urgencies and user counts, sequential and gap-tolerant ID generation. |
| `tests/test_workflow.py` | 27 | Assignment rules, the full lifecycle, rejected transitions, reopen behaviour, queue ordering by priority then numeric ID, malformed-ID and invalid-priority resilience. |
| `tests/test_storage.py` | 14 | JSON round-trip, atomic save, missing file, malformed JSON, malformed and duplicate records, storage-path contract, ID continuity after reload. |
| `tests/test_main.py` | 19 | Menu flow, creation/listing/assignment/status/reopen/report output, invalid-option handling, exit behaviour, load errors, and that a failed action never saves. |
| `tests/test_reports.py` | 5 | Totals, breakdowns by status and priority, and empty-category reporting. |

Both successful paths and invalid-input paths are tested. Persistence is verified by real
round-trips rather than mocks.

## Where tickets are stored

Tickets are saved to **`data/tickets.json`** (pretty-printed JSON, one list of ticket objects).

- The directory is created automatically on first save.
- Saves are **atomic**: tickets are written to a temporary file and then moved into place, so an
  interrupted write cannot truncate the real file.
- A **missing file** means a fresh start with an empty list.
- A **malformed file** raises a clear error at startup and the corrupt file is left untouched —
  CampusFlow never silently erases your data. Fix or move the file, then restart.

**To start fresh**, stop the app and delete the file:

```bash
rm data/tickets.json          # macOS / Linux
del data\tickets.json         # Windows
```

`data/tickets.json` is listed in `.gitignore` and is never committed.

## Project structure

```
campusflow-learn2earn/
├── main.py                      # CLI: menu loop, prompts, and error display
├── campusflow/
│   ├── __init__.py
│   ├── tickets.py               # Creation, validation, priority engine, ID allocation
│   ├── workflow.py              # Assignment, status lifecycle, reopen, work queue
│   ├── storage.py               # JSON load/save, record validation, atomic writes
│   └── reports.py               # Totals and breakdowns
├── tests/
│   ├── test_tickets.py
│   ├── test_workflow.py
│   ├── test_storage.py
│   ├── test_main.py
│   └── test_reports.py
├── docs/
│   ├── design-decisions.md      # Agreed data structures, contracts, and ownership
│   └── ai-learning-log.md       # AI learning log (per-fellow entries)
└── README.md
```

Business logic lives in the `campusflow` package and is free of `input()` and `print()`, so every
rule can be unit-tested directly. `main.py` owns all interaction with the user.

## Design decisions

The team's agreed interfaces are recorded in [`docs/design-decisions.md`](docs/design-decisions.md):

- Tickets are held in a **list of dictionaries**, passed to functions as a parameter.
- Business functions **return the created or updated ticket**; the caller decides when to save.
- Invalid input and invalid transitions **raise `ValueError`**; the CLI catches it and prints a
  readable message.
- **Functions never partially modify tickets** — all validation happens before any mutation.
- `campusflow/storage.py` is the only module that touches JSON.

## Team and contributions

Built by a two-person team during the AI-Native Engineering Sprint.

| Engineer | Scope | Feature branch | Pull request |
|----------|-------|----------------|--------------|
| **Engineer A — Ochai Stanley** ([@Stanley-0ps](https://github.com/Stanley-0ps)) | Ticket creation, input validation, priority engine, ticket IDs, JSON storage, CLI integration, and the matching tests | `feat/1-ticket-creation` | [#10](https://github.com/cikwuejohn/campusflow-learn2earn/pull/10) |
| **Engineer B — @cikwuejohn** | Assignment, status workflow, reopen, work queue, reports, CLI wiring for those paths, and the matching tests | `feat/2-status-workflow` | [#11](https://github.com/cikwuejohn/campusflow-learn2earn/pull/11) |

Both engineers wrote application code **and** tests. Each authored a pull request, reviewed the
other's, and merged only after review approval — see the PR links above for the code, review
comments, and test evidence.

## Known limitations

Honest gaps in the current implementation:

- **Single-user, local only.** There is no authentication, locking, or multi-user support — two
  people running CampusFlow against the same file can overwrite each other's changes.
- **No editing or deletion.** A ticket's title, category, urgency, and affected-user count cannot
  be changed after creation; tickets cannot be deleted. Priority is not recalculated on update
  because tickets are not editable.
- **No search or filtering.** `List tickets` always prints everything; there is no filter by
  status, priority, or assignee, and no pagination.
- **No SLA, timestamps, or history.** Tickets carry no created/updated timestamps, no assignment
  or transition audit trail, and no comments.
- **`assigned_to` is a free-text name.** There is no staff directory, so no validation that a
  staff member exists and no per-assignee workload view.
- **Storage is unencrypted JSON in the working directory.** There is no file locking, schema
  migration, or backup rotation.
- **The interactive CLI is not exhaustively tested.** `tests/test_main.py` drives the menu with
  patched input and output for the main paths, but manual end-to-end runs are still needed for
  confidence in the full interactive experience.

Possible next steps, in rough priority order: make tickets editable (with priority recalculation),
add filtering and search to the list view, record timestamps and a status history, and add a staff
directory to validate assignees.

## License

Developed for the Learn2Earn AI-Native Engineering Sprint. No license is currently declared; add
one before reusing this code outside the programme.

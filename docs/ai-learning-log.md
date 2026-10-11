# CampusFlow — AI Learning Log

**Engineer B** · Ticket assignment, status management, work queue, reports, tests and CLI integration
**Branch:** `feat/2-status-workflow` · **Repo:** `cikwuejohn/campusflow-learn2earn`

This log records how I used an AI assistant while completing my part
of CampusFlow, what I asked it, what I accepted or rejected, and what I learned.
The assistant wrote and explained code, but I owned the design decisions, reviewed
every change, and verified each step by running the test suite myself.

---

## 1. How I worked with the AI

- **Pair-programming, not copy-paste.** I broke the task into small verifiable
  steps (assignment → lifecycle → queue → reports → tests → CLI) and reviewed
  each change before moving on.
- **Ask "why", not just "what".** For each function I asked the assistant to
  justify its validation order and error handling, so I could defend the code.
- **Verify every step.** I ran `python3 -m unittest discover -s tests -v` after
  each change instead of trusting that the code worked.
- **Start from the shared contract.** The team's `docs/design-decisions.md`
  defined the data model, the status workflow and the `T001` ID format, so I made
  the AI work *inside* those decisions rather than inventing its own.

### Prompt style that worked well

| Instead of… | I asked… |
| --- | --- |
| "Write workflow.py" | "Implement `assign_ticket` so validation happens before any mutation, and explain why ordering matters." |
| "Fix my bug" | "This test expects an error but the ticket is still being modified — find the cause and show the minimal fix." |
| "Sort the queue" | "Sort open tickets by priority, then by the *numeric* part of the ID, without mutating the input list." |
| "Write tests" | "List the edge cases the spec requires, then write one unittest per case." |

---

## 2. Log entries

### 2026-10-11 — Session 1: Understanding the task and the data model

**Goal:** Turn the brief into a concrete plan and confirm the shared interfaces.

I started by reading the repo and the team's `docs/design-decisions.md`. The AI
summarised the agreed contract back to me: tickets are dictionaries with the
eight required fields, IDs follow `T001`, new tickets start `open`, and business
functions raise `ValueError` on invalid input while never partially modifying a
ticket. That summary let me spot early that the lifecycle functions needed the
same "validate first, mutate last" rule as Engineer A's `create_ticket`.

**Learning:** The most valuable first AI task wasn't writing code — it was
reconstructing the contract from the docs so my module would fit Engineer A's
without rework.

### 2026-10-11 — Session 2: Assignment and status lifecycle (`workflow.py`)

**Goal:** `assign_ticket`, `update_status`, `reopen_ticket`.

Prompts I used (paraphrased):

- "Implement `assign_ticket` requiring a non-empty staff name, trimming
  whitespace, rejecting resolved tickets, and raising a clear error for an
  unknown ID."
- "Where should the resolved-ticket check go relative to the staff-name check,
  and why?"
- "Implement `update_status` allowing only `open → in_progress → resolved`, and
  block `in_progress` unless the ticket is assigned."

The assistant proposed a `PRIORITY_ORDER` map and an `ALLOWED_TRANSITIONS` map,
which I liked because it replaced nested `if` chains with a single lookup. It
also put all validation **before** the mutation, which satisfied the design
doc's "no partial modification" rule.

I pushed back on one detail: I wanted the resolved-ticket guard to run before
any other change, so a user who tries to touch a closed ticket always gets the
"reopen first" message rather than a confusing unrelated error.

**Learning:** A transition table is easier to read and audit than a stack of
conditionals — and easier to test exhaustively.

### 2026-10-11 — Session 3: Work queue (`get_work_queue`)

**Goal:** Open tickets only, ordered by priority then numeric ID, without
mutating the input.

The first draft used `sorted(...)` and indexed the ID with `int(ticket["id"][1:])`.
I questioned that because a malformed or non-ID value would crash the whole
queue. We replaced it with a small `ticket_number()` helper that extracts the
numeric suffix and falls back safely. I also asked for an explicit test proving
the original list is untouched, since "do not modify the original list" was a
stated requirement.

**Learning:** The AI's first answer was correct for the *happy path* but brittle
on bad data; reviewing it as a critic (not a consumer) caught it.

### 2026-10-11 — Session 4: Reports (`reports.py`)

**Goal:** Totals plus status and priority breakdowns, including zero categories.

The key requirement here is that **every** category appears even when its count
is zero, and that an empty list still returns a well-formed report. The
assistant used a dictionary comprehension over a fixed tuple of statuses and
priorities, which is exactly right — iterating over the canonical list, not over
the tickets, guarantees the zero categories show up.

**Learning:** Iterating over the *expected* categories rather than the *data* is
the trick for stable, zero-filled reports.

### 2026-10-11 — Session 5: Tests

**Goal:** Cover every case the brief lists.

I had the assistant enumerate the required cases from the brief first, then
write one `unittest` per case, grouped into classes (`AssignmentTests`,
`StatusLifecycleTests`, `ReopenTests`, `WorkQueueTests`, `ReportTests`). Beyond
the listed cases we added edge cases the brief implied: non-string staff names,
skipping `open → resolved`, moving backwards, and zero categories in reports.

I ran the suite after each class rather than writing all tests at once, so a
failure pointed at one small change.

**Learning:** Turning the spec's bullet list into a checklist of test names kept
me honest — no requirement went untested.

### 2026-10-12 — Session 6: CLI integration and coordinating with Engineer A

**Goal:** Add assign / status / reopen / work-queue / report to `main.py`
without breaking Engineer A's shared file.

This was the collaboration-heavy part. I first inspected Engineer A's branch
(`feat/1-ticket-creation`) to learn the real interface — `create_ticket`,
`save_tickets`, `load_tickets` — instead of guessing. I merged that branch in so
the CLI could work end-to-end against real storage.

The menu had to grow from three options to eight. This changed the **Exit**
option number, and Engineer A had written tests that pressed `3` to exit. Rather
than leave a confusing menu, I renumbered the menu properly **and updated
Engineer A's `tests/test_main.py`** to match, then flagged that change for review
in the PR. I did **not** touch `tickets.py` or `storage.py`.

We wrapped every action in `try/except ValueError` so bad input prints
`Error: …` instead of crashing, and I verified that a rejected action never
modifies the ticket list.

**Learning:** On a shared file, the AI is most useful for *reading the other
person's code accurately* before changing anything. The riskiest part wasn't the
logic — it was the interface and the tests another person already owned.

### 2026-10-12 — Session 7: Code review, verification and the pull request

**Goal:** Prove the work, survive review, and get it merged.

I ran a scripted end-to-end CLI session against a real `data/tickets.json`
(create → assign → `in_progress` → resolved → queue → report → reopen) and
confirmed the file persisted and reloaded.

Engineer A reviewed the work and found two real edge cases in the queue, fixed in
commit `b2e5c77`:

1. `ticket_number()` used `str.isdigit()`, which also accepts non-ASCII digits
   such as `²` that `int()` then rejects — so a malformed ID could still crash
   the queue despite the docstring's promise. The fix requires ASCII digits.
2. `get_work_queue()` indexed `PRIORITY_ORDER` directly, leaking a bare
   `KeyError` for an unknown priority. The fix routes it through a
   `priority_rank()` helper that raises `ValueError`, matching our contract.

Both were exactly the kind of "correct on the happy path, wrong on bad data"
gap my own review missed, so the review genuinely improved the module. I
re-ran the suite and confirmed the fix; the branch and PR #8 were merged into
`main`, with the remaining merges (`#9`, `#10`) bringing in Engineer A's creation
work.

Verification:

```bash
python3 -m unittest discover -s tests -v
# Ran 85 tests ... OK
```

The assistant also found that earlier commits had accidentally tracked
`__pycache__/*.pyc` files; we untracked them (they are now covered by
`.gitignore`). No `gh` CLI or token is available in this environment, so the AI
produced the compare URL and a ready-to-paste PR description, and I linked the
relevant issues (#2, #3, #7).

**Learning:** "It works in a test" and "it works as a program" are different
claims; the manual CLI run is what actually convinced me the integration held.
And a second pair of eyes catches the failure cases a first pass rationalises
away.

---

## 3. Things the AI got wrong (and I caught)

| Issue | What the AI produced | What I changed |
| --- | --- | --- |
| Brittle queue sort | `int(ticket["id"][1:])` | Added a tolerant `ticket_number()` helper |
| Shared test breakage | Renumbered the CLI menu only | Also updated Engineer A's `test_main.py` to match |
| No mutation proof | Sorted with `sorted()` and moved on | Added an explicit test that the input list is unchanged |
| Happy-path bias | First drafts handled only valid data | Added tests for non-string names, skips and backwards moves |
| Non-ASCII digit crash *(found in review)* | `str.isdigit()` accepted `²` then `int()` failed | Engineer A's `b2e5c77` requires ASCII digits |
| Bare `KeyError` on bad priority *(found in review)* | Indexed `PRIORITY_ORDER` directly | Engineer A's `priority_rank()` now raises `ValueError` |

---

## 4. What I learned

- **Spec → checklist → tests.** The fastest way to be sure I'd covered the brief
  was to convert each requirement into a named test.
- **Validate first, mutate last.** Carrying Engineer A's contract into my module
  kept failed operations from leaving tickets half-changed.
- **Review like a critic.** AI output is a strong first draft, not a final
  answer; the bugs I found were almost always on edge cases, not the happy path.
- **Read the shared file before editing it.** Coordination with Engineer A cost
  more than the code itself, and AI helped most by reading their interfaces
  accurately.
- **Reviews are part of the work.** Engineer A's follow-up fix showed the value
  of a second reviewer on exactly the boundary cases I'd glossed over.
- **Verification is my job.** Passing tests plus a real end-to-end run — not the
  AI's confidence — is what made me trust the result.

---

## 5. Definition of Done — Engineer B

- [x] Ticket assignment works correctly.
- [x] Status transitions follow the required lifecycle.
- [x] Unassigned tickets cannot move to `in_progress`.
- [x] Resolved tickets require explicit reopening.
- [x] Work queue sorting is correct.
- [x] Reports contain accurate totals and breakdowns.
- [x] Tests cover normal cases and edge cases.
- [x] All relevant tests pass (`85 tests ... OK`).
- [x] CLI integration works with ticket creation and storage.
- [x] Code is submitted through a pull request (`feat/2-status-workflow`, PR #8).
- [x] Required reviews and approvals are completed (Engineer A's review and
      hardening fix `b2e5c77`).

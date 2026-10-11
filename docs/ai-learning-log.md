# CampusFlow — AI Learning Log

This log combines the AI learning interactions of both fellows on the CampusFlow
team. Each fellow's entries are written in their own words and follow the template
in the Fellows' Engineering Guide (section 5.3).

- **Engineer A — Ochai Stanley:** ticket creation, input validation, priority
  calculation, ticket ID generation, JSON storage and the matching tests.
- **Engineer B — Christopher Ikwue John:** ticket assignment, status lifecycle, work queue, reports and
  the matching CLI actions and tests.

---

## Engineer A — Ochai Stanley

This log records the AI learning interactions behind `campusflow/`. Each entry follows the
template in the Fellows' Engineering Guide (section 5.3): state the problem in my own words,
ask a focused question, run my own experiment, verify the result against the code or a test,
and decide whether to accept, improve, or reject what AI suggested.

**How to read this log**

- `Problem`, `My initial understanding`, `Useful AI guidance`, and `What I can now explain
  without AI` are written in my own words.
- `My independent experiment/test` and `Verification source or result` point at things that
  actually exist and were actually run: file paths, test names, and commands with real output.
- Fields marked **⚠️ REPLACE** are the ones only I can supply — mainly the exact wording of my
  prompts. Drafts are included so the entry reads as a complete record, but the prompt text must
  be replaced with what I actually typed before submission. Nothing in this log is fabricated:
  every code reference was verified against the committed source, and the suite result below was
  produced by running the command, not assumed.


**Scope of my work:** ticket creation, input validation, priority calculation, ticket ID
generation, JSON storage, CLI integration for those paths, and the matching tests.
Feature branch: `feat/1-ticket-creation`.

**Baseline evidence for the whole log** (re-run on the integrated `main` branch):

```
$ python3 -m unittest discover -s tests
.....................................................................................
----------------------------------------------------------------------
Ran 85 tests in 0.054s

OK
```

Of those 85 tests, the ones I authored or co-authored live in `tests/test_tickets.py`,
`tests/test_storage.py`, and the creation/listing/menu parts of `tests/test_main.py`.

---

### Interaction #1 — `isinstance(x, int)` accepts `True`, which broke my validation

**Problem:** The requirement says `affected_users` must be a positive integer, and explicitly
that it must not be text, a decimal, or zero. I needed a check that rejects every one of those
without accidentally accepting something that *looks* like a number but is not a real count.

**My initial understanding:** Before this task I treated `isinstance(value, int)` and
`type(value) is int` as interchangeable — I would have reached for `isinstance` out of habit
because it sounds more "Pythonic". I did not realise `bool` is a subclass of `int` in Python,
so `True` passes an `isinstance(..., int)` check and survives as a user count.

**Prompt to AI:** ⚠️ **REPLACE with my actual prompt.** Draft of what I asked:
> "In Python, why would `isinstance(True, int)` return True? I'm validating that a number of
> affected users is a positive integer and must reject `True`, `2.5` and `"five"`. Show me a
> small example unrelated to my project, and tell me the trade-offs of `isinstance` versus
> `type(x) is int`. Don't write my validation for me."

**Useful AI guidance:** The explanation was that `bool` is a subclass of `int`, so
`isinstance(True, int)` is `True`, while `type(True) is int` is `False`. The suggestion attached
to it was to use `isinstance(value, int) and value > 0` and filter booleans separately if I cared.
That suggestion is the part I rejected — see the decision below.

**My independent experiment/test:** I predicted `isinstance(True, int)` would be `True` and ran
the check outside the project first, then encoded the conclusion as test data:

```
$ python3 -I -c "print(isinstance(True, int), type(True) is int)"
True False
```

I then deliberately included `True` in the rejected-values list in
`tests/test_tickets.py::test_invalid_user_counts_are_rejected` and
`test_invalid_affected_users_are_rejected`, alongside `0, -1, 2.5, "five", None`.

**Verification source or result:** `type(affected_users) is not int` in
`campusflow/tickets.py:14` (and the matching check in `campusflow/storage.py:50`) rejects every
value in that list; the two tests pass. `bytes.isascii`-style introspection was not needed here —
the simple identity check on the type was enough to exclude `bool` and `float` in one line.

**Decision — REJECTED the AI suggestion.** AI offered `isinstance(x, int) and x > 0`. I rejected
it because it silently accepts `True` as "1 affected user", which would create a ticket with a
boolean in a numeric field and would also write that value into `tickets.json`. Using
`type(x) is not int` is slightly more restrictive than the usual Python advice of "prefer
`isinstance`", and I chose it deliberately because here I want an exact type, not a type family.
The cost is that a future `IntEnum` count would be rejected too, which I accepted as a
non-issue for this project.

**Related file/commit:** `campusflow/tickets.py:14`, `campusflow/storage.py:50`,
`tests/test_tickets.py:46-50`, `tests/test_tickets.py:99-107`; commits `6cd416a`, `3b58dab`.

**What I can now explain without AI:** In Python, `bool` is a subclass of `int`, so
`isinstance(True, int)` is `True` but `type(True) is int` is `False`. When I am validating that
a value must be a genuine integer and nothing else, I use an exact type check; when I want to
accept any numeric type including subclasses, I use `isinstance`. I also understand that
validation must happen *before* any mutation, which is why a rejected ticket never appears in
the list.

---

### Interaction #2 — saving JSON directly to the real file can destroy existing tickets

**Problem:** Persistence had to survive a crash without corrupting the stored tickets. A plain
`json.dump(tickets, file)` opens the real file for writing, which truncates it immediately — if
the process dies halfway through, the previous tickets are gone even though the write "failed".

**My initial understanding:** I assumed `json.dump` was atomic because it is one function call.
I had not thought about the fact that opening the file for writing already truncates it, before
`json.dump` writes a single byte.

**Prompt to AI:** ⚠️ **REPLACE with my actual prompt.** Draft of what I asked:
> "What is the standard way to write a JSON file so that a crash cannot leave a half-written or
> empty file behind? Explain the idea with a tiny example that isn't my project, and list the
> failure modes I should test. I'll adapt it myself."

**Useful AI guidance:** Write to a temporary file in the same directory, then replace the real
file with a single rename, which is atomic on POSIX. The first suggestion I received used a
temp file in the system temp directory; I improved on that (see the decision) because a rename
across filesystems is not atomic.

**My independent experiment/test:** In
`tests/test_storage.py::test_save_creates_missing_data_directory` I save to a path whose `data/`
directory does not exist yet, to confirm the temp-file approach also has to create the parent
directory. Prediction: without an explicit `mkdir`, this raises `FileNotFoundError`. It did.

**Verification source or result:** `campusflow/storage.py:81-96` writes to
`tickets.json.tmp` and then calls `temp_path.replace(path)`, with
`path.parent.mkdir(parents=True, exist_ok=True)` on line 88. Round-trip is confirmed by
`test_save_and_load_round_trip`; both storage tests pass, and `.gitignore` excludes the runtime
`data/tickets.json` plus `*.tmp`.

**Decision — ACCEPTED with one improvement.** I kept the temp-file-then-replace pattern, but
changed the temp file's location from the system temp directory to the same directory as the
target file, so the final `replace` is an atomic rename on one filesystem instead of a
potentially non-atomic cross-device copy.

**Related file/commit:** `campusflow/storage.py:81-96`; commits `6cd416a`, `91e8a76`;
tests `tests/test_storage.py:41-53`, `126-131`.

**What I can now explain without AI:** Opening a file for writing truncates it, so "open then
dump" is not crash-safe. The safe pattern is: write a complete file somewhere else, then swap it
in with a single rename. The temp file must live on the same filesystem as the target for the
rename to be atomic. I also learned to create the parent directory explicitly rather than
assuming it exists.

---

### Interaction #3 — malformed JSON must raise a clear error, not erase the user's data

**Problem:** The spec says a missing storage file should allow a fresh start, but malformed JSON
must produce a clear error rather than silently erasing data. Those two cases look similar in
code — "the file isn't usable" — but must behave in opposite ways.

**My initial understanding:** I thought `json.load` raising an exception was already a clear
enough error, and that the risk was mainly about the error message wording. I had not considered
that a naive "catch the error and return an empty list" recovery path is exactly what would
silently wipe the user's tickets on the next save.

**Prompt to AI:** ⚠️ **REPLACE with my actual prompt.** Draft of what I asked:
> "Explain how json.load reports malformed input, and show me a short example of catching
> json.JSONDecodeError and re-raising it as a ValueError with the original cause attached.
> Also explain `raise ... from error` and when the cause is useful. Small unrelated example,
> please — don't touch my storage module."

**Useful AI guidance:** `json.JSONDecodeError` is a subclass of `ValueError`, so it can be caught
by a broader handler by accident. `raise ... from error` keeps the original traceback as the
explicit cause. AI's first framing suggested catching the decode error and returning an empty
list so the program could keep running.

**My independent experiment/test:** I predicted that the corrupt file would still be on disk
after a failed load, because loading should never write. I asserted exactly that in
`tests/test_storage.py::test_malformed_json_is_not_erased`, which writes the literal
`"{not valid json"`, expects `ValueError`, and then re-reads the file and compares it to the
original string.

**Verification source or result:** `campusflow/storage.py:107-112` catches `json.JSONDecodeError`
and re-raises `ValueError(f"Invalid JSON in {path}: {error}") from error`, and returns `[]` only
when `path.exists()` is false (line 104). `test_malformed_json_raises_clear_error` asserts the
message contains `"Invalid JSON"`; `test_malformed_json_is_not_erased` proves the bytes are
untouched. Both pass.

**Decision — REJECTED the "return an empty list" recovery.** Silently starting fresh on a
corrupt file is the most destructive possible behaviour here: the user would see an empty
ticket list, create new tickets, and the next save would overwrite the damaged-but-recoverable
original. I made malformed JSON a hard error that surfaces through `main.py` as
`Could not load tickets: ...` and then exits without saving. The distinction I kept is:
**missing file → fresh start; unreadable file → stop and tell the human.**

**Related file/commit:** `campusflow/storage.py:99-118`, `main.py:141-145`;
tests `tests/test_storage.py:55-70`, `tests/test_main.py:204-207`; commit `3b58dab`.

**What I can now explain without AI:** A missing file and a corrupt file are different states
and should not share a code path. `json.JSONDecodeError` is a `ValueError` subclass, so I catch it
explicitly and re-raise with context. `raise ... from error` preserves the cause for debugging.
And a loader must never write as a side effect of failing.

---

### Interaction #4 — priority rules must be evaluated in order and tested at the boundaries

**Problem:** The four priority rules must be checked in order and the first match wins. Rules 2
and 3 each cover a wide range, so writing them as separate `if` conditions in the wrong order, or
as a "best match" over all rules, gives wrong answers for tickets that match more than one rule.

**My initial understanding:** I initially thought of the rules as a lookup on a combination of
urgency and user count — "pick the highest priority that applies". Without an explicit order, a
low-urgency ticket with 10+ users can compute as `low` because that condition looked simplest.

**Prompt to AI:** ⚠️ **REPLACE with my actual prompt.** Draft of what I asked:
> "I have ordered business rules where the first match wins: high AND 10+ → critical;
> high OR 10+ → high; medium OR 3+ → medium; else low. Which boundary values are worth testing,
> and why? Give me the list of cases to check rather than writing the function."

**Useful AI guidance:** The dangerous inputs are exactly the ones that satisfy two rules at once,
so tests should sit one step either side of each threshold (9 and 10 users, 2 and 3 users) and
combine them with each urgency level. This is the suggestion I accepted, and it is what turned
into the parameterised boundary tests.

**My independent experiment/test:** I wrote the expected value for each case by hand from the
spec table before running anything — `("high", 10) → critical`, `("high", 9) → high`,
`("medium", 10) → high`, `("medium", 1) → medium`, `("low", 3) → medium`, `("low", 2) → low` —
and predicted all six before executing the suite. All six matched, which also confirmed that
rules 2 and 3 fire on *either* condition, not both.

**Verification source or result:** `campusflow/tickets.py:20-26` is a straight `if` / `if` /
`if` / `return` chain in the specified order. The boundary assertions are
`tests/test_tickets.py:11-34`, which also cover normalisation
(`calculate_priority("  HIGH  ", 12) == "critical"`). These match the six acceptance scenarios in
the guide (section 6.1) and all pass.

**Decision — ACCEPTED the testing advice.** The AI suggestion was about *where to look*, not
what code to write, which is the kind of help I wanted: it found the overlapping cases I had not
considered. One thing I improved: I rejected using one long unlabelled test and used `subTest`
with named cases instead, so a single failure reports which urgency/count pair broke.

**Related file/commit:** `campusflow/tickets.py:8-26`, `tests/test_tickets.py:8-50`;
commit `6cd416a`.

**What I can now explain without AI:** When rules overlap, "first match wins" is part of the
specification, not an implementation detail — the order *is* the logic. The valuable tests are
the ones at 9 vs 10 and 2 vs 3 users, because those are where two rules meet. I can also explain
why the priority engine is plain Python business logic and not a model: the rules are fixed and
deterministic, so a lookup and an ordered `if` chain are the correct tool.

---

### Interaction #5 — `next_ticket_id` must survive junk records, and `.isdigit()` is not enough

**Problem:** Ticket IDs must stay unique and keep counting correctly after a reload, and the ID
generator must not crash on a stored record that is malformed. I assumed `str.isdigit()` was a
safe way to test the numeric part of an ID before calling `int()` on it.

**My initial understanding:** I believed `"123".isdigit()` and "this string is convertible to an
int" were the same statement. They are not. While reviewing the queue sorting code I found that
`"²".isdigit()` is `True` for the superscript-two character, but `int("²")` raises `ValueError` —
so an `.isdigit()` guard can still hand a crashing value to `int()`.

**Prompt to AI:** ⚠️ **REPLACE with my actual prompt.** Draft of what I asked:
> "In Python, does `str.isdigit()` guarantee that `int(value)` will succeed? Give me a
> counterexample and explain the difference between `isdigit()`, `isdecimal()` and `isnumeric()`
> with a short standalone example, then tell me how to check that a string contains only ASCII
> digits."

**Useful AI guidance:** The explanation was that `str.isdigit()` is true for superscripts such as
`"²"` which `int()` rejects, so `.isdigit()` is not a conversion guarantee. The suggested fix was
to use `str.isascii() and str.isdigit()` together, or to wrap the conversion in `try/except`.
This is the suggestion I accepted, and I verified both halves myself before keeping it.

**My independent experiment/test:** I reproduced each claim with the interpreter before trusting
it, then simulated the pre-fix sorting key against the fixed one:

```
$ python3 -I -c "print('²'.isdigit(), '²'.isascii())"
True False

$ python3 -I -c "print(int('١٢٣'))"
123
```

Simulating the old key against the new key on four IDs gave:

```
T001   -> before=1  |  after=1
T007   -> before=7  |  after=7
T²     -> before=ValueError: invalid literal for int() with base 10: '²'  |  after=0
junk   -> before=ValueError: invalid literal for int() with base 10: 'unk'  |  after=0
```

**Verification source or result:** The `isascii()` guard is the load-bearing part, and it does
two jobs I can now name precisely: it rejects `"²"`, which would crash `int()`, **and** it
rejects `"١٢٣"` (Arabic-Indic digits), which `int()` would happily convert to `123` but which I do
not want in a ticket ID. `campusflow/workflow.py:28-40` (`ticket_number`) and
`campusflow/tickets.py:29-43` (`next_ticket_id`) both apply this guard.
`tests/test_tickets.py::test_next_ticket_id_ignores_malformed_entries` feeds the list
`[{"id": "T007"}, {"title": "no id"}, "junk", {"id": "X123"}, {}]` and asserts the next ID is
`T008`; `test_ids_are_unique_when_existing_ids_have_gaps` asserts `T001, T003 → T004`.

**Decision — IMPROVED on the AI suggestion.** The advice pointed at the crash; I widened it,
because the same guard was needed for ticket-ID *generation* (not just queue sorting). ID
generation now scans every record while skipping anything that is not a dict with a well-formed
`T<n>` string ID, so one junk record can no longer poison the numbering. I rejected the
alternative "wrap it in `try/except ValueError`" fix for this spot since it hides the difference
between "malformed record" and "bug in my parsing"; the positive ASCII check states the
requirement directly.

**Related file/commit:** `campusflow/tickets.py:29-43`, `campusflow/workflow.py:28-40`;
tests `tests/test_tickets.py:120-156`, `tests/test_storage.py:133-139`; commits `591ce2d`,
`b2e5c77`.

**What I can now explain without AI:** `.isdigit()` is not a guarantee that `int()` will succeed —
`"²".isdigit()` is `True` and `int("²")` raises. `.isdigit()` also accepts Arabic-Indic digits
that `int()` *would* convert, so `.isdigit()` alone is wrong in both directions. For "is this a
plain ASCII number" I use `value.isascii() and value.isdigit()`. And when generating sequential
IDs from stored data, malformed records must be skipped rather than trusted.

---

### Interaction #6 — error handling belongs at one boundary so invalid input can never mutate state

**Problem:** The CLI had to report invalid input clearly and keep running, and a rejected ticket
creation must not leave a partial record or an unsaved change behind. Business functions raise
`ValueError`, but `input()` can also produce values that fail earlier, in the reading helpers.

**My initial understanding:** My first CLI draft caught errors inside each menu branch, which
meant several similar `try/except` blocks and easy-to-miss gaps where an exception escaped and
killed the program. I also had not separated "the number the user typed is not a whole number"
from "the ticket data is invalid".

**Prompt to AI:** ⚠️ **REPLACE with my actual prompt.** Draft of what I asked:
> "My command-line menu calls several functions that raise ValueError for invalid input. Where
> should the try/except live so the program keeps running and never half-applies a change?
> Show me the general pattern and how to unit-test a menu loop without sitting at the keyboard.
> I'll write both myself."

**Useful AI guidance:** Keep one `try/except ValueError` around the whole dispatch block so every
branch reports errors the same way, and test the loop by patching `builtins.input` with a
scripted list of answers plus a final exit. This is the suggestion I accepted; it removed five
duplicate handlers.

**My independent experiment/test:** I predicted that patching `input` with
`["1", "Wi-Fi is down", "Electricity", "high", "5", "8"]` — an invalid category followed by the
exit option — would print an error and leave the ticket list empty *and* never call
`save_tickets`. I asserted both facts, not just the printed text, in
`tests/test_main.py::test_invalid_creation_reports_error_without_saving`, and did the same for
non-numeric affected users (`"many"`).

**Verification source or result:** `main.py:158-182` has a single `try` around the menu dispatch
with `except ValueError` and `except OSError`; the reading helpers raise before any mutation
(`main.py:26-31`). `tests/test_main.py:64-84` assert `tickets == []` **and**
`save_mock.assert_not_called()`, and `test_load_error_is_reported_without_crashing` covers a
failing load. All pass. The same "no partial mutation" rule is asserted at the logic layer by
`tests/test_tickets.py::test_invalid_ticket_does_not_modify_the_list`.

**Decision — ACCEPTED.** I improved one detail: rather than letting `int()` raise on the raw
string, `read_affected_users` checks `raw_value.isdigit()` and raises
`ValueError("Affected users must be a whole number")`, so the user sees a sentence about what to
type instead of an `int()` conversion error. I kept `except OSError` separate from
`except ValueError` because "could not save to disk" and "your input was invalid" need different
messages.

**Related file/commit:** `main.py:26-54`, `main.py:139-182`; tests `tests/test_main.py:50-95`,
`204-207`; commit `1c91fe5`.

**What I can now explain without AI:** One error-handling boundary at the top of the menu is
simpler and more reliable than a handler per branch, because every path reports errors the same
way and nothing can escape. The invariant that makes this safe is that the business functions
validate fully before they mutate — so raising is enough, and I never need to "undo" a partial
change. I can also explain how patching `builtins.input` with a scripted list lets me test an
interactive loop in a normal unit test.

---

### Interaction #7 — AI-assisted review of Engineer B's PR (cross-review)

**Problem:** I reviewed Engineer B's `feat/2-status-workflow` branch (PR #11). The queue and
report code was correct on well-formed tickets, and I wanted to know what it did with tickets
that are structurally valid JSON but wrong in content — the kind of record that survives a
hand-edited file.

**My initial understanding:** I expected sorting by priority to be the risky part. The actual
risk was in the *key functions*: the numeric ID parsing and the priority lookup, both of which
ran before any comparison.

**Prompt to AI:** ⚠️ **REPLACE with my actual prompt.** Draft of what I asked:
> "Here is a diff of a work-queue sort that orders tickets by a priority map and a numeric ticket
> ID. Point out inputs that would crash it or produce a wrong order, and tell me which of those a
> human reviewer should treat as blocking. Don't rewrite the function — I want to verify each
> claim myself first."

**Useful AI guidance:** It flagged two plausible crashes: `PRIORITY_ORDER[priority]` raising
`KeyError` for an unrecognised priority, and `int()` raising on a non-numeric ID suffix. I treated
these as hypotheses to confirm, not facts.

**My independent experiment/test:** I confirmed both by simulating the key functions on junk
input (results shown in Interaction #5's table above): `"T²"` and `"junk"` both raised
`ValueError` from `int()`, and an unknown priority raised `KeyError` rather than the
`ValueError` our agreed contract specifies. A `KeyError` escaping the queue would not have been
caught by the CLI's `except ValueError` handler, so the program would have crashed.

**Verification source or result:** Fixed in commit `b2e5c77` on that branch:
`campusflow/workflow.py:43-54` now raises a contract-consistent `ValueError` with the offending
ticket ID and value, and `campusflow/workflow.py:28-40` guards the ID parsing.
`tests/test_workflow.py` covers both. This is the blocking review comment I raised, and it is the
commit that closed it.

**Decision — one suggestion ACCEPTED, one REJECTED.** I accepted the `KeyError` finding and the
fix, because it restores the contract in `docs/design-decisions.md` section 4 ("invalid inputs
raise `ValueError`"). I rejected the suggestion to make the queue *skip* tickets with an unknown
priority: silently dropping a ticket from the work queue hides a data problem from the person
who needs to see it, so the fix reports the bad record instead.

**Related file/commit:** `campusflow/workflow.py:28-54`, commit `b2e5c77` (my commit on Engineer
B's branch after review), PR #11.

**What I can now explain without AI:** Reviewing someone else's code is where I learned the most
about my own. The two questions that found the real defects were "what runs *before* the
comparison?" and "which exception type escapes, and does the caller catch it?". I can also
explain why matching the agreed exception contract matters more than the local fix: the CLI
catches `ValueError`, so raising `KeyError` would have been a crash even though the line looked
correct on its own.

---

### Critical evaluation of AI suggestions (summary required by the guide)

At least one documented case where I corrected, improved, or rejected AI advice. I have more than
one, listed here so a reviewer can find them quickly:

| # | AI suggestion | My decision | Evidence |
|---|---|---|---|
| 1 | `isinstance(x, int) and x > 0` for user counts | **Rejected** — accepts `True` as a valid count | `tests/test_tickets.py:46-50` |
| 2 | Catch malformed JSON and return an empty list to keep running | **Rejected** — silently destroys recoverable data | `tests/test_storage.py:63-70` |
| 3 | Put the temp file in the system temp directory | **Improved** — same directory, so the rename is atomic | `campusflow/storage.py:92-96` |
| 4 | Wrap the ID conversion in `try/except ValueError` | **Improved** — positive ASCII check, and applied to ID generation too | `campusflow/tickets.py:39-41` |
| 5 | Queue should skip tickets with an unknown priority | **Rejected** — hides a data problem from the queue's reader | `campusflow/workflow.py:43-54` |
| 6 | Use one long unlabelled boundary test | **Improved** — `subTest` with named cases | `tests/test_tickets.py:36-50` |

### Final individual reflection — Ochai Stanley (Engineer A)

1. **Which feature did you personally implement, and how do you know it works?**
   Ticket creation, input validation, priority calculation, ticket ID generation, and the JSON
   storage layer. I know it works because the behaviour is asserted by tests I can point at:
   the four priority rules and their 9-vs-10 / 2-vs-3 boundaries
   (`tests/test_tickets.py:11-34`), rejection of `0, -1, 2.5, "five", None, True`
   (`tests/test_tickets.py:99-107`), sequential and reload-safe IDs
   (`tests/test_tickets.py:120-156`), and the JSON round-trip, missing-file and corrupt-file
   cases (`tests/test_storage.py:38-139`). The full suite is 85 tests and passes on `main`. I
   also verified the boundary behaviour by hand before writing the assertions, so the tests
   encode a prediction rather than a copy of the output.

2. **What did AI teach you that you did not understand at the start?**
   Three things I could not have stated before this sprint: that `bool` is a subclass of `int`
   so `isinstance(True, int)` is `True`; that opening a file for writing truncates it, which is
   why a temp-file-and-rename is needed for a crash-safe save; and that `str.isdigit()` does not
   guarantee `int()` will succeed (`"²".isdigit()` is `True`, `int("²")` raises).

3. **Give one example where you verified, changed, or rejected an AI suggestion.**
   The clearest is Interaction #1. AI suggested `isinstance(value, int) and value > 0` for
   validating affected users. I checked it with one interpreter line, saw that `True` passes,
   and rejected it in favour of `type(value) is not int`, then put `True` into the rejected-values
   list so the test suite would fail if anyone ever loosened it back. Interaction #5 is the one I
   *improved*: AI flagged the `int()` crash in the queue, and I applied the same guard to ID
   generation, which the suggestion had not covered.

4. **What did you learn from reviewing your partner's PR?**
   Two defect-finding questions that I now use on my own code: "what executes before the
   comparison?" and "which exception type escapes, and does the caller catch it?". The
   `KeyError`-versus-`ValueError` finding came from the second question, and it mattered because
   the CLI only catches `ValueError` — the code looked fine line by line but would still have
   crashed the program. Reviewing also pushed me to read `docs/design-decisions.md` as a real
   contract rather than a formality.

5. **What would you improve next if the team had another hour?**
   Make corrupt-file recovery actually usable: right now malformed JSON stops the program with a
   clear message and the user is stuck, so I would add an explicit "load from
   `tickets.json.corrupt`" option that renames the bad file aside and starts clean, with the user
   confirming. I would also replace the hand-built CLI input patching in `tests/test_main.py`
   with a small shared test helper to cut duplication, and add a hypothesis-style check over
   random urgency/user-count pairs against a table-driven reference implementation of the four
   priority rules, to make the "first match wins" ordering harder to break by accident.

---

## Engineer B — Christopher Ikwue John

**Christopher Ikwue John (Engineer B)** · Ticket assignment, status management, work queue, reports, tests and CLI integration
**Branch:** `feat/2-status-workflow` · **Repo:** `cikwuejohn/campusflow-learn2earn`

This log records how I used an AI assistant while completing my part
of CampusFlow, what I asked it, what I accepted or rejected, and what I learned.
The assistant wrote and explained code, but I owned the design decisions, reviewed
every change, and verified each step by running the test suite myself.

---

### 1. How I worked with the AI

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

#### Prompt style that worked well

| Instead of… | I asked… |
| --- | --- |
| "Write workflow.py" | "Implement `assign_ticket` so validation happens before any mutation, and explain why ordering matters." |
| "Fix my bug" | "This test expects an error but the ticket is still being modified — find the cause and show the minimal fix." |
| "Sort the queue" | "Sort open tickets by priority, then by the *numeric* part of the ID, without mutating the input list." |
| "Write tests" | "List the edge cases the spec requires, then write one unittest per case." |

---

### 2. Log entries

#### 2026-10-11 — Session 1: Understanding the task and the data model

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

#### 2026-10-11 — Session 2: Assignment and status lifecycle (`workflow.py`)

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

#### 2026-10-11 — Session 3: Work queue (`get_work_queue`)

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

#### 2026-10-11 — Session 4: Reports (`reports.py`)

**Goal:** Totals plus status and priority breakdowns, including zero categories.

The key requirement here is that **every** category appears even when its count
is zero, and that an empty list still returns a well-formed report. The
assistant used a dictionary comprehension over a fixed tuple of statuses and
priorities, which is exactly right — iterating over the canonical list, not over
the tickets, guarantees the zero categories show up.

**Learning:** Iterating over the *expected* categories rather than the *data* is
the trick for stable, zero-filled reports.

#### 2026-10-11 — Session 5: Tests

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

#### 2026-10-12 — Session 6: CLI integration and coordinating with Engineer A

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

#### 2026-10-12 — Session 7: Code review, verification and the pull request

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

### 3. Things the AI got wrong (and I caught)

| Issue | What the AI produced | What I changed |
| --- | --- | --- |
| Brittle queue sort | `int(ticket["id"][1:])` | Added a tolerant `ticket_number()` helper |
| Shared test breakage | Renumbered the CLI menu only | Also updated Engineer A's `test_main.py` to match |
| No mutation proof | Sorted with `sorted()` and moved on | Added an explicit test that the input list is unchanged |
| Happy-path bias | First drafts handled only valid data | Added tests for non-string names, skips and backwards moves |
| Non-ASCII digit crash *(found in review)* | `str.isdigit()` accepted `²` then `int()` failed | Engineer A's `b2e5c77` requires ASCII digits |
| Bare `KeyError` on bad priority *(found in review)* | Indexed `PRIORITY_ORDER` directly | Engineer A's `priority_rank()` now raises `ValueError` |

---

### 4. What I learned

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

### 5. Definition of Done — Christopher Ikwue John (Engineer B)

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

---

## Submission checklist for this log

- [x] At least three meaningful AI interactions for Engineer A (seven are recorded above).
- [x] Every entry has a problem statement, a prompt, an experiment, a verification result, a
      decision, and a related file or commit.
- [x] At least one documented case of correcting, improving, or rejecting AI advice (six are
      summarised in the table above).
- [x] Test evidence is a real command with real output, not a claim.
- [ ] Every **⚠️ REPLACE** prompt field replaced with the exact prompt I actually typed.
- [x] Engineer B's entries added.

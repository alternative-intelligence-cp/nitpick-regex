# `tests/rejection/` — refusals about **using this library**

Created at cycle 0.0.3. Declared as `[[test]] name = "rejection"`, stage
**`check`** — *"refused by the frontend with **exactly** the expected codes"*
(`../../meta/specs/BUILD.md` §3, rules B-6, B-7, B-7a).

## How this differs from `../probe/refused/`

Both directories hold files that must **not** compile, and the distinction is
the subject, not the mechanism:

| | Subject | Example |
|---|---|---|
| `tests/probe/refused/` | **the language** — what Nitpick will not let anyone write | `prove` is `NITPICK-RUNG-001` |
| `tests/rejection/` | **this library's contract** — what a consumer can get wrong | a `failsafe` that does not name a system arm |

A probe's refusal is a fact about the compiler. A rejection fixture's refusal is
a promise `nregex` makes to the programs that import it, and it is the only kind
of test that can hold one.

## Why these two, and not the one you would write first

- **`failsafe_missing_system_arm.npk`** — `NITPICK-REACH-002`. `(*)` discharges
  exhaustiveness and **nothing else**; the diagnostic says so in as many words:
  *"`(*)` counts for nothing here"*.
- **`failsafe_not_exhaustive.npk`** — `NITPICK-PICK-003`. The `(*)` is missing
  and every named arm is present. Two rules, two codes, and **neither discharges
  the other** — which is what a consumer gets wrong, because "I added a
  wildcard" reads like "I am covered".

**The obvious third fixture does not exist, and the reason is measured.** A
consumer that omits the `(ERegexPattern)` arm **still compiles**: nothing in it
can raise one while the public surface has no callable entry point, so
REACH-002 does not demand the arm yet. That was control **E4** at cycle 0.0.1
(`../conformance/TRANSCRIPT.txt`). The day `regex_compile` exists, it changes,
and that is when the fixture is worth writing.

## Why they are the standing instance of rule B-7

Both import `../../src/lib.npk` by a **relative** path, because every import
here is relative until O-G3 closes (B-15). If either path is typo'd or the file
moves, `npkc` exits **1** with `NITPICK-RESOLVE-005` — a genuine refusal, and
these tests want a refusal. Under a *subset* rule they would pass, having
refused the **path** rather than the thing under test, and nothing anywhere
would report it.

**Code-set equality (B-7, D-237) is the single thing that closes that hole**, and
the harness names `RESOLVE-005` specially when it fires so the reader is not left
guessing. `harness/selfcheck.py` case 3a constructs the mistyped-path version on
every run and requires the harness to catch it.

## Writing another

- **Name every code you expect**, and only those. A `check` test that names no
  code asserts nothing (B-7a): exit 1 alone cannot tell "refused for the reason
  this test is about" from "the file was not there".
- **`// expect-error-at: L:C` is worth pinning** — it separates "refused with
  this code" from "refused with this code *at the failsafe*". It is also
  brittle: adding a line above the span moves it, and both fixtures here had
  their line numbers corrected by measurement rather than by counting.
- **Measure, never predict.** Run
  `$NPKC tests/rejection/<file>.npk -o /dev/null` and read the span it prints.
- **Assert the specific exit integer.** `npkc` exit **2** is not a refusal — the
  driver could not proceed and judged nothing, silently, with an empty stderr.
  The harness says so by name; a test that treated `!= 0` as a refusal would
  pass on a broken command line.

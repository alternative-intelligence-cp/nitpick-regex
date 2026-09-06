# Cycle 0.12 — Hardening

**The fuzzers, the linear-time sweep, the stress sweep, and the verification
obligations reconciled.**

## Decisions in

RX-072, and `VERIFICATION.md` in full.

**Open questions to settle:** O-P1 (does the step counter ship? —
recommendation: yes, with the cost measured at 0.13 before confirming).

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.12.0 | **The pattern fuzzer** — structured trees over the grammar | a hundred million patterns, clean |
| 0.12.1 | **The haystack fuzzer** — bytes, invalid UTF-8, pattern-derived strings | every engine agrees, nothing allocates, nothing traps |
| 0.12.2 | **The linear-time sweep** — a generated family, not four cases | the guarantee measured across a pattern space |
| 0.12.3 | **The stress sweep** — `// stress: 40` where it belongs | forty runs, same answer |
| 0.12.4 | **Verification reconciliation** — the obligation list against the code | an obligation list that is true |
| 0.12.5 | **The audit** — the tree read against the specifications | a findings list, and the specs corrected |
| 0.12.6 | **Close** | `done/0.12/`, `0.13.0.md` written |

## Checklist

### 0.12.0 — the pattern fuzzer
- [ ] `tools/fuzz_pattern.py`: random trees over `SYNTAX.md` §1, biased toward nesting, large repetitions, large classes, and every refused construct
- [ ] the invariants (V-17): the compiler produces a program **or** a `PatternError` with a valid offset; it never traps; it never exceeds a bound without reporting it; it always terminates
- [ ] also fuzz **raw bytes as patterns**, since a pattern arrives from a user
- [ ] a hundred million inputs clean
- [ ] everything it found committed as a permanent fixture, minimised, with the defect named

### 0.12.1 — the haystack fuzzer
- [ ] corpus patterns against generated haystacks: random bytes, invalid UTF-8, long runs, and strings derived from the pattern itself (the ones most likely to match)
- [ ] the invariants: **every engine agrees**; the naive oracle agrees where it finishes; **no search allocates**; no search traps; offsets are within the haystack and, in Unicode mode, on UTF-8 boundaries
- [ ] the UTF-8 boundary invariant is the one that would catch a byte-automaton defect from 0.4 that nothing else has

### 0.12.2 — the linear-time sweep
- [ ] a **generated family** of adversarial patterns, not the four hand-picked ones: nested quantifiers to depth 5, ambiguous alternations, `a?{n}a{n}` for n up to 50, and their combinations
- [ ] each against geometrically increasing haystacks
- [ ] step growth no faster than linear within the stated constant, for **every** engine
- [ ] the worst observed constant recorded — the number that says how tight the bound really is

### 0.12.3 — the stress sweep
- [ ] `// stress: 40` on: the `Cache` shared across threads, the DFA cache clearing under contention, and anything the fuzzers found that was timing-shaped
- [ ] **a red under stress is a stop sign, never a retry** — every timing-shaped defect the compiler found looked like flakiness first

### 0.12.4 — verification reconciliation
- [ ] `VERIFICATION.md`'s obligation list read against the code, entry by entry
- [ ] every obligation the code generates that the list does not name, added
- [ ] every obligation the list names that the code does not generate, removed or scheduled
- [ ] the comment-form contracts checked to be **syntactically what they will be**, by pasting one into a scratch file and confirming the compiler's verdict on it — probe 13's check, repeated against the real clauses. **The expected verdict is per construct and must not be assumed uniform (`VERIFICATION.md` P-1a, RX-127):** `prove`, `requires` and `ensures` refused `NITPICK-RUNG-001` at pin `3d15ac9` and `limit<Rules>` did not, because it is live. A clause that has landed is checked by **running** it, not by confirming a refusal that will no longer come — and a clause that has landed is also re-measured for what it charges a consumer's `failsafe`, which is how RX-127 decided against `limit`
- [ ] the property tests standing in for each, present and green
- [ ] the whole list handed forward as `meta/OBLIGATIONS.md`, ready for the compiler's verified build (P-12)
- [ ] O-P1 decided, pending 0.13's measurement

### 0.12.5 — the audit
- [ ] every specification document read against the code implementing it
- [ ] every numbered rule either implemented, refused with a reason, or struck by a decision
- [ ] **a rule with no implementation and no refusal is the dormant-rule pattern**, which the compiler found three times
- [ ] the tree checks' coverage reviewed: is there a document nothing diffs against?
- [ ] `check_specs_current`'s backlog drained

## Gate

A hundred million fuzz inputs clean across both fuzzers, the linear-time sweep
green over a generated family, and an obligation list that is true.

## Watch for

- **The audit is the most valuable part and the easiest to shorten.** The
  compiler's cycle 0.6 found every one of its holes this way and none of them
  by a test.
- **The fuzzers will find things in 0.4's UTF-8 compiler**, because that is
  where a subtle omission hides. A finding there goes back to 0.4's exhaustive
  round trip as a new case, not into a patch at the point of failure.
- **"No search allocates" is checkable and worth checking**, because it is what
  makes `SAFETY.md` S-5's "matching cannot trap" true rather than merely
  likely.

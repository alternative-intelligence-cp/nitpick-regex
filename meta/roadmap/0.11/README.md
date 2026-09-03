# Cycle 0.11 — The optional engines

**The one-pass NFA and the bounded backtracker.** Latency optimisations for
capture-heavy workloads, added after there is something to measure.

## Why here and not earlier

RX-040: a Pike VM plus a lazy DFA plus prefilters is a defensible 1.0. These two
make captures faster on the patterns that qualify, and "which patterns qualify"
is a question best answered against a working library and a real corpus rather
than in the abstract.

**Both are optional in the strongest sense**: if either fails its gate, it does
not ship, the meta-engine does not know about it, and nothing else changes.
That is worth stating because it makes this the cheapest cycle to abandon.

## Decisions in

RX-040, RX-041, RX-044. Settled. **No open questions.**

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.11.0 | **One-pass eligibility** — which programs qualify, computed at compile time | a stated, tested predicate |
| 0.11.1 | **The one-pass NFA** — captures in `O(n)` with no thread set | corpus agreement on eligible patterns |
| 0.11.2 | **The bounded backtracker** — captures on short haystacks | corpus agreement within its bounds |
| 0.11.3 | **Meta-engine integration** — the decision order extended | RX-041 in full, five engines |
| 0.11.4 | **Close** | `done/0.11/`, `0.12.0.md` written |

## Checklist

### 0.11.0 — one-pass eligibility
- [ ] a program is one-pass when, at every state, no two outgoing transitions can be taken on the same input byte — so there is never a choice to record
- [ ] computed at compile time, cached in the program's flags
- [ ] the predicate is **conservative**: a program wrongly judged not-one-pass is slow; one wrongly judged one-pass is **wrong**
- [ ] a test over the corpus recording which patterns qualify — the number that says whether this engine was worth building

### 0.11.1 — the one-pass NFA
- [ ] captures without a thread set: one state, one capture array, no copying
- [ ] **the gate**: over every eligible corpus pattern, identical offsets and slots to the Pike VM
- [ ] a test that an ineligible pattern is never routed here, by forcing it and asserting a refusal rather than a wrong answer

### 0.11.2 — the bounded backtracker
- [ ] a backtracking matcher with a **visited set** — `(program_counter, haystack_offset)` pairs — which is what makes it `O(m·n)` rather than exponential
- [ ] the visited set bounded by `program_size × haystack_len`, so it is used only when that product fits a stated budget
- [ ] **this is not RX-009's declined engine.** It supports no lookaround and no backreferences; it is a different implementation of the same language, faster on short haystacks. A comment at the top says so, because the name invites the confusion
- [ ] **the gate**: over every corpus case within its bounds, identical results to the Pike VM

### 0.11.3 — meta-engine integration
- [ ] `ENGINES.md` R-24's order extended to five engines
- [ ] still deterministic (R-22)
- [ ] **the full cross-engine run over five engines**, and with each optimisation off
- [ ] the linear-time property test through every engine

### 0.11.4 — close
- [ ] the measured benefit recorded per engine — and **an engine that did not earn its keep is removed**, not kept out of politeness
- [ ] findings written; `0.12.0.md` written; archived

## Gate

Both engines agree with the Pike VM over every case in their domain, the
five-engine cross run is green, and the measured benefit of each is recorded.

## Watch for

- **The bounded backtracker's name is a trap.** It has nothing to do with the
  backtracking RX-003 refuses: it has a visited set, it is linear, and it
  supports exactly the same language. Somebody will read the name and try to
  add lookaround to it.
- **One-pass eligibility wrong in the permissive direction is a silent wrong
  answer.** Conservative means: when in doubt, not one-pass.
- **An engine that does not measurably help should not ship.** Every engine is
  a permanent correctness obligation in every future cross-engine run.

# Cycle 0.8 — The lazy DFA

**On-demand state construction over the compressed alphabet, with a bounded
cache and a fallback.**

## Decisions in

RX-042. Settled.

**Open questions to settle:** O-R2 and O-C2 (a reverse DFA and reverse programs
for finding a match's start — recommendation: decide here, and defer the
implementation to post-1.0 unless 0.7's capture measurements demand it).

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.8.0 | **State representation** — a sorted set of program counters, and its identity | two orders of one set are one cache entry |
| 0.8.1 | **On-demand construction** — the transition function, the cache | `is_match` correct and fast over the corpus |
| 0.8.2 | **The cache budget** — clearing, and the fallback rule | a 4 KiB cache still gives right answers |
| 0.8.3 | **Match end, then the Pike VM** — `find` composed | `find` correct over the corpus |
| 0.8.4 | **O-R2 decided** — reverse DFA, or not | a recorded decision either way |
| 0.8.5 | **Close** | `done/0.8/`, `0.9.0.md` written |

## Checklist

### 0.8.0 — state representation
- [ ] a DFA state is the **sorted** set of NFA program counters it represents (R-15)
- [ ] the sort is not optional: two orders for one state would be two cache entries for one state — correctness-neutral, reproducibility-fatal, and it would make 0.8.2's assertions untestable
- [ ] state lookup by that key
- [ ] the end-of-input pseudo-symbol handled as an alphabet member

### 0.8.1 — on-demand construction
- [ ] transitions computed lazily over the **compressed alphabet** (C-7), not over 256 bytes
- [ ] `is_match` correct over the whole corpus, agreeing with the Pike VM
- [ ] the state count for `\d+`, `\p{L}+` and a 50-branch alternation recorded — the numbers 0.13's benchmarks are compared against

### 0.8.2 — the cache budget
- [ ] `NREGEX_DFA_CACHE_BYTES` enforced; clearing on exhaustion (R-13)
- [ ] the states-created-per-byte measure, and the threshold below which the DFA is abandoned **for that search**
- [ ] `NREGEX_DFA_MIN_STATES` — below this the DFA gives up permanently rather than thrashing
- [ ] **the gate for this subcycle**: the whole corpus green with the cache forced to 4 KiB, so it clears constantly. Same answers, different times
- [ ] the fallback is invisible: a test asserts the answer is identical with the DFA forced off

### 0.8.3 — match end, then the Pike VM
- [ ] `find` uses the DFA for the end and the Pike VM for the start and captures (R-12)
- [ ] correct over the whole corpus
- [ ] the composition's cost recorded against the Pike VM alone

### 0.8.4 — O-R2 decided
- [ ] a reverse-compiled program and a reverse DFA would let the start be found without the Pike VM
- [ ] the cost: the compiler's output doubles, and the reverse automaton needs its own correctness argument
- [ ] **decide, and record either way.** Recommendation: not at 1.0; revisit if 0.13's benchmarks show the capture path dominating
- [ ] O-C2 (reverse programs) resolved with it

### 0.8.5 — close
- [ ] **the gate**: the DFA and the Pike VM agree over the whole corpus, including with a 4 KiB cache
- [ ] self-check case 7 goes live — a fixture passing under one engine and failing under another. **The case that proves RX-041 is doing work**
- [ ] the linear-time property test still green (it is in every gate from 0.7)
- [ ] findings written; `0.9.0.md` written; archived

## Gate

Corpus agreement with the Pike VM, including under a cache small enough to
clear constantly — and self-check case 7 live.

## Watch for

- **A DFA that is right until the cache fills** is the failure mode, and it
  only appears on large haystacks with many states. The 4 KiB-cache run is what
  makes it appear in a two-second test instead of in production.
- **The state key must be sorted.** It is the kind of thing that works by
  accident when program counters happen to be inserted in order, and stops
  working the day an optimisation reorders them.
- **The DFA cannot do captures** and every attempt to make it will be a
  correctness bug. R-12 is a hard line: a DFA state is a set and has lost which
  thread got there.

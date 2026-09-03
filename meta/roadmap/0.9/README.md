# Cycle 0.9 — Prefilters and the meta-engine

**Literal scanning that finds candidates, and the deterministic rule that
chooses an engine.**

## Decisions in

RX-043, RX-041, and `ENGINES.md` R-22 … R-24. Settled.

**Open by design:** O-F1 and O-N4 (whether SIMD scanning pays) — a
*measurement*, taken at cycle 0.13. 0.9 ships the scalar version and leaves the
seam.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.9.0 | **memchr and the first-byte set** — the scalar scanners | a candidate finder that never misses |
| 0.9.1 | **The literal prefix** — a required byte string | a substring search with a stated algorithm |
| 0.9.2 | **The meta-engine** — the decision order, `force_engine`, `last_engine` | the choice is deterministic and inspectable |
| 0.9.3 | **The full cross-engine run** — RX-041 in full for the first time | the corpus through every engine, and with each optimisation off |
| 0.9.4 | **Close** | `done/0.9/`, `0.10.0.md` written |

## Checklist

### 0.9.0 — memchr and the first-byte set
- [ ] a scalar `memchr` over `uint8[]`, and a small-set variant
- [ ] driven by `HIR.md` §5's extracted first-byte set
- [ ] **a prefilter never decides a match** (RX-043): every candidate is confirmed by a real engine
- [ ] **the property test**: for every corpus pattern and haystack, every position a real engine finds is a position the prefilter admitted. A prefilter wrong in the "too few" direction is a correctness defect, and this is what catches it
- [ ] the scanner is a separate function with a stable signature, so 0.13 can swap in a SIMD implementation and compare

### 0.9.1 — the literal prefix
- [ ] a required byte-string search, algorithm stated and recorded (recommendation: a simple two-way or memchr-plus-verify, not Boyer–Moore, because the patterns are short and the code is smaller)
- [ ] bounded by `NREGEX_LITERAL_BYTES`
- [ ] the same never-miss property test

### 0.9.2 — the meta-engine
- [ ] the decision order in `ENGINES.md` R-24, exactly
- [ ] **deterministic** (R-22): no timing, no randomness, no state carried between searches. Same program, haystack and start offset choose the same engine every time
- [ ] `RegexOptions.force_engine` and `regex_last_engine(@cache)` (R-23), both public — a user diagnosing a performance problem needs the same information the test suite does
- [ ] a test asserting the same inputs choose the same engine over a thousand repeated searches

### 0.9.3 — the full cross-engine run
- [ ] the corpus through **every** engine, forced (RX-041)
- [ ] and with each optimisation disabled in turn: prefilters off, alphabet compression off, suffix sharing off, DFA off (R-3)
- [ ] identical offsets and identical capture slots in every combination
- [ ] the run's matrix reported, so a combination that was skipped is visible

### 0.9.4 — close
- [ ] the linear-time property test still green
- [ ] findings written; `0.10.0.md` written; archived

## Gate

The corpus green through every engine **and** with each optimisation disabled
in turn. This is the first cycle where RX-041 runs in full, and it is the
strongest correctness statement the library makes.

## Watch for

- **A prefilter that misses is a silent wrong answer**, not a slow one. The
  never-miss property test is the only thing standing between a clever literal
  optimisation and a library that sometimes says "no match" about a haystack
  that matches.
- **Do not make the meta-engine adaptive.** Choosing by measured throughput
  would be faster on average and would make a bug report unreproducible.
  Deterministic and inspectable beats fast-on-average for a library whose
  selling point is that you can reason about it.
- **The SIMD seam is left, not filled.** 0.13 measures; if it loses, that
  measurement is a consumer's evidence for a movemask intrinsic (O-N4), which
  is a better request than a speculative one.

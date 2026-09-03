# Cycle 0.7 — The Pike VM

**`src/engine/`: the reference engine.** The first thing that matches, and the
thing every other engine is judged against.

## Decisions in

RX-040, RX-044, RX-061, RX-072. Settled. **No open questions.**

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.7.0 | **The thread set** — two `SparseSet`s, deduplication, the swap | the structure that makes it linear |
| 0.7.1 | **The step loop** — one haystack byte at a time, zero-width closure | `is_match` correct over the corpus |
| 0.7.2 | **Priority and captures** — insertion order, per-thread slots | leftmost-first and greediness correct |
| 0.7.3 | **Assertions** — anchors and word boundaries, including the backward decode | `\b` correct on non-ASCII haystacks |
| 0.7.4 | **The `Cache`** — allocation-free searching | zero allocator calls during a search, asserted |
| 0.7.5 | **The linear-time property test** — RX-072 goes live | `(a+)+$` is linear, measured |
| 0.7.6 | **Close** | `done/0.7/`, `0.8.0.md` written |

## Checklist

### 0.7.0 — the thread set
- [ ] two `SparseSet`s from `src/core/`, current and next, swapped per byte
- [ ] **deduplication by program counter** (R-6) — the single rule that makes it linear
- [ ] the set's capacity is the program size, so it cannot overflow by construction
- [ ] a test asserting the set never exceeds `program_size` entries, over the corpus

### 0.7.1 — the step loop
- [ ] one haystack byte per outer iteration; all threads advanced
- [ ] the transitive zero-width closure when a thread is added, in one bounded walk (R-9)
- [ ] **the closure terminates because the set is deduplicated** — `(a*)*` is the case, and a test runs it against a thousand `a`s and asserts a bounded step count
- [ ] `is_match` correct over the whole corpus, agreeing with the oracle

### 0.7.2 — priority and captures
- [ ] insertion order is thread priority; `Split`'s preferred branch inserted first (R-7)
- [ ] leftmost-first: `sam|samwise` against `samwise` matches `sam`
- [ ] greedy and lazy quantifiers correct, with cases from the corpus
- [ ] per-thread capture slots, copied on split (R-8)
- [ ] a program with no `Save` skips the machinery entirely, asserted by a step-count difference
- [ ] `NREGEX_CAPTURE_GROUPS` slots allocated from the program, not guessed

### 0.7.3 — assertions
- [ ] all six `Assert` kinds
- [ ] **`\b` decodes backward** to find the preceding codepoint (U-16): UTF-8 is self-synchronising, so it is a bounded backward scan of at most three bytes, and it is **the only backward read in any engine**
- [ ] a test with a non-ASCII haystack asserting `\b` is right — the byte-level implementation is wrong for every non-ASCII haystack and passes every ASCII test
- [ ] `\b` on an invalid UTF-8 boundary treats the byte as non-word (U-17), asserted
- [ ] `^`/`$` under `m`, and `\A`/`\z`

### 0.7.4 — the `Cache`
- [ ] `regex_cache(@re)` sized from the program (R-16)
- [ ] a search allocates **nothing** — asserted by an allocator call counter around every corpus search
- [ ] a cache too small is grown at the call; a cache from another `Regex` is reset (R-17); neither is an error
- [ ] a `// stress: 40` test with two threads borrowing one `Regex` and their own caches, asserting identical results

### 0.7.5 — the linear-time property test
- [ ] the step counter (V-15), behind the build switch
- [ ] generated patterns including `(a+)+$`, `(a|a)*$`, `(a|aa)*$`, `a?{n}a{n}`
- [ ] haystacks of geometrically increasing length
- [ ] **the gate**: step count grows no faster than linearly within a stated constant
- [ ] `(a+)+$` against 100 KiB of `a` finishes, and its step count is recorded — the number that is the whole point of RX-003

### 0.7.6 — close
- [ ] **the gate**: the oracle and the Pike VM agree over the whole corpus
- [ ] `check_inst_kinds_total`'s Pike VM half green
- [ ] findings written; `0.8.0.md` written; archived

## Gate

Oracle agreement over the whole corpus, **and** the linear-time property test
green. From this cycle onward the property test is in **every** cycle's gate
and never leaves it.

## Watch for

- **This is where "right on straight-line code, wrong after a merge" lives** —
  the compiler's cycle-0.5 lesson in this library's terms. A Pike VM that is
  right on `abc` and wrong on `(a|ab)c` passes every easy test. The corpus and
  the oracle are what find it.
- **The backward decode for `\b` is the subtle one** and the ASCII-only
  implementation passes every test somebody writes by hand.
- **Capture copying on split is the cost**, and the temptation is to share
  slots between threads. That is wrong under leftmost-first: two threads have
  different capture histories and sharing them silently reports the wrong
  group.
- **The step counter's cost is measured at 0.13** (O-P1), not guessed at now.
  Build it in behind the switch and leave the decision.

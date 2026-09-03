# Cycle 0.5 — The oracle

**`tests/oracle/`: a naive reference matcher, and the conformance corpus.** The
instrument every engine cycle after this one is judged by.

## Why before any engine

Because an instrument co-developed with the thing it judges tends to agree with
it. Written first and tested against **hand-written pattern/haystack cases**,
the oracle is a working checker on the day the NFA compiler's first line is
written — so 0.6 through 0.11 are developed against something that already
works.

This is the compiler's "instruments precede the constructs they guard", and it
is the reason this library's cycle order looks unusual.

## Decisions in

RX-070, RX-071, RX-044. Settled. **No open questions.**

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.5.0 | **The naive matcher** — backtracking over the HIR, deliberately simple | hand-written cases green |
| 0.5.1 | **The step budget** — abandoning rather than hanging | a pathological case reports *not compared*, not a failure |
| 0.5.2 | **The fixture format** — pattern, haystack, expected offsets and slots | a triple a reviewer can read in a diff |
| 0.5.3 | **The corpus runner** — the `corpus` stage | our own fixtures green through the oracle |
| 0.5.4 | **Third-party corpora** — RE2, Rust `regex`, AT&T POSIX | fetched by pinned revision, filtered where semantics differ |
| 0.5.5 | **Close** — the pending self-check cases go live | `done/0.5/`, `0.6.0.md` written |

## Checklist

### 0.5.0 — the naive matcher
- [ ] a backtracking matcher over the HIR: literals, classes, concat, alternate, repeat (greedy and lazy), groups, anchors, word boundaries
- [ ] **leftmost-first** (RX-013) — the branch and expansion order is the semantics, and the naive matcher is where that is easiest to get right
- [ ] captures recorded
- [ ] **imports nothing from `src/` but `core` and `hir`** (V-4), enforced by `check_layering`
- [ ] deliberately simple: no memoisation, no optimisation, no cleverness. It is judged on being obviously correct, not on being fast
- [ ] hand-written cases covering every `HirKind` and every construct in `SYNTAX.md`

### 0.5.1 — the step budget
- [ ] a step counter, and a bound
- [ ] a case exceeding it reports **not compared**, not failed (V-6)
- [ ] the corpus runner counts and reports how many cases were not compared, so a silent collapse to comparing nothing is visible
- [ ] `(a+)+$` against thirty `a`s is a *not compared* case, and that is the correct outcome

### 0.5.2 — the fixture format
- [ ] a text triple: pattern, haystack (with an escaping scheme for non-UTF-8 bytes), expected match offsets and capture slots
- [ ] one file per case or one file per group, decided and recorded — whichever makes a diff readable
- [ ] a fixture that came from a bug **names the bug** (V-9)
- [ ] the escaping scheme round-trips, tested

### 0.5.3 — the corpus runner
- [ ] the `corpus` stage in the harness
- [ ] our own fixtures: every construct in `SYNTAX.md`, every bound sat on exactly and exceeded by one, every refusal
- [ ] the empty-match cases, including `a*` over an empty haystack and over `bbb`
- [ ] mixed-width and non-UTF-8 haystacks

### 0.5.4 — third-party corpora
- [ ] `tools/fetch_corpora.py`, by **pinned revision**, into gitignored `meta/research/corpora/`
- [ ] `meta/research/corpora/README.md` recording which suite, which revision, and how to fetch — so a run is reproducible without the bytes living here
- [ ] **RE2's test data** — closest semantics, expectations adopted directly
- [ ] **Rust `regex`'s suite** — closest feature set; differences from `COMPAT.md` §2 filtered with the reason recorded per exclusion
- [ ] **AT&T POSIX** — leftmost-**longest** expectations, so they are filtered or reinterpreted, **not adopted wholesale** (RX-071). Every exclusion recorded
- [ ] the count of adopted, excluded and reinterpreted cases published in the cycle's close

### 0.5.5 — close
- [ ] self-check case 6 (a fixture off by one) live
- [ ] 0.2's pending normalisation test now green — the oracle can run both forms
- [ ] 0.2's pending literal-extraction property test now green
- [ ] findings written; `0.6.0.md` written; archived

## Gate

The oracle green over our own corpus and over the adopted third-party cases,
with the *not compared* count reported and understood.

## Watch for

- **The temptation to make the oracle fast.** It is not for that. Every
  optimisation is a chance for it to share a bug with the thing it judges, and
  V-6's step budget is the answer to slowness.
- **AT&T POSIX's expectations are leftmost-longest** and adopting them
  wholesale would produce hundreds of spurious failures that somebody would
  then "fix" by changing the semantics. Filter deliberately, record every
  exclusion.
- **The corpus is the library's most valuable long-lived asset** and it starts
  here. A case with no comment about where it came from is a case nobody dares
  delete.

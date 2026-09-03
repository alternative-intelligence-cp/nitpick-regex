# Cycle 0.6 — The NFA compiler

**`src/compile/`: HIR to the instruction program.**

## Decisions in

RX-030, RX-031, RX-032. Settled. **No open questions.**

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.6.0 | **The instruction set** — the eight kinds, the `Program` struct, the dump | a program that round-trips through its text form |
| 0.6.1 | **Emission** — the explicit-stack walk, every HIR kind | every kind emitted; `check_inst_kinds_total` live |
| 0.6.2 | **Repetition** — expansion under the bound, greedy and lazy `Split` order | `a{2,4}` and `a{2,}` emit the documented shapes |
| 0.6.3 | **Entry points** — the unanchored `.*?` prefix and the anchored start | both emitted always; the meta-engine chooses later |
| 0.6.4 | **Multi-pattern reservation** — the pattern id in `Match` | the field exists, unused, and every fixture carries it |
| 0.6.5 | **Close** — determinism proven | `done/0.6/`, `0.7.0.md` written |

## Checklist

### 0.6.0 — the instruction set
- [ ] the eight kinds from `COMPILE.md` §4, and no others
- [ ] `Inst` POD, `#size_of` asserted against probe 01's measurement
- [ ] `Program` with `insts`, `classes`, `byte_classes`, `start`, `start_anchored`, `capture_slots`, `flags`
- [ ] a stable text dump and its parser, round-tripping (C-19)
- [ ] `Assert`'s six kinds

### 0.6.1 — emission
- [ ] an explicit stack (RX-032, C-13); a tree check greps for self-calls in `src/compile/`
- [ ] every `HirKind` emitted
- [ ] `check_inst_kinds_total` live: every `InstKind` emitted by the compiler and handled by the oracle — the engines' half goes live per engine cycle
- [ ] `check_hir_kinds_total`'s compiler half now green
- [ ] **`Split` order is the semantics** (C-11): preferred branch first, and a test asserting that swapping it changes the answer, so the ordering is protected by something

### 0.6.2 — repetition
- [ ] `a{2,4}` expands to the documented shape; `a{2,}` to `aa` plus a `Split` loop
- [ ] greedy and lazy differ **only** in `Split` operand order, and a test asserts the two programs are otherwise identical
- [ ] `NREGEX_REPEAT_PRODUCT` already checked at the HIR (H-8), so emission expands without re-deriving — asserted by a test that the compiler does no product arithmetic
- [ ] `ProgramTooLarge` when `NREGEX_PROGRAM_INSTRUCTIONS` is exceeded

### 0.6.3 — entry points
- [ ] the unanchored `.*?` prefix compiled as a `Split` loop over the any-byte class
- [ ] `start` and `start_anchored` both emitted always (C-15)
- [ ] `IS_ANCHORED_START` from the HIR recorded in the program's flags

### 0.6.4 — multi-pattern reservation
- [ ] `Match` carries a pattern id, always zero at 1.0 (C-17)
- [ ] every committed program fixture carries the field, so 1.1's `RegexSet` does not rewrite them all
- [ ] a comment naming Q-3 at the reservation site

### 0.6.5 — close
- [ ] **the gate**: compiling the same pattern twice is byte-identical (C-18), asserted over the whole corpus
- [ ] the dump round-trips over the whole corpus
- [ ] representative programs committed as fixtures (V-10), so a compiler change is a visible diff
- [ ] findings written; `0.7.0.md` written; archived

## Gate

Deterministic compilation over the whole corpus, and the dump round-tripping.

## Watch for

- **`Split` operand order is the entire semantics of greediness and
  alternation.** A refactor that "tidies" it inverts every lazy quantifier in
  the library, and the only test that catches it is one that asserts the
  inversion changes the answer.
- **There is no engine yet**, so 0.6's tests are structural: does it emit, does
  it round-trip, is it deterministic. The behavioural test arrives at 0.7 and
  the temptation to skip the structural ones because "we will find out later"
  is how a compiler defect gets attributed to an engine.

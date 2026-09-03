# Roadmap — the cycle map

The specification set (`meta/specs/`) is written and the decisions it rests on
are in `meta/DECISIONS.md`. This is the plan built on them.

**One decision batch is settled** — RX-001 … RX-080, written with the
specification set. What remains open in `../OPEN_QUESTIONS.md` is open *by
design*: two measurements taken in the cycles that can take them, one set of
data, one item gated on the compiler's tooling, one feature kept open rather
than closed, and four that are the compiler's rather than ours. **No cycle in
this plan is blocked on a decision.**

## How this is organised

- **A cycle is a folder** — `0.0/`, `0.1/`, … — focused on **one topic**.
- **A subcycle is a file inside it** — `0.0.0.md`, `0.0.1.md`, … — one workable
  chunk, written execution-grade before its code is touched.
- **A finished cycle moves to `done/`**, so the active work stays easy to find.
- **Commit after every subcycle. Push at the end of every cycle.**
- **Every cycle's README carries a checklist.** Tick items as they land; a
  cycle whose checklist is complete is a cycle ready to close.

Each cycle's opening subcycle file is written at the **previous** cycle's
close, by the session that just learned what that cycle taught. Cycle 0.0 is
the exception — it is written up front because there is no previous cycle.

---

## The two constraints that shape everything

**`nregex` cannot be built by `npkg`**, and cross-repository imports do not
resolve (`specs/BUILD.md` §1, O-N3). So `harness/` is the build and test
runner and every import is relative, exactly as `bootstrap/harness/` precedes
`npkg` in the compiler repository. It is the first thing cycle 0.0 builds,
because everything after it is tested by it.

**The library is an automaton, not a backtracker** (RX-003). That single
decision orders the entire cycle map: there is no engine before there is a
program, no program before there is a compiler, no compiler before there is an
HIR, and — the part that looks unusual — **no engine before there is an oracle
to judge it**.

The happy consequence, and it is worth stating because it removes the largest
structural risk every other library in this ecosystem carries: **`nregex` makes
no syscall.** There is no device to double, no terminal to skip, no network to
mock. The entire suite runs anywhere, under a debugger, forty times over, from
cycle 0.0.

---

## Phase 0 — the library, bottom-up

| Cycle | Topic | Gated on |
|---|---|---|
| **0.0** | **Foundations** — the language probes, the harness, `src/core/` | — |
| **0.1** | **The pattern parser** — syntax to AST, an explicit stack, byte-accurate errors | 0.0 |
| **0.2** | **The HIR** — desugaring, normalisation, computed properties, literal extraction | 0.1 |
| **0.3** | **Unicode** — generated tables, properties, scripts, simple case folding | 0.0 |
| **0.4** | **UTF-8 automata** — codepoint ranges to byte ranges, alphabet compression | 0.3 |
| **0.5** | **The oracle** — the naive reference matcher, and the conformance corpus | 0.2, 0.3 |
| **0.6** | **The NFA compiler** — HIR to program, the instruction set, the bounds | 0.4, 0.5 |
| **0.7** | **The Pike VM** — the reference engine, captures, leftmost-first | 0.6 |
| **0.8** | **The lazy DFA** — the state cache, its budget, the fallback | 0.7 |
| **0.9** | **Prefilters and the meta-engine** — literal scanning, the deterministic choice | 0.8 |
| **0.10** | **The public API** — `Regex`, `Cache`, `Match`, `Captures`, iterators, replacement | 0.9 |
| **0.11** | **The optional engines** — the one-pass NFA and the bounded backtracker | 0.10 |
| **0.12** | **Hardening** — the fuzzers, the linear-time property test, the verification obligations | 0.11 |
| **0.13** | **Performance** — benchmarks, baselines, the regression gate, the SIMD measurement | 0.12 |
| **0.14** | **The dogfood consumer** — a real program, written against the library by a user of it | 0.13 |
| **1.0** | **Release** — documentation, the API freeze, the one-arm contract, versioning | 0.14 |

---

## What each cycle produces

### 0.0 — Foundations
The **language probes** first: fourteen small programs asking the compiler
whether the shapes this design depends on are spellable — a POD instruction
array, a payload enum in a `pick`, an explicit-stack parser, a `SparseSet` over
two `Vec`s, offsets-not-slices, `string_bytes`'s borrow edges, and — expected
to **fail** — a `comptime` pattern walker (O-N1). *A construct that parses is
not a construct that works*: the compiler's cycle 0.4 was mostly repair, and
every repair dated to the cycle that had parsed the construct.

Then the harness, its self-check, the tree checks, and `src/core/` —
`Vec<T>`, `Bytes`, `ByteSet`, `SparseSet`, `limits.npk`.

### 0.1 — The pattern parser
`src/syntax/`: the grammar in `specs/SYNTAX.md` §1, an explicit stack bounded
by `NREGEX_NEST_DEPTH`, byte offsets on every error, and every
`PatternErrorKind` in §9 provoked by a test.

**Gate:** every kind in §9 has a test that produces it, and
`check_error_kinds_tested` is green — a kind nothing can produce is a promise
the documentation makes and the code does not keep.

### 0.2 — The HIR
`src/hir/`: the flat POD arena, the nine kinds, the desugaring table, the four
computed properties in one bottom-up pass, literal extraction, and
normalisation to a canonical form.

**Gate:** structurally equal patterns produce byte-identical HIR dumps, and
`NREGEX_REPEAT_PRODUCT` refuses `((a{1000}){1000}){1000}` at the third `{1000}`
— before the memory is requested.

### 0.3 — Unicode
`tools/gen_unicode.py`, the committed tables, the regeneration check, the
property and script lookups with UAX #44 loose name matching, and simple case
folding computed as an orbit over the inverse fold map.

**Gate:** `(?i)k` matches `U+212A` and `(?i)s` matches `U+017F`. Those two
assertions are the whole reason folding is a table and not `± 32`.

### 0.4 — UTF-8 automata
`src/compile/`: codepoint ranges split at the encoding-length and prefix
boundaries into products of independent byte ranges, and the alphabet
compressed into equivalence classes.

**Gate:** a property test — for every byte pair in the same equivalence class,
every instruction accepts both or neither — and a round-trip test asserting the
union of the produced byte sequences is exactly the input codepoint range.

### 0.5 — The oracle
`tests/oracle/`: a deliberately simple backtracking matcher over the HIR,
importing nothing from `src/` but `core` and `hir`. Plus the corpus runner and
the first fixtures.

**Written before any real engine, deliberately**, and tested against
hand-written cases, so that everything from 0.6 onward is developed against an
instrument that already works.

### 0.6 — The NFA compiler
HIR to the eight-instruction program, repetition expanded under the bound, the
unanchored `.*?` prefix and the anchored entry point, capture slots emitted
only when wanted, and the stable text dump that makes a program a fixture.

**Gate:** compiling the same pattern twice is byte-identical, and the dump
round-trips.

### 0.7 — The Pike VM
The reference engine: two `SparseSet`s, deduplication by program counter,
insertion-ordered thread priority, per-thread captures, and the transitive
zero-width closure.

**Gate:** the oracle and the Pike VM agree over the whole corpus — and
`RX-072`'s linear-time property test goes live and stays in the gate for every
cycle after this one.

### 0.8 — The lazy DFA
On-demand state construction over the compressed alphabet, the bounded cache,
clearing, and the fall-back-to-Pike-VM rule.

**Gate:** the DFA and the Pike VM agree over the whole corpus, including with
the cache forced to a size that makes it clear constantly.

### 0.9 — Prefilters and the meta-engine
memchr, the first-byte set, the literal prefix, and the deterministic choice
rule with `force_engine` and `last_engine`.

**Gate:** the corpus green through every engine and with each optimisation
disabled in turn — RX-041 in full for the first time.

### 0.10 — The public API
`src/api/`: `Regex`, `Cache`, `Match`, `Captures`, the three iterators, the
template replacement, and the inspection functions. The first program a
consumer could write.

### 0.11 — The optional engines
The one-pass NFA and the bounded backtracker, each checked against the Pike VM
over the whole corpus before it is allowed into the meta-engine's decision.

### 0.12 — Hardening
The pattern fuzzer and the haystack fuzzer with their stated invariants, the
linear-time property test swept over a generated pattern family,
`// stress: 40` on anything with a timing dimension, and
`specs/VERIFICATION.md`'s obligation list reconciled against what the code
actually generates.

### 0.13 — Performance
`harness/bench.py`, the six benchmarks, the committed baselines, the 20% gate
on **steps**, and the two measurements the plan has been deferring: the SIMD
memchr against the scalar one (O-F1, O-N4), and the step counter's cost
(O-P1).

### 0.14 — The dogfood consumer
A real program in `examples/` — a `grep`-shaped tool (Q-2) — written against
the library as a consumer, with every friction recorded and triaged as a
defect, a gap, or an accepted cost.

### 1.0 — Release
`docs/` written, the public API frozen and enumerated, the **one-arm
`failsafe` contract** published, examples for every entry point, and the
version policy.

---

## Post-1.0, as a map rather than a plan

| Cycle | Topic |
|---|---|
| **1.1** | `RegexSet` — the multi-pattern API over the format 1.0 already reserves (Q-3) |
| **1.2** | The reverse DFA and one-pass capture path, if 0.13's measurements say captures are the bottleneck |
| **1.3** | Full case folding, if a consumer arrives needing it (O-U1) |
| **1.4** | Verified build — `nregex`'s obligations through the compiler's `npkg verify`, once that reaches libraries |

---

## Ordering notes

- **The probes come first, in 0.0, not last.** Fourteen small programs asking
  the compiler whether the design is spellable. One of them (09) is expected to
  fail, and its failure is the evidence for O-N1's request.
- **The harness comes first too.** It is how every later cycle is tested, and a
  suite written after the code is a suite shaped by the code.
- **The oracle precedes every engine** (0.5, before the compiler at 0.6). An
  instrument co-developed with the thing it judges tends to agree with it.
  Written first and tested against hand-written cases, it is a working checker
  on the day the first engine's first line is written.
- **Unicode (0.3) does not depend on the parser (0.1)** and could run in
  parallel with 0.1 and 0.2 if there were two writers. It is placed after them
  because the HIR is what consumes the tables and building a table with no
  consumer is how a table gets the wrong shape.
- **Every engine cycle's gate is agreement, not correctness.** 0.7 is gated on
  agreeing with the oracle, 0.8 on agreeing with 0.7, 0.9 and 0.11 on agreeing
  with everything before them. That is RX-041 as a schedule.
- **The linear-time property test enters the gate at 0.7 and never leaves.** It
  is the test that would be quietly dropped when it goes red under a refactor,
  and RX-003 is the claim it is the only evidence for.
- **Performance is 0.13, after hardening.** Measuring an implementation that is
  still changing measures noise, and the two open measurements (O-F1, O-P1) are
  both decisions that want a stable subject.
- **A decision precedes the cycle that needs it.** Each cycle's README lists
  its open questions; a cycle whose questions are open is not ready to start.

---

## What to expect, from the compiler's experience

**A construct that parses is not a construct that works.** Most of the
compiler's cycle 0.4 was repair, and every repair dated to the cycle that had
parsed the construct. Here: a program that compiles is not a program that
matches, and the cross-engine agreement runner is the analogue of the sweep
that found those.

**An analysis that is right on straight-line code and wrong after a merge
passes every test written the easy way.** Here: an engine that is right on a
simple pattern and wrong on one with an ambiguous quantifier; a parser that is
right on a whole pattern and wrong when a construct spans a buffer boundary.
Both have a dedicated test shape — the generated corpus and the fuzzers.

**Every hole was found by a check that diffs two lists, and none by a test.**
`specs/TESTING.md` §8 is this library's list of such checks, and the plan
schedules each one in the cycle that creates what it diffs.

**A suite that only ever agrees with what it is handed is worse than no
suite.** The harness self-check (V-20) is not optional and runs first — and
its most important case is the one where a fixture passes under one engine and
fails under another, because that is the case proving RX-041 is doing work.

---

## The cycle-numbering convention

Cycle numbers sort lexically only up to `0.9`; `0.10` sorts before `0.2` in a
plain listing. The compiler hit this and chose correctness over comfort, and so
does this plan: **the table above is authoritative over lexical order.**
Renumbering to keep single digits would invalidate every cross-reference the
moment a cycle is inserted, which is a cost the compiler project has paid
twice.

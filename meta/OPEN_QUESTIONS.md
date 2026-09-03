# Open questions

Everything that is not settled, each with a recommendation, so that nothing
lives only in a conversation. Three prefixes:

| Prefix | Whose |
|---|---|
| `O-x` | **ours** — a design question this project decides, at the cycle named |
| `O-N` | the **compiler's** — a gap in the language or its tooling that `nregex` needs closed, to be raised as a request |
| `Q-` | the **user's** — a question wanting an answer before the work it gates begins |

A question that gets answered moves to `DECISIONS.md` as a numbered decision
and is struck through here with the decision's number, **never deleted** — the
question is part of the record of how the answer was reached.

**No cycle in this plan is blocked on a question.**

---

## Q — for the user

### ~~Q-1 — the Unicode version to pin~~ — **SETTLED, RX-100**
The latest stable UCD when cycle 0.3 runs, in `src/unicode/version.npk`. No
floor; a bump regenerates the tables and re-runs the agreement suite.

### ~~Q-2 — the dogfood consumer for cycle 0.14~~ — **SETTLED, RX-101 and RX-102**
`grep`, built in [`nitpick-posix`](https://github.com/alternative-intelligence-cp/nitpick-posix)
rather than in this repository's `examples/` — consumers are real programs and
live in the application workbench. **RX-102** records the conformance
consequence: POSIX basic REs have back-references, this library does not, and
`grep` refuses such a pattern by name rather than acquiring a backtracker.

### ~~Q-3 — whether `RegexSet` lands at 1.0 or 1.1~~ — **SETTLED, RX-103**
1.1 for the API; the compiled program format reserves a pattern id from 1.0, so
the deferral costs nothing. Defer the API, not the representation.

### O-N1 — `comptime` cannot index a string, so a compile-time-validated pattern is not expressible
**The most valuable thing on this list.** The obvious safety win for this
library is `#regex("…")` — a form that parses the pattern *while compiling the
program*, so a malformed pattern literal is a **compile error** and
`regex_compile` never fails at run time. No regex library in any language
offers that.

Nitpick has a real `comptime` interpreter with loops, mutable locals,
`comptime func:` calls and strings (`MACRO_REFERENCE.md` §8), so it looks
available. It is not. Measured at the compiler's 1.5.0, reading
`src/frontend/resolve_type.npk`:

- `fold_expr` dispatches on integer, bool, char and string literals; `comptime`
  expressions; unary, binary, cast and unchecked-cast expressions; builtins;
  identifiers; calls; the iteration variable; and `raw` unwraps. **There is no
  arm for an index expression, a member access, an array literal or a struct
  literal.**
- `fold_string_builtin` handles exactly four names — `string_concat`,
  `string_equals`, `string_byte_length`, `string_is_empty`.

So a `comptime func:` can concatenate, compare and measure a pattern string and
**cannot look at a byte of it**. A pattern walker is not expressible.

**Ask:** one more `fold_expr` arm for indexing a string literal, or
`string_slice` in the foldable set. Small; the payoff is a class of error moved
from run time to compile time. Probe 09 in cycle 0.0 confirms the refusal and
records the exact diagnostic as the evidence for the request.

### O-N2 — `MACRO_REFERENCE.md` §8 says `const`, which no longer exists
**A documentation defect, found in the same reading.** §8's "What a name means
inside one" says *"A `const` global folds; nothing else that is a name does
(D-130)"*, and `const` was retired from the language at 1.4.2c by D-222 —
`fixed` is the one immutability keyword in every position. The **implementation
is correct**: `fold_ident` checks `QUAL_FIXED()`. The prose beside it, and the
specification, are stale.
**Ask:** amend §8 to say `fixed`, and the comment above `fold_ident`.

### O-N3 — `npkg` cannot build a library, and `[dependencies]` resolves to nothing
As `nitpick-tui` records. `npkg build` is the compiler's own bootstrap ladder;
`target = "library"` is accepted by the schema and read by nothing; the
loader's dependency-root list is created empty and never populated.
**Consequence:** `nregex` builds through its own Python harness (RX-004) and
every import is relative until this closes.
**Ask:** `npkg build` honouring `target = "library"`, and the driver populating
the resolver's roots from `[dependencies]`. Neither is on the compiler's 1.5 or
1.6 map, so this is a request, not a date.

### O-N4 — `simd` reductions lower to extract chains, so SIMD scanning may not pay
Not a defect — a measurement to report. `simd<T, N>` exists (D-194) and a byte
scan is its textbook use, but `.any()` on a `simd<bool, N>` is specified as an
**ordered extract-and-fold chain**, not a movemask plus count-trailing-zeros,
and shuffles are out by decision. So a SIMD `memchr` is correct here and its
speed is unknown.
**Ask:** none yet. Cycle 0.13 measures scalar against SIMD and records the
number; if SIMD loses, *that measurement* is a consumer's evidence for a
movemask intrinsic, which is a better request than a speculative one.

---

## O-x — ours

### Safety and engines

- **O-R1 — a bounded backtracker with lookaround, behind an opt-in.** Declined
  at 1.0 as RX-009, with three reasons. **Open by design**, with the shape
  written down: a separate `RegexBacktrack` type, a separate compile entry
  point, a step budget in the options, an explicit error when it is exhausted,
  and a documentation page stating that the linear-time guarantee does not
  apply. Declining a feature is cheaper to revisit than removing one.
- **O-R2 — a reverse DFA to find a match's start.** It is how Rust's `regex`
  avoids the Pike VM for simple captures. It doubles the compiler's output and
  needs its own correctness argument. **Decide at cycle 0.8**, where the DFA's
  capture story is settled; `O-C2` is the compiler half.

### The pattern language

- **O-Y1 — leftmost-longest (POSIX) mode.** Cheap in a Pike VM — a different
  rule for which thread wins a slot — and wanted by nobody yet.
  **Recommendation:** deferred; revisit if a consumer asks.
- **O-Y2 — whether `x` mode ignores whitespace inside classes.** Rust does not;
  Perl does with `xx`. **Recommendation:** do not, matching Rust, and refuse
  `xx` with a message naming the escape. **Decide at cycle 0.1.**

### Unicode

- **O-U1 — full case folding.** Refused at 1.0 as RX-022, because it turns a
  class from a set of codepoints into a set of strings and changes the matching
  model. **Recommendation:** stay simple; revisit only with a concrete
  consumer, and as its own cycle.
- **O-U2 — the Unicode version to pin.** See Q-1. **Open by design:** it is
  data, chosen at cycle 0.3.
- **O-X1 — the overlap with `nitpick-tui`.** Both libraries generate range
  tables from the same UCD and both need `Vec` and `Bytes`. Today
  `[dependencies]` resolves to nothing (O-N3), so each carries its own.
  **Open by design:** when resolution lands, whether a shared `nunicode`
  package is worth extracting is a real question with a real cost — a third
  repository, a third release cadence — and pre-deciding it now would be
  deciding against tooling that does not exist.

### Compilation

- **O-C1 — sharing instruction suffixes across alternations.** A real size win
  on patterns with many similar branches, a real complication in emission. It
  is an optimisation subject to RX-041's off-switch rule, so it can be added
  later with the cross-check proving it changed nothing.
  **Recommendation:** not at 1.0.
- **O-C2 — reverse programs.** The compiler half of O-R2. **Decide at cycle
  0.8.**
- **O-H1 — a reverse literal suffix for reverse searching.** Only useful once a
  reverse engine exists. **Deferred to cycle 0.8** with O-R2.

### The API

- **O-A1 — whether `Matches` implements the prelude `Iterator` trait or only
  exposes `matches_next`.** The trait gives `for … in`, which is ergonomic; it
  requires an associated type, which disqualifies the trait from `dyn` (D-160)
  — irrelevant here, since nothing erases an iterator.
  **Recommendation:** implement it *and* keep `matches_next` as the explicit
  form. **Decide at cycle 0.10**, after probe 12 says what the trait admits.
- **O-A2 — a `RegexSet` API.** See Q-3.
- **O-S1 — whether `RegexOptions` should be a `comptime` parameter rather than
  a value.** A `comptime` bound would let the program-size limit be a
  type-level fact and the arrays fixed. Against: it makes `Regex` generic over
  its options, infecting every signature that takes one.
  **Recommendation:** a plain value. **Decide at cycle 0.10.**

### Verification and performance

- **O-P1 — does the step counter ship, or is it a debug switch?** Shipping it
  makes `VERIFICATION.md` P-10's obligation about the real code and makes the
  guarantee measurable in production; not shipping saves one increment per
  inner iteration. **Recommendation: ship it**, and measure the cost at cycle
  0.13 before confirming. If it measures worse than 3%, revisit.
- **O-F1 — a SIMD `memchr`.** **Open by design:** it is a *measurement*, taken
  at cycle 0.13 against the scalar version. See O-N4.

### Build

- **O-B1 — when to migrate off the harness.** Gated on O-N3. **No action until
  then**; the harness and `npkg` run side by side with a parity check before
  the harness retires, exactly as in the compiler repository.
- **O-B2 — ship as source or as an object.** **Settled for now in favour of
  source**: it keeps the closed-world undefined-symbol scan seeing every symbol
  the program contains, and keeps whole-program verification available.
  Revisit only if build times become a real complaint from someone building a
  real program.

# `nregex` specifications

This directory is the **authority on what `nregex` does** (RX-002). Code that disagrees
with a document here is a defect in the code; a document that turns out to be
wrong is amended by a decision recorded in
[`../DECISIONS.md`](../DECISIONS.md), never by editing the text and moving on.

That discipline is borrowed, deliberately, from the compiler repository, where
the cycle notes record the same finding over and over: **the compiler and the
thing that describes it have to be diffed, because reading either alone never
reveals the gap.** A specification nothing is held to is decoration.

## Reading order

Read the first three before proposing anything. `SAFETY.md` in particular
contains the one decision the entire library is arranged around, and most
proposals that look reasonable in the abstract die on it.

| # | Document | What it settles |
|---|---|---|
| 1 | [`SAFETY.md`](SAFETY.md) | the linear-time guarantee, what it costs, the error budget, the resource bounds — **the constraints, and where they come from** |
| 2 | [`SYNTAX.md`](SYNTAX.md) | the pattern language: exactly what is accepted, what is refused, and why |
| 3 | [`BUILD.md`](BUILD.md) | how this is built and tested today, and the module and import conventions |
| 4 | [`HIR.md`](HIR.md) | the high-level intermediate: desugaring, normalisation, literal extraction |
| 5 | [`UNICODE.md`](UNICODE.md) | properties, scripts, case folding, and where the tables come from |
| 6 | [`COMPILE.md`](COMPILE.md) | UTF-8 automata, alphabet compression, the instruction set, the program |
| 7 | [`ENGINES.md`](ENGINES.md) | the Pike VM, the lazy DFA, the prefilters, and the meta-engine |
| 8 | [`API.md`](API.md) | the public surface, and the shapes the language forces on it |
| 9 | [`TESTING.md`](TESTING.md) | the harness, the naive oracle, the corpora, the fuzzer |
| 10 | [`VERIFICATION.md`](VERIFICATION.md) | the proof obligations this library carries into the compiler's cycle 1.5 |
| 11 | [`PERFORMANCE.md`](PERFORMANCE.md) | what is promised, what is measured, and what is explicitly not promised |
| 12 | [`COMPAT.md`](COMPAT.md) | how the accepted syntax compares to PCRE, RE2, Rust and POSIX |
| 13 | [`GLOSSARY.md`](GLOSSARY.md) | the words, used one way each |

## What is normative, and what is not

- A **rule** stated in these documents is normative. Rules read as statements of
  fact about the library ("a search allocates nothing"), not as intentions.
- A **rationale** paragraph explains why, and carries no obligation of its own.
- A **decision reference** — `RX-nnn` — points at
  [`../DECISIONS.md`](../DECISIONS.md), which holds the argument, the
  alternatives considered, and the date. `D-nnn` points at the **compiler's**
  `meta/specs/DECISIONS.md`; those are language decisions and are not ours to
  amend.
- An **open item** is listed at the end of the document that owns it, and is
  mirrored in [`../OPEN_QUESTIONS.md`](../OPEN_QUESTIONS.md) with a
  recommendation. A question that lives only in a conversation evaporates.

## The language, in one paragraph, for a reader arriving from C

Nitpick has no exceptions and no unhandled errors: every function returns
`Result<T>` except `main` and `failsafe`. There is no garbage collector; the
default regime is static ownership with destruction at scope exit, owning
values are move-only, and borrows are second class — they pass down the call
stack and never up, which is why a `Match` in this library carries byte offsets
rather than a slice. Plain integer overflow **traps**, and so does an
out-of-range index. There are no closures, which is why replacement takes a
template rather than a callback. `defer` runs on every normal exit path and
**not** on a trap. Read the compiler's `meta/specs/` for the full statement;
the pieces that bite hardest here are enumerated in [`SAFETY.md`](SAFETY.md) §1.

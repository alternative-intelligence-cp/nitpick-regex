# nregex

A regular-expression library for **[Nitpick](https://github.com/alternative-intelligence-cp/nitpick)** —
the safety-critical systems language. No dependencies, no libc, no C. It makes
no syscall at all: it is pure computation over bytes, and that is most of what
makes the guarantee below possible.

> **The guarantee, in one sentence: a search takes time linear in the length of
> the haystack, on every pattern, on every input, always.**

> **Status: planning.** No code yet. The specification set is in
> [`meta/specs/`](meta/specs/) and the plan in
> [`meta/roadmap/`](meta/roadmap/), written in the same order and by the same
> discipline the compiler used — specs first, then a cycle map, then
> execution-grade subcycles, then code.

---

## Why the guarantee is the whole design

Every regex engine built on backtracking — PCRE, Perl, Python's `re`, Java's,
JavaScript's, .NET's — can be made to run for longer than the universe has
existed by an input of a few dozen characters against a pattern of a few dozen
characters. `(a+)+$` against `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa!` is the textbook
one. It is called ReDoS, it has taken down Cloudflare and Stack Overflow, and
it is a **denial of service triggered by data somebody else controls**.

In a language whose entire proposition is that a failure is a controlled stop
chosen by the programmer, a library that lets a remote string hang the process
is not a library that belongs in it. So `nregex` is built on **finite automata**
— Thompson construction, a Pike VM, a lazy DFA — where the work is bounded by
the product of the pattern size and the haystack size and cannot be otherwise.
This is the choice RE2 and Rust's `regex` made, for the same reason.

**The price is stated plainly and is not softened: there are no backreferences
and no lookaround.** Neither describes a regular language, and both are exactly
what makes backtracking unavoidable. A pattern needing them is refused at
compile time, by name, with the position — never accepted and then slow.

## What follows from it

**Matching cannot fail and cannot trap.** Every way a pattern can be wrong is
found when it is compiled. Once you hold a `Regex`, a search returns an answer
or the absence of one; there is no error path, no allocation, and no
possibility of a stop. That is why importing this library costs your program's
`failsafe` **exactly one arm**.

**The same pattern and the same haystack give the same answer, always.** The
engine chosen internally — Pike VM, lazy DFA, one-pass, prefiltered — is a
performance decision that can never change a result, and the test suite proves
it by running every case through every engine and requiring agreement.

**Nothing is hidden.** The mutable state a lazy DFA needs lives in a `Cache`
value the caller owns and passes in, so a `Regex` is immutable, shareable
across threads with no lock, and a search allocates nothing.

**Every bound is named, stated, and tested** — program size, nesting depth,
repetition expansion, DFA cache bytes. A pattern that would exceed one is
refused when it is compiled, and the DFA cache falls back to the Pike VM rather
than growing.

---

## What it will provide

| Layer | Contents |
|---|---|
| **syntax** | the pattern parser — an explicit stack, never native recursion, with byte-accurate error positions |
| **hir** | desugaring and normalisation into a high-level intermediate: literals extracted, classes computed, repetitions bounded |
| **unicode** | `\p{…}` properties, scripts, simple case folding, and the class ranges — from generated, committed, version-pinned tables |
| **compile** | codepoint ranges to UTF-8 byte automata, alphabet compression, and the NFA program |
| **engine** | the Pike VM (the reference), a lazy DFA, literal prefilters, and a deterministic meta-engine that chooses between them |
| **api** | `Regex`, `Cache`, `Match`, `Captures`, iterators, and template replacement |

Matching is over `uint8[]`, so a haystack may be a network buffer, a mapped
file, or anything else that is bytes — not only a validated `string`.

---

## Layout

```
src/          # THE LIBRARY — Nitpick source only
  core/       #   storage primitives, bitsets, named limits
  syntax/     #   the pattern parser
  hir/        #   desugaring, normalisation, literal extraction
  unicode/    #   GENERATED property and case-folding tables
  compile/    #   HIR -> NFA program, UTF-8 automata, alphabet compression
  engine/     #   Pike VM, lazy DFA, prefilters, the meta-engine
  api/        #   the public surface
tests/        # probe, conformance, unit, oracle, rejection, fixtures
examples/     # runnable demonstrations
harness/      # the Python build and test runner, until `npkg` can build a library
tools/        # generators — the Unicode tables; the fuzzer; the corpus fetcher
meta/specs/   # the design authority
meta/roadmap/ # the plan, in numbered cycles
docs/         # user-facing documentation, written at 1.0
```

## Specification

[`meta/specs/`](meta/specs/) is the authority on behaviour, and
[`meta/DECISIONS.md`](meta/DECISIONS.md) records every settled design decision
with its reasoning — start there when something looks unusual, because it is
recorded why.

## Plan

[`meta/roadmap/ROADMAP.md`](meta/roadmap/ROADMAP.md) is the cycle map. A cycle
is a folder, a subcycle is a file inside it, and a finished cycle moves to
`meta/roadmap/done/`.

## Requirements

The Nitpick compiler and LLVM 20.1.2 — the same toolchain the compiler pins.
The library itself makes no syscall and assumes no operating system; only the
test harness is Linux-specific.

## Licence

Apache 2.0. See [`LICENSE`](LICENSE).

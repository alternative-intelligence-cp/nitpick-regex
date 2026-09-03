# CLAUDE.md

Guidance for Claude Code sessions working in this repository.

## What this is

## Before starting a session here

Check **[`../BOARD.md`](../BOARD.md)** — it says whether this repository
is claimed by a stream, and by which. **One writer per repository, always.**
[`../WORKSTREAMS.md`](../WORKSTREAMS.md) is the dependency graph and the
stream partition: what gates this repository, what this repository gates, and
what to do when a cross-stream gate is not ready yet.

`nregex` — a regular-expression library for **Nitpick**, the safety-critical
systems language at `../../nitpick`. **Status: planning.** No library code
exists yet. The specifications and the plan do.

## Read these first, in this order

1. **`meta/specs/SAFETY.md`** — the constraints, and §2's decision that the
   whole library is arranged around. Most proposals that look reasonable in the
   abstract die on §1 or §2.
2. **`meta/specs/SYNTAX.md`** — what the pattern language accepts and refuses.
3. **`meta/specs/README.md`** — the index and reading order for the rest.
4. **`meta/DECISIONS.md`** — every settled decision with its reasoning. **Read
   before proposing a change**, because it is recorded why.
5. **`meta/roadmap/ROADMAP.md`**, then the current cycle's `README.md`.
6. **`meta/OPEN_QUESTIONS.md`** — what is not settled, each with a
   recommendation.
7. **`../PLAYBOOK.md`** — the shared house rules for every library in this
   ecosystem, if you have the sibling checkouts.

## The rules that are not negotiable

- **Automata only** (RX-003). No backreferences, no lookaround, no atomic
  groups, no recursion. A search is `O(m·n)`, always, on every input. This is
  not a performance preference: catastrophic backtracking is a denial of
  service triggered by untrusted data, and the language has no cancellation
  (D-062) with which to survive one.
- **One public `error:` identity** (RX-060). REACH-002 makes every one a
  mandatory `pick` arm in every consuming program's `failsafe`. A second is a
  **major version**. Detail rides in a `PatternError` value with a closed kind
  enum — thirty ways to be malformed, one identity.
- **Matching cannot fail, cannot trap, and cannot allocate** (RX-061). Every
  way a pattern can be wrong is found at compile time. `regex_find` returns
  `Match?`, not `Result<Match?>`. Anything that would put an error channel on
  the search path is wrong.
- **Every engine gives the same answer** (RX-041), and the suite proves it by
  running every case through every engine and with each optimisation disabled
  in turn. An engine is a performance decision, never a semantic one.
- **The specifications are the authority** (RX-002). Code that disagrees is a
  defect in the code. A specification that is wrong is amended by a decision
  recorded in `meta/DECISIONS.md`, in the same commit — never by a comment.
- **A settled decision's text is never rewritten.** Supersede it with a new
  numbered decision that says why.
- **No dependencies** (RX-007). Not the compiler's `src/`, not its `lib/`, not
  `nitpick-tui` even though both generate Unicode tables from the same UCD.
- **No syscalls** (RX-008). `check_no_syscalls` enforces it. A convenience that
  reads a file or an environment variable costs the library its
  target-independence.
- **Never work around a compiler defect.** Record the reproduction, stop, and
  raise it. A workaround buried in library code outlives the bug.

## The compiler constraints that shape everything

Full statement in `meta/specs/SAFETY.md` §1. The ones that bite hardest:

- **Borrows never pass up the call stack** (D-004), so a `Match` is byte
  offsets and not a slice, and an iterator cannot be returned from a function.
- **A value in an array declares no owning field** (TYPE-046), so instructions,
  HIR nodes and thread entries are all POD.
- **There are no closures** (D-018), so replacement is a template and iteration
  is a struct with `next`.
- **Integer overflow, division by zero and out-of-range indexing all trap**.
- **`comptime` cannot index a string**, so a compile-time-validated pattern is
  not currently expressible — see O-N1, which is the most valuable request on
  the list.
- **There are no static methods** (D-185), so construction is
  `regex_compile(…)`.

## Reserved words that read like ordinary names

`meta/specs/BUILD.md` §7 has the table. The ones this domain wants most:
`range`, `end`, `in`, `limit`, `any`, `buffer`, `raw`, `move`, `error`, `mod`,
`on`, `as`, `with`, `where`, `is`, `is_err`, `never`, `fails`, `pick`, `fall`,
`give`, `pass`, `fail`, `relay`, `drop`, `Rules`, `fixed`, `Self`.

The substitutes this library uses, so the tree stays consistent: **`hi`** for a
range's upper bound and for a `Match`'s end (`Match.end` does not parse — the
fields are `lo` and `hi`), **`src`** for an input cursor, **`bound`** for a
limit, **`rng`** for a range value, **`dot`** for the any-character construct,
**`sel`** for a selection.

Three shapes that surprise a C or Rust habit: adjacent string literals do not
concatenate; `discard(x);` takes parentheses and `defer { … }` takes no
trailing semicolon; declarations end `};` and control-flow blocks do not. And a
file's `mod:` name must equal its basename.

## Building and testing

**`npkg` cannot build this yet** (`meta/specs/BUILD.md` §1, O-N3): it is the
compiler's own bootstrap ladder, and `[dependencies]` resolves to nothing.
`harness/run.py` is the runner until that changes (RX-004). Until cycle 0.0.2
lands it, probes are run by hand — `meta/roadmap/0.0/0.0.0.md` §2 has the
command.

The compiler is at `../../nitpick`. Build it per its own `CLAUDE.md`. LLVM
20.1.2 exactly; `llvm-config --version` to check.

## Where things go

```
src/       the library, Nitpick only, layered per meta/specs/BUILD.md §6
tests/     probe, conformance, unit, oracle, rejection, fixtures
harness/   the Python build and test runner, until npkg can
tools/     generators — the Unicode tables, the corpus fetcher, the fuzzers
examples/  runnable demonstrations, built and run by the harness
docs/      user-facing documentation, written at cycle 1.0
meta/      specs, decisions, open questions, the roadmap, research
.internal/ gitignored scratch — never commit anything from here
```

## When you find something

- A **compiler defect**: record the reproduction, stop, raise it. Do not work
  around it.
- A **specification error**: fix the specification and record the decision, in
  the same commit as the code that revealed it.
- A **finding that is neither**: write it into the current subcycle's execution
  record. This project's execution records are load-bearing; the compiler's
  cross-cycle patterns exist only because one writer kept them.

# Contributing

`nregex` is planned before it is written, and the plan is in the repository.
That is unusual and it is deliberate: the specifications catch design mistakes
that would otherwise be found by writing the wrong code twice.

## Before you write anything

Read, in this order:

1. `meta/specs/SAFETY.md` — the constraints, and the decision the library is
   arranged around
2. `meta/specs/SYNTAX.md` — what the pattern language is
3. `meta/specs/README.md` — the index and reading order
4. `meta/DECISIONS.md` — why things are the way they are
5. `meta/roadmap/ROADMAP.md`, then the current cycle's `README.md`

## The shape of a change

**Every change belongs to a subcycle.** The current cycle's `README.md` has the
checklist; a change that is not on it either goes on it or is a finding to be
recorded first.

**A specification change is a decision.** If your change requires the library
to behave differently from what `meta/specs/` says, the specification is
amended and a numbered decision recorded in `meta/DECISIONS.md`, **in the same
commit**. A settled decision's text is never rewritten — supersede it.

**Every change is green under the full harness.** `--only` is for iterating and
never for concluding; nothing is committed on the strength of a filtered run.

## The seven things that will surprise you

1. **There are no backreferences and no lookaround, and there never will be.**
   They are not missing features. They are what makes catastrophic
   backtracking possible, and the linear-time guarantee is the reason this
   library exists. A patch adding either is a patch that removes the
   guarantee.

2. **Every public `error:` this library declares becomes a mandatory `pick` arm
   in every consuming program's `failsafe`.** The language enforces it and
   forgetting one is a compile error. The budget is **one**. If a failure needs
   a distinction the caller cares about, it rides as a field on the
   `PatternError` value.

3. **Every engine must produce the same answer, and the suite proves it.** A
   change to any engine runs the whole corpus through all of them, and again
   with each optimisation disabled. An optimisation that changes an answer is
   caught by the run that turns it off, and by nothing else.

4. **A `Match` is byte offsets and an iterator cannot be returned.** Both fall
   out of borrows being second-class (D-004). Do not try to hand a caller a
   slice; the caller slices its own haystack. The compiler currently *accepts*
   the slice return (registry O-N9, its DEF-3, scheduled); that acceptance is a
   defect being repaired and is not a licence — see RX-112.

5. **Indexing is NOT bounds-checked on the types this library indexes**
   (RX-111, RX-118). D-070's check attaches to a slice `T[]` and a fixed array
   `T[N]`. A `wild T->` block is a bare pointer, `Vec<T>.items` is one, and a
   `buffer` reached through `.ptr` is another — `buffer_bytes` does not exist,
   so there is no slice route to one. An out-of-range index there **returns an
   unrelated heap word**, silently, which inverts the failure mode the safety
   document advertises. `vec_get`/`vec_set` and `bytes_get`/`bytes_set` are the
   only bounds check there is; a raw `.items[` or `.ptr[` outside its own
   `src/core/` file is a tree-check failure, not a style note.

6. **There is no library object, and `npkc` exiting 0 proves nothing**
   (RX-115). Every file in `src/` compiles at exit 0 and every one is refused by
   `llc`, because a library file cannot define `@npk_failsafe` and `npkc` never
   declares it. `src/` reaches the compiler only by being imported from a
   program root. So **run all four steps** — `npkc`, `llc`, `ld.lld`, then the
   binary — and judge the last one. A change that "compiles" has not been
   tested.

7. **`src/lib.npk` is `pub use`, one name per line, and never plain-`use`s a
   path it re-exports** (RX-113). A plain `use` re-exports nothing, and a plain
   `use` written above a `pub use` of the same path cancels the re-export
   silently — no diagnostic, and the failure appears in a consumer as "cannot
   find X in this scope". If you add a name to the public surface, add one
   line, and add it to `API.md` §1 in the same commit.

## Tests

- **Expectations live in the test file**, as markers, and assert on codes and
  exit codes — never on message text.
- **A negative test with no expectation is a failing test.**
- **Unexpected diagnostics fail a test as surely as missing ones.**
- **The linear-time property test is in every gate from cycle 0.7 onward.** It
  is the one that would be quietly dropped when it goes red under a refactor,
  and it is the only evidence for the library's central claim.
- **Anything with a timing dimension runs forty times**, not once.
- **A red under stress is a stop sign, never a retry.**
- **Anything a fuzzer finds becomes a permanent fixture**, minimised, with the
  defect named.
- **"The programs exit 0, so a leak is a trap" is true of `wild` blocks and of
  nothing else** (RX-110). D-151 counts `wild` blocks, D-188 counts live
  drivers, and neither sees a managed body — a container freed without dropping
  its owning elements exits 0. Where the obligation is managed, the gate is a
  memory cap, not an exit code.
- **A timing without an exit code is not a measurement.** A file that fails to
  compile stops early and looks fast, so a broken configuration is the fastest
  row in the table — which is the row a curve is most sensitive to.

## Compiler defects

You will find them; the library is written against a compiler that is itself
under construction. **Record the reproduction, stop, and raise it in the
compiler repository.** Do not work around it in library code: a workaround
buried here outlives the bug, is never removed, and is indefensible at
verification time.

## Style

Match the surrounding code. Public names carry their module's short prefix;
types are PascalCase; constants are `SCREAMING_SNAKE`. `meta/specs/BUILD.md`
§7 lists the reserved words that read like ordinary names and the substitutes
this library uses instead — use those, so the tree is consistent.

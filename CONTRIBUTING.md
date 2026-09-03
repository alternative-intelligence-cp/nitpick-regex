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

## The four things that will surprise you

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
   slice; the caller slices its own haystack.

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

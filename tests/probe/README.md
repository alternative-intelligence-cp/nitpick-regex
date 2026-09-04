# `tests/probe/` — the language probes

**What lives here.** Small, complete Nitpick programs that ask the compiler
whether a shape `meta/specs/` depends on is spellable, compilable and correct.
They are not tests of `nregex` — no probe imports anything from `src/`, and
none will ever be able to (P-1). They are tests of the **language**, kept in
this library's tree because this library's design rests on their answers.

Written by cycle 0.0.0 (`meta/roadmap/0.0/0.0.0.md`), which has the verdict
table and the reasoning.

## A probe is never deleted

**P-5.** They are a permanent regression suite for the language shapes this
library depends on. A compiler change that breaks one of these is caught here,
by a file whose header says which specification rule cared, rather than in
cycle 0.8 by an engine that starts failing mysteriously.

Cycle 0.0.2 picks them up as the harness's first `program`-stage entries.

## How to run one

Four steps, all of them, every time (`0.0.0.md` §2):

```
$NPKC tests/probe/probeNN_topic.npk -o /tmp/p.ll \
  && llc -O0 -filetype=obj -relocation-model=static /tmp/p.ll -o /tmp/p.o \
  && ld.lld -static /tmp/p.o $NPKRT -o /tmp/p \
  && /tmp/p ; echo "exit $?"
```

**`npkc` exiting 0 does not mean a program is well-formed.** A root file with
`main` and no `failsafe` compiles at exit 0 and is refused only by `llc`, a long
way from the cause — the workbench registry's O-N11, the compiler's DEF-5. *A
probe that was only compiled is a probe that has not been run.*

`$NPKC` and `$NPKRT` are the pinned toolchain the board names (`../../../BOARD.md`,
W-18). LLVM must be exactly 20.1.2.

## The conventions

| Marker | Means |
|---|---|
| `// expect-exit: 0` | compiles, links, runs, exits 0 |
| `// expect-exit: 94` | runs and traps — 94 is `failsafe`'s `OutOfBounds` arm |
| `// expect-error: NITPICK-…` | **refused**, and that code is the whole set reported (D-237) |

- **Exit 0 on success; a distinct positive code per assertion.** A failure names
  itself, so `exit 33` sends a reader to one line.
- **Assert on codes, never on message text.**
- **The `expect-` header is a HYPOTHESIS, not a verdict.** It records what the
  probe was written to ask. `0.0.0.md` §7 records what happened, and they
  disagree on exactly the probes that found something — which are the ones a
  later reader is most likely to be looking at. `probe06b` is the example: it
  was planned as "expected refused" and is accepted.
- **A refusal probe's header quotes the diagnostic verbatim**, with the span,
  because the diagnostic *is* the result.

## What `exit 0` does and does not assert

**D-151 counts `wild` blocks, D-188 counts live drivers, and neither sees a
managed body** (`meta/specs/SAFETY.md` §8b, RX-110). So exiting 0 proves a
probe's `wild` allocations were paired on that path, and proves nothing about a
`string` body or a container's owning elements. Where a probe's obligation is
managed, the gate is a memory cap; the real instrument is the compiler's
`NPK_HEAP_STATS`, which does not exist yet.

## Naming

`probeNN_topic.npk`, and the `mod:` line equals the basename. Sub-probes that
isolate one half of a question take a letter — `probe08b`, `probe08c`.

**No source file may be named beginning with a digit**: D-147 gives that opening
to numeric literals, so `01_thing.npk` is `NITPICK-LEX-003` with
`NITPICK-RESOLVE-005` behind it. This repository wrote `01_name.npk` before
anybody compiled one, and fixed it at commit `d6fb0ce`.

**And no file may be named after a reserved word**, because D-248 makes
`mod:<basename>;` mandatory and a module name is an identifier. `PLAYBOOK.md`
§10 has the list. Note that it is not complete: **`stack` is reserved** — a
MemoryQualifier beside `wild`, `wildx` and `defer` — which probe 05 found the
expensive way, and which no list in this ecosystem carried.

## The transcript

[`TRANSCRIPT.txt`](TRANSCRIPT.txt) is every command that produced a verdict,
with its exit code, committed verbatim. It is regenerated rather than edited. A
prose summary of a run is not evidence of it.

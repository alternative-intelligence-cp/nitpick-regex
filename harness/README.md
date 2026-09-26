# `harness/` — the build and test runner

Python, because `npkg` cannot build a library yet
(`../meta/specs/BUILD.md` §1, O-G3) and zero-dependency governs the artifact,
not the workbench. It retires into `npkg` the way `bootstrap/harness/` does in
the compiler repository, with both running side by side and a parity check
first. Built in cycles 0.0.2 and 0.0.3.

```
NPKC=… NPKRT=… python3 harness/run.py
```

`$NPKC` and `$NPKRT` are the pinned toolchain the board names (`../../BOARD.md`,
W-18). LLVM must be exactly 20.1.2, and the runner **asserts** that rather than
reporting it.

## The modules

| File | What |
|---|---|
| `run.py` | the driver: build steps, then the suites in manifest order, then the summary |
| `manifest.py` | `nitpick.toml`, in the compiler's own subset, with the compiler's schema |
| `toolchain.py` | `llc`, `opt`, `ld.lld` asked their versions and held to the pinned LLVM 20.1.2 |
| `lexical.py` | **the harness's one reading of `.npk` source** (RX-157, RX-165): every `.npk` file opened by `lexical.read`, as BYTES — `\n` the only line end, as in the compiler's lexer — comments, strings, character literals and template text blanked, imports read the way the compiler's parser reads them, each path the literal's decoded value. The program suites' skip, B-2's reach, the expectation markers and every tree check stand on it; self-check case 18 tests it through a file |
| `expect.py` | the `// expect-…` grammar, marker for marker with `npkg/expect.npk`, **plus two markers of this runner's own** — `mem-cap-mib:` and `pending-until: <commit> exit <N>` (`BUILD.md` B-5b, RX-146 as amended by RX-154), each declared there so the parity stage has a row rather than a surprise |
| `elf.py` | an ELF64 symbol table, read with `struct` — no fourth tool |
| `irscan.py` | the emitted IR's call edges to the floor |
| `build.py` | the pipeline, and `npkc`'s exit alphabet |
| `stages.py` | `program`, `compile`/`positive`, `compile`/`negative`, `parse`, `check` |
| `treecheck.py` | the live tree checks — the library diffed against its own documents; every one but `check_specs_current` can fail the run, and the runner prints each with what it examined |
| `selfcheck.py` | **the harness fed wrong expectations and required to fail**; runs FIRST |
| `baseline/` | the empty program the two scans are differences against, `rx120.sh`, and the two REVIEWED LISTS — `RESIDUE.txt` (what `nregex` needs from the runtime, RX-131) and `PENDING.txt` (every unit a `pending-until:` marker takes out of the denominator, RX-154), each checked both ways |
| `baseline/rx120.sh` | **executable**: builds the floor and a syscaller at the pinned compiler and ASSERTS floor == 5, syscaller == 6, difference == `{npk_sys6}` (at `c3bdae2`; 2 and 3 at `3d15ac9`); with `950bb1d` present it also asserts 29/29/identical, compiling the two programs without the two arms that compiler does not have (RX-148). A harness **build step** and its own CI step. It replaced a hand-copied transcript that recorded a command which could not have produced the output beside it (RX-142's neighbourhood; cycle 0.0 audit, adjudication (a)) |
| `selfcheck/` | fixtures that must **fail**; `selfcheck.py` drives them |

## What a green run asserts

- every **program** — each `program`-stage and `compile`/`positive` file — built
  by the **pinned** `npkc`, assembled by `llc`, scanned, linked closed-world
  against `npkrt.o`, and **run**; every other file — the `parse` sweep, the
  refusals, the rejection fixtures — compiled by the same `npkc` and judged by
  its exit and codes, **neither linked nor run** *(this bullet said "every
  declared suite's every file … run" until the fourth cycle 0.0 audit, N-23)*;
- every `program`-stage file gave the **same exit code** at −O0 and again
  through `opt -O2` + `llc -O2` (B-3);
- every rejection fixture was refused with **exactly** the codes it names
  (B-7, D-237);
- no object gained an undefined symbol the baseline lacks, and no function
  outside the baseline called a floor symbol this library may not (B-2, B-2a);
- the same tree built from two different working directories produced
  byte-identical IR (B-4);
- **every `.npk` in the tree was swept as a root** by the `parse` stage, which
  is what re-checks the six `src/` files `src/lib.npk` does not reach;
- the live **tree checks** (`treecheck.ALL`; the runner prints each one and what it examined) agreed with the specifications they diff against;
- every unit a `pending-until:` marker took out of the denominator is a line in
  `baseline/PENDING.txt`, gave exactly the exit its marker names on every leg
  and every run, and did not meet its expectation (RX-154, RX-159); and every
  file of a program suite that **the compiler** says defines `main` was judged,
  whatever a sibling's text seems to import (RX-157, RX-165), and the run names
  every file it judged through an importer instead. That closes the two routes
  two audits measured — a marker line, and a `use` a sibling's text only seems
  to hold (BL-7's `/* */`, BL-9's lone CR) — and nothing wider is claimed: the
  skip has two defences that share no reader, each tested alone (self-check
  cases 19 and 23) *(the bullet stopped at the marker until the fourth audit's
  BL-7; it then said "neither a marker line nor a comment in another file can
  move a red out of a green run", and the fifth audit's BL-9 moved one out with
  two carriage returns, because both defences read through one reader)*;
- and — the one that makes the rest mean anything — **the runner was shown able
  to fail before any of it ran** (V-21).

## The self-check, which is the load-bearing half

`selfcheck.py` builds a throwaway tree per case, runs the **real** runner over
it with the **real** pinned `npkc`, and requires a **failure**. Some cases are
**PENDING** on stages that do not exist yet and print as pending rather than as
passing, because `20 live, 4 pending` and `24 passing` are different claims and
only one is true — and the counts here are the day they were written
(2026-09-25, the fifth cycle 0.0 audit's triage, which added cases 19–23 to the
fourth's 15–18): the runner prints them from `selfcheck.CASES` on every run, and
that line is the authority.

A case requires more than a non-zero exit: it requires the runner to **say the
thing**, naming the case's own file. A non-zero exit alone would also be
produced by the runner crashing for an unrelated reason — a passing case whose
red is unreachable, which is the exact failure this file exists to prevent.

**It was mutation-tested at 0.0.3**, and that is the evidence it works: deleting
B-7's equality half reddens cases 3 and 3a and nothing else; disabling the IR
call-edge scan reddens case 8 and **not** case 9, which is RX-120's own finding
reproduced from the other side; comparing exit codes by truthiness instead of by
value reddens case 1. `../meta/roadmap/0.0/0.0.3.md` §4 has the transcripts.
**And at every triage since**: the fifth (`0.0.5.md` §12) reverted each of its
fixes in a copy and read which cases went red — the reader back in text mode
reddens 18 and 20; the escape decoding removed, 18 and 21; `395308f`'s
block-string close, 18; the skip's second defence deleted, or asked of the reader
again, 23 alone; both defences removed, 18, 19, 20 and 23 — 19 is the case that
needs both gone; `range(exp.stress)` narrowed to one run, 22; the first leg only,
11 and 22; and all three of BL-9's fixes reverted together, 18, 19, 20, 21 and 23.

## What it does not assert yet

The four pending self-check cases: a generated table off by one line (0.3), a
corpus fixture off by one (0.5), an engine and the naive oracle disagreeing
(0.5), and **a corpus fixture that passes under one engine and fails under
another** (0.8) — the last is the most important case in `TESTING.md` V-20's
list, because it is what proves RX-041 is being *checked* rather than assumed. `corpus` and `oracle` are not stages yet. `accept` is not
pending but **struck** (B-4a), and declaring it is a manifest error.

## Three things that will trip a reader

- **`npkc`'s exit codes are an alphabet**: `0` success, `1` refused, `2` the
  driver could not proceed and judged **nothing**, `3` a trap. Every stage
  asserts the specific integer. A `2` means the run is broken, and it arrives
  with an **empty stderr** — see `../tests/conformance/TRANSCRIPT.txt` §F, §G.
- **There is no library object** (B-0, RX-115 as corrected by RX-151).
  `npkc src/lib.npk` exiting 0 is a parse-and-resolve check and nothing more;
  the library reaches the compiler only through a program root. *The reason
  changed and the rule did not:* at `950bb1d` every `src/` file was refused by
  `llc`; since `94874ce` every one assembles, and at `c3bdae2` a module's object
  still links neither alone (no `npk_failsafe`, no `main`) nor beside a program,
  which already carries everything it reaches (`ld.lld: duplicate symbol`). The
  runner prints that on every run rather than letting a green `libcheck` line
  imply otherwise.
- **`--only` iterates; it never concludes.** The runner says so twice.

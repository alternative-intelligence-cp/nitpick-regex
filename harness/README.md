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
| `expect.py` | the `// expect-…` grammar, marker for marker with `npkg/expect.npk` |
| `elf.py` | an ELF64 symbol table, read with `struct` — no fourth tool |
| `irscan.py` | the emitted IR's call edges to the floor |
| `build.py` | the pipeline, and `npkc`'s exit alphabet |
| `stages.py` | `program`, `compile`/`positive`, `compile`/`negative`, `parse`, `check` |
| `treecheck.py` | the **seven** live tree checks — the library diffed against its own documents; six can fail the run and `check_specs_current` reports |
| `selfcheck.py` | **the harness fed wrong expectations and required to fail**; runs FIRST |
| `baseline/` | the empty program the two scans are differences against, and `rx120.sh` |
| `baseline/rx120.sh` | **executable**: builds the floor and a syscaller at the pinned compiler and ASSERTS floor == 2, syscaller == 3, difference == `{npk_sys6}`; with `950bb1d` present it also asserts 29/29/identical. A harness **build step** and its own CI step. It replaced a hand-copied transcript that recorded a command which could not have produced the output beside it (RX-142's neighbourhood; cycle 0.0 audit, adjudication (a)) |
| `selfcheck/` | fixtures that must **fail**; `selfcheck.py` drives them |

## What a green run asserts

- every declared suite's every file built by the **pinned** `npkc`, assembled by
  `llc`, scanned, linked closed-world against `npkrt.o`, and **run**;
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
- the four live **tree checks** agreed with the specifications they diff against;
- and — the one that makes the rest mean anything — **the runner was shown able
  to fail before any of it ran** (V-21).

## The self-check, which is the load-bearing half

`selfcheck.py` builds a throwaway tree per case, runs the **real** runner over
it with the **real** pinned `npkc`, and requires a **failure**. Eight cases are
live; three are **PENDING** on stages that do not exist yet and print as pending
rather than as passing, because `8 live, 3 pending` and `11 passing` are
different claims and only one is true.

A case requires more than a non-zero exit: it requires the runner to **say the
thing**, naming the case's own file. A non-zero exit alone would also be
produced by the runner crashing for an unrelated reason — a passing case whose
red is unreachable, which is the exact failure this file exists to prevent.

**It was mutation-tested at 0.0.3**, and that is the evidence it works: deleting
B-7's equality half reddens cases 3 and 3a and nothing else; disabling the IR
call-edge scan reddens case 8 and **not** case 9, which is RX-120's own finding
reproduced from the other side; comparing exit codes by truthiness instead of by
value reddens case 1. `../meta/roadmap/0.0/0.0.3.md` §4 has the transcripts.

## What it does not assert yet

The three pending self-check cases: a generated table off by one line (0.3), a
corpus fixture off by one (0.5), and **a corpus fixture that passes under one
engine and fails under another** (0.8) — the last is the most important case in
`TESTING.md` V-20's list, because it is what proves RX-041 is being *checked*
rather than assumed. `corpus` and `oracle` are not stages yet. `accept` is not
pending but **struck** (B-4a), and declaring it is a manifest error.

## Three things that will trip a reader

- **`npkc`'s exit codes are an alphabet**: `0` success, `1` refused, `2` the
  driver could not proceed and judged **nothing**, `3` a trap. Every stage
  asserts the specific integer. A `2` means the run is broken, and it arrives
  with an **empty stderr** — see `../tests/conformance/TRANSCRIPT.txt` §F, §G.
- **There is no library object** (B-0, RX-115). `npkc src/lib.npk` exiting 0 is
  a parse-and-resolve check and nothing more; the library reaches the compiler
  only through a program root. The runner prints that on every run rather than
  letting a green `libcheck` line imply otherwise.
- **`--only` iterates; it never concludes.** The runner says so twice.

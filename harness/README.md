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
| `toolchain.py` | `llc`, `opt`, `ld.lld` asked their versions and held to the pin |
| `expect.py` | the `// expect-…` grammar, marker for marker with `npkg/expect.npk` |
| `elf.py` | an ELF64 symbol table, read with `struct` — no fourth tool |
| `irscan.py` | the emitted IR's call edges to the floor |
| `build.py` | the pipeline, and `npkc`'s exit alphabet |
| `stages.py` | `program`, `compile`/`positive`, `compile`/`negative` |
| `baseline/` | the empty program the two scans are differences against |
| `selfcheck/` | fixtures that must **fail**; cycle 0.0.3 drives them |

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
  byte-identical IR (B-4).

## What it does not assert yet

`parse`, `accept` and `check` as stages, the tree checks, and — the one that
matters — **the self-check that proves this runner can fail**. All of that is
cycle 0.0.3. Until it exists, `TESTING.md` V-21 applies: a harness that has not
proven it can fail has not proven anything. Three of the eventual cases were
run **by hand** at 0.0.2 and their transcripts are in
`../meta/roadmap/0.0/0.0.2.md` §6; two of them left committed fixtures in
`selfcheck/`.

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

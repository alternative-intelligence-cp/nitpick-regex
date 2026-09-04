# Cycle 0.0 — Foundations

**The probes, the harness, and `src/core/`.** Nothing in this cycle matches
anything. What it produces is the ability to find out whether the rest of the
plan is buildable, and the machinery every later cycle is tested by.

## Why this shape

Two of the compiler project's most expensive lessons decide this cycle's
contents:

- **"A construct that parses is not a construct that works."** Its cycle 0.4
  was mostly repair, and every repair dated to the cycle that had parsed the
  construct. `nregex` leans on several language shapes that have never been
  exercised in this combination — a POD instruction array in the tens of
  thousands, a payload enum destructured in a hot loop, an explicit-stack
  parser, a `SparseSet` over two `Vec`s, a `Match` that is offsets because a
  slice cannot be returned. **0.0.0 asks the compiler about all of them before
  anything is built on them.**
- **"Diagnostics come first, not last — they are how every later cycle is
  tested."** Here that is the harness. A suite written after the code is a
  suite shaped by the code.

One probe (09) is **expected to fail**, and its failure is the evidence for
O-G1 — the request that would make a compile-time-validated pattern literal
possible. A probe that fails is a result, not an obstacle.

## Decisions in

RX-001, RX-002, RX-004, RX-005, RX-006, RX-007, RX-008, RX-050, RX-062. All
settled. **Nothing in this cycle is blocked on a question.**

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| [0.0.0](0.0.0.md) | **The language probes** — fourteen programs asking whether the design is spellable | a recorded verdict per probe, and any design change the answers force |
| [0.0.1](0.0.1.md) | **The skeleton** — the module layout, `src/lib.npk`, the manifest's first test entries, CI | `npkc` compiles an empty library and a program that imports it |
| [0.0.2](0.0.2.md) | **The harness, part 1** — build, the `program` stage, the toolchain pin, the no-syscall scan | one test program builds, links, runs, and its exit code is judged |
| [0.0.3](0.0.3.md) | **The harness, part 2** — `parse`, `accept`, `check`; the self-check; the tree checks | the self-check proves the harness can fail, seven ways |
| [0.0.4](0.0.4.md) | **`src/core/`** — `Vec<T>`, `Bytes`, `ByteSet`, `SparseSet`, `limits.npk` | four primitives with their own suites and their obligations written |
| [0.0.5](0.0.5.md) | **Close** — the findings, the spec amendments the probes forced, the handoff to 0.1 | `done/0.0/`, and 0.1 openable by a fresh session |

## Checklist

### 0.0.0 — the probes
- [x] `tests/probe/probe01_pod_inst_array.npk` — a `Vec<Inst>` of 100 000 12-byte POD values: fill, read, copy, clear; `#size_of<Inst>()` asserted  
      **DONE** — `#size_of<Inst>` = 12, confirmed.
- [x] `tests/probe/probe02_payload_enum.npk` + `probe02b_derive_eq_refused.npk` + `probe02c_derive_ord_tag_only.npk` — a tagged enum with payloads, destructured in a `pick`, stored in a `Vec`, `#[derive(Eq, Debug)]`, `#size_of` asserted  
      **DONE** — but `#[derive(Eq)]` on a payload enum is **refused** (workbench O-N10), so the comparison is hand-written and 02b/02c record both halves.
- [x] `tests/probe/probe03_generic_move.npk` — `move T:v` into a generic container, `T` both scalar and owning  
      **DONE** — and the element obligation is the caller's; the specification's offset-into-`Bytes` design avoids it.
- [x] `tests/probe/probe04_inherent_generic_impl.npk` — `impl:<T>:Vec<T> = { … }` with a `Vec<T>->:self` receiver that mutates, called as `v.push(x)`  
      **DONE** — *both* forms work, so 0.0.4's API is a choice made with evidence.
- [x] `tests/probe/probe05_explicit_stack.npk` — a nested-structure parser over an explicit `Vec<Frame>`, 250 deep, **no native recursion**, and a 10 000-deep input refused rather than crashing  
      **DONE** — 10 000 deep refused at depth 251, program survives.
- [x] `tests/probe/probe06a_offsets_returned.npk` + `probe06b_subview_returned.npk` — a function returning `{lo, hi}` offsets; and one **returning a `uint8[]`**, expected to be **refused**, with the code recorded  
      **DONE, hypothesis REFUTED** — the slice return is **accepted** (workbench O-N9). RX-112 records why `API.md` §2 is *not* re-planned.
- [x] `tests/probe/probe07_string_bytes_edges.npk` — `string_bytes` into a scanner, `.len`/`.ptr`, and the four borrow edges: passed down (legal), returned (refused), stored past the call (refused), held across an `await` (refused)  
      **DONE** — edges 2–3 are O-N9 and are cited, not re-run. Edge 4 is accepted *and so is the `@`-borrow control*, so it is not reported as a sibling defect.
- [x] `tests/probe/probe08_sparse_set.npk` + `probe08b_wild_index_unchecked.npk` + `probe08c_slice_index_traps.npk` — two `Vec<int32>` as a sparse set: O(1) insert, membership and clear, over 100 000 keys, with the dense/sparse invariant asserted  
      **DONE, and it found RX-111** — a `wild T->` index is **not** bounds-checked; `SAFETY.md` §5.3 (S-23) added and §1's row corrected.
- [x] `tests/probe/probe09_comptime_walker.npk` — a `comptime func:` that indexes a pattern string; **expected to be REFUSED**. Record the exact diagnostic: it is O-G1's evidence  
      **DONE** — `NITPICK-TYPE-004`; the wall is `string_bytes`, not the index. O-G1's ask sharpened to two arms.
- [x] `tests/probe/probe10_comptime_capabilities.npk` — what `comptime` *can* do: `string_concat`, `string_equals`, `string_byte_length`, `string_is_empty`, a `loop`, a mutable local, a `comptime func:` call. Records the boundary from the other side  
      **DONE** — all four foldable builtins confirmed; a pattern-length check is buildable today.
- [x] `tests/probe/probe11_byteset_bitset.npk` — a `uint64[4]` field inside a struct inside a `Vec`, with union/intersect/complement/contains  
      **DONE** — `#size_of<ByteSet>` = 32.
- [x] `tests/probe/probe12_iterator_borrowing.npk` + `probe12b_for_over_borrow_refused.npk` — the prelude `Iterator` trait implemented on a struct holding a borrow, driven by `for … in`; O-A1 depends on the answer  
      **DONE, and it splits O-A1** — the impl is legal, `for … in` over it is `NITPICK-BORROW-009`.
- [x] `tests/probe/probe13a_prove_refused.npk` … `probe13d_ensures_refused.npk` — `prove`, `limit<Rules>`, `requires`/`ensures` each **refused by name** with `NITPICK-RUNG-001` naming "1.5", so the comment-form obligations are known to be inert rather than silently parsed as something else  
      **DONE** — all four refuse `NITPICK-RUNG-001` naming 1.5; and `never fails` + `limit` is a *permanent* refusal, `NITPICK-TYPE-037`.
- [x] `tests/probe/probe14_size_bound.npk` — a `Vec<Inst>` at `NREGEX_PROGRAM_INSTRUCTIONS`, built and walked, exiting 0 so a leak is a trap  
      **DONE** — 1 200 000 B, peak RSS 1152 KiB, wall < 10 ms.
- [x] a verdict line per probe recorded in `0.0.0.md` §7, with the exact diagnostic where refused — **23 rows**, and every probe's outcome equals its `expect-` header (checked mechanically against `tests/probe/TRANSCRIPT.txt`)
- [x] every design consequence written into `meta/specs/` **and** `meta/DECISIONS.md` before 0.0.1 starts — RX-110, RX-111, RX-112; `SAFETY.md` §1, §5.3 (S-23) and §8b (S-22)

### 0.0.1 — the skeleton
- [x] ~~`src/lib.npk` exists and `pub use`s nothing yet~~ — **STRUCK, and it `pub use`s exactly one name.**
      `ERegexPattern` *is* the public surface today: it is the whole cost of importing this library
      (RX-060), and re-exporting it is what makes the consumer's `(ERegexPattern)` arm resolve, which
      is the property `0.0.1.md` §3 step 2 wanted proved. "Nothing yet" would have made the umbrella
      untestable and left `pub use` unmeasured — and it needed measuring: **RX-113** found that a
      plain `use` re-exports nothing and that a plain `use` above a `pub use` of the same path
      cancels the re-export silently.
- [x] every `src/` subdirectory has a placeholder module that parses, so the `parse` stage has something to sweep  
      **DONE** — seven, one per layer, each naming the specification that fills it, the cycle that
      does, and what `BUILD.md` §6 permits it to import. All seven compile at `npkc` exit 0
      (`tests/conformance/TRANSCRIPT.txt` §A) — and all seven are refused by `llc`, which is **RX-115**.
- [~] `nitpick.toml`'s `[[test]]` table has its first entries: `probe` and `conformance`  
      **HALF DONE, deliberately.** `conformance` is declared at `compile`/`positive` and is live.
      `probe` is **not** declared: 16 of the 23 probes carry `expect-exit:` and 7 carry
      `expect-error:`, and no single entry can judge both — `run_program` does not skip a file with
      `expect-error`, and `run_compile`'s `kind` selects the checker, not the file set
      (`npkg/suites.npk` :779 and :608). **RX-119**; the three-entry shape is in the manifest ready
      to uncomment and the split is 0.0.2's, above.
- [x] a consumer program under `tests/conformance/` imports `src/lib.npk` by relative path and compiles, with a comment naming O-G3 as the reason the path is relative  
      **DONE, and it links and runs** — `npkc` 0, `llc` 0, `ld.lld` 0, binary 0, and the same four
      through `opt -O2` (rule B-3). Six controls beside it, each failing for the right reason.
- [x] CI: a workflow running `harness/run.py` on push, with LLVM 20.1.2 and the compiler built from a **pinned commit**, not a branch  
      **WRITTEN, NOT RUN.** Pins the compiler by full sha (verified present on the public remote) and
      LLVM by exact patch release, and *asserts* both. It has not executed: that needs a push, and
      building the compiler from here is refused by W-18. See 0.0.1's acceptance for what is and is
      not evidence.
- [x] `CLAUDE.md` and `CONTRIBUTING.md` re-read against 0.0.0's verdicts and extended  
      **DONE, and the re-read earned its place**: `CLAUDE.md` still said out-of-range indexing traps,
      which probe 08b refuted at 0.0.0 (RX-111), and its "What this is" section was empty.

### 0.0.2 — the harness, part 1
- [ ] `harness/run.py`: the manifest reader, the toolchain pin check, the module-graph walk
- [ ] the build pipeline — `npkc` → `opt` (check leg) → `llc` → the undefined-symbol scan → `ld.lld`
- [ ] the undefined-symbol scan against the runtime allowlist, as a **build step** and not a test (B-2)
- [ ] **`check_no_syscalls`**: the object's undefined symbols held to a committed expected list — the allocator, `memcpy`/`memset`, the string primitives. A syscall in a `nregex` object is a red run (RX-008)
- [ ] the `program` stage, at -O0 and again under `opt -O2`, same exit required (B-3)
- [ ] `// expect-exit:` and `// stress: N` honoured
- [ ] the `repro` check: two builds from different working directories, byte-identical IR
- [ ] one real program green — probe 01, run as a `program`-stage entry
- [ ] **split `tests/probe/` by kind and declare both entries** (RX-119). 16 of
      the 23 probes carry `expect-exit:` and 7 carry `expect-error:`, and no
      single `[[test]]` entry can judge both — `run_program` does not skip a
      file with `expect-error` and `run_compile`'s `kind` selects the checker,
      not the file set. `nitpick.toml` carries the three-entry shape ready to
      uncomment. Moving the seven into `tests/probe/refused/` also moves paths
      that cycle 0.0.0's verified record cites, so record the move there

### 0.0.3 — the harness, part 2
- [ ] the `parse` stage over every `.npk` in the tree, each file once
- [ ] the `accept` and `check` stages, with the **exact-code** rule (B-7)
- [ ] `--only`, and output that says twice that a filtered run concludes nothing
- [ ] `harness/selfcheck.py` with all seven cases from `specs/TESTING.md` V-20, two of them pending until the corpus stage exists at 0.5
- [ ] the self-check runs **first** in every full invocation
- [ ] `check_layering` — every `use` edge against `specs/BUILD.md` §6, **including the oracle's restriction** (B-17), which will have nothing to check yet and is the right answer
- [ ] `check_constants_named` and `check_error_budget` live
- [ ] `check_specs_current` reporting, not failing

### 0.0.4 — `src/core/`
- [ ] `src/core/limits.npk` — all nine bounds from `specs/SAFETY.md` §5, each with the specification rule that set it
- [ ] `src/core/vec.npk` — `Vec<T>`: `init`, `reserve`, `push`, `pop`, `at`, `set`, `truncate`, `clear`, `insert`, `remove`, `swap_remove`, `fill`, `free`; both `T` shapes exercised
- [ ] `src/core/bytes.npk` — `Bytes`: `init`, `push`, `extend`, `extend_str`, `put_uint`, `len`, `view`, `take`, `clear`; `put_uint` allocation-free and correct at 0, 1, 9, 10, 99, 100 and `uint64` maximum
- [ ] `Bytes` growth amortised linear, proven by appending a million bytes and bounding the reallocation count — the compiler's own quadratic-capture defect is why this test exists
- [ ] `src/core/byteset.npk` — `ByteSet` as `uint64[4]`: union, intersect, complement, contains, iterate; exhaustive over all 256 bytes
- [ ] `src/core/sparseset.npk` — `SparseSet`: O(1) insert, membership, clear; **the invariant `dense[sparse[k]] == k` asserted after every operation** in a property test. This is the structure the linear-time guarantee rests on and it is the easiest to get subtly wrong
- [ ] every accessor's bounds obligation written as a comment in the `requires`/`ensures` syntax it will take, with a property test standing in
- [ ] the leak tests exit 0, so a missing `vec_free` is a trap and not a pass

### 0.0.5 — close
- [ ] every probe verdict reconciled against the specifications
- [ ] the cycle's findings written as a numbered list
- [ ] the harness self-check green, the full run green
- [ ] `0.1/0.1.0.md` written execution-grade
- [ ] cycle archived to `done/0.0/`, `ROADMAP.md` updated

## Gate

A full `harness/run.py` green; the self-check proving the harness fails seven
ways; `check_no_syscalls` green over a real object; `src/core/`'s four
primitives each with a suite; and every probe with a recorded verdict whose
consequences are written into the specifications.

## Watch for

- **A probe that fails is a finding, not an obstacle.** Record the exact
  diagnostic, decide the design change, amend the specification, and only then
  continue. Working around a compiler refusal in library code is what the
  compiler's own R6 forbids, for exactly the reason it applies here: a
  workaround buried in library code outlives the reason for it.
- **Probe 09 is expected to fail.** Do not treat it as a blocker or try to make
  it pass. Its output is a request, not a defect.
- **The reserved words in `specs/BUILD.md` §7 bite hardest in `src/core/`**:
  `buffer`, `raw`, `move`, `end`, `in`, `limit`, `any` and `range` are all
  words a container library reaches for, and `range` in particular is what a
  `ByteSet` iterator wants to be called.
- **`Vec<T>` is `wild` storage** and every path out of a function that took
  some must release it, or `exit 0` traps under D-151. The suite's programs exit
  0 on purpose, so **a leaked `wild` block** on any path turns a pass into a
  trap. **It is only `wild` blocks that this catches**: D-151 counts them, D-188
  counts live drivers, and neither sees a managed body, so a container freed
  without dropping its owning elements exits 0 (RX-110). Where the obligation is
  managed, the gate is a memory cap.

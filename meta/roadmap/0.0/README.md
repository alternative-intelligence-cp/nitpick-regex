# Cycle 0.0 — Foundations — **NOT CLOSED. The close was refused TWICE on 2026-09-06.**

> ## The SECOND refusal, and it found a defect in the fix for the first
>
> **[`../../audits/nitpick-regex-0.0-2026-09-06-second.md`](../../audits/nitpick-regex-0.0-2026-09-06-second.md)**
> returned **DO-NOT-ACCEPT** on two blocking findings. One, `BL-4`, was
> **introduced by the first triage's own fix commit**. The other, `BL-3`, is the
> largest defect this cycle has found and it sits one level below the template the
> first audit was given: **not a missing guard, but the guard's stop failing to
> stop.** `vec_oob` was spelled as an index into a one-element array, so
> `vec_oob(0)` **returned** — and 0 is exactly the index that nine `i >= count`
> guards pass when the container is empty. Every call site is `drop vec_oob(…)`
> and `drop` continues, so those nine performed the read or write they had just
> refused: a heap word returned from an empty `Vec`, a write completed through a
> dangling pointer, `count` left at −1, a phantom sparse-set member.
>
> **All twelve out-of-range units in the shipped suite passed a NON-ZERO
> argument**, so 108 green was green over it and a thirteenth case of the same
> shape would have been too. The triage is [`0.0.5.md`](0.0.5.md) §9 — **6 items,
> 6 lines, all fixed** — and it adds seventeen units, of which the three that
> matter test the **stop itself** rather than any entry point.
>
> **The cycle is still not archived and `meta/roadmap/done/` is still empty.** The
> gate below requires an audit that has seen the tree it is accepting, and the
> only audit that has seen this one refused an earlier version of it.


> ## The archive was made and then REVERSED, and this note replaces the redirect
>
> **On 2026-09-06 this cycle was marked DONE and moved to
> `meta/roadmap/done/0.0/`. Both were wrong, and the W-22 audit said so the
> same day.** The close was reported `READY-TO-CLOSE`, passed by an independent
> verifier on eight checks, and refused by the audit on **two blocking findings
> in `src/core/`** — the cycle's headline deliverable. The audit is
> [`../../audits/nitpick-regex-0.0-2026-09-06.md`](../../audits/nitpick-regex-0.0-2026-09-06.md)
> and the triage is [`0.0.5.md`](0.0.5.md) §8.
>
> **The folder is back at `meta/roadmap/0.0/`, so every citation of the form
> `meta/roadmap/0.0/X` — including the 33 the redirect note existed to
> serve — is correct again, and needs no redirect.** The handful of live
> pointers that had been rewritten to `done/` were rewritten back: `CLAUDE.md`,
> `harness/README.md`, `nitpick.toml`, `meta/OPEN_QUESTIONS.md`,
> `tests/probe/README.md`, three probe headers,
> `harness/selfcheck/syscall_consumer.npk`, `meta/roadmap/0.1/0.1.0.md` and
> `ROADMAP.md`. `0.0.0.md` and `0.0.1.md` had their relative link depth changed
> by the move and it is changed back; **the depth changed and no claim did**,
> in both directions.
>
> **Why reverse rather than fix in place — RX-140.** A cycle folder inside
> `done/` is a claim that the cycle is finished. Fixing two blocking defects in
> files sitting there would have meant editing archived notes, and
> `done/README.md`'s rule that *archived cycle notes are never rewritten* is
> worth more than a tidy directory. A rule gets its force from being absolute,
> and the first exception would have been granted by the session that wanted
> it. `0.0.5.md`'s own REPORT block anticipated this: *"if the audit wants
> anything undone, it is one `git mv` back."*
>
> **What is NOT rewritten, deliberately.** `0.0.5.md`'s committed REPORT block
> (W-28) and its two statements that step 6 *performed* `git mv meta/roadmap/0.0
> meta/roadmap/done/0.0` still read that way, because they are true accounts of
> an action that was taken. The distinction this note draws, and that the
> earlier one did not: **live navigation is corrected, historical claims are
> not.**
>
> **The redirect note's own numbers were wrong, which is finding N-3 and is now
> moot.** It said "41 such mentions across 15 files", present tense. Re-derived
> at the time it was written: 33 occurrences across 9 files, having been 49
> across 17 before the move. It matched no state the tree ever had. The
> reversal removes its subject rather than its arithmetic, and the lesson —
> **a count written in the present tense about a tree that is mid-edit is stale
> before the commit lands** — is recorded in `0.0.5.md` §8 where it can be
> acted on.


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
| [0.0.3](0.0.3.md) | **The harness, part 2** — `parse`, ~~`accept`~~, `check`; the self-check; the tree checks | the self-check proves the harness can fail, **eight** of eleven ways; the other three need stages that do not exist until 0.3, 0.5 and 0.8 |
| [0.0.4](0.0.4.md) | **`src/core/`** — `Vec<T>`, `Bytes`, `ByteSet`, `SparseSet`, `limits.npk` | four primitives with their own suites and their obligations written |
| [0.0.5](0.0.5.md) | **Close** — the findings, the spec amendments the probes forced, the handoff to 0.1 | the audit triage discharged, `done/0.0/`, and 0.1 openable by a fresh session |

## Checklist

### 0.0.0 — the probes
- [x] `tests/probe/probe01_pod_inst_array.npk` — a `Vec<Inst>` of 100 000 12-byte POD values: fill, read, copy, clear; `#size_of<Inst>()` asserted  
      **DONE** — `#size_of<Inst>` = 12, confirmed.
- [x] `tests/probe/probe02_payload_enum.npk` + `probe02b_derive_eq.npk` + `probe02c_derive_ord.npk` — a tagged enum with payloads, destructured in a `pick`, stored in a `Vec`, `#[derive(Eq, Debug)]`, `#size_of` asserted  
      **DONE at 0.0.0** — and at that pin `#[derive(Eq)]` on a payload enum was **refused** and `#[derive(Ord)]`
      compared tags only (workbench O-N10), so the comparison was hand-written and 02b/02c recorded both halves.
      **O-N10 IS DISCHARGED AT THE RE-PIN, measured here 2026-09-04 — RX-125.** Both derives now work and read
      every payload field; the two probes were rewritten to assert the new behaviour and **renamed**, because
      `…_refused` and `…_tag_only` had become false claims. 0.0.0's verdict table is not rewritten; the redirect
      is `0.0.3.md` §6.
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
      **DONE at pin `950bb1d`, and HALF OF IT HAS SINCE CHANGED — RX-127, 2026-09-06.** `prove`,
      `requires` and `ensures` still refuse `NITPICK-RUNG-001` naming 1.5, so the comment-form
      obligations remain inert. **`limit<Rules>` does not**: it went live in the compiler's 1.5.2
      and is now accepted and enforced, so `probe13b` moved out of `refused/` as
      `probe13b_limit_enforced.npk`, `probe13e` proves the check fires, and
      `refused/probe13f` records the new refusal. **And `never fails` + `limit` is NOT a permanent
      refusal**: the compiler's D-241 (2026-09-03) retired that rule, so the `NITPICK-TYPE-037`
      sentence this line used to carry is false. See `0.0.4.md` §7 and `VERIFICATION.md` P-1a.
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
      **HALF DONE WHEN THIS WAS WRITTEN AT 0.0.1, AND FULLY DONE AT 0.0.2 — the counts below are
      0.0.1's and are kept because they are the reasoning's evidence.** `conformance` is declared at
      `compile`/`positive` and is live. `probe` was **not** declared: 16 of the 23 probes then in the
      tree carried `expect-exit:` and 7 carried `expect-error:`, and no single entry can judge both —
      `run_program` does not skip a file with `expect-error`, and `run_compile`'s `kind` selects the
      checker, not the file set (`npkg/suites.npk` :779 and :608). **RX-119**; 0.0.2 split the
      directory and declared **both** `probe` and `probe-refused`, and the split today is
      **19 / 6 over 25 probes** (`tests/probe/README.md`). The three-entry shape is in the manifest ready
      to uncomment and the split is 0.0.2's, above.
- [x] a consumer program under `tests/conformance/` imports `src/lib.npk` by relative path and compiles, with a comment naming O-G3 as the reason the path is relative  
      **DONE, and it links and runs** — `npkc` 0, `llc` 0, `ld.lld` 0, binary 0, and the same four
      through `opt -O2` (rule B-3). Six controls beside it, each failing for the right reason.
- [x] CI: a workflow running `harness/run.py` on push, with LLVM 20.1.2 and the compiler built from a **pinned commit**, not a branch  
      **WRITTEN, AND NOW RUN GREEN.** Pins the compiler by full sha and LLVM by exact patch release,
      and *asserts* both rather than reporting them. Run
      [`33835762747`](https://github.com/alternative-intelligence-cp/nitpick-regex/actions/runs/33835762747)
      on a push of `main` at `c7b8711`: conclusion **`success`**, job `build` green, 8m48s, all ten
      declared steps — including the compiler built from the pin, which W-18 forbids rehearsing
      from here. It proves the toolchain pin and that the conformance consumer still compiles, links and
      runs; it proves nothing about this library's behaviour, because `harness/run.py` is the stub
      until 0.0.2. See 0.0.1's acceptance for the full boundary.
- [x] `CLAUDE.md` and `CONTRIBUTING.md` re-read against 0.0.0's verdicts and extended  
      **DONE, and the re-read earned its place**: `CLAUDE.md` still said out-of-range indexing traps,
      which probe 08b refuted at 0.0.0 (RX-111), and its "What this is" section was empty.

### 0.0.2 — the harness, part 1
- [x] `harness/run.py`: the manifest reader, the toolchain pin check, the module-graph walk
      **DONE** — six modules (`manifest`, `toolchain`, `expect`, `elf`, `irscan`, `build`, `stages`)
      plus the driver. The manifest reader is the compiler's subset with the compiler's schema, and
      refuses a key the schema lacks; the toolchain check asks `llc`, `opt` and `ld.lld` themselves.
- [x] the build pipeline — `npkc` → `opt` (check leg) → `llc` → the undefined-symbol scan → `ld.lld`
      **DONE, with the IR call-edge scan inserted between `npkc` and `llc`** (B-2a). `BUILD.md` §2's
      diagram is amended to the order the runner actually uses.
- [~] ~~the undefined-symbol scan against the runtime allowlist~~ — **STRUCK: there is no runtime
      allowlist and there cannot be one.** RX-116 replaced it with a difference against a committed
      baseline before this subcycle started; the scan **is** a build step, as this line asked
      (B-2, P-11), and it reads the ELF64 symbol table with `struct` rather than spawning a fourth
      tool. Verified against `llvm-nm --undefined-only`: 29 = 29, identical sets.
- [~] ~~**`check_no_syscalls`**: the object's undefined symbols held to a committed expected list~~
      — **STRUCK AND REPLACED, and the replacement is the subcycle's main finding.** The committed
      list was already dead (RX-116). The *difference* that replaced it **also cannot see a
      syscall**: measured **at compiler `950bb1d`**, a program with `sys(39i64)` in `main` has the same 29
      undefined symbols as one without, because `npk_sys6` is already the prelude's.
      *(Dated 2026-09-06 at 0.0.5: this line said "measured at the pin", and **the pin moved twice
      underneath it** — at `3d15ac9` the floor is 2 symbols and the difference IS `npk_sys6`, so the
      sentence went false with nobody editing it. The commit is named here for that reason; the
      finding itself is RX-131's, the reproduction of both pins is `harness/baseline/RX120.txt`, and
      the two-layer conclusion below is unchanged because the second layer names the calling
      function and no symbol set can.)* So
      `check_no_syscalls` is now **two** layers — the symbol difference, and an IR call-edge scan
      that names the function (**RX-120**). RX-008's rule is unchanged; both layers apply to
      programs whose graph reaches `src/` (**RX-121**), and the runner says per run how many that
      was.
- [x] the `program` stage, at -O0 and again under `opt -O2`, same exit required (B-3)
      **DONE** — 16 probes, both legs, same exit.
- [x] `// expect-exit:` and `// stress: N` honoured
      **DONE, marker for marker with `npkg/expect.npk`** — including `expect-error-at:`,
      `expect-note:`, `argv:` and the "a number that cannot be read makes the test FAIL" rule.
      Two values are refused that the compiler's reader accepts, both unsatisfiable rather than
      merely odd (**RX-122**).
- [x] the `repro` check: two builds from different working directories, byte-identical IR
      **DONE, and seen to fail** — §6 D4.
- [x] one real program green — probe 01, run as a `program`-stage entry
      **DONE, and all sixteen are**, plus the conformance consumer and the seven refusals.
- [x] **split `tests/probe/` by kind and declare both entries** (RX-119).
      **DONE.** The seven `expect-error:` probes are in `tests/probe/refused/`; both entries are
      declared and live; `recursive` defaulting false is what keeps them disjoint. Cycle 0.0.0's
      verified record is **not** rewritten — the redirect table is `0.0.2.md` §4, in the pattern
      RX-114 set.

### 0.0.3 — the harness, part 2
- [x] the `parse` stage over every `.npk` in the tree, each file once
      **DONE, and it is `npkc` rather than the compiler's `tools/parse_check` — RX-124.** That tool imports
      nineteen files of the compiler's frontend, which RX-007 forbids depending on and W-18 forbids building
      from here; it is the same reason rule B-4a already gave for striking `accept`, one row away in the same
      table. The stage is **strictly stronger than parsing** and every file is judged **as a root**.
      **It earns its place:** `src/lib.npk` reaches only `src/api/api.npk`, so six of the eight `src/` files
      were reached by no suite at all before it existed.
- [~] ~~the `accept` **and** `check` stages~~ — **`check` DONE; `accept` was already STRUCK.**
      Rule B-4a (RX-117) struck `accept` before this subcycle began, and the runner now refuses it **by name**
      rather than reporting it unimplemented — declaring it is a manifest error, not a pending feature.
      `check` runs over the new `tests/rejection/`, sharing `check_rejection` with `compile`/`negative` so that
      rule B-7 has one implementation and not two.
- [x] `--only`, and output that says twice that a filtered run concludes nothing
- [x] `harness/selfcheck.py` with all **eleven** cases — **EIGHT live, three pending.**
      The plan said "seven live … and case 4 live with the `parse` stage this subcycle adds", which is eight;
      the runner's summary says eight. Case 10 was decided in execution: **neither a substituted emitter nor a
      fixture** — a fixture cannot exist, because a file whose IR differs between two builds is what D-078 says
      the compiler never produces. It tests the instrument directly. `0.0.3.md` §3.
      **And the self-check was MUTATION-TESTED** (`0.0.3.md` §4): three defects introduced into the harness,
      each reddening exactly its own case. Disabling the IR call-edge scan reddens case 8 and **not** case 9,
      which is RX-120 reproduced from the other side.
- [x] the self-check runs **first** in every full invocation
      **DONE** — the only invocation that skips it is `--record-baseline`, which judges nothing and writes a file.
- [x] `check_layering` — every `use` edge against `specs/BUILD.md` §6, **including the oracle's restriction**
      (B-17), which has nothing to check yet and is the right answer
      **DONE, and it carries B-15a too** — the umbrella's plain-`use`-cancels-`pub use` shape (RX-113, O-N13),
      which produces **no compiler diagnostic at all**. Seen to fail, `0.0.3.md` §5 D2 and D3.
- [x] `check_constants_named` and `check_error_budget` live — and both **seen to fail**, `0.0.3.md` §5 D1, D4
- [x] `check_specs_current` reporting, not failing — 42 markdown files, 14 specs, nothing stale
- [x] **added in execution:** `tests/rejection/` exists, with the repository's first two rejection fixtures —
      a consumer missing a system `failsafe` arm (`REACH-002`) and one missing the `(*)` wildcard (`PICK-003`).
      Both import `src/lib.npk` by a relative path, which makes them the **standing** instance of B-7's hazard.
      A third was planned and abandoned on evidence: a consumer missing the `(ERegexPattern)` arm still
      **compiles**, because nothing can raise one while the surface has no callable entry point (control E4).
- [x] **added in execution:** the two O-N10 probes rewritten and renamed at the re-pin — **RX-125**, `0.0.3.md` §3 and §6

### 0.0.4 — `src/core/`
- [x] `src/core/limits.npk` — all nine bounds from `specs/SAFETY.md` §5, each with the specification rule that set it  
      **DONE** — nine, plus `HIR.md` §5's two literal-extraction bounds. `check_constants_named` reports 9/9 and had been running with only its negative half since 0.0.3, so the day the file appeared the check already did.
- [x] `src/core/vec.npk` — `Vec<T>`: `init`, `reserve`, `push`, `pop`, `at`, `set`, `truncate`, `clear`, `insert`, `remove`, `swap_remove`, ~~`fill`~~, `free`; both `T` shapes exercised  
      **DONE**, with two renames and one strike, each with a reason.
      **AND THREE GROWTH PATHS DID NOT TERMINATE OR DID NOT CHECK — RX-139**, found by the cycle 0.0 audit and not by this checklist. `vec_free` sets `cap = 0` as poison and `vec_reserve` read it as an arithmetic starting point: `while (nc < want) { nc = nc * 2 }` from zero **does not terminate** (exit 124 under `timeout 6`). `vec_push` and `vec_insert` reached `ralloc(<dangling>, 0)` and were stopped by the RUNTIME's refusal (D-150) rather than by this library's own check. All three now trap `OutOfBounds` at the top of the entry point, with a unit case each. `vec_init_zeroed(-5)` — found while establishing the extent — wrote five elements **before** its block at exit 0, and traps too.
      **`at` is `vec_get`**: `SAFETY.md` S-23 names the pair `vec_get`/`vec_set` and the specification is the authority (RX-002).
      **~~`fill`~~ IS STRUCK AND CANNOT EXIST**: a generic `vec_fill<T>(v, n, x)` is refused `NITPICK-TYPE-046` — *"`T` is a type parameter, and this body is checked once for every type it is instantiated at — some of which own storage (D-264): a copy here would leave two owners at those"*. A generic body is checked against EVERY instantiation, so an operation that COPIES its element cannot be generic at all, and `move` does not rescue it because the value is consumed by the first slot. Replaced by **`vec_init_zeroed<T>`** over `calloc` — the fill that needs no value — which is what `SparseSet` wanted.
      **`vec_free_owning` is new**, and it is the function the managed-half gate exists to test.
- [x] `src/core/bytes.npk` — `Bytes`: `init`, `push`, `extend`, `extend_str`, `put_uint`, `len`, ~~`view`~~, `take`, `clear`; `put_uint` allocation-free and correct at 0, 1, 9, 10, 99, 100 and `uint64` maximum  
      **DONE**, and **~~`view`~~ IS STRUCK ON A SAFETY GROUND**. A view is a `uint8[]`, and returning a slice over a local's body is the ONE ESCAPE THE COMPILER DOES NOT DIAGNOSE — workbench registry **O-N9**: returning `@x` is `NITPICK-BORROW-001`, returning a slice is not, and reading it afterwards reads freed memory. The ecosystem's house rule until it lands is *a view is a PARAMETER, never a return value*. `bytes_get` serves one byte, `bytes_extend` bulk.
      **AND THE LINE THAT STOOD HERE WAS FALSE IN BOTH ITS HALVES — RX-138.** It read *"`bytes_take_string` hands over an owning `string`, which is the only shape that may leave the frame"*. It handed over a **borrowed view** — `string_from_bytes` sets `cap 0` and the compiler's runtime calls that *"the not-mine bit"* — so every growth freed the body underneath it (measured: exit 46 on a read-back, exit 170 = `0xAA`, D-183's free poison), and returning it from the frame that owns the `Bytes` was refused `NITPICK-BORROW-001`. **This file struck `view` for the escape and then described the escape as the safe shape**, eleven lines from where the rule is stated. It is `bytes_copy_string` now, it copies, and the read-back after a growth is a unit assertion rather than a sentence.
      `put_uint` is also **division-free** — `RX-132`, and the reason is the error budget rather than speed.
- [x] `Bytes` growth amortised linear, proven by appending a million bytes and bounding the reallocation count — the compiler's own quadratic-capture defect is why this test exists  
      **DONE** — one million bytes from capacity 1, **counting the reallocations** rather than the time, because a timing assertion in CI is a flake generator. Doubling gives 20; the gate is 30, which separates doubling from linear-or-worse, and the capacity ceiling catches a growth factor that overshot.
- [x] `src/core/byteset.npk` — `ByteSet` as `uint64[4]`: union, intersect, complement, contains, iterate; exhaustive over all 256 bytes  
      **DONE, and literally exhaustive**: every operation at every one of the 256 values, including the add/remove sweep that asks 256 membership questions per value — 65 536 pairs — because *only* the byte just added is a test a word-index slip passes. **The sweep prints its count and the program asserts it**, so "swept the domain" and "swept three of it" are not byte-identical here.
      It is also the one structure in `src/core/` needing **no accessor pair**, and the reason is the type rather than care: `uint64[4]` is a fixed array, so D-070's guard IS emitted.
- [x] `src/core/sparseset.npk` — `SparseSet`: O(1) insert, membership, clear; **the invariant `dense[sparse[k]] == k` asserted after every operation** in a property test. This is the structure the linear-time guarantee rests on and it is the easiest to get subtly wrong  
      **DONE** — ten thousand seeded-xorshift operations, and after EVERY one both the membership at every key (against an independent `Vec<int32>` reference sharing no code with it) and the structural invariant read straight off the two backing arrays. Membership could be right while the mapping was corrupt, so both are checked.
      **P-22's open half is decided:** `sparse` is built with `vec_init_zeroed` (one `calloc`) rather than relying on reading uninitialised storage. `clear` is still O(1) — only `count` is reset — so the engine's property is kept without resting on the part of the trick that is a hope.
- [x] every accessor's bounds obligation written as a comment in the `requires`/`ensures` syntax it will take, with a property test standing in  
      **DONE, and checked against the compiler rather than against this repository's own stale claim.** Cycle 0.0.0 recorded that `never fails` and a contract are mutually exclusive by a *permanent* `NITPICK-TYPE-037`; that is false since the compiler's D-241 (RX-127), so the obligations are written `never fails requires …`, which is `VERIFICATION.md` P-2's own shape. `requires` and `ensures` still refuse `NITPICK-RUNG-001`, so they remain inert — but that is now a per-construct fact to re-measure rather than a property of the rung (`VERIFICATION.md` P-1a), because `limit<Rules>` went live and this library declined it (S-24).
- [x] the leak tests exit 0, so a missing **`wild` block** free is a trap — and
      **that is the whole of what `exit 0` proves** (RX-123). D-151 counts `wild`
      blocks, D-188 counts live drivers, and neither sees a managed body, so a
      `Vec` freed without dropping its owning elements exits 0 (`SAFETY.md` §8b,
      S-22). **Where the obligation is managed the gate is a MEMORY CAP**, and
      `Vec<T>`'s elements are exactly that case — this line named `vec_free`
      until 0.0.3 and so asserted the gate for the one case it cannot see  
      **DONE, BOTH HALVES, AND THEY ARE SEPARATE TESTS.** The block half: every
      program in `tests/unit/` exits 0 or traps by design, so a leaked `wild`
      block is a red. The managed half: `vec_owning_freed.npk` and
      `vec_owning_leak.npk` differ only in `vec_free_owning` against `vec_free`,
      run under one 64 MiB address-space cap, and are required to end
      **differently** — 0 and 92 (`HeapOom`) — with `/bin/true` passing at the
      same cap, because a low cap measures the dynamic loader rather than the
      program. `mem-cap-mib:` is the new expectation header that carries it, and
      the harness runs that control on every capped file.

### 0.0.5 — close
- [x] every probe verdict reconciled against the specifications
      **DONE, and six of the 23 had a consequence that landed somewhere other than the document
      that owns it.** Read file by file rather than grepped, because every one of the six is a
      claim about TENSE OR TRUTH and contains no wrong token: `meta/specs/README.md` still said an
      out-of-range index traps (the belief probe 08b refuted on day one, in the paragraph a
      newcomer reads first, citing no decision so no sweep could reach it); `SAFETY.md` §7 still
      gave probe 09's *refuted* prediction while calling itself "the evidence for the request";
      `API.md` §8 still said "decide after probe 12 says what the trait actually admits" three days
      after probe 12 said; `API.md` §2 lacked the `Optional`-is-not-`pick`-able fact the probe's own
      header assigned to it; `SAFETY.md` §6 still spelled `Match` as `start`/`end` where two other
      specs had said `lo`/`hi` since 0.0.0; and `CLAUDE.md` quoted `#size_of<HirNode>` = 24, which
      measures **the payload spelling `HIR.md` H-2 declined**. RX-135, RX-136, RX-137.
- [x] the cycle's findings written as a numbered list — **25 of them, `0.0.5.md` §A**, in three
      groups (the language, the instruments, the documents) so a sibling can act on one without
      reading the rest.
      **Two of the 25 were WRONG and the audit found both**: the RX-120 obligation was recorded as
      discharged by a transcript containing a fabricated command, and the `bytes_take_string`
      hand-over was listed as safe. `0.0.5.md` §8 carries the corrections beneath them.
- [x] the harness self-check green, the full run green — **141/141 in 46.2 s** after the SECOND
      audit triage (108/108 after the first, 98/98 at the refused close), self-check first, eight
      live cases and three printed as PENDING rather than as passing, **plus one PENDING UNIT that
      is outside the denominator and is not a pass**.
      **AND THE GREEN WAS NOT THE EVIDENCE, WHICH IS THIS CYCLE'S SHORTEST LESSON — TWICE OVER.**
      The 98/98 run was green over a use-after-free its own suite CONSTRUCTED and declined to read,
      and over a `vec_reserve` that does not terminate. **The 108/108 run was green over a bounds
      stop that did not stop**, because all twelve of its out-of-range units passed a non-zero
      argument and the stop returned only at zero. Each of the five units added by the first triage
      and the seventeen added by the second was seen to FAIL before it was trusted, and so were the
      seventh tree check, the RX-120 assertion and the new `pending-until:` marker.
- [x] `0.1/0.1.0.md` written execution-grade
- [ ] cycle archived to `done/0.0/`, `ROADMAP.md` updated — **DONE ON 2026-09-06 AND REVERSED THE SAME DAY.**
      The W-22 audit refused the close (two blocking findings in `src/core/`), so the
      move was undone with one `git mv` and this box is open again. It is ticked at
      the close the audit accepts, and not before. See the note at the head of this
      file and `0.0.5.md` §8.
- [x] **added by the audit triage:** every one of the audit's 15 findings carries a line —
      fixed, deferred to a named cycle with a reason, or refused with its cost stated —
      counted rather than asserted (`0.0.5.md` §8)
- [x] **added by the SECOND audit triage:** every one of the second audit's findings carries a
      line — **6 items, 6 lines, all FIXED, none deferred and none refused** (`0.0.5.md` §9).
      The denominator has two halves and both are stated: the audit filed **5** findings, and the
      dispatch split `BL-4` into its comment half and its memory-cap half because the root cause
      was raised as a compiler defect and confirmed as **DEF-25**, which gives **6**.
      **The largest was `BL-3`: the library's only out-of-range stop returned for `i == 0`**, so
      nine `pub` entry points performed the access they had just refused whenever their container
      was empty. RX-143 … RX-146

## Gate

A full `harness/run.py` green; the self-check proving the harness fails eleven
ways; `check_no_syscalls` green over a real object; `src/core/`'s four
primitives each with a suite; and every probe with a recorded verdict whose
consequences are written into the specifications.

**AND, SINCE 2026-09-06, A W-22 AUDIT THAT HAS SEEN THE TREE IT IS ACCEPTING.**
Every clause above was met at the refused close, and an independent verifier
passed it on eight checks, and the cycle still shipped a non-terminating loop and
a use-after-free in `src/core/`. **A gate written as a list of green things is a
gate a green run satisfies**, which is no gate at all against a suite that
declines to make the read that would go red. The audit is the clause that is not
satisfiable by passing.

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

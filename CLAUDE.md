# CLAUDE.md

Guidance for Claude Code sessions working in this repository.

## What this is

`nregex` — a regular-expression library for **Nitpick**, the safety-critical
systems language at `../../nitpick`. **Status: cycle 0.0, foundations.** The
specifications, the decisions and the roadmap are complete; `tests/probe/` holds
**25** language probes with recorded verdicts, split **19 / 6** by kind (16 / 7,
then 17 / 6 when the `94874ce` re-pin discharged O-N10 and `probe02b` stopped
being refused — RX-125; then 19 / 6 when the `3d15ac9` re-pin made
`limit<Rules>` live and `probe13b` stopped being refused — RX-127);
`tests/rejection/` holds two consumer-facing refusals; `harness/` builds, sweeps,
diffs and judges them, **and proves first that it can fail**; and since 0.0.4
`src/core/` is real — `Vec<T>`, `Bytes`, `ByteSet`, `SparseSet` and `limits.npk`,
with 18 unit programs of their own. **No matching happens yet**: `src/syntax/`,
`src/hir/`, `src/compile/`, `src/engine/`, `src/unicode/` and `src/api/` are
still one placeholder module each. A full green run is **108 units** and seven
tree checks; take those numbers from the runner's summary rather than from here.
**This file said 98 and six in one paragraph and *four* tree checks 220 lines
lower**, and the cycle 0.0 audit found it (N-2) in the document every session is
told to read first. Two sections of one file disagreeing is the shape this
repository named a durable lesson and then left standing in its own onboarding
page: **proximity is not review**, and a number written twice is a number that
will be corrected once. There is now ONE statement of each count in this file,
and the runner's summary is the authority for both.

## Before starting a session here

Check **[`../BOARD.md`](../BOARD.md)** — it says whether this repository
is claimed by a stream, and by which. **One writer per repository, always.**
[`../WORKSTREAMS.md`](../WORKSTREAMS.md) is the dependency graph and the
stream partition: what gates this repository, what this repository gates, and
what to do when a cross-stream gate is not ready yet.

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
- **Integer overflow and division by zero trap. OUT-OF-RANGE INDEXING DOES NOT,
  on the type this library indexes most** (RX-111). D-070's check attaches to
  types that carry a length — a slice `T[]`, a fixed array `T[N]`. A
  `wild T->` block is a bare pointer and `Vec<T>.items` is one, and so is a
  `buffer` through `.ptr`, which has no slice route at all (RX-118). An
  out-of-range index there **reads and returns a heap word**, silently. The
  `vec_get`/`vec_set` and `bytes_get`/`bytes_set` pairs are the only bounds
  check this library has. `SAFETY.md` §5.3.
- **`comptime` cannot index a string**, so a compile-time-validated pattern is
  not currently expressible — see O-G1, which is the most valuable request on
  the list.
- **There are no static methods** (D-185), so construction is
  `regex_compile(…)`.

## Reserved words that read like ordinary names

`meta/specs/BUILD.md` §7 has the table. The ones this domain wants most:
`range`, `end`, `in`, `limit`, `any`, `buffer`, `raw`, `move`, `error`, `mod`,
`on`, `as`, `with`, `where`, `is`, `is_err`, `never`, `fails`, `pick`, `fall`,
`give`, `pass`, `fail`, `relay`, `drop`, `Rules`, `fixed`, `Self`, **`stack`**.

**`stack` is the one that costs an hour**, and cycle 0.0.0 paid it. It is a
MemoryQualifier beside `wild`, `wildx` and `defer`, it is the natural name for
an explicit-stack parser's local — which is `src/syntax/`'s whole shape — and
**it does not fail where you write it**: you get `PARSE-002` at the declaration
and then "this `{` is never closed" pointing at an enclosing brace dozens of
lines away, plus a cascade to the end of the file. *If a parse error claims an
unclosed brace and the braces are balanced, look for a local named after a
qualifier before you touch a brace.*

The substitutes this library uses, so the tree stays consistent: **`hi`** for a
range's upper bound and for a `Match`'s end (the fields are `lo` and `hi` by
`API.md` A-3's choice — **not** because `Match.end` is refused, which **RX-134
measured to be false at all three kept pins**: a reserved word is refused as a
**binding** name and accepted as a **field** name), **`src`** for an input
cursor, **`bound`** for a
limit, **`rng`** for a range value, **`dot`** for the any-character construct,
**`sel`** for a selection.

Three shapes that surprise a C or Rust habit: adjacent string literals do not
concatenate; `discard(x);` takes parentheses and `defer { … }` takes no
trailing semicolon; declarations end `};` and control-flow blocks do not. And a
file's `mod:` name must equal its basename.

## What cycles 0.0.0, 0.0.1 and 0.0.2 measured, that a reader would otherwise assume

Each of these was written the other way round in some document here before it
was measured. `meta/roadmap/0.0/0.0.0.md` §7,
`tests/conformance/TRANSCRIPT.txt` and `meta/roadmap/0.0/0.0.2.md` §5 are the
evidence.

- **An `Optional` is not `pick`-able.** `pick (m) { (NIL) {…}, (Match:g) {…} }`
  is `NITPICK-PARSE-005`; an `Optional` has no readable members. Test with
  `== NIL`, read with `??`. This is caller-visible on every entry point in
  `API.md` §2, because `regex_find` returns `Match?`.
- **`npkc` exit 0 does not mean a program is well-formed** (registry O-N11), and
  this library is a standing example: **every file in `src/` compiles at
  exit 0 and every one is refused by `llc`** (RX-115) — eight files when this was
  measured, 13 today — because a library file
  cannot define `@npk_failsafe` and `npkc` never declares it. **There is no
  library object.** `src/` reaches the compiler only through a program root, and
  `tests/conformance/import.npk` is the smallest one. Run all four steps —
  `npkc`, `llc`, `ld.lld`, the binary — on anything you claim compiles.
- **`src/lib.npk` re-exports with `pub use`, one name per line, and must never
  plain-`use` a path it also `pub use`s** (RX-113). A plain `use` re-exports
  nothing; a plain `use` above a `pub use` of the same path silently cancels the
  re-export, at no diagnostic, and the failure lands in the consumer as "cannot
  find X in this scope".
- **`exit 0` traps on a leaked `wild` block and sees nothing else** (RX-110).
  D-151 counts `wild` blocks, D-188 counts live drivers, and neither sees a
  managed body — so a container freed without dropping its owning elements
  exits 0. Where the obligation is managed, the gate is a memory cap.
- **`%` and `/` each add two mandatory `failsafe` arms**, `DivByZero` and
  `DivOverflow`. The error budget is charged by arithmetic, not only by a
  declared `error:`.
- **`limit<Rules>` is LIVE, ENFORCED, and it charges every consumer a `failsafe`
  arm** (**RX-127**, measured here at the `3d15ac9` re-pin). It refused
  `NITPICK-RUNG-001` until the compiler's 1.5.2; it is now checked in every
  build, and a violation traps `LimitViolated`. **A limited binding anywhere in
  a program's reachable call graph makes `(LimitViolated)` a mandatory
  `failsafe` arm** — measured with controls at both `pub` and module-private
  visibility, because reachability follows the call graph and not visibility.
  That is a second arm on top of `SAFETY.md` S-8's one, so **`src/` declares no
  `limit` at all** (S-24). `requires` and `ensures` still refuse
  `NITPICK-RUNG-001`, so the comment-form obligations remain inert — but that is
  now a per-construct fact to re-measure rather than a property of the rung
  (`VERIFICATION.md` P-1a).
- **`never fails` may carry `limit`, `requires` and `ensures`** — the compiler's
  **D-241**, 2026-09-03. This repository shipped the opposite claim, that they
  are *mutually exclusive* by a *permanent* `NITPICK-TYPE-037`, and wrote it
  into cycle 0.0.0's record as deciding which `src/core/` functions could carry
  an obligation at 1.5. It is false, and `VERIFICATION.md` §4's own P-2 example
  is `requires … never fails` — the shape the claim forbade.
- **`#[derive(Eq)]` and `#[derive(Ord)]` on a payload enum WORK, and read every
  payload field** — measured here at the re-pin, 2026-09-04 (**RX-125**). This is
  the reverse of what cycles 0.0.0–0.0.2 recorded: at pin `950bb1d` the `Eq`
  derive was refused `NITPICK-TYPE-034` and the `Ord` derive compared **tags
  only**, so `Repeat(2,5).cmp(Repeat(9,9))` answered `Equal`. That was registry
  **O-N10** and it is **DISCHARGED**. `Repeat(2,5) < Repeat(2,9)` now, so the
  second payload field breaks the tie.
  **But `.eq()` returns `Result<bool>` and `.cmp()` returns `Result<Ordering>`** —
  `if (a.eq(b))` is `NITPICK-TYPE-007`, "there is no truthiness in Nitpick".
  Unwrap with `?! E`. So replacing a hand-written comparison with a derive
  threads an error channel and charges `SAFETY.md` §4's budget; it is a cycle 0.2
  decision, not a free deletion.
- **Measure `#size_of`, never derive it.** `Inst` is 12, `Match` is 16,
  `ByteSet` is 32, `string` is 24.
  **`HirNode` is NOT on that list, and the reason is the rule itself.** The
  measured 24 belongs to the **payload spelling** of `HirKind` — the shape
  `HIR.md` H-2 examined and **declined** — not to the specified `HirNode`, which
  is a tag plus three `int32`s plus a `uint32` and does not exist in `src/` until
  cycle 0.2. Quoting 24 for it would be attributing a measurement of the rejected
  alternative to the accepted one, in the same sentence that says to measure.
  Its size is **unmeasured**; measure it when it is written, and make the probe's
  exit code be `#size_of` so the number cannot be transcribed wrongly (RX-135).
- **`npkc`'s exit codes are an alphabet, and `2` is not a refusal.** `0`
  success; `1` **refused, with diagnostics**; `2` the driver **could not proceed
  and judged nothing**, silently, with an empty stderr; `3` a trap. A test
  expecting 1 that receives 2 was never compiled and proved nothing. Assert the
  specific integer, never `!= 0`. `tests/conformance/TRANSCRIPT.txt` §F and §G.
- **A missing import exits `1` with `NITPICK-RESOLVE-005` — the very code a
  rejection fixture expects.** So a rejection test whose path is typo'd or later
  moved passes for the wrong reason, and only B-7's code-set equality tells the
  two refusals apart. Every import here is relative until O-G3 closes, so this
  is the ordinary case, not the exotic one.
- **`check_no_syscalls` needs two layers, and the reason changed under it —
  which is the more useful half** (RX-120, amended by RX-131). At `950bb1d` the
  undefined-symbol difference **could not see a syscall at all**: a program with
  `sys(…)` had the *same* 29 symbols as one without, because `npk_sys6` was
  already the prelude's. At **`3d15ac9` it can** — D-262 emits a prelude item
  only when referenced, so the floor is **2** symbols, a syscaller **3**, and
  the difference is exactly `npk_sys6`. Both pins are run back to back in
  `harness/baseline/RX120.txt`. **The second layer is not retired**: a symbol
  set reports *that* a kernel symbol is needed and never *where* it is called
  from, and a prelude that emits `npk_sys6` again blinds the first layer once
  more. **The moral is the durable part — that measurement was recorded as a
  permanent property and was a property of one compiler commit.**
- **An exit status is one byte.** `exit 321` reports 65, silently. Compose
  weights that cannot sum past 255, or print the value and assert on stdout.

## Building and testing

**`npkg` cannot build this yet** (`meta/specs/BUILD.md` §1, O-G3): it is the
compiler's own bootstrap ladder, and `[dependencies]` resolves to nothing.
`harness/run.py` is the runner until that changes (RX-004), and **since cycle
0.0.2 it is real**:

```
NPKC=… NPKRT=… python3 harness/run.py
```

builds every declared suite with the pinned `npkc`, assembles, scans, links
closed-world, runs, and judges by exit code — every `program`-stage file twice,
at −O0 and through `opt -O2`. It reads `nitpick.toml` for every path and every
flag and hardcodes none. **Since 0.0.3 it also sweeps every `.npk` in the tree with the `parse`
stage, judges `tests/rejection/` at the `check` stage, runs seven tree checks, and
— the one that matters — **runs the self-check FIRST** (`TESTING.md` V-21): eight
live cases feed it wrong expectations and require a red for each, and three more
print as PENDING on stages that do not exist until 0.3, 0.5 and 0.8.
`harness/README.md` states the boundary. CI (`.github/workflows/ci.yml`) pins the
compiler by full commit sha and LLVM by exact patch release, and **asserts**
both rather than reporting them.

The compiler binary is the **pinned toolchain** the board names
(`../BOARD.md`, W-18): `$NPKC` and `$NPKRT` are supplied to every session by the
orchestrator, or set by hand from `../.internal/toolchain/<commit>/`. Never build the
compiler from here and never read its `build/` directly — the guard refuses
the first, and the second is rebuilt under you. LLVM 20.1.2 exactly, pinned;
`llvm-config --version` to check.

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

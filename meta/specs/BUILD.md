# Building, testing, and the module conventions

How `nregex` is built today, how it will be built when the tooling catches up,
and the file-and-import conventions everything in `src/` follows.

---

## 1. What cannot build this yet, measured

Read at the compiler's commit for cycle 1.5.0:

- **`npkg build` is the compiler's own bootstrap ladder.** It assembles
  `runtime/npkrt.ll` and `bootstrap/seed/stage1.ll` into a builder, has that
  builder compile `[build] entry`, scans, links, and names the result `npkc`.
  There is no generic-project path and no `target = "library"` behaviour; the
  key is accepted by the schema and read by nothing.
- **`[dependencies]` resolves to nothing.** The loader's dependency-root list
  (`RootList`, `src/frontend/resolve_path.npk`) is created empty in
  `src/driver/pipeline.npk` and `rootlist_add` is never called. A
  `use "nregex/api.npk"` path — the dependency-root form — resolves against an
  empty set. Only `./` and `../` paths work.

**Decision RX-004: `harness/` builds and tests `nregex` until `npkg` can, and
retires into it.** That is precisely the relationship `bootstrap/harness/` has
to `npkg` in the compiler repository, including the part where both run side by
side and a parity stage holds them to each other before the older is retired.
Python is not a dependency violation: **zero-dependency governs the artifact,
not the workbench** — the compiler's `ORCHESTRATION.md` §6 says so in as many
words, about valgrind — and the compiler's own harness is Python for the same
reason.

---

## 2. The build, step by step

```
a PROGRAM ROOT  (and every module it reaches by `use`, including src/lib.npk)
   → npkc              →  build/<program>.ll
   → IR call-edge scan, differential against the baseline (B-2a)
   → llc               →  build/<program>.o       at the manifest's flags
   → undefined-symbol scan, differential against the baseline (B-2)
   → ld.lld -static    →  build/<program>         one program object + npkrt.o
   → run, judged by its exit code

and again, on the check leg (B-3):
   the same .ll → opt -O2 → llc -O2 → the symbol scan → ld.lld → run
                                      (minting direction only: `opt` legitimately
                                       REMOVES symbols — measured 29 → 28)
```

**Rule B-0 (RX-115) — the unit `npkc` accepts is a program root, and there is no
library object.** This diagram used to start at `src/lib.npk` and produce
`build/nregex.o`. Neither is achievable at compiler commit `950bb1d`: every file
in `src/` compiles at **`npkc` exit 0** and every one is then refused by `llc`
with `use of undefined value '@npk_failsafe'`, because `npkc` emits calls to
that symbol into every translation unit and never emits a `declare` for it. A
program is saved by its own `failsafe` producing a `define`; a library file has
nothing to produce one and, under D-248, may not. So **the library reaches the
compiler only by being imported from a program root**, and
`tests/conformance/import.npk` is the smallest such root.

`npkc src/lib.npk` is still worth running — it parses and resolves the whole
module graph, which is a real check — but **it is not evidence that the library
builds**, and `npkc` exiting 0 has never meant a program is well-formed
(registry O-N11). `nitpick.toml`'s `[build] output = "build/libnregex"` is kept
and annotated: it is the key `npkg` will read the day O-G3 closes, not a
description of anything that exists. Provisional workbench **O-N14**.

**Rule B-1.** Every tool invocation is built from `nitpick.toml`'s
`[toolchain]` lists. No tool ever runs at its own defaults — `llc` defaults to
`-O2` and would optimise a build the manifest declined, which cost the compiler
project a measured 25× on one module.

**Rule B-2 (amended by RX-116).** The undefined-symbol scan is a **build step,
not a test**, and it is **differential**, not an allowlist.

**`nregex` makes no syscall at all** (RX-008), and that rule is unchanged. What
changed is how it is checked. An absolute allowlist of *"the allocator,
`memcpy`/`memset`, the string primitives"* cannot express it, because there is no
library-only object to scan (B-0) and a whole-program object carries the
prelude's floor whatever the library contains: the consumer in
`tests/conformance/` — which calls nothing — has **29** undefined symbols,
including `npk_open`, `npk_read`, `npk_write` and `npk_sys6`, and `opt -O2`
removes exactly one of them.

So the harness builds a **baseline**: an empty `main`, a `failsafe`, importing
nothing. The undefined-symbol set of every `nregex` program object must **equal**
the baseline's, and anything in one and not the other is attributable to this
library and fails the run. The baseline's set is committed, so a prelude change
in a moving compiler is a visible one-line update rather than a mysterious red.
Measured at `950bb1d`: baseline 29, consumer 29, symmetric difference empty.
The baseline program and its two committed sets are `harness/baseline/`.

**Rule B-2b (RX-131) — the equality above became an emptiness claim about
nothing when the prelude was trimmed, so the difference is now a REVIEWED
RESIDUE LIST.** The compiler's D-262 (its 1.5.2d) emits a prelude item only if
it is REFERENCED. Re-measured at `3d15ac9`: the floor is **2** undefined symbols
(`npk_dalloc`, `npk_ofd_close`) and **2** call edges, both from the drop glue,
against 29 and 237 before. An object's undefined set is therefore exactly what
the program uses, and a four-line program making one `wild` block already
differs from the floor by three symbols — so the equality would fail on every
correct program in this library.

The `got - base` direction is now diffed against
`harness/baseline/RESIDUE.txt`: one line per symbol with **its reason**,
committed, refused at read time if the reason is missing, and checked **both
ways** so an entry no program references fails the run too. It is the absolute
allowlist the paragraph above says cannot be expressed — which was true while
the prelude was emitted whole, and is not any more. RX-120's kernel deny list is
applied on top and independently, so no edit to that file can admit a syscall.

**And this layer can now see a syscall, which RX-120 measured that it could
not.** At `950bb1d` a `sys(39i64)` program had the same 29 undefined symbols as
the floor, because `npk_sys6` was already the prelude's. At `3d15ac9` the floor
has no `npk_sys6` and the difference is exactly that symbol. **RX-120's second
layer stands regardless** — it names the calling function and survives a prelude
that emits `npk_sys6` again — and what is corrected is one supporting clause
inside it, not its decision.

**Rule B-2a (RX-120) — and the symbol difference is not enough, because it
cannot see a syscall.** A second layer scans the **-O0 IR's call edges**: every
`(enclosing function, callee)` pair whose callee is declared and not defined in
the module. A pair the program has and the baseline does not was written here,
and if its callee reaches the kernel or a descriptor it is a red run, named with
the function it is in.

The reason is measured, not argued. Two four-line programs at `950bb1d`
differing only by a `sys(39i64)` call in `main`:

| | undefined symbols | `call i64 @npk_sys6` sites |
|---|---|---|
| baseline | 29 | 2 |
| the same program plus one `sys(…)` | 29 | 3 |

The symmetric difference of the symbol sets is **empty**. `npk_sys6` is already
in every object because the prelude's `ByteReader.seek` and `std_dup` call it,
so **a program that starts making syscalls adds no symbol**, and B-2's first
layer reports a clean run over it. Cycle 0.0.2's own acceptance item — *"a
deliberately introduced `sys(…)` call fails `check_no_syscalls`, by name"* —
could not have been met by the instrument that was specified for it.

Three things the first run over the real suite forced, each of them a false
positive on all sixteen probes *(the suite held sixteen `program`-stage probes
when this was measured at 0.0.2; it holds **19** today, 25 counting
`refused/` — the number is left as the historical one because it describes that
run, and flagged because the next sentence's is not)*:

- **`llvm.*` is not the floor.** `llvm.sadd.with.overflow.i64` is declared,
  never defined, and is an *instruction* — it reaches no symbol table.
- **Compiler-generated glue is numbered and the number moves.** The baseline's
  `npk.drop.365` is probe04's `npk.drop.367`; the trailing digits are not part
  of a function's identity and are normalised away.
- **The list is a DENY list, not a permit list.** A permit list has to swallow
  `npk_trap`, the `defer` chain (`npk_chain_push`/`npk_chain_reset`), the
  allocator and `npk_string_concat`, which is most of what any program calls.
  What RX-008 forbids is *reaching the kernel*, and that is seven symbols:
  `npk_sys6`, `npk_open`, `npk_read`, `npk_write`, `npk_ofd_close`,
  `npk_io_register`, `npk_io_unwatch`.

**Rule B-2b (RX-121) — both layers apply to an `nregex` PROGRAM, which is one
whose module graph reaches `src/`.** RX-116's rule says *"every `nregex`
program object"* and the distinction is load-bearing: `tests/probe/` holds
**language** probes that import nothing from `src/` and never will
(`tests/probe/README.md` P-1). They allocate, they trap, they `await`. Holding
them to a library's zero-syscall rule costs the check its teeth — the residue
over **the 19 program-stage probes** is `npk_trap`, the `defer` chain, the
allocator and `npk_string_concat`, and widening the rule to swallow those would
swallow a real finding with them. *(This said "over the sixteen" in the present
tense until cycle 0.0.5, describing a suite three probes smaller. The harness
prints the number it actually ran on, per run, precisely so this sentence never
has to be the source of truth — read that instead.)* **The harness says, per run, how many units the scans
ran on and how many they did not**, because a check that quietly did not apply
reads exactly like one that passed.

**Rule B-3.** The optimised leg runs on every program, every time: the same
program re-emitted through `opt -O2` + `llc -O2` must produce the **same exit
code**, and the zero-dependency scan is repeated on the optimised object
because `opt` may mint libcalls. This is the compiler's 1.3.8 instrument, and
its first run there found a real defect that had passed for six cycles.

**Rule B-4 — reproducibility.** Two builds of the same tree from different
working directories produce byte-identical IR. `nregex` inherits this from the
compiler (D-078, D-204, D-236) and the harness has a `repro` stage that
measures it.

**Rule B-4c (RX-133) — an emission depends on a file's POSITION IN ITS TREE and
not on how the compiler was invoked, and CI records the compiler's own digest
because of it.** D-236 renders every site-table path relative to the **manifest
root** — the directory holding `nitpick.toml` — so the working directory and
whether the argument was absolute or relative change nothing, while moving a
file *within* the tree changes the bytes. Measured here with four controls at
`3d15ac9`: three invocations sharing no directory, no argument form and no
common working directory emitted byte-identical IR; the same source copied to a
sibling directory whose name is eight characters longer emitted 24 more bytes,
one per character per site row.

Two things follow, and the second is the point. **State the rule as
tree-position-dependent rather than "path-dependent"** — the looser wording
reads as *"an emission cannot be compared between machines"*, which is false and
would have made the next rule pointless. And **the compiler's own emission is
therefore comparable across machines**, since `src/npkc.npk` sits at one
position relative to its own manifest on every checkout — so CI prints
`sha256sum` and the byte count for every artefact the pinned compiler's build
leaves, `npkc.ll` first. It **prints and asserts nothing**: this repository has
not been given an expected value it could honestly check against, and the
comparison belongs to whoever holds both numbers.

---

## 3. Test stages

The harness mirrors the compiler's stage vocabulary
(`BUILD_REFERENCE.md` §7.1) so that the eventual move to `npkg` is a change of
runner and not a change of suite.

| Stage | Directory | Passes when |
|---|---|---|
| `parse` | every `.npk` in the tree | accepted by **`npkc`** with no diagnostic, each file **as a root** — ~~`tools/parse_check`~~, **B-4b (RX-124)** |
| `compile`, `kind = "positive"` | `tests/conformance/` | compiles, links, runs, and exits with the expected code (RX-117) |
| `check` | `tests/rejection/` | refused by the frontend with **exactly** the expected codes |
| `program` | `tests/unit/`, `tests/probe/` | emitted, scanned, assembled, linked, run at -O0 and again under `opt -O2`, the same exit both times |
| `corpus`† | `tests/fixtures/` | every committed pattern/haystack/expectation triple gives the expected answer, **through every engine** |
| `oracle`† | `tests/oracle/` | the naive reference matcher and each real engine agree, over a generated corpus |

† **`corpus` and `oracle` are this library's own**, not the compiler's. The rest
of the column is `BUILD_REFERENCE.md` §7.1's vocabulary exactly, so the move to
`npkg` is a change of runner and not of suite; these two are extensions and will
need a decision from the compiler, or a translation, when that move happens.

**Rule B-4b (RX-124) — and neither is `tools/parse_check`, for B-4a's own
reason.** The `parse` row above said *"accepted by `tools/parse_check`"* until
cycle 0.0.3, two rows above the `accept` row that B-4a struck for depending on a
compiler-repository tool. **It is the same tree and the same prohibition.** Read
at pin `94874ce` rather than assumed: `tools/parse_check.npk` opens with
`mod:parse_check;` and **nineteen** `use "../src/frontend/…"` imports — lexer,
parser, AST, diagnostics writer — so having it means compiling the compiler's
frontend, which RX-007 forbids depending on and W-18 forbids building from here.
`npkc` has no parse-only flag; its usage line at the pin is
`npkc <root.npk> [-o out.ll] [--obligations DIR] [--elide …] [--extra-picky=…]`.

So the stage is **`npkc` itself, and it is strictly stronger than parsing** —
the whole frontend runs and IR is emitted. A file with no `expect-error:` must
exit 0 **with an empty diagnostic channel**, because a warning on a clean exit is
still a finding (B-6) and exit 0 is the one place nobody looks for one; a file
with `expect-error:` is held to its own codes by B-7. **Every file is judged as a
root**, including one another file imports — "each file once" means once *as
itself*, and this is what re-checks the six `src/` files that `src/lib.npk` does
not reach.

*The general lesson, and it is the second instance in this repository within one
subcycle (see RX-123):* **when a rule strikes one row of a table, read the other
rows for the same reason.** A correction stops where its author's attention
stopped.

**Rule B-4a (RX-117) — the conformance suite runs at `compile`/`positive`, and
the `accept` stage is not available to this library.** `accept` is defined as
*"accepted by `tools/check` in silence"*, and `tools/check` is a
**compiler-repository** tool `nregex` does not have and, under RX-007, may not
import. `accept` also neither links nor runs, and linking and running is the
whole point: `npkc` exit 0 does not mean a program is well-formed (registry
O-N11), and B-0 is a fresh instance of exactly that — eight files that compile
at exit 0 and are refused by the next tool in the chain.

**Rule B-5 — expectations live in the test file**, in the compiler's marker
grammar, marker for marker:

```
// expect-exit: 7            // expect-error: NITPICK-TYPE-046
// expect-error-at: 14:9     // stress: 40
```

Marker for marker means marker for marker: a line whose **stripped** form starts
with `//`, the body dispatched on its **prefix**, the value the **whole** rest of
the line. So `// see \`expect-exit: 94\`` is prose and
`// expect-exit: 94 -- the OutOfBounds arm` is **unreadable**, not 94 — and a
test whose expectation cannot be read is a failing test, never a silently
defaulted one.

**Rule B-5a (RX-122) — two expectations are refused at read time, and both are
refusals of something that can never be met rather than a different judgement
of something that can.**

- **`expect-exit:` above 255.** An exit status is one byte: a process that
  exits 321 reports **65**, silently, and the compiler's own reader accepts the
  321 and then compares it against a number that can only be 0–255. Nothing in
  this ecosystem carries such a value today (swept 2026-09-04), so this refuses
  no test that exists; it refuses the one somebody writes next. A negative value
  keeps `npkg`'s meaning — `run_binary` reports a killed process as
  `0 - signal`, so `expect-exit: -11` is SIGSEGV — and below −64 there is no
  such signal.
- **`stress:` below 1.** `npkg` silently clamps it to one run
  (`run_binary`: `if (runs < 1i64) { runs = 1i64; }` — read at the pin, not
  assumed). That is not a hole there, and it is still a marker whose meaning is
  quietly rewritten, which is what this grammar exists to prevent.

**Rule B-6 — assert on codes and exit codes, never on message text.**

**Rule B-7 — unexpected diagnostics fail a test as surely as missing ones**
(D-237). The set of codes a rejection test reports must **equal** the set its
expectations name.

**And this one is load-bearing rather than tidy.** A missing or mistyped import
exits **1** with `NITPICK-RESOLVE-005` — the very code a rejection fixture
expects — so a rejection test whose fixture path is typo'd, or whose file is
later moved, **passes for the wrong reason**: it wanted a refusal, it got a
refusal, and the refusal was about the *path* rather than about the thing under
test. Nothing anywhere reports it. Measured both ways in
[`../../tests/conformance/TRANSCRIPT.txt`](../../tests/conformance/TRANSCRIPT.txt)
§G. Every import here is relative until O-G3 closes (B-15), so a moved path is
the **ordinary** case in this repository, not the exotic one. Code-set equality
is the single thing that makes the hole unreachable, and the harness names
`RESOLVE-005` specially when it fires so the reader is not left guessing.

**Rule B-7a — a `negative` test that names no code is itself a failure.** Exit
1 alone cannot tell "refused for the reason this test is about" from "the file
was not there", so a rejection fixture without an `// expect-error:` asserts
nothing at all.

**Rule B-8 — the harness is itself tested.** A self-check feeds it wrong
expectations and requires it to report every one as a failure, and it runs
first.

---

## 4. Dependencies

**Rule B-9 (RX-007).** `nregex` depends on the language, its prelude, and
nothing else. `[dependencies]` is empty and stays empty until a decision says
otherwise. That includes, specifically:

- **not the compiler's `src/`.** `npkg` imports `../src/frontend/list.npk`
  because `npkg` lives in that tree; `nregex` does not, and reaching into a
  compiler's internals for a growable array would couple this library's
  correctness to a file whose header says it exists for the compiler's own
  tables.
- **not the compiler's `lib/`.** It is on its way out of that repository into
  an `nlibc` sibling, so importing it today is importing a path that will
  change. `nregex` needs nothing from it in any case: it makes no syscall.
- **not `nitpick-tui`**, even though both generate Unicode tables from the same
  UCD and both need `Vec` and `Bytes`. That overlap is real and is recorded as
  **O-X1**, resolvable when dependency resolution lands.

**Rule B-10.** The prelude is used heavily: `Optional`, `Result`, `Ordering`,
the seven derivable traits, `string_bytes`, `string_from_bytes`,
`string_concat`, and the trap error identities. Every module has it bound with
no import.

---

## 5. Storage primitives

**Rule B-11a (RX-129) — the container API is FREE FUNCTIONS**, `vec_push(@v, x)`
and not `v.push(x)`, following the compiler's own `list.npk` shape (D-209).
Probe 04 compiled and ran BOTH forms, at two instantiations, so this is a choice
and not a default; cycle 0.0.0's verdict table deferred it here in as many
words. The deciding reason is that `SAFETY.md` S-23 makes the accessor pair
load-bearing and `VERIFICATION.md` P-2 writes its obligations on free functions.

**Rule B-11 (RX-006).** `nregex` declares its own, in `src/core/`:

- **`Vec<T>`** — the compiler's `List<T>` in shape (a `wild` block, a count, a
  capacity, doubling through `#size_of<T>()`), because that shape is right and
  has been exercised across twenty-two families. Ours because a library must
  not import a compiler's internals.
- **`Bytes`** — an owning byte sink over `buffer`, for building replacement
  output and diagnostic text. Every replacement is composed into one of these:
  `string_concat` allocates per call and a replacement over a large haystack is
  thousands of small pieces, which the compiler measured as quadratic in
  `npkg`'s first full run.
- **`ByteSet`** — a 256-bit class bitmap as `uint64[4]`, with union,
  intersection, complement and `contains`. The unit of a byte-level class after
  compilation, and small enough to live inside an instruction.
- **`SparseSet`** — the Pike VM's thread set: an integer-keyed set with `O(1)`
  insert, `O(1)` membership and `O(1)` clear, over two `Vec<int32>`s. This is
  the data structure that makes the Pike VM linear (`ENGINES.md` §3) and it is
  in `core` because the DFA's state-set construction uses it too.

**Rule B-12.** `nregex` declares no other container. Anything graph-shaped uses
an index into a `Vec`, not pointers — which is also what keeps every node POD
and every structure serialisable for a fixture.

---

## 6. Modules, files, and imports

**Rule B-13.** One module per file, and **a file's `mod:` name must equal its
basename** — the loader reports `NITPICK-RESOLVE-005` at line 1 otherwise, and
says nothing about the name.

**Rule B-14.** Public names carry the module's short prefix and nothing else
carries it: `regex_compile`, `hir_build`, `prog_emit`, `pike_search`. A
`pub struct` takes PascalCase (`Regex`, `Match`, `Cache`). Constants are
`SCREAMING_SNAKE`.

**Rule B-15 — imports are relative today.** Until dependency roots are
populated, every internal import is `use "./x.npk".*;` or `use "../y/z.npk".*;`,
and a **consumer** imports `nregex` by a relative path to its `src/lib.npk`,
which is the umbrella that `pub use`s the public surface.

> **`use` is not transitive** (`MODULE_REFERENCE.md` §2.3): a symbol imported
> into a module is not re-exported. `src/lib.npk` therefore re-exports
> deliberately, which is a feature — the public surface is a list in one file a
> reviewer can read.

**Rule B-15a (RX-113) — how the umbrella re-exports, and the one way it must
not.** Measured in 0.0.1 over a matrix of a type, an `error:` identity and a
function:

1. **Every line in `src/lib.npk` is `pub use`.** A plain `use` re-exports
   nothing, for any kind of symbol.
2. **No file plain-`use`s a path it also `pub use`s.** `symtab_bind_import`
   declines a name already bound and, on the "same declaration reached twice"
   path, returns the prior binding **without merging the new flags** — so a
   plain `use` above a `pub use` of the same path silently downgrades the
   re-export to nothing, at **no diagnostic**, and the failure appears in the
   consumer as *"cannot find X in this scope"*. Provisional workbench
   **O-N13**. `check_layering` gains this check at cycle 0.0.3.
3. **One name per line.** Several single-name `pub use` lines from one path do
   compose, in either order, so `API.md` §1's list stays one name to a line.

**Rule B-16a — `src/lib.npk` is above the layering diagram, not in it.** It
imports `api` (and, as the surface grows, whichever layers export a public
name) and nothing in `src/` imports it. `check_layering` reads that exception
from this rule rather than special-casing a filename.

**Rule B-16 — the layering, and the direction of every arrow.**

```
   api  ──►  engine  ──►  compile  ──►  hir  ──►  syntax
    │           │            │           │          │
    └───────────┴────────────┴───────────┴──────────┴──►  unicode  ──►  core
```

`core` depends on nothing. `unicode` depends on `core`. Nothing depends on
`api`. A module may not import a module to its left. `check_layering` diffs
every `use` edge against this diagram on every full run, because the compiler's
experience is that a layering violation arrives as a cycle six months after
somebody moved one function.

**Rule B-17 — `tests/oracle/` may import `core` and `hir` and nothing else.**
The naive reference matcher must not share code with the engines it judges: a
shared bug would make them agree. Enforced by the same check.

---

## 7. Reserved words that will bite

The compiler's table, filtered to what this domain reaches for. Each reads like
an ordinary name and is not:

| Wanted as a name | Actually |
|---|---|
| `range` | the builtin generic type — and a class is made of them |
| `end` | the `when`/`then`/`end` terminator — and a `Match` wants `.end` |
| `in` | the `for … in` keyword — and a parser wants an input cursor called `in` |
| `limit` | the verification keyword — and this library is made of limits |
| `any` | the type — and `.` is "any character" |
| `is`, `is_err` | keyword forms |
| `pick`, `fall`, `give`, `pass`, `fail`, `relay`, `move`, `drop` | keywords |
| `raw` | the unwrap keyword |
| `buffer` | the owning byte cell type |
| `error` | the declaration keyword; `Result`'s field is `.err` |
| `mod` | the module keyword |
| `on`, `as`, `with`, `where`, `never`, `fails` | keywords |
| `Rules`, `fixed`, `Self`, `impl`, `trait`, `assoc` | keywords |

The substitutes this library uses, fixed here so they are used consistently:
`hi` for a range's upper bound and for a `Match`'s end offset (**not** because
`Match.end` is refused — it is not, RX-134; because the pair reads better and
`API.md` A-3 settled it); `src` for an
input cursor; `bound` for a limit; `dot` for the any-character construct;
`rng` for a codepoint range value; `sel` for a selection.

**Rule B-18 — `Match`'s fields are `lo` and `hi`.** Stated in `API.md` §2 and
here, because `start`/`end` is what everyone reaches for and `end` does not
parse.

---

## 8. Three shapes that are not what a C or Rust habit expects

- **Adjacent string literals do not concatenate.** `"a" "b"` is two literals; a
  long pattern in a test is built with `Bytes` or written on one line.
- **`discard(expr);` takes parentheses; `defer { … }` takes no trailing
  semicolon.** Both wrong forms are parse errors.
- **Declarations end `};`; control-flow blocks do not.** A semicolon after an
  `if`'s closing brace is a syntax error.

---

## 9. Open items

- **O-B1 — when `npkg` can build a library.** The trigger to migrate is
  `npkg build` honouring `target = "library"` and `[dependencies]` populating
  the resolver's root list. Neither is on the compiler's 1.5 or 1.6 map, so
  this is a request to be made, not a date to wait for. Tracked as O-G3.
- **O-B2 — whether `nregex` ships as source or as an object.** Source keeps the
  closed-world link and the whole-program verification story intact.
  **Settled for now in favour of source**; revisit only if build times become a
  real complaint.

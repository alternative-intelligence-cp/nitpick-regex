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
src/lib.npk  (and every module it reaches by `use`)
   → npkc              →  build/nregex.ll
   → opt -O2           →  build/nregex.opt.ll     only on the check leg
   → llc               →  build/nregex.o          at the manifest's flags
   → undefined-symbol scan against the runtime allowlist
   → ld.lld -static    →  build/<program>         one program object + npkrt.o
```

**Rule B-1.** Every tool invocation is built from `nitpick.toml`'s
`[toolchain]` lists. No tool ever runs at its own defaults — `llc` defaults to
`-O2` and would optimise a build the manifest declined, which cost the compiler
project a measured 25× on one module.

**Rule B-2.** The undefined-symbol scan is a **build step, not a test**. Every
object is scanned and the build fails on any undefined symbol outside the
allowlist derived from `runtime/npkrt.ll`'s own `define`s plus `main`.

For `nregex` this check is stronger than it is for most libraries and worth
stating: **`nregex` makes no syscall at all.** Its only floor symbols are the
allocator, `memcpy`/`memset`, and the string primitives. A syscall appearing in
the scan is a defect, not a feature, and the harness asserts the symbol set
against a committed expected list.

**Rule B-3.** The optimised leg runs on every program, every time: the same
program re-emitted through `opt -O2` + `llc -O2` must produce the **same exit
code**, and the zero-dependency scan is repeated on the optimised object
because `opt` may mint libcalls. This is the compiler's 1.3.8 instrument, and
its first run there found a real defect that had passed for six cycles.

**Rule B-4 — reproducibility.** Two builds of the same tree from different
working directories produce byte-identical IR. `nregex` inherits this from the
compiler (D-078, D-204, D-236) and the harness has a `repro` stage that
measures it.

---

## 3. Test stages

The harness mirrors the compiler's stage vocabulary
(`BUILD_REFERENCE.md` §7.1) so that the eventual move to `npkg` is a change of
runner and not a change of suite.

| Stage | Directory | Passes when |
|---|---|---|
| `parse` | every `.npk` in the tree | accepted by `tools/parse_check` with no diagnostic |
| `accept` | `tests/conformance/` | accepted by `tools/check` in silence |
| `check` | `tests/rejection/` | refused by the frontend with **exactly** the expected codes |
| `program` | `tests/unit/` | emitted, scanned, assembled, linked, run at -O0 and again under `opt -O2`, the same exit both times |
| `corpus` | `tests/fixtures/` | every committed pattern/haystack/expectation triple gives the expected answer, **through every engine** |
| `oracle` | `tests/oracle/` | the naive reference matcher and each real engine agree, over a generated corpus |

**Rule B-5 — expectations live in the test file**, in the compiler's marker
grammar, marker for marker:

```
// expect-exit: 7            // expect-error: NITPICK-TYPE-046
// expect-error-at: 14:9     // stress: 40
```

**Rule B-6 — assert on codes and exit codes, never on message text.**

**Rule B-7 — unexpected diagnostics fail a test as surely as missing ones**
(D-237). The set of codes a rejection test reports must **equal** the set its
expectations name.

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
`hi` for a range's upper bound and for a `Match`'s end offset (`Match.end` is
refused, so the field is `hi` and the accessor is `match_end()`); `src` for an
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
  this is a request to be made, not a date to wait for. Tracked as O-N3.
- **O-B2 — whether `nregex` ships as source or as an object.** Source keeps the
  closed-world link and the whole-program verification story intact.
  **Settled for now in favour of source**; revisit only if build times become a
  real complaint.

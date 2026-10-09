# Cycle 0.2 — The HIR

**`src/hir/`: desugaring, normalisation, the computed properties, and literal
extraction.** Everything decidable without knowing which engine will run.

> **OPEN. [`0.2.0`](0.2.0.md), the arena, and [`0.2.1`](0.2.1.md), the desugaring, are DONE (2026-10-08), and
> [`0.2.1a`](0.2.1a.md), the adoption of compiler `7e91730`, is DONE (2026-10-09).** 0.2.0: RX-222 … RX-225 in seven work
> commits, `02bf6d7` … `35edbfe`, 283/283 in CI run 37817452049. 0.2.1: RX-226 … RX-229 in five work commits, `93e78a1` …
> `3fd81af` — a `pending-until:` marker that names a subcycle, a dump that shows every bit or stops, `hir_build` over H-5's
> table, and the two tests of what cycle 0.3.4 will build, pending until then; 294/294 at `5fbaf4a`, two pending outside
> the count, and in CI run 37858159348. 0.2.1a: RX-230 and RX-231 in four work commits, `90b7a3c` … `c160bb7` — every slice
> the tree holds the read-only view, `fixed uint8[]`, with `5fbaf4a` seeing no difference, then LLVM 20.1.8, one
> `NITPICK-TYPE-079` for a literal, probe 06b's return and CI at the new pin; 294/294 at `7e91730`, two pending outside the
> count, and in CI run 37931590622 — **next, 0.2.2, the repetition product, whose plan no file holds yet.** *(Until
> 0.2.1's record this banner named 0.2.0 alone as done, and 0.2.1 next; until 0.2.1a's plan, 0.2.2 next; until 0.2.1a's
> record, 0.2.1a next.)*

## Decisions in

RX-015, RX-031. Settled. **No open questions.**

## What cycle 0.1 hands on

*(2026-10-08, cycle 0.1's close — [`../done/0.1/0.1.6.md`](../done/0.1/0.1.6.md).)*

- **The AST the HIR is built from** — `SYNTAX.md` Y-26 and Y-27: a flat arena of sixteen kinds of 56-byte node that own
  nothing, every operand an `int64`, a node naming another by index; a class's items unresolved — a Perl class, a
  property, a POSIX class by name — for cycle 0.3 to resolve, so 0.2.1's desugaring carries them as they come. The parser
  builds the arena bottom-up on an explicit stack, and `check_no_recursion` reads `src/hir/` as it reads `src/syntax/`
  (`SAFETY.md` S-19). *(2026-10-08, cycle 0.2.1 — RX-228: "carries them as they come" is read as the build stopping at
  each, answering the node, until cycle 0.3.4 fills the hook that resolves it, and widens `leaf` for a bare one.)*
- **`RepeatProductTooLarge` is a row of `SYNTAX.md` Y-25's table naming 0.2.2**: the test that provokes it strikes the
  row in its own commit, or `check_error_kinds_tested` fails the run (RX-219).
- **Every refusal's offset lies inside the pattern** (Y-10's note, RX-221), and the HIR's refusals keep it;
  `tests/unit/parse_fuzz.npk` is the shape of a fuzz pass over a layer.
- **`regex_escape` is written**, and cycle 0.10.5 re-exports it from `src/lib.npk` (RX-211, RX-214).

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.2.0 | **The arena** — the nine kinds, the flat POD representation, the dump — **[`0.2.0.md`](0.2.0.md)**, written at cycle 0.1's close and measured at `5fbaf4a`, then rehearsed in its real position at `5fbaf4a` by cycle 0.2's planner, three records first — the author's words for `README.md`'s price paragraph, four decisions' first paragraphs freed from their notes' blockquotes, and `ROADMAP.md`'s cycle 0.1 sentence dated; PD-66 … PD-69 accepted as RX-222 … RX-225 — **DONE (2026-10-08)**, 283/283 *(until 0.2.0's record this row said "PD-66 … PD-69 are the orchestrator's to accept")* | a HIR that round-trips through its text form |
| 0.2.1 | **Desugaring** — `HIR.md` §3's table, exactly and nothing else — **[`0.2.1.md`](0.2.1.md)**, planned and rehearsed in its real position at `5fbaf4a` by cycle 0.2's planner, the instruments first — a `pending-until:` marker that names a subcycle, and a dump that shows every bit or stops — then the build and the two tests pending on it until cycle 0.3.4; PD-70 … PD-73 accepted as RX-226 … RX-229, with the orchestrator's correction made through the patches — the build stops in `leaf` too, before any hook — **DONE (2026-10-08)**, 294/294, two pending outside it *(until 0.2.1's record this row said "then the build and the two tests pending on its hooks; PD-70 … PD-73 are the orchestrator's to accept")* | every row tested; flags erased |
| 0.2.1a | **The adoption of compiler `7e91730`** — landing 103, the libraries' one re-pin: `fixed uint8[]`, the read-only view, in every slice the tree holds, the old compiler seeing no difference; then the pin's own moves — LLVM 20.1.8, the compiler's DEF-165 at one rejection header, probe 06b's return, `rx120.sh`, B-4e's re-read — and CI's three rows — **[`0.2.1a.md`](0.2.1a.md)**, planned and rehearsed in its real position at both pins by cycle 0.2's planner; PD-103 and PD-104 accepted as RX-230 and RX-231 — **DONE (2026-10-09)**, 294/294 at `7e91730`, two pending outside it *(until 0.2.1a's record this row said "PD-103 and PD-104 are the orchestrator's to accept")* | the unchanged tree measured at both pins; `294/294` at `7e91730` |
| 0.2.2 | **The repetition product** — the bound checked on the way down | `((a{1000}){1000}){1000}` refused at the third `{1000}` |
| 0.2.3 | **Normalisation** — flattening, merging, canonical form | structurally equal patterns produce identical dumps |
| 0.2.4 | **Computed properties** — the four flags in one bottom-up pass | each asserted against a hand-computed reference |
| 0.2.5 | **Literal extraction** — prefix, first-byte set, inner literal | conservative, bounded, and never wrong in the unsafe direction |
| 0.2.6 | **Close** — `check_hir_kinds_total` live | `done/0.2/`, `0.3.0.md` written |

## Checklist

### 0.2.0 — the arena
- [x] `HirNode` as a POD struct with no owning field; `#size_of` asserted — RX-223, **`2749ad1`**: `HirNode` derives `Copy` and owns nothing, and `check_vec_elements_own_nothing` clears `Vec<HirNode>`; `hir_size` exits with `#size_of<HirNode>()`, **40**, at −O0 and through `opt -O2`; `272/272`
- [x] `Literal` and `GroupInfo` shaped to own nothing — offsets into a `Bytes`, the way `Hir.names` holds group names — because a `Vec` holds a `T` that owns nothing (`SAFETY.md` S-23a, RX-155) and `check_vec_elements_own_nothing` fails the run otherwise. `HIR.md` §2 names both without fields; this cycle is where they get them — and each `#[derive(Copy)]`s, as every `Vec` element must since `Vec` is `Vec<T: Copy>` (cycle 0.1.1b, RX-188) *(2026-10-08, cycle 0.2.0 — RX-224: `GroupInfo` here, a name's offset and length in `Hir.names`; `Literal` is 0.2.5's, shaped with the extraction that fills it, and its checklist says so)* — RX-224, **`2749ad1`**: `GroupInfo` `{ int64:off; int64:len; }`, 16 bytes (`hir_unit` 69), deriving `Copy` and cleared by the check; group 0 the whole match with no name (`hir_unit` 50, 51), three groups' names held in `Hir.names` and copied out (52 … 58); `Literal` is 0.2.5's first box
- [x] children by `int32` index, never by pointer (H-3) *(2026-10-08, cycle 0.2.0 — RX-223: by `int64` index, the AST's width — an `int32` field would be narrowed unchecked at every write)* — RX-223, **`2749ad1`**: every child — a list's first member and each member's `next`, a `Repeat`'s or a `Group`'s body — is an `int64` index into `Hir.nodes`, which only `repr.npk` reads — `hir_get`, `hir_set` and `hir_push` over `vec_get`, `vec_set` and `vec_push`; `hir_oob_get` and `hir_oob_set_root` 94 at both legs, and `tests/rejection/hir_nodes_read.npk` `NITPICK-TYPE-080` at 23:16
- [x] names in one `Bytes`, referenced by offset and length — RX-224, **`2749ad1`**: `Hir.names`, each group's `GroupInfo` its name's offset and length there (`hir_unit` 53 … 58; `hir_dump` 35, 36)
- [x] the nine kinds from H-4 — RX-223, **`2749ad1`**: `HirKind` in H-4's order, held to it by `hir_unit`'s exhaustive `pick` (20), and H-4a for what each kind's operands hold; `hir_dump` writes and reads every one
- [x] a stable text dump and its parser, round-tripping — this is what makes a HIR a committed fixture — RX-225, H-15, **`ef40e9d`**: `hir_dump` and `hir_read`; `hir_dump` 0 at both legs — twenty-six texts read and written back byte for byte, twice, and thirty-three refusals each at its byte; `hir_dump_count` and `hir_dump_stray_next` 94, `hir_dump_not_a_tree` and `hir_dump_shared` 108; the thirty-three mutants each at its exit; `283/283`

### 0.2.1 — desugaring
- [x] every row of `HIR.md` §3's table, with a test each *(2026-10-08, cycle 0.2.0 — RX-223: the arena holds resolved ranges only (H-1, H-5), so a class's unresolved items — a Perl class, a property, a POSIX class by name — have no HIR form until cycle 0.3.4 resolves them; how the desugaring meets one, a hook 0.3.4 fills with a test that fails until then, as `(?i:…)`'s folding has, is this subcycle's to decide, and "carries them as they come" above is read against it)* — RX-228, H-16, **`3a5ee5e`**: `hir_build` 0 at both legs — H-5's six quantifier rows, their lazy forms and their bounds' edges (cases 1 … 9), the `.` row (10 … 14) and the `(?:…)` row (15 … 19) built, every other AST kind (30 … 49), classes and C-3's surrogates (50 … 58); the class row (20 … 23) and the `(?i:…)` row (24 … 27) stopping at the byte named, the root unset — RX-223's question answered so: the build stops at the node and answers it, at the hook `resolve_items` for a class's item, at `fold_ranges` for `i`, and in `leaf` for a bare Perl class, a bare property and a negated class (the orchestrator's correction, `0.2.1.md`'s record); and RX-229, **`2bb85cc`**: `tests/unit/hir_build_classes.npk` and `hir_build_fold.npk` assert what those two rows will build, each `PENDING until cycle 0.3.4` at exit 1, both legs; `hir_build_not_a_tree` 108, `hir_build_misnumbered` 94; the thirty-eight mutants each at its exit; `294/294`
- [x] **flags erased** (H-6): nothing downstream knows what `i`, `s`, `m`, `u` or `x` meant. A test greps the HIR dump for any flag residue — RX-227, **`2aa0545`**, and RX-228, **`3a5ee5e`**: the dump stops on a bit its node's kind does not take, so a dump that completes shows every bit (`hir_dump_stray_bit` 94 at both legs; the four mutants each at its exit); `hir_build`'s `words_ok` reads every token of every dump it builds against the words H-15 writes, a flag's letter none of them; cases 60 … 69 build eight pairs of patterns, a flag against none or against its other scope, to one text, and a `(?flags)` node in every place it may stand; the mutant `copy-ast-flags` stops the dump, 94
- [x] `(?i:…)` folds its classes at construction — the folding itself is 0.3's, so 0.2 leaves a hook and 0.3 fills it, with a test that fails until then — RX-228, **`3a5ee5e`**, and RX-229, **`2bb85cc`**: the hook is `fold_ranges` in `src/hir/build.npk`, false until cycle 0.3.4 fills it, so the build stops at every literal, class and `.` under `i` that reaches it (`hir_build` 24 … 27); the test is `tests/unit/hir_build_fold.npk`, `pending-until: 0.3.4 exit 1` (RX-226) with its line in `harness/baseline/PENDING.txt`, and the 0.3 README's last 0.3.4 box names it; the mutants `fold-hook-answers-true` and `literal-folded-skipped` move it to 10

### 0.2.1a — the adoption of compiler `7e91730`
- [x] the unchanged tree measured at both pins: `294/294` with two pending at `5fbaf4a`; at `7e91730` refused at the toolchain check, and with its LLVM rows moved red by landing 103's readers alone, each enumerated — blocks 0a and 0b `SAME`, before step 1: `294/294` at `5fbaf4a` in 205.4 s, both units `PEND`; at `7e91730` `FAIL  toolchain` before anything was built; with both LLVM rows moved `150/304`, its 154 failures 146 `NITPICK-TYPE-007` verdicts over 78 files, two `PENDING.txt` lines and six `RESIDUE.txt` entries; every `.npk` a root at both pins — 170 distinct `TYPE-007` sites in 39 files, five in `src/`
- [x] every slice the tree holds is `fixed uint8[]`, none written through, and the old compiler sees no difference — `294/294` at `5fbaf4a` (PD-103) — RX-230, **`90b7a3c`**: 133 slots in 32 files; the census at `5fbaf4a` the unchanged tree's in all 160 files; at `7e91730` one `TYPE-007` site, probe 06b's return, and probe 12b's `BORROW-009` back; the six view mutants at their verdicts, `writer` `TYPE-086` and `reassign` `ASSIGN-002` at `7e91730` and both compiling at `5fbaf4a`; `294/294` at `5fbaf4a` in 200.5 s
- [x] the pin moved: LLVM 20.1.8 in the manifest and in every tree the self-check builds, one `NITPICK-TYPE-079` in `pattern_error_literal.npk`, probe 06b's return, `rx120.sh` — `294/294` at `7e91730` (PD-104) — RX-231, **`864ae4c`**: probe 06b compiling at both pins; the literal one `TYPE-079` at 29:22 at `7e91730` and four at `5fbaf4a`; D-332's count agreeing for all 33 files at `7e91730`; each header passing at its own pin and failing at the other; `subview-return-plain` `TYPE-007` at `7e91730` alone; 21 of 31 live self-check cases NOT red with the self-check's manifest at 20.1.2, and the toolchain refusal with the tree's; every file at `7e91730` as the unchanged tree at `5fbaf4a` but the two headers' lines; `294/294` at `7e91730` in 203.7 s
- [x] B-4e's re-read, its verdict beside each reader's pin and in the record — RX-231, **`864ae4c`**: `lexer.npk`, `numeric.npk`, `parse_decl.npk` and `LEXICAL_REFERENCE.md` moved, for a float literal's scan and a refused integer literal kept a literal token; `p_parse_import` and `num_scan` the same at both pins, `escapes.npk` and `num_width.npk` unchanged; neither reader moves — `harness/lexical.py`'s docstring and `harness/treecheck.py`'s literal reader each dated at `7e91730`, B-4d and B-4e dated, and the verdict in `0.2.1a.md`'s record
- [x] CI pinned to `7e91730` — the commit, the emission's row and LLVM 20.1.8 — and its log read per job — **`ff7e1e6`**: the four rows equal to the compiler's commit, `PIN.md`'s row and the manifest's release, and the emission step exiting 1 on a fake and 0 on the fake's own row; CI run 37931590622 on `c160bb7` a success, job 113823372937's log (93 108 bytes) read: the compiler `7e91730` clean, LLVM 20.1.8, `npkc.ll` the pin's emission (31 527 001 B, `b79f89c5…`), rx120's legs held, `294/294`, `GREEN.`
- [x] the prose, and the sweep read line by line — **`c160bb7`**: `CLAUDE.md`, `README.md`, `ROADMAP.md` and `BUILD.md` §8a; `294/294` at `7e91730` in 205.4 s; block 5's 185 and 33 saved lines each read against §5b's classes, and none an omission

### 0.2.2 — the repetition product
- [ ] the product multiplied on the way down, in `uint64`, narrowed only where proven (RX-015) *(2026-10-08, cycle 0.2.1 — RX-228: `hir_build`'s walk enters a `Repeat` before its node and leaves it after, so a factor is known on the way down; the build answers an AST index, HIR_NONE when built, and the answer this subcycle's refusal needs is its to shape — `0.2.1.md` §7)*
- [ ] `NREGEX_REPEAT_MAX` on a single bound; `NREGEX_REPEAT_PRODUCT` on the nest *(2026-09-27, cycle 0.1.1: the single
  bound is the parser's since then — `RepeatTooLarge` at the number, RX-184 — so this subcycle's is the product)*
- [ ] `((a{1000}){1000}){1000}` refused **at the third `{1000}`**, with that offset — asserted, because refusing at the end is a different and worse behaviour *(2026-10-08 — cycle 0.1.6b, RX-219: as `RepeatProductTooLarge`, which `SYNTAX.md` Y-25's table lists for this subcycle; the test that provokes it strikes the row)* *(2026-10-08, cycle 0.2.0 — RX-223: a HIR node holds no position, so the offset is the AST node's being read when the product crosses the bound)*
- [ ] a test that the refusal happens before any large allocation, by bounding the process's peak memory

### 0.2.3 — normalisation
- [ ] concatenations flattened; adjacent literals merged into runs *(2026-10-08, cycle 0.2.1 — RX-228: the build leaves `a(?:bc)` a `Concat` in a `Concat` and a class's ranges in the order written, and an ASCII literal under `(?-u)` is `(literal byte 97)` where `a` is `(literal 97)`: whether those two are one HIR is this subcycle's — `0.2.1.md` §7)*
- [ ] alternations flattened and **not reordered** (order is semantic under RX-013)
- [ ] empty concatenations to `Empty`; single-codepoint classes to `Literal`
- [ ] class ranges sorted, adjacent and overlapping ranges merged
- [ ] **the gate**: a generated corpus of pattern pairs that are structurally equal but textually different produces byte-identical dumps
- [ ] a test asserting no normalisation changes which strings match, by running the oracle over both forms — **pending until 0.5**, and written now as a pending case *(2026-10-08, cycle 0.2.1 — RX-226: a unit can be pending on a subcycle of this library now, `// pending-until: 0.5.N exit E`, with its line in `harness/baseline/PENDING.txt`)*

### 0.2.4 — computed properties
- [ ] `CAN_MATCH_EMPTY`, `IS_ANCHORED_START`, `IS_ANCHORED_END`, `IS_ALTERNATION_LITERAL`
- [ ] computed in **one** bottom-up pass and cached (H-10) *(2026-10-08, cycle 0.2.1 — RX-227: the dump stops on a bit H-4a does not give a node's kind, so each bit this subcycle adds is refused there until it says how the dump shows it)*
- [ ] the query computes-or-returns; no caller remembers to compute first — D-227's precedent, and the compiler found four defects in that neighbourhood, none by a test of the thing that broke
- [ ] each flag asserted against a hand-computed reference over fifty patterns

### 0.2.5 — literal extraction
- [ ] `Literal` shaped to own nothing, `Hir.literals` added and the dump given its section for them — moved here from 0.2.0 by RX-224, because its fields depend on the three roles H-11 names
- [ ] required prefix, first-byte set, inner required literal
- [ ] bounded by `NREGEX_LITERAL_LIMIT` and `NREGEX_LITERAL_BYTES`
- [ ] **conservative**: a pattern that defeats the analysis gets an empty set, never a wrong one (H-12)
- [ ] a property test: for every corpus pattern and haystack, every position the real matcher finds is a position the first-byte set admits — **pending until 0.5**

### 0.2.6 — close
- [ ] `check_hir_kinds_total` live: every `HirKind` produced by the parser, consumed by the compiler (pending until 0.6) and handled by the oracle (pending until 0.5) *(2026-10-08, cycle 0.2.1 — RX-228: "produced by the parser" is `hir_build`'s now, and it produces all nine, each in `tests/unit/hir_build.npk`)*
- [ ] findings written; `0.3.0.md` written; archived

## Gate

Structurally equal patterns produce byte-identical HIR dumps, and the
repetition product refuses `((a{1000}){1000}){1000}` at the third `{1000}`
before the memory is requested.

## Watch for

- **H-14's line is the one that will be crossed.** Reordering an alternation or
  hoisting a common prefix *looks* like normalisation and changes which strings
  match under leftmost-first. The HIR is a canonical form, not an optimiser;
  optimisations belong in `compile/` where RX-041's off-switch can cross-check
  them.
- **The four computed properties are a memoisation**, and the compiler's D-227
  found four defects where a memoised fact was read before it was computed —
  because *absent* and *false* were spelled the same way. Use a distinct
  "not yet computed" state or compute-on-query; do not use `false`.
- **`limit` and `in` are keywords**; `bound` and `src`.

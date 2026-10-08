# Cycle 0.2 — The HIR

**`src/hir/`: desugaring, normalisation, the computed properties, and literal
extraction.** Everything decidable without knowing which engine will run.

> **OPEN. [`0.2.0`](0.2.0.md), the arena, is DONE (2026-10-08)** — RX-222 … RX-225 in seven work commits, `02bf6d7` …
> `35edbfe`: three records first, then `ClassRange` in `unicode`, the arena and the HIR as one line of text and back;
> 283/283 at `5fbaf4a` and in CI run 37817452049 — **next, 0.2.1, the desugaring, its file a planner's to write.**

## Decisions in

RX-015, RX-031. Settled. **No open questions.**

## What cycle 0.1 hands on

*(2026-10-08, cycle 0.1's close — [`../done/0.1/0.1.6.md`](../done/0.1/0.1.6.md).)*

- **The AST the HIR is built from** — `SYNTAX.md` Y-26 and Y-27: a flat arena of sixteen kinds of 56-byte node that own
  nothing, every operand an `int64`, a node naming another by index; a class's items unresolved — a Perl class, a
  property, a POSIX class by name — for cycle 0.3 to resolve, so 0.2.1's desugaring carries them as they come. The parser
  builds the arena bottom-up on an explicit stack, and `check_no_recursion` reads `src/hir/` as it reads `src/syntax/`
  (`SAFETY.md` S-19).
- **`RepeatProductTooLarge` is a row of `SYNTAX.md` Y-25's table naming 0.2.2**: the test that provokes it strikes the
  row in its own commit, or `check_error_kinds_tested` fails the run (RX-219).
- **Every refusal's offset lies inside the pattern** (Y-10's note, RX-221), and the HIR's refusals keep it;
  `tests/unit/parse_fuzz.npk` is the shape of a fuzz pass over a layer.
- **`regex_escape` is written**, and cycle 0.10.5 re-exports it from `src/lib.npk` (RX-211, RX-214).

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.2.0 | **The arena** — the nine kinds, the flat POD representation, the dump — **[`0.2.0.md`](0.2.0.md)**, written at cycle 0.1's close and measured at `5fbaf4a`, then rehearsed in its real position at `5fbaf4a` by cycle 0.2's planner, three records first — the author's words for `README.md`'s price paragraph, four decisions' first paragraphs freed from their notes' blockquotes, and `ROADMAP.md`'s cycle 0.1 sentence dated; PD-66 … PD-69 accepted as RX-222 … RX-225 — **DONE (2026-10-08)**, 283/283 *(until 0.2.0's record this row said "PD-66 … PD-69 are the orchestrator's to accept")* | a HIR that round-trips through its text form |
| 0.2.1 | **Desugaring** — `HIR.md` §3's table, exactly and nothing else | every row tested; flags erased |
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
- [ ] every row of `HIR.md` §3's table, with a test each *(2026-10-08, cycle 0.2.0 — RX-223: the arena holds resolved ranges only (H-1, H-5), so a class's unresolved items — a Perl class, a property, a POSIX class by name — have no HIR form until cycle 0.3.4 resolves them; how the desugaring meets one, a hook 0.3.4 fills with a test that fails until then, as `(?i:…)`'s folding has, is this subcycle's to decide, and "carries them as they come" above is read against it)*
- [ ] **flags erased** (H-6): nothing downstream knows what `i`, `s`, `m`, `u` or `x` meant. A test greps the HIR dump for any flag residue
- [ ] `(?i:…)` folds its classes at construction — the folding itself is 0.3's, so 0.2 leaves a hook and 0.3 fills it, with a test that fails until then

### 0.2.2 — the repetition product
- [ ] the product multiplied on the way down, in `uint64`, narrowed only where proven (RX-015)
- [ ] `NREGEX_REPEAT_MAX` on a single bound; `NREGEX_REPEAT_PRODUCT` on the nest *(2026-09-27, cycle 0.1.1: the single
  bound is the parser's since then — `RepeatTooLarge` at the number, RX-184 — so this subcycle's is the product)*
- [ ] `((a{1000}){1000}){1000}` refused **at the third `{1000}`**, with that offset — asserted, because refusing at the end is a different and worse behaviour *(2026-10-08 — cycle 0.1.6b, RX-219: as `RepeatProductTooLarge`, which `SYNTAX.md` Y-25's table lists for this subcycle; the test that provokes it strikes the row)* *(2026-10-08, cycle 0.2.0 — RX-223: a HIR node holds no position, so the offset is the AST node's being read when the product crosses the bound)*
- [ ] a test that the refusal happens before any large allocation, by bounding the process's peak memory

### 0.2.3 — normalisation
- [ ] concatenations flattened; adjacent literals merged into runs
- [ ] alternations flattened and **not reordered** (order is semantic under RX-013)
- [ ] empty concatenations to `Empty`; single-codepoint classes to `Literal`
- [ ] class ranges sorted, adjacent and overlapping ranges merged
- [ ] **the gate**: a generated corpus of pattern pairs that are structurally equal but textually different produces byte-identical dumps
- [ ] a test asserting no normalisation changes which strings match, by running the oracle over both forms — **pending until 0.5**, and written now as a pending case

### 0.2.4 — computed properties
- [ ] `CAN_MATCH_EMPTY`, `IS_ANCHORED_START`, `IS_ANCHORED_END`, `IS_ALTERNATION_LITERAL`
- [ ] computed in **one** bottom-up pass and cached (H-10)
- [ ] the query computes-or-returns; no caller remembers to compute first — D-227's precedent, and the compiler found four defects in that neighbourhood, none by a test of the thing that broke
- [ ] each flag asserted against a hand-computed reference over fifty patterns

### 0.2.5 — literal extraction
- [ ] `Literal` shaped to own nothing, `Hir.literals` added and the dump given its section for them — moved here from 0.2.0 by RX-224, because its fields depend on the three roles H-11 names
- [ ] required prefix, first-byte set, inner required literal
- [ ] bounded by `NREGEX_LITERAL_LIMIT` and `NREGEX_LITERAL_BYTES`
- [ ] **conservative**: a pattern that defeats the analysis gets an empty set, never a wrong one (H-12)
- [ ] a property test: for every corpus pattern and haystack, every position the real matcher finds is a position the first-byte set admits — **pending until 0.5**

### 0.2.6 — close
- [ ] `check_hir_kinds_total` live: every `HirKind` produced by the parser, consumed by the compiler (pending until 0.6) and handled by the oracle (pending until 0.5)
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

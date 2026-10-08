# The high-level intermediate

Between the parse tree and the program. Everything that can be decided without
knowing which engine will run is decided here, once.

---

## 1. Why a separate stage

**Rule H-1.** The AST records what the user wrote; the HIR records what it
means. The parser produces `[a-zA-Z_]` as a class with three items; the HIR
produces one sorted disjoint range list with the case folding already applied,
and every later stage sees only that.

Three things follow, and each is worth the stage:

- **The engines never see syntax.** A quantifier is a repetition node with a
  bound and a greediness bit, not a `*` or a `{2,5}`. Adding a spelling to
  `SYNTAX.md` never touches `compile/` or `engine/`.
- **Class arithmetic happens once**, at a point where the whole class is known.
  Case folding, negation, `&&`/`--`/`~~` and the Unicode property expansions
  all fold into one range list before anything asks what a character matches.
- **Literal extraction has a place to live** (§5). The prefilters need the
  literal prefixes of a pattern, and computing them from a syntax tree means
  re-deriving what the desugaring already knows.

---

## 2. The representation

**Rule H-2 — a flat POD arena, indexed by `int32`, not a pointer tree.**

```nitpick
pub struct:HirNode = {
    HirKind:kind;
    int32:a;         // kind-specific: first child, class index, group number
    int32:b;         // kind-specific: second child, repetition minimum
    int32:c;         // kind-specific: sibling, repetition maximum
    uint32:flags;    // greedy, can-match-empty, is-anchored, …  §4
};

pub struct:Hir = {
    Vec<HirNode>:nodes;
    Vec<ClassRange>:ranges;   // every class's ranges, contiguous per class
    Vec<Literal>:literals;    // §5
    Bytes:names;              // group names, one after another
    Vec<GroupInfo>:groups;
    int32:root;
};
```

**No node declares an owning field**, so `HirNode` is copyable, storable in an
array, and comparable — which is what makes the whole tree a fixture a test can
commit (`TESTING.md` §4). Names live in one `Bytes` and are referenced by
offset and length.
*(2026-09-28, cycle 0.1.1b — RX-188: and every element type of `Hir`'s `Vec`s —
`HirNode`, `ClassRange`, `Literal`, `GroupInfo` — `#[derive(Copy)]`s, with every enum it
holds: `Vec` is `Vec<T: Copy>`, and a struct of scalars that does not say so is
`NITPICK-TYPE-017` at its `Vec`, measured at `5fbaf4a`.)*
*(2026-10-08, cycle 0.2.0 — RX-223, RX-224: the node `src/hir/repr.npk` declares is not the one drawn. Its operands are
`int64`, as the AST's (`SYNTAX.md` Y-26), because each comes from an `int64` and an `int32` field would be narrowed
unchecked at every write; and it has a fourth, `next`, the sibling a list needs, which three operands cannot hold beside
a `Repeat`'s child, minimum and maximum — **40 bytes**, measured (`tests/unit/hir_size.npk`), where the drawing
measures 20 at `5fbaf4a`. It holds no position, because structurally equal patterns are literally equal (H-13). H-4a
says what each kind's operands hold. `Hir`'s fields are `hidden` but `root`, which is `sealed` and an `int64`, so every
access goes through `repr.npk`'s accessors. `Hir` holds no `literals` until cycle 0.2.5, which shapes `Literal` with
the extraction that fills it; `groups[k]` is group `k`, group 0 the whole match with no name (`COMPILE.md` C-16), each
a `GroupInfo` — its name's offset and length in `names`.)*

**Rule H-3 — children are found by index, never by pointer.** The language
would allow a pointer tree, and it would be worse: a `Vec<HirNode>` reallocates
on growth and every pointer into it would dangle, whereas an index survives.
This is the same reasoning the compiler applies to `Handle<T>` (D-017).

**Rule H-4 — the kinds are a closed list.** `Empty`, `Literal` (one codepoint),
`Class`, `Concat`, `Alternate`, `Repeat`, `Group`, `Anchor`, `WordBoundary`.
Nine. A tree check asserts every kind is produced by the parser, consumed by
the compiler, and handled by the oracle.
*(2026-10-08, cycle 0.2.0 — RX-223: a `Literal` is one codepoint, or under `(?-u)` one byte, `HIR_FLAG_BYTE` set
(`SYNTAX.md` Y-13; the modes mix in one pattern, `UNICODE.md` U-19); a `Class` and a `WordBoundary` the same. Still
nine kinds.)*

**Rule H-4a — each kind's operands** (RX-223):

| Kind | `a` | `b` | `c` | Bit |
|---|---|---|---|---|
| `Empty` | | | | |
| `Literal` | its codepoint; a byte under `BYTE` | | | `HIR_FLAG_BYTE` |
| `Class` | its first range's index in `ranges` | how many ranges | | `HIR_FLAG_BYTE`: the ranges are bytes |
| `Concat` | the first piece | how many | | |
| `Alternate` | the first alternative | how many | | |
| `Repeat` | the repeated node | the minimum | the maximum; `HIR_NONE` if unbounded | `HIR_FLAG_LAZY` |
| `Group` | the body | its group number, from 1 | | |
| `Anchor` | `HIR_TEXT_START` 0, `HIR_TEXT_END` 1, `HIR_LINE_START` 2, `HIR_LINE_END` 3 | | | |
| `WordBoundary` | `HIR_WORD` 0, `HIR_NOT_WORD` 1 | | | `HIR_FLAG_BYTE`: a word character is ASCII's |

A list's members — a `Concat`'s pieces, an `Alternate`'s alternatives — are its first member and each member's `next`,
`b` of them, in the order written; a node in no list — the root, a `Repeat`'s or a `Group`'s child — has `next`
`HIR_NONE`. `flags` holds the two bits above, and cycle 0.2.4's computed properties (H-9) take others. No pattern flag
survives (H-6): `m` is an `Anchor`'s value, `s` a `.`'s class, `i` folded ranges, `x` the parser's, and `u` is
`HIR_FLAG_BYTE`, which says what a node matches.

---

## 3. Desugaring

**Rule H-5 — every rewrite is listed, and nothing else happens.**

| Written | Becomes |
|---|---|
| `a?` | `Repeat{min: 0, max: 1}` |
| `a*` | `Repeat{min: 0, max: ∞}` |
| `a+` | `Repeat{min: 1, max: ∞}` |
| `a{n}` | `Repeat{min: n, max: n}` |
| `a{n,}` | `Repeat{min: n, max: ∞}` |
| `a{n,m}` | `Repeat{min: n, max: m}` |
| `\d`, `\w`, `\s`, POSIX, `\p{…}` | `Class` with the ranges resolved |
| `.` | `Class` — all codepoints, less `\n` unless `s` |
| `(?:…)` | the inner node, with no `Group` wrapper |
| `(?i:…)` | the inner tree, with folding **already applied to its classes** |

*(2026-10-08, cycle 0.2.1 — RX-228: H-16 says how each kind of AST node meets this table. The quantifiers are a `Repeat`
in the AST already (`SYNTAX.md` Y-32); `\d`, `\w`, `\s`, POSIX, `\p{…}` and `(?i:…)` are where the build stops until
cycle 0.3.4 fills its two hooks and widens its `leaf`.)*

**Rule H-6 — flags are erased.** Nothing downstream of the HIR knows what `i`,
`s`, `m`, `u` or `x` meant. Case-insensitivity is folded ranges;
multi-line is a different `Anchor` kind; `s` is a different `.` class; `x` is
consumed by the parser. **A flag that survived into the program would be a
runtime branch, and a runtime branch on a compile-time fact is what
monomorphisation exists to remove.**

**Rule H-7 — repetition is *not* expanded here.** `a{500}` stays a `Repeat`
node in the HIR and becomes 500 instructions in `compile/`. The HIR is
proportional to the pattern text; only the program is proportional to the
expansion. This keeps HIR fixtures small and keeps `NREGEX_REPEAT_PRODUCT`
(`SAFETY.md` §5.1) checkable on a small structure.

**Rule H-8 — the repetition product is checked as the HIR is built**, by
multiplying the enclosing factors on the way down. `((a{1000}){1000}){1000}` is
refused at the third `{1000}`, before a billion instructions are requested.

**Rule H-16 — the build** (RX-228). `hir_build(uint8[]:pat, Ast:t, Hir->:out) -> int64` builds the HIR of a pattern
from its AST (`SYNTAX.md` Y-26, Y-27) into a `Hir` fresh from `hir_init`, each kind of AST node as this table says and
nothing else (H-5) — nothing flattened, merged, sorted or reordered, which is cycle 0.2.3's (H-13), and nothing
expanded (H-7):

| AST node | HIR |
|---|---|
| `Empty` | `Empty` |
| `Literal` | `Literal`: its codepoint, or under `AST_FLAG_BYTE` its byte with `HIR_FLAG_BYTE` |
| `Dot` | `Class`: every codepoint but `\n`, every one under `s` — the surrogates left out (`COMPILE.md` C-3) — or under `(?-u)` every byte but `\n`, every one under `s`, with `HIR_FLAG_BYTE` |
| `Concat` | `Concat` of its pieces in order, a `Flags` piece left out — `Empty` when no piece is left, the piece itself when one is (`SYNTAX.md` Y-33's rule, after the erasure) |
| `Alternate` | `Alternate` of its alternatives in order, a `Flags` alternative an `Empty` |
| `Repeat` | `Repeat`: its node, its minimum and its maximum as written, `HIR_FLAG_LAZY` when lazy |
| `Group` that captures | `Group`: its body, its number, its name copied into `Hir.names` |
| `Group` that captures nothing — `(?:…)`, `(?flags:…)` | its body; a `Flags` body an `Empty` |
| `Flags` — `(?flags)` | nothing: its effect is in the flags of the nodes after it (Y-41) |
| `Anchor` | `^` `HIR_TEXT_START`, under `m` `HIR_LINE_START`; `$` `HIR_TEXT_END`, under `m` `HIR_LINE_END`; `\A` `HIR_TEXT_START` and `\z` `HIR_TEXT_END` always |
| `WordBoundary` | `WordBoundary`, `HIR_NOT_WORD` for `\B`; under `(?-u)` `HIR_FLAG_BYTE` |
| `Class` | `Class` of its members' ranges in the order written, a nested class's in its place, each less the surrogates in Unicode mode (C-3); under `(?-u)` `HIR_FLAG_BYTE` |

A node's flags in force are read for what it means and never copied (H-6). **The build stops** at the first node, in
the order the pattern writes them, whose meaning needs what cycle 0.3.4 builds, and answers its index in the AST with
`out`'s root unset — never a HIR that means something else: a `PerlClass` or a `UnicodeClass`; a `Class` that is
negated or holds a `PerlClass`, a `PosixClass`, a `UnicodeClass`, a `ClassOp` or a negated class, at the outermost
`Class`; and under `i` a `Literal`, a `Class` or a `Dot`, which `i` folds (`UNICODE.md` U-11, U-13). Its two hooks,
`resolve_items` and `fold_ranges` in `src/hir/build.npk`, are where cycle 0.3.4 resolves and folds. Otherwise it answers
`HIR_NONE` with the root set, and **the arena holds the tree and nothing else**: a node is pushed when the node holding
it is built, so every node is reached from the root once, and H-15's bound is exact for every HIR the build answers
`HIR_NONE` for. Groups are added to `Hir.groups` as the walk enters them, the order their `(` is written (Y-6), and
each must be the AST's number or the build stops `OutOfBounds`; an AST that is not a tree stops it
`DecreasesViolated`. The walk is an explicit stack bounded by twice the arena (`SAFETY.md` S-19).
`tests/unit/hir_build.npk` holds every row, and two units more each trap.
*(2026-10-08, cycle 0.2.1 — RX-229: and two are pending until cycle 0.3.4, on the build's stop at a hook or in `leaf`:
`tests/unit/hir_build_classes.npk`, the class row's HIRs and a class's negation and operators, and
`hir_build_fold.npk`, the `(?i:…)` row's.)*

---

## 4. Computed properties

**Rule H-9 — four facts are computed bottom-up for every node and cached in
`flags`**, because every one of them is asked repeatedly by later stages and
each is a whole-subtree walk:

| Flag | Meaning | Used by |
|---|---|---|
| `CAN_MATCH_EMPTY` | the subtree matches the empty string | `SYNTAX.md` Y-21's iterator rule; the one-pass engine's eligibility |
| `IS_ANCHORED_START` | every match begins at the haystack start | the meta-engine — an anchored search skips the scan loop |
| `IS_ANCHORED_END` | every match ends at the haystack end | reverse search |
| `IS_ALTERNATION_LITERAL` | the subtree is a union of plain literals | the Aho-Corasick-style prefilter |

**Rule H-10 — these are computed once, in one bottom-up pass, and never
recomputed.** The compiler's D-227 is the precedent and the reason: a memoised
fact that is read before it is computed is a defect that presents as something
else entirely, and the answer is that the query computes-or-returns rather than
the caller remembering to.

---

## 5. Literal extraction

**Rule H-11.** The prefilters (`ENGINES.md` §6) need, for a pattern:

- the **required literal prefix**, if every match starts with the same bytes;
- the **set of possible first bytes**, always computable;
- an **inner required literal**, if some literal must appear in every match.

All three are computed here, bounded by `NREGEX_LITERAL_LIMIT` entries and
`NREGEX_LITERAL_BYTES` each, and all three are **hints**: an engine may ignore
them and must produce the same answer either way (`ENGINES.md` R-3).

**Rule H-12 — extraction is conservative and its failure mode is "no
literals".** A pattern whose structure defeats the analysis gets an empty
literal set and a slower search, never a wrong one. There is no case where a
missed literal is a correctness problem, which is what makes this analysis safe
to improve later without re-verifying the engines.

---

## 6. Normalisation

**Rule H-13 — the HIR is normalised so that structurally equal patterns are
literally equal**, which is what lets a fixture be a committed HIR dump and a
test be a byte comparison:

- concatenations are flattened (`Concat[Concat[a,b],c]` → `Concat[a,b,c]`);
- adjacent literals in a concatenation are merged into one literal run;
- alternations are flattened, and **not reordered** — order is semantic under
  leftmost-first (`SYNTAX.md` Y-3);
- empty concatenations become `Empty`;
- a class with one single-codepoint range becomes a `Literal`;
- class ranges are sorted and adjacent or overlapping ranges are merged.

**Rule H-14 — nothing that changes which strings match is a normalisation.**
Reordering an alternation, hoisting a common prefix, or eliminating a `Repeat`
with `min == max == 1` around a group would each be an optimisation, and each
is refused here: the HIR is a canonical form, not an optimiser. Optimisations
belong in `compile/` where they can be turned off and cross-checked.

**Rule H-15 — the HIR as text** (RX-225). `hir_dump` writes the tree under the root as one line, each node `(` its
kind's name, its words, its operands and its children `)`:

```text
(empty)
(literal CP)             (literal byte B)
(class LO-HI ...)        (class byte LO-HI ...)
(concat NODE ...)        (alternate NODE ...)
(repeat MIN MAX NODE)    (repeat lazy MIN MAX NODE)      MAX is - when unbounded
(group K NODE)           (group K NAME NODE)
(anchor text-start)      text-end, line-start, line-end
(wordboundary)           (wordboundary not), (wordboundary byte), (wordboundary byte not)
```

One spelling per HIR: one space between tokens, none after `(` or before `)`, a number in decimal with no leading zero
and at most eighteen digits, no line end. `hir_read` reads exactly that, and refuses everything else with the offset of
the first byte that is not what `hir_dump` writes there, so `hir_dump(hir_read(t))` is `t`. It holds a text to: a
codepoint below U+110000 and a byte at most 255; a range's `lo` at most its `hi`; a minimum at most its maximum; one
child for a `repeat` and a `group`, none for a leaf; and each `group` numbered as `SYNTAX.md` Y-6 numbers it, from 1 in
the order the groups open. It does not hold what a builder must — `COMPILE.md` C-3's surrogates, Y-8's names, cycle
0.2.3's order — and `hir_dump` stops on an arena it cannot write truthfully: a list's count that is not its chain's
length, and a `next` on a node in no list (`OutOfBounds`); and a walk longer than twice the arena (`DecreasesViolated`),
which stops a node that wraps itself, and a node with two parents when every node hangs from the root. Beside a node
nothing reaches, the walk's bound has room, and a shared node is written once for each parent: a builder builds a tree.
`tests/unit/hir_dump.npk` holds both directions, and four units more each trap.
*(2026-10-08, cycle 0.2.1 — RX-227: and the writer stops on a node whose `flags` hold a bit its kind does not take — H-4a's
Bit column, `byte` on a `literal`, a `class` and a `wordboundary`, `lazy` on a `repeat` — `OutOfBounds`, so a dump that
completes shows every bit its nodes hold and a dump compared with its expected text is a test of H-6. Five units trap
now: `hir_dump_stray_bit.npk` is the fifth. A bit cycle 0.2.4 adds (H-9) is one this check refuses until that cycle
says how the dump shows it.)*
*(2026-10-08, cycle 0.2.1 — RX-228: and `hir_build` builds one — every node it pushes is reached from the root once
(H-16) — so the walk's bound is exact for every HIR it answers `HIR_NONE` for.)*

---

## 7. Open items

- **O-H1 — whether to compute a "reverse literal suffix" for reverse
  searching.** Only useful once a reverse engine exists (finding a match's
  start after a forward DFA found its end). Recommendation: deferred to cycle
  0.8 where the reverse DFA is decided.

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

---

## 7. Open items

- **O-H1 — whether to compute a "reverse literal suffix" for reverse
  searching.** Only useful once a reverse engine exists (finding a match's
  start after a forward DFA found its end). Recommendation: deferred to cycle
  0.8 where the reverse DFA is decided.

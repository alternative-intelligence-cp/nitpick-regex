# `src/hir/` — the high-level intermediate

What a pattern means, decided once, without knowing which engine will run:
desugaring, normalisation, the computed properties and literal extraction,
over a flat POD arena of nine kinds of node. Governed by
`meta/specs/HIR.md`. Built in cycle 0.2.

A repetition stays one `Repeat` node here, its bounds as written (`HIR.md`
H-7): `a{500}` becomes 500 instructions in `compile/`, never in the HIR, so a
HIR is proportional to its pattern. *(Until 2026-10-08, cycle 0.2.0, this
file said "repetitions expanded under a bound", which is `compile/`'s, not
this layer's.)*

| File | Holds | Since |
|---|---|---|
| `hir.npk` | the layer's entry: one `pub use` per name it offers | 0.2.0 |
| `repr.npk` | the arena — `HirKind`, `HirNode`, `GroupInfo`, `Hir` — and its accessors (H-2 … H-4a) | 0.2.0 |
| `dump.npk` | the HIR as one line of text, and back (H-15) | 0.2.0 |
| `build.npk` | the desugaring: a pattern's AST to a HIR, and the two hooks cycle 0.3.4 fills (H-5, H-6, H-16); the repetition product, refused on the way down, and its `PatternError` (H-8) | 0.2.1; 0.2.2 |

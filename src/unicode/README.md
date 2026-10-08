# `src/unicode/` — generated Unicode tables

Property, script, class and simple-case-folding tables, **generated** from a
pinned UCD by `tools/gen_unicode.py` and committed as source, so a build needs
the compiler and nothing else. Governed by `meta/specs/UNICODE.md`. Built in
cycle 0.3.

Two modules are written by hand, before the tables: `class_range.npk`,
`UNICODE.md` U-4's `ClassRange` — one range of codepoints, or of bytes — which
a HIR's classes hold (`HIR.md` H-2) and every table will (cycle 0.2.0); and
`unicode.npk`, the layer's entry, which re-exports it.

# `src/syntax/` — the pattern parser

Pattern text to an AST, driven by an **explicit stack** so that a deeply nested
pattern is a refusal and never a blown call stack. Every error carries a byte
offset into the pattern. Governed by `meta/specs/SYNTAX.md`. Built in cycle
0.1.

# `src/syntax/` — the pattern parser

Pattern text to an AST, driven by an **explicit stack** so that a deeply nested
pattern is a refusal and never a blown call stack. Every error carries a byte
offset into the pattern. Governed by `meta/specs/SYNTAX.md`. Built in cycle
0.1.

Since cycle 0.1.0 it holds the pieces every later subcycle is written in, and
parses no construct yet:

| File | What |
|---|---|
| `syntax.npk` | the layer entry: every name the layer offers, `pub use`, one per line |
| `pattern_error.npk` | `PatternErrorKind` (`SYNTAX.md` §9), `PatternError` (`SAFETY.md` S-9), and `pattern_error`, the only way to build one — RX-172 |
| `cursor.npk` | the byte cursor: one byte of lookahead, moved by nothing outside it — RX-173 |
| `ast.npk` | the AST arena: sixteen kinds of 56-byte node that own nothing (`SYNTAX.md` Y-26, Y-27) — RX-174 |
| `parse.npk` | the parser's entry: at 0.1.0 only its first refusal, `parse_check_length` — RX-175 |

`tests/unit/syntax_skeleton.npk` composes them through `syntax.npk` alone.

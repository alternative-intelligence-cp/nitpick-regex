# `src/syntax/` — the pattern parser

Pattern text to an AST, driven by an **explicit stack** so that a deeply nested
pattern is a refusal and never a blown call stack. Every error carries a byte
offset into the pattern. Governed by `meta/specs/SYNTAX.md`. Built in cycle
0.1.

Since cycle 0.1.0 it holds the pieces every later subcycle is written in, and
since cycle 0.1.1 it parses the core grammar — literals, `.`, `^`, `$`, groups,
alternation and quantifiers (`SYNTAX.md` Y-28 … Y-33) — and says what each
refusal means (Y-34). Since cycle 0.1.2 its stack is bounded: a `(` that would nest
groups past `NREGEX_NEST_DEPTH` is `NestTooDeep` at it, before a byte after it is read
(Y-35). Since cycle 0.1.3 it parses classes — members, ranges, nested classes and the
operators, Perl classes, properties and POSIX classes, unresolved (Y-36 … Y-38) — and
groups and classes nest at most `NREGEX_NEST_DEPTH` deep together. Since cycle 0.1.4 it reads
every escape, in a class and out (Y-40), and the flags — groups of them, `x` and `(?-u)`
(Y-41 … Y-43); only §8's escapes are refused provisionally, until cycle 0.1.5 (Y-30, Y-31):

| File | What |
|---|---|
| `syntax.npk` | the layer entry: every name the layer offers, `pub use`, one per line |
| `pattern_error.npk` | `PatternErrorKind` (`SYNTAX.md` §9), `PatternError` (`SAFETY.md` S-9), and `pattern_error`, the only way to build one — RX-172; `pattern_error_text`, what is wrong, at which byte, and what to write instead — RX-187; `posix_class_name`, §5.1's fourteen names in one place — RX-197; and `NOT_A_CODEPOINT`, the detail no codepoint takes — RX-203 |
| `cursor.npk` | the byte cursor: one byte of lookahead, moved by nothing outside it — RX-173 |
| `ast.npk` | the AST arena: sixteen kinds of 56-byte node that own nothing (`SYNTAX.md` Y-26, Y-27) — RX-174 |
| `parse.npk` | the parser: `parse_check_length`, the first refusal — RX-175; `parse_check_encoding`, the pattern checked whole as UTF-8 — RX-183; and `parse_pattern`, one explicit-stack walk that builds the AST — RX-182, RX-184 … RX-186 — its stack bounded at the `(`, RX-193; a class read by `parse_class`'s own `while` on a stack of its own — RX-197, RX-199, RX-200 — bounded with the groups', RX-198; every escape read by `escape_cp`, in a class and out — RX-204, RX-205; and the flags by `read_flags`, with `x` and `(?-u)` — RX-206 … RX-208 |

`tests/unit/syntax_skeleton.npk` composes the pieces through `syntax.npk` alone,
and `parse_grammar`, `parse_refusals`, `parse_encoding`, `parse_limits` and
`pattern_error_text` hold the parse and its text to the specification the same
way; `parse_nest_deep` holds the bound at 10 000 levels and at the longest pattern,
forty runs a leg (RX-194); `parse_classes` and `parse_class_refusals` hold every
class shape and every class refusal (RX-197); and `parse_escapes`, `parse_escape_refusals`,
`parse_flags` and `parse_flag_refusals` hold every escape, every flag, and each refusal of
either (RX-203 … RX-208).

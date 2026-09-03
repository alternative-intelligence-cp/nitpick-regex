# Glossary

One word per concept, one concept per word. Where the regex world uses a word
two ways, this says which one `nregex` means.

| Term | Means, in `nregex` |
|---|---|
| **pattern** | the source text a user writes. Never "regex", which is the compiled value. |
| **`Regex`** | the compiled, immutable program. Never the pattern text. |
| **haystack** | the bytes being searched. Never "input", which is ambiguous with the pattern. |
| **`Cache`** | the caller-owned mutable scratch a search needs. Never "state". |
| **program** | the compiled instruction array. |
| **instruction** | one entry in the program. Never "opcode", which names only its kind. |
| **thread** | one program counter in the Pike VM's set. **Not an OS thread**, and never one — the word is the literature's and is kept because every reference uses it. |
| **engine** | one way of running a program. Pike VM, DFA, one-pass, backtracker. |
| **prefilter** | something that finds candidate positions faster than an engine, and never decides a match. |
| **class** | a set of codepoints, or of bytes after compilation. Never "character class" in prose, because the unit is not a character. |
| **range** | one `lo`–`hi` pair inside a class. |
| **fold** | simple Unicode case folding. Never "lowercase", which is a different operation. |
| **capture** | a numbered or named subexpression, and the offsets it recorded. |
| **slot** | one `int64` of capture storage. Two slots per group. |
| **match** | a `lo`/`hi` offset pair. Never a substring. |
| **anchored** | a search that must match at its start offset. Never "rooted". |
| **leftmost-first** | the semantics (`SYNTAX.md` Y-3). Never "greedy", which is a quantifier property. |
| **step** | one unit of engine work, counted for the linear-time property test. |
| **the oracle** | the naive reference matcher in `tests/oracle/`. |
| **the budget** | the one public error identity, and the rule that there is one. |
| **arm** | one `pick` case in a consuming program's `failsafe`. |

## Words deliberately not used

| Not used | Because |
|---|---|
| "regex" for the pattern text | the pattern is text, the `Regex` is compiled; conflating them is how "recompiling in a loop" gets written |
| "string" for the haystack | a haystack is `uint8[]` and need not be text |
| "character" | ambiguous between byte and codepoint, which is the ambiguity `UNICODE.md` exists to be careful about |
| "backtracking" for the Pike VM | it does not backtrack; it advances a set. Using the word invites the wrong performance model |
| "NFA" and "DFA" interchangeably | the program is an NFA; the DFA is one engine over it |
| "compile" for what an engine does | compilation produces the program; an engine runs it |
| "fail" for no match | a search cannot fail (`SAFETY.md` S-4). No match is an answer |

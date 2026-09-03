# Compatibility

How `nregex`'s accepted syntax compares to the engines a user is likely coming
from. An honest difference list, because "PCRE-compatible" is a claim no engine
keeps and the way a user finds out is in production.

---

## 1. The families

| Engine | Model | Backrefs / lookaround | Semantics |
|---|---|---|---|
| **`nregex`** | automata | **no** | leftmost-first |
| RE2 | automata | no | leftmost-first (POSIX mode available) |
| Rust `regex` | automata | no | leftmost-first |
| Go `regexp` | automata (RE2) | no | leftmost-first |
| PCRE / Perl / Python / Java / JS / .NET | backtracking | yes | leftmost-first |
| POSIX ERE (`grep -E`) | varies | backrefs in BRE | leftmost-**longest** |

**`nregex` sits with RE2, Rust and Go.** A pattern that works in Rust's `regex`
is the closest thing to a pattern that works here, and where the two differ it
is listed in §2.

---

## 2. Differences from Rust's `regex`

The closest neighbour, so the list is short and each entry is deliberate.

| | Rust `regex` | `nregex` | Why |
|---|---|---|---|
| named groups | `(?P<n>…)` **and** `(?<n>…)` | `(?<n>…)` only | one spelling per construct (`SYNTAX.md` Y-7) |
| `\Q…\E` | not supported | refused, naming `regex_escape()` | same, with a better message |
| Unicode blocks | not supported | refused, naming `Script` | `UNICODE.md` §2.1 |
| case folding | simple | simple | same |
| `x` mode inside classes | whitespace significant | whitespace significant | same (O-Y2) |
| replacement | closures **or** templates | templates and non-capturing function values | no closures (D-018) |
| `Match` | a `&str` slice | byte offsets | borrows never pass up (D-004) |
| DFA cache | pooled internally | an explicit `Cache` the caller owns | `ENGINES.md` §5 |
| `RegexSet` | yes | format supports it, API at 1.1 | `COMPILE.md` §6 |
| multi-pattern | yes | 1.1 | same |

---

## 3. Differences from PCRE and Perl

The list a user migrating from Python, PHP, Java or JavaScript needs.

| Construct | `nregex` |
|---|---|
| `\1`, `\k<name>` — backreferences | **refused** — `SAFETY.md` §2 |
| `(?=…)`, `(?!…)`, `(?<=…)`, `(?<!…)` — lookaround | **refused** — same |
| `(?>…)`, `a*+` — atomic / possessive | **refused** — meaningless under an automaton |
| `(?R)`, `(?1)` — recursion | **refused** — not regular |
| `\Z` | refused, naming `\n?\z` |
| `$` before a trailing newline | **does not match** unless `m` — `SYNTAX.md` Y-19 |
| `\G` | refused; `regex_find_at` is the mechanism |
| `(?#…)` comments | refused; `x` mode's `#` is the spelling |
| `\p{InGreek}` | refused, naming `\p{Script=Greek}` |
| case folding of `ß`, `ﬁ` | **simple folding only** — `UNICODE.md` U-12 |
| `\w` | UTS #18 Annex C, not `[A-Za-z0-9_]` — `UNICODE.md` U-10 |

**Rule K-1 — every refusal names the alternative in its message**, and where
there is none it names the reason. `LookaroundUnsupported` says the pattern
cannot be matched in linear time, not "unsupported".

---

## 4. When `nregex` is the wrong tool

Stated plainly, because a library that pretends to cover everything sends
somebody down a bad path.

**A pattern needing backreferences or lookaround is not a regular expression**,
and no amount of engine work makes it one in linear time. What to use instead:

- **balanced delimiters, nesting, recursive structure** — `nitpick-parse`. That
  is what a parser is; a regex that appears to do it is matching a bounded
  approximation.
- **"this, but not if preceded by that"** — usually expressible by matching the
  larger construct and inspecting the captures, which is linear and clearer.
- **"the same text twice"** — match once and compare, which is what a
  backreference does anyway, at the cost of the guarantee.

**Rule K-2 — the documentation says this on the same page as the refusal**, not
in a corner. A user who hits `BackreferenceUnsupported` should reach the answer
in one click.

---

## 5. Portability

**Rule K-3 (RX-008) — `nregex` is target-independent.** No syscall, no endianness
assumption in any committed table, no pointer-width assumption in a serialised
form. Only the Python harness is Linux-specific, and only because it drives
`llc` and `ld.lld`.

Stated because it is unusual in this ecosystem: `nitpick-tui` and
`nitpick-sockets` are Linux-on-x86-64 by construction, and `nregex` is not. A
future `aarch64` or bare-metal target needs nothing from this library but a
recompile.

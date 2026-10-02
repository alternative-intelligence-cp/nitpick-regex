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
| `regex::escape` / `regex_escape()` | a `\` before eighteen bytes, white space left bare, so `(?x)` skips it | the same eighteen and the six white-space bytes, and white space past ASCII as `\x{…}` | the text means itself under `x` too (`SYNTAX.md` Y-45) — RX-211 |
| Unicode blocks | not supported | refused, naming `Script` | `UNICODE.md` §2.1 |
| case folding | simple | simple | same |
| `x` mode inside classes | ~~whitespace significant~~ white space and `#` comments ignored (measured, regex 1.13.1) | ~~whitespace significant~~ a white-space byte or a `#` refused (`SYNTAX.md` Y-39) | ~~same (O-Y2)~~ the engines disagree, so neither reading is guessed — RX-201, 2026-10-01; this row said Rust kept white space, and it does not |
| a POSIX class as a whole class, `[:alpha:]` | a class of `:`, `a`, `h`, `l`, `p` | refused, saying a POSIX class goes inside a class — as GNU `grep` refuses it | a class of five bytes where every letter was meant — RX-200 |
| a class's edge cases | an operator with an empty side is the empty set (`[a&&]`, `[!--]`), and a run of `-` first in a class is members (`[--a]`); `[:` that opens no POSIX class opens a nested class (`[[:alpah:]]`); a `-` after `[…]` or `[:name:]` is a member, and a `[` ending a range is a codepoint | each refused, with the kind and the fix `SYNTAX.md` Y-36 and Y-38 name | a reading the author may not have meant is a refusal that says what to write — RX-197 |
| `\e`, `\0` | refused | U+001B and U+0000, as in Perl, PCRE and Python | §1 names them; accepting what Rust refuses changes no pattern Rust accepts — RX-204 |
| `\u{41}`, `\U{1F600}` | a codepoint | refused, naming `\x{…}` | one spelling for a codepoint in braces (`SYNTAX.md` Y-40) — RX-204 |
| `\<`, `\>` | the start and the end of a word | refused, naming `\b`, and `<` or `>` for the byte | Rust and GNU `grep` read a word assertion, Perl, PCRE, Python and Java the byte — RX-205 |
| `\b{start}`, `\b{end}`, `\b{start-half}`, `\b{end-half}` | word assertions | refused, `BadRepeatBounds`, naming `\b` and Rust's reading | here a `{` after `\b` begins a repetition, and Perl reads the braces as a Unicode boundary (`SYNTAX.md` Y-32) — RX-213 |
| flags `U` and `R` | swap greed; CRLF mode | `(?U)` refused, `UnknownFlag`; `(?R)` refused as PCRE's recursion (`SYNTAX.md` Y-30) | flags nregex does not have — RX-206 |
| `x` mode inside a construct | white space skipped inside escapes, bounds and group heads — `\x4 1`, `a{2, 3}`, `( ?:a)` — and before a lazy `?` | read as without `x`, so each refused | Perl, Python and Java read each of these otherwise (`SYNTAX.md` Y-42) — RX-207 |
| white space past ASCII under `x` | Unicode's White_Space skipped | refused, `ExtendedAmbiguity` | Perl skips Pattern_White_Space, Python and Java ASCII white space alone (Y-42) — RX-207 |
| a codepoint past ASCII under `(?-u)` | `é` and `\x{E9}` are é's UTF-8 bytes, `\xE9` the byte E9; `[é]` refused | each refused but `\xE9`, the sentence naming the codepoint and its bytes | two escapes of one value naming different bytes is a difference no pattern should carry in silence (`SYNTAX.md` Y-43) — RX-208 |
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
| `\K` — Perl's and PCRE's reset of a match's start, which keeps what matched before it out of the match, as a lookbehind would | **refused**, `LookaroundUnsupported`, as lookaround — the author's amendment of 2026-10-02 (`SYNTAX.md` Y-44, RX-210) |
| `(?>…)`, `a*+` — atomic / possessive | **refused** — meaningless under an automaton |
| `(?R)`, `(?1)` — recursion | **refused** — not regular |
| `\Z` | refused, naming `\n?\z` |
| `$` before a trailing newline | **does not match** unless `m` — `SYNTAX.md` Y-19 |
| `\G` | refused; `regex_find_at` is the mechanism |
| `(?#…)` comments | refused; `x` mode's `#` is the spelling |
| `\p{InGreek}` | refused, naming `\p{Script=Greek}` |
| case folding of `ß`, `ﬁ` | **simple folding only** — `UNICODE.md` U-12 |
| `\w` | UTS #18 Annex C, not `[A-Za-z0-9_]` — `UNICODE.md` U-10 |
| `x` mode inside a class | a white-space byte or a `#` refused under `x`, where Perl's `/x`, PCRE2's `x`, Python and .NET read them as members and `xx` ignores a space or a tab — write `\x20` or `\#` (`SYNTAX.md` Y-39, RX-201) |
| `[` inside a class; `&&`, `--`, `~~` | a nested class, and the class operators of UTS #18 and Rust: `[a[b]]` is `a` or `b`, and `[a--b]` is `a` but not `b` — write `\[` and `\-` for the bytes (`SYNTAX.md` Y-36, RX-197) |
| `\012`, `\0` and a digit — octal | refused; write the hex form, `\x0A` (`SYNTAX.md` Y-40, RX-204) |
| `\x4`, `\x` and one hex digit | refused; `\x` takes exactly two, or any number in braces, `\x{4}` (Y-40) |
| `[\b]` — a backspace | refused; write `\x08` (Y-40) |
| `\c`, `\h`, ~~`\K`~~, `\N`, `\R`, `\X` and every other letter no rule names | refused, `UnknownEscape`: a `\` before a letter is never the letter (Y-2) — *since 2026-10-02 `\K` is refused as lookaround instead, the author's amendment: its row follows lookaround's (RX-210)* |
| Perl's `\u` and `\U`, which change case | `\u` takes four hex digits and `\U` eight, as in Python and Rust (Y-40) |
| `\uD83D\uDE00` — a UTF-16 pair, one codepoint in Java and JavaScript | refused at the first half; write `\x{1F600}` (Y-40) |
| `\<`, `\>` — the bytes in Perl, PCRE, Python and Java | refused, since Rust's `regex` and GNU `grep` read word assertions; write `<` or `>` (Y-40, RX-205) |
| `\E` alone — ignored by Perl and PCRE, refused by Java | refused, `UnsupportedQuoting`, as `\Q` is (`SYNTAX.md` Y-44, RX-209) |
| `[\1]` … `[\7]` — octal in a class in Perl, PCRE and Python | refused, `UnknownEscape`; write the hex form, `\x01` (Y-44) |
| `[\k]`, `[\G]`, `[\Z]` — the letter in Perl | refused, `UnknownEscape`, as any letter no rule names in a class (Y-44) |
| `\g1`, `\g{-1}`, `\g{name}` — Perl's and PCRE's backreferences; `\g<1>`, `\g'1'` — PCRE's call of a group | refused, `BackreferenceUnsupported` and `RecursionUnsupported` (`SYNTAX.md` Y-44, RX-210) |
| `\b{wb}`, `\b{sb}`, `\b{gcb}`, `\b{lb}`, `\B{wb}` — Perl's Unicode boundaries | refused, `BadRepeatBounds`, naming `\b` and Perl's reading (`SYNTAX.md` Y-32, RX-213) |
| `(?i)` after the pattern's start — global in Python, which requires it first | from there to the enclosing group's `)`, across `|`, as in Perl, PCRE and Rust (`SYNTAX.md` Y-41, RX-206) |
| `(?^)`, `(?a)`, `(?n)`, `(?U)` — Perl's, PCRE's and .NET's other flags | `UnknownFlag`: the flags are `i`, `m`, `s`, `x` and `u` (Y-41) |
| blanks inside `a{2, 3}` and `\x{ 41 }`, which Perl reads since its 5.34 | refused, `BadRepeatBounds` and `BadHexEscape`, under `x` or not (`SYNTAX.md` Y-32, Y-42) |
| white space past ASCII under `x` — U+2028, U+0085, U+200E skipped by Perl | refused, `ExtendedAmbiguity`; write `\x{2028}` (Y-42, RX-207) |

**Rule K-1 — every refusal names the alternative in its message**, and where
there is none it names the reason. `LookaroundUnsupported` says the pattern
cannot be matched in linear time, not "unsupported".
*(2026-10-02, cycle 0.1.5 — RX-212: it says nregex's automata read no lookahead
or lookbehind, and that they are what make every search take linear time — not
that lookaround cannot be matched in linear time, which two published algorithms
do ([`../research/lookaround-linear-time.md`](../research/lookaround-linear-time.md)).
And no refusal says it is unsupported.)*

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

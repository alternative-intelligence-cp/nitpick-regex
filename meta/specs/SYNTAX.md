# The pattern language

Exactly what `nregex` accepts, exactly what it refuses, and why. This document
is the authority; `COMPAT.md` compares it to other engines.

**Rule Y-1 (RX-010) — the accepted syntax is this grammar, not
"PCRE-compatible".** No engine is PCRE-compatible, several claim to be, and the
claim is how a user discovers a difference at run time in production. What is
accepted is written down here, and `COMPAT.md` §2 is an honest difference list.

---

## 1. The grammar

W3C EBNF, the compiler's own dialect, so a reader moving between the
repositories reads one notation.

```ebnf
Pattern      ::= Alternation
Alternation  ::= Concat ("|" Concat)*
Concat       ::= Repeat*
Repeat       ::= Atom Quantifier?
Quantifier   ::= ("*" | "+" | "?" | Bounded) "?"?      /* trailing ? = lazy */
Bounded      ::= "{" Digits "}"
               | "{" Digits "," "}"
               | "{" Digits "," Digits "}"
Atom         ::= Literal | Dot | Class | Group | Anchor | Escape
Group        ::= "(" GroupHead Alternation ")"
GroupHead    ::= ""                       /* capturing, numbered */
               | "?:"                     /* non-capturing */
               | "?<" Name ">"            /* capturing, named */
               | "?" Flags ":"            /* non-capturing, flags scoped to the group */
               | "?" Flags                /* flags applied to the rest of the enclosing group */
Flags        ::= [imsxu]* ("-" [imsxu]+)?
Anchor       ::= "^" | "$" | "\A" | "\z" | "\b" | "\B"
Class        ::= "[" "^"? ClassItem+ "]"
ClassItem    ::= ClassAtom ("-" ClassAtom)?  | PerlClass | PosixClass | UnicodeClass
                 | NestedClass | ClassOp
NestedClass  ::= Class                     /* [a[b-c]] */
ClassOp      ::= "&&" | "--" | "~~"        /* §5.3 */
PerlClass    ::= "\d" | "\D" | "\w" | "\W" | "\s" | "\S"
PosixClass   ::= "[:" "^"? PosixName ":]"
UnicodeClass ::= "\p" ("{" PropSpec "}" | Letter) | "\P" ("{" PropSpec "}" | Letter)
Escape       ::= "\" (Punct | "n" | "r" | "t" | "f" | "v" | "0" | "a" | "e"
                     | "x" HexPair | "x" "{" Hex+ "}" | "u" Hex4 | "U" Hex8)
Name         ::= [A-Za-z_][A-Za-z0-9_]*
```

**Rule Y-2 — a `\` before any ASCII punctuation is that punctuation,
literally.** `\@` is `@`. A `\` before an ASCII **letter or digit** that this
document does not list is a **refusal** (`UnknownEscape`), never a literal:
`\q` today meaning `q` is `\q` tomorrow meaning something else, and a pattern
that changes meaning across versions is worse than one that did not compile.

---

## 2. Matching semantics

**Rule Y-3 (RX-013) — leftmost-first, not leftmost-longest.** For a haystack
position, the alternation branch and the quantifier expansion that comes
*first* in the pattern wins, exactly as Perl, PCRE, Python, Rust and RE2's
default do. `sam|samwise` against `samwise` matches `sam`.

*The alternative*, POSIX leftmost-longest, would match `samwise`. It is more
principled — the answer does not depend on how the author ordered the
alternatives — and it is what almost nobody expects, because every pattern
written on the internet in the last thirty years assumes leftmost-first.
Recorded as O-Y1: a `RegexOptions.longest` switch is cheap in a Pike VM (it is
a different rule for which thread wins a slot) and is deferred until asked for.

**Rule Y-4 — the overall match is the leftmost one.** A search scans forward
from the start position and reports the first position at which any match
begins. Not the longest overall, not the last.

**Rule Y-5 — greedy by default, lazy with a trailing `?`.** `a*` prefers more,
`a*?` prefers fewer. Under leftmost-first this is a **preference order between
threads**, not a backtracking behaviour, and the Pike VM implements it by the
order it pushes alternatives.

**Rule Y-6 — capture group numbering is by the order of the opening
parenthesis**, left to right, starting at 1. Group 0 is the whole match. A
named group is also numbered.

**Rule Y-7 (RX-017) — one spelling for a named group: `(?<name>…)`.** The
Python spelling `(?P<name>…)` and the .NET spelling `(?'name'…)` are
**refused**, not accepted as aliases. Two spellings for one construct is the
context-dependence the ecosystem's blueprint philosophy refuses first, and a
refusal with the right spelling in the message costs a user five seconds once.

**Rule Y-8 — a name is unique within a pattern.** A duplicate is
`DuplicateGroupName`. Engines that allow duplicates have to answer "which one
did it match" and there is no good answer.

---

## 3. Parsing

**Rule Y-9 (RX-032) — an explicit stack, never native recursion**
(`SAFETY.md` S-18). The parser holds a `Vec<Frame>` bounded by
`NREGEX_NEST_DEPTH`; a pattern that exceeds it is `NestTooDeep` with the offset
of the parenthesis that did it.

**Rule Y-10 — every error carries a byte offset into the pattern**, and a
length where the construct spans more than a point. A user gets "unclosed
group at byte 14", not "invalid pattern".

**Rule Y-11 — the parser reads bytes, not codepoints, except inside a literal
or a class**, where a multi-byte UTF-8 sequence is decoded to a codepoint. A
pattern that is not valid UTF-8 is `InvalidPatternEncoding`. The **haystack**
has no such requirement (`SAFETY.md` S-20); the **pattern** does, because a
pattern is text a person wrote.

---

## 4. Flags

| Flag | Meaning | Default |
|---|---|---|
| `i` | case-insensitive, by simple case folding (`UNICODE.md` §4) | off |
| `m` | multi-line: `^` and `$` also match at line boundaries | off |
| `s` | `.` matches `\n` | off |
| `x` | extended: unescaped whitespace and `#`-to-end-of-line are ignored | off |
| `u` | Unicode mode: `.` is a codepoint, classes are Unicode-aware | **on** |

**Rule Y-12 — flags are scoped.** `(?i:…)` applies to the group; `(?i)` applies
from that point to the end of the **enclosing** group, and is undone when the
group closes. `(?-i)` clears. This is the standard scoping and there is no
global-flag argument to `regex_compile` — a pattern's behaviour is a property
of the pattern text, which is what makes a pattern copy-pasteable between
programs.

**Rule Y-13 — `(?-u)` is the byte mode and it is a real mode, not a
performance hint.** With Unicode off, `.` matches one **byte**, `\w` is ASCII,
a class is a byte class, and offsets may land inside a UTF-8 sequence. It
exists because searching binary data is a real thing a systems library is asked
to do. `UNICODE.md` §6 states the interaction with an invalid-UTF-8 haystack.

**Rule Y-14 — `(?-u)` with a pattern containing a non-ASCII literal is
refused** (`ByteModeNonAscii`). In byte mode a literal `é` would be two byte
literals, and `[é]` would be a class of two unrelated bytes — a silent
nonsense. The refusal names the codepoint.

---

## 5. Classes

**Rule Y-15 — a class is a set of codepoints** (or of bytes, under `(?-u)`),
computed at compile time into a sorted disjoint range list. Nothing about the
source order survives.

### 5.1 Perl and POSIX classes

`\d \D \w \W \s \S` are Unicode-aware in Unicode mode and ASCII in byte mode;
`UNICODE.md` §3 gives the exact property expansions, because "what is `\w`"
differs between engines and is worth pinning.

The POSIX bracket classes — `[:alpha:]`, `[:digit:]`, `[:alnum:]`, `[:space:]`,
`[:upper:]`, `[:lower:]`, `[:punct:]`, `[:print:]`, `[:graph:]`, `[:cntrl:]`,
`[:xdigit:]`, `[:blank:]`, `[:word:]`, `[:ascii:]` — are accepted **inside a
class only**, which is where POSIX puts them.

### 5.2 Unicode classes

`\p{Greek}`, `\p{L}`, `\p{Letter}`, `\p{Script=Greek}`,
`\p{Script_Extensions=Greek}`, `\p{gc=Lu}`, `\pL` (single-letter shorthand),
and `\P{…}` for the negation. `UNICODE.md` §2 has the supported property list
and the name-matching rule (loose matching: case, whitespace, `-` and `_`
insensitive, per UAX #44).

### 5.3 Class set operations

**Rule Y-16.** Inside a class, `&&` is intersection, `--` is difference and
`~~` is symmetric difference, with nesting: `[\p{L}&&\p{ASCII}]`,
`[[0-9]--[4]]`. These are the UTS #18 spellings and Rust's.

*Accepted rather than declined* because they are free: a class is already a
range set at compile time and set operations on sorted range lists are twenty
lines. Without them, `[\p{L}&&\p{ASCII}]` is written as an explicit range list
that goes stale when Unicode changes.

**Rule Y-17 — precedence inside a class is: union (implicit) binds tightest,
then `--`, then `~~`, then `&&`.** Stated because it differs between engines,
and a parenthesised nested class is always available where a reader would have
to think.

---

## 6. Anchors and boundaries

| Spelling | Matches at |
|---|---|
| `^` | the start of the haystack, and after every `\n` when `m` is on |
| `$` | the end of the haystack, and before every `\n` when `m` is on |
| `\A` | the start of the haystack, always |
| `\z` | the end of the haystack, always |
| `\b` | a word boundary (`UNICODE.md` §5) |
| `\B` | not a word boundary |

**Rule Y-18 — there is no `\Z`.** Perl's `\Z` matches at the end *or* before a
final newline, which is a special case that surprises everyone once and is
spelled `\n?\z` in three characters. Refused with that suggestion.

**Rule Y-19 — `$` does not match before a final newline** unless `m` is on.
This differs from Perl and matches Rust and RE2. It is stated here and in
`COMPAT.md` because it is the single most common cross-engine surprise.

**Rule Y-20 — a boundary assertion is a zero-width instruction, evaluated from
the byte before and the byte after the current position**, both of which the
engine has. It needs no lookaround machinery and does not compromise §2.

---

## 7. Empty matches

**Rule Y-21.** A pattern may match the empty string, and `a*` at a position
with no `a` does. This is legal and must be handled by every iterator
(`API.md` §6): after an empty match the iterator advances by **one codepoint**
(one byte in byte mode) before searching again, or it does not terminate. This
is the classic bug and the rule is stated here so it is implemented once.

**Rule Y-22 — a quantifier over an expression that can match empty is not an
infinite loop.** `(a*)*` is legal; the Pike VM's thread set is deduplicated by
program counter, so a cycle through zero-width instructions visits each
instruction at most once per haystack position. `ENGINES.md` §3 states the
mechanism; it is what makes `(a*)*` linear here and catastrophic elsewhere.

---

## 8. Refused, with the reason

**Rule Y-23.** Each of these is refused at compile time with its own
`PatternErrorKind`, its byte offset, and a message that names the guarantee
rather than saying "unsupported":

| Construct | Kind |
|---|---|
| `\1`, `\k<name>` | `BackreferenceUnsupported` |
| `(?=…)`, `(?!…)`, `(?<=…)`, `(?<!…)` | `LookaroundUnsupported` |
| `(?>…)`, `a*+`, `a++`, `a?+` | `AtomicGroupUnsupported` |
| `(?R)`, `(?1)`, `(?&name)` | `RecursionUnsupported` |
| `\G` | `UnsupportedAnchor` |
| `(?#comment)` | `UnsupportedGroup` — `x` mode's `#` is the spelling |
| `(?P<name>…)`, `(?'name'…)` | `WrongNamedGroupSpelling` — names `(?<name>…)` |
| `\Z` | `UnsupportedAnchor` — names `\n?\z` |
| `\Q…\E` | `UnsupportedQuoting` — names `regex_escape()` |

**Rule Y-24 — `regex_escape(text)` is the supported way to match a literal
string**, returning a pattern that matches exactly it. `\Q…\E` is refused
rather than implemented because it is a second, in-band quoting mechanism whose
interaction with `x` mode and with class syntax is a source of surprises in
every engine that has it.

---

## 9. `PatternErrorKind`

The closed list. Normative; `SAFETY.md` §4.1 references it.

**Structure**: `UnclosedGroup`, `UnopenedGroup`, `UnclosedClass`,
`EmptyClass`, `NestTooDeep`, `TrailingBackslash`, `EmptyAlternate`.

**Quantifiers**: `NothingToRepeat`, `DoubleRepeat`, `BadRepeatBounds`
(`{3,1}`), `RepeatTooLarge`, `RepeatProductTooLarge`.

**Classes**: `BadClassRange` (`[z-a]`), `UnknownPosixClass`,
`UnknownUnicodeProperty`, `ClassOpMismatch`, `ClassTooLarge`.

**Escapes**: `UnknownEscape`, `BadHexEscape`, `BadUnicodeEscape`,
`InvalidCodepoint` (a surrogate or above `U+10FFFF`).

**Groups and flags**: `DuplicateGroupName`, `BadGroupName`, `UnknownFlag`,
`TooManyCaptureGroups`, `WrongNamedGroupSpelling`.

**Refusals** (§8): `BackreferenceUnsupported`, `LookaroundUnsupported`,
`AtomicGroupUnsupported`, `RecursionUnsupported`, `UnsupportedAnchor`,
`UnsupportedGroup`, `UnsupportedQuoting`.

**Limits and encoding**: `PatternTooLong`, `ProgramTooLarge`,
`InvalidPatternEncoding`, `ByteModeNonAscii`.

**Rule Y-25 — every kind has a test that provokes it**, and a harness check
diffs the enum against the tests, so a kind nothing can produce is caught. This
is the compiler's `check_codes_tested` in this library's terms.

---

## 10. Open items

- **O-Y1 — leftmost-longest (POSIX) mode.** Cheap to add to the Pike VM and
  wanted by nobody yet. Recommendation: deferred; revisit if a consumer asks.
- **O-Y2 — whether `x` mode should ignore whitespace inside classes.** Rust
  does not; Perl does with `xx`. Recommendation: do not, matching Rust, and
  refuse `xx` with a message naming the escape. Decide at cycle 0.1.

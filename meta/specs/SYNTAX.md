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

*(2026-10-01, cycle 0.1.3 — RX-197: a `Class` is read as Y-36 says. Its operators stand between unions —
`Class ::= "[" "^"? Union (ClassOp Union)* "]"`, `Union ::= ClassItem+` — never as an item among the members;
`ClassAtom`, which the grammar leaves undefined, is one codepoint: any but `\`, `[` and `]`, or `\` and ASCII
punctuation, with `]` and `-` members where Y-36 places them; and a `PosixClass`'s name is lowercase, one of §5.1's
fourteen (Y-38).)*
*(2026-10-01, cycle 0.1.3 — RX-199: `Atom` holds `PerlClass` and `UnicodeClass` too, outside a class as in one — as Y-27
already says of `\d`, "in a class or out".)*

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
*(2026-09-25, cycle 0.0.4d — RX-161: the state that holds that `Vec<Frame>` is
move-only by containment — moved, lent by value to a reader, and passed by
pointer to anything that pushes or pops (`SAFETY.md` S-23b).)*
*(2026-09-27, cycle 0.1.1 — RX-182: the parser holds it — `src/syntax/parse.npk`'s
`Parser`, freed by `parse_pattern` on every path (Y-33) — and cycle 0.1.2 adds
the bound; until then the pattern's length bounds the stack.)*
*(2026-10-01, cycle 0.1.2 — RX-193: bounded, and decided at the `(` before a byte
after it is read — Y-35.)*
*(2026-10-01, cycle 0.1.3 — RX-198: and a class's frames on a `Vec<ClassFrame>`, bounded with it: groups and classes
together nest at most `NREGEX_NEST_DEPTH` deep, and a `[` that would go deeper is `NestTooDeep` at that `[` — Y-35.)*

**Rule Y-10 — every error carries a byte offset into the pattern**, and a
length where the construct spans more than a point. A user gets "unclosed
group at byte 14", not "invalid pattern".

**Rule Y-11 — the parser reads bytes, not codepoints, except inside a literal
or a class**, where a multi-byte UTF-8 sequence is decoded to a codepoint. A
pattern that is not valid UTF-8 is `InvalidPatternEncoding`. The **haystack**
has no such requirement (`SAFETY.md` S-20); the **pattern** does, because a
pattern is text a person wrote. *(Since cycle 0.1.1 the whole pattern is checked
first, before any grammar — Y-28, RX-183 — so every later step decodes without
checking.)*

**Rule Y-26 (RX-174) — the AST is a flat arena of nodes that own nothing, and
every operand is an `int64`.** `src/syntax/ast.npk`:

```nitpick
pub struct:AstNode = {
    AstKind:kind;      // Y-27
    uint32:flags;      // the AST_FLAG_ bits
    int64:a;           // Y-27's operands, by kind
    int64:b;
    int64:c;
    int64:next;        // the next sibling in its parent's list, or AST_NONE
    int64:pos;         // the construct's first byte in the pattern
    int64:len;         // its length in bytes
};
```

A node names another by its index in the same arena, or by `AST_NONE` (−1);
never by pointer, which a growing `Vec` would leave dangling (`HIR.md` H-3). It
owns nothing (`SAFETY.md` S-23a): a group's name and a property's text stay in
the pattern, held by offset and length, and the caller keeps the pattern for as
long as the AST lives. `flags` holds the pattern flags in force at the node —
`AST_FLAG_I` 1, `AST_FLAG_M` 2, `AST_FLAG_S` 4, `AST_FLAG_X` 8, `AST_FLAG_U` 16
(§4, scoped by Y-12) — and one bit for each of three kinds: `AST_FLAG_LAZY` 256
on a `Repeat`, `AST_FLAG_NEGATED` 512 on a `Class`, `PerlClass`, `PosixClass` or
`UnicodeClass`, and `AST_FLAG_BYTE` 1024 on a `Literal` that is a byte under
`(?-u)` (Y-13). `#size_of<AstNode>()` is 56, measured, with no padding.

**Rule Y-27 (RX-174) — the node kinds are a closed list of sixteen**, one for
each construct of §1 that survives parsing; a refusal (§8) produces none.

| Kind | Written | `a` | `b` | `c` | Bit |
|---|---|---|---|---|---|
| `Empty` | an empty pattern, alternative or group body | | | | |
| `Literal` | a character, or an escape naming one | its codepoint; a byte under `BYTE` | | | `BYTE` |
| `Dot` | `.` | | | | |
| `Concat` | two or more pieces in sequence | the first | how many | | |
| `Alternate` | two or more alternatives, `a\|b` | the first | how many | | |
| `Repeat` | `*` `+` `?` `{n}` `{n,}` `{n,m}` | the repeated node | the minimum | the maximum; `AST_NONE` if unbounded | `LAZY` |
| `Group` | `(…)` `(?:…)` `(?<name>…)` `(?flags:…)` | the body | its capture index; 0 if it captures nothing | its name's length, the name starting at `pos + 3`; 0 if unnamed | |
| `Flags` | `(?flags)` | the flags it sets | the flags it clears | | |
| `Anchor` | `^` `$` `\A` `\z` | 0, 1, 2, 3, in that order | | | |
| `WordBoundary` | `\b` `\B` | 0, 1 | | | |
| `Class` | `[…]`, a nested class, an operand of a class operator | the first item | how many | | `NEGATED` |
| `ClassRange` | `a-z`, or one character in a class | the low codepoint | the high codepoint, equal for one character | | |
| `PerlClass` | `\d` `\w` `\s`, in a class or out; a capital negates | 0, 1, 2 | | | `NEGATED` |
| `PosixClass` | `[:name:]` `[:^name:]` | the name's place in §5.1's list, from 0 | | | `NEGATED` |
| `UnicodeClass` | `\p{…}` `\pL` `\P{…}` `\PL` | the property text's offset | its length | | `NEGATED` |
| `ClassOp` | `&&` `--` `~~` | the left operand | the right operand | 0, 1, 2, in that order | |

A list's members — a `Concat`'s pieces, an `Alternate`'s alternatives, a
`Class`'s items — are its first member and each member's `next`, in the order
written. The subcycle that parses a construct produces its kind; the operands
are this table's until a decision says otherwise.
*(2026-10-01, cycle 0.1.3 — RX-197: what a class's nodes hold, as the parser builds them (Y-36). A `Class` with no
operator holds its members in order; with operators it holds one item, the last `ClassOp`. A `ClassOp`'s `a` is
everything before its operator — the first union, or the `ClassOp` before it — and its `b` the union after it, so
operators fold left; each union an operator takes is a `Class` of its members, never negated, from its first member's
first byte to its last member's last; a `ClassOp` spans its left operand's first byte through its right operand's
last. A member that is one codepoint is a `ClassRange` from it to itself, spanning how it is written — `\]` is two
bytes. A `PerlClass` spans two bytes, a `UnicodeClass` its `\` through its name's last byte or its `}`, a
`PosixClass` its `[` through its `]`.)*

**Rule Y-28 (RX-183) — a pattern is UTF-8 text, checked whole before the grammar,
and every character is a literal but twelve.** After the length (RX-175), the pattern
is checked against RFC 3629's well-formed UTF-8: no continuation byte where a
character starts; no overlong form (a lead `C0` or `C1`, `E0` before less than `A0`,
`F0` before less than `90`); no surrogate (`ED` before more than `9F`); nothing above
U+10FFFF (`F4` before more than `8F`, or a lead `F5` … `FF`). The first ill-formed
sequence is `InvalidPatternEncoding`: its offset the sequence's first byte, its
length the bytes read up to and including the one that broke it, its detail that
byte — 0 when the pattern ended inside the sequence. Outside a class the
metacharacters are `\ . ^ $ | ? * + ( ) [ {`; every other character — a bare `]` or
`}` included — is a `Literal` of its codepoint, spanning its bytes. `.` is a `Dot`,
`^` an `Anchor` 0 and `$` an `Anchor` 1. `\` before ASCII punctuation is that
punctuation, a `Literal` spanning two bytes (Y-2), and `\` as the last byte is
`TrailingBackslash` at it.

**Rule Y-29 (RX-185) — groups.** `(` opens a capturing group, numbered by its `(`
(Y-6); `(?:` a non-capturing one; `(?<name>` a capturing one named by
`Name ::= [A-Za-z_][A-Za-z0-9_]*`. A capturing group — named or not — numbered past
`NREGEX_CAPTURE_GROUPS` is `TooManyCaptureGroups` at its `(`, detail the bound. A
name that is empty, begins with a digit, holds any other character, or has no `>` is
`BadGroupName`: at the offending character, its detail that character's codepoint —
at the `>` with detail `>` (62) for an empty name — or, when the pattern ends first,
at the name's start, spanning what was read, detail 0. A name already used is
`DuplicateGroupName` at the second, spanning it, its detail the first group's
number. `)` with no group open is `UnopenedGroup` at it. A pattern that ends inside
a group is `UnclosedGroup` at the INNERMOST open `(`, its detail how many are open;
`(?` as the pattern's last two bytes is `UnclosedGroup` spanning both. `(?P<` and
`(?'` are `WrongNamedGroupSpelling` (Y-7) at the `(`, spanning the head, detail `P`
(80) or `'` (39).
*(2026-10-01, cycle 0.1.2 — RX-193: unless the `(` would nest groups deeper than
`NREGEX_NEST_DEPTH`. Then it is `NestTooDeep` before anything this rule decides — its
number, its name, or a `(?` the pattern ends on — so 251 nested `(` are `NestTooDeep`
at byte 250, never `TooManyCaptureGroups` (Y-35).)*

**Rule Y-30 (RX-185) — the refusals of §8 that a group head or a quantifier spells
are made where they are read**, each at the `(`, spanning the head read, its detail
the head's last byte: `(?=`, `(?!`, `(?<=`, `(?<!` are `LookaroundUnsupported`;
`(?>` is `AtomicGroupUnsupported`; `(?R`, `(?&`, `(?P>`, and `(?` before a digit,
`+`, or `-` and a digit are `RecursionUnsupported`; `(?P=` is
`BackreferenceUnsupported`; `(?#` is `UnsupportedGroup`. A `+` straight after a
quantifier — `a*+`, `a{2}+` — is `AtomicGroupUnsupported` at the quantifier,
spanning through the `+`, detail `+` (43). §8's escapes (`\1`, `\k<…>`, `\G`,
`\Z`, `\Q`) are cycle 0.1.5's, after 0.1.4 parses escapes.
*(2026-10-01, cycle 0.1.2 — RX-193: a head a `(` past `NREGEX_NEST_DEPTH` would open is
never read; that `(` is `NestTooDeep` (Y-35).)*

**Rule Y-31 (RX-186) — until its parser exists, a construct is refused
PROVISIONALLY**, with the kind its parser gives a member it does not know: `[` is
`UnclosedClass` at the `[` (cycle 0.1.3); `\` before anything but ASCII punctuation
is `UnknownEscape` at the `\`, spanning it and the character, detail the
character's codepoint (cycle 0.1.4); `(?` before anything Y-29 and Y-30 do not name
— a flag included — is `UnknownFlag` at that character, detail its codepoint (cycle
0.1.4). No test pins a provisional refusal; the subcycle that parses the construct
replaces it. One answer among them is final, and a test pins it: `(?P` before a
byte Y-29 and Y-30 do not name is `UnknownFlag` at the `P`, detail `P` (80), in
every cycle, since `P` is no flag (`parse_refusals.npk` case 64).
*(2026-10-01, cycle 0.1.2 — RX-193: not at a `(` past `NREGEX_NEST_DEPTH`, which is
`NestTooDeep` before what follows it is read (Y-35).)*
*(2026-10-01, cycle 0.1.3 — RX-197: `[` is no longer provisional: Y-36 reads a class and says what a pattern that ends
inside one is — `UnclosedClass` at the innermost open `[`, its detail telling a `]` first in the class apart, unless it
ends inside an escape, a property's name or a `[:`. Inside a class,
`\d \D \w \W \s \S`, `\p` and `\P` are classes (Y-37); any other escape there, and every one outside a class
but punctuation, is still refused provisionally.)*
*(2026-10-01, cycle 0.1.3 — RX-199: outside a class too, `\d \D \w \W \s \S`, `\p` and `\P` are classes (Y-37);
every other escape but punctuation is still refused provisionally, until cycle 0.1.4.)*

**Rule Y-32 (RX-184) — quantifiers.** `*`, `+`, `?`, `{n}`, `{n,}` and `{n,m}`, each
followed by `?` to be lazy, wrap the atom before them in a `Repeat` — `a` the atom,
`b` the minimum, `c` the maximum or `AST_NONE`, `AST_FLAG_LAZY` when lazy; `pos` the
atom's, `len` through the quantifier. With no atom before it — at the pattern's
start, after `(` or after `|` — a quantifier is `NothingToRepeat`; after a
quantifier it is `DoubleRepeat`; each at the quantifier, detail its first byte, and
each decided there, before a bound is read. A lazy `?` belongs to the quantifier
before it: `a*?` is lazy, `a*??` a `DoubleRepeat` at its last `?`. A `{` always
begins a bounded repeat, and one that is not `{`digits`}`, `{`digits`,}` or
`{`digits`,`digits`}` — no space, no sign, no missing minimum — is `BadRepeatBounds`
at the `{`, spanning what was read, detail 0; a bound above `NREGEX_REPEAT_MAX` is
`RepeatTooLarge` at its first digit, spanning its digits, detail the bound (the
value stops growing past the bound, so no digit string overflows); a minimum above
the maximum is `BadRepeatBounds` spanning the braces, detail 1. A repeated group or
anchor is legal (Y-22).

**Rule Y-33 (RX-182) — the tree the parse builds.** `parse_pattern(uint8[]:pat,
Ast->:out)` refuses the length, then the encoding, then walks the pattern ONCE in
one `while`: a `(` saves the frame being built on a `Vec<Frame>` and starts the
group's, and its `)` takes the saved frame back — no function calls itself (RX-032).
A frame holds the alternatives closed so far, the current alternative's pieces, and
its last atom PENDING — not yet linked — so a quantifier can wrap it. An alternative
with no piece is an `Empty` at the offset where it ends; with one, that piece; with
more, a `Concat` from where it starts to where it ends. A body of one alternative is
that alternative; of more, an `Alternate` from where the body starts. A `Group` spans
its `(` through its `)`. Every node's `flags` are the flags in force — `AST_FLAG_U`
until cycle 0.1.4 parses flags — with `AST_FLAG_LAZY` on a lazy `Repeat`. The first
refusal, left to right, is the answer; the tree's nodes are then partial, its root is
unchanged, and the caller frees them.
*(2026-10-01, cycle 0.1.3 — RX-197: a class is read by a `while` of its own, `parse_class`'s, which the walk's `while`
calls at a `[` and which returns at the class's `]` — still once over the pattern, no byte read twice and no function
calling itself, its frames on an explicit stack of their own, a `Vec<ClassFrame>` (Y-36).)*

**Rule Y-35 (RX-193) — groups nest at most `NREGEX_NEST_DEPTH` deep, and the bound
is decided at the `(`.** A `(` read while `NREGEX_NEST_DEPTH` groups — 250 — are open
around it is `NestTooDeep` at that `(`, length 1, detail the bound, and it is decided
BEFORE any byte after the `(` is read: no frame past the bound is pushed, nothing
past the `(` is read, and the parse stops where the bound is rather than where the
pattern ends. So it is the answer whatever would have followed — a capture numbered
past `NREGEX_CAPTURE_GROUPS` (Y-29; 251 nested `(` are `NestTooDeep` at byte 250), a
head §8 refuses (Y-30), a construct refused provisionally (Y-31), or the end of the
pattern. 250 nested groups parse. The bound counts groups, the one construct that
nests here; a class nests too from cycle 0.1.3, which bounds it.
*(2026-10-01, cycle 0.1.3 — RX-198: classes nest, and count with groups. A `[` that would open a class while groups and
classes — `NREGEX_NEST_DEPTH`, 250, together — are open around it is `NestTooDeep` at that `[`, length 1, detail the
bound, before a byte after it is read; a POSIX class's `[:` opens no class and nests nothing. So 250 nested classes
parse and the 251st `[` is `NestTooDeep` at byte 250, and so is a `[` inside 250 groups, or the 126th `[` inside 125.
The refusal's sentence names both: *"the `(` or `[` here would nest groups and classes 251 deep"*.)*

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

> **SUPERSEDED by RX-196 (2026-10-01)** — the order below is no engine's. Rust applies the three operators at one
> precedence, left to right, union binding tighter and negation last, and UTS #18 requires no order and binds every
> operator at one level in its own syntax ([`../research/class-syntax-reference-engines.md`](../research/class-syntax-reference-engines.md)).
> So does this library now: `[a--b&&c]` is `[[a--b]&&c]`. Kept as written: how the rule was stated is part of the
> record.

**Rule Y-17 — precedence inside a class is: union (implicit) binds tightest,
then `--`, then `~~`, then `&&`.** Stated because it differs between engines,
and a parenthesised nested class is always available where a reader would have
to think.

### 5.4 How a class is read

*(2026-10-01, cycle 0.1.3 — RX-197.)*

**Rule Y-36 (RX-197) — a class is read once, left to right: its members, its ranges, and the operators between
unions.** `[` outside a class opens one, `[^` a negated one, and the class ends at its `]`.

- **Its members are codepoints and classes.** A codepoint is written as itself — any but `\`, `[` and `]`, decoded
  from UTF-8 (Y-11), white space and every metacharacter of Y-28 included — or as `\` and ASCII punctuation (Y-2). A
  class is `\d \D \w \W \s \S` or `\p…` `\P…` (Y-37), `[:name:]` (Y-38), or a nested class: `[`, its own
  members, its own `]`. Any other escape is cycle 0.1.4's (Y-31).
- **`]` straight after `[` or `[^` is a member**, not the end, and so is a `-` straight after that `]`. So `[]a]`
  holds `]` and `a`, and `[]` and `[^]` never end. A pattern that ends inside a class — not inside an escape
  (`TrailingBackslash`, Y-28), a property's name (Y-37) or a `[:` (Y-38) — is `UnclosedClass` at the innermost open
  `[`, length 1, its detail `]` (93) when that class's first member is a `]`, else 0.
- **A range** is a codepoint, `-` and a codepoint: `a-z`. Both ends must be codepoints, the first not above the second
  — else `BadClassRange` at the range's first byte, spanning through the byte that made it bad, its detail 0 for an
  end below its start (`[z-a]`) and 1 for a class at either end (`[\w-.]`, `[a-\d]`, `[[a]-z]`, `[a-[b]]`). The end
  is read whatever it is: `[!-&&a]` is the range `!-&` and the members `&` and `a`.
- **A `-` is a member** where a member would start — first in the class, straight after the first `]`, after a range,
  after an operator — and straight before the class's `]`. `[-a]`, `[]-a]`, `[a-]` and `[a-c-e]` each hold a `-`.
- **`&&`, `--` and `~~` are its operators** (Y-16): two of those bytes together, read where a member would start or
  straight after one; a lone `&` or `~` is a member. Members side by side are a union, and an operator takes the
  union before it and the one after it, each of which must hold a member — else `ClassOpMismatch` at the operator,
  length 2, its detail the operator's byte (`[&&a]`, `[a--]`, `[a&&&&b]`, `[--a]`). The operators apply left to
  right at one precedence, and `^` complements the result (RX-196).
- **The tree** is Y-27's, as its note says: a `Class` from `[` through `]`, `AST_FLAG_NEGATED` for `[^`.
- **The nesting** is bounded with groups' (Y-35).

No class the parser builds is empty, so no pattern reaches `EmptyClass` here (§9; O-Y3). Where Rust's `regex` reads a
shape one way and this rule another, this rule refuses it (`COMPAT.md` §2).

**Rule Y-37 (RX-197) — Perl classes and Unicode properties are parsed, never resolved.** `\d`, `\w` and `\s` are
`PerlClass` 0, 1 and 2, and `\D`, `\W` and `\S` the same, negated. `\p` names a Unicode property — one ASCII
letter, `\pL`, or a name in braces up to the first `}`, `\p{Script=Greek}` — kept as text: a `UnicodeClass` holding
the name's offset and length, negated for `\P`. Cycle 0.3 resolves both (`UNICODE.md` §2, §3), and the parser reads
no table. A name that cannot be read is `UnknownUnicodeProperty` at the `\`, spanning what was read: detail 1 when
neither an ASCII letter nor `{` follows the `p`, 2 when the braces never close, 3 when they hold nothing. Each is a
member of a class (Y-36).
*(2026-10-01, cycle 0.1.3 — RX-199: and outside a class, an atom, which a quantifier may repeat.)*

**Rule Y-38 (RX-197) — POSIX classes, inside a class only.** Where a member would start inside a class, `[:` begins
a POSIX class: `[:name:]`, or `[:^name:]` for its complement, its name lowercase and one of §5.1's fourteen — a
`PosixClass` holding the name's place in that list. Anything else after `[:` — a name not on the list, no `:]`, a
capital — is `UnknownPosixClass` at the `[`, spanning what was read, detail 0: never a nested class instead, as Rust
reads one, because the cursor does not go back (RX-173). Outside a class, `[:` opens a class whose first member is
`:`.
*(2026-10-01, cycle 0.1.3 — RX-200: an outermost class whose every member is one codepoint written as itself, the first
and the last `:` and another not — `[:alpha:]`, `[^:alpha:]`, `[:alhpa:]` — is `UnknownPosixClass` at its `[`, spanning
the class: its detail the name's place in §5.1's list plus one when the bytes between the colons, less a leading `^`,
are one of its names, else 0. GNU `grep` refuses these too. `[::]`, `[:::]` and `[:alpha]` are classes of their bytes;
a range, an escape, a nested, POSIX or Perl class, a property or an operator makes a class one written as a class, so
`[:a-z:]` and `[:[:digit:]:]` are classes, and `\:` at either end writes a `:`.)*

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
`EmptyClass`, `NestTooDeep`, `TrailingBackslash`. ~~`EmptyAlternate`~~ — *retired
2026-09-27, cycle 0.1.1 (RX-181): an empty alternative is Y-27's `Empty`, accepted, as
in every engine this document compares against (`COMPAT.md`), so no pattern could
provoke the kind, and Y-25 forbids a kind nothing produces.*
*(2026-10-01, cycle 0.1.3 — RX-197: no pattern reaches `EmptyClass` in the parser: a `]` straight after `[` or `[^` is a
member (Y-36), so every class it builds holds one. Whether a class that RESOLVES to nothing is `EmptyClass`, or the
kind retires as `EmptyAlternate` did, is open question O-Y3, for cycle 0.3.4.)*

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

**Rule Y-34 (RX-187) — every refusal reads as what is wrong, where, and what to
write instead.** `pattern_error_text(PatternError) -> string` (`API.md` §1) renders one
sentence per kind: the kind in words and `at byte` the offset, then the reason, then
the fix wherever the library can tell what the author meant — `\(` for a literal
parenthesis, `(?<name>…)` for Python's and .NET's spellings, `(?:…)` for a group that
need not capture, `\{` for a brace. A refusal of a construct §8 declines names the
guarantee it would break, or the alternative, never "unsupported" alone (`COMPAT.md`
K-1). The text is built from the four fields alone — the pattern is not an argument
— and in a `Bytes`, so a number costs no allocation and no division
(`bytes_put_uint`, `SAFETY.md` S-25). Every kind has a sentence from cycle 0.1.1;
each later subcycle holds its kinds' sentences to the letter when it produces them,
as `tests/unit/pattern_error_text.npk` holds 0.1.1's.

**Rule Y-25 — every kind has a test that provokes it**, and a harness check
diffs the enum against the tests, so a kind nothing can produce is caught. This
is the compiler's `check_codes_tested` in this library's terms.

**What each refusal cycle 0.1.1 makes carries** — Y-10's offset and length, and the
detail a message is built from (Y-29 … Y-32) *(and, since 2026-10-01, each cycle 0.1.3's classes make — Y-36 … Y-38,
RX-197)*:

| Kind | Raised when | Offset | Length | Detail |
|---|---|---|---|---|
| `UnclosedGroup` | the pattern ends inside a group | the innermost open `(` | 1; 2 for `(?` at the end | how many groups are open |
| `UnopenedGroup` | `)` with no group open | the `)` | 1 | 0 |
| `TrailingBackslash` | `\` is the last byte | the `\` | 1 | 0 |
| `NothingToRepeat` | a quantifier with no atom before it | the quantifier | 1 | its first byte |
| `DoubleRepeat` | a quantifier after a quantifier | the second one | 1 | its first byte |
| `BadRepeatBounds` | a `{` that is no bounded repeat; a minimum above the maximum | the `{` | what was read | 0; 1 |
| `RepeatTooLarge` | a bound above `NREGEX_REPEAT_MAX` | its first digit | its digits | the bound |
| `TooManyCaptureGroups` | a group numbered past `NREGEX_CAPTURE_GROUPS` — *not one nested past `NREGEX_NEST_DEPTH`, which is `NestTooDeep` first (Y-35)* | its `(` | 1 | the bound |
| `DuplicateGroupName` | a name already used | the second name | its length | the first group's number |
| `BadGroupName` | an empty, malformed or unfinished name | the bad character; for an unfinished one the name | the character's bytes; what was read | its codepoint; 62 when empty; 0 when unfinished |
| `WrongNamedGroupSpelling` | `(?P<` or `(?'` | the `(` | the head | 80 or 39 |
| `LookaroundUnsupported`, `AtomicGroupUnsupported`, `RecursionUnsupported`, `BackreferenceUnsupported`, `UnsupportedGroup` | Y-30's group heads | the `(` | the head | its last byte |
| `AtomicGroupUnsupported` | a quantifier made possessive | the quantifier | through the `+` | 43 |
| `InvalidPatternEncoding` | ill-formed UTF-8 | the sequence's first byte | through the byte that broke it | that byte; 0 when cut short |
| `PatternTooLong` (cycle 0.1.0) | over `NREGEX_PATTERN_BYTES` | the first byte past the bound | the bytes over it | the bound |
| `NestTooDeep` (cycle 0.1.2) | a `(` that would nest groups deeper than `NREGEX_NEST_DEPTH` (Y-35) — *and since cycle 0.1.3 a `[` that would nest groups and classes deeper, counted together (RX-198)* | that `(` *or `[`* | 1 | the bound |
| `UnclosedClass` (cycle 0.1.3) | the pattern ends inside a class — not inside an escape, a property's name or a `[:` | the innermost open `[` | 1 | 93 when that class's first member is a `]`; 0 |
| `BadClassRange` (cycle 0.1.3) | a range's end below its start; a class at either end | the range's first byte | through the byte that made it bad | 0; 1 |
| `ClassOpMismatch` (cycle 0.1.3) | `&&`, `--` or `~~` with no member before it or after it | the operator | 2 | its byte: 38, 45 or 126 |
| `UnknownPosixClass` (cycle 0.1.3) | `[:` inside a class that opens no `[:name:]` or `[:^name:]` with a name of §5.1 | its `[` | what was read | 0 |
| `UnknownPosixClass` (cycle 0.1.3, RX-200) | an outermost class whose every member is one codepoint written as itself, the first and the last `:` and another not | its `[` | the class | the name's place in §5.1's list plus one; 0 when the bytes name none |
| `UnknownUnicodeProperty` (cycle 0.1.3) | `\p` or `\P` whose name cannot be read | the `\` | what was read | 1, no letter or `{` after it; 2, no `}`; 3, empty braces — 0 is cycle 0.3's, a name it does not know |

*(2026-09-27, cycle 0.1.1 — RX-181: thirty-six, `EmptyAlternate` retired.)*
*(2026-09-26, cycle 0.1.0 — RX-172: `src/syntax/pattern_error.npk`'s
`PatternErrorKind` is this list, all thirty-seven, in this order, declared
before the parser produces any of them, and `tests/unit/pattern_error_unit.npk`
holds the enum to the list with an exhaustive `pick`. The harness check is
cycle 0.1.6's.)*

---

## 10. Open items

- **O-Y1 — leftmost-longest (POSIX) mode.** Cheap to add to the Pike VM and
  wanted by nobody yet. Recommendation: deferred; revisit if a consumer asks.
- **O-Y2 — whether `x` mode should ignore whitespace inside classes.** Rust
  does not; Perl does with `xx`. Recommendation: do not, matching Rust, and
  refuse `xx` with a message naming the escape. Decide at cycle 0.1.
- **O-Y3 — what `EmptyClass` names, now that no pattern reaches it in the parser** (Y-36). Recommendation: a class
  that resolves to no codepoint, refused at its `[`. Decide at cycle 0.3.4. `../OPEN_QUESTIONS.md` has the argument.

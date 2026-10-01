# Class syntax in the reference engines — research digest

**As of 2026-10-01.** Question: in extended (`x`) mode, does each of these ignore unescaped whitespace inside a
bracketed class — Rust's `regex`, Perl (`/x`, `/xx`), PCRE2 (`PCRE2_EXTENDED`, `PCRE2_EXTENDED_MORE`), Python's
`re.VERBOSE`, .NET's `IgnorePatternWhitespace` and Java's `Pattern.COMMENTS`? And what do Rust's `regex` and UTS #18
say about how the class operators `&&`, `--` and `~~` are spelled and how they bind? *(Asked for open question O-Y2
and `SYNTAX.md` Y-16 and Y-17 by the planner of `roadmap/0.1/0.1.3.md`; answered by the researcher, its digest
below, and corroborated by running four of the engines in this repository's gitignored scratch — the last section,
which also records GNU `grep`'s reading of a POSIX class written as a whole bracket expression, for the same plan.)*

## Answer

Two engines ignore whitespace inside a bracketed class in `x` mode: Rust's `regex` 1.13.1 — "whitespace is ignored
everywhere, including within character classes", its parser (regex-syntax 0.8.11) running its whitespace-and-comment
skipper at every item of a class — and Java SE 27's `COMMENTS`. Two more ignore it only under the doubled flag, and
then only space and tab: Perl 5.44.0 with `/xx` (added in v5.26) and PCRE2 10.49 with `PCRE2_EXTENDED_MORE` /
`(?xx)`. Whitespace inside a class stays significant under Perl's single `/x`, PCRE2's `PCRE2_EXTENDED`, Python
3.14.8's `re.VERBOSE` and .NET's `IgnorePatternWhitespace`. So O-Y2's premise, *"Rust does not"*, is false.

Rust spells the class operators `&&` (intersection), `--` (difference) and `~~` (symmetric difference). Its
precedence, tightest first: ranges, then union, then all three operators at one level evaluated left to right, then
negation — not Y-17's order (union, `--`, `~~`, `&&`). UTS #18 revision 25 (2025-01-16) uses the same three
spellings and adds `||` for an explicit union; it "does not require any particular operator precedence scheme", its
example syntax puts every operator, implicit union included, at one level, left to right, and it tells users to
bracket, because binding varies by engine. The latest published `regex` is 1.13.1 and `regex-syntax` 0.8.11;
regex-syntax's AST parser sets `nest_limit: 250`, a limit on the whole tree's depth, a concatenation one level.

| Engine | Version read | `x` ignores whitespace inside a class | The line |
|---|---|---|---|
| Rust `regex` | 1.13.1 (regex-syntax 0.8.11) | yes, all whitespace, and `#` comments too (measured below) | "Note that in verbose mode, whitespace is ignored everywhere, including within character classes." |
| Perl | 5.44.0 | only with `/xx` (since v5.26), and only SPACE and TAB | `/x`: "ignore most whitespace that is neither backslashed nor within a bracketed character class"; `/xx`: "inside bracketed character classes, non-escaped (by a backslash) SPACE and TAB characters are not added to the class" |
| PCRE2 | 10.49 | only with `PCRE2_EXTENDED_MORE` / `(?xx)`, and only space and horizontal tab | `EXTENDED`: "totally ignored except when escaped, inside a character class, or inside a \Q...\E sequence"; `EXTENDED_MORE`: "unescaped space and horizontal tab characters are ignored inside a character class" |
| Python `re` | 3.14.8 | no | "Whitespace within the pattern is ignored, except when in a character class, ..." |
| .NET | article dated 2022-06-02, updated 2026-07-08 | no | "White space within a character class is always interpreted literally." |
| Java | SE 27 | yes | "Comments mode ignores whitespace within a character class contained in a pattern string." |

## Evidence

- <https://docs.rs/regex/latest/regex/> (regex 1.13.1, crate root, Syntax) — retrieved 2026-10-01:
  - "x     verbose mode, ignores whitespace and allow line comments (starting with `#`)"
  - "Note that in verbose mode, whitespace is ignored everywhere, including within character classes."
  - "Precedence in character classes, from most binding to least: 1. Ranges: `[a-cd]` == `[[a-c]d]` 2. Union:
    `[ab&&bc]` == `[[ab]&&[bc]]` 3. Intersection, difference, symmetric difference. All three have equivalent
    precedence, and are evaluated in left-to-right order. For example, `[\pL--\p{Greek}&&\p{Uppercase}]` ==
    `[[\pL--\p{Greek}]&&\p{Uppercase}]`. 4. Negation: `[^a-z&&b]` == `[^[a-z&&b]]`."
  - "`[a-y&&xyz]` Intersection (matching x or y)", "`[0-9--4]` Direct subtraction (matching 0-9 except 4)",
    "`[a-g~~b-h]` Symmetric difference (matching `a` and `h` only)".
- <https://raw.githubusercontent.com/rust-lang/regex/1.13.1/src/lib.rs> (tag 1.13.1) — retrieved 2026-10-01: the
  same sentence, then "To insert whitespace, use its escaped form or a hex literal. For example, `\ ` or `\x20` for
  an ASCII space."
- <https://raw.githubusercontent.com/rust-lang/regex/regex-syntax-0.8.11/regex-syntax/src/ast/parse.rs> (tag
  regex-syntax-0.8.11) — retrieved 2026-10-01: `ParserBuilder::new()` sets "`nest_limit: 250,`"; `bump_space`: "If
  the `x` flag is enabled (i.e., whitespace insensitivity with comments), then this will advance the parser through
  all whitespace and comments to the next non-whitespace non-comment byte"; `parse_set_class` opens "`loop {
  self.bump_space(); if self.is_eof() {`".
- <https://docs.rs/regex-syntax/latest/regex_syntax/struct.ParserBuilder.html> (0.8.11) — retrieved 2026-10-01:
  "The nesting limit controls how deep the abstract syntax tree is allowed to be. If the AST exceeds the given limit
  (e.g., with too many nested groups), then an error is returned by the parser." … "a nest limit of `0` permits `a`
  but not `ab`, since `ab` requires a concatenation, which results in a nest depth of `1`."
- <https://perldoc.perl.org/perlre> (Perl 5.44.0) — retrieved 2026-10-01: "A single /x tells the regular expression
  parser to ignore most whitespace that is neither backslashed nor within a bracketed character class, nor within
  the characters of a multi-character metapattern like (?i: ... )." — "Starting in Perl v5.26, if the modifier has a
  second "x" within it, the effect of a single /x is increased. The only difference is that inside bracketed
  character classes, non-escaped (by a backslash) SPACE and TAB characters are not added to the class".
- <https://raw.githubusercontent.com/PCRE2Project/pcre2/pcre2-10.49/doc/pcre2api.3> (tag pcre2-10.49, the page
  headed "08 December 2025" "PCRE2 10.49") — retrieved 2026-10-01: `PCRE2_EXTENDED`: "most white space characters
  in the pattern are totally ignored except when escaped, inside a character class, or inside a \Q...\E sequence";
  `PCRE2_EXTENDED_MORE`: "unescaped space and horizontal tab characters are ignored inside a character class. Note:
  only these two characters are ignored, not the full set of pattern white space characters that are ignored
  outside a character class."
- <https://docs.python.org/3/library/re.html> (Python 3.14.8) — retrieved 2026-10-01: "Whitespace within the
  pattern is ignored, except when in a character class, or when preceded by an unescaped backslash, …"
- <https://learn.microsoft.com/en-us/dotnet/standard/base-types/regular-expression-options> (ms.date 2022-06-02,
  updated 2026-07-08) — retrieved 2026-10-01: "White space within a character class is always interpreted
  literally."
- <https://docs.oracle.com/en/java/javase/27/docs/api/java.base/java/util/regex/Pattern.html> (Java SE 27) —
  retrieved 2026-10-01: "Comments mode ignores whitespace within a character class contained in a pattern string.
  Such whitespace must be escaped in order to be considered significant."
- <https://www.unicode.org/reports/tr18/> = <https://www.unicode.org/reports/tr18/tr18-25.html> ("Version 25",
  "Revision 25", "Date 2025-01-16") — retrieved 2026-10-01: "OPERATOR := '||' := '&&' := '--' := '~~'"; "This
  specification does not require any particular operator precedence scheme. The illustrative syntax puts all
  operators on the same precedence level, … That is, in the absence of brackets, each operator combines the
  following CHARACTER_CLASS with the current accumulated results."; "In particular, precedence may put all operators
  on the same level, or may take union as binding more closely."; "Binding or precedence may vary by regular
  expression engine, so as a user it is safest to always disambiguate using brackets to be sure."; "For clarity, it
  is common to use doubled symbols, and require a CHARACTER_CLASS on both sides of the OPERATOR."
- <https://raw.githubusercontent.com/coreutils/gnulib/master/lib/dfa.c> (gnulib at master, "Copyright (C) 1988, 1998,
  2000, 2002, 2004-2005, 2007-2026 Free Software Foundation, Inc.") — retrieved 2026-10-01; savannah's own cgit
  answered 502: "Used to warn about [:space:]. Bit 0 = first character is a colon. Bit 1 = last character is a colon.
  Bit 2 = includes any other character but a colon. Bit 3 = includes ranges, char/equiv classes or collation
  elements."; `colon_warning_state = (c == ':');` once a leading `^` is read; `colon_warning_state |= 8;` at a class,
  an equivalence class, a collating element and a range; `colon_warning_state |= (c == ':') ? 2 : 4;` at every other
  member; and `if (colon_warning_state == 7)`, the message *"character class syntax is [[:space:]], not [:space:]"*,
  an error under `DFA_CONFUSING_BRACKETS_ERROR`, else a warning.

## Measured here

Each engine as installed on the planning machine or built in this repository's gitignored scratch, 2026-10-01 —
a reference implementation run at a named version, which is the primary source §2 of the research skill names.

- **Rust**, regex-syntax 0.8.11 and regex 1.13.1, built with rustc 1.93.1 into scratch: `(?x)[a b]` is the class
  `a-b`, the space ignored; `(?x)[a#b]` is "unclosed character class", the `#` beginning a comment inside the class;
  `(?xx)a` is "duplicate flag". Class operators: `[a&&a~~b]` is `a-b` and `[ab~~b--a]` is the empty class — left to
  right at one precedence, where Y-17's order gives `a` for each. `[&&a]`, `[a&&]` and `[a--]` are accepted, the empty
  side the empty set. `[]` and `[^]` are unclosed (a `]` first is a member); `[--a]` is `-` and `a`; `[]-a]` is `]`,
  `-` and `a`; `[a-c-e]` is `a-c`, `-` and `e`; `[\w-.]` and `[a-\d]` are "invalid range boundary, must be a
  literal"; `[[:foo:]]` and `[[:alpha]]` are nested classes of their bytes, not errors; `[:alpha:]` is a class of
  `:`, `a`, `h`, `l`, `p`; `\p1` and `[\p{}]` parse and fail at translation, "Unicode property not found".
- **Perl** 5.38.2: `(?x)[a b]` matches a space, `(?xx)[a b]` does not, and `(?x)[a#b]` matches `#`. `[]-a]` is the
  range `]`–`a`, `[--a]` the range `-`–`a`, and `[!--]` the range `!`–`-`.
- **Python** 3.12.3: `(?x)[a b]` matches a space and `(?x)[a#b]` matches `#`; `(?xx)a` compiles. `[]-a]`, `[--a]`
  and `[!--]` read as Perl reads them; `[\w-a]` is "bad character range".
- **Java** 21.0.12.1: `(?x)[a b]` does not match a space, and `(?x)[a#b]` is "Unclosed character class".
- **.NET** 10.0.12, `RegexOptions.IgnorePatternWhitespace`: `[a b]` matches a space and `[a#b]` matches `#` — both
  members, as its documentation says of white space and leaves to be inferred of `#`.
- **ECMAScript**, node 24.21.0 (V8): `[]` matches nothing and `[^]` any single byte — a `]` straight after `[` ends
  the class — so `[]a]` is that empty class followed by `a]`. Rust, Perl and Python read `[]a]` as a class of `]` and
  `a` (above and below), and `[]` as unclosed.
- **GNU `grep`** 3.11, run as `/usr/bin/grep` — in an agent's shell `grep` is a function that runs ugrep, so the path
  is named — on thirty-one shapes. Exit 2, *"character class syntax is [[:space:]], not [:space:]"*, for `[:alpha:]`,
  `[:foo:]`, `[^:alpha:]`, `[:a,b:]`, `[:;:]`, `[:9:]`, `[:^alpha:]`, `x[:alpha:]y`, `[:a:]`, `[:^:]`, `[: :]`,
  `[:é:]`, `[:\:]`, `[:\d:]`, `[:foo\:]` and `[:a&&b:]`; a bracket expression of its members — exit 0 or 1 — for
  `[::]`, `[:]`, `[:alpha]`, `[a:alpha:]`, `[:alpha:a]`, `[:::]`, `[^:::]`, `[:-:]`, `[:a-z:]`, `[:[:alpha:]:]`,
  `[:[.a.]:]`, `[:[a]:]`, `[]:a:]`, `[:]:]` and `[\:foo:]`. The rule is the one gnulib's `lib/dfa.c` states beside
  `colon_warning_state` (read at its master, copyright 1988 … 2026): *"Bit 0 = first character is a colon. Bit 1 =
  last character is a colon. Bit 2 = includes any other character but a colon. Bit 3 = includes ranges, char/equiv
  classes or collation elements"*, the error raised when the state is exactly the first three — so a bracket
  expression of colons alone, or one holding a range or a class, is read as written. A `\` in a bracket expression is
  a member, so `[:foo\:]` and `[:\d:]` are refused, and `&&` is two members. Rust reads all thirty-one as classes.

## What would change this

1. **Triggered.** Rust ignores whitespace inside a bracketed class under `x`, and `#` comments there too: O-Y2's
   premise *"Rust does not"* and `COMPAT.md` §2's row *"`x` mode inside classes | whitespace significant |
   whitespace significant | same"* are false, and the question is to be decided on other grounds.
2. **Triggered.** Rust's operators bind equally, left to right, union tighter and negation looser; Y-17's ranking
   reads `[a&&a~~b]` and `[ab~~b--a]` otherwise, with no row in `COMPAT.md` §2 saying so.
3. **Partly triggered.** UTS #18 does spell symmetric difference `~~`, so Y-16's attribution holds. It requires no
   precedence; its own example syntax binds every operator at one level, and it names union binding tighter as the
   other choice.
4. **For the same plan, not asked of the researcher:** had GNU `grep` read `[:alpha:]` as a class of its bytes, as
   Rust does, refusing it would have no precedent in a tool this library's first consumer reimplements (RX-101). It
   refuses it, and the shape it refuses is wider than the fourteen names — and narrower than every bracket expression
   whose members begin and end with `:`: colons alone, a range or a class in it, and it reads the members as written.

## Confidence and gaps

High for every engine row: the Rust sentence came back word for word from two fetches and the parser source agrees,
and the scratch builds confirm Rust, Perl, Python and Java at the versions named. GNU `grep`'s rule is read in
gnulib's `dfa.c` at its master, not at the 3.11 tag; the 3.11 binary agrees with it on all thirty-one shapes. Gaps:
`regex`'s own `RegexBuilder::nest_limit` default was not fetched (250 is regex-syntax's AST parser's); PCRE2 10.49's
release date is inferred (the page showed no year; its man page is dated 08 December 2025); the .NET article is
versioned by date and docs commit, not by release; whether a draft UTS #18 revision 26 exists was not checked; Rust's
acceptance of UTS #18's `||` was not checked. The locally installed Perl, Python and Java are older than the
documentation read; each agrees with its documentation on every point measured.
# §8's escapes, `\g`, `\b{…}` and an escape of text in the reference engines — research digest

**As of 2026-10-01.** Question: how do Rust's `regex` and the backtracking engines read the escapes `SYNTAX.md` §8
declines — `\1` … `\9`, `\k`, `\G`, `\Z`, `\Q` and `\E` — outside a class and inside one; how do they read `\g`, which
no rule of nregex names, and `\b` or `\B` before braces; how does Rust's `regex` escape a text, and what is its `R`
flag? *(Asked by the planner of `roadmap/0.1/0.1.5.md` for its PD-53 … PD-57; answered by running each engine at a
named version — the reference implementation run, which the research skill's §2 counts as primary — and by the Rust
crates' own source as published on crates.io. The planner ran it inline in this repository's gitignored scratch, every
engine local, no fetch: the Rust crates are the ones cycle 0.1.3's planner fetched, regex 1.13.1 and regex-syntax
0.8.11.)*

## Answer

Outside a class, every engine that reads `\1` … `\9` reads a backreference, and Rust's `regex` 1.13.1 refuses each,
*"backreferences are not supported"*; `\10` is three things — group 10 in Python, group 1 and `0` in Java, octal or a
group in Perl and PCRE2 by how many groups precede it. `\k<n>`, `\k'n'` and `\k{n}` are named backreferences in Perl
5.38.2 and PCRE2 10.42, `\k<n>` in Java 21.0.12.1 and node 24.21.0, and refused by Python 3.12.3 and Rust; `\k` before
anything else is an error wherever `\k` means something. `\G` and `\Z` are anchors in Perl, PCRE2 and Java and refused
by Rust and node under `u`; Python refuses `\G`, and `\Z` itself is read three ways — the end or before a final `\n` in Perl and
PCRE2, the end or before any final line end (`\r\n`, U+2028 …) in Java, and the end alone in Python. `\Q…\E` quotes in
Perl, PCRE2 and Java, in a class too; a lone `\E` is ignored by Perl (with a warning) and PCRE2 and refused by Java,
Python, Rust and node under `u`. `\g1`, `\g{1}`, `\g{-1}` and `\g{name}` are backreferences in Perl and PCRE2, and
`\g<1>` and `\g'1'` a call of group 1 in PCRE2, refused by Perl; every other engine refuses `\g`. **Inside a class no
engine reads a group or a position**: `[\1]` … `[\7]` are octal in Perl, PCRE2, Python and node without `u`, refused by
Java, Rust and node with `u`; `[\8]` is `8` in Perl and PCRE2; `[\k]`, `[\G]` and `[\Z]` the letter in Perl, refused by
PCRE2, Python, Java and Rust; `[\g]` `g` in Perl and PCRE2. `(?#c)` is a comment in Perl, PCRE2 and Python and refused by
Java and Rust. `\b{start}`, `\b{end}`, `\b{start-half}` and `\b{end-half}` are word assertions in Rust; `\b{wb}`,
`\b{sb}`, `\b{gcb}`, `\b{lb}` and `\B{wb}` Unicode boundaries in Perl, which refuses any other name in the braces,
`\b{2}` included; PCRE2 and Python read `\b` and then the braces as text. Rust's `regex::escape` writes a `\` before
eighteen bytes and leaves white space bare, which `(?x)` then skips; its `R` flag is CRLF mode.

## Evidence

- **Rust's `regex` 1.13.1**, its crate documentation in `src/lib.rs` of the package crates.io serves (rendered at
  <https://docs.rs/regex/1.13.1/regex/>), read in this repository's scratch, 2026-10-01:
  - "`R     enables CRLF mode: when multi-line mode is enabled, \r\n is used`"
  - "When both CRLF mode and multi-line mode are enabled, then `^` and `$` will match either `\r` or `\n`, but never in
    the middle of a `\r\n`"
  - "`\b{start}, \<   a Unicode start-of-word boundary (\W|\A on the left, \w on the right)`", "`\b{end}, \>     a
    Unicode end-of-word boundary (\w on the left, \W|\z on the right))`", "`\b{start-half}  half of a Unicode
    start-of-word boundary (\W|\A on the left)`", "`\b{end-half}    half of a Unicode end-of-word boundary (\W|\z on
    the right)`"
- **regex-syntax 0.8.11**, `src/lib.rs`, the same package source, 2026-10-01:
  - `escape_into`: "`if is_meta_character(c) { buf.push('\\'); }`" — and `is_meta_character`: "`'\\' | '.' | '+' |
    '*' | '?' | '(' | ')' | '|' | '[' | ']' | '{' | '}' | '^' | '$' | '#' | '&' | '-' | '~' => true,`"
  - "This will append escape characters into the given buffer. The characters that are appended are safe to use as a
    literal in a regular expression."

## Measured here

Each engine as installed on the planning machine, or built in this repository's gitignored scratch, 2026-10-01; each
pattern searched in the haystack beside it, or compiled. Rust's column is regex-syntax's parser and translator; PCRE2
is GNU `grep` 3.11's `-P`, one haystack a line, NUL-terminated (`-z`). `—` where a run was not made.

**§8's escapes, and `\g`, outside a class**:

| shape | haystack | Rust 1.13.1 | Perl 5.38.2 | Python 3.12.3 | Java 21.0.12.1 | node 24.21.0 `u` | PCRE2 10.42 |
|---|---|---|---|---|---|---|---|
| `(a)\1` | `aa` | refused, "backreferences are not supported" | 0..2 | 0..2 | 0..2 | 0..2 | 0..2 |
| `\1` | `a` | refused, the same | refused, nonexistent group | refused, invalid group reference | no match | refused | refused, non-existent subpattern |
| `(a)\10` | `aa0` | refused at `\1` | no match | refused, group 10 | 0..3 | refused | no match |
| `(?<n>a)\k<n>` | `aa` | refused, unrecognized escape | 0..2 | refused (`(?<`) | 0..2 | 0..2 | 0..2 |
| `(?<n>a)\k'n'`, `\k{n}` | `aa` | refused | 0..2 | refused | refused | refused | 0..2 |
| `\k`, `\kx` | — | refused | refused, not terminated | refused, bad escape | refused | refused | refused |
| `\G` | `a` | refused | 0..0 | refused | 0..0 | refused | 0..0 |
| `a\Z` | `a⏎` | refused | 0..1 | no match | 0..1 | refused | 0..1 |
| `a\Z` | `a`, CR, LF | refused | no match | no match | 0..1 | refused | no match |
| `\Qa.b\E` | `a.b`; `axb` | refused | 0..3; no match | refused | 0..3; no match | refused | 0..3; no match |
| `a\E`, `\E` | `a`; `E` | refused | 0..1; 0..0, "Useless use of \E" | refused | refused | refused | 0..1; 0..0 |
| `(a)\g1`, `\g{1}`, `\g{-1}` | `aa` | refused | 0..2 | refused | refused | refused | 0..2 |
| `(?<n>a)\g{n}` | `aa` | refused | 0..2 | refused | refused | refused | 0..2 |
| `(a)\g<1>`, `\g'1'` | `aa` | refused | refused, unterminated | refused | refused | refused | 0..2, a call of group 1 |
| `\g`, `\gx` | — | refused | refused | refused | refused | refused | refused |
| `(?#c)a` | `a` | refused, unrecognized flag | 0..1 | 0..1 | refused | refused | 0..1 |

**The same escapes inside a class**:

| shape | haystack | Rust | Perl | Python | Java | node `u`; without | PCRE2 |
|---|---|---|---|---|---|---|---|
| `[\1]` | U+0001; `1` | refused, a backreference | 0..1; no match | 0..1; no match | refused | refused; 0..1 | 0..1; no match |
| `[\7]` | U+0007 | refused | 0..1 | 0..1 | refused | refused; 0..1 | 0..1 |
| `[\12]` | LF; `1` | refused | 0..1; no match | 0..1; no match | refused | refused; 0..1, no match | 0..1; no match |
| `[\18]` | U+0001; `8` | refused | 0..1; 0..1 | 0..1; 0..1 | refused | refused; 0..1 | 0..1; 0..1 |
| `[\8]` | `8` | refused | 0..1, "passed through" | refused | refused | refused; 0..1 | 0..1 |
| `[\k]`, `[\G]`, `[\Z]` | the letter | refused | 0..1, "passed through" | refused | refused | refused; 0..1 | refused |
| `[\g]` | `g` | refused | 0..1, "passed through" | refused | refused | refused; 0..1 | 0..1 |
| `[\Qa]\E]` | `]` | refused | 0..1 | refused | 0..1 | refused; no match | 0..1 |
| `[\Q]`, `[\E]` | the letter | refused | refused, unmatched `[` | refused | refused | refused; 0..1 | refused, missing `]` |

**`\b` and `\B` before braces**:

| shape | haystack | Rust | Perl | Python | Java | node `u` | PCRE2 |
|---|---|---|---|---|---|---|---|
| `\b{start}a` | `a` | a start-of-word assertion | refused, "'start' is an unknown bound type" | no match: `\b`, then the text `{start}a` | refused | refused | no match, the same |
| `\b{wb}a` | `a` | refused, "valid choices are: start, end, start-half or end-half" | 0..1, a Unicode word boundary | no match | refused | refused | no match |
| `\b{sb}a`, `\b{gcb}a`, `\b{lb}a`, `\B{wb}a` | `a` | — | each accepted | — | — | — | — |
| `\b{2}a` | `a` | `\b` repeated | refused, "'2' is an unknown bound type" | refused, nothing to repeat | 0..1 | refused | refused, not a repeatable item |
| `\B{start}a` | `a` | refused, a bad repetition count | refused | no match | refused | refused | no match |

**Rust's escape under `x`**: regex-syntax reads `(?x)a b` as `ab` — so `regex::escape("a b")`, which writes `a b`,
matches `ab` there.

## What would change this

1. **Triggered.** Had an engine read `\1` … `\9` outside a class as anything but a backreference, or a lone `\E` as
   anything but the end of a quotation, PD-53's kinds would be wrong for it; none does.
2. **Triggered.** Had no engine read `\g`, it would stay a letter no rule names; Perl and PCRE2 read backreferences and
   PCRE2 a call of a group, so PD-54 refuses it by those kinds.
3. **Triggered.** Had an engine read a group or a position inside a class, `[\1]` would be a backreference here too;
   none does, and four read octal, so it stays `UnknownEscape` with a sentence about octal.
4. **Triggered.** Had Rust's `regex::escape` escaped white space, PD-55 would take its set as it is; it does not, and
   `(?x)` skips what it leaves.
5. **Triggered.** Had no engine read `\b{…}`, the bad bound's sentence would stand; Rust and Perl read two different
   things there, so PD-57 names both.

## Confidence and gaps

High for every measured row: each was run at the version named, and Rust's rows agree with the crate's source. Gaps:
`.NET` was not run, as for cycle 0.1.4's digest (the sandbox refuses its SDK's mutex under `/tmp`); Perl's own
documentation is not installed, so its rows are measurements alone; node's rows read the `u` flag, the mode a pattern
written for a Unicode library would use, with its legacy reading beside it where it differs; Perl's `\Q` was read as a
pattern literal — `qr/…/` — where it works, since a `\Q` in a string interpolated at run time is not a quotation in
Perl at all.

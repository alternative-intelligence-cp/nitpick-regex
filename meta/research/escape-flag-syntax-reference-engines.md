# Escapes, flags, `x` and `(?-u)` in the reference engines — research digest

**As of 2026-10-01.** Question: how do Rust's `regex` and the backtracking engines read the escapes of `SYNTAX.md` §1,
the inline flags, `x` mode outside a class, and `(?-u)` — where do they agree, and where do they read one pattern two
ways? And which codepoints past ASCII are white space to them under `x`? *(Asked by the planner of
`roadmap/0.1/0.1.4.md` for its PD-48 … PD-52; answered by running each engine at a named version — the reference
implementation run, which the research skill's §2 counts as primary — by the Rust crates' own documentation and source
as published on crates.io, and by the UCD's `PropList.txt` from the Unicode Consortium's own repository. The planner ran
it inline in this repository's gitignored scratch: one fetch per source, every engine local.)*

## Answer

Rust's `regex` 1.13.1 (regex-syntax 0.8.11) reads `\x41`, `\x{1F600}`, `A`, `\U0001F600`, the control escapes
`\a \t \n \v \f \r` and `\` before any ASCII that is neither a letter nor a digit — except `<` and `>` — as codepoints;
it also accepts `\u{…}` and `\U{…}`, and refuses `\e` and `\0`. It reads **`\<` and `\>` as start- and end-of-word
assertions**, where Perl 5.38.2, PCRE2 10.42, Python 3.12.3 and Java 21.0.12.1 read the bytes `<` and `>` and node
24.21.0 refuses them under `u`; GNU `grep` 3.11 reads them as word boundaries too. The engines part on `\0` before a
digit (octal in Perl, PCRE2, Python and Java, refused by Rust), `\x4` (U+0004 in Perl and PCRE2, refused by Rust, Python
and Java), `[\b]` (a backspace in Perl, Python, PCRE2 and node, refused by Rust and Java) and `😀` (one
codepoint in Java and node, two lone surrogates in Python, refused by Rust). Inline flags: Rust refuses a flag named
twice, a `-` with nothing after it, a second `-` and `(?)`; a flag set by `(?i)` holds across `|` to the group's end in
Rust, Perl and PCRE2. Under `x`, all four engines run here skip the six ASCII white-space bytes and a `#` comment
**between** constructs; **inside** one they part (Rust skips white space inside `\x4 1`, `\x{ 41}`, `a{2, 3}`,
`( ?:a)` and before a lazy `?`; Perl, Python and Java each read some of those otherwise); and **past ASCII** they part
again (Rust skips Unicode's White_Space, Perl its Pattern_White_Space, Python and Java ASCII white space alone). Under
`(?-u)`, Rust reads `é` and `\x{E9}` as é's two UTF-8 bytes but `\xE9` as the one byte E9, and refuses `[é]` and
`\pL`. White_Space and Pattern_White_Space are the same in UCD 16.0.0, 17.0.0 and 18.0.0, and 18.0.0 is the latest
version.

## Evidence

- **Rust's `regex` 1.13.1**, its crate documentation — `src/lib.rs` of the package crates.io serves, which docs.rs
  renders at <https://docs.rs/regex/1.13.1/regex/> — read in the package cargo fetched into this repository's scratch,
  2026-10-01:
  - "`\b{start}, \<   start-of-word boundary assertion`", "`\b{end}, \>     end-of-word boundary assertion`"
  - "`\123            octal character code, up to three digits (when enabled)`"
  - "`\x7F            hex character code (exactly two digits)`", "`\x{10FFFF}      any hex character code corresponding
    to a Unicode code point`", "`\u007F          hex character code (exactly four digits)`", "`\u{7F}          any hex
    character code corresponding to a Unicode code point`", "`\U0000007F      hex character code (exactly eight
    digits)`"
  - "Note that in verbose mode, whitespace is ignored everywhere, including within character classes."
- **regex-syntax 0.8.11**, `src/lib.rs`, `is_escapeable_character` — the same, 2026-10-01: "Otherwise, we basically say
  that everything is escapable unless it's a letter or digit."; "While not currently supported, we keep these as not
  escapable to give us some flexibility with respect to supporting the \< and \> word boundary assertions in the
  future."; "OK, now we support \< and \>, and we need to retain them as *not* escapable here since the escape sequence
  is significant."
- **The UCD's `PropList.txt`**, from the Consortium's own repository,
  <https://raw.githubusercontent.com/unicode-org/unicodetools/main/unicodetools/data/ucd/18.0.0/PropList.txt> ("#
  PropList-18.0.0.txt", "# Date: 2026-08-07, 16:20:14 GMT") and the same path at `16.0.0` and `17.0.0` — retrieved
  2026-10-01; the White_Space and Pattern_White_Space lines identical in all three:
  - "`0009..000D ; White_Space`", "`0020 ; White_Space`", "`0085 ; White_Space`", "`00A0 ; White_Space`", "`1680 ;
    White_Space`", "`2000..200A ; White_Space`", "`2028 ; White_Space`", "`2029 ; White_Space`", "`202F ;
    White_Space`", "`205F ; White_Space`", "`3000 ; White_Space`"
  - "`0009..000D ; Pattern_White_Space`", "`0020 ; Pattern_White_Space`", "`0085 ; Pattern_White_Space`",
    "`200E..200F ; Pattern_White_Space`", "`2028 ; Pattern_White_Space`", "`2029 ; Pattern_White_Space`"
- <https://www.unicode.org/versions/latest/> — retrieved 2026-10-01: answered 302, `Location:
  http://www.unicode.org/versions/Unicode18.0.0/`.

## Measured here

Each engine as installed on the planning machine, or built in this repository's gitignored scratch, 2026-10-01.
`.NET` was not run: its SDK's restore takes a named mutex under `/tmp/.dotnet`, which the workbench's sandbox refuses;
its readings below are its documentation's, from `class-syntax-reference-engines.md`.

**Escapes** — each pattern searched in a haystack holding what it should name:

| shape | Rust 1.13.1 | Perl 5.38.2 | Python 3.12.3 | Java 21.0.12.1 | node 24.21.0 (`u`) | PCRE2 10.42 (`grep -P`) |
|---|---|---|---|---|---|---|
| `\e` | refused, unrecognized escape | U+001B | refused, bad escape | U+001B | refused | U+001B |
| `\0` | refused, "backreferences are not supported" | U+0000 | U+0000 | refused, illegal octal escape | U+0000 | — |
| `\012` | refused | U+000A | U+000A | U+000A | refused, invalid decimal escape | — |
| `\08` | refused | U+0000 then `8` | U+0000 then `8` | refused | — | — |
| `\x4` | refused, end of pattern | U+0004 | refused, incomplete escape | refused | refused | U+0004 |
| `\x{1F600}` | U+1F600 | U+1F600 | refused | U+1F600 | — | — |
| `\x{4 1}` | refused at the space | — | — | — | — | — |
| `\x{110000}`, `\x{D800}` | refused, not a Unicode scalar value | — | — | — | — | — |
| `\u{41}` | `A` | nothing matched (`\u` changes case) | refused | refused | `A` | — |
| `\U0001F600` | U+1F600 | nothing matched (`\U` changes case) | U+1F600 | refused | — | — |
| `😀` | refused at the first | nothing matched | nothing matched | U+1F600 | U+1F600 | — |
| `\<`, `\>` on `a <b>` | positions 0, 3 and 1, 4 — word assertions | `<` at 2, `>` at 4 | the same | the same | refused | `<` |
| `[\<]` | refused, invalid class escape | `<` | `<` | `<` | — | — |
| `\ ` (a space) | a space | a space | a space | a space | refused | — |
| `\é` | refused | `é` | `é` | `é` | — | — |
| `[\b]` | refused, invalid class escape | U+0008 | U+0008 | refused | U+0008 | — |
| `\c`, `\i`, `\q`, `\y`, `\L`, `\T`, … | refused | most the letter itself | refused, bad escape | refused | refused | — |

GNU `grep` 3.11 `-E` (ERE) reads `\<` and `\>` as word boundaries and `` \` `` and `\'` as the buffer's ends; Rust,
Perl, Python and Java read `` \` `` and `\'` as the bytes.

**Flags** — Rust 1.13.1: `(?ii)`, `(?i-i)`, `(?-ii)`, `(?xx)`, `(?ix-ims)` "duplicate flag"; `(?-)`, `(?i-)`,
`(?i-:a)` "dangling flag negation operator"; `(?--i)`, `(?i-m-s)` "flag negation operator repeated"; `(?)` and `(?i)*`
"repetition operator missing expression"; `(?q)`, `(?^)`, `(?a)`, `(?n)`, `(?P)`, `(?i x)` "unrecognized flag" — and
under `x` too, `(?x)(?i x)`; `(?i` "expected flag but got end of regex"; `(?U)` swaps greed and `(?R)` is CRLF mode.
`a(?i)b|c` matches `C` in Rust, Perl and PCRE2; `(a(?i)b)c` matches `aBc` and not `aBC` in Rust and PCRE2.

**`x` outside a class** — the haystack after the arrow, `—` where a run was not made:

| shape | Rust | Perl | Python | Java |
|---|---|---|---|---|
| `(?x)a b`, `(?x)a # c⏎b`, `(?x)a \| b`, `(?x)a *`, `(?x)a#c⏎*` | skipped | skipped | skipped | skipped |
| VT, FF, CR, TAB between `a` and `b` | skipped | skipped | skipped | skipped |
| `(?x)\x4 1` | `A` | U+0004 then `1` | refused | `A` |
| `(?x)\x{ 41}` | `A` | `A` | refused (no braces) | `A` |
| `(?x)a{2, 3}` | `a{2,3}` | `a{2,3}` | the text `a{2,3}` | `a{2,3}` |
| `(?x)a{ 2}` | `a{2}` | `a{2}` | the text | refused |
| `(?x)( ?:a)` | non-capturing | refused | refused, nothing to repeat | non-capturing |
| `(?x)a* ?` | lazy `a*?` | lazy | refused, multiple repeat | lazy |
| U+00A0 between `a` and `b` | skipped | `a` U+00A0 `b` | `a` U+00A0 `b` | `a` U+00A0 `b` |
| U+3000 | skipped | as itself | as itself | as itself |
| U+2028, U+0085 | skipped | skipped | as itself | as itself |
| U+200E | as itself | skipped | as itself | as itself |

**`(?-u)`** — Rust 1.13.1, regex-syntax with `utf8` off: `(?-u)é`, `(?-u)\x{E9}` and `(?-u)é` are é's UTF-8 bytes;
`(?-u)\xE9` the byte E9; `(?-u)\x{FF}` ÿ's bytes, `(?-u)\x{100}` Ā's; `(?-u)[é]`, `(?-u)\pL` and `(?-u)\p{Greek}`
refused, "Unicode not allowed here"; `(?-u)\w` `[0-9A-Z_a-z]`, `(?-u).` any byte but `\n`.

## What would change this

1. **Triggered.** Had Rust read `\<` and `\>` as the bytes, Y-2's reading would be every engine's and PD-49 needless;
   Rust reads word assertions, so a pattern written for it would compile here and match `<`.
2. **Triggered.** Had the engines agreed on white space inside a construct under `x`, the plan would follow them; they
   do not, so Y-42 skips white space only where all four do.
3. **Triggered.** Had one white-space set past ASCII been every engine's, the plan would read it; Rust, Perl and
   Python/Java hold three, so Y-42 refuses their union.
4. **Triggered.** Had Rust read `\x{E9}` under `(?-u)` as the byte E9, one rule would serve every hex escape; it reads
   é's two bytes, so PD-52 refuses it.
5. **Not triggered.** Had Rust read `\0` and a digit as octal, `\012` would have one more reading to weigh; it refuses
   it, and the backtracking engines' octal is refused here with the hex form named.

## Confidence and gaps

High for every measured row: each was run at the version named, and the Rust readings agree with the crate's own
documentation and source. Gaps: `.NET` not run (the sandbox, above); Perl's `perlre` not read — its documentation is
not installed — so its rows are measurements alone; PCRE2 was run as GNU `grep -P`'s 10.42, older than the 10.49 the
class digest read, and only on the shapes it could show line by line; the installed Perl, Python and Java are older
than their current releases, and the plan's rules rest on Rust's and on agreement, not on any one of them; whether
Unicode 18.0.0 changed any other property the parser names was not asked — the parser names no other.

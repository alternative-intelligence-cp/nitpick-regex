# Currency — the facts from outside the compiler tree this plan rests on

One row per standard, data release, corpus or reference implementation the plan
names, with the version pinned, the day it was checked, the primary source, and
the decision that pins it (the workbench research skill's §7). A row unchecked
for six months is stale; a cycle whose rows are unchecked is not ready to start.
The Unicode data, the corpora and the reference engines join this table at the
cycles that first depend on them (0.3, 0.5, 0.9).
*(2026-10-01, cycle 0.1.3's plan: Rust's `regex` joins early, as the reference for a
class's syntax — its engines are still cycle 0.9's.)*
*(2026-10-01, cycle 0.1.4's plan: and two properties of the UCD join early too — White_Space and
Pattern_White_Space, which name the white space `x` skips or refuses; the tables are still cycle 0.3's.)*
*(2026-10-01, cycle 0.1.5's plan: and the published algorithms for lookaround, which decide what a refusal of it may
say — nregex's engines are still cycle 0.6's onward.)*

| Depends on | Pinned | Checked | Source | Decision |
|---|---|---|---|---|
| well-formed UTF-8 — what a pattern must be (`SYNTAX.md` Y-11, Y-28) | RFC 3629 (STD 63, November 2003), §4's ABNF | 2026-09-27 | rfc-editor.org/rfc/rfc3629 — [`utf8-rfc3629.md`](utf8-rfc3629.md) | `roadmap/0.1/0.1.1.md` PD-27 |
| Rust's `regex` — a class's syntax, `x` mode inside a class, the class operators' precedence (`SYNTAX.md` Y-16, Y-17, §4; `COMPAT.md` §2) | regex 1.13.1, regex-syntax 0.8.11 | 2026-10-01 | docs.rs/regex; github.com/rust-lang/regex at tags 1.13.1 and regex-syntax-0.8.11; and built and run here — [`class-syntax-reference-engines.md`](class-syntax-reference-engines.md) | `roadmap/0.1/0.1.3.md` PD-40, PD-41, PD-45 |
| UTS #18 — the class set operations' spellings and precedence (`SYNTAX.md` Y-16, Y-17) | revision 25 (2025-01-16) | 2026-10-01 | unicode.org/reports/tr18 — [`class-syntax-reference-engines.md`](class-syntax-reference-engines.md) | `roadmap/0.1/0.1.3.md` PD-40 |
| GNU `grep` — a POSIX class written as a whole bracket expression (`SYNTAX.md` Y-38; `COMPAT.md` §2) | 3.11 | 2026-10-01 | `/usr/bin/grep`, run here on thirty-one shapes; gnulib's `lib/dfa.c`, its `colon_warning_state`, read at master — [`class-syntax-reference-engines.md`](class-syntax-reference-engines.md) | `roadmap/0.1/0.1.3.md` PD-44 |
| ECMAScript — a `]` first in a class (`SYNTAX.md` Y-36) | node 24.21.0 (V8) | 2026-10-01 | run here — [`class-syntax-reference-engines.md`](class-syntax-reference-engines.md) | `roadmap/0.1/0.1.3.md` PD-41 |
| Perl, PCRE2, Python, .NET and Java — whether `x` mode reaches inside a class (`COMPAT.md` §3) | Perl 5.44.0, PCRE2 10.49, Python 3.14.8, .NET's options article of 2026-07-08, Java SE 27 | 2026-10-01 | perldoc.perl.org/perlre; pcre2.org; docs.python.org; learn.microsoft.com; docs.oracle.com — [`class-syntax-reference-engines.md`](class-syntax-reference-engines.md) | `roadmap/0.1/0.1.3.md` PD-45 |
| Rust's `regex` — every escape, the inline flags, `x` outside a class, `(?-u)` (`SYNTAX.md` Y-40 … Y-43; `COMPAT.md` §2) | regex 1.13.1, regex-syntax 0.8.11 | 2026-10-01 | the crates' documentation and source as crates.io serves them (docs.rs/regex/1.13.1); built and run here — [`escape-flag-syntax-reference-engines.md`](escape-flag-syntax-reference-engines.md) | `roadmap/0.1/0.1.4.md` PD-48 … PD-52 |
| Perl, Python, Java, node and PCRE2 — the same shapes, and GNU `grep`'s `\<` (`COMPAT.md` §3) | Perl 5.38.2, Python 3.12.3, Java 21.0.12.1, node 24.21.0, PCRE2 10.42 through GNU `grep` 3.11 | 2026-10-01 | run here — [`escape-flag-syntax-reference-engines.md`](escape-flag-syntax-reference-engines.md) | `roadmap/0.1/0.1.4.md` PD-48 … PD-52 |
| Unicode's White_Space and Pattern_White_Space — the white space `x` skips or refuses (`SYNTAX.md` Y-42) | UCD 18.0.0 `PropList.txt`, the latest release; the same in 16.0.0 and 17.0.0 | 2026-10-01 | unicode.org/versions/latest; github.com/unicode-org/unicodetools, the Consortium's own repository, at `unicodetools/data/ucd/<version>/PropList.txt` — [`escape-flag-syntax-reference-engines.md`](escape-flag-syntax-reference-engines.md) | `roadmap/0.1/0.1.4.md` PD-51 |
| Rust's `regex` — §8's escapes, `\g`, `\b{…}`, the `R` flag and `regex::escape` (`SYNTAX.md` Y-44, Y-45; `COMPAT.md` §2) | regex 1.13.1, regex-syntax 0.8.11 | 2026-10-01 | the crates' source as crates.io serves them (docs.rs/regex/1.13.1); built and run here — [`refusal-syntax-reference-engines.md`](refusal-syntax-reference-engines.md) | `roadmap/0.1/0.1.5.md` PD-53 … PD-57 |
| Perl, PCRE2, Python, Java and node — the same shapes, outside a class and in one (`COMPAT.md` §3) | Perl 5.38.2, PCRE2 10.42 through GNU `grep` 3.11, Python 3.12.3, Java 21.0.12.1, node 24.21.0 | 2026-10-01 | run here — [`refusal-syntax-reference-engines.md`](refusal-syntax-reference-engines.md) | `roadmap/0.1/0.1.5.md` PD-53, PD-54, PD-56, PD-57 |
| matching lookahead and lookbehind in linear time — what `LookaroundUnsupported`'s sentence may claim (`COMPAT.md` K-1) | Mamouras and Chattopadhyay, POPL 2024 (PACMPL 8, Art. 92); Barrière and Pit-Claudel, PLDI 2024 (PACMPL 8, Art. 201); V8's linear engine reads captureless lookbehinds behind a flag, and .NET's `NonBacktracking` no lookaround | 2026-10-01 | the papers, in their authors' copies; V8's source at `main`; .NET's options article — [`lookaround-linear-time.md`](lookaround-linear-time.md) | `roadmap/0.1/0.1.5.md` PD-56 |

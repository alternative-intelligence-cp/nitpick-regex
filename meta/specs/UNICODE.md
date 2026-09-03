# Unicode

Properties, scripts, case folding, and where the tables come from.

---

## 1. The tables

**Rule U-1 (RX-021) — the tables are generated from a pinned UCD and committed
as Nitpick source.** `tools/gen_unicode.py` reads the Unicode Character
Database and writes `src/unicode/*.npk`. A build needs the compiler and nothing
else: no Python, no network, no `/usr/share/unicode`.

**Rule U-2 — the generator is checked, not trusted.** The harness re-runs it
and requires the committed tables to be **byte-identical** to what it would
emit. A generated file that has been hand-edited is the failure this prevents,
and it is the same instrument the compiler uses for its builtin signature
table.

**Rule U-3 — the version lives in exactly one file**,
`src/unicode/version.npk`, as `pub fixed string:UNICODE_VERSION`, and appears
in the header comment of every generated file. Upgrading it is a recorded
decision with a regenerated table set and a re-run corpus, because a property
that changes is a set of patterns that match differently.

> The version to pin is **the latest stable UCD at the time cycle 0.3 runs**,
> and the plan records the one actually used rather than guessing now. There is
> no floor: unlike a grapheme segmenter, nothing here needs a property that
> arrived in a particular release.

**Rule U-4 — the representation is a sorted disjoint range array**, the same
shape a class uses, so a property lookup and a class test are the same code:

```nitpick
pub struct:ClassRange = { uint32:lo; uint32:hi; };   // inclusive, sorted, disjoint
```

Not a trie, and deliberately: a binary search over a sorted disjoint range
array has one invariant (`lo <= hi`, each `lo` above the previous `hi`), that
invariant is checkable over the committed table in one pass, and the search's
bound is a single obligation for cycle 1.5. A trie is faster and has four
invariants nobody will state. **And the hot path does not use these tables at
all** — a class is compiled into the program (`COMPILE.md` §2), so the tables
are read at compile time only, which removes the usual argument for the trie.

---

## 2. Properties

**Rule U-5 (RX-023) — the supported set, exhaustively.**

| Form | Example | Source table |
|---|---|---|
| General_Category, long or short | `\p{Lu}`, `\p{Uppercase_Letter}` | `DerivedGeneralCategory.txt` |
| General_Category group | `\p{L}`, `\p{Letter}` | derived as the union |
| Script | `\p{Greek}`, `\p{Script=Greek}`, `\p{sc=Greek}` | `Scripts.txt` |
| Script_Extensions | `\p{Script_Extensions=Greek}`, `\p{scx=Greek}` | `ScriptExtensions.txt` |
| the standard binary properties | `\p{Alphabetic}`, `\p{White_Space}`, `\p{Uppercase}`, `\p{Lowercase}`, `\p{Default_Ignorable_Code_Point}`, … | `DerivedCoreProperties.txt`, `PropList.txt` |
| Age | *not supported* | — |
| Block | *not supported* | §2.1 |
| single-letter shorthand | `\pL`, `\PN` | the same |

**Rule U-6 — property and value names match loosely**, per UAX #44: case,
whitespace, `-` and `_` are ignored in both the property name and the value. So
`\p{Script=Old_Italic}`, `\p{sc=olditalic}` and `\p{SCRIPT = Old Italic}` are
one thing. The loose-matching function is generated with the tables and tested
against the UCD's own `PropertyAliases.txt` and `PropertyValueAliases.txt`.

**Rule U-7 — an unknown property or value is `UnknownUnicodeProperty` with the
byte offset**, never an empty class. An engine that silently matches nothing
for a typo'd property name turns a mistake into a pattern that quietly never
fires.

### 2.1 Blocks are not supported, deliberately

**Rule U-8.** `\p{InGreek}` and `\p{Block=Greek}` are refused. A Unicode block
is a range of codepoints assigned to a script *historically*, not a set of
characters used by one — Greek letters appear in four blocks and the Greek
block contains Coptic. Every use of a block in a real pattern is a bug that
happens to work for the author's test data, and `Script` or `Script_Extensions`
is what was meant. The refusal names them.

---

## 3. Perl classes, pinned

**Rule U-9.** "What is `\w`" differs between engines and is worth writing down.

| Class | Unicode mode | Byte mode `(?-u)` |
|---|---|---|
| `\d` | `\p{Nd}` | `[0-9]` |
| `\w` | `[\p{Alphabetic}\p{M}\p{Nd}\p{Pc}\p{Join_Control}]` | `[0-9A-Za-z_]` |
| `\s` | `\p{White_Space}` | `[\t\n\v\f\r ]` |

`\D`, `\W`, `\S` are the complements **within the relevant universe** — all
codepoints in Unicode mode, all 256 bytes in byte mode. This matters: `\W` in
Unicode mode includes `U+00E9`, and in byte mode includes the byte `0xC3`.

**Rule U-10 — `\w`'s definition is UTS #18's Annex C word-character set**, not
"letters and underscore". The `\p{M}` and `\p{Join_Control}` terms are what
make `\w+` match a Devanagari word or an emoji ZWJ sequence's joiner without
splitting it, and leaving them out is the most common way to get this wrong.

---

## 4. Case folding

**Rule U-11 (RX-022) — case-insensitive matching uses SIMPLE case folding at
1.0.** `CaseFolding.txt`'s `C` and `S` entries: a one-to-one codepoint mapping
applied to every range in a class when `i` is on.

**Rule U-12 — FULL case folding is refused by name**, not silently omitted.
Full folding maps one codepoint to several — `ß` folds to `ss`, `ﬁ` to `fi` —
which means a case-insensitive class stops being a set of codepoints and
becomes a set of *strings*. That is a different matching problem: it changes
the automaton from character-driven to sequence-driven, it changes what a match
offset means, and it interacts with `.` and with quantifiers in ways that need
their own specification.

A pattern that would depend on it is not detectable, so this is not a refusal
the compiler can issue — it is a **documented limitation** with the exact list
of affected codepoints published in `docs/`, and `COMPAT.md` §3 states which
engines do what. Rust's `regex` also does simple folding by default. Recorded
as O-U1.

**Rule U-13 — folding is applied to CLASSES, at HIR construction, and never at
match time.** `(?i)[a-z]` becomes the range list for `a-z` plus `A-Z` plus
`U+017F` (LATIN SMALL LETTER LONG S, which folds to `s`) plus `U+212A` (KELVIN
SIGN, which folds to `k`). The engine does no folding at all.

Those two codepoints are the reason folding must be a table lookup and not
`+/- 32`: `(?i)k` matching `U+212A` is correct Unicode behaviour and surprises
everybody. A test asserts both.

**Rule U-14 — folding a class is closed under the fold relation**, computed as
an orbit: for each codepoint in the class, add every codepoint that folds to
the same value. The generated table is the **inverse** fold map — from a fold
target to every codepoint that reaches it — because that is the direction the
computation needs and deriving it at run time would be a scan of the whole
table per class.

---

## 5. Word boundaries

**Rule U-15.** `\b` is a position where exactly one of the two adjacent
positions holds a word character, `\w` per U-9, with the haystack's start and
end counting as non-word. `\B` is its complement.

**Rule U-16 — in Unicode mode the adjacency is over CODEPOINTS, and the engine
sees bytes.** A boundary instruction must therefore decode backwards from the
current byte offset to find the preceding codepoint. UTF-8 is
self-synchronising — a continuation byte is `10xxxxxx` — so this is a bounded
backward scan of at most three bytes, and it is the only place in the engines
where a backward read happens. Stated because it is easy to implement as a
byte-level test and be wrong for every non-ASCII haystack.

**Rule U-17 — `\b` on an invalid UTF-8 boundary treats the invalid byte as a
non-word character.** Not an error, not a trap. §6.

---

## 6. The haystack, and invalid UTF-8

**Rule U-18 (RX-020) — matching is over BYTES, and a Unicode class is compiled
into a UTF-8 byte automaton** (`COMPILE.md` §2). The haystack is `uint8[]` and
is never validated.

**Rule U-19 — the consequences, stated exactly:**

- A Unicode-mode pattern **cannot match an invalid UTF-8 sequence**, because
  the byte automaton compiled from a codepoint class only accepts well-formed
  encodings. Invalid bytes simply never match; they are not an error.
- Every offset a Unicode-mode search reports therefore **lands on a UTF-8
  boundary**, by construction rather than by checking.
- A byte-mode `(?-u)` pattern matches bytes and its offsets may land anywhere.
- The two modes may be mixed in one pattern by `(?-u:…)`, and offsets from the
  Unicode parts are still boundaries.

**Rule U-20 — this is the reason for the byte decision** and it is worth the
extra work in the compiler: a library that could only search validated `string`
could not search a network buffer, a mapped file, or a log with one bad byte in
it — and those are the searches a systems library is asked to do. The
alternative, decoding codepoints as the engine runs, would need a decision about
what to do with an invalid byte *at match time*, on the hot path, in the middle
of an automaton.

`COMPILE.md` §2 has the cost: a class of many codepoints becomes a byte
automaton of several alternatives, and that automaton is what
`NREGEX_PROGRAM_INSTRUCTIONS` is really bounding.

---

## 7. Open items

- **O-U1 — full case folding.** Refused at 1.0 (U-12). It would be a cycle of
  its own and change the matching model. Recommendation: stay simple; revisit
  only with a concrete consumer.
- **O-U2 — the Unicode version to pin.** Decided at cycle 0.3 against what is
  published then. Not a design question.
- **O-X1 — the overlap with `nitpick-tui`.** Both libraries generate range
  tables from the same UCD, and both need `Vec` and `Bytes`. Today
  `[dependencies]` resolves to nothing (`BUILD.md` §1), so each carries its
  own. When resolution lands, whether a shared `nunicode` package is worth
  extracting is a real question with a real cost — a third repository, a third
  release cadence — and it is deferred to that point rather than pre-decided.

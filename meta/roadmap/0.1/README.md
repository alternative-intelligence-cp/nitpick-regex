# Cycle 0.1 — The pattern parser

**`src/syntax/`: pattern text to an AST, driven by an explicit stack, with a
byte offset on every error.**

> **`0.1.0.md` is written execution-grade at cycle 0.0's close** (0.0.5, step
> 5), so this cycle is openable by a session that was not present for the
> probes. That is the convention for every cycle: the opening subcycle file is
> written by the cycle before it.

## Why here

It is the first thing that reads a pattern, and everything downstream is
defined in terms of what it produces. It is also entirely pure computation over
a byte slice, so its whole suite is fixtures — no harness capability beyond
what 0.0 built.

## Decisions in

RX-010, RX-013, RX-017, RX-032, RX-060. Settled.

**Open questions to settle:** O-Y2 (does `x` mode ignore whitespace inside
classes? recommendation: no, matching Rust, and refuse `xx`).

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| [0.1.0](0.1.0.md) | **The cursor and the AST** — the byte cursor with offsets, the AST arena, the node kinds | a parser skeleton that accepts `a` and reports an offset for `(` |
| 0.1.1 | **The core grammar** — literals, concatenation, alternation, groups, quantifiers | `SYNTAX.md` §1's grammar minus classes |
| 0.1.2 | **The explicit stack** — nesting, `NREGEX_NEST_DEPTH`, and the refusal | 10 000 levels deep is a `NestTooDeep`, not a segfault |
| 0.1.3 | **Classes** — items, ranges, Perl and POSIX classes, nesting, `&&`/`--`/`~~` | every class form in §5, parsed to unresolved items |
| 0.1.4 | **Escapes and flags** — every escape in §1, flag scoping, `(?-u)` | the escape table, and `(?i)` scoped correctly |
| 0.1.5 | **The refusals** — every construct in §8, by name, with its offset | `BackreferenceUnsupported` names the guarantee, not "unsupported" |
| 0.1.6 | **Close** — `check_error_kinds_tested` live | `done/0.1/`, `0.2.0.md` written |

## Checklist

### 0.1.0 — the cursor and the AST
- [ ] a byte cursor over `uint8[]` with `offset`, `peek`, `bump`, `eat`, and **no lookahead beyond one byte** except where the grammar names it
- [ ] the AST as a flat POD arena indexed by `int32`, the same shape the HIR uses (`HIR.md` H-2) — a `Vec<AstNode>` reallocates and a pointer into it would dangle
- [ ] `PatternError` with `kind`, `offset`, `span_len`, `detail`
- [ ] every error constructed through one helper, so no site can forget the offset
- [ ] `NREGEX_PATTERN_BYTES` enforced before anything else runs

### 0.1.1 — the core grammar
- [ ] alternation, concatenation, groups (capturing, non-capturing, named), quantifiers (`*`, `+`, `?`, `{n}`, `{n,}`, `{n,m}`, each with a lazy `?`)
- [ ] capture numbering by opening parenthesis, left to right, from 1 (Y-6)
- [ ] `(?<name>…)` only; `(?P<name>…)` and `(?'name'…)` refused as `WrongNamedGroupSpelling` **naming the right spelling** (RX-017)
- [ ] `DuplicateGroupName` (Y-8)
- [ ] `NothingToRepeat`, `DoubleRepeat`, `BadRepeatBounds` (`{3,1}`), `RepeatTooLarge`
- [ ] `NREGEX_CAPTURE_GROUPS` enforced

### 0.1.2 — the explicit stack
- [ ] a `Vec<Frame>` bounded by `NREGEX_NEST_DEPTH`, **no native recursion anywhere** (RX-032)
- [ ] `NestTooDeep` names the offset of the parenthesis that exceeded it
- [ ] **the gate for this subcycle**: a 10 000-level pattern produces a clean refusal, and a wrapper script confirms the process exited normally rather than on a signal
- [ ] `// stress: 40` on that test, because a stack overflow is timing-shaped
- [ ] a tree check that greps `src/syntax/` for a function that calls itself

### 0.1.3 — classes
- [ ] class items, ranges, negation, and the literal-`]`-first rule
- [ ] `BadClassRange` (`[z-a]`), `EmptyClass`, `UnclosedClass`
- [ ] Perl classes `\d \D \w \W \s \S` parsed as *unresolved* items — resolution is 0.3's, and the parser must not need the Unicode tables to exist
- [ ] POSIX bracket classes, **inside a class only**
- [ ] `\p{…}` / `\P{…}` parsed with the property spec kept as text, resolved at 0.3
- [ ] nested classes `[a[b-c]]`
- [ ] `&&`, `--`, `~~` with the precedence in Y-17, and `ClassOpMismatch`
- [ ] O-Y2 decided and recorded

### 0.1.4 — escapes and flags
- [ ] every escape in §1's `Escape` production
- [ ] **`\` before an unlisted ASCII letter or digit is `UnknownEscape`, never a literal** (Y-2) — a test per unassigned letter
- [ ] `\x41`, `\x{1F600}`, `A`, `\U0001F600`, with `BadHexEscape`, `BadUnicodeEscape`, `InvalidCodepoint` (surrogates and above `U+10FFFF`)
- [ ] flags `imsxu`, scoped per Y-12: `(?i:…)` to the group, `(?i)` to the end of the enclosing group, `(?-i)` clearing
- [ ] `x` mode: whitespace and `#`-to-end-of-line ignored, per O-Y2's answer
- [ ] `(?-u)` byte mode, and `ByteModeNonAscii` when a non-ASCII literal appears under it (Y-14) — **naming the codepoint**
- [ ] `UnknownFlag`

### 0.1.5 — the refusals
- [ ] every construct in §8 refused with its own kind and offset
- [ ] **each message names the guarantee or the alternative, never "unsupported"** (K-1): `BackreferenceUnsupported` says the pattern could not be matched in linear time; `UnsupportedQuoting` names `regex_escape()`; `\Z` names `\n?\z`; `\p{InGreek}` names `\p{Script=Greek}`
- [ ] `regex_escape(text)` implemented here, since §8 points at it
- [ ] a rejection test per refusal in `tests/rejection/`, with the exact-code rule

### 0.1.6 — close
- [ ] **`check_error_kinds_tested` live and green**: every `PatternErrorKind` in `SYNTAX.md` §9 has a test that provokes it
- [ ] a fuzz pass over random byte strings as patterns: never traps, always terminates, always produces a program or an error with a valid offset
- [ ] findings written; `0.2.0.md` written; archived

## Gate

Every kind in `SYNTAX.md` §9 has a test that produces it, and
`check_error_kinds_tested` is green. A kind nothing can produce is a promise
the documentation makes and the code does not keep — the compiler found that
shape three times and called it the dormant-rule pattern.

## Watch for

- **`in`, `end`, `range` and `any` are keywords** and a parser wants all four.
  `src` for the cursor, `hi` for a range's upper bound, `rng` for a range
  value.
- **The offset is the product.** A parser that is right about structure and
  vague about position is a parser whose errors are useless. Every error goes
  through one constructor so no site can forget.
- **Do not resolve classes here.** `\w` and `\p{L}` are parsed to unresolved
  items; 0.3 resolves them. A parser that needed the Unicode tables would make
  cycle 0.1 depend on 0.3 and neither would be testable alone.
- **The explicit stack is the whole point of 0.1.2** and the temptation to
  "just use recursion for now" is exactly how the hazard survives to 1.0.

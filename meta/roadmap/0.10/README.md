# Cycle 0.10 — The public API

**`src/api/`: the surface a consumer sees.** The first cycle whose output
somebody could write a program against.

## Decisions in

RX-050, RX-051, RX-052, RX-054, RX-034, RX-060, RX-061. Settled.

**Open questions to settle:** O-A1 (does `Matches` implement the prelude
`Iterator` trait? — probe 12 has the answer), O-S1 (`RegexOptions` a value, not
a `comptime` parameter — recommendation: a value).

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.10.0 | **`Regex`, `Cache`, `Match`** — compilation and the three search entry points | a program that compiles a pattern and finds a match |
| 0.10.1 | **`Captures`** — caller-owned storage, by index and by name | a loop over ten thousand matches allocating once |
| 0.10.2 | **`RegexOptions`** — every bound settable, the builder chain | O-S1 decided |
| 0.10.3 | **Iterators** — `Matches`, `CaptureMatches`, `Split`; the empty-match rule | `regex_matches` over `a*` terminates |
| 0.10.4 | **Replacement** — the template, `Replacer`, the `Bytes` sink | `$name` and `$$`, validated once |
| 0.10.5 | **Inspection and `lib.npk`** — the umbrella, the conformance test | every public name touched by a test |
| 0.10.6 | **Close** | `done/0.10/`, `0.11.0.md` written |

## Checklist

### 0.10.0 — `Regex`, `Cache`, `Match`
- [ ] `regex_compile`, `regex_compile_opts`, `regex_escape`, `regex_cache`
- [ ] `regex_is_match`, `regex_find`, `regex_find_at` — **none returning `Result`** (A-1, RX-061)
- [ ] `Match` is `{lo, hi}` (RX-050), and **the fields are `lo` and `hi`** by A-3 — *not* because `end` cannot be a field name, which RX-134 measured to be false at all three kept pins
- [ ] **`regex_find_at`'s `at` is where the search starts, not where the haystack starts** (A-5): `^` still means the start of `hay` and `\b` at `at` still looks at the byte before it. A test asserts searching `hay[at..]` gives a *different* answer, so the distinction is protected
- [ ] `ERegexPattern` is the **only** `error:` in the library; `check_error_budget` green

### 0.10.1 — `Captures`
- [ ] caller-owned; `regex_captures_new(@re)` sizes it from the program
- [ ] `captures_get(i)` and `captures_name(s)`, both returning `Match?`
- [ ] a non-participating group returns `NIL`, not `{0,0}` — a test with `(a)|(b)` against `b`
- [ ] a loop over ten thousand matches allocates **once**, asserted by an allocator counter

### 0.10.2 — `RegexOptions`
- [ ] every bound from `SAFETY.md` §5 settable
- [ ] the meaning flags settable, with **the inline pattern flag winning** where both appear (A-7) — the pattern is the more local statement
- [ ] chained setters take `move Self` and return `Self` (A-8); no `Default` derive
- [ ] O-S1 decided and recorded

### 0.10.3 — iterators
- [ ] `Matches`, `CaptureMatches`, `Split`
- [ ] **one `advance_after(m)` helper** implementing the empty-match rule (A-14, Y-21): after `lo == hi`, advance one codepoint in Unicode mode, one byte in byte mode. Every iterator routes through it, so the rule exists in one place
- [ ] `regex_matches` over `a*` against `bbb` terminates and yields the documented sequence
- [ ] O-A1 decided from probe 12's verdict; if the trait fits, implement it **and** keep `matches_next`
- [ ] an iterator is second-class (A-15) — a test in `tests/rejection/` asserting that returning one from a function is refused, with the code recorded

### 0.10.4 — replacement
- [ ] the closed template syntax from A-9: `$0`…`$9`, `${12}`, `$name`, `${name}`, `$$`
- [ ] a non-participating group substitutes the empty string
- [ ] `$` followed by anything else is `BadTemplate`
- [ ] **the template is validated once, before the first search** (A-10) — a test asserting a bad template over a haystack with a thousand matches produces exactly one error
- [ ] `Replacer` as a bare non-capturing function value (A-11)
- [ ] output into a caller-owned `Bytes` (A-12), never a returned `string`

### 0.10.5 — inspection and `lib.npk`
- [ ] `regex_group_count`, `regex_group_name`, `regex_group_index`, `regex_pattern`, `regex_last_engine`, `regex_program_size`
- [ ] `pattern_error_kind`, `pattern_error_offset`, `pattern_error_text`
- [ ] `src/lib.npk` lists every public name from `API.md` §1, one per line
- [ ] a conformance test touching **every** name, so a removal breaks a test rather than a user

### 0.10.6 — close
- [ ] the corpus green through the public API, not only through the internals
- [ ] the linear-time property test still green
- [ ] findings written; `0.11.0.md` written; archived

## Gate

Every public name touched by a conformance test, the error budget still one,
and a real program compiled and run from the examples directory.

## Watch for

- **`regex_find_at`'s semantics are the thing engines get wrong.** Searching a
  subslice is not the same as searching from an offset, and the difference is
  invisible until a pattern uses `^` or `\b`.
- **The empty-match rule in one place.** Three iterators each implementing it is
  three chances for one of them not to terminate.
- **`end` is refused as a BINDING name and accepted as a FIELD name** (RX-134, measured). The field is `hi` by A-3's choice, not by the compiler's. What will actually bite is `int64:end = …` in a loop, which is `NITPICK-PARSE-002`.
- **A returned iterator is refused** and a consumer arriving from Rust will try.
  The rejection test is documentation as much as it is a test.

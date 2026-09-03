# The public surface

What a consumer sees, and the shapes the language forces on it.

---

## 1. The whole surface

`src/lib.npk` re-exports exactly this, one name per line, and a conformance
test touches every one so a removal breaks a test rather than a user.

```nitpick
// types
Regex  Cache  Match  Captures  PatternError  PatternErrorKind  RegexOptions
Matches  CaptureMatches  Split   Replacer

// compiling
regex_compile(string) -> Result<Regex>
regex_compile_opts(string, RegexOptions) -> Result<Regex>
regex_escape(string) -> string
regex_cache(Regex->) -> Cache

// searching                              (never fail — SAFETY.md S-4)
regex_is_match(Regex->, Cache->, uint8[]) -> bool
regex_find(Regex->, Cache->, uint8[]) -> Match?
regex_find_at(Regex->, Cache->, uint8[], int64) -> Match?
regex_captures(Regex->, Cache->, uint8[], Captures->) -> bool

// iterating
regex_matches(Regex->, Cache->, uint8[]) -> Matches
regex_capture_matches(Regex->, Cache->, uint8[]) -> CaptureMatches
regex_split(Regex->, Cache->, uint8[]) -> Split

// replacing
regex_replace(Regex->, Cache->, uint8[], uint8[], Bytes->) -> Result<NIL>
regex_replace_all(Regex->, Cache->, uint8[], uint8[], Bytes->) -> Result<NIL>
regex_replace_with(Regex->, Cache->, uint8[], Replacer, Bytes->) -> Result<NIL>

// inspecting
regex_group_count(Regex->) -> int32
regex_group_name(Regex->, int32) -> string?
regex_group_index(Regex->, string) -> int32?
regex_pattern(Regex->) -> string
regex_last_engine(Cache->) -> EngineKind
regex_program_size(Regex->) -> int32

// errors
pattern_error_kind(PatternError) -> PatternErrorKind
pattern_error_offset(PatternError) -> int64
pattern_error_text(PatternError) -> string
```

**Rule A-1 — everything on the search path returns a value, not a `Result`.**
`SAFETY.md` S-4: a compiled `Regex` cannot fail to search. `Match?` is the
absence of a match, not an error.

---

## 2. `Match`

```nitpick
pub struct:Match = { int64:lo; int64:hi; };     // byte offsets, half-open [lo, hi)
```

**Rule A-2 (RX-050) — byte offsets, never a slice.** A slice is a second-class
borrow and cannot be returned (D-004, D-070, `SAFETY.md` §6). The caller slices
its own haystack.

**Rule A-3 — the fields are `lo` and `hi`, not `start` and `end`.** `end` is
the `when`/`then`/`end` terminator and does not parse as a field name
(`BUILD.md` §7). `match_len(m)` is `hi - lo`.

**Rule A-4 — an empty match has `lo == hi`** and is a real match
(`SYNTAX.md` Y-21).

---

## 3. Searching

**Rule A-5 — `regex_find_at(re, cache, hay, at)` searches from `at` and is the
primitive; every other search is it.** The distinction that matters and that
engines get wrong: `at` is where the **search starts**, not where the haystack
starts. `^` still means the start of `hay`, and `\b` at `at` still looks at the
byte before it. Searching `hay[at..]` as a fresh haystack gives different and
wrong answers for both, which is why the slice form is not the primitive.

**Rule A-6 — `regex_captures` fills a caller-owned `Captures`** and returns
whether it matched:

```nitpick
Captures:caps = regex_captures_new(@re);
if (regex_captures(@re, @cache, hay, @caps)) {
    Match?:whole = captures_get(@caps, 0i32);
    Match?:year  = captures_name(@caps, "year");
}
```

The caller owns the storage so a loop over ten thousand matches allocates once.
`Captures` is `Vec<int64>` of slots plus a back-reference to the group table;
`captures_get` returns `NIL` for a group that did not participate.

---

## 4. `RegexOptions`

A plain value, not a `comptime` parameter (O-S1), constructed by
`regex_options()` and chained:

```nitpick
RegexOptions:o = regex_options()
    .size_limit(1000000i32)
    .dfa_cache_bytes(4194304i64)
    .case_insensitive(true)
    .force_engine(EngineKind.PikeVm);
```

**Rule A-7 — every bound in `SAFETY.md` §5 is settable here**, and nothing else
is. Flags that affect *meaning* — `i`, `m`, `s`, `x`, `u` — are also settable,
and are equivalent to writing the inline flag at the start of the pattern; the
inline form wins where both appear, because the pattern is the more local
statement.

**Rule A-8 — chained setters take `move Self` and return `Self`** (the
ecosystem's builder convention, `nitpick-tui`'s W-5), because there are no
static methods and no `Default` derive (D-123, D-185).

---

## 5. Replacement, without closures

**Rule A-9 (RX-051) — replacement takes a template, not a callback.** The
language has no closures (D-018), so `replace_with(|m| …)` is unspellable.

```nitpick
Bytes:out = bytes_new();
relay regex_replace_all(@re, @cache, hay, "$year-$month", @out);
```

**The template syntax**, closed and stated:

| Form | Means |
|---|---|
| `$0` … `$9` | the numbered group |
| `${12}` | a group number needing braces |
| `$name`, `${name}` | a named group |
| `$$` | a literal `$` |
| a group that did not participate | the empty string |
| `$` followed by anything else | **refused at replace time** — `BadTemplate` |

**Rule A-10 — the template is validated once, not per match.**
`regex_replace_all` parses it before the first search, so a bad template is one
error and not one per occurrence. This is why the replace functions return
`Result<NIL>` when nothing else on the search path does: the failure is the
*template*, not the search.

**Rule A-11 — `regex_replace_with` takes a `Replacer`**, which is a bare
function value with no capture:

```nitpick
pub struct:Replacer = { func:f = NIL(uint8[]:hay, Captures->:caps, Bytes->:out); };
```

A caller needing context passes it through the haystack or performs the
replacement itself over `regex_matches`. That is the honest consequence of
D-018 and it is stated rather than worked around, because the alternative — a
`any->` context pointer — would be an untyped escape hatch in a library whose
selling point is that it has none.

**Rule A-12 — output goes into a caller-owned `Bytes`**, never a returned
`string`. Returning one would allocate per call; the sink lets a caller replace
across a hundred haystacks into one buffer.

---

## 6. Iteration

**Rule A-13 (RX-052) — an iterator is a struct with a `next` method**, not a
callback, and it implements the prelude's `Iterator` trait where the shape
fits.

```nitpick
Matches:it = regex_matches(@re, @cache, hay);
while (true) {
    Match?:m = matches_next(@it);
    if (m == NIL) { break; }
    // …
}
```

**Rule A-14 — the empty-match advance rule, stated once and implemented once**
(`SYNTAX.md` Y-21). After a match with `lo == hi`, the next search starts at
`hi` plus one **codepoint** in Unicode mode, one byte in byte mode. Without it,
`regex_matches` over `a*` does not terminate. Every iterator in this library
routes through one `advance_after(m)` helper so the rule exists in one place.

**Rule A-15 — an iterator borrows its `Regex` and its `Cache`** and so is
second-class: it cannot be returned, stored past the call, sent through a
channel, or held across an `await` (D-004). It is built by struct literal where
it is used. Stated because a consumer arriving from Rust will expect to return
one from a function, and will not be able to.

---

## 7. Strings and bytes

**Rule A-16 (RX-054) — `uint8[]` is the primitive; `string` is a convenience
over it.** Every search entry point takes a haystack slice. A `string` caller
writes `string_bytes(s)`, which is the borrowed view the floor already provides
at no cost.

Two reasons this direction rather than the other: a systems library is asked to
search things that are not validated text, and `string_bytes` is free while
`string_from_bytes` over a subrange is not.

**Rule A-17 — a `Match`'s offsets index the haystack the caller passed**, which
for a `string` caller is the string's bytes. Slicing a `string` by them is
`string_slice(s, m.lo, m.hi)`, which is an **owned copy** (D-186) — a fact
worth knowing before it appears in a loop.

---

## 8. Open items

- **O-A1 — whether `Matches` should implement the prelude `Iterator` trait or
  only expose `matches_next`.** The trait gives `for … in`, which is
  ergonomic; it also requires an associated type, which disqualifies the trait
  from `dyn` (D-160) — irrelevant here, since nothing erases an iterator.
  Recommendation: implement it, and keep `matches_next` as the explicit form.
  Decide at cycle 0.10, after probe 12 says what the trait actually admits.
- **O-A2 — a `RegexSet` API over `COMPILE.md` §6's multi-pattern programs.**
  The format supports it at 1.0; the API does not. Cycle 1.1.

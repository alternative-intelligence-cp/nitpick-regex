r"""0.1.0 step 2 -- what a pattern can get wrong (the plan's PD-16, recorded as RX-172).

`src/syntax/pattern_error.npk` -- `PatternErrorKind`, all thirty-seven of `SYNTAX.md`
§9 in its order; `PatternError`, `SAFETY.md` S-9's value with every field sealed; and
`pattern_error`, the one constructor -- and `src/syntax/syntax.npk` becomes the layer
entry, re-exporting those three names. Three units and one refusal pin them. Applied by
`python3 -B f10_edit.py error "$REPO"`; the engine's docstring says how.
"""

_FAILSAFE = r"""func:failsafe = int32(Error:e) {
    pick (e) {
        (HeapBadRequest)    { exit 91i32; },
        (HeapOom)           { exit 92i32; },
        (IntOverflow)       { exit 93i32; },
        (OutOfBounds)       { exit 94i32; },
        (Unreachable)       { exit 95i32; },
        (WildLeak)          { exit 96i32; },
        (StackExhausted)    { exit 106i32; },
        (MachineFault)      { exit 107i32; },
        (DecreasesViolated) { exit 108i32; },
        (LimitViolated)     { exit 109i32; },
        (ShiftRange)        { exit 115i32; },
        (*)                 { exit 99i32; }
    }
    exit 9i32;
};
"""

KINDS = """UnclosedGroup UnopenedGroup UnclosedClass EmptyClass NestTooDeep TrailingBackslash EmptyAlternate
NothingToRepeat DoubleRepeat BadRepeatBounds RepeatTooLarge RepeatProductTooLarge
BadClassRange UnknownPosixClass UnknownUnicodeProperty ClassOpMismatch ClassTooLarge
UnknownEscape BadHexEscape BadUnicodeEscape InvalidCodepoint
DuplicateGroupName BadGroupName UnknownFlag TooManyCaptureGroups WrongNamedGroupSpelling
BackreferenceUnsupported LookaroundUnsupported AtomicGroupUnsupported RecursionUnsupported UnsupportedAnchor UnsupportedGroup UnsupportedQuoting
PatternTooLong ProgramTooLarge InvalidPatternEncoding ByteModeNonAscii"""
_GROUPS = ["structure", "quantifiers", "classes", "escapes", "groups and flags",
           "refusals (§8)", "limits and encoding"]
_ENUM = "\n".join("    // " + g + "\n" + "".join(f"    {k};\n" for k in line.split())
                  for g, line in zip(_GROUPS, KINDS.split("\n"))).rstrip("\n")
_ALL = KINDS.split()
assert len(_ALL) == 37
_ARMS = ",\n".join(f"        (PatternErrorKind.{k}) {{ n = {i}i64; }}" for i, k in enumerate(_ALL))

NEW = {}

NEW["src/syntax/pattern_error.npk"] = r"""// `src/syntax/pattern_error.npk` — WHAT A PATTERN CAN GET WRONG, AND THE ONE
// WAY TO SAY SO. Cycle 0.1.0, RX-172.
//
// `PatternErrorKind` is `meta/specs/SYNTAX.md` §9's closed list: every kind, in
// that section's order, declared complete before the parser produces any of
// them. `check_error_kinds_tested`, cycle 0.1's gate at 0.1.6, diffs this enum
// against the tests that provoke each kind, and it cannot be written against an
// enum that is still moving; a kind added later is a kind nobody notices is
// untested.
//
// `PatternError` is `SAFETY.md` rule S-9's value: the kind, the byte offset into
// the pattern (`SYNTAX.md` Y-10), a length where the construct spans more than a
// point, and a kind-specific detail. EVERY FIELD IS `sealed` (the compiler's
// D-313): read anywhere, written only here -- so outside this file a
// `PatternError{ … }` literal is NITPICK-TYPE-079, and `pattern_error(…)` below
// is the only way anything can build one. No site can forget an offset, because
// there is no other way to build the value than to pass one
// (`tests/rejection/pattern_error_literal.npk`).
//
// A VALUE, NOT AN `error:` IDENTITY. The library has one identity,
// `ERegexPattern`, and it is `api`'s (S-8); `syntax` sits below `api` (`BUILD.md`
// B-16), so the parser hands a `PatternError` back as a value and `api` turns it
// into the identity (RX-175).
//
// THE FILE IS NOT `error.npk`, AND CANNOT BE. `error` is a keyword (the
// `error:` declaration), a file's `mod:` name must equal its basename (B-13), and
// `mod:error;` is refused NITPICK-RESOLVE-012 at 1:1 -- measured at `c970483`. So
// the module is named for the value it builds.
//
// LAYERING (`BUILD.md` §6, rule B-16). `syntax` may import `unicode` and `core`;
// this file imports `core` for one thing, its out-of-range stop `vec_oob`, so a
// program importing it owes `core`'s eleven arms.
mod:pattern_error;

use "../core/core.npk".*;

// `SYNTAX.md` §9, in its order. `tests/unit/pattern_error_unit.npk` holds this
// list to that order with an exhaustive `pick`, so a kind added, dropped or
// moved here is a red run, not a review comment.
pub enum:PatternErrorKind = {
""" + _ENUM + r"""
};

// `SAFETY.md` S-9, field for field. Thirty-two bytes, measured at `c970483`:
// S-9 fixes the fields and their order, and the padding that order costs is
// harmless because nothing stores a `PatternError` in a `Vec` -- a parse stops
// at its first error.
pub struct:PatternError = {
    sealed PatternErrorKind:kind;    // SYNTAX.md §9's closed list
    sealed int64:offset;             // byte offset into the pattern (Y-10)
    sealed int64:span_len;           // 0 when the position is a point
    sealed uint32:detail;            // kind-specific: the offending codepoint, the bound exceeded
};

// obligation: never fails requires offset >= 0i64 && span_len >= 0i64
//
// THE ONE CONSTRUCTOR (RX-172). A negative offset or length is a defect in the
// code that built the error, never in the pattern, and it stops HERE, on `core`'s
// one out-of-range stop (exit 94, `OutOfBounds`), rather than reaching a user as
// a position that is not in their pattern. `tests/unit/pattern_error_offset_negative.npk`
// and `pattern_error_span_negative.npk` are the two stops.
pub func:pattern_error = PatternError(PatternErrorKind:kind, int64:offset, int64:span_len, uint32:detail) never fails {
    if (offset < 0i64)   { drop vec_oob(offset); }
    if (span_len < 0i64) { drop vec_oob(span_len); }
    pass PatternError{ kind: kind, offset: offset, span_len: span_len, detail: detail };
};
"""

NEW["tests/unit/pattern_error_unit.npk"] = r"""// expect-exit: 0
//
// `PatternErrorKind` IS `SYNTAX.md` §9, ALL THIRTY-SEVEN, IN ITS ORDER -- AND
// `pattern_error` BUILDS EACH ONE, THROUGH THE LAYER ENTRY. Cycle 0.1.0, RX-172.
//
// WHAT IT PINS. `ordinal` is an EXHAUSTIVE `pick` over the enum, no `(*)`, one
// arm per kind in §9's order, each answering its place in that list. So the enum
// cannot gain a kind (the `pick` then misses one: NITPICK-PICK-001), lose one (an
// arm then names no variant, and the file is refused -- at `c970483` by the
// emitter, NITPICK-EMIT-002, which the frontend should have caught), or reorder
// two (tag k answers some other place: exit 20) without this file going red.
// Every kind is then built by
// `pattern_error` with an offset, a length and a detail of its own, and each
// field read back (21, 22, 23): the constructor stores what it is given.
//
// The kind is made from its place, `k =>! PatternErrorKind` -- the language's
// spelling for a tag-only enum's tag (the compiler's D-140), which it does not
// range-check, so the loop's bound keeps `k` inside the list. Every name here
// reaches the file through `src/syntax/syntax.npk`'s re-exports.
mod:pattern_error_unit;

use "../../src/syntax/syntax.npk".*;

func:ordinal = int64(PatternErrorKind:k) never fails {
    int64:n = -1i64;
    pick (k) {
""" + _ARMS + r"""
    }
    pass n;
};

func:main = int32(cstring[]:_~argv) {
    int64:k = 0i64;
    while (k < 37i64) decreases 37i64 - k {
        PatternErrorKind:kind = (k =>! int32) =>! PatternErrorKind;
        PatternError:e = raw pattern_error(kind, k * 3i64, k + 1i64, (k =>! uint32) + 1000u32);
        if ((raw ordinal(e.kind)) != k)             { exit 20i32; }
        if (e.offset != k * 3i64)                   { exit 21i32; }
        if (e.span_len != k + 1i64)                 { exit 22i32; }
        if (e.detail != (k =>! uint32) + 1000u32)   { exit 23i32; }
        k = k + 1i64;
    }
    exit 0i32;
};

""" + _FAILSAFE

NEW["tests/unit/pattern_error_offset_negative.npk"] = r"""// expect-exit: 94
//
// `pattern_error` STOPS ON A NEGATIVE OFFSET. Cycle 0.1.0, RX-172.
//
// A negative offset is a defect in the code building the error, never in the
// pattern, so it traps on `core`'s one out-of-range stop, `vec_oob` -- 94,
// `OutOfBounds` -- rather than reaching a user as a position that is not in
// their pattern. One stop per file: a trapping call cannot be followed by an
// assertion in the same program.
mod:pattern_error_offset_negative;

use "../../src/syntax/syntax.npk".*;

func:main = int32(cstring[]:_~argv) {
    PatternError:e = raw pattern_error(PatternErrorKind.UnclosedGroup, -1i64, 0i64, 0u32);
    if (e.offset != -1i64) { exit 10i32; }
    exit 0i32;
};

""" + _FAILSAFE

NEW["tests/unit/pattern_error_span_negative.npk"] = r"""// expect-exit: 94
//
// `pattern_error` STOPS ON A NEGATIVE LENGTH. Cycle 0.1.0, RX-172 -- the offset's
// twin: a construct cannot span fewer than no bytes, so a negative `span_len` is
// the building code's defect and traps on `vec_oob` (94, `OutOfBounds`).
mod:pattern_error_span_negative;

use "../../src/syntax/syntax.npk".*;

func:main = int32(cstring[]:_~argv) {
    PatternError:e = raw pattern_error(PatternErrorKind.UnclosedGroup, 0i64, -1i64, 0u32);
    if (e.span_len != -1i64) { exit 10i32; }
    exit 0i32;
};

""" + _FAILSAFE

NEW["tests/rejection/pattern_error_literal.npk"] = r"""// expect-error: NITPICK-TYPE-079
// expect-error-at: 22:22
//
// A `PatternError` IS BUILT BY `pattern_error` AND BY NOTHING ELSE. Cycle 0.1.0,
// RX-172; `SYNTAX.md` Y-10, `SAFETY.md` S-9.
//
// WHAT IT PINS. Every field of `PatternError` is `sealed` (the compiler's D-313):
// written only by `src/syntax/pattern_error.npk`. So this struct literal, outside
// that file, is NITPICK-TYPE-079 -- once for each field it writes, all four at
// the literal -- and the one way left to build an error is the constructor,
// which takes an offset and refuses a negative one. The rule "every error
// carries a byte offset" is the compiler's to hold, not a tree check's or a
// reviewed grep's.
//
// A TEST OF THE SEAL, NOT OF THIS FILE: with the four `sealed`s deleted it
// compiles (`meta/roadmap/0.1/0.1.0.md`, step 2's controls).
mod:pattern_error_literal;

use "../../src/syntax/syntax.npk".*;

func:main = int32(cstring[]:_~argv) {
    PatternError:e = PatternError{ kind: PatternErrorKind.UnclosedGroup, offset: 0i64, span_len: 1i64, detail: 0u32 };
    discard(e);
    exit 0i32;
};

""" + _FAILSAFE

EDITS = {}

_PLACEHOLDER = r"""// `src/syntax/` — the pattern parser. PLACEHOLDER: nothing yet.
//
// FILLED BY cycle 0.1, governed by `meta/specs/SYNTAX.md`. Pattern text to an
// AST, driven by an EXPLICIT STACK and never by native recursion (RX-032,
// `SAFETY.md` S-18) so that a deeply nested pattern is a refusal and not a
// blown call stack. `tests/probe/probe05_explicit_stack.npk` is the evidence
// that the shape is both writable and sufficient: 10 000 levels deep is
// refused at depth 251 and the program survives.
//
// LAYERING (`BUILD.md` §6, rule B-16). May import: `unicode`, `core`.
//
// See `src/core/core.npk` for why a placeholder exists at all (P-6).
mod:syntax;
"""

ENTRY = r"""// `src/syntax/syntax.npk` — THE PATTERN PARSER'S LAYER ENTRY. A module above
// `syntax` writes one import, this file, and reaches what the layer offers.
//
// FILLED BY cycle 0.1, governed by `meta/specs/SYNTAX.md`. Pattern text to an
// AST, driven by an EXPLICIT STACK and never by native recursion (RX-032,
// `SAFETY.md` S-18) so that a deeply nested pattern is a refusal and not a
// blown call stack. `tests/probe/probe05_explicit_stack.npk` is the evidence
// that the shape is both writable and sufficient: 10 000 levels deep is
// refused at depth 251 and the program survives.
//
// EVERY LINE BELOW IS `pub use`, ONE NAME PER LINE (`BUILD.md` B-15a rules 1
// and 3): `use` is not transitive, a plain `use` re-exports nothing, and one
// name to a line keeps the list greppable and a removal one line of diff. Each
// section names the decision that put it here.
//
// LAYERING (`BUILD.md` §6, rule B-16). May import: `unicode`, `core`. A program
// importing this file owes `core`'s eleven arms (measured at `c970483`), because
// `pattern_error.npk` imports `core`.
mod:syntax;

// ---- what a pattern can get wrong (RX-172) ---------------------------------
pub use "./pattern_error.npk".PatternErrorKind;
pub use "./pattern_error.npk".PatternError;
pub use "./pattern_error.npk".pattern_error;
"""

EDITS["src/syntax/syntax.npk"] = [(_PLACEHOLDER, ENTRY)]

EDITS["meta/specs/SAFETY.md"] = [(
r"""variants. A caller that wants to report "unclosed group at byte 14" has
everything it needs; a `failsafe` that wants to stop has one arm.
""",
r"""variants. A caller that wants to report "unclosed group at byte 14" has
everything it needs; a `failsafe` that wants to stop has one arm.

*(@@DATE@@, cycle 0.1.0 — RX-172: `src/syntax/pattern_error.npk` declares it,
every field `sealed` (the compiler's D-313), so outside that file a
`PatternError` literal is `NITPICK-TYPE-079` and `pattern_error(kind, offset,
span_len, detail)` is the only way to build one — Y-10's offset on every error,
held by the compiler (`tests/rejection/pattern_error_literal.npk`). The
constructor stops on a negative offset or length, a defect in the code that
built the error. Thirty-two bytes, measured. `SYNTAX.md` §9 lists thirty-seven
kinds; "thirty" above is a round number.)*
"""),
]

EDITS["meta/specs/SYNTAX.md"] = [(
r"""**Rule Y-25 — every kind has a test that provokes it**, and a harness check
diffs the enum against the tests, so a kind nothing can produce is caught. This
is the compiler's `check_codes_tested` in this library's terms.
""",
r"""**Rule Y-25 — every kind has a test that provokes it**, and a harness check
diffs the enum against the tests, so a kind nothing can produce is caught. This
is the compiler's `check_codes_tested` in this library's terms.

*(@@DATE@@, cycle 0.1.0 — RX-172: `src/syntax/pattern_error.npk`'s
`PatternErrorKind` is this list, all thirty-seven, in this order, declared
before the parser produces any of them, and `tests/unit/pattern_error_unit.npk`
holds the enum to the list with an exhaustive `pick`. The harness check is
cycle 0.1.6's.)*
"""),
]

EDITS["meta/DECISIONS.md"] = [(
r"""true reason; **leaving it to the next audit** — the first layer entry written since is this subcycle's, and
cycle 0.0's close placed the decision before it.
""",
r"""true reason; **leaving it to the next audit** — the first layer entry written since is this subcycle's, and
cycle 0.0's close placed the decision before it.

### RX-172 — `PatternErrorKind` is `SYNTAX.md` §9 complete and in order; `PatternError` is sealed, so `pattern_error(…)` is the only way to build one, and it stops on a negative offset

**@@DATE@@, cycle 0.1.0 (the plan's PD-16), at compiler `c970483`.** `src/syntax/pattern_error.npk`:

- **`PatternErrorKind` holds all thirty-seven of `SYNTAX.md` §9, in its order, now** — before the parser
  produces any. `check_error_kinds_tested` (0.1.6) diffs the enum against the tests that provoke each kind,
  and cannot be written against a moving enum; a kind added later is one nobody notices is untested.
  `tests/unit/pattern_error_unit.npk` holds the enum to §9 with an exhaustive `pick`: a kind dropped, added or
  moved is a red run.
- **`PatternError` is `SAFETY.md` S-9's four fields, each `sealed`** (the compiler's D-313). Outside the
  file a `PatternError{ … }` literal is `NITPICK-TYPE-079` — measured, once per field, at the literal
  (`tests/rejection/pattern_error_literal.npk`) — so `pattern_error(kind, offset, span_len, detail)` is the one
  way to build an error, and `SYNTAX.md` Y-10's offset on every error is the compiler's to hold. The value is
  32 bytes (measured); S-9 fixes the fields' order, and nothing stores one in a `Vec`.
- **`pattern_error` stops on a negative `offset` or `span_len`**, through `core`'s `vec_oob` (94): either is
  a defect in the code that built the error, and a stop beats a position that is not in the user's pattern.
- **The file is `pattern_error.npk`, because `error.npk` cannot exist**: `error` is a keyword, a file's
  `mod:` name is its basename (B-13), and `mod:error;` is `NITPICK-RESOLVE-012` (measured). It imports `core`
  for `vec_oob`, so it — and the layer entry, `src/syntax/syntax.npk`, which re-exports its three names —
  costs a consumer `core`'s eleven arms.

*Alternatives declined:* **the fields open, with a tree check or a reviewed grep for other construction
sites** — the first draft of `0.1.0.md`'s acceptance; the seal makes the compiler refuse every other site,
where a grep only finds the ones that exist today; **a constructor that stores what it is given** — a
negative offset would reach the user as a position that is not there; **declaring each kind when the
subcycle that produces it lands** — the enum would move under the gate's check, and each late kind would be one
nothing notices is untested; **S-9's fields reordered to save the eight bytes of padding** — S-9 is the
specification, the value is never in an array, and a parse stops at its first error.
"""),
]

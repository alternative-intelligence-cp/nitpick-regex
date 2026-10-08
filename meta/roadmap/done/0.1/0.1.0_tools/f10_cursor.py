r"""0.1.0 step 3 -- the byte cursor (the plan's PD-17, recorded as RX-173).

`src/syntax/cursor.npk` -- a sealed view of the pattern and an `int64` offset, built by
`cursor_init` and moved only by its own functions -- and the layer entry's cursor
section; one unit and one refusal pin it. Applied by `python3 -B f10_edit.py cursor
"$REPO"` after step 2; the engine's docstring says how.
"""
import importlib.util
import os

_spec = importlib.util.spec_from_file_location(
    "f10_error", os.path.join(os.path.dirname(os.path.abspath(__file__)), "f10_error.py"))
_error = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_error)
_FAILSAFE = _error._FAILSAFE

NEW = {}

NEW["src/syntax/cursor.npk"] = r"""// `src/syntax/cursor.npk` — THE BYTE CURSOR THE PARSER READS A PATTERN WITH.
// Cycle 0.1.0, RX-173.
//
// A PATTERN IS READ AS BYTES (`SYNTAX.md` Y-11), and the cursor is a view of
// them and an `int64` offset: the offset of the next byte, from 0 to the
// pattern's length. Every position the parser reports comes from here
// (`cursor_offset`), which is Y-10's byte offset on every error made structural.
//
// ONE BYTE OF LOOKAHEAD, AND THE COMPILER HOLDS THE PARSER TO IT. Both fields are
// `sealed` (the compiler's D-313): outside this file nothing builds a `Cursor`
// but `cursor_init`, which starts it at 0, and nothing moves one but the
// functions below -- a write of `pos` is NITPICK-TYPE-079
// (`tests/rejection/cursor_pos_write.npk`). So cycle 0.1's rule "no lookahead
// beyond one byte except where the grammar names it" is not a convention: a
// construct that needs more asks for a function here, by a decision, and there
// is no rewind to reach for.
//
// `cursor_init` RETURNS A STRUCT HOLDING A VIEW, AND THAT IS SOUND AT THIS
// LIBRARY'S PIN. The view is of `cursor_init`'s PARAMETER -- the caller's bytes --
// and the compiler accepts exactly that and refuses the unsound case: a `Cursor`
// over a view of a LOCAL, returned, is NITPICK-BORROW-001 at the `pass` (measured
// at `c970483`, at `c3bdae2`, and at the next re-pin's control, `9f6f370`). Cycle
// 0.0 wrote "a view is a parameter, never a return value" while the compiler
// could not see that escape (O-N9, the compiler's DEF-3, fixed at `94874ce`).
//
// WHAT `c970483` DOES NOT SEE: THE PATTERN'S OWNER WRITTEN WHILE A CURSOR HOLDS
// ITS VIEW. A `string` reassigned under a live `Cursor` leaves the cursor reading
// freed memory -- measured, the next byte read is the allocator's `0xAA` poison
// (exit 170 at both legs). The compiler's view freeze refuses that write (its
// DEF-107, NITPICK-BORROW-015, measured at `9f6f370`), and our pin does not carry
// it. The parser holds a view PARAMETER, never the owner, so no code in `src/`
// can do it; a test keeps its pattern's owner unwritten while a cursor lives.
//
// A WRONG `pos` COULD NOT READ PAST THE PATTERN ANYWAY. `src` is a slice, which
// carries its length, so D-070's bounds guard traps an out-of-range index
// (`OutOfBounds`) rather than reading a byte -- measured with a forged `pos` of
// -1 at `c970483`. The seal keeps `pos` in range; the slice is the second line.
//
// EVERY LOOP OVER A CURSOR IS A `while` WITH AN `int64` MEASURE, `decreases
// <length> - <offset>` (the compiler's D-304) -- never a `for` over a range, a
// `loop` or a `till`. At `c970483` each of those has a shape that runs the wrong
// number of times in silence (the compiler's DEF-127 … DEF-130, registered on
// 2026-09-26 for its 1.6.1d), and a byte loop is exactly where they live.
//
// LAYERING (`BUILD.md` §6, B-16). Imports nothing, so a program importing only
// this file owes eight arms: the floor's six, `IntOverflow` and `OutOfBounds`.
mod:cursor;

// What `cursor_peek` and `cursor_bump` answer when no byte is left. A byte is
// 0 … 255, so -1 names none.
pub fixed int32:CURSOR_END = -1i32;

pub struct:Cursor = {
    sealed uint8[]:src;    // the pattern: a VIEW of the caller's bytes (Y-11)
    sealed int64:pos;      // the offset of the next byte, 0 .. src.len
};

// obligation: never fails ensures result.pos == 0i64
pub func:cursor_init = Cursor(uint8[]:pat) never fails {
    pass Cursor{ src: pat, pos: 0i64 };
};

// obligation: never fails ensures result == (c.pos >= c.src.len)
pub func:cursor_at_end = bool(Cursor->:c) never fails {
    pass c.pos >= c.src.len;
};

// obligation: never fails ensures result == c.pos
pub func:cursor_offset = int64(Cursor->:c) never fails {
    pass c.pos;
};

// The next byte, 0 … 255, without moving past it -- `CURSOR_END` at the end,
// and never a read past it.
pub func:cursor_peek = int32(Cursor->:c) never fails {
    if (c.pos >= c.src.len) { pass CURSOR_END; }
    pass c.src[c.pos] => int32;
};

// The next byte, moving past it -- `CURSOR_END` at the end, which does not move.
pub func:cursor_bump = int32(Cursor->:c) never fails {
    if (c.pos >= c.src.len) { pass CURSOR_END; }
    int32:b = c.src[c.pos] => int32;
    c.pos = c.pos + 1i64;
    pass b;
};

// Moves past the next byte if it is `want`, and says whether it did.
pub func:cursor_eat = bool(Cursor->:c, uint8:want) never fails {
    if (c.pos >= c.src.len)   { pass false; }
    if (c.src[c.pos] != want) { pass false; }
    c.pos = c.pos + 1i64;
    pass true;
};
"""

NEW["tests/unit/cursor_unit.npk"] = r"""// expect-exit: 0
//
// THE BYTE CURSOR, WALKED ONE BYTE AT A TIME, THROUGH THE LAYER ENTRY. Cycle
// 0.1.0, RX-173.
//
// `walk` reads a three-byte pattern -- `a`, then NUL, then 0xFF, because the
// cursor reads BYTES (`SYNTAX.md` Y-11) and neither of the last two is a
// character anything special happens to -- and checks the offset after every
// call: `peek` does not move (13), a `eat` that misses does not move (15), one
// that matches does (17), `bump` returns the byte and moves (18 to 21). At the end
// `peek` and `bump` answer `CURSOR_END` and `bump` does not move (23, 24, 26), and
// `eat` misses (25) -- so nothing reads past the pattern. `empty` does the same
// at offset 0. `pos` is also read directly, as `c.pos` -- a sealed field is read
// anywhere -- and must agree with `cursor_offset` (27).
//
// Each pattern's owner -- `pat3`, `none` -- is never written while a cursor holds
// its view: at compiler `c970483` that write goes unrefused and the cursor then
// reads freed memory (`src/syntax/cursor.npk`'s header).
mod:cursor_unit;

use "../../src/syntax/syntax.npk".*;

func:walk = int32(uint8[]:pat) never fails {
    Cursor:c = raw cursor_init(pat);
    if (raw cursor_at_end(@c))               { pass 10i32; }
    if ((raw cursor_offset(@c)) != 0i64)     { pass 11i32; }
    if ((raw cursor_peek(@c)) != 97i32)      { pass 12i32; }
    if ((raw cursor_offset(@c)) != 0i64)     { pass 13i32; }
    if (raw cursor_eat(@c, 98u8))            { pass 14i32; }
    if ((raw cursor_offset(@c)) != 0i64)     { pass 15i32; }
    if (!(raw cursor_eat(@c, 97u8)))         { pass 16i32; }
    if ((raw cursor_offset(@c)) != 1i64)     { pass 17i32; }
    if ((raw cursor_bump(@c)) != 0i32)       { pass 18i32; }
    if ((raw cursor_offset(@c)) != 2i64)     { pass 19i32; }
    if ((raw cursor_bump(@c)) != 255i32)     { pass 20i32; }
    if ((raw cursor_offset(@c)) != 3i64)     { pass 21i32; }
    if (!(raw cursor_at_end(@c)))            { pass 22i32; }
    if ((raw cursor_peek(@c)) != CURSOR_END) { pass 23i32; }
    if ((raw cursor_bump(@c)) != CURSOR_END) { pass 24i32; }
    if (raw cursor_eat(@c, 97u8))            { pass 25i32; }
    if ((raw cursor_offset(@c)) != 3i64)     { pass 26i32; }
    if (c.pos != (raw cursor_offset(@c)))    { pass 27i32; }
    pass 0i32;
};

func:empty = int32(uint8[]:pat) never fails {
    Cursor:c = raw cursor_init(pat);
    if (!(raw cursor_at_end(@c)))            { pass 30i32; }
    if ((raw cursor_peek(@c)) != CURSOR_END) { pass 31i32; }
    if ((raw cursor_bump(@c)) != CURSOR_END) { pass 32i32; }
    if ((raw cursor_offset(@c)) != 0i64)     { pass 33i32; }
    pass 0i32;
};

func:main = int32(cstring[]:_~argv) {
    uint8[3]:pat3 = [97u8, 0u8, 255u8];
    int32:r = raw walk(pat3[0i64...3i64]);
    if (r != 0i32) { exit r; }
    string:none = "";
    int32:q = raw empty(string_bytes(none));
    exit q;
};

""" + _FAILSAFE

NEW["tests/rejection/cursor_pos_write.npk"] = r"""// expect-error: NITPICK-TYPE-079
// expect-error-at: 22:5
//
// NOTHING OUTSIDE `src/syntax/cursor.npk` MOVES A CURSOR. Cycle 0.1.0, RX-173.
//
// WHAT IT PINS. `Cursor.pos` is `sealed` (the compiler's D-313), so this write,
// outside that file, is NITPICK-TYPE-079. That is what makes cycle 0.1's rule --
// no lookahead beyond one byte except where the grammar names it -- the
// compiler's: a parser can move a cursor only through `cursor_bump` and
// `cursor_eat`, and nothing rewinds one. The literal form, `Cursor{ … }`
// outside the file, is refused the same way, once per field.
//
// A TEST OF THE SEAL, NOT OF THIS FILE: with `cursor.npk`'s two `sealed`s
// deleted it compiles (`meta/roadmap/0.1/0.1.0.md`, step 3's controls).
mod:cursor_pos_write;

use "../../src/syntax/syntax.npk".*;

func:main = int32(cstring[]:_~argv) {
    string:s = "ab";
    Cursor:c = raw cursor_init(string_bytes(s));
    c.pos = 1i64;
    discard(c);
    exit 0i32;
};

""" + _FAILSAFE

EDITS = {}

EDITS["src/syntax/syntax.npk"] = [(
r"""pub use "./pattern_error.npk".pattern_error;
""",
r"""pub use "./pattern_error.npk".pattern_error;

// ---- the byte cursor (RX-173) ----------------------------------------------
pub use "./cursor.npk".CURSOR_END;
pub use "./cursor.npk".Cursor;
pub use "./cursor.npk".cursor_init;
pub use "./cursor.npk".cursor_at_end;
pub use "./cursor.npk".cursor_offset;
pub use "./cursor.npk".cursor_peek;
pub use "./cursor.npk".cursor_bump;
pub use "./cursor.npk".cursor_eat;
"""),
]

EDITS["meta/specs/SAFETY.md"] = [(
r"""`NITPICK-TYPE-047` (S-23b, RX-169) — and `vec_get` takes `T: Pod`, so a by-value read
of an owning element out of a `Vec` is refused rather than a move (S-23a,
RX-168).)*
""",
r"""`NITPICK-TYPE-047` (S-23b, RX-169) — and `vec_get` takes `T: Pod`, so a by-value read
of an owning element out of a `Vec` is refused rather than a move (S-23a,
RX-168).)*

*(@@DATE@@, cycle 0.1.0 — RX-173: the second row is narrower than it reads.
D-004 keeps a BORROW of a local, `@x`, out of `pass`. A struct holding a view of
a PARAMETER, or a pointer parameter, IS returned, and runs, at `c970483` and at
`c3bdae2` — what it borrows is the caller's. What the compiler refuses is the
unsound case: a struct holding a view of a LOCAL, returned, is
`NITPICK-BORROW-001` at the `pass`. So `cursor_init` returns the parser's
`Cursor`. Open at `c970483`: writing the viewed value while the view is live —
a `Cursor`'s pattern reassigned — reads freed memory; the compiler's DEF-107
refuses it, `NITPICK-BORROW-015`, in no pin of ours yet.)*
"""),
]

EDITS["meta/DECISIONS.md"] = [(
r"""specification, the value is never in an array, and a parse stops at its first error.
""",
r"""specification, the value is never in an array, and a parse stops at its first error.

### RX-173 — the parser reads a pattern through a sealed cursor: `cursor_init` returns it, only its own functions move it, and it looks one byte ahead

**@@DATE@@, cycle 0.1.0 (the plan's PD-17), at compiler `c970483`.** `src/syntax/cursor.npk`:
`struct:Cursor = { sealed uint8[]:src; sealed int64:pos; }`, built by `cursor_init(uint8[]:pat)` at offset 0,
read by `cursor_at_end`, `cursor_offset` and `cursor_peek`, moved by `cursor_bump` and `cursor_eat` and by
nothing else. A byte is answered as an `int32` from 0 to 255, and `CURSOR_END` (−1) when none is left; nothing
reads past the pattern.

- **Sealed, so the lookahead rule is the compiler's.** Cycle 0.1's checklist asks for "no lookahead beyond one
  byte except where the grammar names it". With both fields sealed (the compiler's D-313) a write of `pos`
  outside the file is `NITPICK-TYPE-079` (`tests/rejection/cursor_pos_write.npk`), and so is a `Cursor{ … }`
  literal, once per field (measured) — so a construct that needs more lookahead asks for a function here, by a
  decision, and there is no rewind to reach for.
- **Returned by `cursor_init`, because that is sound now.** `0.1.0.md`'s first draft (its D2) kept the cursor
  "a parameter everywhere, never a return value", for a reason cycle 0.0 met at `950bb1d`: a view that escaped
  its frame drew no diagnostic (O-N9, the compiler's DEF-3). DEF-3 was fixed at `94874ce`. Measured at
  `c970483`, `c3bdae2` and the next re-pin's control, `9f6f370`: a `Cursor` over a view of the constructor's
  PARAMETER is returned and reads correctly (0 / 0), and one over a view of a LOCAL is `NITPICK-BORROW-001` at
  the `pass` — the escape analysis sees through the struct. `SAFETY.md` §1's second row said a struct holding a
  borrow cannot be returned; it gains a dated note, since what D-004 bars is a borrow of a local.
- **What is NOT closed at `c970483`, and how it is kept out of reach.** A `string` reassigned while a `Cursor`
  holds its view leaves the cursor reading freed memory: the next byte read is the allocator's `0xAA` poison
  (170 at both legs). The compiler's view freeze refuses that write (its DEF-107, `NITPICK-BORROW-015` —
  measured at `9f6f370`), and no pin of ours carries it. The parser never holds the pattern's owner — it takes
  a view parameter — so nothing in `src/` can write it; a test keeps its pattern's owner unwritten while a
  cursor is live.
- **`int64` offsets, and every loop over a cursor is a `while` with an `int64` measure** (`decreases` the
  length less the offset, the compiler's D-304). No `for` over a range, no `loop`, no `till`: at `c970483` each
  has a shape that runs the wrong number of times at no diagnostic — a range ending at its type's maximum or
  crossing an unsigned type's sign bit runs zero times, `loop` and `till` widen an unsigned bound by its sign,
  `till` with a negative limit counts down, and a `for` binding sharing an outer local's name overwrites it
  (the compiler's DEF-127 … DEF-130, registered 2026-09-26 for its 1.6.1d). A byte loop is exactly where those
  shapes live; none is written here, and a design that needs one is a question for the author, not a
  workaround.

*Alternatives declined:* **the draft's D2 — a struct literal at every call site, its fields open** — the
position would be writable by anyone holding a cursor and the lookahead rule a convention; its reason, the
undiagnosed escape, is gone; **the offset alone, with the slice passed beside it to every call** — two things
to keep together at every site, and nothing to seal; **`cursor_peek` answering `uint8?`** — an `Optional` per
byte, read with `??` and a default, for what one sentinel says; **a two-byte peek or a rewind now** — no
construct 0.1.0 writes needs one, and the grammar names where one is needed when a subcycle meets it;
**`int32` offsets** — every one would be narrowed from an `int64` length, and the language has no checked
narrowing.
"""),
]

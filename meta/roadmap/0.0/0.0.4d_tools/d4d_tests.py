#!/usr/bin/env python3
"""0.0.4d step 3 -- the tests: five copy units become rejection fixtures (after the
`git mv`), the swap is spelled with moves, the loan is pinned and its reach extended,
the positive twin, `buf`'s fixture, three probes, and the nine `.buf.len` reads.
Run: python3 d4d_tests.py "$REPO".

IDEMPOTENT: a header already in place, a file already written with this content, and
an edit already applied are each reported ALREADY. A file whose content differs from
both the expected before and after is a STOP, and NOTHING is written.
"""
import os, re, sys

ROOT = sys.argv[1]

# The failsafe each unit and probe names is EXACTLY its bill -- the identities
# NITPICK-REACH-003 lists for the program with its failsafe removed -- in the house
# order, with the ecosystem's codes (RX-149). Measured at `c3bdae2` for every file
# below; `0.0.4d.md` step 3 re-measures them.
ARMS = {
    "HeapBadRequest": 91, "HeapOom": 92, "IntOverflow": 93, "OutOfBounds": 94,
    "Unreachable": 95, "WildLeak": 96, "StackExhausted": 106, "MachineFault": 107,
    "DecreasesViolated": 108, "LimitViolated": 109,
}
ORDER = ["HeapBadRequest", "HeapOom", "IntOverflow", "OutOfBounds", "Unreachable",
         "WildLeak", "StackExhausted", "MachineFault", "DecreasesViolated", "LimitViolated"]
CORE10 = set(ORDER)


def failsafe(ids):
    w = max(len(i) for i in ids) + 2
    lines = ["func:failsafe = int32(Error:e) {", "    pick (e) {"]
    for i in [x for x in ORDER if x in ids]:
        lines.append(f"        ({i}){' ' * (w - len(i) - 2)} {{ exit {ARMS[i]}i32; }},")
    lines.append(f"        (*){' ' * (w - 3)} {{ exit 99i32; }}")
    lines += ["    }", "    exit 9i32;", "};", ""]
    return "\n".join(lines)


# ------------------------------------------------------------------ the five headers
# Each replaces everything above the file's `mod:` line. `expect-error-at: 0:0` is
# re-pinned by measurement in step 4, never by counting.
MOVED = {}

MOVED["vec_alias_double_free"] = """// expect-error: NITPICK-TYPE-046
// expect-error-at: 0:0
//
// A WHOLE-`Vec` COPY IS REFUSED: `Vec` IS MOVE-ONLY BY CONSTRUCTION SINCE
// CYCLE 0.0.4d (RX-161, `SAFETY.md` S-23b). N-15, the fourth cycle-0.0 audit's
// BL-8, closed for a copy.
//
// WHAT IT PINS. `Vec<int64>:w = v;` would copy the header -- `items`, `count`,
// `cap` -- and be a second handle on the block. Until 0.0.4d it compiled, and
// freeing both copies was a double free the `cap <= 0` guard could not see: 95
// at -O0 and through `opt -O2`, measured at `c3bdae2` (RX-160), when this file
// was `tests/unit/vec_alias_double_free.npk` with `expect-exit: 95`. Now the
// last field of `Vec`, a zero-length array of an owning type, makes it owning,
// and the copy is NITPICK-TYPE-046 before anything after it is reached.
//
// A TEST OF THE MARKER, NOT OF THIS FILE. Against the tree before 0.0.4d this
// file compiles cleanly, and so it does with the marker's element changed to a
// type that owns nothing, `int64[0]` -- both measured, `0.0.4d.md` step 5.
// `../unit/vec_moves.npk` is the positive twin: what a move-only `Vec` still
// allows compiles and runs.
"""

MOVED["vec_alias_read_after_free"] = """// expect-error: NITPICK-TYPE-046
// expect-error-at: 0:0
//
// A READ THROUGH A `Vec` COPY CANNOT HAPPEN, BECAUSE THE COPY IS REFUSED --
// `Vec` IS MOVE-ONLY BY CONSTRUCTION SINCE CYCLE 0.0.4d (RX-161, `SAFETY.md`
// S-23b). N-15, the fourth cycle-0.0 audit's BL-8, closed for a copy.
//
// WHAT IT PINS. Until 0.0.4d `Vec<int64>:w = v;` compiled, and after
// `vec_free(@v)` the copy still said `count == 1`, so `vec_get(w, 0)` passed
// both of its checks and read the reclaimed block -- the `0xAA` free poison, no
// trap, no diagnostic: exit 0 at -O0 and through `opt -O2`, measured at
// `c3bdae2` (RX-160), when this file was `tests/unit/vec_alias_read_after_free.npk`.
// Now the copy is NITPICK-TYPE-046 and the read below is never compiled.
//
// A TEST OF THE MARKER, NOT OF THIS FILE: it compiles cleanly against the tree
// before 0.0.4d and with a marker whose element owns nothing (`0.0.4d.md` step
// 5). The positive twin is `../unit/vec_moves.npk`.
"""

MOVED["vec_alias_struct_copy"] = """// expect-error: NITPICK-TYPE-046
// expect-error-at: 0:0
//
// A STRUCT HOLDING A `Vec` IS MOVE-ONLY WITH IT, SO ITS COPY IS REFUSED -- since
// cycle 0.0.4d (RX-161, `SAFETY.md` S-23b). N-15's reach, the fourth cycle-0.0
// audit's BL-8, closed for a copy.
//
// WHAT IT PINS. `Prog` is `COMPILE.md` C-1's `Program` in miniature: a `Vec` and
// a scalar. Until 0.0.4d `Prog:q = p;` compiled and copied the `Vec`'s header
// with it, so after `p`'s block was freed, `q`'s read was the `0xAA` poison --
// exit 0 at -O0 and through `opt -O2`, measured at `c3bdae2` (RX-160), when this
// file was `tests/unit/vec_alias_struct_copy.npk`. A struct owns when a field
// does, and `Vec` owns by construction now, so the copy is NITPICK-TYPE-046.
// The parser's state and cycle 0.6's `Program` are this shape: they are MOVED,
// and a copy of their contents is written element by element.
//
// A TEST OF THE MARKER, NOT OF THIS FILE: it compiles cleanly against the tree
// before 0.0.4d and with a marker whose element owns nothing (`0.0.4d.md` step
// 5). `../unit/vec_moves.npk` moves this struct and runs.
"""

MOVED["sparseset_alias_double_free"] = """// expect-error: NITPICK-TYPE-046
// expect-error-at: 0:0
//
// A WHOLE-`SparseSet` COPY IS REFUSED: ITS TWO `Vec`s MAKE IT MOVE-ONLY SINCE
// CYCLE 0.0.4d (RX-161, `SAFETY.md` S-23b). N-15's reach, the fourth cycle-0.0
// audit's BL-8, closed for a copy.
//
// WHAT IT PINS. Until 0.0.4d `SparseSet:t = s;` compiled and copied `dense` and
// `sparse` -- two `Vec` headers -- and `count`; `sset_free(@s)` freed both
// blocks through `s`, `t`'s headers still said `cap == 8`, and `sset_free(@t)`
// reached `dalloc` with reclaimed blocks: 95 at -O0 and through `opt -O2`,
// measured at `c3bdae2` (RX-160), when this file was
// `tests/unit/sparseset_alias_double_free.npk`. Now the copy is
// NITPICK-TYPE-046. The Pike VM's per-byte swap MOVES instead
// (`../unit/sparseset_alias_swap.npk`).
//
// A TEST OF THE MARKER, NOT OF THIS FILE: it compiles cleanly against the tree
// before 0.0.4d and with a marker whose element owns nothing (`0.0.4d.md` step
// 5).
"""

MOVED["sparseset_alias_read_after_free"] = """// expect-error: NITPICK-TYPE-046
// expect-error-at: 0:0
//
// THE SILENT WRONG ANSWER THROUGH A `SparseSet` COPY CANNOT HAPPEN, BECAUSE THE
// COPY IS REFUSED -- since cycle 0.0.4d (RX-161, `SAFETY.md` S-23b). The worst
// row of the fourth cycle-0.0 audit's BL-8, closed for a copy.
//
// WHAT IT PINS. Until 0.0.4d `SparseSet:t = s;` compiled; after `sset_free(@s)`
// the copy kept `count == 1` and its `sparse` header, and `sset_contains(@t, 3)`
// read `sparse[3]` from the reclaimed block -- the `0xAA` poison, a negative
// `int32` -- so it answered FALSE for the key it held while `sset_len(@t)`
// answered 1: exit 0 at -O0 and through `opt -O2`, measured at `c3bdae2`
// (RX-160), when this file was `tests/unit/sparseset_alias_read_after_free.npk`.
// In the Pike VM's thread set that is a thread lost or invented, with a green
// suite beside it. Now the copy is NITPICK-TYPE-046.
//
// NOT CLOSED BY THIS: the same wrong answer through a BY-VALUE parameter, which
// is a loan and not a copy (`../unit/sparseset_alias_param_free.npk`, RX-162).
//
// A TEST OF THE MARKER, NOT OF THIS FILE: it compiles cleanly against the tree
// before 0.0.4d and with a marker whose element owns nothing (`0.0.4d.md` step
// 5).
"""

# ------------------------------------------------------ the loan's pinned unit
PARAM_FREE_HEADER = """// expect-exit: 0
//
// A BY-VALUE PARAMETER IS A LOAN, NOT A COPY -- AND A CALLEE STILL FREES ITS
// CALLER'S `Vec` THROUGH IT. N-15's reach (the fourth cycle-0.0 audit's BL-8),
// NOT closed by cycle 0.0.4d.
//
// PINNED, NOT ENDORSED. `consume` takes `Vec<int64>` by value. Since 0.0.4d
// `Vec` is move-only (RX-161) and this still compiles, because a by-value
// parameter is a LOAN -- the compiler's D-065 and D-183: the callee may read it
// and may not keep it, so `move(v)` in `consume` would be NITPICK-TYPE-047. But
// `consume` takes its own parameter's ADDRESS and frees through it; the
// caller's `v` still says `count == 1`, and its next `vec_get` reads the
// reclaimed block -- the `0xAA` poison, exit 0 here (21: the value survived;
// 22: something else came back). Measured at `c3bdae2`, -O0 and `opt -O2`, with
// the move-only marker and without it.
//
// WHY NO TYPE CLOSES IT, AND WHOSE IT IS (RX-162). A loan is the language's
// read-only convention -- `vec_get` is one -- and the compiler does not hold a
// callee to it: `@v` is allowed and so is every write through it. For an owning
// FIELD it drops the caller's value on the write
// (`../probe/probe17_lent_field_drop.npk`, no library code). A compiler defect,
// raised as O-N21 and not worked around. The day loans are held read-only this
// file stops compiling and moves to `../rejection/`, like its four siblings
// there; the growth half is `vec_alias_param_grow.npk`.
"""

# ------------------------------------------------------------ whole new files
NEW = {}

NEW["tests/unit/sparseset_alias_swap.npk"] = """// expect-exit: 0
//
// THE SWAP `ENGINES.md` R-5 NEEDS, SPELLED WITH MOVES -- THE CONTROL THAT A
// MOVE-ONLY `Vec` LEFT THE ENGINES WRITABLE (RX-161).
//
// The Pike VM swaps its current and next thread sets every haystack byte (R-5,
// subcycle 0.7.0). Until cycle 0.0.4d this file spelled it through a temporary
// as three whole-`SparseSet` copies -- harmless only because the temporary's
// alias was never used or freed (0 at `c3bdae2`, RX-160). Since 0.0.4d a
// `SparseSet` is move-only and that spelling is NITPICK-TYPE-046 three times,
// so it is written as the language now requires, in the two shapes an engine
// can use:
//
//   1. three locals: `tmp = move(cur); cur = move(nxt); nxt = move(tmp);`
//   2. two FIELDS of a struct reached through a pointer -- the `Cache` shape
//      (`ENGINES.md` R-10) -- flipped a thousand times, with a clear and an
//      insert before each flip.
//
// Each block is freed exactly once, at the end, so `exit 0` also says no `wild`
// block leaked. 21-23: shape 1 answered a membership wrongly; 24: shape 2 found
// a member missing after a flip.
mod:sparseset_alias_swap;

use "../../src/core/sparseset.npk".*;

struct:Cache = {
    SparseSet:cur;
    SparseSet:nxt;
};

func:flip = NIL(Cache->:c) never fails {
    SparseSet:t = move(c.cur);
    c.cur = move(c.nxt);
    c.nxt = move(t);
    pass NIL;
};

func:flips = int64(int64:n) never fails {
    Cache:c = Cache{ cur: raw sset_init(16i64), nxt: raw sset_init(16i64) };
    int64:i = 0i64;
    int64:found = 0i64;
    while (i < n) decreases n - i {
        drop sset_clear(@c.nxt);
        drop sset_insert(@c.nxt, i & 15i64);
        drop flip(@c);
        if (raw sset_contains(@c.cur, i & 15i64)) { found = found + 1i64; }
        i = i + 1i64;
    }
    drop sset_free(@c.cur);
    drop sset_free(@c.nxt);
    pass found;
};

func:main = int32(cstring[]:_~argv) {
    SparseSet:cur = raw sset_init(8i64);
    SparseSet:nxt = raw sset_init(8i64);
    drop sset_insert(@cur, 1i64);
    drop sset_insert(@nxt, 5i64);
    SparseSet:tmp = move(cur);
    cur = move(nxt);
    nxt = move(tmp);
    if (!(raw sset_contains(@cur, 5i64))) { exit 21i32; }
    if (!(raw sset_contains(@nxt, 1i64))) { exit 22i32; }
    if (raw sset_contains(@cur, 1i64)) { exit 23i32; }
    drop sset_free(@cur);
    drop sset_free(@nxt);
    if ((raw flips(1000i64)) != 1000i64) { exit 24i32; }
    exit 0i32;
};

""" + failsafe(CORE10)

NEW["tests/unit/vec_alias_param_grow.npk"] = """// expect-exit: 95
//
// A CALLEE THAT GROWS A LENT `Vec` LEAVES ITS CALLER'S HEADER NAMING A FREED
// BLOCK -- the loan's second face (RX-162), beside `vec_alias_param_free.npk`.
//
// PINNED, NOT ENDORSED. `grow` takes `Vec<int64>` by value -- a loan, which
// compiles for a move-only `Vec` (RX-161) -- and pushes through its own
// parameter's address until the block moves: `ralloc` releases the old block,
// and it is the one the caller's header still names. The caller's own
// `vec_free(@v)` is then a double free the `cap <= 0` guard cannot see (its
// header still says `cap == 1`): 95, the allocator's `Unreachable`, at -O0 and
// through `opt -O2`, measured at `c3bdae2` with the marker and without it. The
// block `grow` moved to is held by nothing and would trap `WildLeak` at exit;
// 95 comes first.
//
// No type closes it, because a loan is not a copy. A compiler defect -- the
// loan is not held read-only -- raised as O-N21 and not worked around. Any exit
// but 95 means the loan changed: read the compiler's ruling before editing this
// file, which then moves to `../rejection/` if the change is a refusal.
mod:vec_alias_param_grow;

use "../../src/core/vec.npk".*;

func:grow = NIL(Vec<int64>:v) never fails {
    int64:k = 0i64;
    while (k < 64i64) decreases 64i64 - k {
        drop vec_push(@v, 9i64);
        k = k + 1i64;
    }
    pass NIL;
};

func:main = int32(cstring[]:_~argv) {
    Vec<int64>:v = raw vec_init::<int64>(1i64);
    drop vec_push(@v, 7i64);
    drop grow(v);
    drop vec_free(@v);
    exit 0i32;
};

""" + failsafe(CORE10)

NEW["tests/unit/sparseset_alias_param_free.npk"] = """// expect-exit: 0
//
// THROUGH A LENT `SparseSet`, A CALLEE FREES BOTH BLOCKS AND THE CALLER READS A
// MEMBER AS ABSENT WHILE THE COUNT SAYS ONE -- the silent wrong answer
// `../rejection/sparseset_alias_read_after_free.npk` refuses for a copy, still
// reachable through a loan (RX-162).
//
// PINNED, NOT ENDORSED. `consume` takes `SparseSet` by value -- a loan, which
// compiles for a move-only `SparseSet` (RX-161) -- and frees through its own
// parameter's address. The caller's `s` keeps `count == 1` and its headers, so
// `sset_contains(@s, 3)` reads `sparse[3]` from the reclaimed block -- the
// `0xAA` poison, a negative `int32` -- and answers FALSE for the key it holds,
// while `sset_len(@s)` answers 1. Exit 0 means that wrong answer was given, at
// -O0 and through `opt -O2`, measured at `c3bdae2` with the marker and without
// it; 21 would be the member found, 22 a count other than one.
//
// No type closes it. A compiler defect, raised as O-N21; the day loans are held
// read-only this file stops compiling and moves to `../rejection/`.
mod:sparseset_alias_param_free;

use "../../src/core/sparseset.npk".*;

func:consume = NIL(SparseSet:s) never fails {
    drop sset_free(@s);
    pass NIL;
};

func:main = int32(cstring[]:_~argv) {
    SparseSet:s = raw sset_init(8i64);
    drop sset_insert(@s, 3i64);
    drop consume(s);
    bool:has = raw sset_contains(@s, 3i64);
    int64:n = raw sset_len(@s);
    if (has) { exit 21i32; }
    if (n != 1i64) { exit 22i32; }
    exit 0i32;
};

""" + failsafe(CORE10)

NEW["tests/unit/bytes_alias_param_grow.npk"] = """// expect-exit: 95
//
// A CALLEE THAT GROWS A LENT `Bytes` FREES ITS CALLER'S BODY -- A DOUBLE FREE
// IN THE MANAGED REGIME, FOR A TYPE THAT WAS MOVE-ONLY ALL ALONG (RX-162).
//
// PINNED, NOT ENDORSED. `Bytes` holds a `buffer`, so a copy of one has always
// been NITPICK-TYPE-046 (`../rejection/bytes_copy.npk`). But `grow` takes it BY
// VALUE -- a loan -- and pushes through its own parameter's address until
// `bytes_reserve` replaces the body, `b.buf = move(bigger)`. Overwriting an
// owning field drops the old value, and through a loan the old value is the
// CALLER's: its body is freed under it. `run`'s read then sees freed memory and
// its scope-exit drop frees the body again -- 95, the allocator's `Unreachable`,
// at -O0 and through `opt -O2`, measured at `c3bdae2`. The same mechanism with
// no library code is `../probe/probe17_lent_field_drop.npk`.
//
// A compiler defect, raised as O-N21 and not worked around; every `Bytes`
// function takes `Bytes->`. Any exit but 95 means the loan changed (21: the
// caller's byte survived): read the compiler's ruling before editing this file.
mod:bytes_alias_param_grow;

use "../../src/core/bytes.npk".*;

func:grow = NIL(Bytes:b) never fails {
    int64:k = 0i64;
    while (k < 64i64) decreases 64i64 - k {
        drop bytes_push(@b, 66u8);
        k = k + 1i64;
    }
    pass NIL;
};

func:run = int32() never fails {
    Bytes:b = raw bytes_init(1i64);
    drop bytes_push(@b, 65u8);
    drop grow(b);
    uint8:x = raw bytes_get(@b, 0i64);
    if (x == 65u8) { pass 21i32; }
    pass 22i32;
};

func:main = int32(cstring[]:_~argv) {
    int32:r = raw run();
    exit r;
};

""" + failsafe(CORE10)

NEW["tests/unit/vec_moves.npk"] = """// expect-exit: 0
//
// WHAT A MOVE-ONLY `Vec` STILL ALLOWS -- THE POSITIVE TWIN OF THE FIVE COPIES
// `../rejection/` REFUSES SINCE CYCLE 0.0.4d (RX-161).
//
// Each refusal passes if the compiler refuses the copy -- and would ALSO pass
// under a compiler that refused every use of a `Vec`. This file is the other
// half, every value distinct from the vacant 0 and from the `0xAA` poison:
//   1. a whole-`Vec` MOVE, `Vec<int64>:w = move(v);`, then a read through `w`
//      (21);
//   2. a struct holding a `Vec` -- `COMPILE.md` C-1's `Program` in miniature --
//      built by moving the `Vec` in, then MOVED itself (22, 23);
//   3. a LOAN: every `vec_get` below takes its `Vec` by value, with no `move`;
//   4. `ENGINES.md` R-8's capture copy, ELEMENT BY ELEMENT into a fresh `Vec`,
//      which keeps its values after the source is freed -- the two share no
//      block (24, 25).
// Every block is freed exactly once, so `exit 0` also says none leaked.
mod:vec_moves;

use "../../src/core/vec.npk".*;

struct:Prog = {
    Vec<int64>:insts;
    int32:start;
};

func:main = int32(cstring[]:_~argv) {
    Vec<int64>:v = raw vec_init::<int64>(2i64);
    drop vec_push(@v, 7i64);
    drop vec_push(@v, 8i64);
    Vec<int64>:w = move(v);
    if ((raw vec_get(w, 1i64)) != 8i64) { exit 21i32; }
    Prog:p = Prog{ insts: move(w), start: 5i32 };
    Prog:q = move(p);
    if ((raw vec_get(q.insts, 0i64)) != 7i64) { exit 22i32; }
    if (q.start != 5i32) { exit 23i32; }
    int64:n = q.insts.count;
    Vec<int64>:c = raw vec_init::<int64>(n);
    int64:i = 0i64;
    while (i < n) decreases n - i {
        drop vec_push(@c, raw vec_get(q.insts, i));
        i = i + 1i64;
    }
    drop vec_free(@q.insts);
    if ((raw vec_get(c, 0i64)) != 7i64) { exit 24i32; }
    if ((raw vec_get(c, 1i64)) != 8i64) { exit 25i32; }
    drop vec_free(@c);
    exit 0i32;
};

""" + failsafe(CORE10)

NEW["tests/rejection/bytes_buf_ptr_write.npk"] = """// expect-error: NITPICK-TYPE-080
// expect-error-at: 0:0
//
// A CONSUMER CANNOT WRITE THROUGH `Bytes.buf` -- IT IS `hidden` SINCE CYCLE
// 0.0.4d (RX-163). The board's question 9's other item, closed.
//
// WHAT IT PINS. From 0.0.4c `buf` was `sealed`: a consumer could not assign the
// field, but `b.buf.ptr[0i64] = 65u8;` wrote THROUGH it, into the body, and
// compiled and ran -- measured at `c3bdae2`, `bytes_get` then read 65. A write
// through a sealed field's pointer is not a write of the field, which the
// compiler's D-313 says in as many words; `hidden` (D-314) refuses the member
// access itself, read or write. The capacity a consumer used to read as
// `b.buf.len` is `bytes_capacity(@b)`.
//
// A TEST OF THE QUALIFIER, NOT OF THIS FILE: against the tree before 0.0.4d it
// compiles cleanly (`0.0.4d.md` step 5).
mod:bytes_buf_ptr_write;

use "../../src/core/bytes.npk".*;

func:main = int32(cstring[]:_~argv) {
    Bytes:b = raw bytes_init(4i64);
    drop bytes_push(@b, 7u8);
    b.buf.ptr[0i64] = 65u8;
    exit 0i32;
};

// A SUPERSET of what REACH asks, on purpose: a later change in the compiler's
// phase order must not add a stray `REACH-002` beside this file's one code.
""" + failsafe(CORE10)

NEW["tests/probe/probe16_zero_length_owner.npk"] = """// expect-exit: 24
//
// PROBE 16 -- A ZERO-LENGTH ARRAY OF AN OWNING TYPE IS A FIELD THAT HOLDS
// NOTHING, OCCUPIES NOTHING, AND MAKES ITS STRUCT MOVE-ONLY. Measured at
// compiler `c3bdae2` by cycle 0.0.4d's planning; `SAFETY.md` S-23b rests on it
// (RX-161), and `src/core/vec.npk`'s `move_only` field is this shape.
//
// WHY THE LANGUAGE DOES IT. `type_drops_recorded` (`src/frontend/types.npk`,
// read at `c3bdae2` with `git show`) answers an ARRAY by its element, whatever
// the length, and layout marks a struct owning when any field is
// (`type_layout.npk`, D-183) -- and an owning type is move-only (TYPE-046). The
// array's size is its element's times zero. The empty literal `[]` is D-139's
// zero array. The compiler's own checker says `int32[0]:a = [];` "is fine".
//
// WHAT THIS PROGRAM ASSERTS, each a different exit:
//   * `Plain`, the same shape over `int64[0]` -- an element that owns nothing --
//     IS copied, and both copies read right (21, 22): ownership comes from the
//     ELEMENT, not from the array;
//   * `Marked` is built, MOVED and dropped a thousand times with the right sum
//     (23): the generated drop walks no elements and frees nothing;
//   * and the exit code IS `#size_of<Marked>()`: 24, three `int64`s and nothing
//     for the marker.
// Its refused twin is `refused/probe16b_zero_length_owner_copy.npk`, a copy of
// `Marked`, NITPICK-TYPE-046.
//
// WHEN THIS REDDENS -- a compiler that refuses `T[0]`, gives it a size, or stops
// counting its element's ownership: `SAFETY.md` S-23b's marker changes with it,
// and the fallback measured at planning is `hidden string:move_only` holding the
// literal `""`, whose drop frees nothing (+24 bytes on every `Vec`).
mod:probe16_zero_length_owner;

struct:Marked = {
    int64:a;
    int64:b;
    int64:c;
    string[0]:move_only;
};

struct:Plain = {
    int64:a;
    int64:b;
    int64:c;
    int64[0]:nothing;
};

func:hold = int64(int64:k) never fails {
    Marked:m = Marked{ a: k, b: k, c: k, move_only: [] };
    Marked:n = move(m);
    pass n.c;
};

func:main = int32(cstring[]:_~argv) {
    Plain:p = Plain{ a: 1i64, b: 2i64, c: 3i64, nothing: [] };
    Plain:q = p;
    if (q.c != 3i64) { exit 21i32; }
    if (p.c != 3i64) { exit 22i32; }
    int64:i = 0i64;
    int64:sum = 0i64;
    while (i < 1000i64) decreases 1000i64 - i {
        sum = sum + (raw hold(i));
        i = i + 1i64;
    }
    if (sum != 499500i64) { exit 23i32; }
    int64:size = #size_of<Marked>();
    exit (size =>! int32);
};

""" + failsafe({"HeapBadRequest", "HeapOom", "IntOverflow", "Unreachable", "WildLeak",
                "StackExhausted", "MachineFault", "DecreasesViolated"})

NEW["tests/probe/refused/probe16b_zero_length_owner_copy.npk"] = """// expect-error: NITPICK-TYPE-046
// expect-error-at: 0:0
//
// PROBE 16b -- A COPY OF A STRUCT WHOSE ONLY OWNING FIELD IS A ZERO-LENGTH ARRAY
// IS REFUSED, like the copy of any owner (TYPE-046, D-183). The refused twin of
// `../probe16_zero_length_owner.npk`, measured at compiler `c3bdae2` by cycle
// 0.0.4d's planning: `SAFETY.md` S-23b's marker rests on it (RX-161).
//
// It asserts the half probe 16 cannot: that the marker makes its struct OWNING
// as the compiler's move rule sees it, not merely that it compiles. The day this
// compiles cleanly, `Vec` is copyable again -- and `../../rejection/`'s five copy
// fixtures redden with it.
mod:probe16b_zero_length_owner_copy;

struct:Marked = {
    int64:a;
    string[0]:move_only;
};

func:main = int32(cstring[]:_~argv) {
    Marked:m = Marked{ a: 4i64, move_only: [] };
    Marked:n = m;
    exit (n.a =>! int32);
};

""" + failsafe({"HeapBadRequest", "HeapOom", "Unreachable", "WildLeak",
                "StackExhausted", "MachineFault"})

NEW["tests/probe/probe17_lent_field_drop.npk"] = """// expect-exit: 70
//
// PROBE 17 -- OVERWRITING AN OWNING FIELD OF A LENT PARAMETER FREES THE
// CALLER'S VALUE. A compiler defect, found at compiler `c3bdae2` by cycle
// 0.0.4d's planning and raised as O-N21 (RX-162); no library code, no `wild`,
// and no pointer cast anywhere in the program.
//
// WHAT THE LANGUAGE SAYS. An ordinary parameter is LENT: "passing transfers
// nothing", the callee may read it and may not keep it (the compiler's D-065 and
// D-183), and `move` of one is NITPICK-TYPE-047. WHAT THE COMPILER DOES: the
// assignment `b.s = …` below drops the field's old value first -- D-186's
// unconditional field drop, whose comment reasons that "the struct's owner is
// exactly who is overwriting it" (`src/backend/ir/ir_stmt.npk`, read at
// `c3bdae2`). For a lent parameter it is not: the old value is the CALLER's
// string, and its body is freed under it. So `main` reads the free poison,
// `0xAA` -- exit 70, at -O0 and through `opt -O2`. (Returned normally instead
// of exiting, the caller's own drop frees it again: 95.) The controls, measured
// the same day: the same write on a `move` parameter, and on a local, run
// clean.
//
// WHAT IT REACHES HERE: a lent `Bytes` grown by its callee dies this way
// (`../unit/bytes_alias_param_grow.npk`), and a lent `Vec` or `SparseSet` is
// freed or grown through `@` with no field write at all
// (`../unit/vec_alias_param_*.npk`, `sparseset_alias_param_free.npk`).
//
// WHEN THIS REDDENS: exit 21 is the caller's value surviving (the write no
// longer drops it); a refusal is a fix that holds loans read-only. Either way
// read the compiler's ruling, then move this probe -- to `refused/` for a
// refusal -- and the four library units with it.
mod:probe17_lent_field_drop;

struct:Box = {
    string:s;
};

func:overwrite = NIL(Box:b) never fails {
    b.s = string_concat("xyzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz", "w");
    pass NIL;
};

func:main = int32(cstring[]:_~argv) {
    Box:b = Box{ s: string_concat("abbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "c") };
    drop overwrite(b);
    uint8[]:bs = string_bytes(b.s);
    if (bs[0i64] == 97u8) { exit 21i32; }
    if (bs[0i64] == 170u8) { exit 70i32; }
    exit 71i32;
};

""" + failsafe({"HeapBadRequest", "HeapOom", "OutOfBounds", "Unreachable", "WildLeak",
                "StackExhausted", "MachineFault"})

# ------------------------------------------------------------ exact line edits
EDITS = {
    "tests/unit/bytes_unit.npk": [
        ("    if (z.buf.len < 1i64)                               { exit 11i32; }",
         "    if ((raw bytes_capacity(@z)) < 1i64)                { exit 11i32; }"),
        ("    int64:cap_before = b.buf.len;",
         "    int64:cap_before = raw bytes_capacity(@b);"),
        ("    if (b.buf.len != cap_before)                        { exit 31i32; }",
         "    if ((raw bytes_capacity(@b)) != cap_before)         { exit 31i32; }"),
        ("    int64:seen_cap = g.buf.len;",
         "    int64:seen_cap = raw bytes_capacity(@g);"),
        ("        if (g.buf.len != seen_cap) {",
         "        if ((raw bytes_capacity(@g)) != seen_cap) {"),
        ("            seen_cap = g.buf.len;",
         "            seen_cap = raw bytes_capacity(@g);"),
        ("    if (g.buf.len > 4000000i64)                         { exit 73i32; }",
         "    if ((raw bytes_capacity(@g)) > 4000000i64)          { exit 73i32; }"),
    ],
    "tests/unit/bytes_oob_get_after_clear.npk": [
        ("    if (b.buf.len < 4i64)                    { exit 32i32; }",
         "    if ((raw bytes_capacity(@b)) < 4i64)     { exit 32i32; }"),
    ],
    "tests/unit/sealed_reads.npk": [
        ("    if (b.buf.len != 4i64)                       { exit 14i32; }",
         "    if ((raw bytes_capacity(@b)) != 4i64)        { exit 14i32; }"),
        ("""// must have. `sealed` refuses a write and admits a read (the compiler's D-313);
// only `items` is `hidden` (D-314), and it is not read here.""",
         """// must have. `sealed` refuses a write and admits a read (the compiler's D-313);
// `items` and, since cycle 0.0.4d, `buf` are `hidden` (D-314; RX-163) -- the
// capacity is read through `bytes_capacity` -- and neither is read here."""),
    ],
    # SAME LINE COUNT, so the fixture's `expect-error-at: 28:5` does not move.
    "tests/rejection/bytes_len_write.npk": [
        ("""// WHAT THE SEAL DOES NOT CLOSE, stated so nobody reads this file as more: a
// write THROUGH the sealed `buf` -- `b.buf.ptr[0i64] = 65u8;` -- still compiles
// and runs from a consumer, because it writes the pointee and not the field
// (`SAFETY.md` S-23's dated note; the board's question 9). This file is about
// `len`.""",
         """// WHAT THE SEAL DID NOT CLOSE: a write THROUGH the sealed `buf` --
// `b.buf.ptr[0i64] = 65u8;` -- compiled and ran from a consumer until cycle
// 0.0.4d made `buf` `hidden` (RX-163); it is NITPICK-TYPE-080 since, and
// `bytes_buf_ptr_write.npk` is that refusal. This file is about `len`, and was
// written when `buf` was sealed; the change moved nothing in it."""),
    ],
    # SAME LINE COUNT, so the fixture's `expect-error-at: 27:5` does not move.
    "tests/rejection/bytes_copy.npk": [
        ("""// CONSTRUCTION, landing as 0.0.4d before cycle 0.0 closes. Today a `Vec` copy
// compiles and aliases its block (`../unit/vec_alias_*.npk`); on that day it is
// refused the way this one is, and those units become fixtures like this.
//
// A TEST OF THE LANGUAGE'S RULE AT THIS LIBRARY'S TYPE, NOT OF THIS FILE: the
// same program copying a `Vec` compiles, links and runs
// (`../unit/vec_alias_double_free.npk`), so the refusal here is `Bytes`' field
// and not a refusal of every whole-struct copy. Measured at `c3bdae2` (RX-160).""",
         """// CONSTRUCTION, which landed as 0.0.4d (RX-161): a `Vec` copy is refused the
// way this one is (`vec_alias_*.npk` and `sparseset_alias_*.npk` here). A loan
// is not a copy, and a `Bytes` lent to a callee that grows it still dies
// (`../unit/bytes_alias_param_grow.npk`, RX-162).
//
// A TEST OF THE LANGUAGE'S RULE AT THIS LIBRARY'S TYPE, NOT OF THIS FILE: until
// 0.0.4d the same program copying a `Vec` compiled, linked and ran, so the
// refusal here is `Bytes`' field. Measured at `c3bdae2` (RX-160)."""),
    ],
}


PIN = re.compile(r"^// expect-error-at: \d+:\d+$", re.M)


def unpinned(text):
    """The text with every measured position put back to 0:0, so a file step 4 has
    pinned still reads as ALREADY here -- a re-run after the pin must not undo it."""
    return PIN.sub("// expect-error-at: 0:0", text)


def header_swap(path, header):
    s = open(path, encoding="utf-8").read()
    i = s.index("\nmod:") + 1
    if unpinned(s[:i]) == header:
        return s, "ALREADY"
    return header + s[i:], "EDIT"


def main():
    bad, out, done, already = 0, {}, 0, 0
    for name, header in MOVED.items():
        path = os.path.join(ROOT, "tests/rejection", name + ".npk")
        if not os.path.exists(path):
            print(f"  STOP     {path}: not there -- run step 3's `git mv` first")
            bad += 1
            continue
        out[path], how = header_swap(path, header)
        done, already = done + (how == "EDIT"), already + (how == "ALREADY")
        print(f"  {how:<8} tests/rejection/{name}.npk (header)")
    path = os.path.join(ROOT, "tests/unit/vec_alias_param_free.npk")
    out[path], how = header_swap(path, PARAM_FREE_HEADER)
    done, already = done + (how == "EDIT"), already + (how == "ALREADY")
    print(f"  {how:<8} tests/unit/vec_alias_param_free.npk (header)")
    for rel, text in NEW.items():
        path = os.path.join(ROOT, rel)
        if os.path.exists(path) and unpinned(open(path, encoding="utf-8").read()) == text:
            already += 1
            print(f"  ALREADY  {rel}")
            continue
        if os.path.exists(path) and not rel.endswith("sparseset_alias_swap.npk"):
            print(f"  STOP     {rel}: exists with other content")
            bad += 1
            continue
        out[path] = text
        done += 1
        print(f"  WRITE    {rel}")
    for rel, pairs in EDITS.items():
        path = os.path.join(ROOT, rel)
        s = open(path, encoding="utf-8").read()
        before = s.count("\n")
        for n, (old, new) in enumerate(pairs, 1):
            if s.count(new) == 1:
                already += 1
                print(f"  ALREADY  {rel} #{n}")
            elif s.count(old) == 1:
                s = s.replace(old, new)
                done += 1
                print(f"  EDIT     {rel} #{n}")
            else:
                print(f"  STOP     {rel} #{n}: old x{s.count(old)}, new x{s.count(new)}")
                bad += 1
        if rel.startswith("tests/rejection/") and s.count("\n") != before:
            print(f"  STOP     {rel}: its line count moved, and so would its expect-error-at")
            bad += 1
        out[path] = s
    if bad:
        print(f"d4d_tests: {bad} stop(s) -- NOTHING WRITTEN")
        return 1
    for path, s in out.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w", encoding="utf-8").write(s)
    print(f"d4d_tests: {done} written, {already} already, of {len(MOVED)} moved headers, "
          f"1 pinned header, {len(NEW)} whole files and "
          f"{sum(len(p) for p in EDITS.values())} line edits -- 0 stops")
    return 0


sys.exit(main())

#!/usr/bin/env python3
"""0.0.4d step 2 -- the source edits: the marker, `buf` hidden, `bytes_capacity`,
and the comments the change makes false. Run: python3 d4d_src.py "$REPO".

IDEMPOTENT BY CONSTRUCTION. Every edit is an exact (old, new) pair. If `new` is
present exactly once the edit is reported ALREADY and skipped; otherwise, if `old`
occurs exactly once, it is replaced; anything else is a STOP, exit 1, and NO file is
written. So a second run changes nothing and says so, and a run
against a tree that drifted from the plan refuses rather than guessing.
"""
import datetime, os, re, sys

ROOT = sys.argv[1]
DATE = datetime.date.today().isoformat()

EDITS = {}

# ---------------------------------------------------------------- src/core/vec.npk
EDITS["src/core/vec.npk"] = [
# (1) the header's list gains item 5
("""//   4. **THE ELEMENT OWNS NOTHING** (`SAFETY.md` S-23a, RX-155). `Vec<T>` is for
//      a non-owning `T`, and NOTHING IN THE LANGUAGE SAYS SO -- the section
//      "WHAT A `Vec` MAY HOLD" below has the verbs, one by one.
//
""",
"""//   4. **THE ELEMENT OWNS NOTHING** (`SAFETY.md` S-23a, RX-155). `Vec<T>` is for
//      a non-owning `T`, and NOTHING IN THE LANGUAGE SAYS SO -- the section
//      "WHAT A `Vec` MAY HOLD" below has the verbs, one by one.
//   5. **A `Vec` IS MOVE-ONLY, AND THE COMPILER SAYS SO** (`SAFETY.md` S-23b,
//      RX-161, since cycle 0.0.4d). A copy of one -- or of any struct holding
//      one -- is NITPICK-TYPE-046. A BY-VALUE PARAMETER IS NOT A COPY, IT IS A
//      LOAN, and it still reaches the block: the section "MOVE-ONLY, AND WHAT A
//      LOAN STILL REACHES" below says how far (RX-162).
//
"""),
# (2) a new header section, after the RX-160 dated note
("""// not compile. `tests/unit/vec_alias_*.npk` and `sparseset_alias_*.npk` pin
// today's behaviour and are what 0.0.4d turns into rejection fixtures.)*
//
""",
"""// not compile. `tests/unit/vec_alias_*.npk` and `sparseset_alias_*.npk` pin
// today's behaviour and are what 0.0.4d turns into rejection fixtures.)*
//
// ============================================================================
// MOVE-ONLY, AND WHAT A LOAN STILL REACHES (S-23b; RX-161, RX-162)
// ============================================================================
//
// **SINCE CYCLE 0.0.4d A `Vec` CANNOT BE COPIED.** The struct's last field is
// `hidden string[0]:move_only` -- a fixed array of NO strings. It holds nothing
// and occupies nothing (`#size_of<Vec<int64>>()` is 24, as it was), and because
// its element type owns, the compiler's layout walk marks every `Vec<T>` as
// owning (`type_drops`, D-183) -- and an owning type is move-only. So
// `Vec<int64>:w = v;` is NITPICK-TYPE-046, and so is a copy of anything that
// holds a `Vec`: `SparseSet:t = s;`, `COMPILE.md` C-1's `Program`, the parser's
// state. A transfer is `move(v)`, which invalidates `v` (D-065). The three
// shapes the fourth cycle-0.0 audit measured through a copy -- a double free
// (95), a read of the free poison, a `SparseSet` member reading ABSENT -- no
// longer compile (`tests/rejection/vec_alias_*.npk`, `sparseset_alias_*.npk`).
// Measured at `c3bdae2`: the drop the compiler now generates for a `Vec` walks
// the empty array and frees NOTHING -- the block stays `wild`, freed only by
// `vec_free`, and a `Vec` never freed still traps `WildLeak` at `exit 0` -- and
// no consumer's `failsafe` bill moves. A marker whose element owns nothing,
// `int64[0]`, changes nothing at all: the element's ownership is the mechanism.
//
// **A BY-VALUE PARAMETER IS A LOAN, NOT A COPY, AND IT STILL REACHES THE
// BLOCK.** An ordinary parameter is one the callee may read and may not keep
// (the compiler's D-065 and D-183): a move-only `Vec` is passed to one WITHOUT
// `move`, and `move(v)` inside the callee is NITPICK-TYPE-047. `vec_get` below
// is such a reader and keeps its signature. But the callee may take its own
// parameter's address, `@v`, and free or grow through it, and the caller's
// header then names a block the callee released: a read of the free poison, a
// double free (95), a `SparseSet` member ABSENT with no trap
// (`tests/unit/vec_alias_param_*.npk`, `sparseset_alias_param_free.npk`). For
// an owning FIELD the compiler goes further: overwriting one through a lent
// parameter DROPS THE CALLER'S VALUE -- a double free with no `wild` block in
// the program (`tests/probe/probe17_lent_field_drop.npk`), which is how a lent
// `Bytes` grown by its callee dies (`bytes_alias_param_grow.npk`). No type here
// can refuse a loan. That is a compiler defect, raised and not worked around
// (RX-162); until it is fixed, a callee that must change a `Vec` takes
// `Vec<T>->`, as every function below does.
//
"""),
# (3) the paragraph above `struct:Vec` gains its dated note
("""// author's answer, MOVE-ONLY BY CONSTRUCTION at 0.0.4d before cycle 0.0
// closes, changes its signature and every by-value read in `src/core/`.)*
pub struct:Vec<T> = {""",
"""// author's answer, MOVE-ONLY BY CONSTRUCTION at 0.0.4d before cycle 0.0
// closes, changes its signature and every by-value read in `src/core/`.)*
// *(Dated @@DATE@@, cycle 0.0.4d -- RX-161, RX-162. The copy is closed by the
// last field below; the header's "MOVE-ONLY, AND WHAT A LOAN STILL REACHES"
// says how. The last clause above is FALSE, measured at `c3bdae2`: a by-value
// parameter is a LOAN, which compiles for an owning type without `move`, so
// `vec_get` and every by-value read in `src/core/` are unchanged. What a loan
// reaches is not closed by any type, and the header says whose it is.)*
pub struct:Vec<T> = {"""),
# (4) the marker
("""    sealed limit<ListLen> int64:cap;       // elements the block can hold
};""",
"""    sealed limit<ListLen> int64:cap;       // elements the block can hold
    hidden string[0]:move_only;            // ZERO BYTES, HOLDS NOTHING -- AND MAKES `Vec` MOVE-ONLY (RX-161)
};"""),
# (5), (6) the two constructors fill it with D-139's zero array
("""    pass Vec{ items: mem =>! wild T->, count: 0i64, cap: n };""",
 """    pass Vec{ items: mem =>! wild T->, count: 0i64, cap: n, move_only: [] };"""),
("""    pass Vec{ items: mem =>! wild T->, count: n, cap: k };""",
 """    pass Vec{ items: mem =>! wild T->, count: n, cap: k, move_only: [] };"""),
# (7) vec_get's parameter is a loan
("""// is a bounds-checked place -- and that is the shape a cycle lifting S-23a
// would take (RX-155).
pub func:vec_get<T> = T(Vec<T>:v, int64:i) never fails {""",
"""// is a bounds-checked place -- and that is the shape a cycle lifting S-23a
// would take (RX-155).
//
// ITS `Vec` IS A LOAN, NOT A COPY (the compiler's D-065 and D-183: an ordinary
// parameter is one the callee may read and may not keep). Since cycle 0.0.4d
// `Vec` is move-only, and a loan still needs no `move` -- which is what lets a
// consumer read a sealed field, `vec_get(s.sparse, k)`, without taking the
// address D-313 counts as a write. The fourth cycle-0.0 audit expected
// move-only to change this signature; measured at `c3bdae2`, it does not
// (RX-162). Nothing here writes through `v`, which is the whole of what makes a
// loan safe while the compiler does not hold a callee to it.
pub func:vec_get<T> = T(Vec<T>:v, int64:i) never fails {"""),
# (8) Q-6 is answered -- RX-130's section
("""// trap's identity. So the obligations below stay comments, by
// `meta/OPEN_QUESTIONS.md` Q-6, which carries this cost -- RX-152.)*""",
"""// trap's identity. So the obligations below stay comments, by
// `meta/OPEN_QUESTIONS.md` Q-6, which carries this cost -- RX-152.)*
// *(Dated @@DATE@@, cycle 0.0.4d: Q-6 is answered -- A′, RX-164,
// `VERIFICATION.md` P-1b. An obligation stays a comment unless a numbered
// decision accepts the arm its live clause adds to every consumer, and none is
// taken here, so this stop keeps its identity, 94.)*"""),
# (9) and (10) vec_oob's obligation paragraph
("""// obligation, in the syntax it takes since the compiler's 1.5.3 (a comment by
// `meta/OPEN_QUESTIONS.md` Q-6 until it is answered):""",
"""// obligation, in the syntax it takes since the compiler's 1.5.3 (a comment,
// by A′ -- `VERIFICATION.md` P-1b, RX-164, the answer to
// `meta/OPEN_QUESTIONS.md` Q-6):"""),
("""// and at `c3bdae2`, where it would be live, it is a comment by Q-6.**""",
 """// and at `c3bdae2`, where it would be live, it is a comment by A′ (RX-164).**"""),
]

# --------------------------------------------------------------- src/core/bytes.npk
EDITS["src/core/bytes.npk"] = [
# (1) a loaned `Bytes` -- the ownership section
("""// `Bytes[2]` compiles and runs at `c3bdae2` -- and what TYPE-046 asks is that a
// read of one out of the array be a `move`. A `Vec` may not hold one, by
// `SAFETY.md` S-23a, RX-155.)*""",
"""// `Bytes[2]` compiles and runs at `c3bdae2` -- and what TYPE-046 asks is that a
// read of one out of the array be a `move`. A `Vec` may not hold one, by
// `SAFETY.md` S-23a, RX-155.)*
// *(Dated @@DATE@@, cycle 0.0.4d -- RX-162. Move-only does not make a BY-VALUE
// `Bytes` safe: a by-value parameter is a LOAN, and a callee that grows it
// through its own parameter's address, `bytes_push(@b, x)`, overwrites `buf`
// -- and the compiler drops the CALLER's body there, so the caller's own drop
// is a double free, 95 (`tests/unit/bytes_alias_param_grow.npk`; the form with
// no library code is `tests/probe/probe17_lent_field_drop.npk`). A compiler
// defect, raised and not worked around; every function here takes `Bytes->`.)*"""),
# (2) sealed -> hidden, the paragraph above the struct
("""// still this library's and the tree check's, and not the compiler's; `hidden
// buf` would close it and is the board's question 9, not this subcycle's.""",
"""// still this library's and the tree check's, and not the compiler's; `hidden
// buf` would close it and is the board's question 9, not this subcycle's.
// *(Dated @@DATE@@, cycle 0.0.4d -- RX-163: `buf` IS `hidden` NOW. Outside this
// module `b.buf` is NITPICK-TYPE-080, the write through `.ptr` included
// (`tests/rejection/bytes_buf_ptr_write.npk`), and the capacity is read
// through `bytes_capacity`. The rule above is the compiler's for a consumer;
// the tree check stays for this file's own use, as it does for `vec.npk`.)*"""),
# (3) the field
("""    sealed buffer:buf;                   // MANAGED, owning, dropped at scope exit. Capacity is `buf.len`.""",
 """    hidden buffer:buf;                   // MANAGED, owning, dropped at scope exit. Capacity: `bytes_capacity`."""),
# (4) the accessor
("""// obligation: never fails ensures result == b.len
pub func:bytes_len = int64(Bytes->:b) never fails {
    pass b.len;
};
""",
"""// obligation: never fails ensures result == b.len
pub func:bytes_len = int64(Bytes->:b) never fails {
    pass b.len;
};

// obligation: never fails ensures result == b.buf.len
//
// THE CAPACITY, and the only way a consumer reads it since cycle 0.0.4d, when
// `buf` became `hidden` (RX-163). It is `buf.len`, the size of the managed body,
// which is what `bytes_reserve` grows -- never `b.len`, the bytes in use.
pub func:bytes_capacity = int64(Bytes->:b) never fails {
    pass b.buf.len;
};
"""),
]

# ---------------------------------------------------------------- src/core/core.npk
EDITS["src/core/core.npk"] = [
("""pub use "./bytes.npk".bytes_len;
""",
 """pub use "./bytes.npk".bytes_len;
pub use "./bytes.npk".bytes_capacity;
"""),
]

# ----------------------------------------------------------- src/core/sparseset.npk
EDITS["src/core/sparseset.npk"] = [
("""// cannot index `.items` at all -- every access here goes through `vec_get` and
// `vec_set` because nothing else compiles.
pub struct:SparseSet = {""",
"""// cannot index `.items` at all -- every access here goes through `vec_get` and
// `vec_set` because nothing else compiles.
//
// AND SINCE CYCLE 0.0.4d A `SparseSet` IS MOVE-ONLY, BECAUSE ITS FIELDS ARE
// (RX-161; `SAFETY.md` S-23b). A struct owns when a field does, and `Vec` owns
// by construction, so `SparseSet:t = s;` is NITPICK-TYPE-046 -- the copy that
// read a member ABSENT after the free (`tests/rejection/sparseset_alias_*.npk`).
// The Pike VM's per-byte swap is three moves (`ENGINES.md` R-5;
// `tests/unit/sparseset_alias_swap.npk`). A `SparseSet` passed BY VALUE is a
// loan and still reaches both blocks (`sparseset_alias_param_free.npk`), so a
// callee that changes one takes `SparseSet->`, as every function here does
// (RX-162).
pub struct:SparseSet = {"""),
]


def main():
    bad, out, edits, already = 0, {}, 0, 0
    for rel, pairs in EDITS.items():
        path = os.path.join(ROOT, rel)
        s = open(path, encoding="utf-8").read()
        for n, (old, new) in enumerate(pairs, 1):
            # A dated `new` is matched with ANY date, so a re-run on a later day
            # still recognises its own edit instead of stopping on it. `new`
            # present once is ALREADY whatever `old` does, because most edits
            # here APPEND to `old` and so leave it inside `new`.
            pat = re.escape(new).replace(re.escape("@@DATE@@"), r"\d{4}-\d{2}-\d{2}")
            new = new.replace("@@DATE@@", DATE)
            co, cn = s.count(old), len(re.findall(pat, s))
            if cn == 1:
                already += 1
                print(f"  ALREADY  {rel} #{n}")
            elif cn == 0 and co == 1:
                s = s.replace(old, new)
                edits += 1
                print(f"  EDIT     {rel} #{n}")
            else:
                print(f"  STOP     {rel} #{n}: old x{co}, new x{cn}")
                bad += 1
        out[path] = s
    if bad:
        print(f"d4d_src: {bad} stop(s) -- NOTHING WRITTEN")
        return 1
    for path, s in out.items():
        open(path, "w", encoding="utf-8").write(s)
    print(f"d4d_src: {edits} edited, {already} already, over {len(EDITS)} files -- 0 stops")
    return 0


sys.exit(main())

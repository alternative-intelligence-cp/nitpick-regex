"""0.0.4e step 2 -- the source: `Pod` and `vec_get<T: Pod>`, `vec_pop`'s spelled
move, the umbrella's re-export, and the comments the re-pin makes false.
Applied by `python3 e4e_edit.py src "$REPO"`; the engine's docstring says how.

WHY, in one line each (`0.0.4e.md` §1.2, §1.3; PD-12, recorded as RX-168):
  * at `c970483` the compiler refuses `vec_get`'s `pass v.items[i]` and `vec_pop`'s
    `pass v.items[v.count]`, NITPICK-TYPE-047, at every `T` (DEF-104's gate);
  * `vec_pop` takes the prelude's own spelling, `pass move(...)`;
  * `vec_get` reads through `Pod`, whose one `never fails` method an owning type
    cannot implement as declared -- so `vec_get` at an owning `T` is refused.
"""

_SCALARS = ["int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64", "bool"]
_IMPLS = "".join(
    f"impl:{t}:Pod = {{ func:pod_copy = {t}({t}:self) never fails {{ pass self; }}; }};\n"
    for t in _SCALARS)

EDITS = {}

# ------------------------------------------------------------------ src/core/vec.npk
EDITS["src/core/vec.npk"] = [
# (1) the header's item 4 gains the compiler's half
("""//   4. **THE ELEMENT OWNS NOTHING** (`SAFETY.md` S-23a, RX-155). `Vec<T>` is for
//      a non-owning `T`, and NOTHING IN THE LANGUAGE SAYS SO -- the section
//      "WHAT A `Vec` MAY HOLD" below has the verbs, one by one.
""",
"""//   4. **THE ELEMENT OWNS NOTHING** (`SAFETY.md` S-23a, RX-155). `Vec<T>` is for
//      a non-owning `T`, and NOTHING IN THE LANGUAGE SAYS SO -- the section
//      "WHAT A `Vec` MAY HOLD" below has the verbs, one by one.
//      *(Since cycle 0.0.4e THE COMPILER SAYS SO FOR `vec_get`, the one verb
//      that hands an element back: it takes `T: Pod`, and an owning type
//      cannot implement `Pod` as it is declared -- RX-168.)*
"""),
# (2) the header's item 5 gains the loan's refusal
("""//      one -- is NITPICK-TYPE-046. A BY-VALUE PARAMETER IS NOT A COPY, IT IS A
//      LOAN, and it still reaches the block: the section "MOVE-ONLY, AND WHAT A
//      LOAN STILL REACHES" below says how far (RX-162).
""",
"""//      one -- is NITPICK-TYPE-046. A BY-VALUE PARAMETER IS NOT A COPY, IT IS A
//      LOAN, and it still reaches the block: the section "MOVE-ONLY, AND WHAT A
//      LOAN STILL REACHES" below says how far (RX-162).
//      *(Since cycle 0.0.4e, compiler `c970483`, the compiler holds the loan
//      READ-ONLY: `@v` of a lent `Vec` is NITPICK-TYPE-085 -- RX-169.)*
"""),
# (3) the MOVE-ONLY section's RX-167 note gains the re-pin's measurement
("""// function below has either shape: no generic here takes a lent bare `T`, and
// there is no `for`. Both are pinned, not endorsed, and the re-pin to a compiler
// carrying 3g measures whether each is refused.)*
""",
"""// function below has either shape: no generic here takes a lent bare `T`, and
// there is no `for`. Both are pinned, not endorsed, and the re-pin to a compiler
// carrying 3g measures whether each is refused.)*
//
// *(Dated @@DATE@@, cycle 0.0.4e, compiler `c970483` -- RX-169. The re-pin
// measured each face, and all are REFUSED: a write through a lent container --
// `@v` of a parameter, `@x` of a `for` binding, an owning field overwritten --
// is NITPICK-TYPE-085 (the compiler's DEF-102), and the generic pass-out is
// NITPICK-TYPE-047 (DEF-104). The six pins and probe 17 are refusals now, each
// refused exactly its code at the `@` or the `pass`, and each still RUNS at
// `c3bdae2`, so each refusal is the pin's (`tests/rejection/vec_alias_param_*`,
// `sparseset_alias_param_free`, `bytes_alias_param_grow`,
// `vec_alias_for_binding_free`, `vec_alias_generic_passout`;
// `tests/probe/refused/probe17_lent_field_drop`). The spellings the refusals
// prescribe run clean (`tests/unit/loan_spellings.npk`): a callee that frees
// takes `move Vec<T>:v` and its caller writes `move(v)`, one that grows takes
// `Vec<T>->`. "No generic here takes a lent bare `T`" stays true and was not
// the whole of DEF-104's reach: it refuses a `T` PLACE passed out of a lent or
// pointed-to container too, which was `vec_get` and `vec_pop` -- see each
// (RX-168).)*
"""),
# (4) the S-23a section: vec_get's row is the compiler's now
("""// decision, and the compiler's own `List<T>` is the shape it would take:
// removals that return the element, discards that drop it, and no by-value get.
""",
"""// decision, and the compiler's own `List<T>` is the shape it would take:
// removals that return the element, discards that drop it, and no by-value get.
// *(Dated @@DATE@@, cycle 0.0.4e, compiler `c970483` -- RX-168. The table's
// second row is a COMPILE ERROR now. The pin refuses `vec_get` as it was written
// at every `T` -- a generic body is checked once with `T` owning (D-264), and
// since DEF-104 that is asked of a `T` place passed out of a loan too -- so
// `vec_get` takes `T: Pod`, and at `Vec<string>` it is NITPICK-TYPE-017
// (`tests/rejection/vec_owning_get_moves_out.npk`). The other rows are unchanged,
// and S-23a and its check stand for them.)*
"""),
# (5) the paragraph above `struct:Vec`: its 0.0.4d note's "vec_get ... unchanged"
("""// `vec_get` and every by-value read in `src/core/` are unchanged. What a loan
// reaches is not closed by any type, and the header says whose it is.)*
pub struct:Vec<T> = {""",
"""// `vec_get` and every by-value read in `src/core/` are unchanged. What a loan
// reaches is not closed by any type, and the header says whose it is.)*
// *(Dated @@DATE@@, cycle 0.0.4e, compiler `c970483` -- RX-168, RX-169.
// `vec_get` keeps its by-value `Vec<T>:v` and gains a bound, `T: Pod`, because
// the pin refuses its old body; and a loan IS closed now -- by the compiler,
// which refuses every write through one, NITPICK-TYPE-085.)*
pub struct:Vec<T> = {"""),
# (6) `Pod`, declared above the accessor pair
("""// ---- the checked accessor pair ---------------------------------------------
""",
"""// ---- `Pod`: what `vec_get` may hand back by value (S-23a; RX-168) -----------
//
// ONE METHOD, AND THE LANGUAGE DECIDES WHO MAY IMPLEMENT IT. `pod_copy` takes
// its `self` LENT and returns a `Self`, never failing. For a type that owns
// nothing, `pass self` is its copy; for an owning type the same body is
// NITPICK-TYPE-047 -- a lent owner cannot be passed on -- so an impl the
// compiler admits for one would have to build an independent value. That is what
// makes `T: Pod` on `vec_get` S-23a's rule stated TO THE COMPILER, at every
// consumer's instantiation, and not only by `check_vec_elements_own_nothing` over
// `src/`. Measured at `c970483`: `impl:string:Pod`, `impl:Bytes:Pod`,
// `impl:SparseSet:Pod` and `impl:Vec<int64>:Pod`, each written `pass self`, are
// each NITPICK-TYPE-047.
//
// THE SCALARS ARE HERE -- the integers to 64 bits and `bool`, every scalar this
// library's specifications store in a `Vec`. A struct that owns nothing
// implements it where it is declared, in one line like these; `core.npk`
// re-exports the name so a consumer can. A wider scalar is one line here.
//
// THE HOLE, stated where a reader meets it: the compiler also accepts an impl
// that declares its `self` `move` where the trait lends it, and a call through
// the trait then hands the callee a value the caller still owns -- a double
// free (95). @@DEFECT@@; `tests/probe/probe18_impl_adds_move.npk` pins it with no
// library code. No impl here does it, and the harness's S-23a check still
// refuses an owning element anywhere in `src/`.
pub trait:Pod = {
    func:pod_copy = Self(Self:self) never fails;
};
""" + _IMPLS + """
// ---- the checked accessor pair ---------------------------------------------
"""),
# (7) vec_get: the note, the bound, the read
("""// (RX-162). Nothing here writes through `v`, which is the whole of what makes a
// loan safe while the compiler does not hold a callee to it.
pub func:vec_get<T> = T(Vec<T>:v, int64:i) never fails {
    if (i < 0i64)        { drop vec_oob(i); }
    if (i >= v.count)    { drop vec_oob(i); }
    pass v.items[i];
};""",
"""// (RX-162). Nothing here writes through `v`, which is the whole of what makes a
// loan safe while the compiler does not hold a callee to it.
//
// *(Dated @@DATE@@, cycle 0.0.4e, compiler `c970483` -- RX-168. THE FIRST
// PARAGRAPH IS HISTORY. The pin refuses this body as it was, at every `T`:
// `pass v.items[i]` passes a `T` PLACE out of a lent parameter, and since the
// compiler's DEF-104 a bare `T` owns for that question -- NITPICK-TYPE-047, "this
// parameter was lent, not given". The language's copy of a `T` place is
// `.clone()` under `Clone`, whose `clone` the prelude declares MAY FAIL, so in a
// `never fails` body it is a `Result<T>` (NITPICK-TYPE-007; NITPICK-TYPE-042
// under `raw`). So this asks for `T: Pod` and reads through `pod_copy`, and at an
// owning `T` it is NITPICK-TYPE-017 -- the move the first paragraph describes
// cannot be written any more. Its `Vec` is still a loan, read-only now
// (NITPICK-TYPE-085); a consumer still reads a sealed field by value,
// `vec_get(s.sparse, k)`.)*
pub func:vec_get<T: Pod> = T(Vec<T>:v, int64:i) never fails {
    if (i < 0i64)        { drop vec_oob(i); }
    if (i >= v.count)    { drop vec_oob(i); }
    pass raw v.items[i].pod_copy();
};"""),
# (8) vec_pop: the move spelled
("""// pop is the caller's error and traps rather than returning a value nobody
// chose (D-123: a default that carries meaning is a value nobody chose).
pub func:vec_pop<T> = T(Vec<T>->:v) never fails {
    if (v.count <= 0i64) { drop vec_oob(v.count - 1i64); }
    v.count = v.count - 1i64;
    pass v.items[v.count];
};""",
"""// pop is the caller's error and traps rather than returning a value nobody
// chose (D-123: a default that carries meaning is a value nobody chose).
// *(Dated @@DATE@@, cycle 0.0.4e, compiler `c970483` -- RX-168. The move is
// SPELLED now. `pass v.items[v.count]` passes a `T` place out of what a pointer
// reaches, and at `c970483` that is NITPICK-TYPE-047 at every `T` (DEF-104;
// D-264's `T` owns). `move(...)` is the prelude's own `list_pop`, and it is what
// the implicit move did: diffed at `c3bdae2`, `vec_pop<string>` writes the same
// vacancy into the slot past `count`, plus one temporary and its flag.)*
pub func:vec_pop<T> = T(Vec<T>->:v) never fails {
    if (v.count <= 0i64) { drop vec_oob(v.count - 1i64); }
    v.count = v.count - 1i64;
    pass move(v.items[v.count]);
};"""),
]

# ----------------------------------------------------------------- src/core/core.npk
EDITS["src/core/core.npk"] = [
("""pub use "./vec.npk".vec_get;
""",
"""pub use "./vec.npk".vec_get;
pub use "./vec.npk".Pod;
"""),
]

# ---------------------------------------------------------------- src/core/bytes.npk
EDITS["src/core/bytes.npk"] = [
("""// no library code is `tests/probe/probe17_lent_field_drop.npk`). A compiler
// defect, raised and not worked around; every function here takes `Bytes->`.)*
""",
"""// no library code is `tests/probe/probe17_lent_field_drop.npk`). A compiler
// defect, raised and not worked around; every function here takes `Bytes->`.)*
// *(Dated @@DATE@@, cycle 0.0.4e, compiler `c970483` -- RX-169. Refused now: the
// `@b` is NITPICK-TYPE-085, the compiler's DEF-102, so a lent `Bytes` is
// read-only; both files are refusals, `tests/rejection/bytes_alias_param_grow.npk`
// and `tests/probe/refused/probe17_lent_field_drop.npk`.)*
"""),
]

# ------------------------------------------------------------ src/core/sparseset.npk
EDITS["src/core/sparseset.npk"] = [
("""// loan and still reaches both blocks (`sparseset_alias_param_free.npk`), so a
// callee that changes one takes `SparseSet->`, as every function here does
// (RX-162).
""",
"""// loan and still reaches both blocks (`sparseset_alias_param_free.npk`), so a
// callee that changes one takes `SparseSet->`, as every function here does
// (RX-162). *(Since cycle 0.0.4e, compiler `c970483`, the compiler refuses the
// `@` of a lent `SparseSet`, NITPICK-TYPE-085, and that file is a refusal in
// `tests/rejection/` -- RX-169.)*
"""),
]

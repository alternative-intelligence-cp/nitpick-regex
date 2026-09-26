"""0.0.4e step 3 -- the tests: the nine moved files' headers, two lines that name a
`T`, one read removed, two new files, and the comments the re-pin makes false.
Applied by `python3 e4e_edit.py tests "$REPO"` AFTER step 3's nine `git mv`s -- a
moved file absent from its new path is a STOP. The engine's docstring says how.

The moves (made by the step, not here):
  tests/unit/{vec_alias_param_free,vec_alias_param_grow,sparseset_alias_param_free,
              bytes_alias_param_grow,vec_alias_for_binding_free,
              vec_alias_generic_passout,vec_owning_get_moves_out}.npk -> tests/rejection/
  tests/probe/probe17_lent_field_drop.npk            -> tests/probe/refused/
  tests/probe/refused/probe15_block_string_close.npk -> tests/probe/
Every new `expect-error-at` is `0:0` here and MEASURED by step 4's `pin`.
"""

HEADERS = {}

HEADERS["tests/rejection/vec_alias_param_free.npk"] = (
"ec87beffb2ac23bee5b7e3bf725e0c99bac549ccfbc0bac5e73a1c02d0672660",
"""// expect-error: NITPICK-TYPE-085
// expect-error-at: 0:0
//
// A CALLEE CANNOT FREE ITS CALLER'S `Vec` THROUGH A LOAN: A PLAIN BY-VALUE
// PARAMETER OF AN OWNING TYPE IS READ-ONLY SINCE THE COMPILER'S 1.6.0 STEP 3g
// (DEF-102, the workbench registry's O-N21), carried by the pin `c970483` --
// cycle 0.0.4e, RX-169. N-15's loan face (the fourth cycle-0.0 audit's BL-8),
// closed.
//
// WHAT IT PINS. `consume` takes `Vec<int64>` by value -- a LOAN (the compiler's
// D-065 and D-183) -- and frees through its own parameter's address. Through
// `c3bdae2` that compiled, and the caller's next `vec_get` read the reclaimed
// block, the `0xAA` poison: exit 0 at -O0 and through `opt -O2`, when this file
// was `tests/unit/vec_alias_param_free.npk`, PINNED, NOT ENDORSED (RX-162). At
// `c970483` the `@v` is NITPICK-TYPE-085, "a plain parameter of an owning type
// is LENT", and nothing after it is reached.
//
// THE FREE NAMES ITS `T`, `vec_free::<int64>`, so the refusal is the only
// diagnostic: written `vec_free(@v)`, the refused argument leaves `T` nothing to
// be inferred from, and the compiler adds NITPICK-TYPE-022 at the same call -- a
// code about the cascade, not the loan (measured at `c970483`).
//
// THE REFUSAL IS THE PIN'S: this file still compiles and runs at `c3bdae2`, exit
// 0 at both levels (`meta/roadmap/0.0/0.0.4e.md` step 5). Its positive twin,
// `../unit/loan_spellings.npk`, frees through a `move Vec<int64>:v` parameter and
// grows through `Vec<int64>->`, the spellings TYPE-085's message names.
""")

HEADERS["tests/rejection/vec_alias_param_grow.npk"] = (
"29ca3496ffc59d3f96834f5d2fe91c9fb1410be774d01b7d38c5753dd95a8237",
"""// expect-error: NITPICK-TYPE-085
// expect-error-at: 0:0
//
// A CALLEE CANNOT GROW ITS CALLER'S `Vec` THROUGH A LOAN -- the loan's second
// face, refused NITPICK-TYPE-085 since the compiler's 1.6.0 step 3g (DEF-102),
// carried by the pin `c970483` -- cycle 0.0.4e, RX-169.
//
// WHAT IT PINS. `grow` pushes through its own lent parameter's address until
// `ralloc` moves the block. Through `c3bdae2` that compiled, and the caller's own
// `vec_free(@v)` then freed the block `ralloc` had already released -- 95, the
// allocator's `Unreachable`, at -O0 and through `opt -O2`, when this file was
// `tests/unit/vec_alias_param_grow.npk`, PINNED, NOT ENDORSED (RX-162). At
// `c970483` the `@v` in `grow` is refused, and nothing after it is reached. It
// still compiles and runs, 95, at `c3bdae2`: the refusal is the pin's
// (`meta/roadmap/0.0/0.0.4e.md` step 5). A callee that grows its caller's `Vec`
// takes it by pointer, `Vec<int64>->` -- `../unit/loan_spellings.npk`.
""")

HEADERS["tests/rejection/sparseset_alias_param_free.npk"] = (
"a5e6d8d1610f95d15cc963b69604f60e2c52ec841dd709c7a369d87a413d24e3",
"""// expect-error: NITPICK-TYPE-085
// expect-error-at: 0:0
//
// A CALLEE CANNOT FREE ITS CALLER'S `SparseSet` THROUGH A LOAN -- refused
// NITPICK-TYPE-085 since the compiler's 1.6.0 step 3g (DEF-102), carried by the
// pin `c970483` -- cycle 0.0.4e, RX-169. The silent wrong answer
// `sparseset_alias_read_after_free.npk` beside it refuses for a copy, refused
// here for a loan.
//
// WHAT IT PINS. Through `c3bdae2` `consume` freed both blocks through its lent
// parameter's address, and the caller then read member 3 ABSENT while `sset_len`
// said 1 -- exit 0 at -O0 and through `opt -O2`, when this file was
// `tests/unit/sparseset_alias_param_free.npk`, PINNED, NOT ENDORSED (RX-162). At
// `c970483` the `@s` is refused. It still runs, 0, at `c3bdae2`: the refusal is
// the pin's (`meta/roadmap/0.0/0.0.4e.md` step 5). A callee that frees a
// `SparseSet` takes it as `move SparseSet:s` -- `../unit/loan_spellings.npk`.
""")

HEADERS["tests/rejection/bytes_alias_param_grow.npk"] = (
"035494b8de17476a3d07ccfe2590dc2859a2a43c3c7f26a61b54b74b4a66e729",
"""// expect-error: NITPICK-TYPE-085
// expect-error-at: 0:0
//
// A CALLEE CANNOT GROW ITS CALLER'S `Bytes` THROUGH A LOAN -- refused
// NITPICK-TYPE-085 since the compiler's 1.6.0 step 3g (DEF-102), carried by the
// pin `c970483` -- cycle 0.0.4e, RX-169.
//
// WHAT IT PINS. Through `c3bdae2` `grow` pushed through its lent parameter's
// address until `bytes_reserve` replaced the body, `b.buf = move(bigger)`; that
// overwrite dropped the CALLER's body, and the caller's own drop freed it again
// -- 95 at -O0 and through `opt -O2`, when this file was
// `tests/unit/bytes_alias_param_grow.npk`, PINNED, NOT ENDORSED (RX-162). The
// same mechanism with no library code is
// `../probe/refused/probe17_lent_field_drop.npk`, refused the same way. It still
// runs, 95, at `c3bdae2`: the refusal is the pin's (`meta/roadmap/0.0/0.0.4e.md`
// step 5). A callee that grows a `Bytes` takes `Bytes->`, as every function in
// `bytes.npk` does -- `../unit/loan_spellings.npk`.
""")

HEADERS["tests/rejection/vec_alias_for_binding_free.npk"] = (
"b23d02fcb708d22a202500cfc618ad41bcffb0293b788b85d26a0f7cb968b50e",
"""// expect-error: NITPICK-TYPE-085
// expect-error-at: 0:0
//
// A `for` BINDING OVER AN ARRAY OF CONTAINERS IS A LOAN, AND A WRITE THROUGH IT
// IS REFUSED -- NITPICK-TYPE-085 at `@x`, since the compiler's 1.6.0 step 3g
// (DEF-102), carried by the pin `c970483` -- cycle 0.0.4e, RX-169. The fifth
// cycle-0.0 audit's N-26, measured rather than assumed: 3g closes the loan for
// this shape too, so cycle 0.0's gate holds for it.
//
// WHAT IT PINS. `for (Vec<int64>:x in arr) { drop vec_free(@x); }` binds each
// element as a parameter is bound -- the parser builds it as a `ParamDecl` -- so
// `x` is lent, and through `c3bdae2` the loop freed each element's block through
// it; `arr[0]` then read the free poison -- exit 0 at -O0 and through `opt -O2`,
// when this file was `tests/unit/vec_alias_for_binding_free.npk`, PINNED, NOT
// ENDORSED (RX-167). The free NAMES ITS `T`, `vec_free::<int64>`, so the refusal
// is the only diagnostic: written `vec_free(@x)` the compiler adds
// NITPICK-TYPE-022 at the same call, the refused argument's cascade (measured at
// `c970483`). It still runs, 0, at `c3bdae2`: the refusal is the pin's
// (`meta/roadmap/0.0/0.0.4e.md` step 5). A loop READS its binding and the array
// frees its own elements -- `../unit/loan_spellings.npk`.
""")

HEADERS["tests/rejection/vec_alias_generic_passout.npk"] = (
"47824408747be5f570c4c769c5d9ccb0f6be91973a63657d0df70d0aa52569a8",
"""// expect-error: NITPICK-TYPE-047
// expect-error-at: 0:0
//
// A GENERIC FUNCTION CANNOT HAND BACK ITS LENT `T` -- NITPICK-TYPE-047 at the
// `pass`, since the compiler's 1.6.0 step 3g (DEF-104, the workbench registry's
// O-N22), carried by the pin `c970483` -- cycle 0.0.4e, RX-169. The fifth
// cycle-0.0 audit's N-25.
//
// WHAT IT PINS. `func:id<T> = T(T:x) { pass x; }` passes on a loan. Through
// `c3bdae2` TYPE-047 was not asked of a lent `T` in a generic body -- its gate
// asked `type_drops`, false for an unsubstituted `T` -- so at `T = Vec<int64>` the
// result was a second owner of the block: after `vec_free(@a)` a read through it
// returned the free poison, exit 0 at -O0 and through `opt -O2`, when this file
// was `tests/unit/vec_alias_generic_passout.npk`, PINNED, NOT ENDORSED (RX-167).
// At `c970483` the gate asks `type_owns_for_move` -- D-264's predicate, a bare
// `T` owns -- and the `pass` is refused with the code its `string` twin always
// got. It still runs, 0, at `c3bdae2`: the refusal is the pin's
// (`meta/roadmap/0.0/0.0.4e.md` step 5). A generic that passes its argument on
// takes it as `move T:x` -- `../unit/loan_spellings.npk`. The same gate reached
// `vec_get` and `vec_pop` in `src/core/vec.npk`: that is why `vec_get` takes
// `T: Pod` and `vec_pop` spells its move (RX-168).
""")

HEADERS["tests/rejection/vec_owning_get_moves_out.npk"] = (
"c66b10a7b184699e0066a1aba51b45dea8f19b286c29ccc8570b2f497ea8e40c",
"""// expect-error: NITPICK-TYPE-017
// expect-error-at: 0:0
//
// `vec_get` AT AN OWNING `T` IS REFUSED: IT TAKES `T: Pod` SINCE CYCLE 0.0.4e
// (RX-168), AND AN OWNING TYPE CANNOT IMPLEMENT `Pod` AS IT IS DECLARED. The name
// is kept so RX-155's citations still find the file.
//
// WHAT IT PINS. Through `c3bdae2` `vec_get` returned its `T` by value from
// `pass v.items[i]`, an implicit MOVE, so at `T = string` the first read TOOK the
// element -- the slot zeroed and marked vacant -- and a second read returned an
// empty string from a slot `count` still counted: exit 0 at -O0 and through
// `opt -O2`, when this file was `tests/unit/vec_owning_get_moves_out.npk` and read
// twice (RX-155; `SAFETY.md` S-23a's table). At `c970483` that body is refused at
// EVERY `T`, NITPICK-TYPE-047 -- DEF-104's gate treats `T` as owning -- and
// `vec_get` reads through `pod_copy`, whose `pass self` is NITPICK-TYPE-047 for an
// owning type. So `vec_get` at `Vec<string>` is NITPICK-TYPE-017 here, "`string`
// does not implement `Pod`". One call, so one diagnostic.
//
// A TEST OF THE BOUND, NOT OF THIS FILE: against the tree before cycle 0.0.4e
// this file compiles and runs, exit 0, at `c3bdae2` (`meta/roadmap/0.0/0.0.4e.md`
// step 5) -- the refusal is the bound's, at either pin -- and `vec_get` at
// `int32`, `int64` and a POD struct runs throughout the unit suite.
""")

HEADERS["tests/probe/refused/probe17_lent_field_drop.npk"] = (
"293fce7b86e70dbaa0d0b53bf1abae53e7ee449c8ac459a640b15f8b657608aa",
"""// expect-error: NITPICK-TYPE-085
// expect-error-at: 0:0
//
// PROBE 17 -- OVERWRITING AN OWNING FIELD OF A LENT PARAMETER IS REFUSED:
// NITPICK-TYPE-085 at the write, since the compiler's 1.6.0 step 3g (DEF-102, the
// workbench registry's O-N21), carried by the pin `c970483` -- cycle 0.0.4e,
// RX-169. No library code, no `wild`, no pointer cast anywhere in the program.
//
// WHAT THE LANGUAGE SAYS. An ordinary parameter is LENT: "passing transfers
// nothing", the callee may read it and may not keep it (the compiler's D-065 and
// D-183). WHAT THE COMPILER DID THROUGH `c3bdae2`: the assignment `b.s = …` below
// dropped the field's old value first -- D-186's unconditional field drop, which
// reasons that "the struct's owner is exactly who is overwriting it" -- and for a
// lent parameter the old value is the CALLER's string, so `main` read the free
// poison, `0xAA`: exit 70 at -O0 and through `opt -O2`, when this was
// `tests/probe/probe17_lent_field_drop.npk` (found by cycle 0.0.4d's planning,
// raised as O-N21, RX-162). WHAT IT DOES AT `c970483`: a place rooted at a lent
// parameter whose type owns admits no write path, and the write is refused. It
// still compiles and runs, 70, at `c3bdae2` (`meta/roadmap/0.0/0.0.4e.md` step 5),
// so the verdict is the pin's. TYPE-085's message names what remains: read it,
// `.clone()` the part you change, or take it as `move Box:b` and let the caller
// write `move(b)`; `../../unit/loan_spellings.npk` runs the library's spellings.
//
// WHAT IT REACHED HERE: a lent `Bytes` grown by its callee, and a lent `Vec` or
// `SparseSet` freed or grown through `@` -- each refused the same way now
// (`../../rejection/bytes_alias_param_grow.npk`, `vec_alias_param_*.npk`,
// `sparseset_alias_param_free.npk`).
""")

HEADERS["tests/probe/probe15_block_string_close.npk"] = (
"a67ad8b8ab6175dbdce5b12f9302a48874fc98f30823d350c0e42e133ebb903c",
"""// expect-exit: 4
//
// PROBE 15 -- A BLOCK STRING CLOSES AT `\"\"\"`, AND A `""` INSIDE ITS BODY IS TWO
// BODY CHARACTERS: the compiler's lexer since its 1.6.0 step 3e (DEF-98), carried
// by the pin `c970483` -- cycle 0.0.4e, RX-170.
//
// WHAT THE SPECIFICATION SAYS. `LEXICAL_REFERENCE.md` §6.3:
//     BlockStringLiteral ::= '\"\"\"' (SourceCharacter - '\"\"\"')* '\"\"\"'
// so `\"\"\"a""b\"\"\"` is one literal whose body is `a""b` -- four bytes, and `main`
// exits with its length: 4 at -O0 and through `opt -O2`, measured at `c970483`.
//
// WHAT THE COMPILER DID THROUGH `c3bdae2`: `lexer_next` ended a block string at
// the first `""` and consumed three characters there, so `\"\"\"a""` was one
// literal, the `""b` its "closing quotes", and the last `\"\"\"` opened a second
// that never closed -- NITPICK-LEX-005, with the parser's cascade, PARSE-001 and
// PARSE-003. Found 2026-09-25 by cycle 0.0.5's fourth audit triage while writing
// `harness/lexical.py` (RX-157), raised, and fixed as DEF-98; this file sat in
// `refused/` with those three codes until cycle 0.0.4e moved it here. It still
// refuses at `c3bdae2` (`meta/roadmap/0.0/0.0.4e.md` step 5), so the verdict is
// the pin's.
//
// WHAT KEEPS THE READER IN STEP: `harness/lexical.py` mirrors the lexer, not the
// grammar, and moved with it (RX-170). Self-check case 18 holds a block string
// with `""` in its body and a `use` after its close, and fails against the old
// close; this probe is what says the lexer moved.
""")

EDITS = {}

# the two refused frees name their `T`, so TYPE-085 is the only diagnostic
EDITS["tests/rejection/vec_alias_param_free.npk"] = [
("""func:consume = NIL(Vec<int64>:v) never fails {
    drop vec_free(@v);
""",
"""func:consume = NIL(Vec<int64>:v) never fails {
    drop vec_free::<int64>(@v);
"""),
]
EDITS["tests/rejection/vec_alias_for_binding_free.npk"] = [
("""    for (Vec<int64>:x in arr) {
        drop vec_free(@x);
""",
"""    for (Vec<int64>:x in arr) {
        drop vec_free::<int64>(@x);
"""),
]
# one read, so one diagnostic
EDITS["tests/rejection/vec_owning_get_moves_out.npk"] = [
("""    string:first = raw vec_get(v, 0i64);
    if (string_byte_length(first) != 11i64)             { exit 21i32; }
    string:second = raw vec_get(v, 0i64);
    if (string_byte_length(second) != 0i64)             { exit 22i32; }
    if (v.count != 1i64)                                { exit 23i32; }
""",
"""    string:first = raw vec_get(v, 0i64);
    if (string_byte_length(first) != 11i64)             { exit 21i32; }
    if (v.count != 1i64)                                { exit 23i32; }
"""),
]

# N-22's two fixture sites: TYPE-083 is in our pin now. LINE COUNT KEPT -- each
# fixture's measured position sits below this line.
_T083_OLD = """    // NITPICK-TYPE-083 (DEF-96, at `d156c4f`, not our pin) -- B-7 would fail it.
"""
_T083_NEW = """    // NITPICK-TYPE-083 (DEF-96, in our pin since `c970483`) -- B-7 would fail it.
"""
EDITS["tests/rejection/failsafe_missing_system_arm.npk"] = [(_T083_OLD, _T083_NEW)]
EDITS["tests/rejection/failsafe_not_exhaustive.npk"] = [(_T083_OLD, _T083_NEW)]
EDITS["tests/conformance/import.npk"] = [
("""    // compiler's 1.6.0 step 3c refuses it `NITPICK-TYPE-083` (its DEF-96), landed
    // on the compiler's `main` at `d156c4f` -- no pin of ours carries it yet.
""",
"""    // compiler's 1.6.0 step 3c refuses it `NITPICK-TYPE-083` (its DEF-96), landed
    // at `d156c4f` and in our pin since `c970483` (cycle 0.0.4e).
"""),
]
# vec_unit's comment said `vec_get` MOVES an owning element out -- a program
# unit, so no measured position depends on its line count
EDITS["tests/unit/vec_unit.npk"] = [
('''    // cycle-0.0 audit (BL-5) that such a copy "is TYPE-046" -- refused -- and
    // declined to read for that reason; nothing refuses it (RX-155).
''',
'''    // cycle-0.0 audit (BL-5) that such a copy "is TYPE-046" -- refused -- and
    // declined to read for that reason; nothing refuses it (RX-155).
    // (Since cycle 0.0.4e, compiler `c970483`, something does: `vec_get` takes
    // `T: Pod`, so the read this comment declines is NITPICK-TYPE-017 here --
    // `../rejection/vec_owning_get_moves_out.npk`, RX-168.)
'''),
]
# two fixtures' headers named a loan unit's old place, `../unit/`. LINE COUNT KEPT.
EDITS["tests/rejection/bytes_copy.npk"] = [
('''// is not a copy, and a `Bytes` lent to a callee that grows it still dies
// (`../unit/bytes_alias_param_grow.npk`, RX-162).
''',
'''// is not a copy; a `Bytes` lent to a callee that grows it died through `c3bdae2`
// and is refused since `c970483` (`bytes_alias_param_grow.npk` here, RX-169).
'''),
]
EDITS["tests/rejection/sparseset_alias_read_after_free.npk"] = [
('''// NOT CLOSED BY THIS: the same wrong answer through a BY-VALUE parameter, which
// is a loan and not a copy (`../unit/sparseset_alias_param_free.npk`, RX-162).
''',
'''// NOT CLOSED BY THIS, BUT SINCE `c970483`: the same answer through a BY-VALUE
// parameter, a loan, is NITPICK-TYPE-085 (`sparseset_alias_param_free.npk`, RX-169).
'''),
]
KEEP_LINES = ("tests/rejection/failsafe_missing_system_arm.npk",
              "tests/rejection/failsafe_not_exhaustive.npk",
              "tests/conformance/import.npk",
              "tests/rejection/bytes_copy.npk",
              "tests/rejection/sparseset_alias_read_after_free.npk")

# probe 06b and probe 07: O-N9 is discharged, and their headers said it was live.
_ON9_NOTE = """//
// *(Dated @@DATE@@, cycle 0.0.4e, compilers `c3bdae2` and `c970483` -- the fifth
// cycle-0.0 audit's triage left these headers for the re-pin. O-N9 IS DISCHARGED:
// the compiler's DEF-3 landed at its 1.5.1b (in every pin from `94874ce`).
// Re-measured at both pins: a view of a LOCAL returned is NITPICK-BORROW-001, a
// view of a TEMPORARY is NITPICK-BORROW-012 -- the code this header calls "not in
// the pinned toolchain" -- and a subrange of a PARAMETER returned, the shape
// below, compiles and runs, as the header says DEF-3's rule would keep it. Every
// present-tense sentence below about O-N9, DEF-3 being "scheduled" or
// "unlanded", and a code "not in the pinned toolchain" was true at `950bb1d` and
// `3d15ac9` and is history; the measured behaviour it records has not moved.)*
"""
EDITS["tests/probe/probe06b_subview_returned.npk"] = [
("""// PROBE 06b — RETURNING A `uint8[]` SUBRANGE IS ACCEPTED. THE HYPOTHESIS WAS
// THAT IT WOULD BE REFUSED, AND IT WAS REFUTED.
""",
"""// PROBE 06b — RETURNING A `uint8[]` SUBRANGE IS ACCEPTED. THE HYPOTHESIS WAS
// THAT IT WOULD BE REFUSED, AND IT WAS REFUTED.
""" + _ON9_NOTE),
]
EDITS["tests/probe/probe07_string_bytes_edges.npk"] = [
("""// PROBE 07 — `string_bytes` at the borrow edges.
""",
"""// PROBE 07 — `string_bytes` at the borrow edges.
""" + _ON9_NOTE),
]

NEW = {}

NEW["tests/unit/loan_spellings.npk"] = """// expect-exit: 0
//
// THE SPELLINGS A LOAN'S REFUSAL PRESCRIBES, EACH ONE RUN -- the positive twin of
// the six loan and pass-out fixtures `../rejection/` holds since cycle 0.0.4e
// (RX-169), at compiler `c970483`.
//
// Each refusal passes if the compiler refuses the loan -- and would ALSO pass
// under a compiler that refused every container parameter. This file is the
// other half: what NITPICK-TYPE-085's message and NITPICK-TYPE-047's name as the
// way to do what the refused files did, each checked on a value distinct from the
// vacant 0 and the `0xAA` poison, and every block freed exactly once, so `exit 0`
// also says none leaked (`WildLeak`, 96) and none was freed twice (95):
//   1. a callee that FREES takes `move Vec<int64>:v`, and the caller writes
//      `move(a)` (21);
//   2. a callee that GROWS takes `Vec<int64>->`, and the caller passes `@w` --
//      the caller's own header then sees the growth (22, 23, 24);
//   3. the same two for a `SparseSet` (25) and a `Bytes` (26, 27);
//   4. a `for` binding READS; the array frees its own elements by index (28);
//   5. a generic that passes its argument on takes `move T:x` (29).
// Measured 0 at -O0 and through `opt -O2` at `c970483` and at `c3bdae2`: these
// were always legal, and now they are the spellings that compile.
mod:loan_spellings;

use "../../src/core/vec.npk".*;
use "../../src/core/sparseset.npk".*;
use "../../src/core/bytes.npk".*;

func:consume = int64(move Vec<int64>:v) never fails {
    int64:x = raw vec_get(v, 0i64);
    drop vec_free(@v);
    pass x;
};

func:grow = NIL(Vec<int64>->:v) never fails {
    int64:k = 0i64;
    while (k < 64i64) decreases 64i64 - k {
        drop vec_push(v, 9i64);
        k = k + 1i64;
    }
    pass NIL;
};

func:sconsume = bool(move SparseSet:s) never fails {
    bool:h = raw sset_contains(@s, 3i64);
    drop sset_free(@s);
    pass h;
};

func:bgrow = NIL(Bytes->:b) never fails {
    int64:k = 0i64;
    while (k < 64i64) decreases 64i64 - k {
        drop bytes_push(b, 66u8);
        k = k + 1i64;
    }
    pass NIL;
};

func:id_owned<T> = T(move T:x) never fails {
    pass x;
};

func:run = int32() never fails {
    Vec<int64>:a = raw vec_init::<int64>(1i64);
    drop vec_push(@a, 7i64);
    if ((raw consume(move(a))) != 7i64) { pass 21i32; }

    Vec<int64>:w = raw vec_init::<int64>(1i64);
    drop vec_push(@w, 7i64);
    drop grow(@w);
    if (w.count != 65i64) { pass 22i32; }
    if ((raw vec_get(w, 0i64)) != 7i64) { pass 23i32; }
    if ((raw vec_get(w, 64i64)) != 9i64) { pass 24i32; }
    drop vec_free(@w);

    SparseSet:s = raw sset_init(8i64);
    drop sset_insert(@s, 3i64);
    if (!(raw sconsume(move(s)))) { pass 25i32; }

    Bytes:b = raw bytes_init(1i64);
    drop bytes_push(@b, 65u8);
    drop bgrow(@b);
    if ((raw bytes_len(@b)) != 65i64) { pass 26i32; }
    if ((raw bytes_get(@b, 0i64)) != 65u8) { pass 27i32; }

    Vec<int64>:p = raw vec_init::<int64>(1i64);
    drop vec_push(@p, 7i64);
    Vec<int64>:q = raw vec_init::<int64>(1i64);
    drop vec_push(@q, 8i64);
    Vec<int64>[2]:arr = [move(p), move(q)];
    int64:total = 0i64;
    for (Vec<int64>:x in arr) {
        total = total + (raw vec_get(x, 0i64));
    }
    if (total != 15i64) { pass 28i32; }
    drop vec_free(@arr[0i64]);
    drop vec_free(@arr[1i64]);

    Vec<int64>:g = raw vec_init::<int64>(1i64);
    drop vec_push(@g, 7i64);
    Vec<int64>:h = raw id_owned::<Vec<int64>>(move(g));
    if ((raw vec_get(h, 0i64)) != 7i64) { pass 29i32; }
    drop vec_free(@h);
    pass 0i32;
};

func:main = int32(cstring[]:_~argv) {
    int32:r = raw run();
    exit r;
};

func:failsafe = int32(Error:e) {
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
        (*)                 { exit 99i32; }
    }
    exit 9i32;
};
"""

NEW["tests/probe/probe18_impl_adds_move.npk"] = """// expect-exit: 95
//
// PROBE 18 -- AN IMPL MAY DECLARE `move` ON A PARAMETER ITS TRAIT LENDS, AND A
// CALL THROUGH THE TRAIT THEN GIVES THE CALLEE A VALUE THE CALLER STILL OWNS. A
// compiler defect, found at compiler `c970483` by cycle 0.0.4e's planning --
// @@DEFECT@@ (RX-168). No library code, no `wild`, no pointer cast.
//
// WHAT THE LANGUAGE SAYS. `TRAITS_REFERENCE.md` §2: "An impl's method must have
// the signature the trait declares", and a `move` parameter takes ownership
// where a plain one is lent (the compiler's D-065, D-183). A call checked against
// `Dup` below lends `x`; a plain function with a `move` parameter, called
// without `move(...)`, is NITPICK-TYPE-046 (measured).
//
// WHAT THE COMPILER DOES. It compares the impl with the trait without the
// `move`, so `impl:string:Dup` compiles with `move string:self`, and `twice` --
// checked once, against the trait -- lends `a` to a callee that takes it and
// passes it back. `a` and `b` are then two owners of one body, both dropped at
// `run`'s end: a double free, 95 (`Unreachable`), at -O0 and through `opt -O2`,
// measured at `c970483` and at `c3bdae2` -- not a regression. The same impl
// written as the trait declares it, `string(string:self)`, is NITPICK-TYPE-047.
// A prelude trait is no different: `impl:Named:Eq` with `move Named:self`, over a
// struct holding a `string`, double-frees at `a.eq(b)`, 95.
//
// WHAT IT REACHES HERE: `vec_get` takes `T: Pod` (RX-168), and `Pod` is refused
// to an owning type only through its declared, lent `self`. A consumer's
// `impl:string:Pod` written with `move string:self` compiles, and `vec_get` at
// `Vec<string>` then hands back a second owner of the element -- 95, measured at
// planning (`meta/roadmap/0.0/0.0.4e.md` §1.4). No impl in this repository does
// it, and `check_vec_elements_own_nothing` still refuses an owning element in
// `src/`.
//
// WHEN THIS REDDENS: a refusal at the impl is the fix -- move this file to
// `refused/` with that code, and state `Pod` without its hole (`SAFETY.md` S-23a,
// `src/core/vec.npk`). Exit 46, the string's length, would mean the call site
// moved `a` instead: read the compiler's ruling before editing anything.
mod:probe18_impl_adds_move;

trait:Dup = {
    func:dup = Self(Self:self) never fails;
};

impl:string:Dup = { func:dup = string(move string:self) never fails { pass self; }; };

func:twice<T: Dup> = T(T:x) never fails {
    pass raw x.dup();
};

func:run = int32() never fails {
    string:a = string_concat("abbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "c");
    string:b = raw twice::<string>(a);
    pass (string_byte_length(b) =>! int32);
};

func:main = int32(cstring[]:_~argv) {
    int32:r = raw run();
    exit r;
};

func:failsafe = int32(Error:e) {
    pick (e) {
        (HeapBadRequest) { exit 91i32; },
        (HeapOom)        { exit 92i32; },
        (Unreachable)    { exit 95i32; },
        (WildLeak)       { exit 96i32; },
        (StackExhausted) { exit 106i32; },
        (MachineFault)   { exit 107i32; },
        (*)              { exit 99i32; }
    }
    exit 9i32;
};
"""

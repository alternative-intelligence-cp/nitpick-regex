r"""0.1.0 step 4 -- the AST (the plan's PD-18, recorded as RX-174).

`src/syntax/ast.npk` -- `AstKind`'s sixteen kinds, `AstNode` (56 bytes, owning
nothing, every operand `int64`), the flag bits, and the arena `Ast` with its hidden
`Vec` -- the layer entry's AST section, `SYNTAX.md` rules Y-26 and Y-27, four units and
one refusal. Applied by `python3 -B f10_edit.py ast "$REPO"` after step 3.
"""
import importlib.util
import os

_spec = importlib.util.spec_from_file_location(
    "f10_error", os.path.join(os.path.dirname(os.path.abspath(__file__)), "f10_error.py"))
_error = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_error)
_FAILSAFE = _error._FAILSAFE

KINDS = ("Empty Literal Dot Concat Alternate Repeat Group Flags Anchor WordBoundary "
         "Class ClassRange PerlClass PosixClass UnicodeClass ClassOp").split()
assert len(KINDS) == 16
_ENUM = "".join(f"    {k};\n" for k in KINDS).rstrip("\n")
_ARMS = ",\n".join(f"        (AstKind.{k}) {{ n = {i}i64; }}" for i, k in enumerate(KINDS))

NEW = {}

NEW["src/syntax/ast.npk"] = r"""// `src/syntax/ast.npk` — THE AST: A FLAT ARENA OF NODES THAT OWN NOTHING.
// Cycle 0.1.0, RX-174; `meta/specs/SYNTAX.md` rules Y-26 and Y-27.
//
// THE SHAPE IS `HIR.md` H-2's, FOR H-2's REASON. The tree is a `Vec<AstNode>`,
// and a node names another by INDEX, never by pointer: a `Vec` reallocates as
// it grows and every pointer into it would dangle, while an index survives
// (H-3). A node owns nothing -- no `string`, no `Vec`, no pointer -- which is
// what lets a `Vec` hold it (`SAFETY.md` S-23a, RX-155; the harness's
// `check_vec_elements_own_nothing` clears it by reading this file) and what lets
// `vec_get` hand it back by value (`AstNode: Pod`, below). A group's name and a
// property's text are not copied: the node holds their offset and length in the
// pattern, which the caller keeps for the whole life of the AST.
//
// EVERY OPERAND IS `int64`, SO THE PARSER NARROWS NOTHING (RX-174). The values
// it stores come from `int64`s -- the cursor's offset, a `Vec`'s count, a parsed
// bound -- and the language has no checked narrowing: `=>!` truncates in
// silence. An `int32` field would need a hand-written range check at every write,
// against a bound `RegexOptions` may raise (`SAFETY.md` S-12, `API.md` A-7). The
// AST is compile-time scratch, so its size is a cost paid once per pattern.
//
// FIFTY-SIX BYTES, MEASURED, AND THE SAME UNDER ANY ALIGNMENT RULE. `kind` and
// `flags` are four bytes each and come first, together, so every field sits at
// its natural alignment with nothing between -- `tests/unit/ast_size.npk` exits
// with `#size_of<AstNode>()`. With `kind` first and `flags` last, the same fields
// are 64 bytes, eight of them padding (measured at `c970483`).
//
// THE ARENA IS THE COMPILER'S TO GUARD. `Ast.nodes` is `hidden` (the compiler's
// D-314): outside this file it cannot even be read (NITPICK-TYPE-080,
// `tests/rejection/ast_nodes_read.npk`), so every access goes through `ast_get`,
// `ast_set` and `ast_push` -- `vec_get`, `vec_set` and `vec_push` underneath, the
// only bounds check this library has (S-23). `root` is `sealed`: read anywhere,
// set only by `ast_set_root`.
//
// LAYERING (`BUILD.md` §6, B-16). Imports `core`, whose eleven arms a program
// importing this file owes.
mod:ast;

use "../core/core.npk".*;

// The index that names no node: an absent sibling, an unbounded repetition's
// maximum, and the root of an `Ast` that nothing has been parsed into.
pub fixed int64:AST_NONE = -1i64;

// The flag bits (Y-26). The first five are the pattern flags in force at the
// node (`SYNTAX.md` §4, scoped by Y-12); the last three each belong to a kind.
pub fixed uint32:AST_FLAG_I = 1u32;          // `i`: case-insensitive
pub fixed uint32:AST_FLAG_M = 2u32;          // `m`: multi-line
pub fixed uint32:AST_FLAG_S = 4u32;          // `s`: `.` matches a newline
pub fixed uint32:AST_FLAG_X = 8u32;          // `x`: extended
pub fixed uint32:AST_FLAG_U = 16u32;         // `u`: Unicode mode, on by default
pub fixed uint32:AST_FLAG_LAZY = 256u32;     // a `Repeat` with a trailing `?`
pub fixed uint32:AST_FLAG_NEGATED = 512u32;  // a `Class`, `PerlClass`, `PosixClass` or `UnicodeClass`, negated
pub fixed uint32:AST_FLAG_BYTE = 1024u32;    // a `Literal` that is a byte, under `(?-u)` (Y-13)

// `SYNTAX.md` Y-27's closed list, in its order; what each kind's operands hold is
// that rule's table. `tests/unit/ast_unit.npk` holds this list to the order with
// an exhaustive `pick`.
pub enum:AstKind = {
""" + _ENUM + r"""
};

pub struct:AstNode = {
    AstKind:kind;      // Y-27
    uint32:flags;      // the AST_FLAG_ bits
    int64:a;           // Y-27's operands, by kind
    int64:b;
    int64:c;
    int64:next;        // the next sibling in its parent's list, or AST_NONE
    int64:pos;         // the construct's first byte in the pattern
    int64:len;         // its length in bytes
};

// `vec_get` hands back a `T: Pod` by value (RX-168), and a node owns nothing, so
// its copy is itself. `self` is LENT, exactly as the trait declares it: an impl
// declaring `move` on it compiles at `c970483` and is a double free through the
// trait -- the workbench registry's O-N28, the compiler's DEF-116, refused
// NITPICK-TYPE-014 from the compiler's landing 69
// (`tests/probe/probe18_impl_adds_move.npk`).
impl:AstNode:Pod = { func:pod_copy = AstNode(AstNode:self) never fails { pass self; }; };

// MOVE-ONLY, because it holds a `Vec` (`SAFETY.md` S-23b, RX-161): transfer it
// with `move(...)`, lend it by value to a reader, hand it by pointer to anything
// that changes it.
pub struct:Ast = {
    hidden Vec<AstNode>:nodes;     // the arena
    sealed int64:root;             // the root node, AST_NONE until a parse sets it
};

// obligation: never fails ensures result.root == AST_NONE && ast_len(result) == 0i64
pub func:ast_init = Ast(int64:cap) never fails {
    pass Ast{ nodes: raw vec_init::<AstNode>(cap), root: AST_NONE };
};

// obligation: never fails ensures result == t.nodes.count
pub func:ast_len = int64(Ast:t) never fails {
    pass t.nodes.count;
};

// obligation: never fails ensures ast_len(t) == old(ast_len(t)) + 1i64 && result == ast_len(t) - 1i64
//
// Appends a node and answers its index.
pub func:ast_push = int64(Ast->:t, AstNode:n) never fails {
    drop vec_push(@t.nodes, n);
    pass t.nodes.count - 1i64;
};

// obligation: never fails requires i >= 0i64 && i < ast_len(t)
pub func:ast_get = AstNode(Ast:t, int64:i) never fails {
    pass raw vec_get(t.nodes, i);
};

// obligation: never fails requires i >= 0i64 && i < ast_len(t)
pub func:ast_set = NIL(Ast->:t, int64:i, AstNode:n) never fails {
    drop vec_set(@t.nodes, i, n);
    pass NIL;
};

// obligation: never fails requires i >= 0i64 && i < ast_len(t)
pub func:ast_set_root = NIL(Ast->:t, int64:i) never fails {
    if (i < 0i64)           { drop vec_oob(i); }
    if (i >= t.nodes.count) { drop vec_oob(i); }
    t.root = i;
    pass NIL;
};

// obligation: never fails ensures t.root == AST_NONE
//
// Frees the arena. A node owns nothing, so the block is the whole obligation,
// and a unit that frees and exits 0 proves it (D-151: a leaked `wild` block
// traps at exit).
pub func:ast_free = NIL(Ast->:t) never fails {
    drop vec_free(@t.nodes);
    t.root = AST_NONE;
    pass NIL;
};
"""

NEW["tests/unit/ast_unit.npk"] = r"""// expect-exit: 0
//
// THE AST ARENA: A HUNDRED NODES IN, EVERY FIELD OUT, THROUGH THE LAYER ENTRY --
// AND FREED, SO A LEAKED `wild` BLOCK TRAPS. Cycle 0.1.0, RX-174; `SYNTAX.md`
// Y-26, Y-27.
//
// WHAT IT PINS. `ordinal` is an EXHAUSTIVE `pick` over `AstKind`, no `(*)`, one
// arm per kind in Y-27's order: a kind dropped, added or moved is a red run. A
// hundred nodes go in from capacity 1, so the arena grows under them, each kind
// in turn and every field distinct from its neighbours' (12: `ast_push` answers
// the new index); each comes back through `ast_get` field for field (20 to 27).
// `ast_set` rewrites one node and leaves its neighbour alone (30, 31);
// `ast_set_root` sets the sealed root (32); `ast_free` resets it (33). The flag
// bits are Y-26's values (40 to 47). The program exits 0 only after `ast_free`,
// and D-151 traps a `wild` block still live at exit -- so an `ast_free` that
// freed nothing, or a missing one, is red (96).
mod:ast_unit;

use "../../src/syntax/syntax.npk".*;

func:ordinal = int64(AstKind:k) never fails {
    int64:n = -1i64;
    pick (k) {
""" + _ARMS + r"""
    }
    pass n;
};

func:run = int32() never fails {
    Ast:t = raw ast_init(1i64);
    if ((raw ast_len(t)) != 0i64)   { pass 10i32; }
    if (t.root != AST_NONE)         { pass 11i32; }
    int64:i = 0i64;
    int64:kk = 0i64;
    while (i < 100i64) decreases 100i64 - i {
        AstNode:n = AstNode{ kind: (kk =>! int32) =>! AstKind, flags: (i =>! uint32) + 7u32,
                             a: i * 7i64, b: i * 11i64, c: 0i64 - i, next: i - 1i64,
                             pos: i + 1000i64, len: i + 2i64 };
        int64:at = raw ast_push(@t, n);
        if (at != i) { pass 12i32; }
        i = i + 1i64;
        kk = kk + 1i64;
        if (kk == 16i64) { kk = 0i64; }
    }
    if ((raw ast_len(t)) != 100i64) { pass 13i32; }
    i = 0i64;
    kk = 0i64;
    while (i < 100i64) decreases 100i64 - i {
        AstNode:g = raw ast_get(t, i);
        if ((raw ordinal(g.kind)) != kk)         { pass 20i32; }
        if (g.flags != (i =>! uint32) + 7u32)    { pass 21i32; }
        if (g.a != i * 7i64)                     { pass 22i32; }
        if (g.b != i * 11i64)                    { pass 23i32; }
        if (g.c != 0i64 - i)                     { pass 24i32; }
        if (g.next != i - 1i64)                  { pass 25i32; }
        if (g.pos != i + 1000i64)                { pass 26i32; }
        if (g.len != i + 2i64)                   { pass 27i32; }
        i = i + 1i64;
        kk = kk + 1i64;
        if (kk == 16i64) { kk = 0i64; }
    }
    AstNode:m = raw ast_get(t, 50i64);
    m.next = 99i64;
    drop ast_set(@t, 50i64, m);
    AstNode:m2 = raw ast_get(t, 50i64);
    if (m2.next != 99i64)                        { pass 30i32; }
    AstNode:m3 = raw ast_get(t, 51i64);
    if (m3.next != 50i64)                        { pass 31i32; }
    drop ast_set_root(@t, 99i64);
    if (t.root != 99i64)                         { pass 32i32; }
    drop ast_free(@t);
    if (t.root != AST_NONE)                      { pass 33i32; }
    pass 0i32;
};

func:flags = int32() never fails {
    if (AST_FLAG_I != 1u32)          { pass 40i32; }
    if (AST_FLAG_M != 2u32)          { pass 41i32; }
    if (AST_FLAG_S != 4u32)          { pass 42i32; }
    if (AST_FLAG_X != 8u32)          { pass 43i32; }
    if (AST_FLAG_U != 16u32)         { pass 44i32; }
    if (AST_FLAG_LAZY != 256u32)     { pass 45i32; }
    if (AST_FLAG_NEGATED != 512u32)  { pass 46i32; }
    if (AST_FLAG_BYTE != 1024u32)    { pass 47i32; }
    pass 0i32;
};

func:main = int32(cstring[]:_~argv) {
    int32:r = raw run();
    if (r != 0i32) { exit r; }
    int32:f = raw flags();
    exit f;
};

""" + _FAILSAFE

NEW["tests/unit/ast_size.npk"] = r"""// expect-exit: 56
//
// `#size_of<AstNode>()` IS 56, AND THIS PROGRAM'S EXIT CODE IS THE MEASUREMENT.
// Cycle 0.1.0, RX-174; `SYNTAX.md` Y-26.
//
// Measured, never derived from field widths (RX-135): the exit code is the size,
// so the number cannot be transcribed wrongly. Two four-byte fields and six
// eight-byte ones, the two first and together, so nothing pads -- 56 under any
// alignment an `int64` could be given. With `flags` moved last the same fields
// are 64 (measured at `c970483`, `ast.npk`'s header). A type's size, not an
// emission's: nothing here reads the IR.
mod:ast_size;

use "../../src/syntax/syntax.npk".*;

func:main = int32(cstring[]:_~argv) {
    exit (#size_of<AstNode>() =>! int32);
};

""" + _FAILSAFE

NEW["tests/unit/ast_oob_get.npk"] = r"""// expect-exit: 94
//
// `ast_get` PAST THE LAST NODE STOPS. Cycle 0.1.0, RX-174.
//
// `ast_get` is `vec_get` underneath -- the accessor pair is the only bounds check
// this library has, because `Vec<T>.items` is a bare `wild T->` and D-070 guards
// no bare pointer (`SAFETY.md` S-23). This reads index 1 of a one-node arena and
// must trap (94, `OutOfBounds`) rather than return a heap word: a wrapper that
// clamped, or read `.items` itself, would pass the in-range unit and fail here.
mod:ast_oob_get;

use "../../src/syntax/syntax.npk".*;

func:main = int32(cstring[]:_~argv) {
    Ast:t = raw ast_init(4i64);
    discard(raw ast_push(@t, AstNode{ kind: AstKind.Empty, flags: 0u32, a: 0i64, b: 0i64, c: 0i64,
                                      next: AST_NONE, pos: 0i64, len: 0i64 }));
    AstNode:g = raw ast_get(t, 1i64);
    drop ast_free(@t);
    if (g.pos != 0i64) { exit 10i32; }
    exit 0i32;
};

""" + _FAILSAFE

NEW["tests/unit/ast_oob_set_root.npk"] = r"""// expect-exit: 94
//
// `ast_set_root` AT AN INDEX NO NODE HAS STOPS. Cycle 0.1.0, RX-174.
//
// The root is `sealed` and set only here, so the check here is the whole of the
// guarantee that `root` names a node or `AST_NONE`. This sets root 1 in a
// one-node arena and must trap (94, `OutOfBounds`).
mod:ast_oob_set_root;

use "../../src/syntax/syntax.npk".*;

func:main = int32(cstring[]:_~argv) {
    Ast:t = raw ast_init(4i64);
    discard(raw ast_push(@t, AstNode{ kind: AstKind.Empty, flags: 0u32, a: 0i64, b: 0i64, c: 0i64,
                                      next: AST_NONE, pos: 0i64, len: 0i64 }));
    drop ast_set_root(@t, 1i64);
    drop ast_free(@t);
    exit 0i32;
};

""" + _FAILSAFE

NEW["tests/rejection/ast_nodes_read.npk"] = r"""// expect-error: NITPICK-TYPE-080
// expect-error-at: 28:16
//
// A CONSUMER CANNOT REACH THE AST'S `Vec`. Cycle 0.1.0, RX-174.
//
// WHAT IT PINS. `Ast.nodes` is `hidden` (the compiler's D-314): outside
// `src/syntax/ast.npk` even a READ of it is NITPICK-TYPE-080. So every access to
// the arena goes through `ast_get`, `ast_set` and `ast_push`, and the accessor
// pair underneath them is the only bounds check (`SAFETY.md` S-23).
//
// IT READS `.count`, NOT AN ELEMENT, ON PURPOSE. A `vec_get(t.nodes, 0i64)` here
// is refused NITPICK-TYPE-080 at `t.nodes` and, at `c970483`, NITPICK-TYPE-022 at
// the call as well -- a cascade, `T` left with nothing to be inferred from --
// which the compiler's DEF-117 removes at the next re-pin (measured at
// `9f6f370`). This file's code set must not move when the compiler's recovery
// improves, so it names the field and nothing generic.
//
// A TEST OF THE HIDING, NOT OF THIS FILE: with `hidden` replaced by `sealed` it
// compiles (`meta/roadmap/0.1/0.1.0.md`, step 4's controls).
mod:ast_nodes_read;

use "../../src/syntax/syntax.npk".*;

func:main = int32(cstring[]:_~argv) {
    Ast:t = raw ast_init(4i64);
    discard(raw ast_push(@t, AstNode{ kind: AstKind.Empty, flags: 0u32, a: 0i64, b: 0i64, c: 0i64,
                                      next: AST_NONE, pos: 0i64, len: 0i64 }));
    int64:n = t.nodes.count;
    drop ast_free(@t);
    discard(n);
    exit 0i32;
};

""" + _FAILSAFE

EDITS = {}

EDITS["src/syntax/syntax.npk"] = [(
r"""pub use "./cursor.npk".cursor_eat;
""",
r"""pub use "./cursor.npk".cursor_eat;

// ---- the AST arena (RX-174) ---------------------------------------------------
pub use "./ast.npk".AST_NONE;
pub use "./ast.npk".AST_FLAG_I;
pub use "./ast.npk".AST_FLAG_M;
pub use "./ast.npk".AST_FLAG_S;
pub use "./ast.npk".AST_FLAG_X;
pub use "./ast.npk".AST_FLAG_U;
pub use "./ast.npk".AST_FLAG_LAZY;
pub use "./ast.npk".AST_FLAG_NEGATED;
pub use "./ast.npk".AST_FLAG_BYTE;
pub use "./ast.npk".AstKind;
pub use "./ast.npk".AstNode;
pub use "./ast.npk".Ast;
pub use "./ast.npk".ast_init;
pub use "./ast.npk".ast_len;
pub use "./ast.npk".ast_push;
pub use "./ast.npk".ast_get;
pub use "./ast.npk".ast_set;
pub use "./ast.npk".ast_set_root;
pub use "./ast.npk".ast_free;
"""),
]

EDITS["meta/specs/SYNTAX.md"] = [(
r"""has no such requirement (`SAFETY.md` S-20); the **pattern** does, because a
pattern is text a person wrote.
""",
r"""has no such requirement (`SAFETY.md` S-20); the **pattern** does, because a
pattern is text a person wrote.

**Rule Y-26 (RX-174) — the AST is a flat arena of nodes that own nothing, and
every operand is an `int64`.** `src/syntax/ast.npk`:

```nitpick
pub struct:AstNode = {
    AstKind:kind;      // Y-27
    uint32:flags;      // the AST_FLAG_ bits
    int64:a;           // Y-27's operands, by kind
    int64:b;
    int64:c;
    int64:next;        // the next sibling in its parent's list, or AST_NONE
    int64:pos;         // the construct's first byte in the pattern
    int64:len;         // its length in bytes
};
```

A node names another by its index in the same arena, or by `AST_NONE` (−1);
never by pointer, which a growing `Vec` would leave dangling (`HIR.md` H-3). It
owns nothing (`SAFETY.md` S-23a): a group's name and a property's text stay in
the pattern, held by offset and length, and the caller keeps the pattern for as
long as the AST lives. `flags` holds the pattern flags in force at the node —
`AST_FLAG_I` 1, `AST_FLAG_M` 2, `AST_FLAG_S` 4, `AST_FLAG_X` 8, `AST_FLAG_U` 16
(§4, scoped by Y-12) — and one bit for each of three kinds: `AST_FLAG_LAZY` 256
on a `Repeat`, `AST_FLAG_NEGATED` 512 on a `Class`, `PerlClass`, `PosixClass` or
`UnicodeClass`, and `AST_FLAG_BYTE` 1024 on a `Literal` that is a byte under
`(?-u)` (Y-13). `#size_of<AstNode>()` is 56, measured, with no padding.

**Rule Y-27 (RX-174) — the node kinds are a closed list of sixteen**, one for
each construct of §1 that survives parsing; a refusal (§8) produces none.

| Kind | Written | `a` | `b` | `c` | Bit |
|---|---|---|---|---|---|
| `Empty` | an empty pattern, alternative or group body | | | | |
| `Literal` | a character, or an escape naming one | its codepoint; a byte under `BYTE` | | | `BYTE` |
| `Dot` | `.` | | | | |
| `Concat` | two or more pieces in sequence | the first | how many | | |
| `Alternate` | two or more alternatives, `a\|b` | the first | how many | | |
| `Repeat` | `*` `+` `?` `{n}` `{n,}` `{n,m}` | the repeated node | the minimum | the maximum; `AST_NONE` if unbounded | `LAZY` |
| `Group` | `(…)` `(?:…)` `(?<name>…)` `(?flags:…)` | the body | its capture index; 0 if it captures nothing | its name's length, the name starting at `pos + 3`; 0 if unnamed | |
| `Flags` | `(?flags)` | the flags it sets | the flags it clears | | |
| `Anchor` | `^` `$` `\A` `\z` | 0, 1, 2, 3, in that order | | | |
| `WordBoundary` | `\b` `\B` | 0, 1 | | | |
| `Class` | `[…]`, a nested class, an operand of a class operator | the first item | how many | | `NEGATED` |
| `ClassRange` | `a-z`, or one character in a class | the low codepoint | the high codepoint, equal for one character | | |
| `PerlClass` | `\d` `\w` `\s`, in a class or out; a capital negates | 0, 1, 2 | | | `NEGATED` |
| `PosixClass` | `[:name:]` `[:^name:]` | the name's place in §5.1's list, from 0 | | | `NEGATED` |
| `UnicodeClass` | `\p{…}` `\pL` `\P{…}` `\PL` | the property text's offset | its length | | `NEGATED` |
| `ClassOp` | `&&` `--` `~~` | the left operand | the right operand | 0, 1, 2, in that order | |

A list's members — a `Concat`'s pieces, an `Alternate`'s alternatives, a
`Class`'s items — are its first member and each member's `next`, in the order
written. The subcycle that parses a construct produces its kind; the operands
are this table's until a decision says otherwise.
"""),
]

EDITS["meta/DECISIONS.md"] = [(
r"""**`int32` offsets** — every one would be narrowed from an `int64` length, and the language has no checked
narrowing.
""",
r"""**`int32` offsets** — every one would be narrowed from an `int64` length, and the language has no checked
narrowing.

### RX-174 — the AST is a flat arena of sixteen kinds of 56-byte node that own nothing, every operand an `int64`, and only `ast.npk` touches its `Vec`

**@@DATE@@, cycle 0.1.0 (the plan's PD-18), at compiler `c970483`.** `src/syntax/ast.npk`, and `SYNTAX.md`
rules Y-26 (the node) and Y-27 (the kinds):

- **`HIR.md` H-2's shape, for H-2's reason**: a `Vec<AstNode>`, and a node names another by index, because a
  `Vec` reallocates and a pointer into it would dangle. A node owns nothing — the S-23a check clears
  `Vec<AstNode>` (measured: six element types, ten declarations) — and `AstNode` implements `Pod` in one line,
  its `self` lent as the trait declares it, so `vec_get` hands a node back by value. A name or a property's
  text stays in the pattern, as an offset and a length.
- **Every operand is an `int64`.** The values come from `int64`s — the cursor's offset, a `Vec`'s count, a
  parsed bound — and `=>!` narrows in silence, so an `int32` field would need a hand-written range check at every
  write, against a bound `RegexOptions` may raise (`SAFETY.md` S-12, `API.md` A-7). The AST is compile-time
  scratch.
- **56 bytes, the same under any alignment rule**: `kind` and `flags` first, together, then six `int64`s —
  no padding (measured 56 at `c970483`, `c3bdae2` and the next re-pin's control; the order `kind`, operands,
  `flags` is 64). `tests/unit/ast_size.npk` exits with the size.
- **The sixteen kinds are declared now, with their operands** (Y-27's table): every construct of §1's grammar
  that survives parsing has a kind, and the node is shown to hold each before any is parsed. The flag bits are
  Y-26's: the five pattern flags, and `LAZY`, `NEGATED` and `BYTE`.
- **The arena is `Ast`: `hidden Vec<AstNode>:nodes`, `sealed int64:root`.** Outside `ast.npk` the `Vec`
  cannot even be read (`NITPICK-TYPE-080`, `tests/rejection/ast_nodes_read.npk`), so `ast_get`, `ast_set` and
  `ast_push` — `vec_get`, `vec_set` and `vec_push` underneath — are the only way in (S-23). `ast_set_root`
  checks its index; `ast_free` frees the block and resets the root.

*Alternatives declined:* **`int32` operands** — `0.1.0.md`'s first draft (its D1, "exactly like the HIR")
and the cycle README's checklist: every one would narrow an `int64` in silence, and the HIR is 0.2's to size;
**a payload enum per construct** — the spelling H-2 examined and declined, and the flat operands are what the
HIR mirrors; **declaring each kind when the subcycle that parses it lands** — the node would be proven
against the first constructs only, which is `0.1.0.md`'s own warning about a skeleton shaped by what fitted
first; **children in a side array** — a second arena and an index pair per parent, where H-2 links siblings;
**names copied into a `Bytes` in the `Ast`** (the first draft's D1) — the pattern is at hand for the AST's
whole life, and `Hir.names` is the HIR's copy; **`nodes` sealed rather than hidden** — a consumer could then
read the `Vec` and index it past `ast_get`; **`AstNode`'s fields sealed** — the parser, in another module,
builds nodes, and a node has no invariant a constructor would keep.
"""),
]

r"""0.1.0 step 5 -- the parser's entry and the skeleton (the plan's PD-19, recorded as RX-175).

`src/syntax/parse.npk` -- `parse_check_length`, the entry's first refusal -- and the
layer entry's last section and paragraph; `tests/unit/parse_check_length.npk` at the
bound; and `tests/unit/syntax_skeleton.npk`, the subcycle's acceptance, which composes
every piece through `syntax.npk`'s re-exports alone. Applied by
`python3 -B f10_edit.py entry "$REPO"` after step 4.
"""
import importlib.util
import os

_here = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("f10_error", os.path.join(_here, "f10_error.py"))
_error = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_error)
_FAILSAFE = _error._FAILSAFE
_spec = importlib.util.spec_from_file_location("f10_ast", os.path.join(_here, "f10_ast.py"))
_ast = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ast)
_ARMS = _ast._ARMS

NEW = {}

NEW["src/syntax/parse.npk"] = r"""// `src/syntax/parse.npk` — THE PARSER'S ENTRY. Cycle 0.1.0 writes its first
// refusal and nothing else; cycle 0.1.1 writes the parse (RX-175).
//
// HOW `syntax` SAYS A PATTERN IS WRONG: WITH A VALUE. The library's one `error:`
// identity, `ERegexPattern`, is `api`'s (`SAFETY.md` S-8), and `syntax` sits
// below `api` (`BUILD.md` B-16), so the parser answers a `PatternError` as a
// value -- `PatternError?`, `NIL` when nothing is wrong -- and `api` turns the
// first one into the identity. The parse (0.1.1) takes the pattern as a view and
// the tree by pointer, `parse_pattern(uint8[]:pat, Ast->:out)`, and answers
// `PatternError?`.
//
// THE LENGTH FIRST, BEFORE A CURSOR EXISTS (RX-175). `NREGEX_PATTERN_BYTES` is the
// cheapest refusal there is, and it bounds everything after it, the arena
// included, so it runs before anything reads a byte of the pattern.
//
// LAYERING (`BUILD.md` §6, B-16). Imports `core` for the bound and
// `pattern_error` for the value; a program importing it owes `core`'s eleven arms.
mod:parse;

use "../core/core.npk".*;
use "./pattern_error.npk".*;

// obligation: never fails ensures (result == NIL) == (pat.len <= NREGEX_PATTERN_BYTES)
//
// `NIL` if the pattern is at most `NREGEX_PATTERN_BYTES` long, else
// `PatternTooLong`: its offset the first byte past the bound, its length the bytes
// over it, its detail the bound. The bound is 65 536, which a `uint32` holds, so
// the narrowing truncates nothing (`SAFETY.md` S-12).
pub func:parse_check_length = PatternError?(uint8[]:pat) never fails {
    if (pat.len > NREGEX_PATTERN_BYTES) {
        pass raw pattern_error(PatternErrorKind.PatternTooLong, NREGEX_PATTERN_BYTES,
                               pat.len - NREGEX_PATTERN_BYTES, NREGEX_PATTERN_BYTES =>! uint32);
    }
    pass NIL;
};
"""

NEW["tests/unit/parse_check_length.npk"] = r"""// expect-exit: 0
//
// `parse_check_length` AT ITS BOUND: ON IT, ACCEPTED; ONE OVER, REFUSED. Cycle
// 0.1.0, RX-175 -- `SAFETY.md` §5's "a test sitting exactly on it and one
// exceeding it", for `NREGEX_PATTERN_BYTES`.
//
// Patterns of 0, 1, the bound less one and exactly the bound answer `NIL` (10 to
// 13). One byte over, and sixteen over, answer `PatternTooLong` -- its offset the
// first byte past the bound, its length the bytes over it, its detail the bound
// (20 to 24, 30 to 34). Every length is written from the constant, so the unit
// states the rule rather than today's number, 65 536.
//
// The bytes are `a`s pushed into a `Bytes` and copied out as a `string`, whose
// view each case slices; the `string` is not written while the view is live.
mod:parse_check_length;

use "../../src/core/core.npk".*;
use "../../src/syntax/syntax.npk".*;

func:fits = bool(uint8[]:pat) never fails {
    PatternError?:e = raw parse_check_length(pat);
    pass e == NIL;
};

func:check_over = int32(uint8[]:pat, int32:base) never fails {
    PatternError?:e = raw parse_check_length(pat);
    if (e == NIL) { pass base; }
    PatternError:got = e ?? raw pattern_error(PatternErrorKind.UnclosedGroup, 0i64, 0i64, 0u32);
    bool:right = false;
    pick (got.kind) {
        (PatternErrorKind.PatternTooLong) { right = true; },
        (*)                               { right = false; }
    }
    if (!right)                                               { pass base + 1i32; }
    if (got.offset != NREGEX_PATTERN_BYTES)                   { pass base + 2i32; }
    if (got.span_len != pat.len - NREGEX_PATTERN_BYTES)       { pass base + 3i32; }
    if (got.detail != (NREGEX_PATTERN_BYTES =>! uint32))      { pass base + 4i32; }
    pass 0i32;
};

func:run = int32(uint8[]:v) never fails {
    int64:bound = NREGEX_PATTERN_BYTES;
    if (!(raw fits(v[0i64...0i64])))                   { pass 10i32; }
    if (!(raw fits(v[0i64...1i64])))                   { pass 11i32; }
    if (!(raw fits(v[0i64...(bound - 1i64)])))         { pass 12i32; }
    if (!(raw fits(v[0i64...bound])))                  { pass 13i32; }
    int32:r = raw check_over(v[0i64...(bound + 1i64)], 20i32);
    if (r != 0i32) { pass r; }
    r = raw check_over(v[0i64...(bound + 16i64)], 30i32);
    pass r;
};

func:main = int32(cstring[]:_~argv) {
    int64:n = NREGEX_PATTERN_BYTES + 16i64;
    Bytes:b = raw bytes_init(n);
    int64:i = 0i64;
    while (i < n) decreases n - i {
        drop bytes_push(@b, 97u8);
        i = i + 1i64;
    }
    string:s = raw bytes_copy_string(@b);
    uint8[]:v = string_bytes(s);
    if (v.len != n) { exit 9i32; }
    int32:r = raw run(v);
    exit r;
};

""" + _FAILSAFE

NEW["tests/unit/syntax_skeleton.npk"] = r"""// expect-exit: 0
//
// THE PIECES COMPOSE: A SKELETON PARSE, BUILT HERE FROM `src/syntax/syntax.npk`'S
// RE-EXPORTS ALONE. Cycle 0.1.0, RX-175 -- the subcycle's acceptance: it accepts
// `a`, and it reports offset 0 for `(`.
//
// `skeleton` IS NOT THE PARSER AND PARSES NO CONSTRUCT; cycle 0.1.1 writes
// `parse_pattern`, fresh, in `src/syntax/parse.npk`. It is a test of the pieces
// every later subcycle is written in: the length refused first, before a cursor
// exists (`parse_check_length`); the cursor read a byte at a time; nodes pushed
// into the arena, linked through `next` and rooted; an error built by
// `pattern_error` at the cursor's offset. Its domain is bytes other than `(` and
// `)`, each taken as a literal, and `(`, which it reports unclosed -- no input here
// holds a `)`, so every `(` it meets IS unclosed.
//
// THE CASES. The empty pattern is one `Empty` root (10 to 13). "a" is one
// `Literal` root, 97 at offset 0 (20 to 24). "ab" is a `Concat` of two `Literal`s
// linked in order (30 to 37). "(" is `UnclosedGroup` at offset 0, length 1, with
// no root (40 to 44); "ab(" is the same at offset 2, after two nodes (50 to 52). A
// pattern of exactly `NREGEX_PATTERN_BYTES` bytes is accepted, a `Concat` of that
// many literals (60 to 62); one byte more is `PatternTooLong` and pushes NO node
// (70 to 73) -- the length is refused before anything reads the pattern.
//
// The scan is a `while` over the cursor's `int64` offset, `decreases` the bytes
// left: never a `for`, a `loop` or a `till` (the compiler's DEF-127 … DEF-130 at
// `c970483`). No pattern's owner is written while a cursor holds its view.
mod:syntax_skeleton;

use "../../src/core/core.npk".*;
use "../../src/syntax/syntax.npk".*;

func:ordinal = int64(AstKind:k) never fails {
    int64:n = -1i64;
    pick (k) {
""" + _ARMS + r"""
    }
    pass n;
};

func:skeleton = PatternError?(uint8[]:pat, Ast->:out) never fails {
    PatternError?:long = raw parse_check_length(pat);
    if (long != NIL) { pass long; }
    Cursor:c = raw cursor_init(pat);
    int64:first = AST_NONE;
    int64:last = AST_NONE;
    int64:count = 0i64;
    while (!(raw cursor_at_end(@c))) decreases pat.len - c.pos {
        int64:at = raw cursor_offset(@c);
        int32:b = raw cursor_bump(@c);
        if (b == 40i32) {
            pass raw pattern_error(PatternErrorKind.UnclosedGroup, at, 1i64, 0u32);
        }
        int64:i = raw ast_push(out, AstNode{ kind: AstKind.Literal, flags: AST_FLAG_U, a: b => int64,
                                             b: 0i64, c: 0i64, next: AST_NONE, pos: at, len: 1i64 });
        if (last == AST_NONE) { first = i; }
        else {
            AstNode:prev = raw ast_get(<-out, last);
            prev.next = i;
            drop ast_set(out, last, prev);
        }
        last = i;
        count = count + 1i64;
    }
    if (count == 0i64) {
        int64:e = raw ast_push(out, AstNode{ kind: AstKind.Empty, flags: AST_FLAG_U, a: 0i64, b: 0i64,
                                             c: 0i64, next: AST_NONE, pos: 0i64, len: 0i64 });
        drop ast_set_root(out, e);
        pass NIL;
    }
    if (count == 1i64) {
        drop ast_set_root(out, first);
        pass NIL;
    }
    int64:cat = raw ast_push(out, AstNode{ kind: AstKind.Concat, flags: AST_FLAG_U, a: first, b: count,
                                           c: 0i64, next: AST_NONE, pos: 0i64, len: pat.len });
    drop ast_set_root(out, cat);
    pass NIL;
};

func:unclosed_at = int32(PatternError?:e, int64:off, int32:base) never fails {
    if (e == NIL) { pass base; }
    PatternError:got = e ?? raw pattern_error(PatternErrorKind.PatternTooLong, 0i64, 0i64, 0u32);
    bool:right = false;
    pick (got.kind) {
        (PatternErrorKind.UnclosedGroup) { right = true; },
        (*)                              { right = false; }
    }
    if (!right)               { pass base + 1i32; }
    if (got.offset != off)    { pass base + 2i32; }
    if (got.span_len != 1i64) { pass base + 3i32; }
    pass 0i32;
};

func:case_empty = int32() never fails {
    string:s = "";
    Ast:t = raw ast_init(4i64);
    PatternError?:e = raw skeleton(string_bytes(s), @t);
    if (e != NIL)                               { pass 10i32; }
    if ((raw ast_len(t)) != 1i64)               { pass 11i32; }
    if (t.root != 0i64)                         { pass 12i32; }
    AstNode:r = raw ast_get(t, t.root);
    if ((raw ordinal(r.kind)) != 0i64)          { pass 13i32; }
    drop ast_free(@t);
    pass 0i32;
};

func:case_a = int32() never fails {
    string:s = "a";
    Ast:t = raw ast_init(4i64);
    PatternError?:e = raw skeleton(string_bytes(s), @t);
    if (e != NIL)                               { pass 20i32; }
    if ((raw ast_len(t)) != 1i64)               { pass 21i32; }
    AstNode:r = raw ast_get(t, t.root);
    if ((raw ordinal(r.kind)) != 1i64)          { pass 22i32; }
    if (r.a != 97i64)                           { pass 23i32; }
    if (r.pos != 0i64)                          { pass 24i32; }
    drop ast_free(@t);
    pass 0i32;
};

func:case_ab = int32() never fails {
    string:s = "ab";
    Ast:t = raw ast_init(4i64);
    PatternError?:e = raw skeleton(string_bytes(s), @t);
    if (e != NIL)                               { pass 30i32; }
    if ((raw ast_len(t)) != 3i64)               { pass 31i32; }
    AstNode:r = raw ast_get(t, t.root);
    if ((raw ordinal(r.kind)) != 3i64)          { pass 32i32; }
    if (r.b != 2i64)                            { pass 33i32; }
    AstNode:x = raw ast_get(t, r.a);
    if (x.a != 97i64)                           { pass 34i32; }
    AstNode:y = raw ast_get(t, x.next);
    if (y.a != 98i64)                           { pass 35i32; }
    if (y.pos != 1i64)                          { pass 36i32; }
    if (y.next != AST_NONE)                     { pass 37i32; }
    drop ast_free(@t);
    pass 0i32;
};

func:case_open = int32() never fails {
    string:s = "(";
    Ast:t = raw ast_init(4i64);
    PatternError?:e = raw skeleton(string_bytes(s), @t);
    int32:r = raw unclosed_at(e, 0i64, 40i32);
    if (r != 0i32)                              { pass r; }
    if (t.root != AST_NONE)                     { pass 44i32; }
    drop ast_free(@t);
    pass 0i32;
};

func:case_ab_open = int32() never fails {
    string:s = "ab(";
    Ast:t = raw ast_init(4i64);
    PatternError?:e = raw skeleton(string_bytes(s), @t);
    int32:r = raw unclosed_at(e, 2i64, 50i32);
    if (r != 0i32)                              { pass r; }
    if ((raw ast_len(t)) != 2i64)               { pass 52i32; }
    drop ast_free(@t);
    pass 0i32;
};

func:case_bound = int32(uint8[]:v) never fails {
    int64:bound = NREGEX_PATTERN_BYTES;
    Ast:t = raw ast_init(4i64);
    PatternError?:e = raw skeleton(v[0i64...bound], @t);
    if (e != NIL)                               { pass 60i32; }
    if ((raw ast_len(t)) != bound + 1i64)       { pass 61i32; }
    AstNode:r = raw ast_get(t, t.root);
    if (r.b != bound)                           { pass 62i32; }
    drop ast_free(@t);
    Ast:u = raw ast_init(4i64);
    PatternError?:f = raw skeleton(v[0i64...(bound + 1i64)], @u);
    if (f == NIL)                               { pass 70i32; }
    PatternError:got = f ?? raw pattern_error(PatternErrorKind.UnclosedGroup, 0i64, 0i64, 0u32);
    bool:right = false;
    pick (got.kind) {
        (PatternErrorKind.PatternTooLong) { right = true; },
        (*)                               { right = false; }
    }
    if (!right)                                 { pass 71i32; }
    if (got.offset != bound)                    { pass 72i32; }
    if ((raw ast_len(u)) != 0i64)               { pass 73i32; }
    drop ast_free(@u);
    pass 0i32;
};

func:main = int32(cstring[]:_~argv) {
    int32:r = raw case_empty();
    if (r != 0i32) { exit r; }
    r = raw case_a();
    if (r != 0i32) { exit r; }
    r = raw case_ab();
    if (r != 0i32) { exit r; }
    r = raw case_open();
    if (r != 0i32) { exit r; }
    r = raw case_ab_open();
    if (r != 0i32) { exit r; }
    int64:n = NREGEX_PATTERN_BYTES + 1i64;
    Bytes:b = raw bytes_init(n);
    int64:i = 0i64;
    while (i < n) decreases n - i {
        drop bytes_push(@b, 97u8);
        i = i + 1i64;
    }
    string:s = raw bytes_copy_string(@b);
    r = raw case_bound(string_bytes(s));
    exit r;
};

""" + _FAILSAFE

EDITS = {}

EDITS["src/syntax/syntax.npk"] = [(
r"""// refused at depth 251 and the program survives.
//
// EVERY LINE BELOW IS `pub use`, ONE NAME PER LINE (`BUILD.md` B-15a rules 1""",
r"""// refused at depth 251 and the program survives.
//
// SINCE CYCLE 0.1.0 THE LAYER HOLDS THE PIECES EVERY LATER SUBCYCLE IS WRITTEN
// IN, AND PARSES NO CONSTRUCT YET: `pattern_error.npk` (the closed kind list and
// the one constructor, RX-172), `cursor.npk` (the byte cursor, RX-173), `ast.npk`
// (the arena, RX-174) and `parse.npk` (the parser's entry and its first refusal,
// RX-175). `tests/unit/syntax_skeleton.npk` shows they compose, through this
// file's re-exports alone.
//
// EVERY LINE BELOW IS `pub use`, ONE NAME PER LINE (`BUILD.md` B-15a rules 1"""), (
r"""pub use "./ast.npk".ast_free;
""",
r"""pub use "./ast.npk".ast_free;

// ---- the parser's entry (RX-175) ----------------------------------------------
pub use "./parse.npk".parse_check_length;
"""),
]

EDITS["src/syntax/README.md"] = [(
r"""Pattern text to an AST, driven by an **explicit stack** so that a deeply nested
pattern is a refusal and never a blown call stack. Every error carries a byte
offset into the pattern. Governed by `meta/specs/SYNTAX.md`. Built in cycle
0.1.
""",
r"""Pattern text to an AST, driven by an **explicit stack** so that a deeply nested
pattern is a refusal and never a blown call stack. Every error carries a byte
offset into the pattern. Governed by `meta/specs/SYNTAX.md`. Built in cycle
0.1.

Since cycle 0.1.0 it holds the pieces every later subcycle is written in, and
parses no construct yet:

| File | What |
|---|---|
| `syntax.npk` | the layer entry: every name the layer offers, `pub use`, one per line |
| `pattern_error.npk` | `PatternErrorKind` (`SYNTAX.md` §9), `PatternError` (`SAFETY.md` S-9), and `pattern_error`, the only way to build one — RX-172 |
| `cursor.npk` | the byte cursor: one byte of lookahead, moved by nothing outside it — RX-173 |
| `ast.npk` | the AST arena: sixteen kinds of 56-byte node that own nothing (`SYNTAX.md` Y-26, Y-27) — RX-174 |
| `parse.npk` | the parser's entry: at 0.1.0 only its first refusal, `parse_check_length` — RX-175 |

`tests/unit/syntax_skeleton.npk` composes them through `syntax.npk` alone.
"""),
]

EDITS["meta/specs/SAFETY.md"] = [(
r"""and `hir` below the error: a program importing `nregex/unicode.npk` to ask
whether a codepoint is alphabetic owes **nothing**.
""",
r"""and `hir` below the error: a program importing `nregex/unicode.npk` to ask
whether a codepoint is alphabetic owes **nothing**.

*(@@DATE@@, cycle 0.1.0 — RX-175: `syntax` is below the error too; it sits
under `hir` in B-16's diagram and cannot import `api`. So the parser answers a
`PatternError` as a value, `PatternError?`, and `api` turns the first one into
`ERegexPattern`. `src/syntax/syntax.npk` reaches `core`, so a program importing
it owes `core`'s eleven arms, measured at `c970483`: the language's six,
`IntOverflow`, `OutOfBounds`, `DecreasesViolated`, `LimitViolated` and
`ShiftRange` — none of this library's own.)*
"""),
]

EDITS["meta/DECISIONS.md"] = [(
r"""read the `Vec` and index it past `ast_get`; **`AstNode`'s fields sealed** — the parser, in another module,
builds nodes, and a node has no invariant a constructor would keep.
""",
r"""read the `Vec` and index it past `ast_get`; **`AstNode`'s fields sealed** — the parser, in another module,
builds nodes, and a node has no invariant a constructor would keep.

### RX-175 — the syntax layer answers a `PatternError` as a value, `PatternError?`, never as an identity; the pattern's length is refused first; and 0.1.0 writes no parser, only the entry's first refusal and a unit that composes the pieces

**@@DATE@@, cycle 0.1.0 (the plan's PD-19), at compiler `c970483`.**

- **A value, because `syntax` is below the error.** The library's one `error:` identity, `ERegexPattern`, is
  `api`'s (`SAFETY.md` S-8), and `syntax` sits below `api` (`BUILD.md` B-16), so it cannot raise it. A parse
  answers `PatternError?` — `NIL`, or the first error — and `api` turns the first error into the identity.
  Cycle 0.1.1's parse is `parse_pattern(uint8[]:pat, Ast->:out)`: the pattern as a view, the tree by pointer,
  and the arena the caller's to free either way.
- **The length first** (the first draft's D5): `parse_check_length(uint8[]:pat)` answers `PatternTooLong`
  for a pattern longer than `NREGEX_PATTERN_BYTES` — its offset the first byte past the bound, its length the
  bytes over it, its detail the bound — and `NIL` otherwise, and the parse calls it before a cursor exists: it
  is the cheapest refusal, and it bounds everything after it, the arena included. Measured: on the bound
  `NIL`, one over refused (`tests/unit/parse_check_length.npk`), and a refused pattern pushes no node
  (`tests/unit/syntax_skeleton.npk`).
- **No parser in `src/` at 0.1.0.** The subcycle's acceptance — a skeleton that accepts `a` and reports offset
  0 for `(` — is a unit, `tests/unit/syntax_skeleton.npk`, built from `syntax.npk`'s re-exports alone.
  `src/syntax/parse.npk` holds the entry's first refusal and nothing else until 0.1.1.
- **The bill.** `src/syntax/syntax.npk` reaches `core`, so a program importing it owes `core`'s eleven arms
  (measured): the language's six, `IntOverflow`, `OutOfBounds`, `DecreasesViolated`, `LimitViolated` and
  `ShiftRange`. `SAFETY.md` S-11 says `syntax` is below the error too.

*Alternatives declined:* **an `error:` identity in `syntax`** — REACH-002 makes an identity an arm in every
program that can reach it, and S-8 allows the library exactly one; **`Result<Ast>` failing with
`ERegexPattern`** — `syntax` would import `api`, to its left (B-16); **a `bool` and a `PatternError`
out-parameter** — the caller would build a `PatternError` to pass in, and the closed list has no kind that
means "none"; **a skeleton parser in `src/`** — outside its two cases it would have to trap or answer a kind
about a pattern it did not parse, and 0.1.1 would delete it; **the length checked during the scan** — the
cheapest refusal would come after the most expensive work.
"""),
]

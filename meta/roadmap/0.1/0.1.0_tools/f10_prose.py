r"""0.1.0 step 6 -- the prose: every statement of the tree's state or of a count that
steps 1 to 5 made false (`0.1.0.md` §7's count sweep lists them). The status in
`README.md` and `CLAUDE.md`, `CLAUDE.md`'s counts, the rejection suite's README and the
manifest's comment on it, and `ROADMAP.md`'s row for cycle 0.1. Applied by
`python3 -B f10_edit.py prose "$REPO"` after step 5.
"""

EDITS = {}

EDITS["README.md"] = [(
r"""> **Status: cycle 0.0, the foundations, closed on 2026-09-26.** The language
> probes, the test harness and the storage primitives in `src/core/` are built
> and audited; nothing matches a pattern yet. **Cycle 0.1, the pattern parser, is
> next.** The specification set is in""",
r"""> **Status: cycle 0.1, the pattern parser, is open.** Cycle 0.0, the
> foundations, closed on 2026-09-26 — the language probes, the test harness and
> the storage primitives in `src/core/` are built and audited — and cycle 0.1.0
> laid the parser's pieces in `src/syntax/`: the closed list of pattern errors,
> the byte cursor and the AST arena. Nothing parses or matches a pattern yet.
> The specification set is in"""),
]

EDITS["CLAUDE.md"] = [(
r"""systems language at `../../nitpick`. **Status: cycle 0.0, foundations, CLOSED on
2026-09-26** — the sixth audit accepted it, and it is archived in
`meta/roadmap/done/0.0/`; **cycle 0.1, the pattern parser, opens next** from
`meta/roadmap/0.1/0.1.0.md`. The
""",
r"""systems language at `../../nitpick`. **Status: cycle 0.1, the pattern parser, is
open, and its 0.1.0 is done** — the pieces the parser is written in, in
`src/syntax/`: the closed list of pattern errors and their one constructor, the
byte cursor, and the AST arena (RX-171 … RX-175, `meta/roadmap/0.1/0.1.0.md`).
Cycle 0.0, foundations, CLOSED on 2026-09-26 — the sixth audit accepted it, and
it is archived in `meta/roadmap/done/0.0/`. The
"""), (
r"""`tests/rejection/` holds twenty-one consumer-facing refusals (five of them the""",
r"""`tests/rejection/` holds twenty-four consumer-facing refusals (five of them the"""), (
r"""six loan and pass-out pins, refused `TYPE-085` and `TYPE-047`, and `vec_get` at an
owning element, refused `TYPE-017`); `harness/` builds, sweeps,""",
r"""six loan and pass-out pins, refused `TYPE-085` and `TYPE-047`, and `vec_get` at an
owning element, refused `TYPE-017`; and since 0.1.0 the syntax layer's three — a
`PatternError` literal and a cursor's position written, each refused `TYPE-079`,
and the AST's `Vec` read, refused `TYPE-080`); `harness/` builds, sweeps,"""), (
r"""cycle 0.0 close (the sixth audit's N-30). **No matching happens yet**: `src/syntax/`,
`src/hir/`, `src/compile/`, `src/engine/`, `src/unicode/` and `src/api/` are
still one placeholder module each. A full green run at compiler `c970483` is
**220 units** (after the cycle 0.0 close; 218 after cycle 0.0.4e;""",
r"""cycle 0.0 close (the sixth audit's N-30). **Since 0.1.0 `src/syntax/` holds the
parser's pieces** — `pattern_error.npk`, `cursor.npk`, `ast.npk` and `parse.npk`
behind its layer entry, with ten unit programs and three refusals of their own —
and parses no construct yet. **No matching happens yet**: `src/hir/`,
`src/compile/`, `src/engine/`, `src/unicode/` and `src/api/` are still one
placeholder module each. A full green run at compiler `c970483` is
**250 units** (after cycle 0.1.0; 220 after the cycle 0.0 close; 218 after cycle 0.0.4e;"""),
]

EDITS["tests/rejection/README.md"] = [(
r"""## Why they are the standing instance of rule B-7

All twenty-one import `src/` by a **relative** path — the two `failsafe_*` fixtures
`../../src/lib.npk`, the other nineteen the `../../src/core/` modules they test
(*"all seven" went stale when the fourth triage added `bytes_copy.npk`; corrected
at 0.0.4d; "fourteen" and "twelve" at 0.0.4e*) —""",
r"""## The syntax layer's three — cycle 0.1.0

Each pins a guarantee the compiler now holds for `src/syntax/`, and each compiles
with the one qualifier it tests deleted (`meta/roadmap/0.1/0.1.0.md`'s controls):

- **`pattern_error_literal.npk`** — a `PatternError` literal outside
  `src/syntax/pattern_error.npk`: `NITPICK-TYPE-079`, once per sealed field. So
  `pattern_error(…)`, which takes an offset and refuses a negative one, is the
  only way to build an error (RX-172).
- **`cursor_pos_write.npk`** — a write of a `Cursor`'s `pos`: `NITPICK-TYPE-079`.
  So nothing outside `cursor.npk` moves a cursor, and the parser's one byte of
  lookahead is the compiler's rule (RX-173).
- **`ast_nodes_read.npk`** — a read of `Ast.nodes`: `NITPICK-TYPE-080`. So every
  access to the arena goes through `ast_get`, `ast_set` and `ast_push` (RX-174).
  It reads `.count` rather than an element, so the `TYPE-022` cascade the
  compiler adds at a generic call — gone at its next landing — cannot join its
  code set.

## Why they are the standing instance of rule B-7

All twenty-four import `src/` by a **relative** path — the two `failsafe_*` fixtures
`../../src/lib.npk`, nineteen the `../../src/core/` modules they test, and three
`../../src/syntax/syntax.npk` (*"all seven" went stale when the fourth triage added
`bytes_copy.npk`; corrected at 0.0.4d; "fourteen" and "twelve" at 0.0.4e;
"twenty-one" at 0.1.0*) —"""),
]

EDITS["nitpick.toml"] = [(
r"""# and the six loan and pass-out pins and `vec_owning_get_moves_out` since 0.0.4e)
# the `src/core/` modules they test -- which makes them the standing""",
r"""# and the six loan and pass-out pins and `vec_owning_get_moves_out` since 0.0.4e)
# the `src/core/` modules they test, and since cycle 0.1.0 three the syntax
# layer's entry, `src/syntax/syntax.npk` -- which makes them the standing"""),
]

EDITS["meta/roadmap/ROADMAP.md"] = [(
r"""| **0.1** | **The pattern parser** — syntax to AST, an explicit stack, byte-accurate errors — **NEXT: it opens from [`0.1/0.1.0.md`](0.1/0.1.0.md), planned and rehearsed at `c970483`** | 0.0 |""",
r"""| **0.1** | **The pattern parser** — syntax to AST, an explicit stack, byte-accurate errors — **OPEN: [`0.1.0`](0.1/0.1.0.md), the cursor and the AST, done; 0.1.1, the core grammar, is next** | 0.0 |"""),
]

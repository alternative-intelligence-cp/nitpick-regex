# Cycle 0.1 — The pattern parser

**`src/syntax/`: pattern text to an AST, driven by an explicit stack, with a
byte offset on every error.**

> **OPEN. [`0.1.0`](0.1.0.md) is DONE (2026-09-26)** — RX-171 … RX-175 in six work
> commits, `64a5ca9` … `0d26478`, 250/250 at `c970483` and in CI — **and [`0.1.0b`](0.1.0b.md), the
> adoption of compiler `5fbaf4a` with the ecosystem audit's items, is DONE (2026-09-27)** — RX-176 … RX-180 in
> seven work commits, `2c748d4` … `186db2c`, 250/250 at `5fbaf4a` and in CI run 36338559696 — **and [`0.1.1`](0.1.1.md),
> the core grammar, is DONE (2026-09-27)** — RX-181 … RX-187 in four work commits, `34b2801` … `1953d72`, 260/260 at
> `5fbaf4a` and in CI run 36347047570 — **and [`0.1.1b`](0.1.1b.md), open question O-R3 — `Vec<T: Copy>`, the
> bound on the type — is PLANNED** (2026-09-27, rehearsed at `5fbaf4a`), **then 0.1.2**. *(Until 0.1.1b's plan this
> banner said "Next, open question O-R3 as a subcycle of its own, then 0.1.2" (the board, 2026-09-27).)* *(Until
> 0.1.1's record it said 0.1.1 "is next, planned and rehearsed at `5fbaf4a`".)*
> *(Until 0.1.0b's record this banner said
> 0.1.0b and 0.1.1 "are PLANNED (2026-09-27, one planner dispatch, both rehearsed at `5fbaf4a`) and run in that
> order".)* *(Until
> then this banner said 0.1.1 was next and its file its planner's to write — `0.1.0.md` §8.)* *(Until
> 0.1.0's record this banner opened "OPENS NEXT":)* Cycle 0.0 closed on 2026-09-26 — the sixth audit accepted it, and it
> is archived in [`../done/0.0/`](../done/0.0/README.md). [`0.1.0.md`](0.1.0.md) is the
> first dispatch, revised at that close for what its last audit taught — and made
> execution-grade by a planner before that dispatch, rehearsed at `c970483` on
> 2026-09-26: B-15a's rule 2 decided first, then the error list, the cursor, the AST
> and the parser's entry, five decisions in six commits (`0.1.0.md` §2, §3).

> **`0.1.0.md` is written execution-grade at cycle 0.0's close** (0.0.5, step
> 5), so this cycle is openable by a session that was not present for the
> probes. That is the convention for every cycle: the opening subcycle file is
> written by the cycle before it.

## Why here

It is the first thing that reads a pattern, and everything downstream is
defined in terms of what it produces. It is also entirely pure computation over
a byte slice, so its whole suite is fixtures — no harness capability beyond
what 0.0 built.

## Decisions in

RX-010, RX-013, RX-017, RX-032, RX-060. Settled.

**Open questions to settle:** O-Y2 (does `x` mode ignore whitespace inside
classes? recommendation: no, matching Rust, and refuse `xx`).

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| [0.1.0](0.1.0.md) | **The cursor and the AST** — the byte cursor with offsets, the AST arena, the node kinds | a parser skeleton that accepts `a` and reports an offset for `(` |
| [0.1.0b](0.1.0b.md) | **The adoption of `5fbaf4a`, and the ecosystem audit's items** — probe 18 refused, `Pod` into `Copy`, the target pins held, D-332's count, EC4 EC5 EC11 ED1 ED3 ES4 EK2 | `250/250` at `5fbaf4a`, and CI asserting the emission |
| [0.1.1](0.1.1.md) | **The core grammar** — literals, concatenation, alternation, groups, quantifiers — and the error text | `SYNTAX.md` §1's grammar minus classes, escapes and flags; every refusal at its byte, with a sentence saying what to write |
| [0.1.1b](0.1.1b.md) | **`Vec<T: Copy>`** — open question O-R3: the bound on the type and every verb, the owning units and `vec_free_owning` retired, the element check restated | `Vec<string>` refused at the type and at each verb; `238/238` at `5fbaf4a` |
| 0.1.2 | **The explicit stack** — nesting, `NREGEX_NEST_DEPTH`, and the refusal | 10 000 levels deep is a `NestTooDeep`, not a segfault |
| 0.1.3 | **Classes** — items, ranges, Perl and POSIX classes, nesting, `&&`/`--`/`~~` | every class form in §5, parsed to unresolved items |
| 0.1.4 | **Escapes and flags** — every escape in §1, flag scoping, `(?-u)` | the escape table, and `(?i)` scoped correctly |
| 0.1.5 | **The refusals** — every construct in §8, by name, with its offset | `BackreferenceUnsupported` names the guarantee, not "unsupported" |
| 0.1.6 | **Close** — `check_error_kinds_tested` live | `done/0.1/`, `0.2.0.md` written |

## Checklist

### 0.1.0 — the cursor and the AST
- [x] `BUILD.md` B-15a's rule 2 decided before the layer entry gains its first `pub use` — its reason was a compiler defect fixed at `94874ce` (`0.1.0.md` PD-15) — **retired, RX-171, `64a5ca9`**: block 1a measured the shape refused `NITPICK-RESOLVE-002` at `950bb1d` and running at `94874ce` and `c970483`; eight live sites corrected and `_check_umbrella`'s rule-2 branch removed, a planted plain `use` still failing it by rule 1; 220/220
- [x] a byte cursor over `uint8[]` with `offset`, `peek`, `bump`, `eat`, and **no lookahead beyond one byte** except where the grammar names it — its fields sealed, so that is the compiler's rule (PD-17) — **RX-173, `7c34431`**: `src/syntax/cursor.npk`; a write of `pos` outside it is `NITPICK-TYPE-079` (`tests/rejection/cursor_pos_write.npk`); `tests/unit/cursor_unit.npk` 0 at `c970483` and `9f6f370`; 234/234
- [x] the AST as a flat POD arena, the same shape the HIR uses (`HIR.md` H-2) — a `Vec<AstNode>` reallocates and a pointer into it would dangle — its operands `int64` so the parser narrows nothing, and the node kinds declared (PD-18; the draft said `int32`) — **RX-174, `c291752`**: `src/syntax/ast.npk`, 56 bytes (`tests/unit/ast_size.npk` exits 56), sixteen kinds (`SYNTAX.md` Y-26, Y-27), `nodes` hidden (`NITPICK-TYPE-080`, `tests/rejection/ast_nodes_read.npk`); 245/245
- [x] `PatternError` with `kind`, `offset`, `span_len`, `detail`, and `PatternErrorKind` all of `SYNTAX.md` §9 (PD-16) — **RX-172, `bcbf7e3`**: `src/syntax/pattern_error.npk`, all thirty-seven kinds in §9's order, held there by an exhaustive `pick` in `tests/unit/pattern_error_unit.npk`; 229/229
- [x] every error constructed through one helper, so no site can forget the offset — the fields sealed, so no other site compiles (PD-16) — **RX-172, `bcbf7e3`**: a `PatternError` literal outside the module is `NITPICK-TYPE-079`, once per field (`tests/rejection/pattern_error_literal.npk`); `pattern_error` stops on a negative offset or length, 94
- [x] `NREGEX_PATTERN_BYTES` enforced before anything else runs (PD-19) — **RX-175, `1224dce`**: `parse_check_length` answers `NIL` on the bound and `PatternTooLong` one over (`tests/unit/parse_check_length.npk`), and a refused pattern pushes no node; 250/250
- [x] a skeleton that accepts `a` and reports offset 0 for `(`, composed from the layer entry alone (PD-19) — **RX-175, `1224dce`**: `tests/unit/syntax_skeleton.npk`, through `syntax.npk`'s re-exports alone (one deleted: `NITPICK-RESOLVE-002`); 250/250 locally, and in CI run 36252533730 on `0d26478`

### 0.1.0b — the adoption of `5fbaf4a`, and the ecosystem audit's items
- [x] the unchanged tree measured at `5fbaf4a` — `248/250`, only probe 18 moving — and D-332's count over every file carrying `expect-error` (`0.1.0b.md` §1) — **block 0b `SAME`**: `248/250`, both failures probe 18 (`NITPICK-TYPE-014` at 42:39); thirty-one files, the literal's `TYPE-079` the one count that differs (×4 at 22:22), at both pins
- [x] probe 18 in `tests/probe/refused/`, `NITPICK-TYPE-014`, one site (PD-20) — **RX-176, `2c748d4`**: at 35:39, and still compiling at `c970483`; the split 24 / 8
- [x] the manifest's `triple` and `datalayout`, READ: the layout held to `opt`'s derivation and every linked emission to both; self-check cases 24, 25 (PD-20) — **RX-176, `2c748d4`**: `ok    target x86_64-unknown-linux-gnu, its layout the one the pinned opt derives` on every run; cases 24 and 25 red, each naming its fault; `250/250`
- [x] every adoption re-reads what `lexical.py` mirrors — `BUILD.md` B-4e — and this one's re-read recorded (PD-20; the audit's ED1) — **RX-176, `2c748d4`**: `lexer.npk` +13/−2, a character literal's width (DEF-145), not its span; `p_parse_import` hashing the same at both pins; no `\u{…}` character literal in the tree; the mirror does not move
- [x] 0.1.0's block-3b controls re-run: `BORROW-015` for the owner written, `BORROW-001` for a local's view returned — **block 0b**: `NITPICK-BORROW-015` at 6:5 and `NITPICK-BORROW-001` at 5:10 at `5fbaf4a`; the owner written compiling at `c970483` — judged by `npkc` alone, never built or run
- [x] `Pod` retired into the prelude's `Copy`: `vec_get<T: Copy>`, the AST types derive it (PD-21) — **RX-177, `855c5b6`**: no `Pod` in `src/` code; `vec_owning_get_moves_out` `NITPICK-TYPE-017` at 32:31; `AstKind`'s derive removed in a copy, `NITPICK-TYPE-087` at 80:1; `250/250`
- [x] a rejection's sites counted per code; the literal fixture names its code four times; cases 26, 27 (PD-22) — **RX-178, `7d837e3`**: thirty-two files, no count differing; the literal ×4 at 31:22; cases 26 and 27 red; `250/250`
- [x] `check_error_budget` and `check_accessor_confinement` read blanked text whole; cases 28, 29 (PD-23; EC4, EC5) — **RX-179, `1445ff6`**: against the previous checks every plant passes (block 4's control, EC4 and EC5 reproduced); against the new, each fails by name and the clean trees pass; `250/250`
- [x] CI pinned to `5fbaf4a` in a commit of its own — **`6a08a22`**
- [x] CI asserts the compiler's commit, the emission against the pin's row, and the unqualified `GREEN.` (PD-24; ED3, EK2) — **RX-180, `a536546`**, its patch amended for BUILD.md B-4c and §8a and RX-133's marker (`0.1.0b.md`'s record); CI run 36338559696 on `186db2c`: `compiler HEAD == 5fbaf4a… (clean)`, `npkc.ll == the pin's emission, 30232291 B / 5630c2b4…`, `GREEN.` and `250/250`
- [x] EC11's two cycles corrected; the registry's entry for 0.1.0's `EMIT-002` finding recorded and struck (ES4); the Node-24 bump homed with the workbench (EK2) — **`186db2c`**, its patch amended for ten more statements steps 1–6 had made stale (`0.1.0b.md`'s record): the table takes the roadmap's 0.6.1 and 0.4.3; O-N32 struck as discharged by DEF-142 and DEF-143; the Node-24 bump the orchestrator's, one research request for both CIs

### 0.1.1 — the core grammar
- [x] `EmptyAlternate` retired — Y-27's `Empty` accepts every empty alternative (PD-25) — **RX-181, `34b2801`**: thirty-six kinds, `pattern_error_unit` 0 at both legs; `a|`, `|a`, `|`, `()`, `(|a)+` and `a(|)` parse (`parse_grammar` cases 5–7, 10, 49, 68); 250/250
- [x] the pattern checked whole as UTF-8 first, per RFC 3629 — `InvalidPatternEncoding` at the first ill-formed sequence (PD-27) — **RX-183, `6feaa54`**: `parse_check_encoding`, RFC 3629's table case for case (`meta/research/utf8-rfc3629.md`); `parse_encoding` holds seventeen ill-formed sequences and nine boundaries decoded, `(` then 0xFF refused at the byte; 258/258
- [x] alternation, concatenation, groups (capturing, non-capturing, named), quantifiers (`*`, `+`, `?`, `{n}`, `{n,}`, `{n,m}`, each with a lazy `?`) — **RX-182, RX-184, `6feaa54`**: `parse_grammar`'s fifty-nine shapes, each tree dumped and compared whole, 0 at −O0 and through `opt -O2`, and 3 with one expectation wrong; 258/258
- [x] capture numbering by opening parenthesis, left to right, from 1 (Y-6) — **RX-185, `6feaa54`**: `parse_grammar` cases 13–16, 46, 47, named groups numbered too
- [x] `(?<name>…)` only; `(?P<name>…)` and `(?'name'…)` refused as `WrongNamedGroupSpelling` **naming the right spelling** (RX-017) — **RX-185, `6feaa54`; the sentence RX-187, `09f000e`**: `parse_refusals` cases 49, 50; `pattern_error_text` cases 14, 15 write `(?<name>...)`
- [x] `DuplicateGroupName` (Y-8) — **RX-185, `6feaa54`**: `parse_refusals` cases 46–48, at the second name, detail the first group's number
- [x] `NothingToRepeat`, `DoubleRepeat`, `BadRepeatBounds` (`{3,1}`), `RepeatTooLarge` — **RX-184, `6feaa54`**: `parse_refusals` cases 12–36, each decided at the quantifier's first byte; `a{1000}` parses and `a{1001}` is refused
- [x] `NREGEX_CAPTURE_GROUPS` enforced — **RX-185, `6feaa54`**: `parse_limits` — 250 groups parse, the 251st is `TooManyCaptureGroups` at its `(`, byte 500, named groups counted too
- [x] one explicit-stack walk, no function calling itself; the tree's spans and flags as Y-33 (PD-26) — **RX-182, `6feaa54`**: one `while` in `parse_run`; of `parse.npk`'s twenty-seven functions none calls itself and none is on a call cycle (read by script, `0.1.1.md`'s record); 250 nested groups parse (`parse_limits`); spans and flags by `parse_grammar` cases 60–68 and its `!flags` check
- [x] §8's group heads — lookaround, atomic, recursion, `(?P=`, the comment group — and a possessive quantifier refused where they are read (PD-29) — **RX-185, `6feaa54`**: `parse_refusals` cases 51–63 and 21–23; `(?-1`'s detail the digit, the head's last byte, as Y-30 says (the patch amended, `0.1.1.md`'s record)
- [x] `[`, an escape other than punctuation, and a flag refused provisionally, pinned by no test (PD-30) — **RX-186, `6feaa54`**: none pinned but `(?Px)`, `UnknownFlag` at the `P` — final, since `P` is no flag, and so stated in Y-31 and RX-186 (`parse_refusals` case 64; the patch amended, `0.1.1.md`'s record)
- [x] `pattern_error_text`: every kind a sentence — what is wrong, at which byte, what to write instead — 0.1.1's held to the letter (PD-31) — **RX-187, `09f000e`**: twenty-two sentences held to the letter and every kind naming its byte (`pattern_error_text.npk`), 5 with one sentence changed; no new symbol, and the bill `core`'s eleven before and after; 260/260 — one sentence reads the wrong reason for one input, a NUL inside a group name (`0.1.1.md`'s record, for the author)

### 0.1.1b — `Vec<T: Copy>`, open question O-R3
- [ ] the shape measured before it is taken: the bound compiles, every verb must repeat it, twelve files move and no other, the masked IR of every other program identical (`0.1.1b.md` §1)
- [ ] `struct:Vec<T: Copy>` and every verb bounded; `Vec<string>` refused at the type and at each of thirteen verbs, one fixture, fourteen sites; the ten owning units and `vec_unit`'s owning section retired; O-R3 struck (PD-32)
- [ ] `vec_free_owning` and `drop_element` removed with their re-export and unit; the guard on `vec_free` still 94 (PD-33)
- [ ] `check_vec_elements_own_nothing` kept and restated: a pointer-holding `Copy` struct compiles and the check fails it; a POD struct without `Copy` is refused and the check clears it (PD-34)
- [ ] the prose: the status, `238` units, `src/core/` at 37 unit programs, and what cycles 0.2 and C-1's inherit

### 0.1.2 — the explicit stack
- [ ] a `Vec<Frame>` bounded by `NREGEX_NEST_DEPTH`, **no native recursion anywhere** (RX-032)
- [ ] `NestTooDeep` names the offset of the parenthesis that exceeded it — checked in `parse.npk`'s `push_group`, its sentence already written (`0.1.1.md` §8)
- [ ] **the gate for this subcycle**: a 10 000-level pattern produces a clean refusal, and a wrapper script confirms the process exited normally rather than on a signal
- [ ] `// stress: 40` on that test, because a stack overflow is timing-shaped
- [ ] a tree check that greps `src/syntax/` for a function that calls itself

### 0.1.3 — classes
- [ ] `[`'s provisional `UnclosedClass` (`SYNTAX.md` Y-31) replaced by the class parser, and each class kind's sentence held to the letter (`0.1.1.md` §8)
- [ ] class items, ranges, negation, and the literal-`]`-first rule
- [ ] `BadClassRange` (`[z-a]`), `EmptyClass`, `UnclosedClass`
- [ ] Perl classes `\d \D \w \W \s \S` parsed as *unresolved* items — resolution is 0.3's, and the parser must not need the Unicode tables to exist
- [ ] POSIX bracket classes, **inside a class only**
- [ ] `\p{…}` / `\P{…}` parsed with the property spec kept as text, resolved at 0.3
- [ ] nested classes `[a[b-c]]`
- [ ] `&&`, `--`, `~~` with the precedence in Y-17, and `ClassOpMismatch`
- [ ] O-Y2 decided and recorded

### 0.1.4 — escapes and flags
- [ ] the provisional `UnknownEscape` and `UnknownFlag` (`SYNTAX.md` Y-31) replaced; a `Flags` node never the pending atom (`(?i)*` is `NothingToRepeat`); each kind produced here held to its sentence (`0.1.1.md` §8)
- [ ] every escape in §1's `Escape` production
- [ ] **`\` before an unlisted ASCII letter or digit is `UnknownEscape`, never a literal** (Y-2) — a test per unassigned letter
- [ ] `\x41`, `\x{1F600}`, `A`, `\U0001F600`, with `BadHexEscape`, `BadUnicodeEscape`, `InvalidCodepoint` (surrogates and above `U+10FFFF`)
- [ ] flags `imsxu`, scoped per Y-12: `(?i:…)` to the group, `(?i)` to the end of the enclosing group, `(?-i)` clearing
- [ ] `x` mode: whitespace and `#`-to-end-of-line ignored, per O-Y2's answer
- [ ] `(?-u)` byte mode, and `ByteModeNonAscii` when a non-ASCII literal appears under it (Y-14) — **naming the codepoint**
- [ ] `UnknownFlag`

### 0.1.5 — the refusals
- [ ] every construct in §8 refused with its own kind and offset — the group-head ones and the possessive quantifier since 0.1.1 (Y-30); here the escape-shaped ones
- [ ] **each message names the guarantee or the alternative, never "unsupported"** (K-1) — the sentences exist since 0.1.1 (Y-34); here each is held to the letter: `BackreferenceUnsupported` says the pattern could not be matched in linear time; `UnsupportedQuoting` names `regex_escape()`; `\Z` names `\n?\z`; `\p{InGreek}` names `\p{Script=Greek}`
- [ ] `regex_escape(text)` implemented here, since §8 points at it
- [ ] a rejection test per refusal in `tests/rejection/`, with the exact-code rule

### 0.1.6 — close
- [ ] **`check_error_kinds_tested` live and green**: every `PatternErrorKind` in `SYNTAX.md` §9 has a test that provokes it
- [ ] a fuzz pass over random byte strings as patterns: never traps, always terminates, always produces a program or an error with a valid offset
- [ ] findings written; `0.2.0.md` written; archived

## Gate

Every kind in `SYNTAX.md` §9 has a test that produces it, and
`check_error_kinds_tested` is green. A kind nothing can produce is a promise
the documentation makes and the code does not keep — the compiler found that
shape three times and called it the dormant-rule pattern.

## Watch for

- **`in`, `end`, `range` and `any` are keywords** and a parser wants all four.
  `src` for the cursor, `hi` for a range's upper bound, `rng` for a range
  value.
- **The offset is the product.** A parser that is right about structure and
  vague about position is a parser whose errors are useless. Every error goes
  through one constructor so no site can forget.
- **Do not resolve classes here.** `\w` and `\p{L}` are parsed to unresolved
  items; 0.3 resolves them. A parser that needed the Unicode tables would make
  cycle 0.1 depend on 0.3 and neither would be testable alone.
- **The explicit stack is the whole point of 0.1.2** and the temptation to
  "just use recursion for now" is exactly how the hazard survives to 1.0.

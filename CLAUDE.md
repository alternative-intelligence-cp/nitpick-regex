# CLAUDE.md

Guidance for Claude Code sessions working in this repository.

## What this is

`nregex` — a regular-expression library for **Nitpick**, the safety-critical
systems language at `../../nitpick`. **Status: cycle 0.1, the pattern parser, is
open, and its 0.1.0 is done** — the pieces the parser is written in, in
`src/syntax/`: the closed list of pattern errors and their one constructor, the
byte cursor, and the AST arena (RX-171 … RX-175, `meta/roadmap/0.1/0.1.0.md`).
Cycle 0.0, foundations, CLOSED on 2026-09-26 — the sixth audit accepted it, and
it is archived in `meta/roadmap/done/0.0/`. The
specifications, the decisions and the roadmap are complete; `tests/probe/` holds
**32** language probes with recorded verdicts, split **25 / 7** by kind (16 / 7,
then 17 / 6 when the `94874ce` re-pin discharged O-N10 and `probe02b` stopped
being refused — RX-125; then 19 / 6 when the `3d15ac9` re-pin made
`limit<Rules>` live and `probe13b` stopped being refused — RX-127; then 22 / 5
when the `c3bdae2` re-pin made `prove`, `requires` and `ensures` live — RX-152;
then 22 / 6 when probe 15 recorded that the compiler's lexer closes a block string
at the first `""` — found by the cycle 0.0 close's fourth triage, RX-157; then
24 / 7 when cycle 0.0.4d added probe 16 and its refused twin, the language fact
`Vec`'s move-only marker rests on, and probe 17, a compiler defect a lent
parameter shows — RX-161, RX-162; then 25 / 7 when cycle 0.0.4e moved probe 15 out
of `refused/` and probe 17 into it — the compiler's lexer and its loan rule fixed —
and added probe 18, a compiler defect an impl's `move` shows — RX-168 … RX-170);
`tests/rejection/` holds twenty-four consumer-facing refusals (five of them the
containers' seal, since 0.0.4c; one a `Bytes` copy refused `TYPE-046`, since the
fourth triage; since 0.0.4d five `Vec` and `SparseSet` copies refused
`TYPE-046` and a write through `Bytes.buf` refused `TYPE-080`; and since 0.0.4e the
six loan and pass-out pins, refused `TYPE-085` and `TYPE-047`, and `vec_get` at an
owning element, refused `TYPE-017`; and since 0.1.0 the syntax layer's three — a
`PatternError` literal and a cursor's position written, each refused `TYPE-079`,
and the AST's `Vec` read, refused `TYPE-080`); `harness/` builds, sweeps,
diffs and judges them, **and proves first that it can fail**; and since 0.0.4
`src/core/` is real — `Vec<T>`, `Bytes`, `ByteSet`, `SparseSet` and `limits.npk`,
with 48 unit programs of their own — seven of them measuring what each `Vec` verb does at an
owning element type, which `SAFETY.md` S-23a keeps out of `src/` (the eighth, `vec_get`'s, is a
refusal since cycle 0.0.4e: `vec_get` takes `T: Pod`, RX-168); the swap and the moves a move-only
`Vec` still allows (RX-161); and `loan_spellings`, the spellings the six loan and pass-out
refusals prescribe — the six were units pinning a compiler defect until `c970483` refused them
(RX-169); and `vec_get_pod_struct`, a consumer's own `Pod` for a POD struct, read back through
`vec_get` with every name from `core.npk`'s re-exports — RX-168's positive half, pinned at the
cycle 0.0 close (the sixth audit's N-30). **Since 0.1.0 `src/syntax/` holds the
parser's pieces** — `pattern_error.npk`, `cursor.npk`, `ast.npk` and `parse.npk`
behind its layer entry, with ten unit programs and three refusals of their own —
and parses no construct yet. **No matching happens yet**: `src/hir/`,
`src/compile/`, `src/engine/`, `src/unicode/` and `src/api/` are still one
placeholder module each. A full green run at compiler `c970483` is
**250 units** (after cycle 0.1.0; 220 after the cycle 0.0 close; 218 after cycle 0.0.4e; at `c3bdae2`, 214 after the cycle 0.0 close's fifth audit triage, 210 after cycle 0.0.4d, 194 after the fourth triage, 174 after the third), plus eight tree checks; take those numbers from the runner's
summary rather than from here. **Nothing is PENDING any more**:
`tests/unit/bytes_copy_string_empty.npk` was committed red under
`pending-until: fe42dba` while this tree was pinned below that fix (DEF-25); at
`c3bdae2` it started passing, the harness reddened the run, and the marker was
deleted (cycle 0.0.4b).
**This file said 98 and six in one paragraph and *four* tree checks 220 lines
lower**, and the cycle 0.0 audit found it (N-2) in the document every session is
told to read first. Two sections of one file disagreeing is the shape this
repository named a durable lesson and then left standing in its own onboarding
page: **proximity is not review**, and a number written twice is a number that
will be corrected once. There is now ONE statement of each count in this file,
and the runner's summary is the authority for both.

## Before starting a session here

Check **[`../BOARD.md`](../BOARD.md)** — it says whether this repository
is claimed by a stream, and by which. **One writer per repository, always.**
[`../WORKSTREAMS.md`](../WORKSTREAMS.md) is the dependency graph and the
stream partition: what gates this repository, what this repository gates, and
what to do when a cross-stream gate is not ready yet.

## Read these first, in this order

1. **`meta/specs/SAFETY.md`** — the constraints, and §2's decision that the
   whole library is arranged around. Most proposals that look reasonable in the
   abstract die on §1 or §2.
2. **`meta/specs/SYNTAX.md`** — what the pattern language accepts and refuses.
3. **`meta/specs/README.md`** — the index and reading order for the rest.
4. **`meta/DECISIONS.md`** — every settled decision with its reasoning. **Read
   before proposing a change**, because it is recorded why.
5. **`meta/roadmap/ROADMAP.md`**, then the current cycle's `README.md`.
6. **`meta/OPEN_QUESTIONS.md`** — what is not settled, each with a
   recommendation.
7. **`../PLAYBOOK.md`** — the shared house rules for every library in this
   ecosystem, if you have the sibling checkouts.

## The rules that are not negotiable

- **Automata only** (RX-003). No backreferences, no lookaround, no atomic
  groups, no recursion. A search is `O(m·n)`, always, on every input. This is
  not a performance preference: catastrophic backtracking is a denial of
  service triggered by untrusted data, and the language has no cancellation
  (D-062) with which to survive one.
- **One public `error:` identity** (RX-060). REACH-002 makes every one a
  mandatory `pick` arm in every consuming program's `failsafe`. A second is a
  **major version**. Detail rides in a `PatternError` value with a closed kind
  enum — thirty ways to be malformed, one identity.
- **Matching cannot fail, cannot trap, and cannot allocate** (RX-061). Every
  way a pattern can be wrong is found at compile time. `regex_find` returns
  `Match?`, not `Result<Match?>`. Anything that would put an error channel on
  the search path is wrong.
- **Every engine gives the same answer** (RX-041), and the suite proves it by
  running every case through every engine and with each optimisation disabled
  in turn. An engine is a performance decision, never a semantic one.
- **The specifications are the authority** (RX-002). Code that disagrees is a
  defect in the code. A specification that is wrong is amended by a decision
  recorded in `meta/DECISIONS.md`, in the same commit — never by a comment.
- **A settled decision's text is never rewritten.** Supersede it with a new
  numbered decision that says why.
- **No dependencies** (RX-007). Not the compiler's `src/`, not its `lib/`, not
  `nitpick-tui` even though both generate Unicode tables from the same UCD.
- **No syscalls** (RX-008). `check_no_syscalls` enforces it. A convenience that
  reads a file or an environment variable costs the library its
  target-independence.
- **Never work around a compiler defect.** Record the reproduction, stop, and
  raise it. A workaround buried in library code outlives the bug.

## The compiler constraints that shape everything

Full statement in `meta/specs/SAFETY.md` §1. The ones that bite hardest:

- **Borrows never pass up the call stack** (D-004), so a `Match` is byte
  offsets and not a slice, and an iterator cannot be returned from a function.
- **Owning values are move-only (TYPE-046) — and NOTHING keeps an owner out of an
  array or a `Vec`.** TYPE-046 asks for `move` when an owning place is copied;
  `pass` moves implicitly, so `vec_get` at `Vec<string>` compiles and MOVES the
  element out, leaving an empty slot `count` still counts. So instructions, HIR
  nodes and thread entries are POD **by design**, and `Vec<T>` is for a `T` that
  owns nothing (`SAFETY.md` S-23a, RX-155), enforced over `src/` by
  `check_vec_elements_own_nothing`, which is default-deny (RX-158): it clears an
  element only when it can see that it owns nothing. This bullet said until the third cycle 0.0
  audit that the language forced it.
  *(Since cycle 0.0.4e, compiler `c970483`, it does for `vec_get`: the old body is refused at
  every `T` (DEF-104), and `vec_get` takes `T: Pod`, which an owning type cannot implement as
  declared — so `vec_get` at `Vec<string>` is `NITPICK-TYPE-017`, not a move (RX-168). An impl
  that declares `move` on its `self` defeats that: a compiler defect,
  `tests/probe/probe18_impl_adds_move.npk`.)*
  **And since cycle 0.0.4d a `Vec` IS itself an owner** — a hidden zero-length array of
  `string` makes it one — so a `Vec`, a `SparseSet` and any struct holding one are
  move-only: copy one and it is `TYPE-046`; transfer it with `move(...)`; lend it BY VALUE
  only to a function that reads it; hand it by POINTER to anything that changes it
  (`SAFETY.md` S-23b; RX-161, RX-162). **Move-only is not "one handle"**: a callee can
  still free through its loan's address, a `for` binding is a loan too, and a GENERIC
  function passing out its lent `T` compiles and hands back a second owner — TYPE-047 is
  not asked of a lent `T` in a generic body (the registry's O-N22, the compiler's DEF-104).
  So no generic in `src/` takes a lent bare `T` (RX-167).
  *(At `c970483`, cycle 0.0.4e, all three are refused — a write through a loan
  `NITPICK-TYPE-085`, the generic pass-out `NITPICK-TYPE-047` (RX-169). A callee that
  changes a container takes `move T:p` or a pointer: `tests/unit/loan_spellings.npk`.)*
- **There are no closures** (D-018), so replacement is a template and iteration
  is a struct with `next`.
- **Integer overflow and division by zero trap. OUT-OF-RANGE INDEXING DOES NOT,
  on the type this library indexes most** (RX-111). D-070's check attaches to
  types that carry a length — a slice `T[]`, a fixed array `T[N]`. A
  `wild T->` block is a bare pointer and `Vec<T>.items` is one, and so is a
  `buffer` through `.ptr`, which has no slice route at all (RX-118). An
  out-of-range index there **reads and returns a heap word**, silently. The
  `vec_get`/`vec_set` and `bytes_get`/`bytes_set` pairs are the only bounds
  check this library has. `SAFETY.md` §5.3.
- **`comptime` cannot index a string**, so a compile-time-validated pattern is
  not currently expressible — see O-G1, which is the most valuable request on
  the list.
- **There are no static methods** (D-185), so construction is
  `regex_compile(…)`.

## Reserved words that read like ordinary names

`meta/specs/BUILD.md` §7 has the table. The ones this domain wants most:
`range`, `end`, `in`, `limit`, `any`, `buffer`, `raw`, `move`, `error`, `mod`,
`on`, `as`, `with`, `where`, `is`, `is_err`, `never`, `fails`, `pick`, `fall`,
`give`, `pass`, `fail`, `relay`, `drop`, `Rules`, `fixed`, `Self`, **`stack`**.

**`stack` is the one that costs an hour**, and cycle 0.0.0 paid it. It is a
MemoryQualifier beside `wild`, `wildx` and `defer`, it is the natural name for
an explicit-stack parser's local — which is `src/syntax/`'s whole shape — and
**it does not fail where you write it**: you get `PARSE-002` at the declaration
and then "this `{` is never closed" pointing at an enclosing brace dozens of
lines away, plus a cascade to the end of the file. *If a parse error claims an
unclosed brace and the braces are balanced, look for a local named after a
qualifier before you touch a brace.*

The substitutes this library uses, so the tree stays consistent: **`hi`** for a
range's upper bound and for a `Match`'s end (the fields are `lo` and `hi` by
`API.md` A-3's choice — **not** because `Match.end` is refused, which **RX-134
measured to be false at all three kept pins**: a reserved word is refused as a
**binding** name and accepted as a **field** name), **`src`** for an input
cursor, **`bound`** for a
limit, **`rng`** for a range value, **`dot`** for the any-character construct,
**`sel`** for a selection.

Three shapes that surprise a C or Rust habit: adjacent string literals do not
concatenate; `discard(x);` takes parentheses and `defer { … }` takes no
trailing semicolon; declarations end `};` and control-flow blocks do not. And a
file's `mod:` name must equal its basename.

## What cycles 0.0.0, 0.0.1 and 0.0.2 measured, that a reader would otherwise assume

Each of these was written the other way round in some document here before it
was measured. `meta/roadmap/done/0.0/0.0.0.md` §7,
`tests/conformance/TRANSCRIPT.txt` and `meta/roadmap/done/0.0/0.0.2.md` §5 are the
evidence.

- **An `Optional` is not `pick`-able.** `pick (m) { (NIL) {…}, (Match:g) {…} }`
  is `NITPICK-PARSE-005`; an `Optional` has no readable members. Test with
  `== NIL`, read with `??`. This is caller-visible on every entry point in
  `API.md` §2, because `regex_find` returns `Match?`.
- **`npkc` exit 0 does not mean a program is well-formed** (registry O-N11), and
  this library was a standing example: at `950bb1d` **every file in `src/`
  compiled at exit 0 and every one was refused by `llc`** (RX-115), because
  `npkc` never declared `@npk_failsafe`. **That mechanism expired at
  `94874ce`** — `npkc` declares it now, and at `c3bdae2` all 13 `src/` files
  compile and assemble — **and the conclusion did not** (RX-151): a module's
  object links neither alone (no `npk_failsafe`, no `main`) nor beside a
  program, which already carries everything it reaches (`ld.lld: duplicate
  symbol`). **There is no library object.** `src/` reaches the compiler only
  through a program root, and `tests/conformance/import.npk` is the smallest
  one. Run all four steps — `npkc`, `llc`, `ld.lld`, the binary — on anything
  you claim compiles.
- **`src/lib.npk` re-exports with `pub use`, one name per line** (RX-113). A
  plain `use` re-exports nothing, and the failure lands in the consumer, not in
  `src/lib.npk`. *(Until cycle 0.1.0 this bullet also said a file must never
  plain-`use` a path it also `pub use`s, because a plain `use` above the
  `pub use` silently cancelled the re-export — the compiler's DEF-7, fixed at
  `94874ce`. Measured at `c970483` it no longer does, and that rule is retired:
  RX-171.)*
- **`exit 0` traps on a leaked `wild` block and sees nothing else** (RX-110).
  D-151 counts `wild` blocks, D-188 counts live drivers, and neither sees a
  managed body — so a container freed without dropping its owning elements
  exits 0. Where the obligation is managed, the gate is a memory cap.
- **`%` and `/` each add two mandatory `failsafe` arms**, `DivByZero` and
  `DivOverflow`. The error budget is charged by arithmetic, not only by a
  declared `error:`.
- **`limit<Rules>` is LIVE, ENFORCED, and it charges every consumer a `failsafe`
  arm** (**RX-127**, measured here at the `3d15ac9` re-pin). It refused
  `NITPICK-RUNG-001` until the compiler's 1.5.2; it is now checked in every
  build, and a violation traps `LimitViolated`. **A limited binding anywhere in
  a program's reachable call graph makes `(LimitViolated)` a mandatory
  `failsafe` arm** — measured with controls at both `pub` and module-private
  visibility, because reachability follows the call graph and not visibility.
  That is a second arm on top of `SAFETY.md` S-8's one, so `src/` declares no
  `limit` of its own (S-24) — **and since cycle 0.0.4c the one limit `src/`
  carries is the prelude's `ListLen`, on its containers' counts** (`Vec.count`,
  `Vec.cap`, `Bytes.len`, `SparseSet.count`; S-24a, RX-153): every consumer of
  `vec.npk`, `bytes.npk` or `sparseset.npk` owes `LimitViolated`, and a count
  driven negative traps at the write. `requires` and `ensures` refused `NITPICK-RUNG-001`
  through `3d15ac9`; **at `c3bdae2` both are live**, each checked at run time and
  each charging every consumer one more arm — `RequiresViolated`,
  `EnsuresViolated` (`probe13c`/`probe13g`, `probe13d`/`probe13h`) — and `prove`
  is accepted and **checks nothing** in a plain build (`probe13a_prove_unchecked`).
  So the comment-form obligations in `src/` are comments by A′ — the answer to
  `meta/OPEN_QUESTIONS.md` Q-6, `VERIFICATION.md` P-1b (RX-164) — not because
  anything refuses them: a live clause is a numbered decision that accepts the arm
  it costs every consumer, and a comment is evidence of nothing (RX-152).
- **`never fails` may carry `limit`, `requires` and `ensures`** — the compiler's
  **D-241**, 2026-09-03. This repository shipped the opposite claim, that they
  are *mutually exclusive* by a *permanent* `NITPICK-TYPE-037`, and wrote it
  into cycle 0.0.0's record as deciding which `src/core/` functions could carry
  an obligation at 1.5. It is false, and `VERIFICATION.md` §4's own P-2 example
  is `requires … never fails` — the shape the claim forbade.
- **`#[derive(Eq)]` and `#[derive(Ord)]` on a payload enum WORK, and read every
  payload field** — measured here at the re-pin, 2026-09-04 (**RX-125**). This is
  the reverse of what cycles 0.0.0–0.0.2 recorded: at pin `950bb1d` the `Eq`
  derive was refused `NITPICK-TYPE-034` and the `Ord` derive compared **tags
  only**, so `Repeat(2,5).cmp(Repeat(9,9))` answered `Equal`. That was registry
  **O-N10** and it is **DISCHARGED**. `Repeat(2,5) < Repeat(2,9)` now, so the
  second payload field breaks the tie.
  **But `.eq()` returns `Result<bool>` and `.cmp()` returns `Result<Ordering>`** —
  `if (a.eq(b))` is `NITPICK-TYPE-007`, "there is no truthiness in Nitpick".
  Unwrap with `?! E`. So replacing a hand-written comparison with a derive
  threads an error channel and charges `SAFETY.md` §4's budget; it is a cycle 0.2
  decision, not a free deletion.
- **Measure `#size_of`, never derive it.** `Inst` is 12, `Match` is 16,
  `ByteSet` is 32, `string` is 24.
  **`HirNode` is NOT on that list, and the reason is the rule itself.** The
  measured 24 belongs to the **payload spelling** of `HirKind` — the shape
  `HIR.md` H-2 examined and **declined** — not to the specified `HirNode`, which
  is a tag plus three `int32`s plus a `uint32` and does not exist in `src/` until
  cycle 0.2. Quoting 24 for it would be attributing a measurement of the rejected
  alternative to the accepted one, in the same sentence that says to measure.
  Its size is **unmeasured**; measure it when it is written, and make the probe's
  exit code be `#size_of` so the number cannot be transcribed wrongly (RX-135).
- **`npkc`'s exit codes are an alphabet, and `2` is not a refusal.** `0`
  success; `1` **refused, with diagnostics**; `2` the driver **could not proceed
  and judged nothing**, silently, with an empty stderr; `3` a trap. A test
  expecting 1 that receives 2 was never compiled and proved nothing. Assert the
  specific integer, never `!= 0`. `tests/conformance/TRANSCRIPT.txt` §F and §G.
- **A missing import exits `1` with `NITPICK-RESOLVE-005` — the very code a
  rejection fixture expects.** So a rejection test whose path is typo'd or later
  moved passes for the wrong reason, and only B-7's code-set equality tells the
  two refusals apart. Every import here is relative until O-G3 closes, so this
  is the ordinary case, not the exotic one.
- **`check_no_syscalls` needs two layers, and the reason changed under it —
  which is the more useful half** (RX-120, amended by RX-131). At `950bb1d` the
  undefined-symbol difference **could not see a syscall at all**: a program with
  `sys(…)` had the *same* 29 symbols as one without, because `npk_sys6` was
  already the prelude's. At **`3d15ac9` it can** — D-262 emits a prelude item
  only when referenced, so the floor is **2** symbols, a syscaller **3**, and
  the difference is exactly `npk_sys6` (at **`c3bdae2`** the floor is **5** and a
  syscaller **6** — `__morestack` and `failsafe`'s own `npk_trap` and
  `npk_chain_reset` joined the floor — and the difference is still exactly
  `npk_sys6`; RX-148). Both pins are run back to back in
  `harness/baseline/RX120.txt`. **The second layer is not retired**: a symbol
  set reports *that* a kernel symbol is needed and never *where* it is called
  from, and a prelude that emits `npk_sys6` again blinds the first layer once
  more. **The moral is the durable part — that measurement was recorded as a
  permanent property and was a property of one compiler commit.**
- **At compiler `c3bdae2` (cycle 0.0.4b) a program owes more before it has done
  anything, and every loop states why it ends.** Every `failsafe` owes **six**
  identities — `StackExhausted` (D-305: every function's stack is checked) and
  `MachineFault` (D-307: the four fault signals reach `failsafe`) join the four.
  **Every `while` states `decreases E` or `unbounded`** (D-304) — 61 loops
  at the adoption, the reading in `meta/roadmap/done/0.0/decreases_read.txt`
  (RX-150), 81 at the fourth triage and 86 after cycle 0.0.4d, none `unbounded` (a count, dated: this
  said 61 until the fourth audit found 79, N-23; the compiler enforces the clause) — and a measured loop reachable from a consumer charges it
  `DecreasesViolated`: the **fourth** kind of charge `SAFETY.md` §4.2 counts.
  **A computed shift charges
  `ShiftRange`**, the fifth (`byteset.npk`). Arms are 106, 107, 108 and 115 here,
  the ecosystem's cross-stream codes; `LimitViolated` is 109 and the contracts
  116 and 117 (RX-149). A `core` consumer's bill went 6 → 9 or 10, measured the
  way `meta/OPEN_QUESTIONS.md` O-B3 says to — and 10 or 11 since cycle 0.0.4c,
  whose `ListLen` on the containers' counts adds `LimitViolated` (S-24a).
- **At compiler `c970483` (cycle 0.0.4e) the language refuses more, and misses one
  thing it should refuse.** A write through a loan is `NITPICK-TYPE-085` and a generic
  body's pass-out of a lent `T` is `NITPICK-TYPE-047` (RX-169); a `T` PLACE passed out
  of a lent or pointed-to container is `TYPE-047` too, at every `T`, which is why
  `vec_get` takes `T: Pod` and `vec_pop` spells `move(...)` (RX-168). A function that
  can reach its closing brace is `NITPICK-FLOW-001`, `NIL` functions included —
  **none in this tree did**: the compiler's own sweep of every file, where a file the
  type checker refuses is not flow-checked (measured), and the refused files' bodies
  read. A keyword cannot be a declared name (`NITPICK-PARSE-001`) and `main` is
  exactly `int32(cstring[]:argv)` (`NITPICK-TYPE-083`) — none here either. A block
  string closes at `"""` (DEF-98, RX-170). **What it should refuse and does not:** an
  impl that declares `move` on a parameter its trait lends compiles, and a call
  through the trait then double-frees — `tests/probe/probe18_impl_adds_move.npk`,
  the workbench registry's O-N28.
- **A sealed field is read anywhere and written only by its own module; a
  hidden one is not even read outside it** (the compiler's D-313 and D-314,
  measured here at `c3bdae2`, cycle 0.0.4c, RX-153). `Vec.items` is hidden and
  every other field of `Vec`, `Bytes` and `SparseSet` sealed, so outside its
  module a write is `NITPICK-TYPE-079`, a read of `items` `NITPICK-TYPE-080` —
  **and `@s.dense` is a write too**, even for a callee that only reads, so read
  `SparseSet`'s arrays by value (`vec_get(s.sparse, k)`). What neither closes:
  a write THROUGH a sealed pointer (`b.buf.ptr[0i64] = x` compiles) and a
  whole-`Vec` copy, which is a second handle on the block (a use-after-free
  after `vec_free`, exit 170) — and so is a whole-`SparseSet` copy, which after
  the free reports a member ABSENT with no trap, and a by-value `Vec` parameter.
  **The copy is DEFERRED TO 0.0.4d, before cycle 0.0 closes, by the author's
  decision on the board's question 9: `Vec` becomes move-only by construction**
  (RX-160; `tests/unit/*_alias_*.npk` pin today's behaviour). A limited field is written
  `sealed limit<ListLen> int64:f`; the other order is `NITPICK-PARSE-001`.
  *(Since cycle 0.0.4d both are closed: `buf` is `hidden` too — read the capacity with
  `bytes_capacity` (RX-163) — and a `Vec` copy is `TYPE-046` (RX-161). What stays open is
  a LOAN: a by-value parameter is lent, not copied, and a callee that writes through its
  address frees or grows its caller's block — a compiler defect, raised (RX-162;
  `tests/unit/*_alias_param_*.npk`, `tests/probe/probe17_lent_field_drop.npk`) — the
  registry's O-N21, the compiler's DEF-102, refused `NITPICK-TYPE-085` from its 1.6.0
  step 3g, not in `c3bdae2`. A `for` binding is the same loan, and a generic identity is
  a second owner (O-N22, DEF-104): RX-167, `tests/unit/vec_alias_for_binding_free.npk`
  and `vec_alias_generic_passout.npk`.)*
  *(Since cycle 0.0.4e, compiler `c970483`, none of that stays open: the loan is
  `NITPICK-TYPE-085` and the generic pass-out `NITPICK-TYPE-047`, and each file named
  above is a refusal in `tests/rejection/` or `tests/probe/refused/` — RX-169.)*
- **An exit status is one byte.** `exit 321` reports 65, silently. Compose
  weights that cannot sum past 255, or print the value and assert on stdout.
- **`&{…}` interpolates only inside a backtick template.** `"&{k}"` in double
  quotes is the four characters `&{k}`, measured at `c3bdae2`; `` `&{k}` `` is the
  number. `vec_owning_freed.npk` and `vec_owning_leak.npk` build their tags the
  first way, which is harmless there — the pair measures bytes, not content — and
  is why no program here has ever referenced `npk_int_to_string` (RX-131).

## Building and testing

**`npkg` cannot build this yet** (`meta/specs/BUILD.md` §1, O-G3): it is the
compiler's own bootstrap ladder, and `[dependencies]` resolves to nothing.
`harness/run.py` is the runner until that changes (RX-004), and **since cycle
0.0.2 it is real**:

```
NPKC=… NPKRT=… python3 harness/run.py
```

builds every declared suite with the pinned `npkc`, and every PROGRAM it also
assembles, scans, links closed-world, runs and judges by exit code — every
`program`-stage file twice, at −O0 and through `opt -O2`; the sweep, the refusals
and the rejection fixtures are judged by `npkc` alone and neither link nor run.
Every reading of source it makes goes through `harness/lexical.py`, which opens each
`.npk` file as BYTES — `\n` the only line end — and mirrors the compiler's lexer, a
`use` path being the literal's decoded value (RX-157, RX-165); and the program suites'
"imported by a sibling" skip asks `npkc` itself whether a file defines `main`, so its
two defences share no reader. It reads `nitpick.toml` for every path and every
flag and hardcodes none. **Since 0.0.3 it also sweeps every `.npk` in the tree with the `parse`
stage, judges `tests/rejection/` at the `check` stage, runs the tree checks (the count is
the one stated at the top of this file), and
— the one that matters — **runs the self-check FIRST** (`TESTING.md` V-21): every live
case feeds it a wrong expectation and requires a red, and the pending ones print as
PENDING on stages that do not exist until 0.3, 0.5 and 0.8 — the runner prints how
many of each, from `harness/selfcheck.py`'s own list. Three of its cases are the
`pending-until:` marker's reds, because a marker takes a unit out of the denominator
and must name the exit it excuses and a line in `harness/baseline/PENDING.txt`
(RX-154). `harness/README.md` states the boundary. CI (`.github/workflows/ci.yml`) pins the
compiler by full commit sha and LLVM by exact patch release, and **asserts**
both rather than reporting them.

The compiler binary is the **pinned toolchain** the board names
(`../BOARD.md`, W-18): `$NPKC` and `$NPKRT` are supplied to every session by the
orchestrator, or set by hand from `../.internal/toolchain/<commit>/`. Never build the
compiler from here and never read its `build/` directly — the guard refuses
the first, and the second is rebuilt under you. LLVM 20.1.2 exactly, pinned;
`llvm-config --version` to check.

## Where things go

```
src/       the library, Nitpick only, layered per meta/specs/BUILD.md §6
tests/     probe, conformance, unit, oracle, rejection, fixtures
harness/   the Python build and test runner, until npkg can
tools/     generators — the Unicode tables, the corpus fetcher, the fuzzers
examples/  runnable demonstrations, built and run by the harness
docs/      user-facing documentation, written at cycle 1.0
meta/      specs, decisions, open questions, the roadmap, research
.internal/ gitignored scratch — never commit anything from here
```

## When you find something

- A **compiler defect**: record the reproduction, stop, raise it. Do not work
  around it.
- A **specification error**: fix the specification and record the decision, in
  the same commit as the code that revealed it.
- A **finding that is neither**: write it into the current subcycle's execution
  record. This project's execution records are load-bearing; the compiler's
  cross-cycle patterns exist only because one writer kept them.

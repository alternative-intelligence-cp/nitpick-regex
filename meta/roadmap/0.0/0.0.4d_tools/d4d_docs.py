#!/usr/bin/env python3
"""0.0.4d step 7 -- the decisions, the question, and the prose the change makes false
or makes stronger. Run: python3 d4d_docs.py "$REPO".

The same engine as d4d_src.py: every edit an exact (old, new) pair; `new` present
once is ALREADY; else `old` present once is EDIT; else STOP -- and a single STOP
writes NOTHING. `@@DATE@@` is today's date, and a re-run on a later day still
recognises its own edits. Line wrapping in the texts below keeps every
`supersedes` at the END of a line, so this file, quoted inside the plan, never
reads to `check_refs` as a supersession before the markers exist.
"""
import datetime, os, re, sys

ROOT = sys.argv[1]
DATE = datetime.date.today().isoformat()
E = {}

# ============================================================ meta/DECISIONS.md
E["meta/DECISIONS.md"] = [
("""### RX-160 — N-15's premise was false and its reach was wider; the author has decided it: `Vec` becomes MOVE-ONLY BY CONSTRUCTION at 0.0.4d, before cycle 0.0 closes
""",
"""### RX-160 — N-15's premise was false and its reach was wider; the author has decided it: `Vec` becomes MOVE-ONLY BY CONSTRUCTION at 0.0.4d, before cycle 0.0 closes
> **SUPERSEDED IN PART by RX-161 and RX-162 (@@DATE@@)** — its hand-off's count, *"seven units that must STOP
> COMPILING"* and the swap beside them (the tree held seven `*_alias_*` units in all: six defect shapes and the
> swap), and its consequence that move-only *"changes `vec_get`'s signature and every by-value read in
> `src/core/`"* — measured false. Five of the six stop compiling; the sixth is a loan. The corrections and the
> reach stand.
"""),
("""### RX-153 — `Vec`, `Bytes` and `SparseSet` carry the compiler's field qualifiers, and the containers' four counts are limited by the prelude's `ListLen`
""",
"""### RX-153 — `Vec`, `Bytes` and `SparseSet` carry the compiler's field qualifiers, and the containers' four counts are limited by the prelude's `ListLen`
> **SUPERSEDED IN PART by RX-163 (@@DATE@@)** — `Bytes.buf` among the `sealed` fields: it is `hidden`, and the
> capacity is read through `bytes_capacity`. Every other qualifier, and `ListLen` on the counts, stands.
"""),
("""*Not decided here:* the shape of move-only — an owning field behind `items`, a
marker the compiler treats as owning, or another — which is 0.0.4d's plan's to
measure and choose.
""",
"""*Not decided here:* the shape of move-only — an owning field behind `items`, a
marker the compiler treats as owning, or another — which is 0.0.4d's plan's to
measure and choose.

---

## `Vec` move-only by construction — cycle 0.0.4d

*Appended @@DATE@@ by stream 1, working `meta/roadmap/0.0/0.0.4d.md` at pinned
toolchain `c3bdae2` under LLVM 20.1.2. Drafted at planning as PD-8 … PD-11; every
number below was measured at `c3bdae2`, at −O0 and through `opt -O2`.*

### RX-161 — `Vec` is MOVE-ONLY BY CONSTRUCTION: a hidden zero-length array of an owning type makes the compiler treat it as an owner, and the five COPY shapes stop compiling

**@@DATE@@, cycle 0.0.4d (the plan's PD-8) — the author's decision on the board's
question 9 (2026-09-25 15:45), whose shape RX-160 left to this plan.** It supersedes
RX-160 in part: its count — *"seven units that must STOP COMPILING"* and the
swap beside them, eight, where the tree held seven `*_alias_*` units in all, six
defect shapes and one control — and, with RX-162, its consequence for
`vec_get`.

**The shape.** `struct:Vec<T>` ends in `hidden string[0]:move_only`, filled with
`[]` (the compiler's D-139, the zero array) by `vec_init` and `vec_init_zeroed`.
`type_drops_recorded` answers an array by its element whatever the length, and
layout marks a struct owning when any field is (D-183) — so `Vec<T>` owns at
every `T`, and an owner is move-only (TYPE-046). `SparseSet`, and any struct
holding a `Vec`, owns by containment. **It costs nothing measurable:**
`#size_of<Vec<int64>>()` stays 24 and `SparseSet` 56; the generated drop walks no
elements and frees nothing, so the block stays `wild`, `vec_free` is still its
release, and a `Vec` never freed still traps `WildLeak` at `exit 0` (96); no
module's `failsafe` bill moves (10, 10, 10, 10, 6, 11, 6, 6, 6).

**Measured.** The five copy shapes — `vec_alias_double_free`,
`vec_alias_read_after_free`, `vec_alias_struct_copy`,
`sparseset_alias_double_free`, `sparseset_alias_read_after_free` — are each
refused `NITPICK-TYPE-046`, exactly once, and move to `tests/rejection/`.
`sparseset_alias_swap`, spelled with `move(...)` as three locals and as two
fields of a struct through a pointer flipped a thousand times, runs 0.
`vec_moves` — a whole-`Vec` move, a struct holding one moved, loans, and
`ENGINES.md` R-8's element-by-element copy — runs 0. **Two controls, each a case
the wrong implementation gets wrong:** against the tree before this decision the
five fixtures compile cleanly; and with the marker's element made `int64`, which
owns nothing, they compile cleanly again — the ELEMENT's ownership is the
mechanism, not the zero-length array. `probe16` and `probe16b` record the
language fact the marker rests on, so a compiler that changes it is named by a
probe before five fixtures fail at once.

*Alternatives declined, each measured at `c3bdae2`:* **a `string` marker**
(`hidden string:move_only`, filled `""`, whose drop frees nothing) — identical
verdicts on every file, and `Vec` 48 bytes, `SparseSet` 104; it is the fallback
if a later compiler refuses a zero-length array or stops counting its element,
which probe 16 would show first; **a `buffer` marker** (`buffer_new(0i64)`) —
identical verdicts, 48 bytes, and a runtime call in every constructor:
`npk_buffer_new` joins the undefined symbols of every `Vec` program; **a
`string?` marker** (`NIL`) — identical, 56 bytes; **an `OwnedFd` marker** —
4 bytes, and its drop is a `close`, a syscall path under every `Vec` in a library
whose rule is no syscalls (RX-008); **the block itself in a managed `buffer`**,
an owning field behind `items` — move-only too, but the drop would free the
block, `vec_free` would be redundant, D-151's gate would stop covering `Vec`
(S-22), every element access would be cast off a `uint8->` with `=>!`, and a loan
would still reach it (RX-162): a redesign of this cycle's deliverable; **the
prelude's `List<T>` as the backing store** — owning and move-only by D-247, and
declined on 2026-09-19 when the container question was answered (keep our `Vec`,
give it the properties) on the cost of rewriting every call site in two
libraries; **a language marker for move-only** — there is none at `c3bdae2`
(only a field's type makes a struct own); **a harness check refusing a `Vec`
copy in `src/`** — a house rule where the compiler can refuse, blind to every
consumer; **accept and document** — the author declined it on question 9.

### RX-162 — a by-value parameter is a LOAN, not a copy: `vec_get` keeps its signature, and what a loan still reaches is a compiler defect, pinned and raised, not worked around

**@@DATE@@, cycle 0.0.4d (the plan's PD-9).** It supersedes
RX-160 in part — its placing of `vec_alias_param_free` among the shapes that
*"must STOP COMPILING"*, and its consequence that move-only changes `vec_get`'s
signature and every by-value read in `src/core/`.

**Measured.** An ordinary parameter is LENT — the compiler's D-065 and D-183,
*"passing transfers nothing"* — and `move` of one is `NITPICK-TYPE-047`. So a
move-only `Vec`, `SparseSet` or `Bytes` passes to a by-value parameter without
`move`, and (1) `vec_get<T>(Vec<T>:v, i)` and every by-value read in
`src/core/` compile unchanged: the fourth audit's expectation was false. (2) The
loan is still a second handle, because the callee may take its own parameter's
address and write through it: `vec_alias_param_free` still compiles and the
caller reads the free poison (0); a callee's growth leaves the caller's own
`vec_free` a double free the guard cannot see (`vec_alias_param_grow`, 95); a
callee's `sset_free` makes the caller read a member ABSENT while `sset_len` says
1 (`sparseset_alias_param_free`, 0) — each the same with the marker and without.
(3) For an owning FIELD the compiler drops the caller's value on the write —
`probe17_lent_field_drop`, no library code, reads the poison (70; returned
normally instead, the caller's drop is a double free, 95) — which is how a
`Bytes`, move-only all along, dies when lent to a callee that grows it
(`bytes_alias_param_grow`, 95). The controls: the same write on a `move`
parameter and on a local run clean. The mechanism, read at `c3bdae2`: D-186's
unconditional field drop reasons that *"the struct's owner is exactly who is
overwriting it"* (`src/backend/ir/ir_stmt.npk`), and a lent parameter's callee
is not its owner.

**The decision.** `vec_get` keeps `Vec<T>:v`: a loan is the language's read-only
convention, it lets a consumer read a sealed field without taking the address
D-313 counts as a write, and nothing in `vec_get` writes through `v`. The four
loan units and probe 17 pin today's behaviour — PINNED, NOT ENDORSED — and each
says what to do when it reddens. The defect is raised as the workbench registry's O-N21, and nothing in
`src/` works around it: every function that changes a container already takes
it by pointer. **The cycle 0.0 gate's "every alias shape refused" is met for the
five COPY shapes and cannot be met at `c3bdae2` for a loan**; whether the close
waits for the compiler's fix is the author's, asked at 0.0.4d's planning.

*Alternatives declined:* **`vec_get` by pointer** (`Vec<T>->`) — a consumer's
`vec_get(@s.sparse, k)` is then `NITPICK-TYPE-079`, since a sealed field's address
is a write, so `SparseSet` would need new accessors, and it would close nothing:
a consumer's own by-value parameter is still a loan; **consuming verbs** — a
`vec_free(move Vec<T>:v)` and growth paths that take and return the `Vec`, which
would make a callee's free and growth through a loan `TYPE-047` — reshaping the
whole API around a compiler defect (W-11), at a copy in and out on every call in
the Pike VM's inner loop, and not reaching (3), which needs no library verb;
**documentation alone** — the loan units are the documentation that runs.

### RX-163 — `Bytes.buf` is `hidden`, and the capacity is read through `bytes_capacity`

**@@DATE@@, cycle 0.0.4d (the plan's PD-10) — the author's answer to question 9
let it ride with this subcycle where judged cheaper, and it is.** It supersedes
RX-153 in part: `buf` among the `sealed` fields. RX-153's other qualifiers,
and `ListLen` on the counts, stand.

A sealed field admits a write THROUGH its pointer: a consumer's
`b.buf.ptr[0i64] = 65u8;` compiled and ran at `c3bdae2`, and `bytes_get` then read
65. `hidden` refuses the member access itself (D-314):
`tests/rejection/bytes_buf_ptr_write.npk`, `NITPICK-TYPE-080`, which compiles
cleanly against the tree before this decision. The capacity the tests read as
`b.buf.len` — **nine** code lines in three files at `acaf99c` (cycle 0.0.4c
counted eight, before its own `sealed_reads.npk` added the ninth; the author's
answer carried the eight) — is `bytes_capacity(@b)`. Nothing in `src/` outside
`bytes.npk` reads `buf`. S-23's `Bytes` half is the compiler's for a consumer, as
`Vec`'s has been since 0.0.4c, and `check_accessor_confinement` stays for the
owning files.

*Alternatives declined:* **its own subcycle after the close** (the board's first
recommendation) — nine test lines and one accessor, beside the prose sweep this
subcycle runs anyway, and `nitpick-time` ports both at once; **`buf` sealed, as
0.0.4c left it** — a consumer corrupts the body with no diagnostic, the argument
that made `items` hidden.

### RX-164 — A′ replaces `VERIFICATION.md` P-1: an obligation is a comment unless a numbered decision accepts the arm its live clause costs every consumer; `prove` stays a comment until the verified build

**@@DATE@@, cycle 0.0.4d (the plan's PD-11) — the author's answer to Q-6,
2026-09-25 15:56: *"the recommendation on q-6 seems fine to me."*** It replaces
`VERIFICATION.md` P-1 with rule P-1b, and Q-6 is struck with this number.

P-1's argument — every construct it names refuses, so a premature clause is a
build failure — is false at `c3bdae2` (RX-152): `requires`, `ensures`,
`invariant` and `limit` are live and each adds one identity to every consumer's
`failsafe` (`probe13c`, `probe13d`, `probe13f`), and `prove` is accepted and
lowers to nothing in a plain build (`probe13a_prove_unchecked`). **The rule, P-1b:**
a `requires`, `ensures`, `invariant` or `limit` is written live only where a
numbered decision says the check earns the identity it adds to every consumer —
the containers' `ListLen` (S-24a, RX-153) is the one today; every other
obligation stays a comment in the syntax it would take, is evidence of nothing,
and is stood in for by a property test; `prove` stays a comment until the
harness runs the verified build (cycle 0.8), because a plain build drops it; and
`decreases`/`unbounded` are the language's and always live (D-304). Nothing in
`src/` changes: the obligation comments are what A′ keeps, and RX-130's trap
identity stands — a live `requires` on `vec_get` would trap 116 where the stop
traps 94 (`roadmap/0.0/0.0.4b.md` §10).

*Alternatives declined (Q-6's own list):* **A, live now** — every `core` consumer
owes `RequiresViolated` and `EnsuresViolated`, and the accessors' stop changes
identity, so RX-130 would need a successor; **B, every obligation a comment until
0.8, `assert_static` included** — nothing checks a comment; **C, everything live,
`prove` included** — a plain build lowers `prove` to nothing, the silent no-op P-1
was written against.
"""),
]

# ========================================================= meta/OPEN_QUESTIONS.md
E["meta/OPEN_QUESTIONS.md"] = [
("""### Q-6 — what replaces `VERIFICATION.md` P-1, now that every construct it names is live? — **the board's question for all six work repositories, cited here under its number there**
""",
"""### ~~Q-6 — what replaces `VERIFICATION.md` P-1, now that every construct it names is live?~~ — **SETTLED, RX-164** — the board's question for all six work repositories, cited here under its number there

**Answered by the author on 2026-09-25 at 15:56 — *"the recommendation on q-6 seems
fine to me"* — and recorded at cycle 0.0.4d: A′, as `VERIFICATION.md` rule P-1b.**
The question as it stood is kept below, because it is how the answer was reached.
"""),
]

# ====================================================== meta/specs/VERIFICATION.md
E["meta/specs/VERIFICATION.md"] = [
("""§6 name stay comments, per `../OPEN_QUESTIONS.md` Q-6 (its recommendation A′)
until the author answers it. And 1.5.8c's `decreases` is taken, on every loop
(P-8's note below).*
""",
"""§6 name stay comments, per `../OPEN_QUESTIONS.md` Q-6 (its recommendation A′)
until the author answers it. And 1.5.8c's `decreases` is taken, on every loop
(P-8's note below).*
*(Answered 2026-09-25 and recorded @@DATE@@, cycle 0.0.4d: A′ is rule P-1b below,
RX-164. The clauses stay comments.)*
"""),
("""**Rule P-1.** Until a construct is live, its obligation is stated **as a
comment beside the code in the exact syntax it will take**, and is enforced by""",
"""> **SUPERSEDED by rule P-1b (RX-164, @@DATE@@)** — its safety argument, that every
> construct it names refuses, is false at `c3bdae2`. Kept as written: how the
> error survived is part of the record.

**Rule P-1.** Until a construct is live, its obligation is stated **as a
comment beside the code in the exact syntax it will take**, and is enforced by"""),
("""nothing (`probe13a_prove_unchecked`). Until Q-6 is answered, no comment-form
obligation in `src/` becomes a live clause, and **no comment-form obligation is
evidence of anything** — it is checked by nothing, at any pin.*
""",
"""nothing (`probe13a_prove_unchecked`). Until Q-6 is answered, no comment-form
obligation in `src/` becomes a live clause, and **no comment-form obligation is
evidence of anything** — it is checked by nothing, at any pin.*

**Rule P-1b (RX-164, cycle 0.0.4d) — A′: an obligation is a comment unless a
numbered decision accepts the arm its live clause costs every consumer.** The
author's answer to `../OPEN_QUESTIONS.md` Q-6, 2026-09-25. A `requires`,
`ensures`, `invariant` or `limit` is written live only where a numbered decision
says the check earns the one `failsafe` identity it adds to every consuming
program — today that is the containers' `ListLen` alone (`SAFETY.md` S-24a,
RX-153). Every other obligation stays a comment in the syntax it would take, is
**evidence of nothing**, and is stood in for by a property test. `prove` stays a
comment until the harness runs the verified build (cycle 0.8), because a plain
build lowers it to nothing (`probe13a_prove_unchecked`). `decreases` and
`unbounded` are the language's and always live (P-8's note). And a live
`requires` is not written on an accessor whose body already stops: it would
pre-empt the stop and change its identity (RX-130 — 116 where the stop is 94,
measured at `c3bdae2`).
"""),
("""  author decided the remedy on the board's question 9: `Vec` becomes move-only by
  construction at 0.0.4d, before cycle 0.0 closes, which puts it inside this
  bullet's rule rather than beside it.)*
""",
"""  author decided the remedy on the board's question 9: `Vec` becomes move-only by
  construction at 0.0.4d, before cycle 0.0 closes, which puts it inside this
  bullet's rule rather than beside it.)*
  *(@@DATE@@, cycle 0.0.4d — RX-161, RX-162. It is inside it now: a copy of a
  `Vec`, a `SparseSet` or any struct holding one is refused. A BY-VALUE parameter
  is not: it is a loan, this rule does not see it, and a callee writing through
  its address still frees or grows the caller's block — a compiler defect,
  `SAFETY.md` S-23b.)*
"""),
]

# ============================================================ meta/specs/SAFETY.md
E["meta/specs/SAFETY.md"] = [
("""is a COPY of an owning place; where an owner is stored it does not govern. The
third cycle 0.0 audit's BL-5, RX-155.)*
""",
"""is a COPY of an owning place; where an owner is stored it does not govern. The
third cycle 0.0 audit's BL-5, RX-155.)*

*(Since cycle 0.0.4d a `Vec` is an owner itself — S-23b, RX-161 — so a copy of
one, or of any struct holding one, is refused like any owner's. A by-value
parameter is a loan, not a copy, and S-23b says what it still reaches.)*
"""),
("""uncommented: that is `../OPEN_QUESTIONS.md` Q-6's to decide, and until it is
the obligations stay comments.*
""",
"""uncommented: that is `../OPEN_QUESTIONS.md` Q-6's to decide, and until it is
the obligations stay comments.*
*(Q-6 was answered on 2026-09-25: A′ — `VERIFICATION.md` P-1b, RX-164. The
obligations stay comments; a live clause is a numbered decision that accepts its
arm.)*
"""),
("""  (`../../tests/rejection/bytes_copy.npk`). The pointer half — a write through
  `b.buf.ptr` — is question 9's other item and is not changed here.)*
""",
"""  (`../../tests/rejection/bytes_copy.npk`). The pointer half — a write through
  `b.buf.ptr` — is question 9's other item and is not changed here.)*
  *(@@DATE@@, cycle 0.0.4d — RX-161, RX-162, RX-163. Both of question 9's items
  are closed for a consumer: a copy of a `Vec`, a `SparseSet` or a struct holding
  one is `NITPICK-TYPE-046` (S-23b; the five copy fixtures in
  `../../tests/rejection/`), and `Bytes.buf` is `hidden`, so a write through
  `b.buf.ptr` is `NITPICK-TYPE-080` (`bytes_buf_ptr_write.npk`) — `Bytes`' half of
  this rule is the compiler's too. What stays open is a LOAN, which is not a
  copy: S-23b's last two rows.)*
"""),
("""  here would pre-empt this bullet's stop and change its identity; the clauses
  stay comments by `../OPEN_QUESTIONS.md` Q-6, which records the cost — RX-152.)*
""",
"""  here would pre-empt this bullet's stop and change its identity; the clauses
  stay comments by `../OPEN_QUESTIONS.md` Q-6, which records the cost — RX-152.)*
  *(Q-6 was answered on 2026-09-25 — A′, `VERIFICATION.md` P-1b, RX-164 — and
  under it this bullet's stop keeps its identity: no live `requires` is written
  where the body already stops.)*
"""),
("""  question 9: `Vec` becomes move-only by construction, and the guard's reach
  stops mattering because the second handle stops compiling.)*
""",
"""  question 9: `Vec` becomes move-only by construction, and the guard's reach
  stops mattering because the second handle stops compiling.)*
  *(@@DATE@@, cycle 0.0.4d — RX-162: for a COPY it does. A BY-VALUE parameter is
  a loan, still compiles, and carries the old `cap` into its callee, so the guard
  reaches one binding there as before — `vec_alias_param_grow.npk` is a double
  free it cannot see, 95.)*
"""),
("""---

## 6. Offsets, not slices
""",
"""### 5.3b What a `Vec` copy is, and what a loan still reaches

**Rule S-23b (RX-161, RX-162, cycle 0.0.4d) — `Vec` is move-only by
construction; a by-value parameter is a loan, and no type refuses it.**
`Vec<T>`'s last field is `hidden string[0]:move_only`: a fixed array of no
strings, which occupies no bytes and holds nothing, and whose element type owns —
so the compiler treats every `Vec<T>` as an owner (D-183's layout walk), and an
owner is move-only (TYPE-046). A struct holding a `Vec` owns by containment:
`SparseSet`, `COMPILE.md` C-1's `Program`, `SYNTAX.md` Y-9's parser state.

| written | at `c3bdae2`, since 0.0.4d |
|---|---|
| `Vec<T>:w = v;`, `SparseSet:t = s;`, a struct holding a `Vec` copied | `NITPICK-TYPE-046` — the five copy fixtures in `../../tests/rejection/` |
| `Vec<T>:w = move(v);`; a struct built by moving a `Vec` in, then moved | compiles and runs; `v` is invalid after (D-065) — `../../tests/unit/vec_moves.npk` |
| two `SparseSet`s swapped: three `move`s, of locals or of fields through a pointer | compiles and runs — `../../tests/unit/sparseset_alias_swap.npk`; `ENGINES.md` R-5 |
| a `Vec`'s content copied | element by element into a fresh `Vec`, which shares no block — `vec_moves.npk`; `ENGINES.md` R-8 |
| `f(v)`, where `f` takes `Vec<T>` by value | compiles WITHOUT `move`: the parameter is a LOAN (D-065, D-183), and `move` of it is `NITPICK-TYPE-047`. `vec_get` is one, and its signature is unchanged |
| a callee freeing or growing through its loan's address, `vec_free(@v)`, `vec_push(@v, x)` | **compiles, and the caller's header names a released block** — `vec_alias_param_free`, `vec_alias_param_grow`, `sparseset_alias_param_free` |
| a callee overwriting an owning field of a loan | **compiles, and drops the caller's value** — a double free with no `wild` block: `../../tests/probe/probe17_lent_field_drop.npk`, `bytes_alias_param_grow` |

The last two rows are a compiler defect — a loan is not held read-only — raised
and not worked around (W-11). Until it is fixed, a function that changes a
container takes it by pointer (`Vec<T>->`, `SparseSet->`, `Bytes->`), as every
function in `src/core/` does, and a by-value container parameter is for reading.
**The marker costs nothing measured:** `#size_of<Vec<int64>>()` is 24 as before;
the generated drop frees nothing, so the block stays `wild`, freed by `vec_free`,
and D-151 still traps one never freed (S-22 is unchanged); no consumer's bill
moves. The language fact it rests on is probe 16 and its refused twin; if a
later compiler refuses a zero-length array or stops counting its element's
ownership, the fallback is a `string` field holding `""` — measured identical on
every file, at 24 more bytes a `Vec`.

---

## 6. Offsets, not slices
"""),
]

# ========================================================= the other specifications
E["meta/specs/COMPILE.md"] = [
("""move-only too, and a copy of a `Program` is written element by element into fresh
`Vec`s. Cycle 0.6 builds `Program` against whatever 0.0.4d lands.)*
""",
"""move-only too, and a copy of a `Program` is written element by element into fresh
`Vec`s. Cycle 0.6 builds `Program` against whatever 0.0.4d lands.)*

*(Resolved @@DATE@@, cycle 0.0.4d — RX-161: `Vec` is move-only by construction,
so a `Program` is too, by containment. It is MOVED (`Program:q = move(p);`), lent
by value to a reader, and passed by pointer to anything that changes it; a binding
copy is `NITPICK-TYPE-046` (`../../tests/rejection/vec_alias_struct_copy.npk`).
"Copyable" keeps the meaning the flag above gives it — the CONTENT, copied element
by element into fresh `Vec`s (`../../tests/unit/vec_moves.npk`), and compared and
dumped the same way.)*
"""),
]
E["meta/specs/ENGINES.md"] = [
("""cycle 0.0 closes — a swap MOVES rather than copies, and 0.0.4d's design must keep
it writable; that unit is the control that shows it did.)*
""",
"""cycle 0.0 closes — a swap MOVES rather than copies, and 0.0.4d's design must keep
it writable; that unit is the control that shows it did.)*
*(@@DATE@@, cycle 0.0.4d — RX-161: a `SparseSet` is move-only, and the swap is
three `move`s — of two locals, or of two fields of the `Cache` through a pointer,
`SparseSet:t = move(c.cur); c.cur = move(c.nxt); c.nxt = move(t);` — both measured
at `c3bdae2`, the second a thousand times (`sparseset_alias_swap.npk`). A
`SparseSet[2]` indexed by a flipping `int64` also compiles and runs and moves
nothing; subcycle 0.7.0 chooses between them.)*
"""),
("""after 0.0.4d makes `Vec` move-only by the author's decision on question 9.)* A program with no `Save` instructions""",
 """after 0.0.4d makes `Vec` move-only by the author's decision on question 9.)* *(@@DATE@@, cycle 0.0.4d — RX-161: measured, the element-by-element copy into a fresh `Vec` keeps its values after the source is freed, so the two share no block, and a header copy is `NITPICK-TYPE-046` — `../../tests/unit/vec_moves.npk`.)* A program with no `Save` instructions"""),
]
E["meta/specs/SYNTAX.md"] = [
("""`NREGEX_NEST_DEPTH`; a pattern that exceeds it is `NestTooDeep` with the offset
of the parenthesis that did it.
""",
"""`NREGEX_NEST_DEPTH`; a pattern that exceeds it is `NestTooDeep` with the offset
of the parenthesis that did it.
*(@@DATE@@, cycle 0.0.4d — RX-161: the state that holds that `Vec<Frame>` is
move-only by containment — moved, lent by value to a reader, and passed by
pointer to anything that pushes or pops (`SAFETY.md` S-23b).)*
"""),
]
E["meta/specs/BUILD.md"] = [
("""`ByteSet` needs neither: it is a fixed array, so D-070's guard is emitted for it.*
""",
"""`ByteSet` needs neither: it is a fixed array, so D-070's guard is emitted for it.*

*Since cycle 0.0.4d (RX-161, RX-163) `Vec` carries a fourth field,
`hidden string[0]:move_only` — zero bytes, and it makes `Vec`, and everything
holding one, move-only (`SAFETY.md` S-23b) — and `Bytes.buf` is `hidden`, its
capacity read through `bytes_capacity`.*
"""),
]
E["meta/specs/TESTING.md"] = [
("""The check stays for both, and for the owning files' own use of their accessors* |""",
 """The check stays for both, and for the owning files' own use of their accessors. Since cycle 0.0.4d `Bytes`' half is the compiler's too: `buf` is `hidden` (RX-163)* |"""),
]

# ============================================================== the roadmap
E["meta/roadmap/0.1/0.1.0.md"] = [
("""own it by pointer (`@`/`->`). If 0.0.4d has not landed when this subcycle is
dispatched, that is a stop, not a start (W-23).
""",
"""own it by pointer (`@`/`->`). If 0.0.4d has not landed when this subcycle is
dispatched, that is a stop, not a start (W-23).
*(@@DATE@@ — 0.0.4d LANDED, and it did not change `vec_get`'s signature (RX-161,
RX-162): D6's `ast_get` wraps `vec_get` exactly as planned. A `Vec`, and any
struct holding one — the AST arena, the parser's state — is move-only: a copy is
`NITPICK-TYPE-046`, a transfer is `move(...)`. A by-value parameter is a LOAN and
compiles without `move`, so use one only to READ; a function that pushes, pops or
frees takes the container by pointer, because a callee that writes through a
loan's address frees or grows its caller's block — a compiler defect
(`SAFETY.md` S-23b; `../../../tests/unit/*_alias_param_*.npk`). The copy units
this paragraph names moved to `../../../tests/rejection/`.)*
"""),
]
E["meta/roadmap/0.1/0.1.0.md"].append((
"""S-24a. `Bytes`' half stays this library's: a sealed `buf` still admits a write
THROUGH `b.buf.ptr`.)*
""",
"""S-24a. `Bytes`' half stays this library's: a sealed `buf` still admits a write
THROUGH `b.buf.ptr`.)*
*(@@DATE@@, cycle 0.0.4d: `Bytes`' half is the compiler's too — `buf` is `hidden`
(RX-163), so `b.buf` outside `bytes.npk` is `NITPICK-TYPE-080`, and the capacity is
`bytes_capacity(@b)`. The tree check stays for the owning files.)*
"""))
E["meta/roadmap/0.7/README.md"] = [
("""  never by copying the header. Re-read 0.0.4d's record before planning either.
""",
"""  never by copying the header. Re-read 0.0.4d's record before planning either.
  *(@@DATE@@ — 0.0.4d landed (RX-161): the swap is three `move`s, measured as
  locals and as the `Cache`'s two fields through a pointer, and the element copy
  is measured too — `../../../tests/unit/sparseset_alias_swap.npk`,
  `../../../tests/unit/vec_moves.npk`; the copied-and-freed `SparseSet` above is a
  refusal now, `../../../tests/rejection/sparseset_alias_read_after_free.npk`. A
  thread set or a capture `Vec` handed BY VALUE is a loan a callee can still free
  through (RX-162): pass them by pointer.)*
"""),
]
E["meta/roadmap/ROADMAP.md"] = [
("""Next: 0.0.4d, `Vec` move-only by the author's decision, then a fifth audit** | — |""",
 """0.0.4d LANDED @@DATE@@: `Vec` move-only by the author's decision, a loan still a compiler defect. Next: a fifth audit** | — |"""),
("""> 0.0.4d, BEFORE cycle 0.0 closes** — so the next act is 0.0.4d's plan, and the
> fifth audit sees both.
""",
"""> 0.0.4d, BEFORE cycle 0.0 closes** — so the next act is 0.0.4d's plan, and the
> fifth audit sees both.
>
> **0.0.4d landed @@DATE@@** (`0.0/0.0.4d.md`), RX-161 … RX-164: the five copy
> shapes are refused, `Bytes.buf` is hidden and A′ replaces P-1; the LOAN is
> pinned against a compiler defect, and whether the close waits for its fix is the
> author's.
"""),
("""**52** unit programs, a self-check of **19** cases, 15 live, and decisions through
RX-160.)*
""",
"""**52** unit programs, a self-check of **19** cases, 15 live, and decisions through
RX-160.)*
*(After cycle 0.0.4d, the same compiler: **210** units — the five copy units moved
to the rejection suite, `bytes_buf_ptr_write`, three loan units and the positive
twin `vec_moves`, probes 16, 16b and 17, and the parse sweep's eight more files —
**31** probes, `src/core/` with **51** unit programs, and decisions through
RX-164.)*
"""),
]
E["meta/roadmap/0.0/README.md"] = [
("""# Cycle 0.0 — Foundations — **NOT CLOSED. The close was refused FOUR times — three on 2026-09-06, the fourth on 2026-09-25 — and it waits on 0.0.4d, the author's decision, and then a fifth audit.**
""",
"""# Cycle 0.0 — Foundations — **NOT CLOSED. The close was refused FOUR times — three on 2026-09-06, the fourth on 2026-09-25 — and it waits on 0.0.4d, the author's decision, and then a fifth audit.**

> ## 0.0.4d landed — `Vec` is move-only, and a loan is not a copy
>
> **[`0.0.4d.md`](0.0.4d.md), @@DATE@@.** The author's answer to the board's
> question 9 is in the tree: a hidden zero-length array of an owning type makes
> every `Vec` — and so every `SparseSet`, and every struct holding one — an owner,
> and the five COPY shapes the fourth audit measured are refused
> `NITPICK-TYPE-046` in `tests/rejection/` (RX-161). `Bytes.buf` is `hidden`
> (RX-163), and A′ replaces `VERIFICATION.md` P-1 (RX-164). **The sixth shape is
> not a copy**: a by-value parameter is a LOAN, a callee can still free or grow
> its caller's block through it, and for an owning field the compiler drops the
> caller's value — a compiler defect, pinned by four units and probe 17 and raised
> (RX-162). The gate below says what that leaves for the close.
"""),
("""close must have seen 0.0.4d's tree, in which every `tests/unit/*_alias_*` shape
is refused (RX-160).
""",
"""close must have seen 0.0.4d's tree, in which every `tests/unit/*_alias_*` shape
is refused (RX-160).

*(@@DATE@@, cycle 0.0.4d — RX-161, RX-162. "Every `*_alias_*` shape is refused"
was written before the shapes were measured against a move-only `Vec`, and it
counted the swap, which must run. Measured at `c3bdae2`: the five COPY shapes are
refused and live in `tests/rejection/`; the swap runs, spelled with `move(...)`;
and the shape through a BY-VALUE parameter is a LOAN, which no type refuses — it,
three more loan units and probe 17 pin a compiler defect that was raised. So the
clause is met for copies. For loans it is the author's call whether the close
waits for the compiler's fix and a re-pin, or proceeds with the loan open against
the defect (W-27) — asked at 0.0.4d's planning.)*
"""),
]

# ================================================================== CLAUDE.md
E["CLAUDE.md"] = [
("""**28** language probes with recorded verdicts, split **22 / 6** by kind (16 / 7,""",
 """**31** language probes with recorded verdicts, split **24 / 7** by kind (16 / 7,"""),
("""at the first `""` — found by the cycle 0.0 close's fourth triage, RX-157);
`tests/rejection/` holds eight consumer-facing refusals (five of them the
containers' seal, since 0.0.4c, and one a `Bytes` copy refused `TYPE-046`, since the
fourth triage); `harness/` builds, sweeps,""",
 """at the first `""` — found by the cycle 0.0 close's fourth triage, RX-157; then
24 / 7 when cycle 0.0.4d added probe 16 and its refused twin, the language fact
`Vec`'s move-only marker rests on, and probe 17, a compiler defect a lent
parameter shows — RX-161, RX-162);
`tests/rejection/` holds fourteen consumer-facing refusals (five of them the
containers' seal, since 0.0.4c; one a `Bytes` copy refused `TYPE-046`, since the
fourth triage; and since 0.0.4d five `Vec` and `SparseSet` copies refused
`TYPE-046` and a write through `Bytes.buf` refused `TYPE-080`); `harness/` builds, sweeps,"""),
("""with 52 unit programs of their own — eight of them measuring what each `Vec` verb does at an
owning element type, which `SAFETY.md` S-23a keeps out of `src/`, and seven pinning what a
copied `Vec` or `SparseSet` header aliases (N-15, deferred to 0.0.4d — RX-160). **No matching happens yet**: `src/syntax/`,""",
 """with 51 unit programs of their own — eight of them measuring what each `Vec` verb does at an
owning element type, which `SAFETY.md` S-23a keeps out of `src/`; four pinning what a LENT
`Vec`, `SparseSet` or `Bytes` still reaches, a compiler defect (RX-162); and the swap and the
moves a move-only `Vec` still allows (RX-161). **No matching happens yet**: `src/syntax/`,"""),
("""**194 units** (after the cycle 0.0 close's fourth audit triage; 174 after the third), plus eight tree checks; take those numbers from the runner's""",
 """**210 units** (after cycle 0.0.4d; 194 after the cycle 0.0 close's fourth audit triage, 174 after the third), plus eight tree checks; take those numbers from the runner's"""),
("""  element only when it can see that it owns nothing. This bullet said until the third cycle 0.0
  audit that the language forced it.
""",
"""  element only when it can see that it owns nothing. This bullet said until the third cycle 0.0
  audit that the language forced it.
  **And since cycle 0.0.4d a `Vec` IS itself an owner** — a hidden zero-length array of
  `string` makes it one — so a `Vec`, a `SparseSet` and any struct holding one are
  move-only: copy one and it is `TYPE-046`; transfer it with `move(...)`; lend it BY VALUE
  only to a function that reads it; hand it by POINTER to anything that changes it
  (`SAFETY.md` S-23b; RX-161, RX-162).
"""),
("""  So the comment-form obligations in `src/` are comments because
  `meta/OPEN_QUESTIONS.md` Q-6 is unanswered, not because anything refuses them,
  and a comment is evidence of nothing (`VERIFICATION.md` P-1, P-1a; RX-152).""",
 """  So the comment-form obligations in `src/` are comments by A′ — the answer to
  `meta/OPEN_QUESTIONS.md` Q-6, `VERIFICATION.md` P-1b (RX-164) — not because
  anything refuses them: a live clause is a numbered decision that accepts the arm
  it costs every consumer, and a comment is evidence of nothing (RX-152)."""),
("""  (RX-160; `tests/unit/*_alias_*.npk` pin today's behaviour). A limited field is written
  `sealed limit<ListLen> int64:f`; the other order is `NITPICK-PARSE-001`.""",
 """  (RX-160; `tests/unit/*_alias_*.npk` pin today's behaviour). A limited field is written
  `sealed limit<ListLen> int64:f`; the other order is `NITPICK-PARSE-001`.
  *(Since cycle 0.0.4d both are closed: `buf` is `hidden` too — read the capacity with
  `bytes_capacity` (RX-163) — and a `Vec` copy is `TYPE-046` (RX-161). What stays open is
  a LOAN: a by-value parameter is lent, not copied, and a callee that writes through its
  address frees or grows its caller's block — a compiler defect, raised (RX-162;
  `tests/unit/*_alias_param_*.npk`, `tests/probe/probe17_lent_field_drop.npk`).)*"""),
("""  (RX-150), and 81 at the fourth triage, none `unbounded` (a count, dated: this""",
 """  (RX-150), 81 at the fourth triage and 86 after cycle 0.0.4d, none `unbounded` (a count, dated: this"""),
]

# ======================================================== the test directories
E["tests/rejection/README.md"] = [
("""  those become fixtures here, refused the way this one is (RX-160).
""",
"""  those become fixtures here, refused the way this one is (RX-160).

## The copies refused, and the write through `buf` — cycle 0.0.4d

Since 0.0.4d `Vec` is move-only by construction (`../../meta/specs/SAFETY.md`
S-23b; `../../meta/DECISIONS.md` RX-161): its last field is a zero-length array of
an owning type, so the compiler treats every `Vec` — and every struct holding
one — as an owner, and a copy of one is `NITPICK-TYPE-046`. The five shapes the
fourth cycle-0.0 audit measured through a copy were units under `../unit/` until
then, each asserting the wrong answer the copy gave; they are refusals here now,
under the same names:

- **`vec_alias_double_free.npk`** — a `Vec` and its copy both freed: a double free, 95.
- **`vec_alias_read_after_free.npk`** — a read through the copy after the free returned the poison.
- **`vec_alias_struct_copy.npk`** — `COMPILE.md` C-1's `Program` in miniature, copied; the copy read the poison.
- **`sparseset_alias_double_free.npk`** — a `SparseSet` and its copy both freed: 95.
- **`sparseset_alias_read_after_free.npk`** — through the copy a member read ABSENT while the count said one.

And `buf` is `hidden` (RX-163):

- **`bytes_buf_ptr_write.npk`** — `NITPICK-TYPE-080`. A consumer's
  `b.buf.ptr[0i64] = 65u8;` wrote into the body through the sealed field until 0.0.4d.

**Each is a test of the marker or the qualifier and not of its file, and the
controls say so** (`../../meta/roadmap/0.0/0.0.4d.md` step 5): against the tree
before 0.0.4d all six compile cleanly, and the five copies compile cleanly again
with the marker's element made `int64`, which owns nothing. `../unit/vec_moves.npk`
and `../unit/sparseset_alias_swap.npk` are the positive twins — the moves, loans
and element-by-element copy a move-only `Vec` still allows, and the Pike VM's swap
spelled with `move(...)`.

**What this does not close is a LOAN.** A by-value parameter is lent, not copied,
so it compiles for a move-only `Vec`, and a callee that writes through its address
still frees or grows its caller's block — a compiler defect, pinned in `../unit/`
(`vec_alias_param_free`, `vec_alias_param_grow`, `sparseset_alias_param_free`,
`bytes_alias_param_grow`) and by `../probe/probe17_lent_field_drop.npk`, and raised
(RX-162). The day the compiler holds a loan read-only, those move here.
"""),
("""these fields. **What the seal does not close** is stated in S-23: a write
THROUGH `b.buf.ptr` still compiles from a consumer, and so does a whole-`Vec`
copy.
""",
"""these fields. **What the seal does not close** is stated in S-23: a write
THROUGH `b.buf.ptr` still compiles from a consumer, and so does a whole-`Vec`
copy. *(Both closed at 0.0.4d — RX-163 and RX-161, the section above.)*
"""),
("""All seven import `src/` by a **relative** path — the two `failsafe_*` fixtures
`../../src/lib.npk`, the seal's five the `../../src/core/` modules they seal —""",
 """All fourteen import `src/` by a **relative** path — the two `failsafe_*` fixtures
`../../src/lib.npk`, the other twelve the `../../src/core/` modules they test
(*"all seven" went stale when the fourth triage added `bytes_copy.npk`; corrected
at 0.0.4d*) —"""),
]
E["tests/probe/README.md"] = [
("""| `tests/probe/` | **22**, each `// expect-exit: N` |""",
 """| `tests/probe/` | **24**, each `// expect-exit: N` |"""),
("""| `tests/probe/refused/` | **6**, each `// expect-error: CODE` |""",
 """| `tests/probe/refused/` | **7**, each `// expect-error: CODE` |"""),
("""> **The split is 22 / 6, and 28 is the count of probes in this repository.** It
> was 16 / 7, then 17 / 6, then 19 / 6, then 22 / 5, and every move was a probe
> changing directory or name because the compiler changed its answer — not a probe
> being deleted, which P-5 forbids — until the last, which is a probe ADDED.
>
""",
"""> **The split is 24 / 7, and 31 is the count of probes in this repository.** It
> was 16 / 7, then 17 / 6, then 19 / 6, then 22 / 5, then 22 / 6, and every move
> was a probe changing directory or name because the compiler changed its answer —
> not a probe being deleted, which P-5 forbids — or a probe ADDED.
>
> **@@DATE@@, cycle 0.0.4d (RX-161, RX-162).** Three probes added.
> `probe16_zero_length_owner.npk` (exit 24) and
> `refused/probe16b_zero_length_owner_copy.npk` (`NITPICK-TYPE-046`) record the
> language fact `src/core/vec.npk`'s `move_only` field rests on: a zero-length
> array of an owning type holds nothing, occupies nothing, and makes its struct an
> owner, so a copy of it is refused — while the same shape over `int64[0]` copies
> freely. `probe17_lent_field_drop.npk` (exit 70) records a compiler defect:
> overwriting an owning field of a LENT parameter frees the caller's value. Each
> says what to do when it reddens.
>
"""),
]
E["nitpick.toml"] = [
("""# about USING THIS LIBRARY. Every fixture imports `src/` by a relative path
# (B-15) -- the two `failsafe_*` ones `src/lib.npk`, and the seal's five (since
# cycle 0.0.4c) the `src/core/` modules they seal -- which makes them the standing""",
 """# about USING THIS LIBRARY. Every fixture imports `src/` by a relative path
# (B-15) -- the two `failsafe_*` ones `src/lib.npk`, and the other twelve (the
# seal's five since cycle 0.0.4c, `bytes_copy` since the close's fourth triage,
# the five `Vec` and `SparseSet` copies and `bytes_buf_ptr_write` since 0.0.4d)
# the `src/core/` modules they test -- which makes them the standing"""),
]


def main():
    bad, out, edits, already = 0, {}, 0, 0
    for rel, pairs in E.items():
        path = os.path.join(ROOT, rel)
        s = open(path, encoding="utf-8").read()
        for n, (old, new) in enumerate(pairs, 1):
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
        print(f"d4d_docs: {bad} stop(s) -- NOTHING WRITTEN")
        return 1
    for path, s in out.items():
        open(path, "w", encoding="utf-8").write(s)
    print(f"d4d_docs: {edits} edited, {already} already, over {len(E)} files -- 0 stops")
    return 0


sys.exit(main())

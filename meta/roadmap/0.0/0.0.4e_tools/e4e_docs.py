r'''0.0.4e step 7 -- the decisions, the questions and the prose. Applied by
`python3 e4e_edit.py docs "$REPO"`, after steps 2 to 6; the engine's docstring says how.

What it writes, one line each (`0.0.4e.md` §5 maps PD -> RX):
  * `meta/DECISIONS.md` -- RX-168 (PD-12), RX-169 (PD-13), RX-170 (PD-14), and a
    `SUPERSEDED IN PART` line under RX-155, RX-157, RX-162, RX-165 and RX-167;
  * `meta/OPEN_QUESTIONS.md` -- O-N17 struck in favour of the registry's O-N27,
    which gains its local entry; O-N21 and O-N22 struck as discharged; O-R3 opened;
    and, only when step 0 wrote a registry number for §6.1's defect, its entry;
  * `meta/specs/` -- SAFETY.md (§1, S-23, S-23a, S-23b), VERIFICATION.md,
    TESTING.md (V-20 case 18), BUILD.md (B-4d);
  * `CLAUDE.md`, `nitpick.toml`, the two test READMEs, the harness README's
    triage list, `meta/roadmap/0.1/0.1.0.md`, this cycle's README and `ROADMAP.md`.
Each decision spells "supersedes" where it names what it replaces, and the
markers it needs are written in the same run, so `check_refs` is clean after it.
'''

EDITS = {}
IF_DEFECT_ID = {}

# =================================================================== meta/DECISIONS.md
_RX168 = r'''
### RX-168 — `vec_get` takes `T: Pod`, a trait an owning type cannot implement as it is declared, and `vec_pop` spells its move: DEF-104's gate reaches `src/`

**@@DATE@@, cycle 0.0.4e (the plan's PD-12), at compiler `c970483`.** It supersedes
RX-155 in part — its declined alternative *"a marker-trait bound (`vec_get<T:
Pod>`)"*, both of whose reasons are false at `c970483`; RX-162 in part —
*"`vec_get` keeps its signature"*: it keeps its parameter and gains a bound; and
RX-167 in part — its reach, *"Nothing in `src/` changes: no generic there takes a
lent bare `T`"*, true of a parameter and not the whole of DEF-104's.

**Measured: the tree as it stood does not compile at `c970483`.** `src/core/vec.npk`
is refused `NITPICK-TYPE-047` twice — `vec_get`'s `pass v.items[i]` (*"this
parameter was lent, not given"*) and `vec_pop`'s `pass v.items[v.count]` (*"`T` is
owned by what this pointer reaches"*) — and so is every file that imports it: the
harness ran `78/223`. The mechanism, read at `c970483` with `git show`: DEF-104
made `refuse_move_of_borrowed` and `refuse_pass_of_pointee_owned` ask
`type_owns_for_move`, which answers yes for a bare `T` (D-264), and a generic body
is checked once — so a `T` PLACE passed out of a lent or pointed-to container is
refused at every `T`, a scalar included. The fifth audit's N-25 and RX-167 looked
at a lent `T` PARAMETER, of which `src/` has none, and not at a `T` place rooted
in one; the audit's post-re-pin item 8 expected `vec_get` to compile.

**`vec_pop` spells the move**: `pass move(v.items[v.count]);` — the prelude's own
`list_pop`, and what the implicit move did: diffed at `c3bdae2`, `vec_pop<string>`
writes the same vacancy into the slot past `count`, plus one temporary and its
flag. Ownership-correct at every `T`, as RX-155 found it.

**`vec_get` takes `T: Pod`.** `pub trait:Pod = { func:pod_copy = Self(Self:self)
never fails; };` is declared in `vec.npk` and re-exported by `core.npk`; `vec_get`
reads `pass raw v.items[i].pod_copy();`; nine impls cover `int8` to `int64`,
`uint8` to `uint64` and `bool`, each `pass self`. **The language decides who may
implement it**: `pass self` of a lent owner is `NITPICK-TYPE-047`, so written as
the trait declares it, `impl:string:Pod`, `impl:Bytes:Pod`, `impl:SparseSet:Pod`,
`impl:Vec<int64>:Pod` and an impl for a struct holding a `string` are each refused
(measured). So `vec_get` at an owning `T` is `NITPICK-TYPE-017` — S-23a's `vec_get`
row, which a later cycle's `Vec<string>` could only break at a harness check over
`src/`, is the compiler's now, for every consumer.
`tests/unit/vec_owning_get_moves_out.npk` moves to `tests/rejection/` as that
refusal. Measured at `c970483`: all thirteen `src/` files compile; the nine bills
are unchanged (10, 10, 10, 10, 6, 11, 6, 6, 6) — `pod_copy` is `never fails` and
adds no identity; `#size_of<Vec<int64>>()` 24, `SparseSet` 56, `Bytes` 32; the
floor 5 / 6 / `{npk_sys6}`; and a consumer of `core.npk` implements `Pod` for its
own POD struct in one line and reads it back. The same `src/` compiles at
`c3bdae2`, so the design is not the pin's.

**The one hole, a compiler defect found at planning** (@@DEFECT@@): an impl may
declare `move` on a parameter its trait lends, the compiler accepts it, and a
call through the trait then hands the callee a value the caller still owns — a
double free, 95, with no library code (`tests/probe/probe18_impl_adds_move.npk`,
at `c970483` and `c3bdae2`), and through `vec_get` a consumer's `impl:string:Pod`
written that way returns a second owner of the element (95, measured). No impl
in this repository does it, `check_vec_elements_own_nothing` still refuses an
owning element in `src/`, and `TRAITS_REFERENCE.md` §2 already says an impl must
have the signature the trait declares. Probe 18 reddens when the compiler agrees.

*Alternatives declined:* **`.clone()` under the prelude's `Clone`** — the language's
own spelling for a copy of a `T` place (D-264), and the prelude declares `clone`
MAY FAIL, so in a `never fails` body it is `Result<T>`: `NITPICK-TYPE-007` as
written, `NITPICK-TYPE-042` under `raw` (both measured); `?!` would put a trap
identity in every consumer's bill and `relay` would make `vec_get` fallible and
every `raw vec_get` a `TYPE-042` — an error channel on the search path, against
S-4. **`vec_get(Vec<T>->:v, …)` with `pass move(v.items[i])`** — RX-162's first
declined alternative with a third cost: at an owning `T` the read empties the
slot, and every reader holding a lent `Vec` would need `@v`, which is
`NITPICK-TYPE-085` now. **A local `#wild_slice` over the lent header's `items`**
(`nitpick-time`'s `vec_at` shape, which compiles at `c970483` because its root is
a pointer) — for a LENT `Vec` it moves an owning element out of the caller's block
through the loan, which is what `TYPE-085` refuses when it is written directly:
the refusal routed around, not answered. **A getter per element type** — a verb
per type, where S-23a's question is the generic one. **`struct:Vec<T: Pod>`** —
S-23a at the type, for every verb and every consumer; it refuses the seven
owning-element measurement units and removes `vec_free_owning`'s reason to exist —
a redesign, not an adoption. It is O-R3, open with a recommendation. **Waiting for
a never-failing `Clone` from the compiler** — a language decision (a `string`'s
clone allocates), raised as a design input, `0.0.4e.md` §6.2, and not waited on.
**Another name** — `Copy` is a name a prelude may yet declare, and D-239 would then
refuse ours; `Pod` is RX-155's own word for what it asks.
'''

_RX169 = r'''
### RX-169 — the loan and the generic pass-out are REFUSED at `c970483`: the six pins and probe 17 move to their refusal homes, each shown to be the pin's, and the spellings the refusals prescribe run

**@@DATE@@, cycle 0.0.4e (the plan's PD-13), at compiler `c970483`.** It supersedes
RX-162 in part — *"PINNED, NOT ENDORSED"* and *"cannot be met at `c3bdae2` for a
loan"*: they are refused and the gate's loan clause is met — and RX-167 in part —
its two units' *"pinned, not endorsed"*. Their decisions on `vec_get`'s loan and on
not working around a defect stand.

**Measured at `c970483`**, each file through `npkc` alone and each refusal
exactly its code under B-7, at the position its own `expect-error-at` records: a
write through a lent container is `NITPICK-TYPE-085` (DEF-102) —
`vec_alias_param_free` and `vec_alias_param_grow` at their callee's `@v`,
`sparseset_alias_param_free` at `@s`, `bytes_alias_param_grow` at `@b`,
`vec_alias_for_binding_free` at `@x` (the fifth audit's N-26: the `for` binding
is a loan to 3g, as its parser reading predicted), and probe 17 at its field
write; the generic identity's `pass x` is `NITPICK-TYPE-047` (DEF-104). The six
units move to `tests/rejection/` and probe 17 to `tests/probe/refused/`, under
their names, their headers rewritten. **Each refusal is the pin's**: every one
still compiles and runs at `c3bdae2` with the exit it asserted as a unit — 0, 95,
0, 95, 0, 0, and 70 — at −O0 and through `opt -O2`.

**Two frees name their `T`.** Written `vec_free(@v)`, the refused argument leaves
`T` nothing to be inferred from and the compiler adds `NITPICK-TYPE-022` at the
same call; `vec_free::<int64>(@v)` leaves `TYPE-085` alone. The cascade is the
compiler's diagnostic recovery, not the loan, and B-7's equality would have made it
part of what the file asserts.

**The positive twin, `tests/unit/loan_spellings.npk`**, runs what the refusals
prescribe — a callee that frees takes `move Vec<int64>:v` and its caller writes
`move(a)`; one that grows takes `Vec<int64>->`; the same for a `SparseSet` and a
`Bytes`; a `for` loop reads its binding and the array frees its elements by index;
a generic that passes its argument on takes `move T:x` — each value checked, every
block freed once: exit 0 at both levels, at `c970483` and at `c3bdae2`. Without it
the refusals would also pass a compiler that refused every container parameter.

**Cycle 0.0's gate** — every loan shape refused at a pin carrying DEF-102 — **is
met**: the four `*_alias_param_*` fixtures, probe 17 and the `for` binding.

*Alternatives declined:* **keeping `TYPE-022` in the two expectation sets** — it
pins the compiler's recovery after an error, which may change without the loan
changing; **new names for the moved files** — RX-160, RX-162 and RX-167 find them
by name, 0.0.4d's precedent; **leaving them in `tests/unit/` behind a marker** — a
refusal is a `check`-stage fact, and the rejection suite is where B-7 holds it.
'''

_RX170 = r'''
### RX-170 — `harness/lexical.py` closes a block string at `"""`, as the compiler's lexer has since its 1.6.0 step 3e (DEF-98): probe 15 runs, and self-check case 18 reads the two closes apart in both directions

**@@DATE@@, cycle 0.0.4e (the plan's PD-14), at compiler `c970483`.** It supersedes
RX-157 in part — its paragraph that the lexer closes a block string at the first
`""` and `lexical.py` follows it — and RX-165 in part — item 4's case 18 *"read the
way the lexer at `c3bdae2` reads it"*. The one-reader rule, the lexer mirror, the
bytes, the decoded path and both defences stand.

**Measured.** `lexer_next` at `c970483` breaks a block string only when the
current byte and the next two are quotes (`lexer_peek3`), and a backslash still
skips the byte after it; the lexer's diff from `c3bdae2` is that alone,
`escapes.npk` is unchanged, and `parse_decl.npk`'s change is DEF-103's declared-name
check, which reads no import. Probe 15, `"""a""b"""`, compiles and exits 4 at −O0
and through `opt -O2` at `c970483` and is refused `LEX-005`, `PARSE-001`,
`PARSE-003` at `c3bdae2`; it moves out of `refused/` with `expect-exit: 4`.

**Case 18's line 23 is rewritten, not only re-expected.** It read `"""a""b use
"./in_block_pin.npk".*; """x""!;` and required its import, the old close's
reading. Merely flipping the expectation to "no import" would also pass a reader
that never closed a block string at all. It now reads `"""a""b use
"./in_block.npk".*; """; use "./after_block.npk".*;` and requires
`./after_block.npk` alone: the new close reads the `use` after the literal; the
old one reads the `use` inside it and opens a block that never closes. Both
readings were measured against the compilers, in a module holding that line: at
`c970483` the only import is `./after_block.npk` (`NITPICK-RESOLVE-005` naming it,
nothing naming the other), and at `c3bdae2` the compiler reads `./in_block.npk`
and reports the second block unterminated (`LEX-005`). `c3bdae2`'s close, restored
in a copy of `lexical.py`, reddens case 18 alone.

*Alternatives declined:* **keeping the old close** — the module's purpose is to
agree with the compiler, and it no longer would; **following the grammar and not
the lexer** — they agree now, and the day they part the lexer is still what reads
the files; **flipping line 23's expectation alone** — measured above as a case a
never-closing reader passes.
'''

EDITS["meta/DECISIONS.md"] = [
# the three decisions, after RX-167's last line
(r'''every consumer; **holding the close for N-25** — it is no clause of cycle 0.0's
gate and `src/` has no exposure; whether it should become one is the author's.
''',
r'''every consumer; **holding the close for N-25** — it is no clause of cycle 0.0's
gate and `src/` has no exposure; whether it should become one is the author's.
''' + _RX168 + _RX169 + _RX170),
# the markers
(r'''### RX-155 — `Vec<T>` is for a `T` that owns nothing, because nothing in the language keeps an owner out; the restriction is stated per verb, measured per verb, and enforced over `src/`
''',
r'''### RX-155 — `Vec<T>` is for a `T` that owns nothing, because nothing in the language keeps an owner out; the restriction is stated per verb, measured per verb, and enforced over `src/`
> **SUPERSEDED IN PART by RX-168 (@@DATE@@)** — its declined alternative, *"a marker-trait bound
> (`vec_get<T: Pod>`)"*: at `c970483` the old `vec_get` does not compile, and the language refuses an
> owning `Pod` impl written as declared, so the bound is taken. The rule, its check and its table stand.
'''),
(r'''### RX-157 — the harness reads Nitpick source ONE way, the compiler's, and a file that declares `main` is never skipped
''',
r'''### RX-157 — the harness reads Nitpick source ONE way, the compiler's, and a file that declares `main` is never skipped
> **SUPERSEDED IN PART by RX-170 (@@DATE@@)** — its paragraph that a block string closes at the first
> `""` and `lexical.py` follows that: the lexer closes at `"""` since the compiler's 1.6.0 step 3e.
'''),
(r'''### RX-162 — a by-value parameter is a LOAN, not a copy: `vec_get` keeps its signature, and what a loan still reaches is a compiler defect, pinned and raised, not worked around
''',
r'''### RX-162 — a by-value parameter is a LOAN, not a copy: `vec_get` keeps its signature, and what a loan still reaches is a compiler defect, pinned and raised, not worked around
> **SUPERSEDED IN PART by RX-168 and RX-169 (@@DATE@@)** — `vec_get` keeps its parameter and gains a
> bound, `T: Pod` (RX-168); and the loan is REFUSED at `c970483`, `NITPICK-TYPE-085`, so its pins are
> rejection fixtures and the gate's loan clause is met (RX-169). A loan is still a loan, and nothing was
> worked around.
'''),
(r'''### RX-165 — the harness opens every `.npk` as the compiler does, decodes an import path by the compiler's escape rules, and the skip's second defence is the compiler's own answer
''',
r'''### RX-165 — the harness opens every `.npk` as the compiler does, decodes an import path by the compiler's escape rules, and the skip's second defence is the compiler's own answer
> **SUPERSEDED IN PART by RX-170 (@@DATE@@)** — item 4's case 18 *"read the way the lexer at `c3bdae2`
> reads it"*: the block string closes at `"""` at `c970483`, and line 23 is rewritten to read the two
> closes apart. Everything else stands.
'''),
(r'''### RX-167 — two more shapes reach a move-only `Vec`'s block without a copy — a `for` binding, and a generic function passing out its lent `T` — each pinned as a unit and raised, not worked around
''',
r'''### RX-167 — two more shapes reach a move-only `Vec`'s block without a copy — a `for` binding, and a generic function passing out its lent `T` — each pinned as a unit and raised, not worked around
> **SUPERSEDED IN PART by RX-168 and RX-169 (@@DATE@@)** — both shapes are refused at `c970483`, and
> their units are rejection fixtures (RX-169); and "Nothing in `src/` changes" was true of a lent `T`
> PARAMETER and not the whole of DEF-104's reach — `vec_get` and `vec_pop` (RX-168).
'''),
]

# =============================================================== meta/OPEN_QUESTIONS.md
EDITS["meta/OPEN_QUESTIONS.md"] = [
# O-N17: struck in favour of the registry's O-N27
(r'''### O-N17 — **PROVISIONAL, awaiting the author's number**: the borrow tracker taints a function's return by SIGNATURE, so a function that takes a container by borrow cannot return an owned `string`
''',
r'''### ~~O-N17 — **PROVISIONAL, awaiting the author's number**: the borrow tracker taints a function's return by SIGNATURE, so a function that takes a container by borrow cannot return an owned `string`~~ — **RE-HOMED: it is the workbench registry's O-N27, the same finding, registered 2026-09-26** (the entry below)

*(@@DATE@@, cycle 0.0.4e: struck in favour of O-N27, as the registry directs. The
number collided and the finding was never filed under it; the orchestrator
registered it as O-N27 after `nitpick-time` measured it independently, and sent it
to the compiler as a design input to its S-106 (DEF-107's decision), where it is
recorded as S-107. **Re-measured here at `c3bdae2` and at `c970483`**: the
registry's reproduction — a `func:make = string(Box->:b)` returning
`string_concat("small", "!")`, called `pass raw make(@b);` from the frame owning
`b` — is `NITPICK-BORROW-001` at both. The heading and the text below are kept as
raised, so the four citations in `roadmap/0.0/0.0.5.md` §8 still resolve.)*
'''),
# O-N21's link to probe 17 follows the file to `refused/` -- live navigation is
# corrected, the text it sits in is kept as raised
(r'''[`probe17_lent_field_drop.npk`](../tests/probe/probe17_lent_field_drop.npk): the
''',
r'''[`probe17_lent_field_drop.npk`](../tests/probe/refused/probe17_lent_field_drop.npk): the
'''),
# O-N21 and O-N22: discharged
(r'''### O-N21 — **the workbench registry's**: a callee writing through a LENT parameter frees or grows its caller's value
''',
r'''### ~~O-N21 — **the workbench registry's**: a callee writing through a LENT parameter frees or grows its caller's value~~ — **DISCHARGED upstream: refused `NITPICK-TYPE-085` since the compiler's 1.6.0 step 3g (DEF-102), in our pin since `c970483`; RX-169**

*(@@DATE@@, cycle 0.0.4e: measured at `c970483`, every face refused exactly
`NITPICK-TYPE-085` at its write — the four units, the `for` binding and probe 17,
each now a refusal (`tests/rejection/`, `tests/probe/refused/`) and each still
running at `c3bdae2` with its old exit, so the refusal is the pin's. The text below
is kept as raised.)*
'''),
(r'''### O-N22 — **the workbench registry's**: `NITPICK-TYPE-047` is not asked of a lent `T` inside a generic body, so a generic function hands back its lent parameter as a second owner
''',
r'''### ~~O-N22 — **the workbench registry's**: `NITPICK-TYPE-047` is not asked of a lent `T` inside a generic body, so a generic function hands back its lent parameter as a second owner~~ — **DISCHARGED upstream: refused `NITPICK-TYPE-047` since the compiler's 1.6.0 step 3g (DEF-104), in our pin since `c970483`; RX-169 — and its reach here was wider than this entry said: RX-168**

*(@@DATE@@, cycle 0.0.4e: measured at `c970483`, `vec_alias_generic_passout` is
refused `NITPICK-TYPE-047` at its `pass` and runs at `c3bdae2`. "Nothing in `src/`,
where no generic takes a lent bare `T`" below was true of a PARAMETER and not the
whole of it: the fixed gate also refuses a `T` PLACE passed out of a lent or
pointed-to container, which was `vec_get` and `vec_pop` — the tree did not compile
at `c970483` until `vec_get` took `T: Pod` and `vec_pop` spelled `move(...)`
(RX-168). The workbench registry's entry states the same "none" and is corrected
there, not here.)*
'''),
# O-N27's local entry, before the O-G section
(r'''## O-G — the compiler's, raised from here
''',
r'''### O-N27 — **the workbench registry's**: the borrow tracker taints a call's result by SIGNATURE, so an owned string built by `f(Container->)` cannot be returned from the frame that owns the container

**Registered 2026-09-26 in the workbench registry (`../meta/OPEN_QUESTIONS.md`
§"For the compiler")**, from this repository's cycle 0.0 triage — filed here on
2026-09-06 under a local number, O-N17 above, that collided — and measured
independently by `nitpick-time`'s 0.1.4b. Sent to the compiler as a design input to
its S-106 (DEF-107's decision) and recorded there as S-107, with the recommendation
that 1.6.1 step 0's per-function summaries refine the marking. The registry's entry
is the authority; this one restates it so a citation from this tree resolves
without leaving it.

A function that takes a container by pointer and returns an owned `string` it
BUILT — which cannot alias its argument — is refused `NITPICK-BORROW-001` (*"a
borrow cannot travel up"*) when called from the frame owning the container, bound
first or not; with the container a parameter of the returning frame, or the string
built inline, it compiles and runs. Measured here at `c3bdae2` and at `c970483`
(cycle 0.0.4e): `BORROW-001` at both. **Sound and coarse** — a false reject, the
mirror of a view escaping, both from a rule keyed on a call's shape rather than a
value's provenance. *What it means here:* refused code, not unsafe code; this
library meets the shape at cycle 0.6, where replacement returns built text, and
O-N17's two working spellings stand. **What it blocks (W-27):** nothing today.

## O-G — the compiler's, raised from here
'''),
# O-R3, beside O-R2
(r'''  needs its own correctness argument. **Decide at cycle 0.8**, where the DFA's
  capture story is settled; `O-C2` is the compiler half.
''',
r'''  needs its own correctness argument. **Decide at cycle 0.8**, where the DFA's
  capture story is settled; `O-C2` is the compiler half.
- **O-R3 — `struct:Vec<T: Pod>`: S-23a stated at the type, not only at
  `vec_get`.** Since cycle 0.0.4e `vec_get` takes `T: Pod` (RX-168), which an owning
  type cannot implement as declared, so the one verb that hands an element back
  refuses an owning `T`. Bounding the TYPE would refuse `Vec<string>` itself — every
  verb, every consumer — and retire `check_vec_elements_own_nothing` into a belt;
  it would also refuse the seven owning-element measurement units and remove
  `vec_free_owning`'s reason to exist. **Recommendation: yes, at cycle 0.1's
  opening subcycle, once the compiler refuses an impl that declares `move` on a
  parameter its trait lends** (RX-168's hole, probe 18) — before that fix a
  `move`-self impl defeats a bound on the type exactly as it defeats `vec_get`'s,
  and the tree check stays the only guarantee over `src/`. **Open by design until
  then**: it is gated on a compiler fix, not on a decision here.
'''),
]
IF_DEFECT_ID["meta/OPEN_QUESTIONS.md"] = [
(r'''### O-N27 — **the workbench registry's**: the borrow tracker taints a call's result by SIGNATURE, so an owned string built by `f(Container->)` cannot be returned from the frame that owns the container
''',
r'''### @@DEFECT_ID@@ — **the workbench registry's**: an impl may declare `move` on a parameter its trait lends, and a call through the trait then hands the callee a value the caller still owns

**Raised by this repository's cycle 0.0.4e planning at compiler `c970483` and
filed in the workbench registry (`../meta/OPEN_QUESTIONS.md` §"For the compiler")**;
the registry's entry is the authority, and this one restates it so a citation from
this tree resolves without leaving it. `impl:string:Dup = { func:dup =
string(move string:self) never fails { pass self; }; };` compiles against `trait:Dup
= { func:dup = Self(Self:self) never fails; };`, and a call through the trait lends
its argument to a callee that takes ownership of it: two owners of one body, a
double free, 95, at −O0 and through `opt -O2`, at `c970483` and `c3bdae2` —
`../tests/probe/probe18_impl_adds_move.npk`, no library code. The same impl written
as declared is `NITPICK-TYPE-047`; a plain function with a `move` parameter called
without `move(...)` is `NITPICK-TYPE-046`; a prelude trait is no different
(`impl:Named:Eq` with `move Named:self` double-frees at `a.eq(b)`); and the reverse
mismatch, a trait's `move Self:self` implemented lent, also compiles.
`TRAITS_REFERENCE.md` §2: "An impl's method must have the signature the trait
declares". *What it means here:* `vec_get`'s `T: Pod` (RX-168) refuses an owning
type only through `Pod`'s declared, lent `self`; a consumer's `move`-self impl
defeats it (95 through `vec_get`, measured). **What it blocks (W-27):** nothing in
`src/`, which writes no such impl; O-R3 waits for it.

### O-N27 — **the workbench registry's**: the borrow tracker taints a call's result by SIGNATURE, so an owned string built by `f(Container->)` cannot be returned from the frame that owns the container
'''),
]

# ================================================================== meta/specs/SAFETY.md
EDITS["meta/specs/SAFETY.md"] = [
# §1's dated notes
(r'''*(Since cycle 0.0.4d a `Vec` is an owner itself — S-23b, RX-161 — so a copy of
one, or of any struct holding one, is refused like any owner's. A by-value
parameter is a loan, not a copy, and S-23b says what it still reaches.)*
''',
r'''*(Since cycle 0.0.4d a `Vec` is an owner itself — S-23b, RX-161 — so a copy of
one, or of any struct holding one, is refused like any owner's. A by-value
parameter is a loan, not a copy, and S-23b says what it still reaches.)*

*(Since cycle 0.0.4e, at compiler `c970483`: a loan is READ-ONLY — every write
through one is `NITPICK-TYPE-085`, and a generic body's pass-out of a lent `T` is
`NITPICK-TYPE-047` (S-23b, RX-169) — and `vec_get` takes `T: Pod`, so a by-value read
of an owning element out of a `Vec` is refused rather than a move (S-23a,
RX-168).)*
'''),
# S-23's bullet: what stays open
(r'''  this rule is the compiler's too. What stays open is a LOAN, which is not a
  copy: S-23b's last two rows.)*
''',
r'''  this rule is the compiler's too. What stays open is a LOAN, which is not a
  copy: S-23b's last two rows.)* *(Closed at `c970483`, cycle 0.0.4e: S-23b's
  rows say how — RX-169.)*
'''),
# the RX-156 bullet's 0.0.4d note names a loan unit
(r'''  reaches one binding there as before — `vec_alias_param_grow.npk` is a double
  free it cannot see, 95.)*
''',
r'''  reaches one binding there as before — `vec_alias_param_grow.npk` is a double
  free it cannot see, 95.)* *(Refused at `c970483`, cycle 0.0.4e: that file is a
  rejection fixture, `NITPICK-TYPE-085` — RX-169.)*
'''),
# S-23a: the amendment note
(r'''from a discriminant `= (…)`. And since RX-165 it reads each file as the compiler
does — bytes, `\n` the only line end — which is what a `// …<CR>/*` had defeated.)*
''',
r'''from a discriminant `= (…)`. And since RX-165 it reads each file as the compiler
does — bytes, `\n` the only line end — which is what a `// …<CR>/*` had defeated.)*
*(Amended @@DATE@@ by RX-168, cycle 0.0.4e: FOR `vec_get` THE COMPILER SAYS SO
TOO. At `c970483` the old `vec_get` does not compile at any `T`, and it takes
`T: Pod` — one `never fails` method returning its lent `self`, which an owning type
cannot implement as declared (`pass self` of a lent owner is `NITPICK-TYPE-047`). So
`vec_get` at an owning `T` is `NITPICK-TYPE-017` for every consumer, not a move. The
other verbs are unchanged, and the rule and its check stand for them — and for
`vec_get` too, as the belt: an impl that declares `move` on its `self` defeats the
bound, a compiler defect pinned by `tests/probe/probe18_impl_adds_move.npk`.)*
'''),
# S-23a's table: the vec_get row
(r'''| `vec_get` | **MOVES the element out**: the slot is emptied and still counted, so a second read is empty | `vec_owning_get_moves_out` |
''',
r'''| `vec_get` | **refused, `NITPICK-TYPE-017`, since cycle 0.0.4e**: it takes `T: Pod` (RX-168). Through `c3bdae2` it MOVED the element out — the slot emptied and still counted, so a second read was empty | `vec_owning_get_moves_out`, a rejection fixture since 0.0.4e |
'''),
# S-23b's table
(r'''| written | at `c3bdae2`, since 0.0.4d |
''',
r'''| written | at `c3bdae2`, since 0.0.4d — and at `c970483`, since 0.0.4e |
'''),
(r'''| `f(v)`, where `f` takes `Vec<T>` by value | compiles WITHOUT `move`: the parameter is a LOAN (D-065, D-183), and `move` of it is `NITPICK-TYPE-047`. `vec_get` is one, and its signature is unchanged |
''',
r'''| `f(v)`, where `f` takes `Vec<T>` by value | compiles WITHOUT `move`: the parameter is a LOAN (D-065, D-183), and `move` of it is `NITPICK-TYPE-047`. `vec_get` is one; since 0.0.4e it keeps that parameter and takes `T: Pod` (RX-168), and the loan is read-only |
'''),
(r'''| a callee freeing or growing through its loan's address, `vec_free(@v)`, `vec_push(@v, x)` | **compiles, and the caller's header names a released block** — `vec_alias_param_free`, `vec_alias_param_grow`, `sparseset_alias_param_free` |
''',
r'''| a callee freeing or growing through its loan's address, `vec_free(@v)`, `vec_push(@v, x)` | **refused `NITPICK-TYPE-085` at `c970483`**, at the `@` (DEF-102). Through `c3bdae2` it compiled, and the caller's header named a released block — `vec_alias_param_free`, `vec_alias_param_grow`, `sparseset_alias_param_free`, rejection fixtures since 0.0.4e |
'''),
(r'''| a callee overwriting an owning field of a loan | **compiles, and drops the caller's value** — a double free with no `wild` block: `../../tests/probe/probe17_lent_field_drop.npk`, `bytes_alias_param_grow` |
''',
r'''| a callee overwriting an owning field of a loan | **refused `NITPICK-TYPE-085` at `c970483`**, at the write (DEF-102). Through `c3bdae2` it compiled and dropped the caller's value — a double free with no `wild` block: `../../tests/probe/refused/probe17_lent_field_drop.npk`, `bytes_alias_param_grow` |
'''),
(r'''| a `for` binding over an array of containers freed through, `for (Vec<int64>:x in arr) { drop vec_free(@x); }` | **compiles — the binding is a loan like a parameter, and the element's block is freed through it**; the array's element still says `count == 1` and reads the free poison — `../../tests/unit/vec_alias_for_binding_free.npk` |
''',
r'''| a `for` binding over an array of containers freed through, `for (Vec<int64>:x in arr) { drop vec_free(@x); }` | **refused `NITPICK-TYPE-085` at `c970483`**, at `@x` — the binding is a loan like a parameter (DEF-102). Through `c3bdae2` it compiled, and the array's element read the free poison — `../../tests/rejection/vec_alias_for_binding_free.npk` |
'''),
(r'''| a generic function passing out its lent `T`, `func:id<T> = T(T:x) { pass x; }`, at `T = Vec<int64>` | **compiles, and the result is a second owner of the block** — `../../tests/unit/vec_alias_generic_passout.npk`; the same body written for one type is `NITPICK-TYPE-047` |
''',
r'''| a generic function passing out its lent `T`, `func:id<T> = T(T:x) { pass x; }`, at `T = Vec<int64>` | **refused `NITPICK-TYPE-047` at `c970483`**, at the `pass` (DEF-104), as the same body written for one type always was. Through `c3bdae2` it compiled and the result was a second owner of the block — `../../tests/rejection/vec_alias_generic_passout.npk` |
'''),
# S-23b's closing note
(r'''takes a lent bare `T`. *(This said "the last two rows are a compiler defect"
until the fifth cycle 0.0 audit's N-25 and N-26, which added the last two —
RX-167. The re-pin to a compiler carrying 3g measures each row rather than
assuming it.)*
''',
r'''takes a lent bare `T`. *(This said "the last two rows are a compiler defect"
until the fifth cycle 0.0 audit's N-25 and N-26, which added the last two —
RX-167. The re-pin to a compiler carrying 3g measures each row rather than
assuming it.)*
*(@@DATE@@, cycle 0.0.4e, compiler `c970483` — RX-169. The re-pin measured each
row, and each is refused as the table now says; every file a row names still runs
at `c3bdae2`, so each refusal is the pin's. "No type refuses it" stands and matters
less: the COMPILER refuses it. A callee that must change a container takes `move T:p`
with `move(...)` at the call, or a pointer — `../../tests/unit/loan_spellings.npk`
runs each. And DEF-104's gate reached `src/` after all, through a `T` place rather
than a `T` parameter — `vec_get`, `vec_pop`; RX-168.)*
'''),
]

# ============================================================ meta/specs/VERIFICATION.md
EDITS["meta/specs/VERIFICATION.md"] = [
(r'''  its address still frees or grows the caller's block — a compiler defect,
  `SAFETY.md` S-23b.)*
''',
r'''  its address still frees or grows the caller's block — a compiler defect,
  `SAFETY.md` S-23b.)*
  *(@@DATE@@, cycle 0.0.4e — RX-168, RX-169. At `c970483` the loan is inside a rule
  too, the compiler's: a write through one is `NITPICK-TYPE-085`. And `vec_get` at an
  owning `T` is refused (`T: Pod`) rather than a move out of the slot.)*
'''),
]

# ================================================================= meta/specs/TESTING.md
EDITS["meta/specs/TESTING.md"] = [
(r'''    back through `lexical.read` — it must read exactly the imports and the code
    the compiler does at `c3bdae2` (RX-157, RX-165). Tested on the instrument, as
''',
r'''    back through `lexical.read` — it must read exactly the imports and the code
    the compiler does at `c970483` (RX-157, RX-165; at `c3bdae2` until cycle
    0.0.4e, whose RX-170 moved the block-string close and rewrote line 23 to read
    the two closes apart). Tested on the instrument, as
'''),
]

# =================================================================== meta/specs/BUILD.md
EDITS["meta/specs/BUILD.md"] = [
(r'''  `harness/lexical.py`, which mirrors that lexer at `c3bdae2`: comments (`/* */`
''',
r'''  `harness/lexical.py`, which mirrors that lexer at `c970483` (at `c3bdae2` until
  cycle 0.0.4e, RX-170 — the block string's close): comments (`/* */`
'''),
]

# ============================================================================ CLAUDE.md
EDITS["CLAUDE.md"] = [
(r'''**31** language probes with recorded verdicts, split **24 / 7** by kind (16 / 7,
''',
r'''**32** language probes with recorded verdicts, split **25 / 7** by kind (16 / 7,
'''),
(r'''`Vec`'s move-only marker rests on, and probe 17, a compiler defect a lent
parameter shows — RX-161, RX-162);
''',
r'''`Vec`'s move-only marker rests on, and probe 17, a compiler defect a lent
parameter shows — RX-161, RX-162; then 25 / 7 when cycle 0.0.4e moved probe 15 out
of `refused/` and probe 17 into it — the compiler's lexer and its loan rule fixed —
and added probe 18, a compiler defect an impl's `move` shows — RX-168 … RX-170);
'''),
(r'''`tests/rejection/` holds fourteen consumer-facing refusals (five of them the
containers' seal, since 0.0.4c; one a `Bytes` copy refused `TYPE-046`, since the
fourth triage; and since 0.0.4d five `Vec` and `SparseSet` copies refused
`TYPE-046` and a write through `Bytes.buf` refused `TYPE-080`); `harness/` builds, sweeps,
''',
r'''`tests/rejection/` holds twenty-one consumer-facing refusals (five of them the
containers' seal, since 0.0.4c; one a `Bytes` copy refused `TYPE-046`, since the
fourth triage; since 0.0.4d five `Vec` and `SparseSet` copies refused
`TYPE-046` and a write through `Bytes.buf` refused `TYPE-080`; and since 0.0.4e the
six loan and pass-out pins, refused `TYPE-085` and `TYPE-047`, and `vec_get` at an
owning element, refused `TYPE-017`); `harness/` builds, sweeps,
'''),
(r'''with 53 unit programs of their own — eight of them measuring what each `Vec` verb does at an
owning element type, which `SAFETY.md` S-23a keeps out of `src/`; six pinning what still reaches
a move-only `Vec`'s block without a copy — four through a LENT `Vec`, `SparseSet` or `Bytes`
(RX-162), one through a `for` binding and one through a generic function passing out its lent
`T` (RX-167), each a compiler defect raised; and the swap and the moves a move-only `Vec` still
allows (RX-161). **No matching happens yet**: `src/syntax/`,
''',
r'''with 47 unit programs of their own — seven of them measuring what each `Vec` verb does at an
owning element type, which `SAFETY.md` S-23a keeps out of `src/` (the eighth, `vec_get`'s, is a
refusal since cycle 0.0.4e: `vec_get` takes `T: Pod`, RX-168); the swap and the moves a move-only
`Vec` still allows (RX-161); and `loan_spellings`, the spellings the six loan and pass-out
refusals prescribe — the six were units pinning a compiler defect until `c970483` refused them
(RX-169). **No matching happens yet**: `src/syntax/`,
'''),
(r'''still one placeholder module each. A full green run at compiler `c3bdae2` is
**214 units** (after the cycle 0.0 close's fifth audit triage; 210 after cycle 0.0.4d, 194 after the fourth triage, 174 after the third), plus eight tree checks; take those numbers from the runner's
''',
r'''still one placeholder module each. A full green run at compiler `c970483` is
**218 units** (after cycle 0.0.4e; at `c3bdae2`, 214 after the cycle 0.0 close's fifth audit triage, 210 after cycle 0.0.4d, 194 after the fourth triage, 174 after the third), plus eight tree checks; take those numbers from the runner's
'''),
(r'''  element only when it can see that it owns nothing. This bullet said until the third cycle 0.0
  audit that the language forced it.
''',
r'''  element only when it can see that it owns nothing. This bullet said until the third cycle 0.0
  audit that the language forced it.
  *(Since cycle 0.0.4e, compiler `c970483`, it does for `vec_get`: the old body is refused at
  every `T` (DEF-104), and `vec_get` takes `T: Pod`, which an owning type cannot implement as
  declared — so `vec_get` at `Vec<string>` is `NITPICK-TYPE-017`, not a move (RX-168). An impl
  that declares `move` on its `self` defeats that: a compiler defect,
  `tests/probe/probe18_impl_adds_move.npk`.)*
'''),
(r'''  not asked of a lent `T` in a generic body (the registry's O-N22, the compiler's DEF-104).
  So no generic in `src/` takes a lent bare `T` (RX-167).
''',
r'''  not asked of a lent `T` in a generic body (the registry's O-N22, the compiler's DEF-104).
  So no generic in `src/` takes a lent bare `T` (RX-167).
  *(At `c970483`, cycle 0.0.4e, all three are refused — a write through a loan
  `NITPICK-TYPE-085`, the generic pass-out `NITPICK-TYPE-047` (RX-169). A callee that
  changes a container takes `move T:p` or a pointer: `tests/unit/loan_spellings.npk`.)*
'''),
(r'''  registry's O-N21, the compiler's DEF-102, refused `NITPICK-TYPE-085` from its 1.6.0
  step 3g, not in `c3bdae2`. A `for` binding is the same loan, and a generic identity is
  a second owner (O-N22, DEF-104): RX-167, `tests/unit/vec_alias_for_binding_free.npk`
  and `vec_alias_generic_passout.npk`.)*
''',
r'''  registry's O-N21, the compiler's DEF-102, refused `NITPICK-TYPE-085` from its 1.6.0
  step 3g, not in `c3bdae2`. A `for` binding is the same loan, and a generic identity is
  a second owner (O-N22, DEF-104): RX-167, `tests/unit/vec_alias_for_binding_free.npk`
  and `vec_alias_generic_passout.npk`.)*
  *(Since cycle 0.0.4e, compiler `c970483`, none of that stays open: the loan is
  `NITPICK-TYPE-085` and the generic pass-out `NITPICK-TYPE-047`, and each file named
  above is a refusal in `tests/rejection/` or `tests/probe/refused/` — RX-169.)*
'''),
(r'''  whose `ListLen` on the containers' counts adds `LimitViolated` (S-24a).
''',
r'''  whose `ListLen` on the containers' counts adds `LimitViolated` (S-24a).
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
  @@DEFECT@@.
'''),
]

# ======================================================================== nitpick.toml
EDITS["nitpick.toml"] = [
(r'''# (B-15) -- the two `failsafe_*` ones `src/lib.npk`, and the other twelve (the
# seal's five since cycle 0.0.4c, `bytes_copy` since the close's fourth triage,
# the five `Vec` and `SparseSet` copies and `bytes_buf_ptr_write` since 0.0.4d)
# the `src/core/` modules they test -- which makes them the standing
''',
r'''# (B-15) -- the two `failsafe_*` ones `src/lib.npk`, and the other nineteen (the
# seal's five since cycle 0.0.4c, `bytes_copy` since the close's fourth triage,
# the five `Vec` and `SparseSet` copies and `bytes_buf_ptr_write` since 0.0.4d,
# and the six loan and pass-out pins and `vec_owning_get_moves_out` since 0.0.4e)
# the `src/core/` modules they test -- which makes them the standing
'''),
]

# ============================================================= tests/rejection/README.md
EDITS["tests/rejection/README.md"] = [
(r'''`bytes_alias_param_grow`) and by `../probe/probe17_lent_field_drop.npk`, and raised
(RX-162). The day the compiler holds a loan read-only, those move here.
''',
r'''`bytes_alias_param_grow`) and by `../probe/probe17_lent_field_drop.npk`, and raised
(RX-162). The day the compiler holds a loan read-only, those move here.
*(That day was cycle 0.0.4e's re-pin to `c970483` — the section below.)*
'''),
(r'''## Why they are the standing instance of rule B-7
''',
r'''## The loan and the generic pass-out refused, and `vec_get` at an owner — cycle 0.0.4e

Since cycle 0.0.4e the pin is compiler `c970483`, which holds a LOAN read-only
(DEF-102, `NITPICK-TYPE-085`) and asks `NITPICK-TYPE-047` of a lent `T` in a generic
body (DEF-104) — `../../meta/DECISIONS.md` RX-169. The six files that pinned what a
loan still reached were units under `../unit/` until then, PINNED, NOT ENDORSED;
they are refusals here now, under the same names, each refused exactly its code at
the `@` or the `pass`:

- **`vec_alias_param_free.npk`**, **`vec_alias_param_grow.npk`** — a callee freeing or
  growing its caller's `Vec` through `@v`: `NITPICK-TYPE-085`.
- **`sparseset_alias_param_free.npk`** — the same for a `SparseSet`: `NITPICK-TYPE-085`.
- **`bytes_alias_param_grow.npk`** — a callee growing a lent `Bytes`, whose field
  overwrite dropped the caller's body: `NITPICK-TYPE-085`.
- **`vec_alias_for_binding_free.npk`** — a `for` binding freed through:
  `NITPICK-TYPE-085` at `@x`.
- **`vec_alias_generic_passout.npk`** — a generic identity handing back its lent
  `T`: `NITPICK-TYPE-047` at the `pass`.

Two of them name their free's `T` — `vec_free::<int64>(@v)` — because written
`vec_free(@v)` the refused argument leaves `T` nothing to be inferred from, and the
compiler adds `NITPICK-TYPE-022` at the same call: a code about the cascade, which
B-7's equality would make part of what the file asserts. Their language twin,
`../probe/refused/probe17_lent_field_drop.npk`, moved with them.

And `vec_get` takes `T: Pod` (RX-168):

- **`vec_owning_get_moves_out.npk`** — `vec_get` at `Vec<string>`: `NITPICK-TYPE-017`.
  Through `c3bdae2` it moved the element out of its slot; the name is kept so RX-155
  still finds it.

**Each refusal is shown to be the pin's or the bound's**
(`../../meta/roadmap/0.0/0.0.4e.md` step 5): the six loan and pass-out files and probe
17 still compile and run at `c3bdae2`, each with the exit it asserted as a unit; and
`vec_owning_get_moves_out` compiles and runs against the tree before 0.0.4e.
`../unit/loan_spellings.npk` is the positive twin: a callee that frees takes `move`,
one that grows takes a pointer, a loop reads its binding, a generic takes `move T` —
and all of it runs.

## Why they are the standing instance of rule B-7
'''),
(r'''All fourteen import `src/` by a **relative** path — the two `failsafe_*` fixtures
`../../src/lib.npk`, the other twelve the `../../src/core/` modules they test
(*"all seven" went stale when the fourth triage added `bytes_copy.npk`; corrected
at 0.0.4d*) —
''',
r'''All twenty-one import `src/` by a **relative** path — the two `failsafe_*` fixtures
`../../src/lib.npk`, the other nineteen the `../../src/core/` modules they test
(*"all seven" went stale when the fourth triage added `bytes_copy.npk`; corrected
at 0.0.4d; "fourteen" and "twelve" at 0.0.4e*) —
'''),
(r'''  `NITPICK-TYPE-083` (its DEF-96) — landed on the compiler's `main` at `d156c4f`;
  no pin of ours carries it yet — a code beside the one the fixture names, which B-7's
''',
r'''  `NITPICK-TYPE-083` (its DEF-96) — landed at `d156c4f`, in our pin since
  `c970483` — a code beside the one the fixture names, which B-7's
'''),
]

# ================================================================= tests/probe/README.md
EDITS["tests/probe/README.md"] = [
(r'''| `tests/probe/` | **24**, each `// expect-exit: N` | `probe`, stage `program` | it compiles, links, runs, and exits with that code — at −O0 and again under `opt -O2` |
''',
r'''| `tests/probe/` | **25**, each `// expect-exit: N` | `probe`, stage `program` | it compiles, links, runs, and exits with that code — at −O0 and again under `opt -O2` |
'''),
(r'''> **The split is 24 / 7, and 31 is the count of probes in this repository.** It
> was 16 / 7, then 17 / 6, then 19 / 6, then 22 / 5, then 22 / 6, and every move
> was a probe changing directory or name because the compiler changed its answer —
> not a probe being deleted, which P-5 forbids — or a probe ADDED.
''',
r'''> **The split is 25 / 7, and 32 is the count of probes in this repository.** It
> was 16 / 7, then 17 / 6, then 19 / 6, then 22 / 5, then 22 / 6, then 24 / 7, and
> every move was a probe changing directory or name because the compiler changed its
> answer — not a probe being deleted, which P-5 forbids — or a probe ADDED.
>
> **@@DATE@@, cycle 0.0.4e, at the re-pin to `c970483` (RX-168, RX-169, RX-170).**
> Two probes crossed and one was added. `probe15_block_string_close.npk` moved OUT of
> `refused/`: the compiler's lexer closes a block string at `"""` since its 1.6.0
> step 3e (DEF-98), so `"""a""b"""` compiles and exits 4, and `harness/lexical.py`
> and self-check case 18 moved with it. `probe17_lent_field_drop.npk` moved INTO
> `refused/`: overwriting an owning field of a lent parameter is `NITPICK-TYPE-085`
> since 3g (DEF-102). Each still gives its old verdict at `c3bdae2`, so each move is
> the pin's. `probe18_impl_adds_move.npk` (exit 95) is new: a compiler defect found at
> the subcycle's planning — an impl may declare `move` on a parameter its trait
> lends, and a call through the trait then double-frees. It says what to do when it
> reddens.
'''),
]

# ==================================================================== harness/README.md
EDITS["harness/README.md"] = [
(r'''11 and 22; and all three of BL-9's fixes reverted together, 18, 19, 20, 21 and 23.
''',
r'''11 and 22; and all three of BL-9's fixes reverted together, 18, 19, 20, 21 and 23.
And cycle 0.0.4e (`0.0.4e.md` step 6) put `c3bdae2`'s block-string close back into
`lexical.py` in a copy, after moving the module to the new one: it reddens 18.
'''),
]

# ================================================================= meta/roadmap/0.1/0.1.0.md
EDITS["meta/roadmap/0.1/0.1.0.md"] = [
(r'''- **31 language probes** with recorded verdicts (`0.0/0.0.0.md` §7), 24 at
  the `program` stage and 7 refusals — at compiler `c3bdae2`, after cycle 0.0.4d
  added probes 16, 16b and 17; it was 28, 22 and 6 after the close's fourth
''',
r'''- **32 language probes** with recorded verdicts (`0.0/0.0.0.md` §7), 25 at
  the `program` stage and 7 refusals — at compiler `c970483`, after cycle 0.0.4e
  moved probe 15 out of `refused/` and probe 17 into it and added probe 18; 31, 24
  and 7 at `c3bdae2` after cycle 0.0.4d added probes 16, 16b and 17; it was 28, 22
  and 6 after the close's fourth
'''),
(r'''and `vec_get` then MOVES the element out of its slot, leaving an empty one that
`count` still counts. The rule is this library's, which is why it is checked.)*
''',
r'''and `vec_get` then MOVES the element out of its slot, leaving an empty one that
`count` still counts. The rule is this library's, which is why it is checked.)*
*(@@DATE@@, cycle 0.0.4e — RX-168: for `vec_get` it is the compiler's too now.
`vec_get` takes `T: Pod`, and at an owning `T` it is `NITPICK-TYPE-017`, not a move.)*
'''),
(r'''not say so. `Vec<string>` compiles; `vec_get` on it MOVES the element out and
the next read is empty; `vec_set`, `vec_remove`, `vec_swap_remove`,
''',
r'''not say so. `Vec<string>` compiles; `vec_get` on it MOVED the element out and
the next read was empty, through `c3bdae2` — since cycle 0.0.4e it is refused,
`T: Pod` (RX-168); `vec_set`, `vec_remove`, `vec_swap_remove`,
'''),
(r'''attempt, 158 after the adoption to `c3bdae2`, 174 after the third triage, and more
after the fourth.
''',
r'''attempt, 158 after the adoption to `c3bdae2`, 174 after the third triage, more
after the fourth, and 218 after the adoption to `c970483` (cycle 0.0.4e).
'''),
(r'''writes takes `move T` or a pointer, never a bare lent `T`, and frees nothing
through a `for` binding.)*
''',
r'''writes takes `move T` or a pointer, never a bare lent `T`, and frees nothing
through a `for` binding.)*
*(@@DATE@@ — cycle 0.0.4e, at compiler `c970483`: the compiler holds all of it now.
A write through a loan is `NITPICK-TYPE-085`, a generic pass-out of a lent `T`
`NITPICK-TYPE-047` (RX-169). And `vec_get` takes `T: Pod` (RX-168), so D6's
`ast_get` needs its element to implement `Pod` — for a POD `AstNode`, one line
where it is declared, `impl:AstNode:Pod = { func:pod_copy = AstNode(AstNode:self)
never fails { pass self; }; };`, which the compiler refuses for an owning struct.
`../../../tests/unit/loan_spellings.npk` runs each spelling a callee needs.)*
'''),
(r'''compiler's DEF-97, fixed at its 1.6.0 step 3d (`f758995`), which the pin
`c3bdae2` does not carry. The
''',
r'''compiler's DEF-97, fixed at its 1.6.0 step 3d (`f758995`), which the pin
`c3bdae2` does not carry. *(@@DATE@@, cycle 0.0.4e: `c970483` carries it. The
fourth audit's reproducer, the same with the struct in an imported module, and a
generic helper with a `Vec<T>` local called at `int64` and at `string` each build and
run at −O0 and through `opt -O2` there, where `llc` refused all four at `c3bdae2` —
so such a helper is buildable now.)* The
'''),
(r'''DEF-96 — landed on the compiler's `main` at `d156c4f`; no pin of ours carries it yet). Spell it
''',
r'''DEF-96 — landed at `d156c4f`, in our pin since `c970483`). Spell it
'''),
]

# ============================================================== meta/roadmap/0.0/README.md
EDITS["meta/roadmap/0.0/README.md"] = [
(r'''# Cycle 0.0 — Foundations — **NOT CLOSED. The close was refused FIVE times — three on 2026-09-06, the fourth and fifth on 2026-09-25 — and it waits on the author's question 10: recommended, a re-pin to a compiler carrying its 1.6.0 step 3g, and then an audit that has seen it.**
''',
r'''# Cycle 0.0 — Foundations — **NOT CLOSED. The close was refused FIVE times — three on 2026-09-06, the fourth and fifth on 2026-09-25 — and waited on the author's question 10, answered (a): a re-pin to a compiler carrying its 1.6.0 step 3g. That re-pin is 0.0.4e, to `c970483`; an audit that has seen it is next.**

> ## 0.0.4e — the adoption to compiler `c970483`: the loan refused, `vec_get` bounded
>
> **[`0.0.4e.md`](0.0.4e.md).** The re-pin question 10 waited for, to the end of the
> compiler's 1.6.0 chain. **The loan is refused**: every write through a lent
> container is `NITPICK-TYPE-085` and a generic pass-out of a lent `T`
> `NITPICK-TYPE-047`, so the six pins and probe 17 are refusals, each still running
> at `c3bdae2`, and `loan_spellings` runs what the refusals prescribe (RX-169). **The
> tree did not compile at the new pin until `src/` changed**: DEF-104's gate refuses
> a `T` place passed out of a lent or pointed-to container at every `T`, which was
> `vec_get` and `vec_pop` — so `vec_get` takes `T: Pod`, a trait an owning type cannot
> implement as declared, and `vec_pop` spells `move(...)` (RX-168). `lexical.py`
> closes a block string at `"""` and probe 15 runs (RX-170). Planning found a
> compiler defect, pinned as probe 18: an impl may declare `move` on a parameter its
> trait lends.
'''),
(r'''*(2026-09-25, cycle 0.0.4d — RX-161, RX-162. "Every `*_alias_*` shape is refused"
''',
r'''*(@@DATE@@, cycle 0.0.4e — RX-169. THE LOAN CLAUSE IS MET at `c970483`: the four
`*_alias_param_*` fixtures, probe 17 and the `for` binding are each refused
`NITPICK-TYPE-085` at the position its own `expect-error-at` records, and each still
runs at `c3bdae2`, so each refusal is the pin's; the generic pass-out is
`NITPICK-TYPE-047`. The audit that accepts the close sees this tree.)*

*(2026-09-25, cycle 0.0.4d — RX-161, RX-162. "Every `*_alias_*` shape is refused"
'''),
]

# ====================================================================== ROADMAP.md
EDITS["meta/roadmap/ROADMAP.md"] = [
(r'''triage ([§12](0.0/0.0.5.md)) made the harness read source as the compiler does. Next: the author's question 10 — recommended, a re-pin to a compiler carrying its 1.6.0 step 3g — then an audit** | — |
''',
r'''triage ([§12](0.0/0.0.5.md)) made the harness read source as the compiler does. 0.0.4e ([`0.0.4e.md`](0.0/0.0.4e.md)) re-pinned to `c970483`, question 10's answer: the loan refused, `vec_get` bounded by `Pod`. Next: an audit that has seen it, then the close** | — |
'''),
(r'''> `NITPICK-TYPE-085`, the compiler's 1.6.0 step 3g, not in `c3bdae2` — which is
> the author's question 10 and a separate re-pin subcycle.
''',
r'''> `NITPICK-TYPE-085`, the compiler's 1.6.0 step 3g, not in `c3bdae2` — which is
> the author's question 10 and a separate re-pin subcycle.
>
> **0.0.4e re-pinned to `c970483`** ([`0.0/0.0.4e.md`](0.0/0.0.4e.md)), RX-168 …
> RX-170: the loan and the generic pass-out refused and their pins moved to the
> rejection suite; `vec_get` bounded by `T: Pod`, because DEF-104's gate refused the
> old body at every `T`; `vec_pop`'s move spelled; the harness's block-string close
> moved with the compiler's lexer. The close waits for an audit that has seen it.
'''),
(r'''pass-out, and the parse sweep's two more files — `src/core/` with **53** unit
programs, a self-check of **24** cases, 20 live, and decisions through RX-167.)*
''',
r'''pass-out, and the parse sweep's two more files — `src/core/` with **53** unit
programs, a self-check of **24** cases, 20 live, and decisions through RX-167.)*
*(After cycle 0.0.4e, at compiler `c970483`: **218** units — six loan and pass-out
units and `vec_owning_get_moves_out` moved to the rejection suite, probe 15 and probe
17 crossed, probe 18 and `loan_spellings` added, and the parse sweep's two more files
— **32** probes, `src/core/` with **47** unit programs, and decisions through
RX-170.)*
'''),
]

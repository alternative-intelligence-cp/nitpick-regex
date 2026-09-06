# Verification obligations

The compiler's cycle 1.5 makes `prove`, `requires`/`ensures`, `limit<Rules>`
and Z3 real. Its orchestration rules say that **every branch records its own
verification obligations and the orchestrator merges them** (R9), because
obligations discovered in a branch and never collected are the cheapest way to
lose the campaign.

This is `nregex`'s list, written **before** the code.

---

## 1. Why this library is an unusually good subject

Three properties make `nregex` the strongest verification candidate among the
libraries planned so far, and they are worth stating because they should shape
how much effort goes here:

- **It makes no syscall.** The trusted base beneath it is the allocator and
  `memcpy` — nothing else. There is no kernel behaviour to model, no terminal
  claiming a capability, no network peer.
- **Its central claim is a bound, and a bound is what a solver is for.** "This
  search takes at most `m · n` steps" is an obligation. "Terminal restoration
  happened" is not.
- **Every hot loop has an obvious variant.** Bytes remaining, instructions
  remaining, states remaining. Termination is provable rather than argued.

---

## 2. Where this stands

| Compiler subcycle | What it gives us | Our state |
|---|---|---|
| 1.5.0 (done) | the SMT writer, z3 pinned, the obligation manifest, `llvm.assume` elision | the bounds obligations we generate are already decidable |
| 1.5.1 | `limit<R>` names resolve, `Rules` bodies type, contracts type | §5's types become writable |
| 1.5.2 | `limit<Rules>` live | **LANDED, and §5 does NOT take it — RX-127.** Measured at pin `3d15ac9`: a limited parameter is checked in every build, a violation traps `LimitViolated`, and REACH-002 makes that a mandatory arm in **every consuming program**. That is a second arm on top of S-8's one, so this library declines the construct |
| 1.5.3 | contracts live | §3 and §4's clauses land |
| 1.5.4 | `prove` / `assert_static` | §6's inline proofs land |

**Rule P-1.** Until a construct is live, its obligation is stated **as a
comment beside the code in the exact syntax it will take**, and is enforced by
a property test. Measured at the compiler's 1.5.0: `prove`, `assert_static`,
`limit<Rules>`, loop `invariant` and `requires`/`ensures` all refuse with
`NITPICK-RUNG-001` naming "1.5" (`src/backend/ir/ir_stmt.npk`), so a premature
clause is a build failure and not a silent no-op. The switch is deleting a
comment marker rather than inventing the clause.

**Rule P-1a (RX-127) — the rung is no longer uniform, so "refused by name" must
be re-measured per construct and not inherited.** At pin `3d15ac9`, `prove`,
`requires` and `ensures` still refuse `NITPICK-RUNG-001` — `probe13a`,
`probe13c`, `probe13d` — and **`limit<Rules>` does not**: it is live, accepted
and enforced (`probe13b`, `probe13e`). P-1's guarantee that a premature clause
is a build failure therefore still holds for the three this library writes, and
has stopped holding for the one it does not. **A comment-form obligation is
only inert while its construct is refused**, so any cycle that writes a new
clause re-runs the probe for that clause rather than citing this paragraph.

---

## 3. What the language discharges for free

Most of the list, which is why the residue is small:

- **Indexing a type that CARRIES A LENGTH traps** (D-070) — a slice `T[]` and a
  fixed array `T[N]`. **This library's own containers are not in that set and
  the language discharges nothing for them (RX-111, RX-128).** `Vec<T>.items`
  is a `wild T->` and a `buffer`'s bytes are reached through `.ptr`, both bare
  pointers: an out-of-range index **reads and returns a heap word, silently**.
  So the obligation §4 states is not "is a reachable index out of bounds" —
  every index into a `Vec` or a `Bytes` is an obligation this library
  discharges itself, through the accessor pairs, or not at all.
  `SAFETY.md` §5.3 (S-23).
- **Every plain integer `+ - *` traps on overflow** (D-210), so program-size
  arithmetic cannot silently produce a wrong bound.
- **Borrows cannot escape** (D-004), so a `Cache` cannot outlive its scope and
  a `Match` cannot alias a freed haystack.
- **Owning values are move-only** (TYPE-046), so no program is aliased.
- **`Result<T>` everywhere** with no unchecked unwrap outside a `never fails`
  callee (D-163), so no error is dropped.

---

## 4. Bounds — the largest class

**Rule P-2 — every program access goes through one accessor pair.**

```nitpick
func:prog_inst = Inst(Program->:p, int32:pc)
    requires (pc >= 0i32 && pc < (p.insts.count =>! int32))
    never fails { … };
```

Discharging it makes **every instruction fetch in every engine** safe by
construction rather than by a runtime check at each site — and elides the
check, which is the D-218.9 payoff on the hottest loop in the library.

The callers then owe `pc` in range, which is where the structure does the work:

| Site | Obligation | Discharged by |
|---|---|---|
| `prog_inst` | `pc` in range | contract, Z3 |
| every `goto` operand | the compiler emitted an in-range target | a compile-time invariant: emission only ever writes an index it has allocated. `ensures` on the emitter |
| `SparseSet` insert | the key is below the set's capacity, and capacity is the program size | contract, Z3 |
| capture slot write | `slot < 2 × group_count` | contract, Z3 |
| class index | `< classes.count` | contract, Z3 |
| byte class lookup | the index is a `uint8`, the table is 256 | trivially, and stated so the solver has it |
| haystack read | `at < hay.len` | contract; the engines' loop invariant |
| DFA cache lookup | the state id is below the cache's live count | contract, Z3 |

**Rule P-3 — the emitter's `ensures` is the interesting one.** "Every `goto` in
the emitted program points at an instruction that exists" is a whole-program
property, and if it is discharged then every engine's `pc` obligation follows
from it plus "the engine only ever moves `pc` to a `goto` operand or `pc + 1`".
That is the shape to aim for: one hard proof at the compiler, and cheap
inductive ones at each engine.

---

## 5. `limit<Rules>` — the types this library DECLINED to carry

> **1.5.2 HAS LANDED AND §5 IS NOT TAKEN — `SAFETY.md` S-24 (RX-127).** This
> section was written as a plan for the day the rung opened. The rung opened,
> the construct was measured, and **the answer was no**: a `limit`ed binding
> anywhere in the reachable call graph makes `(LimitViolated)` a mandatory
> `failsafe` arm in every consuming program — at module-private visibility as
> well as `pub`, because reachability follows the call graph and not visibility
> — and no `?|`, `?!` or `is_err` at the call site can decline it, because the
> violation takes D-241's trap route. That is a **second** arm against S-8's
> promise of exactly one, and S-8 is this library's headline API property.
>
> **The section is kept rather than deleted**, because the four `Rules` below
> are the right *ranges* and are what `src/core/limits.npk` and the accessor
> pairs check by hand; and because a later reader will propose exactly this and
> should meet the measurement rather than repeat it. **P-4 is superseded by
> S-24 and is not a live obligation** — corrected at cycle 0.0.5, where the
> reconciliation found §2 of this same file already saying *"LANDED, and §5 does
> NOT take it"* while §5 still read as a plan (RX-137).

**Rule P-4 — SUPERSEDED by `SAFETY.md` S-24.** Written as: *when 1.5.2 lands,
these become `limit`ed and the checks inject at initialisation, at every
assignment, and at parameter entry.* The ranges stand as ranges; the construct
is declined:

```nitpick
Rules:ProgramIndex = { $ >= 0i32; $ < 100000i32; };   // NREGEX_PROGRAM_INSTRUCTIONS
Rules:CaptureSlot  = { $ >= 0i32; $ < 500i32; };      // 2 x NREGEX_CAPTURE_GROUPS
Rules:Codepoint    = { $ <= 1114111u32; };
Rules:ByteClassId  = { $ < 256u32; };
```

The argument that was made for doing it here rather than by hand-written
checks — **and it is still a good argument, which is why the answer had to be
measured rather than assumed**: a `limit`ed parameter's precondition is
discharged **at the caller**, where the caller's own knowledge proves it, and
retained as a runtime check only where it cannot be, with the manifest recording
which is which per site. What defeats it is not the mechanism but its price to
somebody else: the arm lands in **every consuming program**, including one that
only wants to ask whether a codepoint is alphabetic.

**Rule P-5 — the prototype used this construct** (`ARCHIVE/nregx`'s
`regex_types.npk` declares `pub Rules<int64>:r_valid_regex_len = { $ > 0i64, $
<= 8192i64 };`), so the domain has already reached for it once. Recorded
because it is evidence the shape fits, not because that code is a model.

---

## 6. `prove` sites

**Rule P-6 — inline `prove(…)` where a local fact is cheap to state and
expensive to lose:**

| Site | Proof |
|---|---|
| after a UTF-8 range split (`COMPILE.md` §2) | every produced sequence's byte ranges are within `0x00…0xFF`, and the union of the sequences is exactly the input codepoint range |
| after alphabet compression | every byte maps to a class `< class_count` |
| in the Pike VM's step | the thread set holds at most `program_size` entries |
| after a class fold (`UNICODE.md` U-14) | the range list is sorted and disjoint |
| after HIR normalisation | the same |
| at each engine's return | `lo <= hi` and `hi <= hay.len` |
| in the DFA | the cached transition's target is a live state |

**Rule P-7 — the two that matter most.** "The thread set holds at most
`program_size` entries" is the linear-time guarantee's local form: it is what
makes the inner loop `O(m)` per byte, and everything in `SAFETY.md` §2 rests on
it. And "the union of the produced byte sequences is exactly the input
codepoint range" is the UTF-8 compiler's correctness in one line — the place a
subtle bug would produce a class that silently omits a codepoint.

---

## 7. Termination

**Rule P-8 — every loop is bounded by a value that decreases, and the bound is
stated:**

| Loop | Variant |
|---|---|
| the pattern parser | pattern bytes remaining |
| HIR construction | AST nodes remaining |
| class range merge | ranges remaining |
| UTF-8 range split | the codepoint range's width, halving at each boundary |
| program emission | HIR nodes remaining, times the repetition factor (bounded by `NREGEX_REPEAT_PRODUCT`) |
| the Pike VM outer loop | haystack bytes remaining |
| the Pike VM's zero-width closure | thread-set slots not yet occupied — **the deduplication is the variant** |
| the DFA scan | haystack bytes remaining |
| a prefilter scan | haystack bytes remaining |

**Rule P-9 — the zero-width closure's variant is the subtle one** and is worth
naming. It walks `Split` and `Jump` chains, which a pattern can make cyclic
(`(a*)*`). It terminates because a program counter already in the thread set is
not re-added, so each step either adds a slot or stops — and the set has
`program_size` slots. A `prove` there turns "trust me, `(a*)*` is fine" into a
compile-time fact.

---

## 8. The guarantee itself

**Rule P-10 — the headline claim, as an obligation.** `SAFETY.md` S-1 says a
search is `O(m · n)`. Stated for the solver:

```
requires (step_budget >= program_size * hay.len)
ensures  (steps_taken <= program_size * hay.len)
```

This needs the step counter (`TESTING.md` V-15) to be a real value the engine
maintains, not a debug switch, for the obligation to be about the shipped code.
**That is a cost — one increment per inner iteration — and it is a decision:**
`O-P1` records it, with the recommendation that the counter ships, because a
guarantee nothing measures is a claim.

Until 1.5.3, the property test (V-14) is the standing evidence.

---

## 9. What cannot be proven, and is stated instead

**Rule P-11 — the honest claim**, following the compiler's TCB doctrine
(`TCB.md`, D-218.11: *verified middle-end plus validated floor*): `nregex`'s
verification claim covers **its own arithmetic, memory discipline and step
bounds**, and does not cover:

- **the Unicode data.** Tables are generated from the UCD; their *invariants*
  are checked (sorted, disjoint) and their *contents* are the Consortium's.
- **`llc` and `ld.lld`**, which the compiler names as trusted components.
- **the allocator**, which is the floor's.
- **the semantics of the pattern language itself** — that `SYNTAX.md`'s grammar
  describes what a user expects — which is what the conformance corpus is for
  and what no solver can answer.

---

## 10. The handoff

**Rule P-12.** When the compiler's verified build reaches libraries, `nregex`
hands over: this document's obligation list, the `nitpick.obligations` rows its
own build produces, and the property tests that stood in for each unproven row.
Cycle 0.12 owns that handoff.

---

## 11. Open items

- **O-P1 — does the step counter ship, or is it a debug switch?** Shipping it
  makes P-10's obligation about the real code and makes the guarantee
  measurable in production. Not shipping it saves one increment per inner
  iteration. Recommendation: **ship it**, and measure the cost at cycle 0.13
  before confirming. If it measures worse than 3%, revisit.

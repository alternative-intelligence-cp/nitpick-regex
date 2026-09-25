# Audit — `nitpick-regex`, cycle 0.0 — THIRD PASS — 2026-09-06

**W-22 audit, filed by the eighth orchestrator (`nitpick-libs_s3`). The auditor's
final message is reproduced below in full and unedited. Paths in it are already
relative to the workbench root — the auditor wrote them that way deliberately,
having read the earlier reports' headers, and it says so in its own opening.**

- **Dispatched:** `npk:auditor`, `claude-opus-5`, scoped to the delta of commit
  `ab93eae` and to four named places to press, with an explicit instruction not
  to re-derive either prior audit's clean list.
- **Verdict: DO NOT ACCEPT — the third refusal of this close.** Two blocking
  findings.
- **Filed late.** The audit completed and the orchestrating session lost its
  connection before filing. Nothing was lost: the report was held in the
  session's context and the trees were verified clean and level on resume.

**Both blocking findings are the shapes this cycle keeps producing, one level
deeper each time.**

**`BL-5` is the seventh defect in `src/core/`**, and it is the shape the dispatch
asked for by name — not a missing guard (BL-2's class, swept and exhausted), not
a guard whose stop fails to stop (BL-3), but **a compile-time refusal that three
documents cite, that does not exist at the pin, and that the one test able to
catch it names as its reason for not looking.** `vec_get` on an owning `T` is a
destructive read: the slot is zeroed and marked vacant while `count` is
untouched, so the container claims a live element it has emptied. `Vec<string>`,
pushed once and read twice, returns the value and then returns nothing.

**`BL-6` is in the `pending-until` machinery — introduced by the fix for BL-4,
audited by nothing.** Three mutations, three full harness runs, all **exit 0**: a
marker naming a commit that does not exist is accepted and inert; a marker
absorbs a failure other than the one it names; and **one comment line moves an
ordinary red out of a GREEN run's denominator**, printing `140/140`. The two
sentences in the tree describing its safety property are false at the pin, and
the self-check that exists to catch exactly M3's fault is defeated by it.

**The recurring lesson, now on its third instance in one cycle: the fix for a
finding is where the next finding lives.** BL-4 was introduced by BL-1's fix;
BL-6 by BL-4's. Each was invisible to a green suite for a reason the repository
had already written down somewhere else.

---

REPORT nitpick-regex 0.0 audit (THIRD)
status: DO-NOT-ACCEPT
auditor: npk:auditor, claude-opus-5
toolchain: 3d15ac9

Three trees clean before and after (`git status --porcelain` empty in `nitpick-regex`, `nitpick` and the workbench). **Paths below are relative to the workbench root `nitpick-libs/`**, deliberately — the reference gate refuses a tracked file carrying a home directory, and this report gets filed.

# W-22 AUDIT — `nitpick-regex`, cycle 0.0 close, third pass

**Verdict: DO NOT ACCEPT.** Two blocking findings. One is a **seventh defect in `src/core/`**, and it is the shape the dispatch named: not a missing guard, not a guard that fails to stop, but **a compile-time refusal that three documents cite, that does not exist, and that the one test able to catch it names as its reason for not looking.** The other is in the `pending-until` machinery, which nothing had audited: measured, its named commit is never read, it absorbs a failure other than the one it names, and one comment line moves any red out of a GREEN run's denominator.

Method: the compiler working tree is at `47a7eb2` (1.5.3), **not** the pin; every compiler claim below was read with `git show 3d15ac9:<path>`. Every probe ran all four steps (`npkc`, `llc`, `ld.lld`, binary) with `exit=$?` captured on its own line, at `-O0` and through `opt -O2`. Baseline re-established first from a pristine `git archive` of HEAD in the scratchpad: **141/141 GREEN in 44.8 s**, one PENDING printed, seven tree checks, `check_refs` clean over 66 markdown files, leak scan 173/173.

---

## BLOCKING

### BL-5 — `vec_get` is a DESTRUCTIVE READ for an owning `T`. The compile-time refusal that makes it safe does not exist at the pin, it is asserted in three places, and `vec_unit.npk` cites it as the reason it does not read an element back.

**What the documents claim.** Three sites, one belief:

- `nitpick-regex/src/core/vec.npk:288-290` — *"RETURNS BY VALUE, so it is for a scalar `T` only: for an owning `T` a copy is **refused, TYPE-046**, and the caller reads through the site that knows the element's shape."*
- `nitpick-regex/meta/roadmap/0.0/0.0.4.md:73-74` — stated as a **Rule**: *"`vec_at` returns by value and is therefore for scalar `T` only — for an owning `T` a copy is refused (TYPE-046)"*.
- `nitpick-regex/tests/unit/vec_unit.npk:196-197` — *"`vec_get` is scalar-only by construction -- a copy of an owning element is TYPE-046 -- so the assertion here is on the container's own state."*

`vec_pop`'s header (`vec.npk:322-323`) inherits it: *"scalar `T` only, for `vec_get`'s reason."*

**What the compiler actually does at `3d15ac9`.** `TYPE-046` is `TYPE_MOVE_REQUIRED` (`git show 3d15ac9:src/frontend/type_codes.npk:207`) — *"move required"*, the diagnostic that demands an explicit `move` at a binding site (`ir_writer.npk:277`: *"a `string` binding is move-only (TYPE-046)"*). It is not a refusal of this shape, and it does not fire. `Vec<string>` with `vec_get` compiles at **npkc exit 0**, and the emitted IR for `pass v.items[i]` is a **move out of the slot**:

```llvm
  %t19 = getelementptr { ptr, i64, i64 }, ptr %t17, i64 %t18   ; &items[i]
  %t20 = load { ptr, i64, i64 }, ptr %t19
  store { ptr, i64, i64 } zeroinitializer, ptr %t19            ; *** the slot is ZEROED ***
  call void @"npk.vacant.3"(ptr %t19)                          ; and marked vacant
```

`v.count` is not touched. So the container is left claiming a live element that has been emptied.

**Measured, with a control:**

| probe | shape | result |
|---|---|---|
| `zzE1` | `Vec<string>`, push once, `vec_get(v,0)` twice, exit = 70 + length of the **second** read | **exit 70** — the second read is EMPTY; `v.count` still 1 |
| `zzE2` (control) | identical at `T = int64` | **exit 81** — both reads return 11 |

Identical at `-O0` and through `opt -O2`. So it is specific to an owning `T`, and it is a silent wrong answer, not a trap.

**`vec_get` takes `Vec<T>:v` BY VALUE — no `->` — so its signature says it cannot mutate the caller's container.** It mutates the caller's heap block. `CLAUDE.md:104`, `CONTRIBUTING.md:63` and `SAFETY.md:324` all name `vec_get`/`vec_set` as the sanctioned accessor pair.

**The same false belief leaves three siblings orphaning elements with nothing said about it.** Measured with the repository's own instrument — `NPK_HEAP_STATS`, 1 000 rounds, two ~261-byte `string`s per round, `vec_free_owning` at the end of every round:

| verb exercised mid-round | `peak_live` | verdict |
|---|---|---|
| none (control) | **618** | flat |
| `vec_pop`, bound and dropped | 618 | correct |
| `vec_get`, bound and dropped | 618 | "correct" only because it MOVES OUT — this defect |
| **`vec_set`** over a live element | **261 618** | overwritten element never dropped |
| **`vec_remove`** | **257 353** | removed element never dropped |
| **`vec_swap_remove`** | **257 353** | same |
| `vec_truncate` / `vec_clear` | 522 096 | **documented** — `vec.npk:396-399` says so; not a finding |

Strictly linear: at 3 / 10 / 100 / 1 000 rounds `vec_remove` gives 1 124 / 2 923 / 26 053 / 257 353 against a control flat at 610-618, with `allocated` identical in every pair.

**And the API offers no non-leaking way to remove or overwrite an owning element.** Measured: `vec_get` first, *then* `vec_remove` → 618 flat; `vec_get` first, then `vec_set` → 879 flat. **The only correct usage is through the behaviour the specification says is impossible.**

`vec.npk` documents this orphaning for `vec_free` (LIFETIME section), `vec_truncate` (`:396-399`) and `vec_clear` (`:410`). It says nothing at `vec_set` (`:298-305`), `vec_remove` (`:365-380`) or `vec_swap_remove` (`:383-393`) — and `vec_swap_remove`'s comment does spend a paragraph on the *lesser* hazard, order, *"stated here rather than left to the name"*.

**Why 141/141 is green over it.** Of **35 unit programs**, **two** instantiate `Vec<T>` at an owning `T` — `vec_owning_freed.npk` and `vec_owning_leak.npk` — and **neither calls `vec_get`, `vec_set`, `vec_pop`, `vec_remove`, `vec_swap_remove`, `vec_truncate` or `vec_clear`**; they push and free. `vec_unit.npk:191-197` builds a `Vec<string>`, and at the one line where it could have read an element back it declines, **citing the refusal that does not exist**. That is BL-1's shape exactly — *the suite constructs the case and declines to look* — this time with the reason written down.

**Blast radius today: nil.** `Vec<T>` is instantiated under `src/` only at `T = int32` (`SparseSet.dense`, `SparseSet.sparse`), and POD is unaffected (measured, `zzE2`). That is the same "nil today" as BL-1 and BL-4, and both blocked. **Next:** `meta/specs/HIR.md:43` declares `Vec<HirNode>:nodes;` and `SAFETY.md:557` names `Hir.names`, `Vec<GroupInfo>` and *"any future `Vec<string>`"* as the exceptions to watch. Cycle 0.1 is the parser.

**What would resolve it.** (i) Delete the TYPE-046 sentence from all four sites — it is false at the pin and it is load-bearing. (ii) Decide what `vec_get` is for an owning `T` and say so: either rename it to say it removes (and fix `count`), or restrict it and provide the removing verb the API currently lacks. (iii) Write the orphaning caveat at `vec_set`, `vec_remove` and `vec_swap_remove` as it already is at `vec_truncate`. (iv) A unit at an owning `T` for each of the six verbs, under the memory cap `SAFETY.md` S-22 says is the only instrument here — `vec_get` read twice is a one-line assertion and it is the one that catches the wrong answer rather than the leak.

---

### BL-6 — the `pending-until` mechanism has no control. The named commit is never read; the marker absorbs a failure other than the one it names; and one comment line moves any red out of a GREEN run's denominator.

Three mutations, each a full harness run from a pristine `git archive` of HEAD, each **exit 0**:

| | mutation | result |
|---|---|---|
| **M1** | `pending-until: fe42dba` → `pending-until: 00000000000000000000deadbeefdeadbeefdead` (not a commit, not resolvable) | **141/141 GREEN.** Accepted, printed verbatim, behaviour identical |
| **M2** | the pending unit made to fail for a **different real reason** — an out-of-range `bytes_get` on an empty `Bytes`, trapping 94, not the DEF-25 leak's 92 | **141/141 GREEN.** The PEND line prints *"this tree gives 94"* and nothing objects |
| **M3** | an ordinary unit given a wrong expectation (`bytes_oob_get_empty.npk`, `expect-exit: 94` → `77`) **plus** a pending marker | **140/140 GREEN.** The unit left the denominator silently |

**M1 refutes a sentence in the tree.** `harness/expect.py:80-83` says *"the day the pin moves past the named commit, the harness itself says so, in the run that moves it"*, and `.github/workflows/ci.yml:20-23` says *"the run goes RED the day it starts passing, so bumping `NITPICK_COMMIT` past that commit **cannot leave a stale marker behind**."* Read at source: `expect.py:222-229` accepts any single whitespace-free token with no resolution of any kind, and `harness/stages.py:191-220` uses `exp.pending_until` **only inside printed text**. The retirement is keyed solely on `got == exp.exit_code`. Those two are the same day only when the re-pin happens to make *this* file pass; M2 is the counterexample, and the CI sentence contains its own refutation ("the day it starts passing" is not "bumping past that commit").

**M2 is rule B-7's hazard with no rule B-7.** `harness/stages.py:14-25` states the principle for rejection tests in as many words: a test held only to "it failed" *"would pass FOR THE WRONG REASON... It wanted a refusal; it got one; the refusal was about the path."* `Pending` records `got` (`stages.py:150-158`) and **nothing asserts it**. The marker excuses *any* exit that is not the expected one, not the failure it names. A library regression, a timeout, a link change — all absorbed, all outside the denominator, all GREEN.

**M3 defeats the self-check's own case 1.** `harness/selfcheck.py:299` is `Case(1, "a `program` case whose `expect-exit` is wrong by one")` — precisely what M3 plants — and one comment line turns its red into a PEND. And **no self-check case covers the new mechanism**: `CASES` is 11 entries (1, 2, 3, 3a, 4–10), the run's own banner still says *"EIGHT kinds of wrong expectation"*, and `TESTING.md:248-261`'s V-20 list is unchanged. A ninth way the runner must be able to fail was added and V-21's discipline — *"a harness that has not proven it can fail has not proven anything"* — was not extended to it. The verifier exercised the stale-marker red by hand; the mechanism that runs on every invocation does not.

**Nothing asserts the denominator either.** `141` appears as prose at `CLAUDE.md:19` and `.github/workflows/ci.yml:12`; no tree check and no harness step compares it to what ran. M3's run printed `140/140` and `GREEN`.

**Why this blocks rather than carries.** It is new machinery introduced by the commit under audit; it is the tree's only route for a red to leave a green run; it has no control of any kind — no self-check case, no tree check, no count assertion, no check that the marker names anything real; and the two sentences in the tree describing its safety property are false at the pin, measured. That is BL-4's shape, in the fix for BL-4.

**What would resolve it.** (i) Record the *expected* pending exit and fail when the observed one differs — a `pending-until:` that names both the commit and the exit it is pending on, which is B-7 applied to this marker. (ii) A self-check case that plants a pending marker on a red and requires the run to notice, so V-20's list grows with the mechanism. (iii) Either resolve the named commit or stop claiming it is read; the honest sentence is *"it reddens the day the file starts passing"*. (iv) Assert the judged-unit count somewhere a shrinking denominator reddens.

---

## NON-BLOCKING (carry into 0.1)

**N-13 — a ticked acceptance item whose evidence covers one of the three functions it names.** `meta/roadmap/0.0/0.0.4.md:118-121`, `[x]`: *"the MANAGED half has its own gate, and it is a memory cap — `vec_free`, **`vec_clear` and `vec_truncate`** over an owning `T`, under a bounded peak RSS."* The discharge recorded beneath it (`:122-130`) is `vec_owning_freed.npk`/`vec_owning_leak.npk`, which *"differ only in `vec_free_owning` against `vec_free`"*. `vec_clear` and `vec_truncate` have no cap test; measured, both retain 522 096 B over 1 000 rounds against a 618 B control. The behaviour is documented (`vec.npk:396-399`, `:410`) so it is not a defect — the box is ticked and two thirds of it is untested. Same sentence at `0.0.4.md:18-20` enumerates the obligation as three functions where the set is six.

**N-14 — `OutOfBounds` is not the code the language assigns to a double free, and the sentence justifying the change is wrong about the compiler.** Verified at the pin, both primary sources. `git show 3d15ac9:runtime/npkrt.ll:2843` — `-4099 OUT_OF_BOUNDS  a slice/array index past the end, or a range view that does not fit its source (D-070)`; and `-4102 HEAP_INTEGRITY  **double-free**, foreign/misaligned/null pointer to dalloc/ralloc, corrupted header or torn guard, or a UAF caught by a freed slot's magic`. The prelude (`git show 3d15ac9:src/frontend/prelude_source.npk`) declares `pub error:OutOfBounds = 4099i32; // an index outside its array, slice or range` and `pub error:Unreachable = 4102i32; // #unreachable() reached, **and the runtime's integrity defects** (D-061, D-153)`.

So `Unreachable` is the language's designated code for the condition, and 94 is **mechanically honest** — the program really does index a one-element array at −1 — but not descriptive of what happened. `vec.npk:107-121` justifies the change by analogy to `vec_push`/`vec_insert`, where the old code was `HeapBadRequest` and genuinely misdescriptive; here the old code was exact. The header's *"they report the wrong thing"* is false for the free paths: they reported the right thing from the wrong place. Not blocking — the new stop is earlier, deterministic and names the value — but the rationale should say what it traded, and consumers whose `failsafe` distinguished 95 from 94 now cannot.

**N-15 — RX-144's guard covers the same binding only, and the sentence is unqualified.** `vec.npk:120-121`: *"a double free is `OutOfBounds` at this library's own check, not `Unreachable` from inside `dalloc`."* Measured (`zzJ1`): copy the `Vec` header (`Vec<int64>:w = v;`, accepted at exit 0 — no TYPE-046 there either), `vec_free(@v)` then `vec_free(@w)` → **exit 95, `Unreachable`**, at `-O0` and through `opt -O2`. `w.cap` is still 4, so the guard cannot see it. This is the *"a claim about a set, and the set was never enumerated"* shape, in the paragraph that names that lesson.

**N-16 — the nine new boundary units derive their boundary from `argv.len` and never assert it.** Each opens `int64:zero = argv.len - 1i64;`. The harness passes no argv, so it is 0 today. Measured: run `vec_oob_get_empty`, `vec_oob_set_empty`, `vec_oob_remove_empty`, `bytes_oob_get_empty` and `sparseset_oob_at_empty` with one argument — **all five still exit 94**, i.e. they pass while testing index 1, which is the value class the old twelve already covered. Nine units whose whole point is one value have no assertion that they are testing it. One line each (`if (zero != 0i64) { exit <n>i32; }`) closes it, and it is the same idea as `vec_oob_selfcheck_*`.

**N-17 — `RX-130` is declared superseded and its heading carries no marker.** `check_refs.py` on `nitpick-regex`: **1 finding**, `[unmarked-supersede]`, fired at `meta/DECISIONS.md:2376` and `meta/roadmap/0.0/0.0.5.md:964`; the heading is `meta/DECISIONS.md:1590`. **My view: it should not block, but it must be in the closing commit.** It is a one-line marker with a named convention (`nitpick-time`'s `> **SUPERSEDED IN PART by …**`), it misleads nobody — RX-143's text at `:2376-2381` already says exactly which sentence went and that the decision stands — and blocking a cycle on it would be disproportionate. But the gate is mechanical and now red, and a close that leaves it red is a close the next reader cannot verify. Correct form here is *in part*: only the "it never returns" sentence was superseded.

---

## THE FOUR PLACES I WAS TOLD TO PRESS — what each returned

**1. A seventh defect in `src/core/`? YES — BL-5.** Sweep with denominators. **45 `pub func` across 13 `.npk` under `src/`.** The dispatch's three candidate shapes, run down: *(a) a guard that stops but reports a code the caller mishandles* → N-14, real but not blocking. *(b) an invariant restored by one entry point and not another* → **BL-5**, and it is bigger than a missing guard: of the **10** `Vec` verbs that touch an element's storage, four account for ownership correctly (`vec_push`, `vec_pop`, `vec_insert`, `vec_free_owning`), three orphan and say so (`vec_free`, `vec_truncate`, `vec_clear`), three orphan and say nothing (`vec_set`, `vec_remove`, `vec_swap_remove`), and one — `vec_get` — silently empties the slot. *(c) a trap that leaves the container readable* → closed: a trap is a whole-program event (`npkrt.ll:2900`, frames freeze, `failsafe` runs, exit), so there is no "later call".

**2. The `pending-until` mechanism — BL-6.** Every question in the dispatch answered by measurement, and all three answers are the bad one. A marker naming a non-existent commit: accepted, inert. A marker naming a commit in the past: identical, because the commit is never read at all. A control on the denominator's exclusion: none. And *"could a real failure be silenced by marking it pending"* — yes, in one line, with the run still printing GREEN and exiting 0.

**3. Is 94 right for a freed-container misuse? Partly — N-14.** Verified against the runtime's trap-code table and the prelude's `error:` declarations at the pin rather than against any document in this repository. `OutOfBounds` is true of what the program *did*; `Unreachable` is the constant the language assigns to what *happened*. The change is defensible; the sentence defending it is not.

**4. Do the twelve new boundary units test what their names say? Yes — and they are unanimous in a new way, which is where BL-5 lives.** Checked argument by argument: all nine empty/freed-boundary units pass `argv.len - 1i64` = 0 to the entry point named in their filename, one per broken site in BL-3's table, and **each carries a distinct fall-through exit code** (51, 53, 54, 55, 56, 57, 60, 61, 62) — so if a guard vanishes they name themselves rather than collapsing into one verdict. The three selfcheck units reach `vec_oob` at −1, 0 and +1, which spans both values the new body can produce (`below = -1 - (i & 1)` ∈ {−1, −2}). The three free-path units use distinct codes 64, 65, 66. **The unanimity is not in the index — it is in the element type.** Every one of the twelve, and every one of the twelve before them, instantiates its container at a POD type. That is the same defect with a new value, exactly as the dispatch anticipated, and the value is `T`.

---

## CHECKED AND FOUND CLEAN — with denominators

I did **not** re-sweep either prior audit's clean list except where `ab93eae` touched it.

- **Baseline**: pristine `git archive` of HEAD, **141/141 in 44.8 s**, 1 PENDING printed in two places, seven tree checks, self-check 8 live / 3 pending.
- **`check_refs.py`** — 66 markdown files, leak scan **173 of 173** tracked; **one** finding, N-17.
- **The RX-143 fix is total, and I measured the two values no unit covers.** `vec_oob` at `int64` **MIN** and **MAX**, both computed at run time so neither folds: **exit 94 each**, at `-O0` and through `opt -O2`. `below = 0i64 - 1i64 - (i & 1i64)` is −1 or −2 for every `i`, so the header's *"at any `i` including `int64`'s minimum and maximum"* is true and is now measured rather than reasoned.
- **The nine repaired call sites**, re-measured through my own four-step path: `vec_get`, `vec_set`, `vec_remove`, `vec_swap_remove`, `bytes_get`, `bytes_set`, `sset_at`, `sset_contains`, `sset_insert` at the empty/freed boundary — all **94**, and the control (`drop vec_oob(0)` then `exit 50`) is 94 rather than BL-3's 50.
- **Compiler claims re-verified at `3d15ac9` from source, not from a document**: `TYPE-046` is `TYPE_MOVE_REQUIRED` and is a move-required diagnostic, not a copy refusal ✓ (this is BL-5) · `-4099 OUT_OF_BOUNDS` is defined as an index fault ✓ · `-4102 HEAP_INTEGRITY` names double-free ✓ · the prelude maps `OutOfBounds` = 4099 and `Unreachable` = 4102 *"and the runtime's integrity defects"* ✓ · `@npk_trap` freezes the program and routes to `failsafe` with no resumption ✓ · `@npk_dalloc` traps on null, misalignment and a pre-heap free ✓.
- **`vec_insert`'s shift is ownership-correct**: it moves upward into a slot that is either past `count` or already moved-from, so no live element is overwritten. `vec_pop` is correct — the move-out is the ownership transfer and `count` is decremented first.
- **`SparseSet` is unaffected by BL-5**: both its `Vec`s are `Vec<int32>`, POD, and the POD control (`zzE2`) reads the same index twice and gets the same value at both optimisation levels.
- **`main`'s `exit` path emits no scope drops** at this pin — read in the IR, and it is why an owning-element defect cannot be measured at top level. Every measurement above was taken inside a loop scope, where drops are emitted, with `NPK_HEAP_STATS` and a `/bin/true`-controlled 64 MiB cap.
- **The pending unit itself is correct**: `bytes_copy_string_empty.npk` wants exit 0 under a 64 MiB cap and gives 92; its sibling `bytes_copy_string_nonempty.npk` gives 0 under the identical cap; the `/bin/true` control passes at that cap. The finding is the mechanism, not this file.
- **The three free-path units and the three selfcheck units** were re-read and each asserts what its name says.

**Where I pressed and found nothing:** `vec_oob` under folding at both optimisation levels and at the integer extremes; the nine repaired sites; `vec_insert`'s shift; `vec_pop`'s move-out; `SparseSet`'s capacity discipline at `T = int32`; the POD instantiation across every accessor; and `bytes_copy_string`'s non-empty half under the cap.

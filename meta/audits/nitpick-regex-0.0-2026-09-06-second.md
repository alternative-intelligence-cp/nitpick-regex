# Audit — `nitpick-regex`, cycle 0.0 — SECOND PASS — 2026-09-06

**W-22 audit, filed by the eighth orchestrator (`nitpick-libs_s3`). The
auditor's final message is reproduced below in full and unedited; paths in it
are already relative because the auditor wrote them that way, having read the
first audit's header and anticipated the leak gate.**

- **Dispatched:** `npk:auditor`, `claude-opus-5`, scoped **tightly to the delta
  and to where the first audit did not press** — explicitly told not to re-sweep
  its clean list, because that list carries denominators and re-deriving it buys
  nothing.
- **Verdict: DO NOT ACCEPT — again.** Two blocking findings.
- **`BL-3` is the largest finding of the cycle** and was reached by pressing on
  target 1 (*is there a sixth defect in `src/core/`?*). The answer is yes, and it
  sits one level below the template it was given: **not a missing guard, but the
  guard's stop failing to stop.**
- **`BL-4` was introduced by the triage commit `58f5237` itself** — the fix for
  `BL-1` — and its root cause is **a compiler defect at `3d15ac9`**, raised
  separately to `nitpick-compiler_s1` under W-11 rather than worked around.

**The two findings the first audit's targets did NOT produce are worth naming,
because a scoped audit that only confirms its brief is not adversarial.**
Target 2 (BL-1's class) swept **clean** across all 62 tracked `.npk` — only two
builtins in the entire set carry a non-empty `Views` column, verified against the
*generated* table in compiler source rather than against its documentation. And
target 3 found the triage's tests **sound**: six mutations, each reverting exactly
one guard, each reddening exactly its own unit, with cross-independence checked.

---

REPORT nitpick-regex 0.0 audit (SECOND)
status: DO-NOT-ACCEPT
auditor: npk:auditor, claude-opus-5
toolchain: 3d15ac9

Both trees clean before and after — all probing was done in the session scratchpad. **Paths below are relative to the workbench root `nitpick-libs/`**, deliberately: the reference gate refuses a tracked file carrying a home directory, and this report gets filed.

# W-22 AUDIT — `nitpick-regex`, cycle 0.0 close, second pass

**Verdict: DO NOT ACCEPT.** Two blocking findings, both in `src/core/`. One is a **sixth defect** in that directory and it is the largest yet: the library's single out-of-range stop does not stop for one value, and nine accessors then fall through into the read or write the guard exists to prevent. The other was **introduced by the triage commit `58f5237` itself**.

Method note: the compiler working tree is at `c81efa5` and moved during this session (a peer is working there). Every compiler claim below was read with `git show 3d15ac9:<path>`. Every probe ran all four steps with `exit=$?` captured on its own line, at `-O0` and through `opt -O2`.

Baseline re-established first: a pristine `git archive` of HEAD in the scratchpad runs **108/108 GREEN in 34.3 s**, seven tree checks, `check_refs` clean over 65 markdown files with the leak scan now covering 155 of 155 tracked files.

---

## BLOCKING

### BL-3 — `vec_oob(0)` RETURNS. The library's only bounds check falls through at `i == 0`, and nine `pub` functions then perform the access they had just refused.

`nitpick-regex/src/core/vec.npk:162-168`:

```
pub func:vec_oob = NIL(int64:i) never fails {
    int64[1]:guard = [0i64];
    discard(guard[i]);
    pass NIL;
};
```

The trap is spelled as an out-of-range index into a one-element fixed array. **Index 0 is in range.** And every call site is `drop vec_oob(...)` — `drop` discards and *continues*, so a `vec_oob` that returns is a guard that does nothing.

Measured, with controls, at `3d15ac9`:

| probe | result |
|---|---|
| `q1` — `drop vec_oob(0)` then `exit 50` | **exit 50** — the stop did not stop |
| `q2` — `vec_oob(1)` (control) | exit 94, `OutOfBounds` |
| `q3` — `vec_oob(-1)` (control) | exit 94, `OutOfBounds` |

Identical at `-O0` and through `opt -O2`.

**What the documents claim, all three false at the pin:**

- `src/core/vec.npk:146` — "THE OUT-OF-RANGE STOP, FOR THE WHOLE `core` LAYER. **Never returns.**"
- `meta/DECISIONS.md:1599` (RX-130, declared 2026-09-06) — "The helper is `vec_oob`, **it never returns**".
- `meta/specs/SAFETY.md:355` — "**A VIOLATION TRAPS `OutOfBounds` (RX-130)**", unqualified, naming `vec_get`, `vec_set`, `bytes_get` and `bytes_set`.
- The stated obligation `never fails ensures false` (`src/core/vec.npk:157`) is false for `i == 0`.

**The full extent, measured rather than reasoned.** 28 `vec_oob` call sites under `src/`. **19 are sound** — they pass a strictly negative value (`i < 0` arms, `v.cap - 1` with `cap <= 0`, `v.count - 1` with `count <= 0`, `need < 0`, `n < 0`) or a value ≥ 1 (`vec_insert`'s `i > v.count`). **9 are broken** — every guard of the form `i >= <count|len>` where the container is empty and the index is 0:

| entry point | site | measured |
|---|---|---|
| `vec_get` | `vec.npk:231` | `r1` — empty `Vec`, `vec_get(v,0)` **returned a word**, exit 51 (no trap) |
| `vec_set` | `vec.npk:238` | `r4` — **freed** `Vec`, `vec_set(@v,0,999)` **completed the write through a dangling `items`**, exit 62 |
| `vec_remove` | `vec.npk:308` | `r2` — empty `Vec`, `vec_remove(@v,0)` fell through and set **`v.count = -1`**, exit 60 |
| `vec_swap_remove` | `vec.npk:326` | same shape; reads `items[-1]`, writes `items[0]`, `count` → −1 |
| `bytes_get` | `bytes.npk:139` | `r5` — empty `Bytes`, returned a byte past `len`, exit 53 |
| `bytes_set` | `bytes.npk:146` | writes past `len` (inside `cap`, so a wrong answer rather than corruption) |
| `sset_contains` | `sparseset.npk:106` | falls through into `vec_get(s.sparse, 0)` on a freed block |
| `sset_insert` | `sparseset.npk:122` | same |
| `sset_at` | `sparseset.npk:146` | `r6` — empty live `SparseSet`, `sset_at(@s,0)` **returned a phantom member**, exit 55 |

`r3` chains it: after `vec_remove(@v,0)` leaves `count == -1`, `vec_push`'s guard reads `-1 >= 4` → false → the element is written at **`items[-1]`, before the block**, and the damage surfaces only later as **exit 95** when `vec_free`'s `dalloc` finds the heap header corrupted. That is verbatim the `vec_init_zeroed(-5)` shape RX-139 closed three commits ago, reached by a second route the sweep did not cover — and `sset_at`'s phantom member is verbatim the failure `src/core/sparseset.npk:43-45` names in its own header: *"a wrong sparse-set probe adds a thread for a state the automaton is not in and the library returns a match that is not there."*

**Why 108/108 is green over it.** All **12** out-of-range unit programs pass a non-zero argument, checked one by one:

| unit | argument reaching `vec_oob` |
|---|---|
| `vec_oob_get_at_count` | `v.count + past` = 3 |
| `vec_oob_set_at_count` | `v.count + past - 1` = 1 |
| `vec_oob_get_negative` | `0 - past` = −1 |
| `bytes_oob_get_at_len` | `len + past - 1` = 2 |
| `bytes_oob_set_negative` | `0 - past` = −1 |
| `bytes_oob_get_after_clear` | 3 |
| `sparseset_oob_insert` | `capacity + past - 1` = 16 |
| `vec_oob_pop_empty` | `count - 1` = −1 |
| `vec_oob_reserve_freed` / `push_freed` / `insert_freed` | `cap - 1` = −1 |
| `vec_oob_init_zeroed_negative` | −5 |

Twelve of twelve avoid the one argument at which the stop does not stop. `meta/specs/SAFETY.md:363-365` enumerates "Four cases are gated ... `i == count`, a negative `i`, the write side of `i == count`, and a pop from empty" — and reads as exhaustive. **`i == count == 0` is the fifth, and it is the unguarded one.**

**What would resolve it.** A `vec_oob` whose index is out of range for *every* `i` including 0, still non-constant so the optimiser cannot fold it (the reason `i` is a parameter at all is stated at `vec.npk:147-148`, and that reason survives); the three false "never returns" sentences corrected; and — the part that matters more than the fix — **a unit per affected entry point at exactly the empty-container boundary**, since twelve out-of-range units all missed it. A single self-check case asserting `vec_oob(k)` does not return for `k ∈ {-1, 0, 1}` would have caught this and would catch the next spelling.

---

### BL-4 — the BL-1 fix leaks. `bytes_copy_string` on an empty `Bytes` leaks 32 bytes per call, `exit 0` cannot see it, and the sentence in the tree justifying it is false at the pin.

`src/core/bytes.npk:343-345`, the RX-138 fix:

```
pub func:bytes_copy_string = string(Bytes->:b) never fails {
    pass string_concat("", string_from_bytes(b.buf.ptr, b.len));
};
```

The copy itself is **correct and I verified it three ways** (see the clean list). The defect is the empty path.

`src/core/bytes.npk:339-342` states:

> An empty `Bytes` is not a special case: `string_concat` of two empty strings **allocates zero bytes** and returns cap 0, which **the drop correctly frees nothing for**. Measured — `bytes_clear` then this, then `string_byte_length` == 0 and `string_equals("")`, exit 0.

**Both halves are false, and the third sentence describes a measurement that is not in the tree.**

At the pin, `runtime/npkrt.ll:6376` — `@npk_string_concat` has **no empty short-circuit**: it computes `n = al + bl`, calls `npk_alloc_internal(n)` unconditionally, memcpys both operands, and returns `{p, n, n}`. For `n == 0` that is cap 0. And `runtime/npkrt.ll:4808-4811`, `@npk_alloc_impl`:

```
  ; alloc(0) is a real, unique, freeable 16-byte block (D-150) -- a trap here
  ; would make every `alloc(count * elem)` with a legal zero count a landmine
  %n1 = select i1 %z, i64 16, i64 %n
```

So a real block is allocated and the cap-0 "not-mine bit" makes the drop free nothing.

**Measured with the repository's own instrument** — the memory cap `vec_owning_leak.npk`/`vec_owning_freed.npk` use, since `SAFETY.md` S-22 says `exit 0` proves nothing about a managed body:

| program | 2M calls, peak RSS | 4M | 8M | 8M under `ulimit -v 64MiB` |
|---|---|---|---|---|
| `bytes_copy_string` on an **empty** `Bytes` | 62 592 KiB | 125 568 KiB | 251 136 KiB | **exit 92, `HeapOom`** |
| control — same, 5-byte `Bytes` | 0 | 0 | 0 | **exit 0** |
| `/bin/true` under the same cap | — | — | — | exit 0 |

Linear in the call count: **32.2 bytes per call**. Identical through `opt -O2`. Attributed exactly: `string_concat("", "")` in a bare loop with no library code reproduces it (exit 92, 62 592 KiB); `string_concat("", "a")` does not (exit 0, 0 KiB).

**The root cause is a compiler defect at `3d15ac9`, and the asymmetry is documented in the compiler's own source.** `@npk_string_slice` (`runtime/npkrt.ll:6530-6532`) has exactly the branch `string_concat` lacks:

```
  ; there. An empty slice allocates nothing: len 0 is never dereferenced,
  ; and cap 0 gives the drop nothing to free.
  %none = icmp eq i64 %n, 0
```

The compiler took explicit care of this hazard in one primitive and not the other. And RX-138's stated reason for choosing `string_concat` over `string_slice` was that `string_slice` returns a `Result` — the `Result` is the price of the primitive that handles the empty case correctly.

**Why this blocks rather than carries.** Its blast radius today is nil — `bytes_copy_string` is not in `src/lib.npk`, and `API.md` A-12 keeps output in a caller-owned `Bytes`. So did BL-1's, and the first audit blocked on it. What blocks here is the shape: a defect **introduced by the commit under audit**, invisible to a 108-green suite for exactly the reason this repository already wrote down, justified in the tree by a **claim about the compiler that its primary source contradicts**, and cited to a measurement (`exit 0`) that S-22 says is the wrong instrument. Cycle 0.1's parser and 0.6's replacement are its first users, and "the result is empty" is the ordinary case for a replacement that deletes or a capture that matched nothing.

**What would resolve it.** (i) Correct `src/core/bytes.npk:339-342` — the claim, and the citation of an `exit 0` measurement for a managed body. (ii) **Raise the compiler defect**, with the two-line reproduction and the `string_slice` asymmetry, as a numbered open question; `CLAUDE.md` says never work around one, so the library-side guard (`if (b.len == 0i64) { pass ""; }`) is a decision to take deliberately and record, not a silent patch. (iii) Add the memory-cap pair for `Bytes` that `Vec` already has — `bytes_unit.npk:218-221` says in as many words that `exit 0` proves nothing here, and nothing else covers it.

---

## NON-BLOCKING (carry into 0.1)

**N-10 — `check_dated_measurements`, built to answer N-9, cannot see the one file its own docstring names.** `harness/treecheck.py:627` declares `.yml` in `_UNDATED_EXTS`; line 659 prunes every dotted directory (`dirnames[:] = [d for d in dirnames if not d.startswith(".")]`), so `.github/` is unreachable. The tree's only tracked `.yml` is `.github/workflows/ci.yml`. Instrumented: the walk opens **115 files, 0 of them `.yml`, 0 under `.github/`**, and reports `failures: []`. The check's own regex finds **two matches in that file** — `ci.yml:221` (`at this pin`) and `ci.yml:253` (`at the pin`). The docstring's scope sentence reads: *"What is IN scope is ... the harness, `src/`, the probe headers, the manifest **and the workflow**."* Corroborating: `_UNDATED_SKIP_DIRS`' entries `".internal/"` and `".git/"` are dead code, already removed by the prune — evidence the author expected the skip list to do that work. This is finding-shape N-6 (rule wider than mechanism) in the check written to close N-9. Fix: skip by name, not by leading dot, or add `.github` back explicitly; then the two `ci.yml` lines need dating.

**N-11 — `src/core/vec.npk:102` and `meta/DECISIONS.md:2211` say "`cap <= 0` traps `OutOfBounds` through `vec_oob`, like every other misuse in this file". It is not true of the free paths.** Measured: `vec_free` twice → **exit 95, `Unreachable`**; `vec_free_owning` after `vec_free` → **95**; `sset_free` twice → **95**. They stop, deterministically, but on the allocator's double-free check and reporting `Unreachable` — which is precisely the "they report the wrong thing" complaint the same header makes at lines 88-90 about `vec_push`/`vec_insert`, fixed there and not here. Lower severity than BL-3 (it stops), same class.

**N-12 — the RX-138 comment cites a measurement absent from the tree.** `src/core/bytes.npk:341-342` reports "Measured — `bytes_clear` then this ...". No committed test calls `bytes_copy_string` on an empty `Bytes`: the eleven call sites in `bytes_unit.npk` all follow an `extend`/`put_uint`. Folded into BL-4's remedy.

---

## THE FOUR PLACES I WAS TOLD TO PRESS — what each returned

**1. A sixth defect in `src/core/`? YES — BL-3.** Sweep, with denominators. **45 `pub func` across 13 `.npk` under `src/`** (byteset 11, bytes 11, sparseset 8, vec 15; `core.npk`, `limits.npk`, `api.npk`, `lib.npk` declare none). **7 assign a parameter into a struct field** — `vec_init`'s `cap`, `vec_init_zeroed`'s `n`, `vec_truncate`'s `n`, `bytes_init`'s `cap`, `sset_init`'s `cap`, `vec_set`'s `x`, `bytes_set`'s `x` — and **all 7 are guarded or floored**; the RX-139 template is exhausted. The defect was one level below it: not a missing guard, but **the guard's stop failing to stop**, which no amount of sweeping for missing guards would find. Two further candidates were run down and closed clean: `vec_init_zeroed` hands `k * #size_of<T>()` to `calloc` where `vec_init` does the multiply under D-210 — but `@npk_calloc` (`runtime/npkrt.ll:4891`) checks it with `llvm.umul.with.overflow.i64` and traps `npk_heap_badreq`, so no undersized allocation wearing a plausible size; and `bytes_copy_string` is NUL-clean (embedded 0, `string_byte_length == b.len`, survives a growth, exit 0).

**2. BL-1's class, swept. Clean.** At the pin, `meta/specs/BUILTIN_REFERENCE.md`'s `Views` column is non-`—` on exactly **two rows of the whole builtin set** — `string_bytes` (1) and `string_from_bytes` (1) — and I confirmed the document against the **generated** table rather than trusting it: `git show 3d15ac9:src/frontend/builtins.npk:151` `builtin_views` returns `1i32` for those two names and `0i32` for everything else. Of the **45** `pub func`, **4** return an expression containing a compiler primitive: `vec_init` (`alloc`, `—`), `vec_init_zeroed` (`calloc`, `—`), `bytes_init` (`buffer_new`, `—`), `bytes_copy_string` (`string_concat`, `—`). Grepping all **62 tracked `.npk`** for `pass`/`give` of either view primitive returns exactly one line, `bytes.npk:344`, where the view is an **argument**. **No other borrowed view escapes as an owned value.**

And the fix itself is a genuine copy, verified three ways rather than assumed: the runtime body allocates and memcpys unconditionally with no identity short-circuit (`npkrt.ll:6376`); the constant folder cannot rewrite it, because `fold_string_builtin`'s `string_concat` arm (`src/frontend/type_resolve.npk:1408-1414`) requires **both** operands to fold to `CV_STRING` and returns `cv_none()` otherwise, so `string_concat("", <runtime value>)` never folds; and reverting the body to `string_from_bytes` alone reproduces **exit 46** on the committed `bytes_unit.npk`.

**3. Did the triage's own fixes introduce anything? One did — BL-4. The tests are sound.** All six mutations run against a scratchpad copy, each reverting exactly one thing:

| mutation | unit | result |
|---|---|---|
| `vec_reserve`'s `cap <= 0` guard deleted (`vec.npk:208`) | `vec_oob_reserve_freed` | 94 → **124** (the hang, reproduced) |
| `vec_push`'s guard deleted (`vec.npk:248`) | `vec_oob_push_freed` | 94 → **91** |
| `vec_insert`'s guard deleted (`vec.npk:282`) | `vec_oob_insert_freed` | 94 → **91** |
| `vec_init_zeroed`'s `n < 0` deleted (`vec.npk:391`) | `vec_oob_init_zeroed_negative` | 94 → **50** |
| `bytes_clear` made a no-op | `bytes_oob_get_after_clear` | 94 → **31**, its own distinct code |
| `bytes_copy_string` → the view | `bytes_unit` | 0 → **46** |

Cross-independence checked: mutation 1 left `vec_oob_push_freed` at 94, mutation 2 left `vec_oob_insert_freed` at 94 — the per-entry-point claim in those headers holds. `harness/baseline/rx120.sh` is wired as both a harness build step (`harness/build.py:402`, `run.py:214-248`) and a CI step (`ci.yml:254`); in the real tree both pins are present and it asserts **eleven** legs and exits 0; planting `expect_count floor 3` reddens it at exit 1 with a message naming the right next action; and it announces a skipped leg as *not* a pass. The new tree check is the one that carries a defect — N-10.

**4. The nine non-blocking findings — read from the tree, not the report. Eight genuinely discharged, one discharged with a hole.**

| | claimed | verified against the tree |
|---|---|---|
| N-1 | FIXED | ✓ `TESTING.md:198-211` now has a `Built` column, 14 rows, each unbuilt row naming its owning cycle; "Seven run on every full invocation" matches |
| **N-2** | FIXED | ✓ **and correct.** `CLAUDE.md:19` and `:248` both say **seven**; `treecheck.ALL` is 7; `ci.yml`, `0.1.0.md`, `ROADMAP.md` agree. One statement of each count, as claimed |
| **N-3** | MOOT | ✓ **and the number reproduces.** Archive reversed, `meta/roadmap/done/` holds only its README. The replacement note's "**33** citations of `meta/roadmap/0.0/X`" — I re-derived at the archived commit `20bdcea`: **33 occurrences, 32 lines, 9 files**, matching the first audit exactly. The counting error in the document about counting is fixed with a number that checks out |
| N-4 | FIXED | ✓ `API.md:164` is `raw bytes_init(64i64)`; `bytes_new` appears nowhere in 155 tracked files except the note recording its removal |
| N-5 | FIXED | ✓ `vec_unit.npk:21` names the real pair and says why `check_refs` could not see it |
| N-6 | FIXED | ✓ `SAFETY.md:325-326` now reads "anywhere under `src/`", the check's actual scope |
| N-7 | DEFERRED | ✓ discharged by the workbench: `check_refs` reports clean over 65 markdown files, **leak scan 155 of 155 tracked** |
| N-8 | FIXED | ✓ `bytes_unit.npk:195` pushes `(k & 255i64)` and asserts five distinct values at indices 0 / 255 / 256 / 500 000 / 999 999 |
| **N-9** | FIXED + RULE | partial — the 17 live sites are dated, the check is registered and fails on its own regex, **but see N-10**: it cannot reach `.github/`, and two live violations sit there |

---

## CHECKED AND FOUND CLEAN — stated with denominators

I did **not** re-sweep the first audit's clean list except where `58f5237` touched it. New ground:

- **Harness, from a pristine `git archive` of HEAD in the scratchpad**: 108/108 in 34.3 s, self-check first, eight kinds of wrong expectation each requiring a red, three legs honestly printed PENDING.
- **`check_refs.py`** — clean; 65 markdown files; leak scan 155/155.
- **`rx120.sh`** — both pins present in the real tree; 11 assertions; reddens on a planted fault; skipped legs announce themselves.
- **Compiler claims re-verified at `3d15ac9` from source, not from a document**: `builtin_views` returns non-zero for exactly two names ✓ · `@npk_string_concat` allocates and copies unconditionally, returns `{p,n,n}` ✓ · `fold_string_builtin`'s `string_concat` arm requires both operands constant ✓ · `@npk_calloc` checks the multiply with `umul.with.overflow` and rejects negatives ✓ · `@npk_alloc_impl` substitutes 16 for a zero request ✓ · `@npk_string_slice` short-circuits an empty result and `@npk_string_concat` does not ✓ · `@npk_ralloc` refuses `ralloc(p, 0)` ✓.
- **`Vec`'s `count <= cap` invariant** — traced through all 15 `pub func`; no path produces `count > cap` now that `vec_init_zeroed` guards its negative. `count < 0` **is** producible, but only through BL-3.
- **`SparseSet`'s capacity discipline** — `s.count` cannot exceed `dense.count`: keys are bounded by `sparse.count == dense.count == n`, inserts are idempotent, and a full set short-circuits. Re-derived independently including the clear-then-reinsert-in-a-different-order case, which the standard invariant survives.
- **`bytes_reserve`'s postcondition** `b.buf.len >= b.len + need` — holds; `buffer_new(nc)` gives `len == cap == nc`; the `mcpy` copies `b.len` and never `b.buf.len`; no self-aliasing route exists into `bytes_extend` now that `bytes_copy_string` copies.
- **`bytes_put_uint`** — no `/`, no `%`; the power table is built, not spelled; the digit loop's `d` cannot exceed 9, so `d + 48u8` cannot overflow.
- **`ByteSet`** — the `>>6` / `&63` substitutions are exact for `uint8`; `byteset_next` handles `from` outside `[0,256]` on both sides.
- **Decisions and questions** — RX-138 … RX-142 each declared once in `meta/DECISIONS.md` and cited in 2–7 other files; O-N17 raised with its reproduction.
- **The negative-guard family** — sound. `vec_oob(-1)` and `vec_oob(-5)` both trap 94; the 19 sound call sites are exactly the ones that can only pass a negative or a value ≥ 1.

**Where I pressed and found nothing:** `vec_init_zeroed`'s deferred multiply (the runtime checks it); `bytes_copy_string` with an embedded NUL and across a growth; `mcpy` overlap in `bytes_extend`/`bytes_extend_str` (no route from a `Bytes` to a slice over its own body); `vec_pop`/`vec_get`/`vec_set` on a freed `Vec` at any **non-zero** index (all trap 94); `sset_contains` on a freed `SparseSet` at a non-zero key (traps 94); `byteset_*` at every boundary; the seven parameter-into-field sites; and the `Views` class across all 62 tracked `.npk`.

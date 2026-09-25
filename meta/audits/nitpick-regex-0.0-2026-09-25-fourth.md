REPORT nitpick-regex 0.0 audit (FOURTH)
status: DO-NOT-ACCEPT
auditor: npk:auditor, claude-opus-5-5
toolchain: c3bdae2
scope: ab93eae..4420c45 (15 commits: 0.0.4b, 0.0.4c, and 0.0.5's triage of the third pass)

Paths are relative to the workbench root, the directory holding `BOARD.md`. That is deliberate: this message is filed verbatim, and the reference gate refuses a tracked file that contains a home directory. The compiler is `../nitpick`. Every compiler claim below was read at `c3bdae2` with `git show`; its working tree was at `2cd5176` and later moved to `8fbde77` through another session's commits. My probes ran in a session scratchpad that will not survive, so every reproducer that carries weight is inline. I wrote nothing: `nitpick-regex` stayed clean at `4420c45` throughout, and the workbench and compiler trees are clean. Wall clock was 14:45–15:17 EDT. earlyoom sent no signal after 14:40.

# W-22 AUDIT — `nitpick-regex`, cycle 0.0 close, fourth pass

## Verdict: DO NOT ACCEPT

There are two blocking findings. In both, a sentence in the triage closes a hole and a measurement reopens it.

- **BL-7 — a red unit can leave the count without a marker.** A block comment in a sibling unit takes a failing unit out of a GREEN run: `173/173`, exit 0, with no marker and no line in `PENDING.txt`. The triage looked at this route, called it "closed by the language", and used that to decline the third audit's remedy (iv), a check on the judged-unit count.
- **BL-8 — N-15 is deferred on a false premise.** "Nothing in the library copies a `Vec` before cycle 0.8" is wrong three ways:
  - `COMPILE.md` declares `Program`, which holds three `Vec`s, "copyable" at cycle 0.6.
  - Subcycle 0.7.0 swaps two `SparseSet`s every byte.
  - R-8's capture copy is subcycle 0.7.2, not cycle 0.8.

  N-15 also reaches further than recorded. Through a whole-`SparseSet` copy, a double free exits 95, and a read after the free silently reports an inserted key as absent. Through a by-value parameter, a callee can free its caller's `Vec`.

There are six non-blocking findings:

- **N-18:** the new S-23a check misses twelve shapes. Eleven compile and run, and six of those show BL-5's move-out. `SAFETY.md` S-23a and `0.1/0.1.0.md` state the check's enforcement without qualification.
- **N-19:** a pending unit skips the −O2 leg, the optimised B-2 scan and `stress`.
- **N-20:** neither reviewed list's second direction is tested by anything.
- **N-21:** a compiler-defect candidate. For a generic instance, `npkc` exits 0 but emits the type definition after its first use, and `llc` refuses the IR. This is for the compiler seat now; it does not block this close.
- **N-22:** TYPE-083 and DEF-96 are stated as current compiler behaviour, but neither exists in the compiler's tree, at the pin or at its HEAD.
- **N-23:** stale counts and two over-wide claims.

How the third pass's findings stand against the tree:
- BL-5, N-13, N-14, N-16 and N-17 hold as recorded.
- BL-6 holds for what its three cases cover; BL-7, N-19 and N-20 are the gaps around it.
- N-15 is BL-8.

**Method.** The baseline was a fresh `git clone` of `4420c45` in the scratchpad, using the pinned toolchain. `npkc` `5fd636b9…` and `npkrt.o` `162b8975…` match `SHA256SUMS`, and LLVM is 20.1.2. Result: **174/174 GREEN in 72.3 s, exit 0**, self-check 11 live / 4 pending, eight tree checks, rx120 green, and 9 of 9 residue entries referenced. Every mutation was a full run, or a self-check run, over a separate clone. Every probe went through all four steps (`npkc`, `llc`, `ld.lld`, run) at −O0 and through `opt -O2`.

---

## BLOCKING

### BL-7 — A red unit leaves a GREEN run's count through a block comment in a sibling file. The route the triage declared closed is open in the harness.

Severity: **contradiction**. Measured.

**What the tree claims:**
- `nitpick-regex/meta/roadmap/0.0/0.0.5.md:1436-1443` says remedy (iv) "is met by the list rather than by a committed total". It adds that the only other way a program-stage unit could leave the count, "a sibling importing it", "is closed by the language: a file with `main` and `failsafe` imported by another is refused `NITPICK-RESOLVE-013` (D-248) at `c3bdae2`, so the importer is red."
- RX-154 (`nitpick-regex/meta/DECISIONS.md:3100-3102`): "Taking a unit out of the count is then two edits in two files, one of them a reviewed line with a reason."
- `nitpick-regex/harness/run.py:41-44`: "…so one comment line cannot move a red out of a green run."

**The mechanism.** `nitpick-regex/harness/stages.py:60-85` (`imported_by_others`, `_uses`) treats any line whose stripped text starts with `use "` as an import. That includes a line inside a `/* … */` block comment or a `"""` block string. Both are in the language at `c3bdae2`: `../nitpick/meta/specs/LEXICAL_REFERENCE.md` §2 defines `BlockComment ::= "/*" … "*/"`, and §6.3 defines block strings. `run_entry` (`stages.py:441-445`) skips every file matched this way in a program suite. The parse sweep then compiles that file with `npkc` only; it is never linked, run or judged.

**Measured.** This is a full run over a fresh clone of `4420c45`, using the third audit's own M3 unit. `tests/unit/bytes_oob_get_empty.npk` had `expect-exit: 94` changed to `77` (the file really exits 94). In `tests/unit/vec_unit.npk`, after `mod:vec_unit;`, I added:

```
/*
use "bytes_oob_get_empty.npk".*;
*/
```

Result: `unit (program) 43 unit(s)` (the baseline has 44), `173/173 unit(s) passed in 72.0 s.`, `GREEN.`, exit 0. The red unit's only line in the log is the parse sweep's `ok`. There is no marker and no `PENDING.txt` line: **one edit, in a file other than the red one.**

**The control shows that the language half of the claim is true, and that the harness disagrees with it.** A real `use "./zzb.npk".*;` of a file that declares `main` is refused `NITPICK-RESOLVE-013` twice, once for `main` and once for `failsafe`. The same line inside `/* */` compiles, links and runs at exit 0 at both levels. So the compiler sees no import, while `imported_by_others` sees one.

**A related weakness.** The harness has three import readers, and they disagree:
- `stages._uses` and `build.reaches_src` (`nitpick-regex/harness/build.py:391-398`) match only `use "`, so they miss `pub use`.
- `treecheck._USE` (`treecheck.py:52`) matches both forms.
- None of the three skips comments or string literals.

**Why this blocks.** This is exactly what the third audit blocked BL-6 on: "one comment line moves an ordinary red out of a GREEN run's denominator". It now appears in the fix for BL-6. The triage looked at this route, declared it closed, and on that basis declined the third audit's remedy (iv), a check on the judged-unit count. The safety property the tree states is false at the pin.

**What would resolve it:**
1. A file in a program suite that declares `func:main` is never skipped. Skipping one is a failure. Alternatively, assert per suite that judged + pending equals the number of files declaring `main`. D-248 already makes a real import of such a file red, so this costs nothing legitimate. It is computed from the tree, not a committed total.
2. One shared import reader that blanks `//`, `/* */` and every string form, and reads `pub use` as well.
3. A self-check case in which a sibling's block comment names a red unit, and the run must go red.
4. Correct RX-154 with a superseding note, and correct `run.py:41-44`, `PENDING.txt:16-19` and, in a later record, §10's sentence.

### BL-8 — N-15's disposition rests on a false premise and understates the reach. The question put to the author is framed on facts that do not hold.

Severity: **contradiction**. This blocks as a defect in the triage, not as an order to fix N-15. W-22 requires every finding triaged, and this triage's stated reason is false.

**(a) When the first copy happens.** The claim appears in RX-156 (`nitpick-regex/meta/DECISIONS.md:3301-3303`), `0.0.5.md:1471` and `0.0.5.md:1639` (the last is inside a committed REPORT block, so it is corrected in a later record under W-28). It is on the board's question 9 row, and in this dispatch's own notes: the one place the specification copies a `Vec` is R-8, "cycle 0.8". Against the tree:
- **`nitpick-regex/meta/specs/COMPILE.md:24-37`** declares `Program = { Vec<Inst>:insts; Vec<ByteSet>:classes; Vec<uint8>:byte_classes; … }` and says: *"A `Program` is therefore **copyable, comparable, and dumpable** — which is what makes a compiled program a committed fixture."* Copying a `Program` is three whole-`Vec` copies. It is built at **cycle 0.6** (`ROADMAP.md:61`). The triage's sweep phrases could not match "copyable".
- **`nitpick-regex/meta/specs/ENGINES.md:49-50`**: "Two `SparseSet`s (the current thread list and the next), **swapped each byte**". `nitpick-regex/meta/roadmap/0.7/README.md:14,25` schedules this as subcycle **0.7.0**. A swap through a temporary is a whole-`SparseSet` copy, which is two `Vec` headers.
- R-8's capture copy is `0.7/README.md:40`, subcycle **0.7.2**. Cycle 0.8 is the lazy DFA (`ROADMAP.md:63`).
- From 0.1 on, any struct holding a `Vec` is silently copyable. The parser's state holds a `Vec<Frame>` (`SYNTAX.md:99`).

**(b) The reach.** Measured at `c3bdae2`; the results were the same at −O0 and through `opt -O2`.

| shape | result |
|---|---|
| `Vec<int64>:w = v;`, then `vec_free(@v)` and `vec_free(@w)` | **95**, matching the triage |
| same, then `vec_get(w, 0i64)` after the free | **170**, the free poison, matching the triage |
| **`SparseSet:t = s;`**, then `sset_free(@s)` and `sset_free(@t)` | **95** |
| **`SparseSet:t = s;`**, `sset_free(@s)`, then `sset_contains(@t, 3i64)` and `sset_len(@t)` | **false and 1** (exit 21). The inserted key reads as absent while the count says one member. **A silent wrong answer from freed memory, with no trap**, in the engines' core structure |
| **`func:consume = NIL(Vec<int64>:v) never fails { drop vec_free(@v); pass NIL; };`**, then the caller's `vec_get(v, 0i64)` | **170**. No copy binding is needed: a by-value parameter is a second handle, and the callee may free through it |
| `Bytes:c = b;` | refused `NITPICK-TYPE-046` (`Bytes` holds a `buffer`), so `Bytes` is outside N-15 |

The tree states the reach as "a whole-`Vec` copy" only, at:
- `nitpick-regex/src/core/vec.npk:141-158` and `:229-233`
- `SAFETY.md:427-429` and `:494-499`
- `VERIFICATION.md:98-103`
- `DECISIONS.md:3292-3303`

One consequence the recommendation does not mention: `vec_get` takes `Vec<T>:v` **by value** (`vec.npk:390`), and `sparseset.npk` reads `vec_get(s.sparse, k)` by value, as `CLAUDE.md` prescribes. So "move-only by construction" changes `vec_get`'s signature and every by-value read in `src/core/`. That is an API change to this cycle's own deliverable.

**(c) The next cycle is not told.** `nitpick-regex/meta/roadmap/0.1/0.1.0.md` does not mention N-15, question 9, header copies or move-only; I checked with grep. Yet cycle 0.1 builds the first struct that holds a `Vec`.

**What would resolve it.** Correct the premise and the reach:
- RX-156, by a superseding dated note.
- §10, by a later record.
- `COMPILE.md:35`, flagged as depending on question 9's answer either way.
- `0.1.0.md`, which should carry N-15.
- The board row (the orchestrator's).

Then put the corrected facts to the author.

## N-15 AND W-22 — the question put to this audit

**Does W-22 allow the close with N-15 open? Procedurally, yes.**
- W-22 (`WORKSTREAMS.md:208-211`) requires every finding to be triaged, not fixed.
- The worker skill defines triage as "fixed, or declined with a reason".
- This cycle's first triage used "deferred to a named cycle with a reason" (`0.0/README.md:430-432`), and the next audit accepted that.
- The third audit filed N-15 under "NON-BLOCKING (carry into 0.1)".

**But a deferral is only as good as its reason, and this one's reason is false** (BL-8).

**My view: do not close on the current record.** Close with N-15 open only after two things:
1. The premise and the reach are corrected as above.
2. The author has answered question 9 with those facts.

If the answer is **move-only**, land it **before** the close, as a 0.0.4d, not after it:
- It changes `vec_get`'s signature and every by-value read in `src/core/`, which is the deliverable this cycle closes on.
- Every later cycle adds call sites.
- The first struct holding a `Vec` arrives in 0.1.
- The specification's "copyable `Program`" at 0.6 depends on the answer.

If the answer is **accept and document**, the close can proceed once the documentation states the full reach and `COMPILE.md:35` says what "copyable" means for a `Program`. The full reach includes `SparseSet`, by-value parameters, and the silent wrong answer.

I lean to "before the close" for two reasons. The board's own row notes that "the author's standing call on memory safety may weigh the other way". And W-27 (`WORKSTREAMS.md:239-245`) records that the author overruled "conformance rather than a block" for O-N9, a use-after-free guarded only by a rule. A silent wrong answer in the Pike VM's thread-set structure is the same class.

---

## NON-BLOCKING

### N-18 — `check_vec_elements_own_nothing` misses twelve shapes, eleven of which compile and run. S-23a, RX-155 and `0.1.0.md` state its enforcement without the limit.

Severity: **contradiction**.

**What the tree claims:**
- `SAFETY.md:515-517`: "`check_vec_elements_own_nothing` enforces it over `src/`".
- `0.1/0.1.0.md:163-166`: "so an AST node or a parser `Frame` holding a `string` is a red run".
- The check's docstring (`treecheck.py:610-614`) states only one limit, a generic's `Vec<T>`. It also calls that `Vec<T>` "judged where it is instantiated", but nothing judges `Stack<string>`.

**The mechanism**, in `nitpick-regex/harness/treecheck.py`:
- `_OWNS` (lines 540-542) is a nine-word denylist, matched as whole words.
- A name is followed only if it is Capitalised (`_NAME`, line 545) and declared under `src/` by `struct:`/`enum:`.
- Where two declarations share a name, the first one wins (`setdefault`, line 633).
- `Vec<` is found only when the `<` follows immediately (line 556).
- `vec.npk` is skipped as a whole file (lines 636-637).
- Prose is blanked per line, handling only `"` (`_blank_prose`, lines 362-396).

**Plants.** Each plant was a copy of `src/` with one change, judged by the check function itself. The controls reproduce the triage exactly: its four positive plants FAIL, and its comment plant and POD plant pass. I then built each shape as a program at `c3bdae2`. "Second read EMPTY" means the program pushed one owning element, called `vec_get` twice, and found the second result empty: BL-5's move-out.

| # | shape | check | as a program |
|---|---|---|---|
| M1 | `struct:frame = { string:s; … }` and `Vec<frame>` (a lowercase name; the compiler's TYPE_REFERENCE itself has `pub struct:vec9`) | ok | runs; **second read EMPTY** |
| M2 | `Vec<Path>`, the prelude's `pub struct:Path = { string:text; }` | ok | runs; **second read EMPTY** |
| M3 | `Vec<ByteReader>`, a prelude type holding an `OwnedFd` | ok | compiles, runs |
| M4 | a `src/` enum `Tok = { Word(Path); Num(int32); }` and `Vec<Tok>` | ok | runs |
| M5 | a `src/` struct holding `arena<int64>`, in a `Vec` | ok | runs |
| M6 | a `src/` struct holding `wildx uint8->` (`\bwild\b` does not match `wildx`) | ok | runs |
| M7 | `struct:Stack<T> = { Vec<T>:v; … }` and `Stack<string>` | ok | runs; **second read EMPTY** |
| M8 | a generic function with a `Vec<T>` local, called `::<string>` | ok | `npkc` 0, `llc` refuses (see N-21) |
| M9 | `Vec <string>` (a space before `<`) | ok | runs; **second read EMPTY** |
| M10 | a non-generic `struct:VecNames = { Vec<string>:names; }` appended to `vec.npk` | ok | runs; **second read EMPTY** |
| M11 | a POD `Frame` in `src/compile/`, and an owning `Frame` with `Vec<Frame>` in `src/syntax/` | ok; it FAILs once the POD namesake is removed | runs; **second read EMPTY** |
| M12 | `char8:q = '"';` earlier on the same line as a `Vec<string>` | ok | runs |

At `c3bdae2` the compiler's owning kinds (`../nitpick/src/frontend/types.npk`, `type_drops_recorded`) are twelve, plus aggregates of them:
- `string`, `buffer`, `dyn`, `OwnedFd`
- `arena`, `shared_arena`
- `Mutex`, `Guard`, `RwLock`, `RGuard`, `CondVar`, `Barrier`

`_OWNS` names four of them.

Blast radius today is nil: `src/` has no generic outside `vec.npk` and no lowercase type (checked with grep). But `0.1.0.md` tells cycle 0.1's worker to rely on the check.

A stale claim sits alongside: `treecheck.py:606-607` still says every `Vec` the specification declares "already owns nothing (C-1, H-2, R-8)". Commit `4420c45` narrowed that claim everywhere else but did not touch this file.

**What would resolve it.** Make the check default-deny:
- An element passes only if it resolves to scalars, or to `src/` types whose fields do.
- A bare type parameter, an unresolved name or a prelude type fails unless it is on a reviewed list.
- Exempt only `vec.npk`'s generic definition, not the whole file.
- Key declarations by module, not by bare name.
- Normalise whitespace before matching.
- Use one blanker that knows `/* */`, `'…'`, `r"…"` and `"""…"""`.

Otherwise, narrow S-23a, RX-155 and `0.1.0.md` to what the check actually enforces. The `'"'` blanking hole (M12) also affects `check_no_division` and `check_accessor_confinement`, which use the same `_blank_prose`.

### N-19 — A pending unit is observed once, at −O0 only, so the marker still excuses failures it does not name.

Severity: **contradiction**, low.

`stages.py:216-217` returns `_pending(...)` before `check_optimised` is called (line 224). For a pending unit that means:
- no `opt -O2` and no `llc -O2`;
- no B-2 re-scan of the optimised object (`build.py:250-253`, "`opt` is licensed to MINT libcalls");
- no optimised link or run;
- `stress` ignored: one run only (lines 234-238).

Measured with `--only … --keep` over a listed pending unit and an ordinary unit. The ordinary unit's scratch directory holds `.opt.ll`, `.opt.o` and `.opt`; the pending unit's holds none. Yet the summary lists the pending unit among "B-2's two scans ran on 2 unit(s)", and the GREEN line says "every program agreed with itself under opt -O2".

The excusal is also keyed on the exit code alone. A unit pending on 92 (DEF-25's shape: `HeapOom` under a memory cap) is excused for any leak. A unit pending on a trap code is excused for any trap with that identity.

**What would resolve it:**
- Run both legs for a pending unit and require the named exit on both.
- Where the defect allows, prefer a unit-local exit code to a shared trap code.
- State in `expect.py` and B-5b what is still keyed on the exit alone.

### N-20 — The second direction of both reviewed lists has nothing testing it (V-21).

Severity: **dormant**.

- **`PENDING.txt`.** I deleted the "a line no pending unit matches" block (`run.py:370-380`). All 11 live self-check cases still passed, exit 0. The real list is empty, so a full run would be green too.
- **`RESIDUE.txt`.** I deleted the unused-entry block (`run.py:410-415`). The self-check still passed, exit 0. The real list has 9 of 9 entries referenced, so this block never fires.

RX-154's "three self-check cases, one per red the mechanism owes" counts the marker's three reds; it does not count this fourth one. The residue direction used to run only as noise in the fixture trees. The triage's scoping fix correctly removed that noise, and as a result nothing exercises the direction now.

Why it matters: a stale `PENDING.txt` line pre-authorises a future marker, so hiding a unit takes one edit, not the two RX-154 promises.

**What would resolve it.** Add a self-check case with a listed line and no marker; the fixture writes its own list, so this is expressible. For the residue list, add a fixture-local list with one unused entry, or state that the direction is unguarded.

### N-21 — Compiler-defect candidate: `npkc` emits a generic instance's type definition after its first use, so `npkc` exits 0 and `llc` refuses the IR.

Severity: **unverified claim about the compiler**, measured, and not yet in any record. Raise it now (W-11, W-27).

This minimal reproducer uses no library code. The `failsafe` is `tests/unit/vec_owning_get_moves_out.npk`'s, verbatim.

```
mod:zzg1;
struct:Pair<T> = { int64:a; int64:b; };
func:mk<T> = int64(int64:n) never fails {
    Pair<T>:p = Pair{ a: n, b: n };
    pass p.a;
};
func:main = int32(cstring[]:_~argv) {
    int64:c = raw mk::<int64>(4i64);
    if (c != 4i64) { exit 23i32; }
    exit 0i32;
};
```

**Result.** `npkc` exits 0. `llc` reports `error: Cannot allocate unsized type` at `%t1 = alloca %"npk.zzg1.Pair<int64>"`, IR line 358. The type definition `%"npk.zzg1.Pair<int64>" = type { i64, i64 }` *is* emitted, but at **line 873, after the function that allocates it**. The same happens with the struct in an imported module.

**Control.** Add `Pair<int64>:q = Pair{ a: 1i64, b: 2i64 };` to `main`. The definition then moves to line 16, and the program builds and runs, exit 0 at both levels.

Through the library it is the same: a generic helper with a `Vec<T>` local fails when called `::<int64>`. So it happens at `int64` too; it is about emission order, not ownership.

**What it blocks.** Any generic helper over a generic container outside that container's module, unless the concrete instance is also named elsewhere.

**What it does not block.** Cycle 0.0: `src/` has no such helper, and the harness's `llc` step would catch one, so it is not silent.

**Novelty.** Neither the compiler's `src/`/`meta/` at its HEAD nor the libraries contain "unsized", except `../nitpick/meta/roadmap/done/1.5/1.5.4c.md:365-372`, the inline-module form of this same message, fixed at 1.5.4c on a different path.

### N-22 — TYPE-083/DEF-96 is stated as current compiler behaviour in eight places, and the compiler has neither.

Severity: **unverified claim**.

Examples:
- `nitpick-regex/tests/conformance/import.npk:43`: "the compiler's 1.6.0 step 3c refuses it `NITPICK-TYPE-083` (its DEF-96)". The same wording appears in `harness/baseline/baseline.npk:42`, both `harness/selfcheck/*.npk`, `tests/rejection/failsafe_*.npk`, and `0.0.4c.md:553` and `:574`.
- `0.1.0.md:169`: "the compiler's DEF-96 makes any other form an error".

`git grep -E 'TYPE-083|DEF-96'` over the compiler's `src/` and `meta/` finds nothing, at `c3bdae2` or at HEAD. The only source is the compiler seat's advance notice, recorded in `RECORD.md:6637` and `PLAYBOOK.md:257`.

The change itself is correct at the pin. `../nitpick/meta/specs/DECISIONS.md:6229`, D-089: "`main` takes `cstring[]:argv` and nothing else".

**What would resolve it.** Word it as "will refuse, per the compiler's advance notice for 1.6.0 step 3c" until a pin carries it.

### N-23 — Stale counts and over-wide set claims

Severity: **stale / cosmetic**.

- **Loop count.** `CLAUDE.md` says "61 loops here, none `unbounded`". At HEAD there are **79**, every one with `decreases` and none `unbounded`; the eight new owning units added 18. The compiler enforces D-304, so only the number is wrong.
- **Unit count in CI.** `.github/workflows/ci.yml:12` says "all 174 units build, link, run and are judged by their exit codes". **107 of the 174** — the 95-file parse sweep, the 5 refusal probes and the 7 rejection fixtures — neither link nor run. `stages.py`'s own `parse_sweep` docstring says so.
- **The orphaning units' control.** `SAFETY.md:533-535` names `vec_owning_freed`, "the same rounds without the verb", as the control that exits 0. That holds for the set, truncate and clear units (500×1000). It does not hold for remove and swap_remove, which run 40 000 rounds of 16. I built same-shape controls by deleting each unit's verb loop: both exit 0 under the same 64 MiB cap, with `/bin/true` passing that cap too, while the units exit 92. So the units stand; only the sentence is wrong, and the matching control is not committed.

---

## THE FOUR PLACES I WAS TOLD TO PRESS

1. **The new tree check.** It misses twelve shapes (N-18); eleven compile and run, and six demonstrate BL-5's move-out at element types the check passed. One of the twelve, M8, led to the compiler-defect candidate N-21. The docstring's stated limit, "a generic's `Vec<T>` is judged where it is instantiated", is itself inexact: nothing judges `Stack<string>`.
2. **`PENDING.txt`'s both-ways check, and whether a marker can still excuse the wrong failure.**
   - The first direction is tested: s1 reproduces, and deleting the unlisted-marker red fails case 11 alone.
   - The second direction is not tested (N-20).
   - A marker still excuses failures it does not name: everything on the −O2 leg, and any failure that shares its exit code (N-19).
   - Worst, the count has a second exit that bypasses the list entirely (BL-7).
3. **The self-check's residue scoping is correct.** I built every live case's fixture with `selfcheck.py`'s own functions and read every red its inner run printed.
   - In each case, the reds name only the case's own file, printed twice (the suite line and the summary).
   - Cases 12 and 13 add one red each, from their own fixture `PENDING.txt`, not inherited from the repository.
   - There is no residue red anywhere.
   - Fixture trees copy `SYMBOLS.txt`, `EDGES.txt` and `RESIDUE.txt`, which describe the compiler's floor and are valid in any tree. Under `--selfcheck-inner`, rx120, the tree checks and the residue unused-entry direction are skipped.
   - The one consequence is N-20.
4. **N-15.** This became BL-8, and my view is in the section above. The recorded measurements (95, 95, 170) reproduce; the premise for deferring does not.

## DISPOSITIONS RE-CHECKED AGAINST THE TREE

- **BL-5 — FIXED (restriction), holds.**
  - The false TYPE-046 belief is corrected at the original sites. A live-file sweep finds no surviving credit to the language; the remaining TYPE-046 mentions describe a copy being refused, which is true.
  - The per-verb statements are present at `vec_get`, `vec_set`, `vec_remove` and `vec_swap_remove`.
  - All eight owning units are green in the baseline.
  - **The triage's P1 control reproduces.** Against a `vec.npk` whose `vec_set` and `vec_remove` drop what they discard, `vec_owning_set_orphans` and `vec_owning_remove_orphans` go **92 → 0**, while `vec_owning_freed` and `vec_unit` stay 0.
  - The check's six control plants reproduce.
  - Gaps: N-18 and N-23.
- **BL-6 — FIXED, holds for what its cases cover.**
  - The marker grammar (`expect.py:236-267`), the "different failure" red (`stages.py:271-277`) and the stale red (`stages.py:259-270`) are all present.
  - All three triage mutations reproduce exactly, each failing only its own case: s1 → case 11, s2 → case 12, s3 → case 13.
  - Gaps: BL-7, N-19 and N-20.
- **N-13 — FIXED, holds.**
  - `vec_owning_truncate_orphans` and `vec_owning_clear_orphans` exist and expect 92 under 64 MiB.
  - Dated notes are at `0.0.4.md:21` and `:146`.
- **N-14 — FIXED as a rationale, holds.** Read at `c3bdae2`:
  - `npkrt.ll:3828` is `-4099 OUT_OF_BOUNDS`, and `:3843` is `-4102 HEAP_INTEGRITY double-free…`.
  - The prelude has `OutOfBounds = 4099i32` and `Unreachable = 4102i32` ("…and the runtime's integrity defects").
  - RX-144 carries "SUPERSEDED IN PART by RX-156" (`DECISIONS.md:2500`).
- **N-15 — OPEN.** See BL-8.
- **N-16 — FIXED at full extent, holds.** I re-measured all 30 files that `git grep -l 'argv\.len' -- tests` names (24 units, 6 probes). Each gives its expected exit with no argument and **48** with one, and the memory cap is honoured where declared.
- **N-17 — FIXED, holds.** RX-130 carries "SUPERSEDED IN PART by RX-143" (`DECISIONS.md:1612`), and `check_refs` is clean.

## CHECKED AND FOUND CLEAN

- **Baseline:** 174/174 GREEN in 72.3 s, exit 0 (see Method).
- **`check_refs`:** clean, 69 markdown files, leak scan 194 of 194.
- **`check_record nitpick-regex 0.0.5`:** clean.
- **CI:** all eight pushed runs from `f19598c` to `4420c45` concluded `success`. I read `4420c45`'s log (run `36174605917`, job `108202047458`) through the API:
  - compiler pin `c3bdae270d63…`;
  - LLVM 20.1.2 asserted;
  - `npkc.ll` 28 111 929 B, `4029fc70…`, equal to the STAMP in the compiler's own `c3bdae2` commit message;
  - 174/174 GREEN;
  - `1 nested repository pruned: .nitpick`.
- **Compiler claims, read at `c3bdae2` from source:**
  - D-089, D-248, D-264, D-304, D-305 (4118), D-307 (4120), D-308, D-313 and D-314 exist, are SETTLED, and say what they are cited for.
  - TYPE-046 is `TYPE_MOVE_REQUIRED`, TYPE-079 `TYPE_SEALED_WRITE`, TYPE-080 `TYPE_HIDDEN_FIELD`, TYPE-072 `TYPE_LOOP_CLAUSE`, and RESOLVE-013 `RESOLVE_ENTRY_OUTSIDE_ROOT` (`type_codes.npk:207,446,451,503`; `resolve_codes.npk:62`).
  - `type_owns_for_move` treats a bare type parameter as owning (D-264), and its comment that moving out of a container "is NOT this rule's business" is quoted correctly.
  - `&{…}` interpolates only in a template: LEXICAL_REFERENCE §6.3/§6.4, where `StringLiteral` has no interpolation.
- **D-248, measured:** a real import of a file that declares `main` is refused RESOLVE-013 twice.
- **The containers match 0.0.4c:**
  - `Vec`: `hidden wild T->:items`, `sealed limit<ListLen>` on `count` and `cap`.
  - `Bytes`: `sealed buffer:buf`, `sealed limit<ListLen> len`.
  - `SparseSet`: `sealed` `dense` and `sparse`, `sealed limit<ListLen> count`.
  - `Bytes` copies are refused (TYPE-046).
- **The nested-repository prune** (`treecheck.py:769-781`, RX-147) works by name and by the presence of `.git`, and it reports what it pruned.
- **Cross-repository:** `PLAYBOOK.md:54`'s TYPE-046 row is corrected in the workbench. The board's question 9 row still carries the "before cycle 0.8" premise (BL-8).

**Where I pressed and found nothing:**
- the residue scoping;
- the triage's s1–s3 mutations;
- the attribution of BL-5's orphaning units (P1 and the same-shape controls);
- all 30 N-16 files;
- D-248 for real imports;
- whether a `Bytes` copy is refused.

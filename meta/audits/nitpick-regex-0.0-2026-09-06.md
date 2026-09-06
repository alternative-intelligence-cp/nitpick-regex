# Audit — `nitpick-regex`, cycle 0.0 — 2026-09-06

**W-22 audit, filed by the eighth orchestrator (`nitpick-libs_s3`,
`647e6588-8236-4fcc-91a1-0223d220639f`). The auditor's final message is
reproduced below in full.**

**TWO MECHANICAL EDITS WERE MADE AND THIS NOTE EXISTS SO THE WORD "VERBATIM" IS
NOT CLAIMED FALSELY.** The reference gate refused the file as first written, and
both refusals were correct:

1. **An absolute path** — a `/home/<user>/…` prefix — in the toolchain line,
   which the gate's leak check catches because a tracked file must not carry a
   machine's home directory. Rewritten relative to the workbench root. *(This
   note, in its first form, spelled the offending prefix out in full while
   explaining why it had to go, and the gate refused the file a second time for
   exactly that. An example of a forbidden string is still the forbidden string:
   a leak check cannot read intent, and should not be asked to.)*
2. **A bare library open-question id** in the "checked and found clean" section.
   **`O-` ids are REPOSITORY-SCOPED**: `O-N9` resolves here because the workbench
   defines it, while the id in question is `nitpick-regex`'s own and resolves to
   nothing from this repository — the gate is right, and the outgoing
   orchestrator was caught by the identical thing hours earlier. Replaced with a
   description that names the owning repository, which is the convention.

**No finding, number, verdict or line reference was altered.**

- **Dispatched:** `npk:auditor`, `claude-opus-5`, adversarially — told to break
  the verifier's PASS rather than confirm it, and briefed from cycle 0.0's *own*
  closing findings used as templates rather than as closed matters.
- **Toolchain:** `3d15ac9`, `.internal/toolchain/3d15ac9/`, LLVM 20.1.2.
- **Preceded by:** `0.0.5` reporting `READY-TO-CLOSE`, and an independent
  `npk:verifier` returning PASS on eight checks (harness 98/98, both gates clean,
  archive landed, `0.1.0.md` execution-grade, the `end` claim independently
  compiled *and run*, the RX-120 numbers re-derived at both pins, the CI digest
  step confirmed to print rather than assert, and the accessor confinement check
  proved to fail on a planted violation).
- **Verdict: DO NOT ACCEPT cycle 0.0 as closed.** Two blocking findings, both in
  `src/core/`, the cycle's headline deliverable.
- **Both repositories were clean before and after**; all probing was done in the
  session scratchpad and no tracked file was modified by the auditor.

**Why this report matters beyond its own findings.** BL-1 is the **third**
use-after-free this repository has shipped under a green suite, and the second to
survive an independent VERIFIED PASS. The suite *constructs* the stale alias and
declines to read it; one added line turns the green run red. That is the standing
argument for planting faults rather than trusting a pass, and for the rule that a
leak gate is not a correctness gate.

---

REPORT nitpick-regex 0.0 audit
status: DO-NOT-ACCEPT
auditor: npk:auditor, claude-opus-5
toolchain: 3d15ac9

Both trees clean — all probing was done in the scratchpad.

# W-22 AUDIT — `nitpick-regex`, cycle 0.0 close

**Auditor verdict: DO NOT ACCEPT cycle 0.0 as closed.** Two blocking findings, both in `src/core/` — the cycle's headline deliverable — both measured with running programs at the pinned toolchain, and one of them a **use-after-free that the shipped test suite already constructs and does not read**.

Toolchain: `NPKC=.internal/toolchain/3d15ac9/npkc`, `npkrt.o` from the same directory, LLVM 20.1.2. Every probe below was run through all four steps (`npkc`, `llc`, `ld.lld`, binary) with `exit=$?` captured on its own line, never through a pipeline. All probes were built in the scratchpad; **no repository was modified** (`git status --porcelain` empty in both trees).

Note on method: the compiler working tree is at `ddc3dc0`, **not** at the pin. Every compiler-source claim below was re-read with `git show 3d15ac9:<path>`, not from the working tree.

---

## BLOCKING

### BL-1 — `bytes_take_string` returns a BORROWED VIEW, is documented in three places as an owning value, and produces a silent use-after-free that the shipped suite constructs and never reads

This is finding-shape #1 from the dispatch in its worst form: not merely an unmeasured justification, but a decision whose *stated safety rationale is refuted by the runtime*, and whose replacement carries the same hazard the decision was made to avoid.

**What the documents claim**

- `meta/roadmap/done/0.0/README.md:251` — "`bytes_take_string` hands over an **owning** `string`, which is the only shape that may leave the frame."
- `harness/baseline/RESIDUE.txt:35` — "`string_from_bytes`, in `bytes_take_string` -- **the only shape that may leave the frame**, since a `uint8[]` view may not (O-N9)."
- `src/core/bytes.npk:48-57` — the header strikes `bytes_view` because "returning a slice over a local's body is the ONE ESCAPE THE COMPILER DOES NOT DIAGNOSE", and offers `bytes_get`, `bytes_extend` and passing the `Bytes` itself as the safe shapes.
- `src/core/core.npk:64-66` says "There is deliberately no `bytes_view` … returning one is the escape the compiler does not diagnose (O-N9)" — and then re-exports `bytes_take_string` **fourteen lines later at line 78**.

**What the compiler actually does** (`git show 3d15ac9:runtime/npkrt.ll`, lines 6561-6570):

```llvm
define { ptr, i64, i64 } @npk_string_from_bytes(ptr %p, i64 %n) {
  ; CAP 0 FOR THE SAME REASON AS THE SLICE ABOVE: the buffer belongs to the
  ; caller — a writer's sink, the lexer's decode buffer — and this header is a
  ; borrowed view of it.
```

and line 4858: "**cap 0 is the not-mine bit**". The compiler's own specification agrees: `../nitpick/meta/specs/BUILTIN_REFERENCE.md:219` — "`string_bytes`/`string_from_bytes` are **the explicit view primitives**"; line 221 gives it a `Views` column of 1.

`src/core/bytes.npk:271-273` returns exactly that:

```
pub func:bytes_take_string = string(Bytes->:b) never fails {
    pass string_from_bytes(b.buf.ptr, b.len);
};
```

**Both halves of the claim are false, measured:**

| probe | shape | result |
|---|---|---|
| C | return the result from the frame that **owns** the `Bytes` | **REFUSED** `NITPICK-BORROW-001` — "a borrow cannot travel up … (D-004 rule 2)" |
| D (control) | same frame, same `@b`, returns a scalar | **accepted**, exit 5 — so C's refusal is view-tracking, not borrow-passing |
| E | return it where the `Bytes` is a **parameter** | accepted, exit 104 (`'h'`) |

So it is *not* owning, and it may **not** leave the frame — the compiler refuses precisely the case the documents advertise. It may leave only a frame where the `Bytes` belongs to the caller.

**And the actual bug, which nothing documents at all.** `src/core/bytes.npk:117` (`b.buf = move(bigger);`) frees the old body on every growth. Any `string` previously taken dangles:

| probe | result |
|---|---|
| A — take at len 5, grow past capacity 8, re-read by equality | **exit 20** (wrong answer) |
| B — same, exit code *is* the first byte | **exit 170 = 0xAA**, the D-183 free poison |

170 is the exact signature `meta/OPEN_QUESTIONS.md:110` names for O-N9.

**The suite already builds this and does not look at it.** `tests/unit/bytes_unit.npk:55` takes `out` over an 8-byte body; line 63 (`bytes_extend_str(@b, " world")`, want 11 > 8) reallocates and frees it. `out` stays in scope to the end of `main` and is never read again; its cap-0 drop frees nothing, so nothing complains. I copied the shipped file to the scratchpad and added **one** line — `if (!string_equals(out, "hello")) { exit 46i32; }` after line 65:

```
shipped file, unmodified          → RUN exit=0    (the suite's green)
same file + that one read         → RUN exit=46
```

Five public functions grow a `Bytes` (`bytes_reserve`, `bytes_push`, `bytes_extend`, `bytes_extend_str`, `bytes_put_uint`). A sweep of all 147 tracked files for `dangl|invalidat|stale view|after a growth|reallocat.*view` returns 10 hits, every one about `Vec`-arena pointers or O-N9's slice cases — **none about `Bytes`**. The repository documents this exact hazard correctly for `Vec` at `meta/specs/HIR.md:59` and `meta/roadmap/0.1/0.1.0.md:60`, and missed it for the type it wrote to replace the banned one.

Mitigating, and I state it because it bounds the blast radius: `src/lib.npk` re-exports one name (`ERegexPattern`), so this is not consumer-visible today, and `meta/specs/API.md:198` (A-12) says output goes into a caller-owned `Bytes`, "never a returned `string`". It is internal API, and cycle 0.1's parser and 0.6's replacement are its first users.

**What would resolve it.** Either (i) make `bytes_take_string` copy (`string_slice(view, 0, len)` returns an owned copy per D-186) and rename it, or (ii) keep the view, rename it to say so (`bytes_view_string`), write the invalidation contract into `src/core/bytes.npk`, `core.npk` and `done/0.0/README.md:251`, and add a unit case that reads a taken view **after** a growth and requires the trap or the correct value. Either way the three "owning"/"may leave the frame" sentences must go: they are false at the pin, and RESIDUE.txt:35 is one of them.

---

### BL-2 — `vec_reserve` does not terminate on a `Vec` whose capacity is zero, which is the documented postcondition of `vec_free`; the sibling `bytes_reserve` has the guard and `vec_reserve` does not

`src/core/vec.npk:162-172`:

```
    int64:nc = v.cap;
    while (nc < want) { nc = nc * 2i64; }     // traps on overflow (D-210)
```

`src/core/bytes.npk:106-119`, written in the same subcycle for the same purpose, has the guard the other lacks:

```
    int64:nc = b.buf.len;
    if (nc < 1i64) { nc = 1i64; }             // <-- vec.npk has no equivalent
    while (nc < want) { nc = nc * 2i64; }
```

`v.cap == 0` is reachable only after a free — and `vec_free` (`src/core/vec.npk:152-157`) sets `count = 0; cap = 0` **deliberately**, as poison: it is what makes `vec_get`, `vec_set` and `vec_pop` trap on a freed `Vec` rather than read a dangling block. The poisoning is right and incomplete. Measured (probe `vfree`: `vec_init`, `vec_push`, `vec_free`, assert `cap == 0`, then `vec_reserve(@v, 1)`):

```
timeout 6 ./vfree  →  RUN exit=124   (timeout; vec_reserve did not terminate)
```

`vec_push` and `vec_insert` take the same shape one step further: `nc = v.cap * 2i64` is 0, so they call `ralloc(<dangling>, 0)` and then write one element into it.

This matters beyond ordinary use-after-free because `CLAUDE.md`'s first non-negotiable rule is that a search is `O(m·n)` *"always, on every input … catastrophic backtracking is a denial of service … and the language has no cancellation (D-062) with which to survive one."* A non-terminating loop in the container every engine is built on is that failure mode, reached without any backtracking at all.

**What would resolve it.** Add `if (nc < 1i64) { nc = 1i64; }` before the loop, matching `bytes.npk:111`; or have the three growth paths `drop vec_oob(...)` on `cap <= 0` so misuse traps like every other misuse in the file. Then a unit case per entry point.

---

## THE FOUR ADJUDICATIONS

### (a) `harness/baseline/RX120.txt` — **the obligation is NOT discharged**

The verifier is right that the numbers reproduce. That is not the question 0.0.5 was dispatched to answer. Beyond non-executability (`bash … ` exits 2), the file fails its own stated standard in three places:

1. **Line 115-117 records a command that cannot produce the output beside it and cannot have exited 0.** It reads `python3 -c "import harness.irscan as s; print(s.kernel_call_edges(...))"` with `exit=0`. `harness/irscan.py` defines `normalise`, `edges`, `scan` and `DENIED` — `kernel_call_edges` exists nowhere in the tree except this line. Run verbatim against a copy of `irscan.py` in the scratchpad: `AttributeError: module 'harness.irscan' has no attribute 'kernel_call_edges'`, **exit=1**. The recorded output (`irscan public names: [...]`) is the output of a *different, unshown* command. This is section **E** — the section carrying "WHY RX-120'S REMEDY IS NOT RETIRED", the half being propagated to four sibling repositories. The conclusion is sound (`edges`/`scan` do exist and the reasoning holds); the evidence for it is fabricated. The independent VERIFIED PASS did not catch this.
2. **Line 104 consumes files no shown command creates.** `diff .internal/rx120/floor_old.undef .internal/rx120/sys_old.undef` — sections A, B and D show `llvm-nm` printing to stdout, never redirected to `.undef`. A reader re-running the documented commands in order cannot reach the transcript's own decisive diff.
3. **Line 45 contradicts itself and defeats the "Verbatim" claim of line 39 and the "nothing else is edited" claim of line 30.** It shows `-o .internal/rx120/floor.ll` with the trailing comment "`# stdout redirected: npkc emits IR to it`". Measured: `npkc file -o out.ll` writes the file and leaves **stdout empty** (0 bytes). The two forms are alternatives; the line shows one and annotates the other.

**What the artefact should be.** An executable `harness/baseline/rx120.sh` (or a `harness/run.py` stage / self-check case) that: takes both pin directories from the environment or `.internal/toolchain/`; **creates every intermediate it later consumes**; **asserts** floor == 2, syscaller == 3, difference == `{npk_sys6}` at the working pin and equality at `950bb1d` rather than printing them; and is invoked by CI, so the next re-pin that moves the floor reddens something instead of silently invalidating a committed sentence. The narrative transcript keeps its value beside it, not instead of it. This is precisely the lesson `0.0.5.md` §D.5 states — *"a claim other repositories will act on is reproducible by running a file"* — and the file it produced is not runnable.

### (b) The CI digest substitution — **LEGITIMATE. Settled by measurement, not by argument.**

Both artefacts exist on this machine. Read-only comparison:

```
05457db4e98b18a97033eac8bfbe1cfbcddf72f6cf5373dbb99d3693ce94d367  build/npkc.ll
05457db4e98b18a97033eac8bfbe1cfbcddf72f6cf5373dbb99d3693ce94d367  .internal/quickemit/npkc.ll
21514197 bytes each — cmp: BYTE-IDENTICAL
```

The reasoning in `.github/workflows/ci.yml:178-195` also checks out at source: `bootstrap/harness/quickemit.py:75` calls `harness.build_tool(OUT, True, harness.EMIT_CHECK, "npkc")`; `harness.py:2018` defines `EMIT_CHECK` as `src/npkc.npk`; `build_tool` (`harness.py:1758`) runs `BUILDER <source> -o <dir>/npkc.ll` with `BUILDER` the committed snapshot (D-203/D-205) — the same route `npkg/build.npk:377` describes for `build/npkc.ll`. D-236 renders site rows relative to the manifest root, which is the compiler repo root in both cases, so the output directory does not enter the IR. **No blocking finding here.**

One non-blocking note, and it is the same shape as B4: the workflow *argues* "the output directory does not enter the IR" where the measurement was free on the machine that wrote the argument. Now that the digest is known, the step can name `05457db4…` at pin `3d15ac9` and become an assert instead of a print — which is what D-265 clause (4) asks pin notices to carry anyway.

### (c) What the 98 green units do **not** cover

Answering the question as asked — which primitive reads back a value after a free, a growth or a truncation:

| primitive | after growth | after truncation/clear | after free |
|---|---|---|---|
| **`SparseSet`** | n/a | **YES, and it is the strongest artefact in the tree** — `tests/unit/sparseset_unit.npk:111-135` re-checks membership at **every** key after **every** one of 10 000 seeded operations against an independent reference, plus the structural invariant `sparse[dense[i]] == i` | n/a |
| **`Vec<T>`** | **YES, strong** — `tests/unit/vec_unit.npk:127-139`: 100 000 pushes from capacity 1, distinct values, read back at 0 / 50 000 / 99 999 | **NO** — lines 92-98 assert `count` only; no value is read after `vec_truncate` or `vec_clear` | no (correctly) |
| **`Bytes`** | **YES but weak** — `tests/unit/bytes_unit.npk:154-155` reads indices 0 and 999 999 after ~20 reallocations, but **every byte pushed is the constant `88u8`**, so any mis-copy that preserves length is invisible. Contrast `vec_unit`, which pushes `i` | partial (`bytes_clear` then re-fill then read, lines 69-75) | **This is where BL-1 lives** |
| **`ByteSet`** | n/a — value type, no allocation, no free, no growth, no truncation | n/a | n/a |

So: three of four have a growth read-back, one is weak, none reads after a truncation, and the fourth needs none. **And the gap the table exposes is exactly BL-1**: the one place the suite creates a stale alias, it declines to read it. `vec_owning_leak.npk` / `vec_owning_freed.npk` are a well-built memory-cap pair (identical but for one function name, same 64 MiB cap, required to end 92 and 0, with the `/bin/true` control) — but neither reads anything, correctly, and they cover `Vec`, not `Bytes`.

### (d) The three-way error-budget accounting — **the arithmetic holds; a fourth residue was found**

Re-derived over the whole tree:

| charge | count under `src/` | site |
|---|---|---|
| declared `error:` | **1** | `src/api/api.npk:32` — `pub error:ERegexPattern;` |
| arithmetic (`/`, `%`) | **0** | `check_no_division` over 13 files; `bytes_put_uint` is subtraction against a built power-of-ten table |
| contract clause (`limit<Rules>`) | **0** | S-24 |

S-8's "exactly one arm" holds, and `src/lib.npk` re-exports exactly one name. **But the audit found the inverse of the failure the rule warns about**: a charge removed from the code and left standing in the consumer.

`tests/unit/bytes_unit.npk:166-171` states as fact:

> `DivByZero` AND `DivOverflow` ARE HERE BECAUSE `bytes_put_uint` USES `/` AND `%`

`src/core/bytes.npk:186` says the opposite in capitals ("NO `/` AND NO `%`"), and `meta/specs/SAFETY.md:217-224` records the rewrite. Measured: I stripped both arms from a scratch copy of the shipped test and it compiles at **exit 0** — REACH-002 no longer arms them. `bytes_unit.npk` is the only one of 14 test programs carrying them (the other 13 all carry the same six-arm ordinary set). Two dead arms, and the sentence justifying them is false about the file it tests. **A budget audit that counts only `error:` declarations counts one of three; this one also has to catch arms outliving the construct that charged them.**

---

## NON-BLOCKING (carry into 0.1)

**N-1 — `TESTING.md` §8's check table is still wrong, in the same direction the cycle says it fixed.** `meta/specs/TESTING.md:186-203`. Header: "Checks that diff the library against the documents describing it, **run on every full invocation**." Denominator: **13 rows; 7 exist** (6 registered in `harness/treecheck.py:593`'s `ALL`, plus `check_no_syscalls` as a build step); **6 do not exist anywhere in code** — `check_tables_regenerate`, `check_table_invariants`, `check_error_kinds_tested`, `check_inst_kinds_total`, `check_hir_kinds_total`, `check_byte_class_partition`. All six are owned by a future cycle README (0.1, 0.2, 0.3, 0.4, 0.6, 0.7), so they are **not dormant** — but the table gives no column saying so, and rule V-19 two lines below elevates two of the non-existent ones as "the two that matter most". 0.0.5 corrected the two rows it found and not the framing that made both errors possible.

**N-2 — `CLAUDE.md` contradicts itself about the tree-check count, and it is the file `CLAUDE.md` tells every session to read first.** Line 19: "A full green run is **98 units** and **six** tree checks." Line 241: "runs **four** tree checks". `treecheck.ALL` has six. This is finding B6's exact shape — *"two sections of one file contradicted each other … proximity is not review"* — left standing in the onboarding document by the subcycle that named B6 as a durable lesson. (`.github/workflows/ci.yml:17` and `meta/roadmap/0.1/0.1.0.md:23` both say six correctly.)

**N-3 — the archive redirect note's count matches no state the tree has ever had.** `meta/roadmap/done/0.0/README.md:3-8` says "There are **41** such mentions across **15** files", present tense, immediately before "They are deliberately not rewritten". Re-derived:

| state | occurrences | lines | files |
|---|---|---|---|
| pre-archive (`7eb8e53`) | 49 | 45 | 17 |
| **HEAD** | **33** | **32** | **9** |
| README claims | 41 | — | 15 |

18 occurrences across 9 files *were* rewritten (`CLAUDE.md`, `harness/README.md`, `nitpick.toml`, `meta/OPEN_QUESTIONS.md`, `tests/probe/README.md`, three probe headers, `harness/selfcheck/syscall_consumer.npk`), and the note itself adds 2. A reader who greps to check the redirect finds 33/9 and cannot reconcile it. Same defect class as B7, in the note written to record B7's cousin.

**N-4 — `meta/specs/API.md:164` calls a constructor that does not exist.** The one code example under A-9 reads `Bytes:out = bytes_new();`. `src/core/bytes.npk` defines `bytes_init(int64:cap)` and no `bytes_new`; the token appears nowhere else in 147 tracked files. `Bytes` landed at 0.0.4 and 0.0.5's reconciliation read the 23 *probe verdicts* against `meta/specs/` — a constructor name is not a probe verdict, so nothing compared the specification's examples against the code that had just landed. The mechanism 0.0.5 §D.2 names, running in the other direction.

**N-5 — `tests/unit/vec_unit.npk:19` cites a test file that has never existed.** "That half is gated by `vec_owning_cap.npk` under a memory cap." The pair is `vec_owning_freed.npk` / `vec_owning_leak.npk`. Single occurrence in the tree, in a `.npk` file `check_refs` never opens — item 4's shape, still present after the repair.

**N-6 — `SAFETY.md` S-23's wording is broader than the check that enforces it.** `meta/specs/SAFETY.md:325`: "a tree check enforces that **no `.items[` appears outside `src/core/vec.npk`**", unqualified. `check_accessor_confinement` examines `src/` only — 13 files. Denominator outside its scope: **84 occurrences across 20 files**, all currently benign (verified: no probe imports `src/core/vec.npk`; `probe01` and `probe08` define their own `struct:Vec`, and the rest are prose). The check's own docstring and its `over N file(s) under src/` line are honest; the specification is not. 0.0.5 fixed "the check does not exist" and not "the rule's words are wider than the check".

**N-7 — the `check_refs` denominator moved inside the reporting subcycle.** The REPORT block says "62 of this repository's 145 tracked files". At HEAD: `check_refs` reports **63 files**, the tree has **147** (63 markdown, 84 non-markdown). The sweeps table at `0.0.5.md:482-487` uses 145 throughout. The recommendation it carries — extend the leak scan to every tracked text file — stands and is worth acting on.

**N-8 — `Bytes`'s growth test cannot detect a mis-copy that preserves length**, because every pushed byte is `88u8` (`tests/unit/bytes_unit.npk:137-155`). `vec_unit.npk` pushes `i` and checks three distinct values; `bytes_unit.npk` should do the same. Cheap fix, and it is the test standing behind the type BL-1 is in.

**N-9 — 39 lines across 20 files still date a measurement to "the pin" or "this pin".** 0.0.5 swept the exact phrase *"measured at the pin"* (3 sites) and left the class. Live, non-archived sites include `meta/specs/SAFETY.md:201`, `meta/specs/BUILD.md:238` and `:292`, `meta/OPEN_QUESTIONS.md:378`, `harness/build.py:11`, `harness/run.py:215` (printed on every run), `harness/stages.py:166,172`, `src/core/bytes.npk:263`. I spot-checked the two most load-bearing and **both are still true at `3d15ac9`**: `BUILD.md:238`'s quoted usage line matches `npkc`'s actual output, and `npkc --help` exits **2** as documented. So none is currently false — but the class is thirteen times larger than the sweep that closed it.

---

## CHECKED AND FOUND CLEAN — so the absence is evidence

Stated with denominators, because the recurring defect here is a check narrower than its name.

- **`check_refs.py`** — clean over 63 markdown files.
- **Compiler claims re-verified at the pin** (`git show 3d15ac9:`, not the working tree at `ddc3dc0`): `npk_string_from_bytes` returns cap 0 ✓; "cap 0 is the not-mine bit" ✓; `fold_string_builtin` handles exactly four names (`string_concat`, `string_equals`, `string_byte_length`, `string_is_empty`), none reading a byte ✓; `fold_expr` dispatches on 14 `ExprKind`s with **no** index arm and zero occurrences of `ExprIndexExpr` ✓; `src/frontend/type_resolve.npk` exists and `resolve_type.npk` does not ✓. **the library's outward-facing request — its own general open question about the compiler's fold path, numbered in `nitpick-regex/meta/OPEN_QUESTIONS.md` — is accurate and ready to raise.**
- **The renamed-file sweep is complete.** 7 lines across 5 files; every live site corrected, including `tests/probe/refused/probe09_comptime_walker.npk:17`, which is corrected at lines 20-23 (I initially flagged it and was wrong).
- **`meta/specs/README.md`'s "language in one paragraph"** — the out-of-range-index correction did land, with its own account of why it survived five subcycles.
- **Counted claims all re-derived and correct**: `src/` = 13 `.npk`; probes = 19 + 6 = 25; unit = 13; rejection = 2; `treecheck.ALL` = 6.
- **`#size_of<ByteSet>()` = 32**, measured with the exit code as the number (probe `szB`), matching `src/core/byteset.npk:4` and `CLAUDE.md:192`.
- **`sparseset_unit.npk`** — the best-constructed test in the repository. Independent reference, seeded xorshift, all-keys re-check after every operation, structural invariant checked separately from membership, operation count asserted, both branches asserted taken.
- **`vec_owning_leak.npk` / `vec_owning_freed.npk`** — a correctly built differential memory-cap gate with the `/bin/true` control.
- **`check_accessor_confinement`** — genuinely both-directional, and the owner-no-longer-contains-its-pattern arm is a real idea, not decoration.
- **`(*)` discharges nothing** — confirmed incidentally: a program importing only `byteset.npk` is refused `NITPICK-REACH-002` for six arms with `(*)` present.
- **The error budget is one arm**, verified three ways (§d above).
- **The CI digest substitution is legitimate**, verified byte-for-byte (§b above).

**Where I pressed and found nothing:** the `>>`/`&` substitutions in `byteset.npk` are exact for `uint8` operands as claimed; `sset_insert`'s `vec_set(dense, s.count)` cannot exceed `dense.count` because a full set short-circuits on `sset_contains`; `sset_contains`'s `int32`→`int64` position is guarded on both signs before indexing; `src/lib.npk` obeys its own three re-export rules; and the six unregistered checks in `TESTING.md` are each owned by a named future cycle, so none is dormant in the "nobody will build it" sense.

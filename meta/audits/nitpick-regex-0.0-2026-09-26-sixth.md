REPORT nitpick-regex 0.0 audit (SIXTH)
status: ACCEPT
auditor: npk:auditor, claude-opus-5-5
toolchain: c970483 (controls at c3bdae2)
scope: 40074b6..37695a7 (9 commits: the fifth triage be6511f, 1b1a74f; the adoption plan cf63b89, f32d505, 7bc3e9c, 8a9fc04; the adoption 06d5c00, b34b683, 37695a7)

Paths are relative to the workbench root (the directory holding `BOARD.md`), because this message is filed verbatim and the reference gate refuses a tracked file that contains a home directory. The compiler is `../nitpick`, read only with `git show`, `diff`, `log`, `merge-base` and `grep`.

I wrote nothing:
- `nitpick-regex` was clean at `37695a7` before and after. Nothing in its gitignored `.internal/` is newer than 05:23, which is the verifier's run; every run of mine was in a clone.
- The workbench stayed clean. Its HEAD moved to `b0f61fb` during the audit, by the orchestrator's own commits.
- Workbench scripts ran only as programs, under `python3 -B`.

earlyoom took no action today (hourly status lines only), and no run died by signal. Wall clock was 05:25–06:00 EDT.

# W-22 AUDIT — `nitpick-regex`, cycle 0.0 close, sixth pass (the accepting audit, narrow by design)

## Verdict: ACCEPT

- **All 23 items of the fifth audit's post-re-pin checklist are MET.** Each was re-measured at `c970483` against `37695a7`; none was taken from the record.
- **All three corrections in `0.0.4e.md` §9 are right.** The second overstates one word ("only"). That does not change item 8.
- **Five new findings, none blocking:** one dormant (N-30), and four stale, cosmetic or record-keeping (N-31 to N-34).
- **Question 11 is the author's.** My view is below, and the verdict does not depend on it.

## The 23 items

1. **MET.**
   - `.internal/toolchain/c970483/` holds `PIN.md` and `SHA256SUMS`, and `sha256sum -c` is OK for both files (`npkc` `e4d95007…`, `npkrt.o` `162b8975…`).
   - `merge-base --is-ancestor` against `c970483`: `2dde296` gives 1 (not an ancestor); `5bdae98` gives 0; `c3bdae2` gives 0.
   - LLVM is 20.1.2 here, and CI asserts it (`llvm-config --version == 20.1.2`).
   - `ci.yml` has `NITPICK_COMMIT: c9704830ea9c738f523bf6646a355f52679b3aee`.
   - CI at HEAD (run 36232375079, job 108377811687, read with `gh api …/jobs/108377811687/logs`) prints `compiler pin: c9704830…` and `npkc.ll 28188736 bytes d36a7e23…fe3183`. That equals the compiler seat's own ladder row at `c970483` (N-34 says where that row lives).

2. **MET.**
   - `rx120.sh` exits 0 at `c970483`: floor 5, syscaller 6, difference `{npk_sys6}`, and `npk_sys6` is not in the floor. Its `950bb1d` leg ran (29 / 29, identical sets).
   - `SYMBOLS.txt` and `EDGES.txt` are unchanged since `944a5d2`; no commit in scope touches them. The run's live diff against them reads `ok baseline: 5 undefined symbols, 4 floor call edges`.

3. **MET.**
   - REACH-003 bills at `c970483` over `37695a7` are 10, 10, 10, 10, 6, 11, 6, 6, 6. They are equal identity for identity to `c3bdae2` over `40074b6` (`diff` exit 0).
   - Sizes, each measured alone at both levels: `Vec<int64>` 24, `SparseSet` 56, `Bytes` 32 (and `Vec<uint8>` 24).
   - Probe 16 (`expect-exit: 24`) passes in the run.

4. **MET.**
   - Each file is in `tests/rejection/` and gives `npkc` exit 1 with exactly one diagnostic, `NITPICK-TYPE-085`, at its `expect-error-at`:
     - `vec_alias_param_free` 32:28
     - `vec_alias_param_grow` 24:23
     - `sparseset_alias_param_free` 22:20
     - `bytes_alias_param_grow` 25:25
   - Each column is the `@` in the callee (`consume` or `grow`).
   - The files were moved with `git mv` in `06d5c00`. Git detects all nine moves at `-M25%` (see N-32).
   - Every header is rewritten. "PINNED, NOT ENDORSED" survives only as "when this file was `tests/unit/…`".

5. **MET.** `tests/probe/refused/probe17_lent_field_drop.npk` gives exactly `TYPE-085` at 35:5, which is `b.s = string_concat(…)` in `overwrite`. Its verdict is recorded in `tests/probe/README.md`'s 2026-09-26 note.

6. **MET.** `tests/rejection/vec_alias_for_binding_free.npk` is N-26's shape: `for (Vec<int64>:x in arr) { drop vec_free::<int64>(@x); }` over `[move(a), move(b)]`. It gives exactly `TYPE-085` at 32:32, the `@x`. Step 3g closes the loan for this shape.

7. **MET.**
   - At `c3bdae2`, with the new `src/`, seven files compile and run at −O0 and through `opt -O2`, giving their old unit exits. So each refusal is the pin's:

     | file | exit at `c3bdae2` |
     |---|---|
     | `vec_alias_param_free` | 0 |
     | `vec_alias_param_grow` | 95 |
     | `sparseset_alias_param_free` | 0 |
     | `bytes_alias_param_grow` | 95 |
     | the `for` binding | 0 |
     | the generic pass-out | 0 |
     | probe 17 | 70 |

   - The positive twin, `tests/unit/loan_spellings.npk`, is TYPE-085's own prescription: `move Vec<int64>:v` called as `consume(move(a))`, and a pointer for a callee that grows. It runs 0 / 0 at `c970483` and at `c3bdae2`.

8. **MET, with correction 2.**
   - The parse sweep at `c970483`: 117 files, 89 compile, 28 refused.
   - The refused set is exactly `tests/probe/refused/` (7) plus `tests/rejection/` (21).
   - All 13 `src/` files compile, and so do probe04 (`len2(Vec<T>:self)`) and probe08 (`sset_has(SparseSet:s, …)`).
   - `vec_get`'s `Vec<T>:v` compiles under `T: Pod`.

9. **MET.**
   - The gate sentence (`meta/roadmap/0.0/README.md`, now at 578–590) no longer counts `sparseset_alias_swap`. Its 2026-09-26 note records the loan clause met, and the 0.0.4e box at README:486 lists every position.
   - S-23b's four loan and pass-out rows read "refused … at `c970483`".
   - RX-162 carries "SUPERSEDED IN PART by RX-168 and RX-169".
   - `vec.npk`'s loan section and `bytes.npk`'s note are dated 2026-09-26.
   - O-N21 is struck as discharged: "DEF-102 … in our pin since `c970483`".
   - `CLAUDE.md`'s LOAN bullet has its 0.0.4e note. Its counts (218 units, 47 unit programs, 21 refusals, 25 / 7) match the runner's.
   - `0.1.0.md`'s N-15 paragraph and `tests/rejection/README.md` are updated.

10. **MET.** Probe 15 compiles and exits 4 / 4 at `c970483`, and is refused `LEX-005 PARSE-001 PARSE-003` at `c3bdae2`. It lives in `tests/probe/` with `// expect-exit: 4` and a rewritten header.

11. **MET.**
    - `lexical.py`'s loop breaks only on three quotes and skips the byte after a `\`. That is `lexer_next` at `c970483`: `lexer_peek2` and `lexer_peek3 == 34u8`, and `q == 92u8` in both kinds of string.
    - The docstring is re-dated "AND AGAIN AT `c970483`". Its claim that only the close moved is true by `git diff c3bdae2 c970483`: `escapes.npk` and `p_parse_import` are unchanged.
    - Case 18's line 23 is `"""a""b use "./in_block.npk".*; """; use "./after_block.npk".*;`, and the case requires the import `./after_block.npk`.
    - `c3bdae2`'s close, restored in a copy, reddens case 18 alone.

12. **MET, with correction 3.**
    - RX-157 carries "SUPERSEDED IN PART by RX-170" for its block-string paragraph.
    - `CLAUDE.md`, `tests/probe/README.md` and `0.1.0.md:30` say 32 probes, split 25 / 7.
    - On disk there are 25 and 7, and the runner prints probe 25, probe-refused 7.

13. **MET.** The count plant, exactly as the fifth audit filed it, over a clean clone of `37695a7`, in a full run: `217/218`, exit 1, `FAIL tests/unit/bytes_oob_get_empty.npk: … exited 94, expected 77`. The unit suite still judges 47.

14. **MET.**
    - Reader put back in text mode: `217/218`, red on the same unit.
    - Second defence deleted: `217/218`, red on the same unit.
    - Both removed: `217/217` GREEN, with the unit suite at 46 and the skip line naming `tests/unit/bytes_oob_get_empty.npk`.
    - These three ran under `--selfcheck-inner`, as the triage's did, because the self-check reddens those copies first. The both-removed tree in an ordinary run stops at the self-check, with cases 18, 19, 20 and 23 red.

15. **MET.**
    - Escaped syscall plant: `src/core/zz_pid.npk` calls `sys(39i64)`, and a unit imports it as `"..\x2f..\x2fsrc/core/zz_pid.npk"`. It builds and runs 0 / 0 through that path.
    - The full run is `220/221`, red: "`npk.zz_pid.zz_pid` calls `npk_sys6`", with B-2 on 49 units. The plain-path control gives the same red.
    - Escaped layering plant: `use "..\x2fengine/engine.npk".*;` appended to `src/core/limits.npk` gives `218/219`, red. `check_layering` reports "`src/core/limits.npk:108`: `core` imports `engine`".

16. **MET.** The CR-hidden owning `Frame`, appended to `src/syntax/syntax.npk`, gives `218/220`, red. `check_vec_elements_own_nothing` reports "`Frame` … holds `string`" at 21:5 (`Vec<Frame>`) and 21:24 (`vec_init::<Frame>`).

17. **MET.**
    - Cases 19, 20 and 21 exist. Case 18 carries the lone-CR lines 17–19 and the escaped paths 20–22.
    - The self-check over mutated copies at `c970483`:
      - reader in text mode: 18 and 20 red
      - escape decoding removed: 18 and 21 red
      - second defence removed: 23 red
      - both: 18, 19, 20 and 23 red
      - unmutated control: none red

18. **MET.**
    - RX-157 carries "SUPERSEDED IN PART by RX-165".
    - B-4d now says the two defences "share no reader", and takes `main` from the compiler's IR.
    - `stages.py`'s docstring, `run.py` (now lines 47–60), `harness/README.md` (now 63–66) and `TESTING.md` V-20 item 18 (now 284–290) are corrected. Each keeps the old wording in a dated note.
    - No live "every lexical form the compiler has" remains.

19. **MET.** Each plant was appended to `src/syntax/syntax.npk` in a copy and judged by `check_vec_elements_own_nothing` itself:

    | plant | result |
    |---|---|
    | the `#ByteSet()` splice | fails ("a macro splice or an attribute") |
    | `fixed int32:lo` | passes |
    | `Lit = (1i32); Dot = (2i32);` | passes |
    | controls: `#name_fields()`, a `fixed string` field, `Lit(string)` | each fails |
    | nothing planted | passes |

20. **MET.**
    - N-25 was raised (O-N22, the compiler's DEF-104), and its answer is recorded.
    - The fifth audit's own reproducer, `id::<string>`, is `TYPE-047` at 3:5 at `c970483`, and 95 / 95 at `c3bdae2`.
    - `tests/rejection/vec_alias_generic_passout.npk` (`id::<Vec<int64>>`) gives exactly `TYPE-047` at 27:5, its `pass x;`.
    - S-23b's row reads "refused `NITPICK-TYPE-047` at `c970483`", and `vec.npk`'s "CANNOT BE COPIED" is qualified (line 223).

21. **MET.**
    - Case 22 is live. It goes red with the run count narrowed to one (22), and with only the first leg observed (11 and 22).
    - N-29's six lines are corrected: O-N21's DEF number, `0.1.0.md`'s probe counts, the gate sentence, "every lexical form", `vec.npk:183`, and N-22's sites.

22. **MET.**
    - Four programs: N-21's reproducer, its imported-struct twin, and M8 (a generic with a `Vec<T>` local) at `int64` and at `string`.
      - At `c3bdae2`, `llc` refuses all four with "Cannot allocate unsized type".
      - At `c970483`, each builds and runs 0 / 0.
    - `0.1.0.md` §5 has its dated note.
    - All eight N-22 sites read "in our pin since `c970483`". A two-parameter `main` is `TYPE-083` at 2:1 at `c970483` and compiles at `c3bdae2`; the sweep holds no `TYPE-083`.

23. **MET.**
    - A clean clone of `37695a7` at `c970483`: `218/218 unit(s) passed in 91.8 s`, GREEN, exit 0.
    - Suites: conformance 1, probe 25, probe-refused 7, parse 117, rejection 21, unit 47. Every suite skipped 0 files, and each count equals the files on disk.
    - Reconciled with the 214 at `c3bdae2` (1 / 24 / 7 / 115 / 14 / 53):
      - probe: +1 −1 +1 (15 in, 17 out, 18 new)
      - probe-refused: −1 +1
      - rejection: +7
      - unit: −7 +1 (`loan_spellings`)
      - parse: +2 (the two new files)
    - The self-check has 20 live cases (19–23 among them) and 4 pending.
    - CI at `37695a7`, read from the job's log: `218/218`, `GREEN.`, `20 live, 4 pending`, `rx120: every asserted leg held.`. The runs on `06d5c00` and `b34b683` are `success` too.

## The three corrections, judged

- **Correction 1 (item 1 names `2dde296`): RIGHT.**
  - Measured in the compiler repository: `2dde296` is not an ancestor of `c970483`, and `5bdae98` is.
  - Both commits carry the author date 2026-09-25 20:33:35 −0400 and the same step-3g message; `5bdae98`'s is extended by the DEF-104 paragraph.
  - `git diff 2dde296 5bdae98 -- src` is `type_expr.npk` alone, +16/−5: `refuse_pass_of_pointee_owned`, `place_lent_owning` and `refuse_move_of_borrowed` now ask `type_owns_for_move`.
  - `c970483`'s own message says 3g's amendment re-based the chain.
  - So the fifth audit's readings at `2dde296` hold at the pin, except where DEF-104 moved them.

- **Correction 2 (item 8's `vec_get` premise): RIGHT in substance, OVERSTATED in one word.**
  - The premise was false. `8a9fc04`'s `vec.npk` at `c970483` is `TYPE-047` at 487:5 (`vec_get`'s `pass v.items[i]`) and at 533:5 (`vec_pop`), and it compiles at `c3bdae2`.
  - But "compiles ONLY with PD-12's `T: Pod`" is not literally true. A `vec_get<T>` that keeps `Vec<T>:v`, has no bound, and reads through `#wild_slice<T>(v.items, v.count)` compiles at `c970483`. I measured this, and the plan's own §1.3 table says the same.
  - "Only" holds for the spellings the plan accepts; the declined one routes a move of an owning element around TYPE-085.
  - There is no consequence for the tree: `items` is `hidden`, so only `vec.npk` itself could write that body.

- **Correction 3 (items 10–12's totals): RIGHT.** The fifth audit's 24 / 7 was arithmetic for probes 15 and 17 swapping directories. Probe 18, found at planning, adds one program. 25 / 7 is what is on disk and what the runner prints.

## New findings (none blocking)

### N-30 — RX-168's positive half is pinned by nothing, and a fixture header says the suite runs it

Severity: **dormant**, low; one sentence is a **contradiction**.

**The claim.** RX-168 (and `0.0.4e.md` §1.3) rests on this: "a POD struct implements it in one line where it is declared, and `core.npk` re-exports the name so a consumer can". That was measured only in the plan's scratch block 6f.

**What the tree holds.**
- The committed suite calls `vec_get` only on `Vec<int64>` and `Vec<int32>`.
- No committed file implements `Pod` for a struct. `git grep` for an `impl:…:Pod` over `tests/`, `harness/` and `examples/` finds only a comment in probe 18.

**What the documents say.**
- `nitpick-regex/tests/rejection/vec_owning_get_moves_out.npk:21-22` says "`vec_get` at `int32`, `int64` and a POD struct runs throughout the unit suite". That is false in its third term.
- `nitpick-regex/meta/roadmap/0.1/0.1.0.md`'s 2026-09-26 N-15 note tells cycle 0.1 to write `impl:AstNode:Pod` for D6's `ast_get`, which is exactly the path nothing pins.

**Measured here.** A consumer imports `src/core/core.npk`, implements `impl:Pt:Pod` for `struct:Pt = { int32:x; int32:y; }`, and reads twice with `vec_get`. It runs 0 / 0 at `c970483`; without the impl, each call is `TYPE-017`.

**Why it matters.** The property holds today, but nothing would go red if it broke: for example, RX-113's silent cancellation of a re-export by a plain `use`.

**What would resolve it:** a unit that implements `Pod` for a POD struct and reads it back through `core.npk`'s re-export. Otherwise, correct the sentence.

### N-31 — ten sites cite `0.0.4e.md` "step 5" for controls that are its step 6

Severity: **stale**, cosmetic.

In `0.0.4e.md`, step 5 is "the harness, `rx120.sh` and CI". The `c3bdae2` runs of the refusals and the run against the tree before are step 6, blocks 6a and 6b. The ten sites:
- `tests/probe/probe15_block_string_close.npk:19`
- `tests/probe/refused/probe17_lent_field_drop.npk:19`
- in `tests/rejection/`:
  - `vec_alias_param_free.npk:24`
  - `vec_alias_param_grow.npk:15`
  - `sparseset_alias_param_free.npk:15`
  - `bytes_alias_param_grow.npk:16`
  - `vec_alias_for_binding_free.npk:19`
  - `vec_alias_generic_passout.npk:18`
  - `vec_owning_get_moves_out.npk:21`
- `tests/rejection/README.md:145`

All paths are under `nitpick-regex/`. `harness/README.md:99` says "step 6", which is correct.

**What would resolve it:** "step 6" at each site, edited in place. No line count moves, so no `expect-error-at` moves.

### N-32 — the record's "`git log --follow -M40%` follows the others" is false for six of the nine moves

Severity: **cosmetic**, in a record.

**Measured** with `git show -M<n>% --name-status 06d5c00`:
- `-M50%` finds 1 rename, `-M40%` 3, `-M30%` 8, and `-M25%` all 9. Similarities run from 25% to 50%.
- At `-M40%` these six are not followed: probe 15, probe 17, `vec_alias_param_free`, `vec_alias_for_binding_free`, `vec_alias_generic_passout` and `vec_owning_get_moves_out`.
- Provenance is not lost, because `06d5c00`'s message names all nine moves.

**What would resolve it:** the next record says `-M25%`. `0.0.4e.md` is a record, and W-28 leaves it as written.

### N-33 — `0.1.0.md`'s N-21 paragraph still says "stop" right after saying the defect is fixed

Severity: **stale**, cosmetic.

In `nitpick-regex/meta/roadmap/0.1/0.1.0.md`'s N-21 paragraph (about lines 194–206), the 2026-09-26 note ends "so such a helper is buildable now". The next sentences still read: "The harness's `llc` step catches it, so it is loud, not silent. Do not work around it: if a design wants such a helper, record where and stop." That is an instruction to a cycle-0.1 worker that `c970483` retired; item 22 measured the fix.

**What would resolve it:** date the instruction as applying through `c3bdae2`.

### N-34 — item 1's comparison value is recorded in no tracked file

Severity: **unverified by record**, low, on the workbench side.

**Where the value is not.**
- `.internal/toolchain/c970483/PIN.md` records the `npkc` and `npkrt.o` rows only.
- The compiler's `meta/NOTICES.md` counts notices and holds no ladder rows.
- `BOARD.md` and `RECORD.md` do not contain `d36a7e23`.
- `nitpick-regex/meta/roadmap/0.0/0.0.4e.md` records CI's `npkc.ll` value and states that it "equals notice 66's", compared against the dispatch's NOTES.

**Where I verified it instead:**
- the compiler seat's own six-row ladder at `c970483`, as that seat printed it, read-only from its session transcript: `npkc.ll` `d36a7e23…` at 28 188 736 B, `npkc` `e4d95007…`, `npkrt.o` `162b8975…`;
- notice 67's ladder as the orchestrator received it, whose "was" column repeats the same `npkc.ll` row.

**What would resolve it:** record all six ladder rows in `PIN.md` at each pin, so the comparison can be re-made from files.

## Question 11 — does the close wait for O-N28 / DEF-116 (landing 69)? A view, not a condition of the verdict

**My view: (b). The close need not wait.** I would rest that on a different reason from the one recommended.

**"It is no clause of the gate" is weak on its own.** The gate was written before the defect was known. The audit clause exists because a gate written as a list can be met while something is unsafe.

**The stronger reason: nothing in the close, or in `src/`, depends on the defect. Measured:**
- `06d5c00`'s only impls in `src/` are nine scalar `Pod` impls, each taking a lent `self` and doing `pass self`.
- The compiler seat's F14 sweep found exactly one exposed file in this tree: probe 18, the probe that pins the defect.
- An owning element in a `src/` `Vec` is still refused by the S-23a tree check, independently of `Pod` (item 16).
- `src/lib.npk` re-exports neither `Vec` nor `Pod`; its one `pub use` is `ERegexPattern`.
- So the hole reaches only a consumer outside `src/` that imports `core.npk` directly and writes a `move`-self impl. The language's own reference already forbids that impl, and landing 69 will refuse it.

**Where the author's standing default applies.** His recorded default is to hold work that depends on a memory-safety under-enforcement, and not to let a library-side check turn a blocking defect into a non-blocking one. It bites on RX-168's claim that "S-23a's `vec_get` row is the compiler's, for every consumer". That claim is false for such a consumer until landing 69, and RX-168, S-23a, `vec.npk` and probe 18 already say so. No work in this repository relies on that claim, so there is nothing for the default to hold.

**Waiting would also be cheap.** It ties the close to a re-pin that is already owed:
- landing 67 (`BORROW-015`) is on the compiler's `main` as `2eea6f4` as of this audit, and its reach here was measured at zero by the compiler seat (F13);
- 1.6.1 brings the emission-text change;
- landing 68 comes before 69.

That is the author's call.

## Checked and found clean

- **`check_refs`**, run as a program under `-B` on the real checkout: clean, 73 markdown files, leak scan 232 of 232. Neither tree's status moved.
- **`check_record … 0.0.4e`:** record clean.
- **Tracked files:** none holds byte 13, and no `use` path holds a `\`.
- **The `@main` detector**, re-measured at `c970483`: `vec_unit`'s IR defines `@main`, and `vec.npk`'s does not.
- **`src/` code changes in scope** are exactly:
  - `trait:Pod`;
  - nine scalar impls with a lent `self`;
  - `core.npk`'s `pub use "./vec.npk".Pod;` — no plain `use` of `vec.npk` shadows it (RX-113);
  - `vec_get<T: Pod>` reading through `pod_copy`;
  - `vec_pop`'s `move(...)`.
- **Compiler claims in the new decisions, read at `c970483`:**
  - the prelude's `trait:Clone` has no `never fails`;
  - TRAITS_REFERENCE §2 says "An impl's method must have the signature the trait declares — including the contract";
  - `same_signature` in `type_trait.npk` compares the return type and each parameter's type through `same_after_self`, and never a parameter's `move`;
  - the lexer's block-string loop and `lexer_peek3`;
  - DEF-104's three gates.
- **Probe 18** exits 95 / 95 at both pins. Position 42:39 is `move string:self`, which is where F14 says landing 69 refuses.
- **Pressed beyond the checklist, no hole found:**
  - A generic that passes out a field of a lent `Box<T>`, element 0 of a lent `T[2]`, or a `for` binding over a lent array is `TYPE-047` at `c970483` (95 at `c3bdae2`).
  - A generic that passes `<-x` out of a `T->` is a move: the source reads empty afterwards, for generic and concrete functions alike, at both pins.
  - The S-23a check's body reader cannot be cut short by a field's default value, because `p_parse_field` takes qualifiers, `limit`, a type and a name, with no `=`.
- **Known, already disclosed, not re-filed:**
  - `vec.npk`'s `Pod` note has "the workbench registry's O-N28" in lower case after a full stop; the worker recorded this itself.
  - The local O-N28 entry does not carry DEF-116, which the record and the cycle README do. It states nothing false.

## Method

- **Baseline.** A fresh `git clone --no-hardlinks` of `37695a7`, placed beside a read-only link to the workbench's toolchain directory so that `../.internal/toolchain/<pin>` resolved exactly as it does in the real checkout. `NPKC` and `NPKRT` were the `c970483` pair, with digests as in item 1, and LLVM 20.1.2. Temporary files and bytecode were kept out of every tree.
- **Plants.** Each was a full run over its own fresh clone of `37695a7`, and every substitution count was asserted before the run, so a plant that did not apply would have stopped. That made nine full runs:
  - P0–P3;
  - P3 in an ordinary run;
  - the escaped and plain `zz_pid`;
  - the layering edge;
  - the CR `Frame`.

  Nine self-check runs over mutated clones: the unmutated control and eight mutations.
- **Probes.** Each program went through `npkc`, `llc`, `ld.lld` and a run, at −O0 and through `opt -O2`. I used the plan's own `env.sh` helpers (`codes`, `run4`, `sweep`, `bills`, `sizes`), sourced against my clone.
- **N-24.** The check function was called over copies of the tree.
- **Machine.** Runs went one at a time, with 144 GiB available throughout.

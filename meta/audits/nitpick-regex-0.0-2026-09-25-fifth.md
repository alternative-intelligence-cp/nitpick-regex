REPORT nitpick-regex 0.0 audit (FIFTH)
status: DO-NOT-ACCEPT
auditor: npk:auditor, claude-opus-5-5
toolchain: c3bdae2
scope: 4420c45..40074b6 (6 commits: the fourth triage 4bab46f and acaf99c; the 0.0.4d plan 46ab35b and fdc190f; 0.0.4d itself 8a1c4da and 40074b6)

Paths are relative to the workbench root (the directory holding `BOARD.md`), because this message is filed verbatim and the reference gate refuses a tracked file that contains a home directory. The compiler is `../nitpick`.

Every compiler claim below was read with `git show`:
- at `c3bdae2`;
- for the re-pin, also at `395308f` (1.6.0 step 3e) and at `2dde296` (step 3g). `2dde296` sits on the compiler's branches `s15-160-3` and `s15-160-3g`. It is not yet on `main`, whose head I read at `6fb85d3`.

My probes and plants ran in a session scratchpad that will not survive, so every reproducer that carries weight is inline. Below, `<CR>` is one byte, 13, and nothing else.

I wrote nothing. `nitpick-regex` stayed clean at `40074b6`, and the workbench and compiler trees are clean. Wall clock was 20:36–21:20 EDT. earlyoom's last signal today was at 18:00:15, to another seat's `clam`, so none of my runs was touched.

# W-22 AUDIT — `nitpick-regex`, cycle 0.0 close, fifth pass

## Verdict: DO NOT ACCEPT

There is one blocking finding, and it sits in the fix for the fourth pass's first blocking finding.

- **BL-9 — the harness's "one reading of source" is not the compiler's.** I measured two ways it differs, and each reopens a route the tree states is closed.
  - **A lone carriage return (byte 13)** takes a red unit out of a GREEN run: `209/209`, exit 0, over a unit that exits 94 where it expects 77. Both RX-157 defences fall together, because the `main` exception is computed through the same reader it is said to survive. The same byte clears an owning element in a `src/` `Vec` (`210/210` GREEN).
  - **An escape in an import path** hides a syscall in `src/` from B-2. The plain path gives `212/213`, red, naming `npk_sys6` (RX-008). One `\x2f` in the path gives **`213/213` GREEN**. The same escape hides a forbidden `core`→`engine` import from `check_layering`.

There are six non-blocking findings:
- **N-24:** the S-23a check clears a macro splice named after a POD type, and refuses two non-owning shapes.
- **N-25:** a compiler-defect candidate. TYPE-047 is not asked of a lent `T` inside a generic body, so `func:id<T> = T(T:x) { pass x; }` duplicates ownership. It is a double free with no library code, and a second handle on a `Vec`. It is unchanged at 3g.
- **N-26:** a sixth loan shape, unpinned. A `for` binding over an array of containers frees the element's block through `@x`.
- **N-27:** RX-159's "every run" half has no self-check case guarding it.
- **N-28:** self-check case 18 tests neither block-string close, so DEF-98's re-pin is guarded only by prose.
- **N-29:** stale and over-wide statements.

**Everything else in scope holds.** The fourth pass's dispositions stand, except where BL-9 reopens BL-7.

0.0.4d is sound:
- Every copy path I built is refused TYPE-046 or TYPE-047, or is a loan. The one exception is N-25's generic move.
- The marker costs nothing measurable. Bills, sizes and undefined symbols are identical to `4420c45` at −O0 and −O2. `WildLeak` still traps 96.
- Its controls reproduce.

**0.0.4d's correction of the fourth pass is right.** The fourth pass expected move-only to change `vec_get`'s signature. It does not, because a by-value parameter is a loan; that expectation was the fourth pass's error.

**The loan's refusal is excluded from this verdict, as directed.**
- 3g's rule, read at `2dde296`, refuses all five pinned loan files and N-26's shape.
- It does not reach N-25.
- I agree with this seat's recommendation that the close wait for the re-pin. BL-9's fixes can land in the same subcycle, and the checklist at the end keeps the post-re-pin check narrow.

**Method.**
- **Baseline:** a fresh `git clone` of `40074b6`, run with the pinned toolchain.
  - `npkc` is `5fd636b9…` and `npkrt.o` is `162b8975…`, both equal to `SHA256SUMS`; LLVM is 20.1.2.
  - Result: **210/210 GREEN in 85.7 s, exit 0**. Self-check 15 live / 4 pending; eight tree checks; B-2 on 52 units; residue 9 of 9; 0 pending.
- **Plants:** each was a full run over its own clone, or the check function called over a copy of `src/`.
- **Probes:** each went through `npkc`, `llc`, `ld.lld` and a run, at −O0 and through `opt -O2`.
- **Harness mutations:** each was a self-check run over a mutated clone.

---

## BLOCKING

### BL-9 — `lexical.py` is not the compiler's reading of source, in two measured ways; each reopens a route the tree calls closed

Severity: **contradiction**. Measured.

**What the tree claims:**
- `nitpick-regex/meta/DECISIONS.md:3376-3380` (RX-157): the `main` exception "holds whatever the reader gets wrong next, which part 1 cannot promise about itself".
- `nitpick-regex/harness/stages.py:77-84`: "Either defence alone closes BL-7's route; both are kept, because the second is what survives a defect in the first."
- The same claim appears at `nitpick-regex/meta/specs/BUILD.md:289-302` (B-4d), `nitpick-regex/harness/run.py:47-51` and `nitpick-regex/harness/README.md:57-60`: "neither a marker line nor a comment in another file can move a red out of a green run".
- RX-157 says `imports()` reads a `use` "the way the parser's `p_parse_import` does".

#### (a) A lone carriage return

**The mechanism.** Every harness read of `.npk` text uses Python text mode with the default `newline=None`:
- `stages._read` (`stages.py:94-96`);
- `treecheck._read` (`treecheck.py:110-112`);
- `build.reaches_src` (`build.py:395`).

That mode turns a lone CR into `\n` before `lexical.py` sees the text. The compiler behaves differently:
- it ends a line comment at byte 10 only (`lexer_skip_trivia`, `../nitpick/src/frontend/lexer.npk:129` at `c3bdae2`);
- it treats byte 13 as whitespace (`:95`).

So after `// note<CR>`, what is still comment to the compiler is code to the harness.

**Probes at `c3bdae2`:**

| file | the compiler | `lexical.py` |
|---|---|---|
| `// note<CR>use "does_not_exist.npk".*;`, then a `main` that exits 3 | `npkc` 0, runs 3 / 3: no import. With LF instead of CR it is refused `NITPICK-RESOLVE-005` | `imports` returns `[(3, 'does_not_exist.npk', False)]` |
| `// note<CR>/*` above a `main` that exits 4, with no `*/` after it | `npkc` 0, runs 4 / 4 | `declares_main` returns False, and the rest of the file is blanked |

**The count, measured.** This was a full run over a clone of `40074b6`, using the fourth pass's own red unit. Two lines changed:
- In `tests/unit/bytes_oob_get_empty.npk`, `expect-exit: 94` became `77` (I re-checked that it exits 94 at both levels), and one line was added above `func:main`: `// note<CR>/*`.
- In `tests/unit/vec_unit.npk`, after `mod:vec_unit;`, one line was added: `// see<CR>use "bytes_oob_get_empty.npk".*;`.

Result: `unit (program) 50 unit(s)` (the baseline judges 51), `209/209 unit(s) passed in 85.9 s.`, `GREEN.`, exit 0. The red unit's only line in the log is the parse sweep's `ok`.

Neither edit touches a marker or `PENDING.txt`. On a terminal the two lines render as `/* note` and as a plain `use` line, because a CR returns the cursor to the start of the line.

**Why both defences fell.** A file is skipped only when both conditions hold:
- a sibling imports it; and
- `not _declares_main(p)` (`stages.py:91`).

But `_declares_main` is `lexical.declares_main(_read(path))` (`stages.py:106-107`): the same read, through the same module.

The independence the triage measured (0.0.5 §11, m15a–c) was correct for what it tested: one reader defect, the old line reader, which reads too many imports. A defect that blanks too much text defeats both defences at once. RX-154's "two edits in two files, one of them a reviewed line with a reason" is false again: here there are two edits, and neither is reviewed.

**The same byte blinds every tree check.** I appended this to `src/syntax/syntax.npk` in a copy:

```
use "../core/vec.npk".*;
struct:Frame = {
    int32:lo;   // the offset<CR>/*
    string:name;
    // */
};
pub func:frames = int64() never fails {
    Vec<Frame>:v = raw vec_init::<Frame>(1i64);
    drop vec_push(@v, Frame{ lo: 1i32, name: string_concat("ab", "c") });
    int64:n = v.count;
    drop vec_free(@v);
    pass n;
};
```

- `npkc` exits 0. The struct literal names `name`, so the compiler has that field. With LF in place of the CR, the same file is refused `NITPICK-TYPE-026`.
- The same struct, copied in a probe, is refused `NITPICK-TYPE-046`, so it owns.
- `check_vec_elements_own_nothing` examined six element types and cleared every one.
- The full run was **210/210 GREEN, exit 0**.

#### (b) An escape in an import path

**The mechanism.**
- The compiler's `StringLit` payload is the *decoded* string (`decode_string` in `lexer_next`), and `p_parse_import` (`../nitpick/src/frontend/parse_decl.npk:857`) takes that payload as the path.
- `lexical.imports` returns the *undecoded* text, and its docstring says so (`lexical.py:215-216`: "`target` is the string literal's text, not decoded -- nothing here writes an escape into a path"). That is a statement about the tree, not a check.

**Measured on one unit.** In a copy of `tests/unit/vec_unit.npk` I wrote `use "..\x2f..\x2fsrc/core/vec.npk".*;`:
- It compiles, links and runs 0 / 0 through `src/core/vec.npk`.
- `lexical.imports` gives `..\x2f..\x2fsrc/core/vec.npk`.
- `build.reaches_src` answers False; with the plain path it answers True.
- Both B-2 scans run only under `if scanned:` (`build.py:213`, `:224`, `:253`), so this unit is not scanned.

**End to end.** I made two clones of `40074b6` and gave each the same new file, `src/core/zz_pid.npk`:

```
mod:zz_pid;
pub func:zz_pid = int64() never fails {
    Result<int64>:r = sys(39i64);
    if (r.is_error) { pass 0i64; }
    pass 1i64;
};
```

Each clone also got a unit whose `main` calls `raw zz_pid()` and expects exit 0. The results:
- **Plain path:** `212/213`, exit 1. The run says "``npk.zz_pid.zz_pid` calls `npk_sys6`, and the baseline does not. `nregex` makes no syscall … (RX-008)". B-2 scanned 53 units.
- **The path spelled `"..\x2f..\x2fsrc/core/zz_pid.npk"`:** **`213/213` GREEN, exit 0**. B-2 scanned 52 units, and this one was not among them.

**The layering check.** I appended `use "..\x2fengine/engine.npk".*;` to `src/core/limits.npk`. It compiles. `check_layering` reports 0 failures over the same 65 edges. The plain-path control reports 1 failure: "`core` imports `engine`, which is to its LEFT…".

**Blast radius today is nil.** I swept the tree: no tracked file holds byte 13, and no `use` path holds a `\`. This still blocks, for three reasons:
- the tree states the property without qualification;
- the fix for a blocking finding reproduced that finding's class;
- the second defence's independence is false by construction.

**What would resolve it:**
1. Read `.npk` text the way the compiler does: as bytes, or with `newline=""`, with `\n` as the only line end in `lexical.py`. Decode an import target by the lexer's escape rules, or have the harness refuse a `use` whose path contains a `\`.
2. Make the `main` exception independent of `lexical.py`. The parse sweep already runs `npkc` on every `.npk` and emits IR, so "declares `main`" can be taken from the compiler's own output, or cross-checked there.
3. Add self-check forms for:
   - a lone CR in a line comment, with an import after it;
   - a lone CR in a line comment, with a `/*` after it;
   - an escaped import path;
   - at the re-pin, a `""` inside a block string (N-28).

   Show each form failing against a harness without the fix. Re-run the count plant above with each defence removed alone, and with both removed.
4. Supersede RX-157 in part (its independence sentence), and correct B-4d, `stages.py:77-84`, `run.py:47-51`, `README.md:57-60` and `TESTING.md:284-286` ("every lexical form the compiler has").

---

## NON-BLOCKING

### N-24 — The S-23a check: one more wrong clear, and two wrong refusals

Severity: **contradiction**, low. Each plant was appended to `src/syntax/syntax.npk` in a copy, with a `Vec<X>` and a `vec_init::<X>` of the planted type.

**Wrong clear: a macro splice named after a POD type.** The plant:

```
macro:ByteSet = () {
    string:name;
};
struct:Frame = {
    int32:lo;
    #ByteSet();
};
```

- The compiler accepts it. Splices are live in struct bodies: `p_parse_record`, and the compiler's own `tests/accept/splicing.npk`.
- The copy of such a `Frame` is refused `NITPICK-TYPE-046`, so `Frame` owns.
- The check reports **0 failures**. `_members` (`treecheck.py:604-616`) returns `#ByteSet()` as a field type, and `_deny_reason` resolves `ByteSet` against `src/core/byteset.npk`'s POD struct.
- Control: the same macro named `name_fields` gives 2 failures.

**Wrong refusal 1: a `fixed` field.** For `struct:Span = { fixed int32:lo; int32:hi; };` the check says "holds `fixed`". The parser's qualifiers are `stack`, `wild`, `wildx`, `fixed`, `nodrop`, `move`, `sealed` and `hidden` (`p_qualifier_bit`). `_FIELD_QUALS` (`treecheck.py:553`) strips only `sealed`, `hidden` and `limit<…>`.

**Wrong refusal 2: a parenthesised discriminant.** For `enum:Kind = { Lit = (1i32); Dot = (2i32); };` the check says "holds `i32`". `_members` reads `(1i32)` as a payload list, and `_IDENT_RE` finds `i32` inside the literal.

In a probe, both `Span` and `Kind` copy freely and the program runs 3 / 3.

**Cosmetic.** `treecheck.py:535` excludes `simd` and `complex` as "not a plain value". `type_drops_recorded` says both own nothing ("lanes of plain scalars", "two plain components"). The conservatism is deliberate; the stated reason is not the compiler's.

**Pressed, and closed by the language:**
- A POD `struct:Path` under `src/` shadowing the prelude's owning `Path` is refused `NITPICK-RESOLVE-001`; measured.
- Every allowlisted scalar is a keyword (`keywords.npk` at `c3bdae2`), so none can be shadowed.
- `fd` and the flag families resolve to `TY_KERNEL` and `TY_FLAGS`, which own nothing.

**What would resolve it:**
- Deny any member whose text begins with `#`.
- Strip or explicitly name `fixed`, `nodrop` and `move`.
- Read enum payloads only from `Name(…)`, never from `= expr`.
- Otherwise, state these limits beside RX-158.

### N-25 — Compiler-defect candidate: TYPE-047 is not asked of a lent `T` in a generic body, so a generic function hands back its lent parameter as a second owner

Severity: **unverified claim about the compiler**, measured, and not yet in any record. Raise it now (W-11, W-27).

**The mechanism, at `c3bdae2`:**
- `refuse_move_of_borrowed` (`../nitpick/src/frontend/type_expr.npk:490`) returns early unless `type_drops(ty)` is true (`:495`). That is false for an unsubstituted `T`.
- D-264 fixed the same gate for TYPE-046 by asking `type_owns_for_move` instead (`:570`), which treats `TY_PARAM` as owning. That was DEF-23 (`OPEN_DECISIONS.md:858` at `2dde296`). This is its TYPE-047 sibling, never swept.
- A generic body is checked once, so the instance is never re-asked.
- `refuse_move_of_borrowed` is byte-identical at `2dde296`.
- 3g's `place_lent_owning` (`type_expr.npk:434` at `2dde296`) asks `type_drops` too. By that reading, `@x` of a lent `T` in a generic body is not refused at 3g either.

**The reproducer, with no library code.** The `failsafe` is `vec_moves.npk`'s, verbatim.

```
mod:zzid;
func:id<T> = T(T:x) never fails {
    pass x;
};
func:twice = int64() never fails {
    string:a = string_concat("<a 67-byte literal>", "c");
    string:b = raw id::<string>(a);
    pass string_byte_length(b);
};
func:main = int32(cstring[]:_~argv) {
    int64:n = raw twice();
    exit 0i32;
};
```

- The program exits **95** at −O0 and through `opt -O2`: `a` and `b` are both dropped, a double free.
- Passing `b` out to the caller instead, the caller reads the free poison: **70**.
- Control: the same function written non-generically, `func:idstr = string(string:x) never fails { pass x; };`, is refused `NITPICK-TYPE-047`.
- At `Vec<int64>`: `Vec<int64>:b = raw id::<Vec<int64>>(a);` compiles, and after `vec_free(@a)` a read of `b` returns the poison (70).

**Reach here is nil.** No `src/` generic takes a lent bare `T`: `vec_push`, `vec_set`, `vec_insert` and `drop_element` take `move T`.

It does contradict, in effect, `src/core/vec.npk:183` ("SINCE CYCLE 0.0.4d A `Vec` CANNOT BE COPIED"), since a consumer's generic identity function duplicates a `Vec`.

**What would resolve it:**
- Raise it to the compiler seat as DEF-23's TYPE-047 half, together with TYPE-085's same gate.
- Pin it here as a unit, PINNED, NOT ENDORSED.
- Give it a row in S-23b.
- Qualify `vec.npk:183`.

### N-26 — A sixth loan shape, unpinned: a `for` binding over an array of containers

Severity: **dormant**. The tree's loan pins do not cover it.

At `c3bdae2`, `for (Vec<int64>:x in arr) { drop vec_free(@x); }` over `Vec<int64>[2]:arr = [move(a), move(b)]` compiles. After the loop:
- `arr[0i64].cap` still reads 2 and `count` 1;
- `vec_get(arr[0i64], 0i64)` returns the poison (**70**);
- freeing both elements is **95**, because the guard sees a different header.

A read-only loop runs clean (0). Over `string[2]` the binding is a non-owning view: the loop runs clean, and a write through `@x` leaves the element intact.

**Why 3g should cover it.** The parser builds the binding as "a full ParamDecl" (`parse_stmt.npk:752` at `2dde296`). So, by 3g's source, `place_lent_owning` treats it as a loan and TYPE-085 should refuse `@x` there.

**But nothing records it:**
- nothing in the tree pins it;
- S-23b's table (`SAFETY.md:615-623`) omits it;
- the board's exposure sweep covered `for … in` *over a parameter*, not a binding over a local array.

`src/` has no `for` in code, so reach is nil.

**What would resolve it:** pin it as a loan unit now, give it a row in S-23b, and check at the re-pin that it is refused.

### N-27 — RX-159's "every run" half has nothing testing it

Severity: **dormant**.

**Measured.** In a clone I changed `_pending`'s `for _ in range(exp.stress):` to `for _ in range(1):`. The self-check reported **15 live cases passing and 0 failures**.

No pending fixture carries `stress:`, and every one exits a constant code on both legs. So neither "every run" nor "one leg disagreeing with the other" is exercised by any case. Both are guarded only by 0.0.5 §11's one-time function-level stand-ins.

The −O2 leg itself *is* guarded: case 11 requires "41 through opt -O2".

**Reproduced as the triage recorded:**
- deleting the `PENDING.txt` second direction fails case 16 alone;
- deleting the residue unused-entry block fails case 17 alone.

**What would resolve it:** add a case whose pending unit changes exit from run to run and must go red; or state the gap in B-5b.

### N-28 — Case 18 tests neither block-string close

Severity: **dormant**.

`_LEX_TEXT`'s block string (`selfcheck.py:445-447`) contains no `""`. I switched `lexical.py` to `395308f`'s three-quote close, and case 18 still passes, unchanged.

The two rules read the same text differently. For `"""a""b use "./x.npk" """`, the pin's rule reads an import of `./x.npk`, and 3e's rule reads none.

At the re-pin, probe 15 reddens, but only its header's prose ties that to changing `lexical.py`. A re-pin that moves the probe and forgets the reader stays green.

This is BL-9's resolution 3.

### N-29 — Stale and over-wide statements

Severity: **stale / cosmetic**.

- `meta/OPEN_QUESTIONS.md:514` says "no DEF number has come back". The orchestrator's update recorded in `40074b6` says O-N21 is DEF-102 (TYPE-085, `2dde296`). `40074b6` touched only `0.0.4d.md` and the cycle README.
- `meta/roadmap/0.1/0.1.0.md:30-33` gives "28 language probes, 22 … and 6 refusals". After 0.0.4d the numbers are 31, 24 and 7, as `CLAUDE.md` and `tests/probe/README.md` say.
- The gate sentence at `meta/roadmap/0.0/README.md:524`, "every `tests/unit/*_alias_*` shape is refused", still counts `sparseset_alias_swap`, which must run. The dated note under it says so; the sentence itself needs rewording before a close is accepted against it.
- `TESTING.md:284-286` and `selfcheck.py:46`, `:430` and `:597` say "every lexical form the compiler has". That is too wide (BL-9, N-28).
- `vec.npk:183` says "A `Vec` CANNOT BE COPIED". That is true of TYPE-046's copy, but not of a generic function's move out of a loan (N-25).
- N-22's eight sites say TYPE-083 "WILL refuse … no pin carries it yet". That is true of every kept pin. It has since landed on the compiler's `main` at `d156c4f` (step 3c).

---

## THE FIVE PLACES I WAS TOLD TO PRESS

### 1. `lexical.py`'s fidelity

**Two disagreements that change an import or a tree check:** the lone CR and the path escape (BL-9), plus the untested block-string close (N-28).

**Matched against `lexer_skip_trivia` and `lexer_next` at `c3bdae2`:**
- `//`;
- `/* */`, which does not nest, and runs unterminated to the end of the file;
- `"…"`, where `\` skips one byte (including an LF after it) and a newline ends the literal;
- `""` as the empty string;
- `"""`, closing at the first `""` and consuming three bytes there (DEF-98's pin behaviour);
- `r"…"` only at the start of a token;
- `'x'`, with its escapes, one code point, and the resync;
- templates with nested interpolations;
- `pub` with trivia before `use`.

**What `p_parse_import` accepts.** It takes only a `StringLit` as a file path. A raw or block string falls into the logical-path branch and does not resolve, so ignoring those is harmless.

**Differences confined to files the compiler refuses:**
- an interpolation nested more than eight deep (the lexer stops recording it);
- `_?`, `_!`, `_~` and `_^` at the start of a template part (lexed as operators);
- an invalid-escape character literal (the lexer does not resync);
- `e+r"` after a float.

**What moves at the re-pin.** The lexer diff from `c3bdae2` to `2dde296` is DEF-98 alone. `parse_decl.npk`'s DEF-103 does not touch imports, and I swept the tree for keyword-named declarations and found none. So what moves is:
- `lexical.py`'s close, which must read `"""` with `\` still escaping;
- its docstring's "read at `c3bdae2`";
- case 18;
- probe 15, which leaves `refused/` with `expect-exit: 4`;
- RX-157's block-string paragraph;
- the counts. The probe totals stay 24 / 7, because probe 17 moves the other way at the same re-pin.

### 2. The default-deny S-23a check

**It wrongly clears:**
- a CR-hidden `string` field (BL-9);
- a macro splice named after a POD type (N-24).

**It wrongly refuses:**
- a `fixed int32` field;
- a parenthesised discriminant (N-24).

**Closed by the language:** shadowing a prelude name, and shadowing a scalar.

The fourth pass's twelve shapes still fail. I spot-checked four of them (M1, M9, M10, M12), each planted alone.

### 3. The pending marker and the two second directions

**Can a marker excuse the wrong failure, on either leg?** For a deterministic failure, **no**. Every leg is built, scanned and linked. Every run on every leg must give the named exit. Case 11 requires the −O2 leg.

**The second directions reproduce:** m16 fails case 16 alone, and m17a fails case 17 alone.

**What remains:**
- the exit-as-identity limit, stated in `expect.py` and B-5b;
- the "every run" half, which is unguarded (N-27);
- disagreeing legs, which nothing exercises.

A marker on a `check` or `compile/negative` unit is read and never consulted, so it excuses nothing there.

The route that bypasses the marker entirely is BL-9 (a).

### 4. The move-only marker

All measured at `c3bdae2`, −O0 and `opt -O2`, against `src/` at `40074b6`.

| shape | result |
|---|---|
| `Vec<int64>:w = v;` / a struct holding a `Vec`, copied / `SparseSet:t = s;` / `Bytes:c = b;` | `NITPICK-TYPE-046` |
| `Vec<int64>[2]:arr2 = arr;` / `Vec<int64>:x = arr[0i64];` | `NITPICK-TYPE-046` |
| `Vec<int64>?:o = v;` / `p.insts = v;` / `Prog{ insts: v, … }` from a named local / `Vec<int64>:w = <-p;` | `NITPICK-TYPE-046` |
| inside a generic: `Vec<T>:w = v;` at `int64` and at `string`; `T:y = x;` at `Vec<int64>` | `NITPICK-TYPE-046` |
| a lent parameter copied into a local, into a struct literal, or into an array literal | `NITPICK-TYPE-046` |
| `move(v)` of a lent parameter; `pass v` of a lent `Vec`, `SparseSet` or `Bytes`; `pass p.insts` of a lent struct | `NITPICK-TYPE-047` |
| `pass <-p` through a `Vec<int64>->` | a MOVE: the source then reads `cap` 0; one handle |
| a by-value parameter that only reads (`vec_get`) | a LOAN; compiles unchanged |
| `for (Vec<int64>:x in arr)` | a LOAN (a `DeclParamDecl`); read-only runs 0; through `@x`, 70 / 95 (N-26) |
| `func:id<T> = T(T:x) { pass x; }` at `Vec<int64>` | **compiles, and gives a second handle**: 70 (N-25) |
| a `Vec` never freed | `WildLeak`, 96 |

**Nothing moved.**
- **Bills:** REACH-003 for nine consumers is identical at `4420c45` and at `40074b6`: 10, 10, 10, 10, 6, 11, 6, 6, 6.
- **Sizes:** identical. `Vec<int64>` 24, `SparseSet` 56, `Bytes` 32, `Vec<uint8>` 24.
- **Undefined symbols:** identical at −O0 and −O2 for `vec_unit`, `sparseset_unit`, `bytes_unit`, `byteset_unit` and `vec_owning_freed`.
- **New definitions:**
  - `bytes_unit` gains `bytes_capacity`.
  - `vec_owning_freed` gains `npk.drop.1911`, `npk.drop.1913` and two `npk.vacant` twins. `npk.drop.1911` drops field 3 only, through a loop that exits at once (`icmp uge i64 %i, 0`); `items` is never touched.

**Controls A and B reproduce.**
- At `40074b6` the five copy fixtures are refused once each, at 28:5, 25:5, 32:5, 27:5 and 30:5, and `bytes_buf_ptr_write` is refused `NITPICK-TYPE-080` at 24:6.
- Against `4420c45`'s `src/`, all six compile cleanly.
- With an `int64[0]` marker, the five copies compile cleanly.

**Probes 16 and 16b are sound.** 3g's TYPE_REFERENCE §9.2 now states the same fact they record.

### 5. The loan

It is excluded from the verdict. The checklist below states what the tree must show after the re-pin.

---

## DISPOSITIONS RE-CHECKED AGAINST THE TREE

- **BL-7 — FIXED for its plant; REOPENED by BL-9 (a).**
  - Case 15 passes, and m15a–c hold for the reader they tested.
  - The claim that the two defences are independent is false.
- **BL-8 — FIXED as a correction; holds.**
  - I spot-checked RX-156's marker, RX-160, `COMPILE.md` C-1's flag, `ENGINES.md` R-5 and R-8, and the 0.7 README.
  - 0.0.4d then landed N-15, with the swap and `vec_moves` running 0.
- **N-18 — FIXED; holds for the twelve shapes.** New gaps are N-24 and BL-9 (a).
- **N-19 — FIXED for the −O2 leg** (case 11). The "every run" half is not guarded (N-27).
- **N-20 — FIXED.** m16 and m17a reproduce.
- **N-21 — a compiler defect; now DEF-97, fixed at step 3d (`f758995`), which is not in the pin.**
  - `0.1.0.md` §5 records it without the number.
- **N-22 — FIXED.** It is true at the pin. See N-29 on `d156c4f`.
- **N-23 — FIXED.**
  - I count 86 loops at `40074b6` by two methods: every one has `decreases`, and none is `unbounded`. `CLAUDE.md` says 86.
  - The five "links and runs" sites are corrected (I read the `ci.yml` header).
  - `vec_owning_freed_small_rounds.npk` is committed.

## CHECKED AND FOUND CLEAN

- **Baseline:** as in Method.
- **CI:**
  - All six pushed runs from `4bab46f` to `40074b6` concluded `success`.
  - For HEAD, run `36204979166`, job `108299484817`, read through the API: compiler pin `c3bdae270d63…`; LLVM 20.1.2; `npkc.ll` 28 111 929 B, `4029fc70…`; `rx120: every asserted leg held.`; `1 nested repository pruned: .nitpick`; 15 live / 4 pending; 0 PENDING; `210/210`, `GREEN.`
- **`check_refs`:** clean. 71 markdown files; leak scan 219 of 219.
- **`check_record 0.0.4d`:** clean. The one result for 0.0.5 says only that HEAD belongs to 0.0.4d.
- **RX-163:** nine test code lines read `bytes_capacity`, and the only `.buf` outside `bytes.npk` is the refused fixture.
- **RX-164:** there is no live `requires`, `ensures`, `invariant` or `prove` in `src/` code. P-1b is present. The author's answer on Q-6 is at `RECORD.md:6879`.
- **Compiler facts read at source:**
  - `type_drops_recorded` answers an array by its element; `TY_KERNEL` and `TY_FLAGS` own nothing;
  - `type_owns_for_move` and `refuse_move_of_borrowed`;
  - the prelude and the runtime are unchanged between `c3bdae2` and `2dde296`;
  - `395308f`'s `lexer_peek3`;
  - 3g's `place_lent_owning` and `refuse_write_path_ex` (loan, view, frozen), and the `for` binding built as a `DeclParamDecl`.
- **By-value container parameters:** every one in the tree reads only, except the five loan files. That covers `vec_get`, probe04's `len2`, probe08's `sset_has`, and the five loan files themselves.

**Pressed and found nothing:**
- shadowing a prelude name (RESOLVE-001);
- scalar shadowing;
- a raw or block string as an import path;
- returning a lent parameter, non-generic (TYPE-047);
- a whole-binding write through `@x` of a lent `string` (safe: the drop flag holds);
- the triage's m16 and m17a;
- earlyoom.

---

## POST-RE-PIN CHECKLIST — what the tree must show for this pass to be the accepting audit

These are to be verified at a pin that has `2dde296` (1.6.0 step 3g) as an ancestor. Each item is a measurement, not a reading. Separately, BL-9 must be fixed and N-24 to N-29 each dispositioned in a triage record; those fixes may land before the re-pin or with it.

**The pin**
1. `.internal/toolchain/<pin>/` has `PIN.md` and `SHA256SUMS`, and both digests match. `git merge-base --is-ancestor 2dde296 <pin>` is true. LLVM is 20.1.2. `ci.yml`'s compiler commit equals the pin, and CI's log prints that commit and the `npkc.ll` digest the pin's commit stamps.
2. `rx120.sh` is green at the pin. The prelude and runtime are unchanged from `c3bdae2` to `2dde296`, so expect 5, 6 and {`npk_sys6`}. `SYMBOLS.txt` and `EDGES.txt` are either unchanged, or re-recorded in a commit of their own.
3. The nine bills are re-measured by REACH-003 (at `c3bdae2`: 10, 10, 10, 10, 6, 11, 6, 6, 6). Sizes are re-measured: probe 16 exits 24; `SparseSet` 56; `Bytes` 32.

**The loan (DEF-102, `NITPICK-TYPE-085`)**
4. `vec_alias_param_free`, `vec_alias_param_grow`, `sparseset_alias_param_free` and `bytes_alias_param_grow` are each refused with exactly {`NITPICK-TYPE-085`}, under B-7 equality, at a measured position (the `@` in each callee). Each moves with `git mv` to `tests/rejection/`, and its "PINNED, NOT ENDORSED" header is rewritten.
5. `probe17_lent_field_drop` is refused exactly {`NITPICK-TYPE-085`} at its field write, moves to `tests/probe/refused/`, and has its verdict recorded.
6. N-26's `for`-binding shape, pinned before the re-pin, is refused TYPE-085 at `@x`. **If it is not refused, 3g does not close the loan and the gate stays unmet.**
7. Each refusal is shown to be the pin's: every one of them runs at `c3bdae2`. One positive twin is written as TYPE-085's message prescribes (a `move Vec<int64>:v` parameter with `move(v)` at the call site, or a pointer parameter) and runs clean at the new pin.
8. The parse sweep at the new pin refuses nothing else. `vec_get`'s `Vec<T>:v`, probe04's `len2(Vec<T>:self)` and probe08's `sset_has(SparseSet:s, …)` all compile.
9. The documents are updated:
   - the gate sentence (`0.0/README.md:524`) is reworded so it no longer counts `sparseset_alias_swap`, and the loan clause is ticked with the refusals' positions;
   - S-23b's last two rows, and N-26's row, read "refused TYPE-085 from <pin>";
   - RX-162 is superseded in part;
   - `vec.npk`'s loan section and `bytes.npk`'s note are dated;
   - O-N21 reads DEF-102, landed;
   - `CLAUDE.md`'s "What stays open is a LOAN" and its unit counts are updated;
   - `0.1.0.md`'s N-15 paragraph and `tests/rejection/README.md` are updated.

**DEF-98 and the reader**
10. Probe 15 compiles and exits 4 at −O0 and through `opt -O2`. It moves out of `refused/` with `expect-exit: 4`, and its header is rewritten.
11. `lexical.py` closes a block string only at `"""` (with `\` still escaping), and its docstring is re-dated at the pin. Case 18 holds a block string whose body contains `""`, and requires the new reading. The old close, restored in a copy, fails case 18.
12. RX-157's block-string paragraph is superseded in part. `CLAUDE.md`, `tests/probe/README.md` and `0.1.0.md:30` are updated; the totals stay 24 / 7.

**BL-9**
13. BL-9 (a)'s count plant goes red naming the unit. The plant is `// note<CR>/*` above `func:main` in the red `bytes_oob_get_empty.npk`, plus `// see<CR>use "bytes_oob_get_empty.npk".*;` in `vec_unit.npk`.
14. The same plant also goes red in two further mutated copies: one with `lexical.py` broken on purpose, and one with the `main` exception removed. Each defence holds alone, and the pair fails only when both are removed.
15. BL-9 (b)'s escaped-path syscall plant goes red at B-2, naming `npk_sys6`. The escaped `core`→`engine` import fails `check_layering`.
16. The CR-hidden `Frame` plant fails `check_vec_elements_own_nothing` by name.
17. Self-check forms for a lone CR and for an escaped path exist, and each is seen to fail against a harness without the fix.
18. RX-157 is superseded in part, and B-4d, `stages.py:77-84`, `run.py:47-51`, `README.md:57-60` and `TESTING.md:284-286` are corrected.

**The rest of this pass**
19. N-24: the macro plant fails the check, or the limit is stated. The `fixed`-field and parenthesised-discriminant plants pass the check, or those limits are stated.
20. N-25 is raised, and its answer recorded. If `id::<Vec<int64>>` still compiles at the pin (3g does not touch `refuse_move_of_borrowed`), it is pinned as a unit, given a row in S-23b, and `vec.npk:183` is qualified. I lean to not holding the close for it, because `src/` has no exposure and the gate does not name it. That is the author's call.
21. N-27 has a case, or B-5b states the gap. N-29's lines are corrected.
22. N-21 (DEF-97): the fourth pass's M8 reproducer builds and runs at the pin, and `0.1.0.md` §5 is updated. N-22's eight sites say TYPE-083 is refused at the pin.

**The run**
23. A full run at the pin is GREEN. Each suite's count is reconciled with the moves above, from the runner's own lines, and the self-check shows the new cases live. CI is green at the pushed head, read from the job's log through the API.

**If the author decides not to wait for the re-pin:** items 4 to 9 are replaced by the loan staying pinned as it is now (N-26's shape added), and by the gate saying plainly that the loan is open against DEF-102 (W-27). BL-9 still blocks either way.

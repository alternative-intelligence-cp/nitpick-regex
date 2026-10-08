# Pre-close audit — `nitpick-regex` cycle 0.1

**Filed by the orchestrator under W-22**, 2026-10-02. The auditor (`s1-nregex-0.1-audit`, `npk:auditor`, `opus` named, dispatched 2026-10-02 09:59, about 51 minutes, 624 959 tokens) wrote nothing; this file is its final message, reproduced below the line — extracted from its transcript by script, not retyped — **inside a fence, with two mechanical changes and no other**: (1) the four absolute home-directory paths on its "Roots" lines are written relative to this workbench, because its leak scan refuses them; (2) the message is fenced, because it quotes `nitpick-regex`'s own decision and question ids, which at workbench scope collide with other repositories' (`meta/OPEN_QUESTIONS.md`, *"Library questions this board cites"*: quoted evidence belongs in a fence); its 2 inner fence lines already use `~~~`. **The verdict is ACCEPT once C1 is fixed, with 22 findings** (8 contradiction, 1 dormant, 4 stale, 9 cosmetic). **C1 is a silent wrong answer**: `regex_escape`'s text `:name:` inside a nested class is read as a POSIX class, with no error; the auditor recommends escaping `:`, which clears C2 (the outermost class, refused loudly) too. **The close (0.1.6) triages every finding** — W-22 requires each to be addressed or explicitly deferred with a reason, not selected from — and C4 (the Gate cannot pass as written) needs a decision there. **S3 is the orchestrator's** (`PLAYBOOK.md`'s code for a keyword file name), corrected the day this was filed.

---

```
# Audit: nitpick-regex, cycle 0.1 (the pattern parser), pre-close (W-22)

status: ACCEPT once C1 is fixed. There is one silent wrong answer, and it is in `regex_escape`. The parser itself holds everywhere I measured it.

- **Audited:** `nitpick-regex` at `fd76c65`, which equals `origin/main`; the tree is clean. Scope: subcycles 0.1.0 … 0.1.5, the cycle README and its Gate, the specifications, RX-171 … RX-213, `src/syntax/`, `harness/` and `tests/`.
- **Pin:** `5fbaf4a`. `npkc` and `npkrt.o` match `SHA256SUMS`. Every compiler claim was read with `git show` or `git grep` at `5fbaf4a`; the checkout itself is at `93bcb66`.
- **Roots:**
  - REPO = `nitpick-regex`
  - WB = `.`
  - COMPILER = `../nitpick`
  - TIME = `nitpick-time`
  - Paths below are REPO-relative unless prefixed.

**Summary: 22 findings.** 8 contradiction, 0 unverified claim, 1 dormant, 4 stale, 9 cosmetic.

- **C1 is the silent wrong answer, and it overturns part of known finding 1.** In a nested class, `regex_escape`'s text `:name:` is read as a POSIX class with no error. Escaping `:` fixes both C1 and C2 in one change.
- **The parser agrees with SYNTAX.md everywhere measured:**
  - an independent reference parser, written from the specification, against 1.4 million patterns: 0 differences, trees compared whole;
  - an offset and span inside the pattern on every refusal;
  - linear time on every adversarial shape;
  - no trap and no memory growth.
- **Recommendation:**
  - Fix C1 and C2 by escaping `:`.
  - Fix C3 and C5.
  - C4 needs a decision at 0.1.6, or the Gate cannot pass as written.

---

## Contradiction

### C1: `regex_escape(":alpha:")` inside a nested class is read as the POSIX class `[:alpha:]` — a silent wrong answer

**Location:**
- `meta/specs/SYNTAX.md:666-673`, Y-45: "between `[` and `]` one member each".
- `meta/DECISIONS.md:5359` (RX-211's title, "in a class") and `:5372`.
- `src/syntax/parse.npk:1555-1558`. `is_escaped` claims to cover "every byte that means something somewhere in a pattern, in a class or out". `:` means something right after a nested `[`.
- `src/syntax/parse.npk:1567-1573`; `meta/specs/COMPAT.md:34`.
- `tests/unit/regex_escape.npk:12`, and case 31 at `:242`, which pins `:` unescaped.
- `meta/roadmap/0.1/0.1.5_tools/env.sh:158`: the mutant `esc-extra`, which escapes `:` and is required to fail.
- The cause is Y-38 (`SYNTAX.md:574-579`): where a member would start inside a class, `[:` begins a POSIX class.

**Evidence.** My own runs, at −O0 and through `opt -O2` alike:

~~~
[a[ + regex_escape(":alpha:") + ]]   = [a[:alpha:]]    -> NIL; Class{ ClassRange 'a', PosixClass alpha }
[\w--[ + regex_escape(":digit:") + ]] = [\w--[:digit:]] -> NIL; \w minus [:digit:], not \w minus {: d i g t}
~~~

- **Exhaustive check:** every text of length 1–4 over 14 symbols, plus the 14 names — 41 384 texts, each placed in `[a[`…`]]`.
  - The 14 texts `:name:` are accepted and misread.
  - Every other text that begins with `:` (2 955 of them) is refused `UnknownPosixClass`.
  - Every remaining text round-trips.
- **Fuzz:** 2.4 million patterns over 20 contexts.
  - Misreads appear only in nested classes: `[a[…]]`, `[\w--[…]]`, `[[…]]`, `[a&&[…]]` and `(?x)[a[…]]`.
  - None appears in a whole pattern, under `(?x)`, in a piece, or in an outermost class.
- **Why the verifier missed it:** its 333 134 texts stood in four places, none of them a nested class. The test file uses the same four.
- **Impact:** a consumer writing "word characters except these" as `[\w--[` + `regex_escape(s)` + `]]` gets a different set, with no error, for 14 inputs. It gets a refusal for every other `s` that begins with `:`.

**Resolve — recommended: escape `:`.**
- `\:` is ASCII punctuation, so Y-2 reads it as itself in a class and out, and RX-200's sentence already recommends it.
- The change:
  - add `CH_COLON` to `is_escaped`;
  - make the change by a new decision superseding RX-211 in part, with Y-45's list amended;
  - case 31 then expects `x\:=1,'%@!`;
  - add a nested-class place to the round trip, holding every ASCII byte and the 14 names;
  - `esc-extra` becomes the fix rather than a mutant.
- **Why not narrow the claim:** that would leave a silent misread standing behind caveats.

### C2: known finding 1 — the outermost class, `[` + `regex_escape(":a:")` + `]`, is refused, loudly

**Evidence:**
- `[:a:]` is `UnknownPosixClass` at byte 0, span 5, detail 0. `[:alpha:]` gets detail 1.
- In the exhaustive set, the outermost refusals are exactly the RX-200 shape: the text starts and ends with `:`, holds another codepoint, and every codepoint is copied unescaped. That is 68 texts, and none is misread. I agree it is loud.

**Resolve:** C1's fix clears this too. Amending the text alone would leave C1 standing.

### C3: `\b{,3}` and `\b{ 3}` say the brace "holds no number"; it holds `3`

**Location:**
- `SYNTAX.md:353-356`, Y-32's note: "holds no digit".
- `DECISIONS.md:5434`, RX-213's title: "holds no number".
- Against them, `DECISIONS.md:5445-5448` (RX-213's body: "no digit follows it") and `SYNTAX.md:747` (§9's row: "with no digit after it").
- `src/syntax/parse.npk:750-756` and `src/syntax/pattern_error.npk:321`.

**Evidence:**
- `\b{,3}`, `\b{ 3}` and `\B{,2}` are each `BadRepeatBounds` at byte 2, span 1, detail 2. The sentence says "…and this one holds no number. Rust's `regex` reads `\b{start}`…".
- `a{,3}` gets detail 0.
- So the code implements the body and §9's row, while the note, the title and the sentence state another rule. This is the right byte with the wrong reason — the shape of the NUL-in-a-name case RX-203 fixed.

**Resolve — recommended:** give detail 2 only when an ASCII letter follows the `{`.
- That is one byte of lookahead, which the cursor allows.
- Every name Rust and Perl read inside those braces begins with a letter.
- Otherwise, reword the sentence and the note to "is not followed by a number".
- Either way: a new decision superseding RX-213 in part, and a `\b{,3}` case in `parse_refusals`.

### C4: the Gate cannot pass as written, and 0.1.6's checklist box names two of the four kinds nothing produces

**Location:**
- `meta/roadmap/0.1/README.md:164-169` (the Gate) and `:160` (the 0.1.6 box, which names `EmptyClass` and `ClassTooLarge`).
- `meta/roadmap/ROADMAP.md:223-230`; `SYNTAX.md:730-732` (Y-25).
- `meta/OPEN_QUESTIONS.md:925-934` (O-Y3, "as it must `ClassTooLarge`").
- Against them, `meta/roadmap/0.1/0.1.5.md:1011-1013`, which names all four.

**Evidence:**
- Of the 38 kinds, 34 have a producer in `src/` and a unit that provokes them.
- `EmptyClass`, `RepeatProductTooLarge`, `ClassTooLarge` and `ProgramTooLarge` have neither. Their only site in `src/` is `pattern_error_text`'s arm.
- Each has an owner:
  - `RepeatProductTooLarge`: the 0.2 README, line 39;
  - `EmptyClass` and `ClassTooLarge`: 0.3.4 (O-Y3; the 0.3 README, line 61);
  - `ProgramTooLarge`: the 0.6 README, line 43.

**Resolve:**
- At 0.1.6, a decision amends the Gate to: every kind is provoked by a test, or listed with the cycle that will provoke it.
- `check_error_kinds_tested` holds that list both ways: a listed kind that a test provokes fails, and an unlisted kind that no test provokes fails.
- Correct the 0.1.6 box and O-Y3 to name all four kinds.

### C5: the literal reader shared with nitpick-time reads less here

Two differences:
- RX-202 does not read a character literal as a number.
- The adoption re-read misses the two files that RX-202's reader mirrors.

**Location:**
- `harness/treecheck.py:311-430` and `DECISIONS.md:5049-5051` (RX-202).
- `meta/specs/BUILD.md:341-356` (B-4e's list: `lexer.npk`, `escapes.npk`, `parse_decl.npk`, `LEXICAL_REFERENCE.md`).
- In nitpick-time: TIME:`harness/checks.py:620-720` (TM-231 reads character literals by value), TIME:`meta/DECISIONS.md:7100` (its re-read includes `numeric.npk` and `num_width.npk`), and TIME:`harness/selfcheck.py:2350-2372` (part E3, which asks the pinned compiler).

**Evidence:**
- **The character literal:**
  - Planted in a scratch copy's `src/core/bytes.npk`: `pass n > ('\u{10000}' => int64);`.
  - It compiles at `5fbaf4a`, and `check_constants_named` reports ok.
  - The same bound written as `65536i64` fails the check.
  - `'\u{10000}' => int64` is 65 536 at the pin; a probe program exits 7 on that equality.
- **The re-read:**
  - At `5fbaf4a`, `lexer.npk` imports `numeric.npk` and `num_width.npk`, where `num_scan` and `num_width_of` decide a literal's value.
  - Both readers match those functions today.
  - nitpick-regex names neither file anywhere.
  - Self-check case 32 is Python against Python; nothing asks the pinned compiler. So a re-pin that moves `num_scan` fails time's run and passes this one.

**Resolve:**
- Read a character literal at a comparison by its code point, porting `_char_value`, with a plant for it.
- Add both files to B-4e's list.
- Give case 32 a half that asks the compiler, as time's E3 does.
- Or decline the character literal by a decision that says why.

### C6: known finding 2 — the in-class half of the `\K` change is attributed to the author

**Location:**
- `DECISIONS.md:5336-5346` (RX-210's paragraph "The author's amendment") and `:5356`.
- `SYNTAX.md:307-310` (Y-44's note).
- `tests/unit/parse_declined.npk:17-19`.

**Evidence:**
- The subcycle record says it plainly (`meta/roadmap/0.1/0.1.5.md:1202-1205`): "That half is this worker's reading … not the author's words."
- The author accepted it at 09:45 as question 23 (WB:`BOARD.md:9677`, WB:`RECORD.md:8770`).
- Behaviour, measured: `[\K]` is `UnknownEscape` at byte 1, span 2, detail 75. `\K` is `LookaroundUnsupported` at byte 0, span 2, detail 75.

**Resolve:** leave RX-210's text as it is. At all three places, add a dated note: "the in-class half is the worker's reading of RX-209, accepted by the author as question 23, 2026-10-02". Or record question 23's answer as a decision of its own beside RX-209.

### C7: `ast.npk` says a struct is `Copy` only when every member is; the pinned compiler and TM-214 disagree

**Location:** `src/syntax/ast.npk:79-80`. Against it:
- COMPILER:`meta/specs/DECISIONS.md` D-327's landed note: "the structural kinds pass";
- TIME:`meta/DECISIONS.md:6222-6226` (TM-214);
- this repository's own RX-190.

**Evidence, at `5fbaf4a`:**
- `#[derive(Copy)] struct:P = { int64:a; int64->:p; };` passes as `T: Copy`.
- `int64->` on its own is `NITPICK-TYPE-017`: "does not implement `Copy`".

**Resolve:** reword the comment to "every member `Copy` or a structural kind — a pointer or a slice (D-327); RX-190 is why the element check stays". No behaviour moves.

### C8: SAFETY.md S-2's lookaround row contradicts the cycle's own research — known, and deferred with no named owner

**Location:**
- `meta/specs/SAFETY.md:113`: "not regular either … the general case needs backtracking".
- Against it, `meta/research/lookaround-linear-time.md`, RX-212 (`DECISIONS.md:5399-5402`), and `0.1.5.md:1442-1448` ("the next subcycle that touches `SAFETY.md`").

**Evidence:** I checked both papers at their primary records:
- Mamouras and Chattopadhyay, PACMPL 8 POPL, Art. 92 — an O(m·n) algorithm;
- Barrière and Pit-Claudel, PACMPL 8 PLDI, Art. 201.

**Resolve:** the author deferred this note, but "the next subcycle that touches SAFETY.md" names no cycle. 0.1.6 should write the note, or name the cycle that will.

## Unverified claim

None outstanding. Every compiler claim checked is listed under "Checked and found clean"; C7 is the one found false.

## Dormant

### D1: no rule says what a POSIX class matches

**Location:**
- `SYNTAX.md:473-474`: Y-43 cites `UNICODE.md` U-9 for the ASCII meanings of "`\d`, `\w`, `\s`, the POSIX classes, `.`, `\b` and `\B`".
- `UNICODE.md:89-101`: U-9 pins `\d \w \s` only.
- `SYNTAX.md:485-494`: §5.1 says nothing about a POSIX class's meaning in either mode.
- `meta/roadmap/0.3/README.md:19, 42-46`: 0.3.2 points at §3's "pinned definitions", which hold none for POSIX classes.

**Resolve:** before 0.3.2, a rule in `UNICODE.md` §3 giving each of the fourteen names its set in Unicode mode and in byte mode.

## Stale

### S1: TESTING.md V-19 says cycle 0.4 builds `check_inst_kinds_total`

**Location:** `meta/specs/TESTING.md:251-252`. Its own table at `:214` (corrected by 0.1.0b's EC11) and the 0.6 README, lines 14 and 35, say 0.6.1.

**Resolve:** a dated note on V-19.

### S2: two decisions changed by later ones carry no marker

**Location:**
- `DECISIONS.md:4280-4281`: RX-174 says "`AstNode` implements `Pod` in one line". RX-177 retired `Pod` for a derived `Copy`. RX-168, beside it, does carry RX-177's marker.
- `DECISIONS.md:4527-4528`: RX-184 gives detail 0 for every non-bound `{`. RX-213 changed that to detail 2 after `\b` or `\B`. RX-183 carries RX-205's marker for the same kind of carve-out.

**Resolve:** add "SUPERSEDED IN PART by RX-177" to RX-174 and "by RX-213" to RX-184, as the repository already does elsewhere.

### S3: PLAYBOOK gives the wrong code for a keyword file name at the current pin (the orchestrator's to fix)

**Location:** WB:`PLAYBOOK.md:1369-1373` says such a file is `NITPICK-RESOLVE-012` "at the pin".

**Evidence:**
- At `5fbaf4a`, `mod:error;` and `mod:raw;` are each `NITPICK-PARSE-001` at 1:5.
- `NITPICK-RESOLVE-012` at 1:1 was `c970483`'s answer, as RX-176 records.

**Resolve:** date the measurement to `c970483` (RX-142's rule).

### S4: known finding 3a — RX-211's "as it does `pattern_error_text`"

**Location:** `DECISIONS.md:5376`. `src/lib.npk` re-exports `ERegexPattern` alone. `API.md:53-59` and RX-187 (`:4585`) both say 0.10.5, in the future tense.

**Resolve:** a dated note: "as it will `pattern_error_text`, both at 0.10.5".

## Cosmetic

- **K1 — known finding 3b, with a third place.** Each of these omits `g` and `K`:
  - §9's in-class row, `SYNTAX.md:777`;
  - `COMPAT.md:85`;
  - **also** the comment over `class_escape` at `src/syntax/parse.npk:1248-1252`.

  Measured: `[\g]` and `[\K]` are each `UnknownEscape` at byte 1, span 2. Add both letters at all three places.
- **K2:** §9's `UnclosedGroup` row (`SYNTAX.md:741`) gives the length as "1; 2 for `(?` at the end". A pattern that ends inside flags spans the whole head: `(?i` spans 3, measured, as Y-41 says.
- **K3:** `SYNTAX.md:81` and the README at line 147 say "`\u{41}` … at its `{`". The offset is the `\` (byte 0, span 3, detail 123); only the detail is the `{`.
- **K4:** Y-28 (`SYNTAX.md:253-257`) says every character but twelve is a literal. Its notes do not point at Y-42 (under `x`, white space is skipped or refused, and `#` starts a comment) or Y-43 (`(?-u)` refuses anything past ASCII).
- **K5:** `InvalidPatternEncoding`'s detail 0 means two things. `C3 00` gives span 2, detail 0 (a NUL broke the sequence). `C3` at the end gives span 1, detail 0 (the pattern ended). This is RX-203's shape. It is harmless, because the span tells them apart and no sentence reads the detail; say so.
- **K6:** `(?<` at the end is `BadGroupName` at byte 3 of a 3-byte pattern, span 0. It is the only refusal whose offset equals the pattern's length; I enumerated 137 560 patterns to confirm. 0.1.6's fuzz criterion, "a valid offset" (README line 161), should say whether that counts as valid.
- **K7:** at depth 250, `(?i)` and `(?#` get `NestTooDeep`, whose sentence says "would nest … 251 deep". Neither nests anything. Y-35 deliberately decides before reading the head, so only the sentence is off.
- **K8:** Y-45's "a piece of one" has two loud exceptions. After `\0`, a text that begins with a digit is refused: `\01` is `UnknownEscape` with detail 48. And an escaped text longer than 65 536 bytes is `PatternTooLong`, which is checked before the encoding.
- **K9:** RX-172's note at `SYNTAX.md:790-794` ("thirty-seven") sits after the later count notes, so it reads as the latest count.

## Checked and found clean

- **Mechanical checks:**
  - `check_refs` is clean: 87 md files, leak scan 345 of 345. Its own control passes 16 of 16.
  - `check_record 0.1.5` is clean. 0.1.0 … 0.1.4 report only `head-subject`, which is expected because HEAD is 0.1.5's record.
- **Harness:** one full run over a copy of HEAD under `$TMPDIR`:
  - GREEN, 258/258 in 143.2 s;
  - self-check 29 live of 33;
  - all nine tree checks.
- **CI on both heads**, read per job through the jobs API:
  - run 37010845658, job 110849923347, 83 013 B;
  - run 37012421339, job 110855098387, 82 239 B.

  Each shows `5fbaf4a` clean, the pin's emission `30232291 B / 5630c2b4…`, 258/258 and GREEN.
- **The parser against the specification:** I wrote an independent reference parser in Python from Y-2, Y-26 … Y-45 and §9. Compared on the four refusal fields, and on whole trees (flags, operands, positions and lengths included), at both legs:
  - 600 000 generated patterns, about 41 % of them accepted;
  - 800 000 random byte strings;
  - 256 patterns at the nesting bound's edges;
  - 125 of the specification's own worked examples.

  There were 0 differences, and every example behaves as its text says.
- **Offsets and sentences:**
  - Over 1 000 000 fuzzed patterns, every offset and span falls inside the pattern, on the byte the kind names.
  - 114 777 rendered sentences each name their own offset, and none says "support".
- **No trap, no growth:**
  - No trap on 800 000 random byte strings at either leg.
  - Under a 16 MiB address-space cap, 2 000 000 iterations of parse, refusal, sentence and `regex_escape` exit 0, as 1 000 iterations do; both fail at 8 MiB. Growth is under 4 bytes per iteration.
- **Linear time:**
  - 15 adversarial shapes at 16, 32 and 64 KiB give 64K/16K time ratios of 3.5–4.4, and 3.8–4.1 for the parse alone at both legs.
  - The worst case, 250 equal-length group names (the duplicate check), takes 55 ms at −O0.
  - The search's linear time cannot be measured until an engine exists; that is cycle 0.7.5's property test.
- **Compiler claims verified at `5fbaf4a`:**
  - D-305's stack check (`npkrt.ll:100-125`).
  - Probe 19's edges reproduced, twice each: −O0 runs 16 911 levels and traps at 16 912 (exit 106); `opt -O2` runs 52 425 and traps at 52 426.
  - TYPE-075's meaning (`recursion.npk:14-18`). With `decreases 0i64` written on all 138 functions under `src/`, every one is TYPE-075 and nothing else, so the compiler agrees with `check_no_recursion` at HEAD.
  - `src/` holds no `dyn`, trait, impl, function value or `sys(`.
  - `mod:error;` is PARSE-001 at 1:5.
  - `lexer.npk` changed +13/−2 between the two pins (DEF-145); the other files B-4e lists are unchanged.
  - D-236, as RX-195 cites it.
  - A program importing `syntax.npk` owes exactly `core`'s eleven `failsafe` arms.
  - `num_scan`'s base-suffix order and its 37 widths match both libraries' readers.
  - The only `cstring` anywhere is `main`'s `argv`.
- **Outside the compiler:** every CURRENCY.md row was checked between 2026-09-27 and 2026-10-01.
- **Cross-repository:**
  - `lexical.py` is AST-identical to nitpick-time's, docstrings aside.
  - Both libraries put `Vec<T: Copy>` on the type and on every generic verb: 13 verbs here, 9 there.
  - TM-214 and RX-190 agree.
- **Counts:**
  - 61 unit programs, 37 core and 24 syntax;
  - 33 probes, split 25 / 8;
  - 24 rejection fixtures;
  - 258 judged items = 1 + 25 + 8 + 139 + 24 + 61.
- **Left clean:**
  - `git status --porcelain` is empty in all four trees.
  - `.internal/r3/` was not touched.
  - The scratch under `$TMPDIR` is removed.
  - earlyoom logged no kill today.

Sources:
- [Mamouras and Chattopadhyay, "Efficient Matching of Regular Expressions with Lookaround Assertions" (ACM DL)](https://dl.acm.org/doi/10.1145/3632934)
- [POPL 2024 paper page](https://popl24.sigplan.org/details/POPL-2024-popl-research-papers/94/Efficient-Matching-of-Regular-Expressions-with-Lookaround-Assertions)
- [Barrière and Pit-Claudel, "Linear Matching of JavaScript Regular Expressions" (ACM DL)](https://dl.acm.org/doi/10.1145/3656431)
- [PLDI 2024 paper page](https://pldi24.sigplan.org/details/pldi-2024-papers/55/Linear-Matching-of-JavaScript-Regular-Expressions)
```

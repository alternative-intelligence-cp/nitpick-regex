# Open questions

Everything that is not settled, each with a recommendation, so that nothing
lives only in a conversation. Three prefixes:

| Prefix | Whose |
|---|---|
| `O-x` | **ours** — a design question this project decides, at the cycle named |
| `O-G` | the **compiler's**, raised from here — a **G**ap in the language or its tooling that `nregex` needs closed. Numbered locally; where the workbench registry has filed the same item, its id is named beside ours |
| `O-N` | the **workbench registry's** (`../meta/OPEN_QUESTIONS.md` §"For the compiler") — the ecosystem-wide id a compiler request is actually filed under. **Never allocated here**, only cited |
| `Q-` | the **user's** — a question wanting an answer before the work it gates begins |

A question that gets answered moves to `DECISIONS.md` as a numbered decision
and is struck through here with the decision's number, **never deleted** — the
question is part of the record of how the answer was reached.

**No cycle in this plan is blocked on a question.**

---

## Q — for the user

### ~~Q-1 — the Unicode version to pin~~ — **SETTLED, RX-100**
The latest stable UCD when cycle 0.3 runs, in `src/unicode/version.npk`. No
floor; a bump regenerates the tables and re-runs the agreement suite.

### ~~Q-2 — the dogfood consumer for cycle 0.14~~ — **SETTLED, RX-101 and RX-102**
`grep`, built in [`nitpick-posix`](https://github.com/alternative-intelligence-cp/nitpick-posix)
rather than in this repository's `examples/` — consumers are real programs and
live in the application workbench. **RX-102** records the conformance
consequence: POSIX basic REs have back-references, this library does not, and
`grep` refuses such a pattern by name rather than acquiring a backtracker.

### ~~Q-3 — whether `RegexSet` lands at 1.0 or 1.1~~ — **SETTLED, RX-103**
1.1 for the API; the compiled program format reserves a pattern id from 1.0, so
the deferral costs nothing. Defer the API, not the representation.

### ~~Q-6 — what replaces `VERIFICATION.md` P-1, now that every construct it names is live?~~ — **SETTLED, RX-164** — the board's question for all six work repositories, cited here under its number there

**Answered by the author on 2026-09-25 at 15:56 — *"the recommendation on q-6 seems
fine to me"* — and recorded at cycle 0.0.4d: A′, as `VERIFICATION.md` rule P-1b.**
The question as it stood is kept below, because it is how the answer was reached.

**Raised 2026-09-25, at the re-pin to compiler `c3bdae2`**, by `nitpick-time`'s
planner, and queued on the workbench board for the author as **Q-6**. The number
is the board's and `nitpick-time`'s, and it is used here unchanged so that one
question has one id in every repository that owes the same answer — the `O-N`
convention above, applied to a question. Numbers Q-4 and Q-5 are therefore not
used in this file.

P-1 writes an obligation as a comment *"in the exact syntax it will take"*, and
rested its safety on the rung refusing each construct by name; P-1a (RX-127)
narrowed that to `prove`, `requires` and `ensures` at `3d15ac9`. **At `c3bdae2`
none of them refuses.** Measured here by the `probe13` family, as cycle 0.0.4b
re-points it ([`roadmap/0.0/0.0.4b.md`](roadmap/0.0/0.0.4b.md) §5 step 6):

| Construct, live | In a plain build | What a consumer owes |
|---|---|---|
| `prove` | lowers to nothing: a FALSE `prove` over a run-time value runs to exit 0 (`probe13a`) | nothing |
| `requires` | checked at the callee's entry, traps `RequiresViolated`, and `?\|` cannot catch it (`probe13g`) | one arm (`probe13c`) |
| `ensures` | checked at every return, traps `EnsuresViolated` (`probe13h`) | one arm (`probe13d`) |
| `limit<R>` | checked after every write, traps `LimitViolated` (`probe13e`) | one arm (`probe13f`) |

**And one cost that is this repository's alone, measured at planning:** a live
`requires` on an accessor pre-empts RX-130's stop. With `vec_get`'s comment-form
clause made live, the read of an empty `Vec` traps **`RequiresViolated`, not
`OutOfBounds`** — so every out-of-range unit's expected exit would move with it,
and RX-130's decision (*the trap is the language's own `OutOfBounds`*) would need
a successor.

**The options:**

- **A′ — comments by default, and a live clause is a budget decision
  (RECOMMENDED).** `decreases`/`unbounded` are the language's and always live;
  `assert_static` wherever it helps, at no cost. `requires`, `ensures`,
  `invariant` and `limit` are written live **only where a numbered decision says
  the check earns the arm it adds to every consumer**, recorded in `SAFETY.md`
  §4.2 — and never a `requires` on an accessor whose body already stops
  (RX-130). `prove` stays a comment until the harness runs the verified build
  (cycle 0.8), because a plain build lowers it to nothing. **A comment-form
  obligation is documentation, and is never cited as a check.**
- **A — live now.** Every consumer of `core` owes `RequiresViolated` and
  `EnsuresViolated`; the accessor pairs' traps change identity (above), and
  RX-130 needs a successor. Gains: every contract checked on every call of every
  test.
- **B — every obligation a comment until cycle 0.8**, `assert_static` included.
  The simplest, and the weakest: nothing checks a comment's syntax or its truth.
- **C — everything live now, `prove` included.** A live `prove` in a plain build
  is exactly the silent no-op P-1 was written against.

**Recommendation: A′.** It keeps P-1's mechanism — property tests stand in, and
the switch is a decision rather than a sweep — and gives the true reason for it:
the arm and the run-time cost, not a refusal that no longer happens. For this
repository it is also the only option that leaves S-8's one-arm promise and
RX-130's trap identity standing without a new decision. **Nothing waits on the
answer:** cycle 0.0.4b is identical under all four, and 0.0.4c's field limits
are the board's decided design (item 13), not a P-1 choice; `0.0.4b.md` §10
spells out what A would add, as its own subcycle after the close.

---

## The `O-N` collision, and how it was resolved — RX-114

**It used to be true that `O-N` meant two things in this file**, and for one
session `O-N9` meant both a local question and a workbench one. It no longer
does. The four ids this repository allocated locally at planning are now
**`O-G1` … `O-G4`**, one-for-one and in order, and **`O-N` in this repository
means the workbench registry's id and nothing else.** `RX-114` records the
renumbering, why the recommended `O-C` prefix could not be used, and what was
deliberately *not* rewritten.

| was | is now | what it is |
|---|---|---|
| local `O-N1` | **`O-G1`** | `comptime` cannot index a string. Not yet filed in the registry |
| local `O-N2` | **`O-G2`** | `MACRO_REFERENCE.md` §8 says `const`. Not yet filed in the registry |
| local `O-N3` | **`O-G3`** | `npkg` cannot build a library. **Filed as the registry's `O-N2`** |
| local `O-N4` | **`O-G4`** | `simd` reductions lower to extract chains. *Not* the registry's `O-N4`, which is a different finding entirely |

**Two traps this table exists to spring.**

1. **The registry's `O-N4` is `npkc` being quadratic in one declaration** —
   `nitpick-time`'s finding — and has nothing to do with SIMD. Our SIMD
   question is `O-G4`. A citation of "O-N4" written in this repository before
   2026-09-03 means ours; after it, the registry's.
2. **The registry's entry for `O-N2` still names our local id as
   `nitpick-regex O-N3`.** That line is in the workbench, which this repository
   does not write. It is raised in 0.0.1's report for the author to correct.

**`meta/roadmap/0.0/0.0.0.md` was deliberately NOT renumbered.** It is a closed
subcycle's execution record, independently verified at `9b80d69`, and a verified
artifact is not edited afterwards — the workbench's own `RECORD.md` keeps a
misnumbered `O-N7` for exactly this reason. Its `O-N1` and `O-N4` mean the
**local** ids of the day it was written, and the two redirect entries below make
those citations resolve.

### ~~O-N1~~ — **RENUMBERED to `O-G1`** (this repository's legacy local id), RX-114
Cited under the old number only in `meta/roadmap/0.0/0.0.0.md`, which is frozen.
**The workbench registry's `O-N1` is a different thing** — `clone_exec` has no
signal-mask slot, raised by `nitpick-tui` — and this library has no interest in
it.

### ~~O-N4~~ — **RENUMBERED to `O-G4`** (this repository's legacy local id), RX-114
Cited under the old number only in `meta/roadmap/0.0/0.0.0.md`, which is frozen.
**The workbench registry's `O-N4` is a different thing** — `npkc` is quadratic
in the size of one declaration, raised by `nitpick-time`, the compiler's DEF-1.
`nregex` generates no large single declaration before cycle 0.3's Unicode
tables, so the registry's `O-N4` is a thing to watch there and not here yet.

---

## O-N — the workbench registry's, cited here and never allocated here

These are filed in `../meta/OPEN_QUESTIONS.md` §"For the compiler", which is the
ecosystem-wide list. They are restated here, with what each means for this
library, so that a citation from this tree resolves without leaving it.

### ~~O-N2~~ — **RENUMBERED to `O-G2`** (this repository's legacy local id), RX-114
The `MACRO_REFERENCE.md` §8 `const` documentation defect. **The workbench
registry's `O-N2` is a different thing** — `npkg` cannot build a library — which
is *our* `O-G3`. The two are unrelated and the numbers crossed.

### ~~O-N3~~ — **RENUMBERED to `O-G3`** (this repository's legacy local id), RX-114
`npkg` cannot build a library. This one **is** in the registry, under the
registry's `O-N2`, where this repository is listed among the six that raised it.
The registry still names our local id by its old number; correcting that is the
author's, and it is in 0.0.1's report.

### ~~O-N9 — **the workbench registry's**: a `uint8[]` view escapes its owning frame, silently~~ — **DISCHARGED upstream: refused `NITPICK-BORROW-001` since `94874ce`** (the compiler's DEF-3 / D-249, 1.5.1b step 2)
*Struck 2026-09-25 by the fifth cycle 0.0 audit's triage, citing the workbench registry (`../meta/OPEN_QUESTIONS.md` §"For the compiler"), which carries the strike with its evidence — re-measured by the workbench's registry audit (`wb-registry-sweep-1821`), each with a control at an older kept pin, and spot-checked by the orchestrator. Its evidence: `nitpick-time`'s `view_escape/` cases 3–5 are refused at `c3bdae2` (case 5 read the `0xAA` poison, 170, at `950bb1d`), case 6 — the legal view parameter — still runs 0, and seven further escape routes are refused. The text below is kept as raised. **What it means here now:** the house rule *"a view is a parameter, never a return value"* is still this library's (RX-050's offsets need no view at all), and the sites that call the escape "the one the compiler does not diagnose" are stale in the same way — listed, not rewritten, in `roadmap/0.0/0.0.5.md` §12.*
**Not ours, not open to us, and already accepted.** D-004's escape rule is
enforced for `@`-borrows and **not** for slice views: `string_bytes(local)`
returns a view that outlives its owner and reading it afterwards reads freed
memory — `170`, the runtime's `0xAA` free-poison (D-183) — at exit 0. Confirmed,
independently verified, accepted as the compiler's **DEF-3**, and scheduled as
the second commit of its cycle 1.5.1b. The six-case contrast set is
`../nitpick-time/tests/probe/defect/view_escape/`.

*What it means here:* RX-050's offsets-not-slices stands, and
`tests/probe/probe06b_subview_returned.npk` records the acceptance **without
building on it**. That probe also contributes this library's one addition to the
report — the *safe* slice return, a subrange of a **parameter**. DEF-3's checker
already distinguishes it, so that note is confirmation rather than a new ask.

**State the house rule at the right strength.** `nitpick-time`'s version — *"a
view is a parameter, never a return value"* — was deliberately conservative,
because when it was written nothing could tell the safe cases from the dangerous
ones. DEF-3 draws the line where it belongs. **Name which rule you are quoting:**
the live check at `950bb1d` is `borrows_only_param_rooted`
(`../../nitpick/src/frontend/analysis/escape.npk:507`) — *rooted at a
**parameter** of the current function* — and the pointer-shaped formulation
below is DEF-3's future rule.

- **a view of a FRAME-LOCAL OWNER must not escape.** That is the bug, and it is
  what O-N9 is.
- **a view whose root is a POINTER-SHAPED binding is the pointee's borrow and
  may travel.** A wild pointer, a slice and a `cstring` are pointer-shaped, so
  `string_from_bytes(buf, n)` over an alloc'd block, returned, **stays legal**.
  So does `probe06b`'s subrange of a `uint8[]` parameter.
- **a view of a TEMPORARY is refused outright**, `NITPICK-BORROW-012` — the
  **one** code DEF-3 adds, because `@` of a temporary cannot be spelled so no
  existing code's text is true of it. **It is not in the pinned toolchain**
  (DEF-3 step 2, unlanded; `BORROW-011` is the highest at `950bb1d`), so
  grepping `3d15ac9` for it finds nothing and that is expected:
  `string_bytes(string_concat(a, b))` returned must bind the intermediate first.
  That composes with D-246 — the `string_concat` is an owning temporary that
  leaks today — so the shape is doubly wrong and both faults have one fix.

This library needs none of the permitted shapes today, because `API.md` reports
matches as **offsets** (RX-050), which is correct under either regime. But a
later cycle must not adopt the conservative sentence as though it were the whole
truth.

### ~~O-N10 — **the workbench registry's**: `#[derive(Eq)]` on a payload enum is refused; `#[derive(Ord)]` on one silently compares tags~~ — **DISCHARGED at the re-pin, RX-125**
**Both halves fixed in the compiler's 1.5.1b, and verified HERE on this
repository's own measurement at pin `94874ce`, 2026-09-04** — the rule this
ecosystem applies to a blocking defect: it is discharged on our own measurement,
not on a landing note.

*What it was.* `Eq` failed inside the derive expansion with `NITPICK-TYPE-034`
pointing at a synthetic `<derived-1>` module the author cannot open; `Ord`
compiled and its `cmp` ignored the payload entirely, so
`Repeat(2,5).cmp(Repeat(9,9))` answered `Equal`. Confirmed here at cycle 0.0.0
and extended: the arity made no difference.

*What it is now.* Both derives compile and both read **every** payload field.
`Repeat(2,5)` is distinguished from `Repeat(2,9)` and from `Repeat(9,5)`, and
`Repeat(2,5) < Repeat(2,9)` — the second field breaks the tie, which is the
property no test in `nitpick-time` can make, because its enum has one payload
field per variant. Thirteen properties are asserted in
`tests/probe/probe02b_derive_eq.npk` and `tests/probe/probe02c_derive_ord.npk`
(renamed from `…_refused` and `…_tag_only`, which had become false claims).

*How it surfaced, which is the part to keep.* `probe02c` was written to assert
the DEFECT, with a header reserving exit 20 for the day it was fixed. It exited
20 in this subcycle's first full harness run. A probe asserting the correct
answer would have been green throughout and would have reported nothing on
either day.

*The residue.* `.eq()` returns `Result<bool>` and `.cmp()` returns
`Result<Ordering>` — `if (a.eq(b))` is `NITPICK-TYPE-007` — so replacing
`probe02_payload_enum.npk`'s hand-written `hir_eq` with a derive threads an
error channel and charges `SAFETY.md` §4's budget. That is a **cycle 0.2**
decision with the cost on the table, not an automatic consequence of this
discharge.

### ~~O-N11 — **the workbench registry's**: `npkc` exit 0 does not mean a program is well-formed~~ — **DISCHARGED upstream: a root with `main` and no `failsafe` is refused `NITPICK-REACH-003` since `94874ce`** (the compiler's DEF-5, 1.5.1b step 1b)
*Struck 2026-09-25 by the fifth cycle 0.0 audit's triage, citing the workbench registry (`../meta/OPEN_QUESTIONS.md` §"For the compiler"), which carries the strike with its evidence — re-measured by the workbench's registry audit (`wb-registry-sweep-1821`), each with a control at an older kept pin, and spot-checked by the orchestrator. Its evidence: `nitpick-time`'s `missing_failsafe/` cases 1 and 3 are refused at `c3bdae2` and case 2 runs 0. **The general sentence outlives the defect**: a module's object still links neither alone nor beside a program (`BUILD.md` B-0, RX-151), so "exit 0 is not well-formedness" stays true here for that reason, and the four-step recipe stands. The text below is kept as raised.*
**Not ours.** A root file with `main` and no `failsafe` compiles at exit 0 and is
refused only by `llc`, a long way from the cause. Accepted as the compiler's
**DEF-5**.

*What it means here:* every probe in `tests/probe/` is run through **all four**
steps of `0.0.0.md` §2's recipe — `npkc`, `llc`, `ld.lld`, and the binary — and
a probe that was only compiled is a probe that has not been run. The transcript
in `tests/probe/TRANSCRIPT.txt` carries every step's exit code for exactly this
reason.

### ~~O-N12 — **PROVISIONAL, awaiting the author's number**: the compiler's references document two constructs that do not exist~~ — **DISCHARGED upstream: the documents were corrected, as recommended**, at the compiler's 1.5.1b step 2 (present in `94874ce`); the number is the registry's own
*Struck 2026-09-25 by the fifth cycle 0.0 audit's triage, citing the workbench registry (`../meta/OPEN_QUESTIONS.md` §"For the compiler"), which carries the strike with its evidence — re-measured by the workbench's registry audit (`wb-registry-sweep-1821`), each with a control at an older kept pin, and spot-checked by the orchestrator. Its evidence: the `>>>` row is gone and `>>` is described by the operand's signedness (`TYPE_REFERENCE.md`), the "fast compiler intrinsics" sentence reads UNCLAIMED (`BUILTIN_REFERENCE.md`), and at `c3bdae2` `>>>` does not lex (`PARSE-002`) and `string_repeat` does not resolve (`RESOLVE-002`), as documented. The text below is kept as raised.*
**Raised by cycle 0.0.0, 2026-09-03. The number is a proposal** — `O-N` ids
belong to the workbench registry (`../meta/OPEN_QUESTIONS.md`) and O-N1…O-N11
are taken, so this is the next free one pending confirmation.

Two documented constructs are absent from the compiler at `950bb1d`:

| Documented | Where | What `npkc` says |
|---|---|---|
| `>>>`, "right shift (unsigned), `lshr`" | `TYPE_REFERENCE.md` operator table (line ~1799) | `NITPICK-PARSE-002 … expected an expression` |
| `string_repeat(str, n)` | `BUILTIN_REFERENCE.md` string section (line ~167) | `NITPICK-RESOLVE-002 … cannot find `string_repeat` in this scope` |

Evidence: `tests/probe/TRANSCRIPT.txt` §C2 isolates `>>>` against the five
bitwise operators that do compile; `probe05_explicit_stack.npk`'s `nest_of`
carries the `string_repeat` replacement and says why.

**W-27 — what this blocks, what it inconveniences, and what it does not touch.**

- **Blocks: nothing.** Neither construct is on any path this library needs.
- **Inconveniences: mildly, once each.** `>>>` costs nothing at all, because
  `>>` on an unsigned type is already logical — measured at bit 63, the only
  place it could differ: `(1u64 << 63u64) >> 63u64` is **1**, not all-ones. So
  `>>>` would be a pure synonym. `string_repeat` costs a four-line concat loop.
- **Does not touch:** correctness, performance, or any specification rule. The
  cost is entirely in reading a reference, believing it, and finding out.

*Recommendation:* the cheapest fix is documentation — mark both rows "not
implemented" — rather than implementing either. `>>>` in particular should
probably say *"`>>` is `lshr` on unsigned operands; `>>>` is reserved and
unimplemented"*, because a reader who sees `>>` described as `ashr` and `>>>` as
`lshr` will reach for the one that does not exist, which is exactly what
happened here.

### ~~O-N13 — **PROVISIONAL, awaiting the author's number**: a `pub use` is silently downgraded to a plain `use` when the same path was plain-`use`d first~~ — **DISCHARGED upstream: a `pub use` after a plain `use` re-exports since `94874ce`** (the compiler's DEF-7, 1.5.1b step 3c); the number is the registry's own
*Struck 2026-09-25 by the fifth cycle 0.0 audit's triage, citing the workbench registry (`../meta/OPEN_QUESTIONS.md` §"For the compiler"), which carries the strike with its evidence — re-measured by the workbench's registry audit (`wb-registry-sweep-1821`), each with a control at an older kept pin, and spot-checked by the orchestrator. Its evidence: `symbols.npk` gives the earlier binding `SYM_PUB`, tested upstream in `tests/accept/reexport/`; the §E2 shape, rebuilt from the real umbrella, is refused `RESOLVE-002` at `950bb1d` and runs 0 at `94874ce` and `c3bdae2`, and the plain-`use` control stays refused. `TRANSCRIPT.txt` §E2/§E3 recorded files that were never committed, so cite `tests/accept/reexport/` as the evidence from here on. `check_layering`'s B-15a half (RX-113) stays: the umbrella is still all `pub use` by this library's rule. The text below is kept as raised.*
**Raised by cycle 0.0.1, 2026-09-03, against pinned toolchain `950bb1d`.
The number is a proposal** — `O-N` ids belong to the workbench registry and
O-N1…O-N12 are taken, so this is the next free one pending confirmation.

`symtab_bind_import` (`src/frontend/symbols.npk`) declines any name already
bound in the scope and, where the prior binding is **the same declaration
reached twice**, returns it as a success — *"a re-export chain reaching the same
declaration by two routes is not a conflict"*. The `flags` argument, which
carries `SYM_PUB` for a `pub use`, is applied **only on the creation path**. So:

```nitpick
mod:lib;
use     "./api/api.npk".*;              // binds Match, ERegexPattern … without SYM_PUB
pub use "./api/api.npk".ERegexPattern;  // declined as "already bound"; SYM_PUB never set
```

re-exports nothing, and **`npkc` reports nothing at any severity** — the file
compiles at exit 0. The failure surfaces in the *consumer*, as
`NITPICK-RESOLVE-002 cannot find ERegexPattern in this scope`. The same two lines
in the opposite order are correct, also silently: two files that differ in
behaviour and not in output. Evidence:
[`../tests/conformance/TRANSCRIPT.txt`](../tests/conformance/TRANSCRIPT.txt)
§E2 and §E3.

There *is* a diagnostic for the neighbouring case — two **different** paths
exporting one name warns `NITPICK-RESOLVE-008`, *"exported by an earlier import
and also by …; the earlier import is bound"* — so the machinery to say something
exists and the same-declaration path deliberately bypasses it.

**W-27 — what this blocks, what it inconveniences, what it does not touch.**

- **Blocks: nothing.** The umbrella pattern works when written correctly, and
  `src/lib.npk` is written correctly (RX-113): every line is a `pub use` and no
  path is plain-`use`d as well.
- **Inconveniences: once, expensively, per person who meets it.** It cost this
  subcycle its first experiment, and the cost is not in the fix but in the
  distance between the symptom and the cause. Any library with an umbrella
  module — which is every library in this ecosystem — is one redundant `use`
  line away from it, and a reviewer cannot see it.
- **Does not touch:** correctness of anything that compiles, performance, or
  any rule in any specification here.

*Recommendation:* merge the flags on the idempotent path — `p.flags = p.flags |
flags` before `pass prior` — which is the whole fix and preserves the "not a
conflict" intent. Failing that, a warning when a `pub use` is declined because
the name was already bound non-publicly; **silence is the expensive part.**

### ~~O-N14 — **PROVISIONAL, awaiting the author's number**: no library module can be assembled, because `npkc` never emits a `declare` for `@npk_failsafe`~~ — **DISCHARGED since `94874ce`, RX-151**
*Struck 2026-09-25 at cycle 0.0.4b, at compiler `c3bdae2`. The recommendation
below was implemented upstream: since `94874ce` `npkc` declares `@npk_failsafe`
in every module that calls it, and every `src/` file now assembles (`llc` exit
0; `950bb1d` the only kept pin that refuses). Its expectation that "the original
pipeline works unchanged" did not follow: a module's object links neither alone
nor beside a program (`ld.lld: duplicate symbol`), so `BUILD.md` B-0 stands, for
that reason instead. The text below is kept as raised.*

**Raised by cycle 0.0.1, 2026-09-03, against pinned toolchain `950bb1d`.
The number is a proposal**, following O-N13. **Close kin to the registry's
`O-N11` (the compiler's DEF-5) and probably the same fix.**

`npkc` emits seven call sites to `@npk_failsafe` into every translation unit —
the prelude's trap paths — and **no `declare` for it in any module**. LLVM
requires a `declare` for a function called and not defined, so the emitted text
is ill-formed unless something in that module defines the symbol. A program's
own `failsafe` does; a library file cannot, and under D-248 may not, because
`main` and `failsafe` are permitted only in a program's root file.

The result is that **all eight files in this library's `src/` compile at `npkc`
exit 0 and all eight are refused by `llc`**, with
`error: use of undefined value '@npk_failsafe'`. `npkc`'s usage line offers no
library or module mode. Evidence:
[`../tests/conformance/TRANSCRIPT.txt`](../tests/conformance/TRANSCRIPT.txt)
§A and §A2, which counts the call sites, the declares and the defines in a
library module and in a program side by side.

**W-27 — what this blocks, what it inconveniences, what it does not touch.**

- **Blocks:** a per-module object; a `libnregex.o`; and separate compilation as
  `BUILD_REFERENCE.md` §4.1 describes it — *"each module compiles to its own
  object; `ld.lld` links them"* — for any module that is not a program root.
  It is why `BUILD.md` §2's pipeline is amended by RX-115.
- **Inconveniences:** cycle 0.0.2's harness, which builds through a program root
  rather than over `src/`; and RX-008's no-syscall scan, which has no
  library-only object to scan and becomes differential instead (RX-116).
- **Does not touch:** this library's shape, layering, API or any specification
  rule. Nothing was reshaped to dodge it, and the day the `declare` is emitted,
  the original pipeline works unchanged.

*Recommendation:* emit `declare i32 @npk_failsafe(i32)` in any module that calls
it and does not define it. That is one line of emission and it closes this
outright. **It also improves `O-N11`:** DEF-5's root-with-no-`failsafe` case
would then reach `ld.lld` and fail as *"undefined symbol: npk_failsafe"*, which
names the missing thing, instead of failing in `llc`'s parser. The frontend
check DEF-5 asks for is still the right diagnostic; this makes the fallback
honest.

### ~~O-N15 — **PROVISIONAL, awaiting the author's number**: `npkg`'s expectation reader accepts an `expect-exit:` a run can never satisfy~~ — **DISCHARGED upstream: `npkg`'s `expect_read` refuses an `expect-exit:` outside 0..255 and −1..−64 by name since `94874ce`** (compiler `39e69cc`, 1.5.1b step 5); the number is the registry's own
*Struck 2026-09-25 by the fifth cycle 0.0 audit's triage, citing the workbench registry (`../meta/OPEN_QUESTIONS.md` §"For the compiler"), which carries the strike with its evidence — re-measured by the workbench's registry audit (`wb-registry-sweep-1821`), each with a control at an older kept pin, and spot-checked by the orchestrator. Its evidence: `npkg/expect.npk` at `c3bdae2` (a source reading at the commit, not a build of `npkg`), whose self-check carries an `expect-exit: 321` that must fail; no bound existed at `950bb1d`. This harness's own refusal (RX-122) stays, and now agrees with `npkg`'s. The text below is kept as raised.*
**Raised by cycle 0.0.2, 2026-09-04, against pinned toolchain `950bb1d`. The
number is a proposal**, following O-N14. **The smallest thing on this list, and
it is here because it is the same family as the ones that were not.**

`npkg/expect.npk`'s `expect_read` takes `expect-exit:` through `text_int`, which
accepts any integer up to eighteen digits, and stores it. `run_binary` then
compares it against a process's exit status, **which is one byte**. So
`// expect-exit: 321` is accepted in silence and can never be satisfied: the
program that computes 321 and exits with it reports **65**, and the test fails
forever with the message *"exited 65, expected 321"* — which is true, unhelpful,
and does not say that 321 was never reachable.

*Recommendation:* refuse a value outside `-64 … 255` at read time, in
`expect_read`, alongside the existing "a number the reader cannot read marks the
expectations unreadable" rule — which is exactly the right treatment and simply
does not cover a number that reads fine and means nothing. Negative values
already have a meaning worth keeping (`run_binary` reports a killed process as
`0 - signal`).

**W-27 — what this blocks, what it inconveniences, what it does not touch.**

- **Blocks:** nothing, anywhere.
- **Inconveniences:** nobody today. Swept across this ecosystem 2026-09-04: no
  `expect-exit` header and no recorded exit claim exceeds 255. It costs the
  first person who writes one, and it costs them a debugging session rather than
  a red run.
- **Does not touch:** any library's shape, any specification rule, or any
  schedule. `harness/expect.py` already refuses it here (RX-122), so nothing in
  this repository is waiting on it.

*Why raise it at all.* This ecosystem uses exit codes to carry probe results —
`0xAA`/170 for a poison read, 94 for a bounds trap, 221 and 107 in the derive
probes — so the channel is one byte wide and is used as though it were wider.
The compiler session hit the wrap itself writing a DEF-4 regression whose wanted
value was a sum of comparison results. A measurement channel narrower than the
thing measured, failing silently, is the shape worth naming even when today's
instance is empty.

### ~~O-N16 — **PROVISIONAL, awaiting the author's number**: DEF-8's landing note says the workbench does not write the shape the workbench writes~~ — **DISCHARGED upstream: DEF-8's closing note was corrected the day it was catalogued** (compiler `8dbef43`, 2026-09-04; in every pin from `0dfddac`); the number is the registry's own
*Struck 2026-09-25 by the fifth cycle 0.0 audit's triage, citing the workbench registry (`../meta/OPEN_QUESTIONS.md` §"For the compiler"), which carries the strike with its evidence — re-measured by the workbench's registry audit (`wb-registry-sweep-1821`), each with a control at an older kept pin, and spot-checked by the orchestrator. Its evidence: the note now says the workbench does write the shape and is untouched because its containers fall outside `decl_is_list`. The entry's own text said so, and it was never struck here. The text below is kept as raised.*

*Catalogued, not raised* (the compiler session is near its usage limit and its
fix batch is closing). **This is a defect in a NOTE, not in the compiler**, and
it is registered because the note is a reason a later reader would rely on.

The compiler's `meta/roadmap/OPEN_DECISIONS.md` at pin `94874ce` records DEF-8 —
*"`pass` of a COPYABLE field cleared the root's drop flag"*, latent since 1.2.3,
fixed at 1.5.1b step 5 — and closes the entry:

> Blocks nothing of the workbench's: their recipes **pass values, not fields**,
> out of owning locals.

**That premise is false about this repository.**
`tests/probe/probe04_inherent_generic_impl.npk` contains
`func:len2 = int64(Vec<T>:self) never fails { pass self.count; }` — a `pass` of a
**field**, out of a by-value local — and `probe08_sparse_set.npk`'s `sset_has`
takes a `SparseSet` by value and reads through two nested `Vec`s. The recipes the
sentence says the workbench does not write are written here, twice.

**Nothing was harmed, and the reason is not the one the note gives.** These
programs are unaffected because this library's `Vec<T>` **does not own** —
D-247's ownership is keyed on a module named `list` holding a struct named `List`
with fields `items`/`count`/`cap` (`decl_is_list`, read at `3d15ac9`), and this
repository has neither. So DEF-8's precondition — an *owning* local — is never
met here. **RX-126** records the measurement; all three owed probes re-ran at
exit 0.

*Why it is worth a number rather than a shrug.* The note is the compiler's own
record of who a defect could have reached, and a future defect in the same family
will be triaged against it. "Their recipes do not do this" is a claim about the
workbench's code that will be re-used; "their container does not own, so the
precondition is unmet" is the true reason and is stable under this library
growing more `pass field` sites — which cycle 0.0.4 will add, since every `Vec`
accessor is one.

*Recommendation:* replace the note's reason with the true one. No code change is
implied and nothing here is blocked.

---

### ~~O-N17 — **PROVISIONAL, awaiting the author's number**: the borrow tracker taints a function's return by SIGNATURE, so a function that takes a container by borrow cannot return an owned `string`~~ — **RE-HOMED: it is the workbench registry's O-N27, the same finding, registered 2026-09-26** (the entry below)

*(2026-09-26, cycle 0.0.4e: struck in favour of O-N27, as the registry directs. The
number collided and the finding was never filed under it; the orchestrator
registered it as O-N27 after `nitpick-time` measured it independently, and sent it
to the compiler as a design input to its S-106 (DEF-107's decision), where it is
recorded as S-107. **Re-measured here at `c3bdae2` and at `c970483`**: the
registry's reproduction — a `func:make = string(Box->:b)` returning
`string_concat("small", "!")`, called `pass raw make(@b);` from the frame owning
`b` — is `NITPICK-BORROW-001` at both. The heading and the text below are kept as
raised, so the four citations in `roadmap/0.0/0.0.5.md` §8 still resolve.)*

*⚠ 2026-09-25, found by the fifth cycle 0.0 audit's triage: **THIS NUMBER COLLIDES, and the finding has no registry number at all.** The workbench registry's `O-N17` is `nitpick-time`'s *"a generic function that moves OUT of an indexed element at an owning `T` calls a `@npk.vacant.<n>` helper the emitter never defines"* — assigned there by the orchestrator on 2026-09-05 and discharged since `aaffb87` — and nothing in the registry records this entry's finding. It is the same collision the registry's own note describes for a worker's `O-N12`, from the other side: this id was proposed here and never confirmed. A worker does not assign an `O-N` id (`../PLAYBOOK.md`), so it is raised by path for the orchestrator to number or to close, and it is kept under this heading so that the four citations in `roadmap/0.0/0.0.5.md` §8, a closed record, still resolve. Whether it still holds at `c3bdae2` is unmeasured here.*

**Raised by cycle 0.0.5's audit triage, 2026-09-06, measured at `3d15ac9`.**
This is the exact inverse of **O-N9** and the two belong together: O-N9 is a
view escaping with **no diagnostic**, and this is an owned value being **refused
a diagnosis it does not deserve**. Both are the same tracker working on types
where it needs values.

`src/core/bytes.npk`'s `bytes_copy_string(Bytes->:b) -> string` makes a genuine
owned copy — `string_concat("", view)`, which allocates and `memcpy`s, verified
in the runtime's own IR. Returning its result from a frame that OWNS the `Bytes`
is refused:

```
NITPICK-BORROW-001: a borrow cannot travel up: it is valid only for the frame
it was taken in, and this returns it out of that frame (D-004 rule 2)
```

**It is the signature and not the body**, established with a control rather than
assumed:

| shape | result |
|---|---|
| `pass string_concat("", string_from_bytes(b.buf.ptr, b.len));` written INLINE in the owning frame | **accepted, exit 0** |
| `pass raw bytes_copy_string(@b);` from the owning frame | **refused** `NITPICK-BORROW-001` |
| a control taking `Bytes->` and returning `string_concat("small", "!")`, which **cannot alias its argument at all** | **refused identically** |
| the same call where the `Bytes` is a **parameter** of the returning frame | accepted |

The third row is the finding: a function that receives a borrow has any
view-capable return treated as a borrow of it, whatever the body does.

**It is SOUND and it is COARSE.** It refuses safe programs and accepts no unsafe
ones, so nothing here is unsafe today and nothing is worked around — the working
shapes (build and consume in one frame; take the container as a parameter and
return one level up) are `API.md` A-12's shape anyway, and both are measured
accepted. **What it costs is a whole class of constructor**: any
`f(Container->) -> string` that builds its result rather than borrowing it. This
library meets that class at cycle 0.6, where replacement returns built text.

*Recommendation:* raise it with O-N9 rather than separately, because the fix is
one idea — track the **provenance of the value** rather than the shape of the
signature — and it closes an unsound hole and an over-strict refusal at once. If
only one can be had, **O-N9 first**: a false accept is a use-after-free and a
false reject is an inconvenience.

### ~~O-N21 — **the workbench registry's**: a callee writing through a LENT parameter frees or grows its caller's value~~ — **DISCHARGED upstream: refused `NITPICK-TYPE-085` since the compiler's 1.6.0 step 3g (DEF-102), in our pin since `c970483`; RX-169**

*(2026-09-26, cycle 0.0.4e: measured at `c970483`, every face refused exactly
`NITPICK-TYPE-085` at its write — the four units, the `for` binding and probe 17,
each now a refusal (`tests/rejection/`, `tests/probe/refused/`) and each still
running at `c3bdae2` with its old exit, so the refusal is the pin's. The text below
is kept as raised.)*

**Filed in the workbench registry (`../meta/OPEN_QUESTIONS.md` §"For the
compiler") on 2026-09-25 and sent to the compiler seat at 19:55; confirmed as the
compiler's DEF-102 — refused `NITPICK-TYPE-085` from its 1.6.0 step 3g, which no pin
of ours carries (`c3bdae2` does not).** *(This said "no DEF number has come back"
until the fifth cycle 0.0 audit's N-29; the number had reached the board the same
evening.)* Found by this repository's planning of `Vec` move-only by
construction, at compiler `c3bdae2`, and reproduced by the orchestrator before
it was sent. The registry's entry is the authority; this one restates it so that
a citation from this tree resolves without leaving it.

An ordinary parameter is LENT — the compiler's D-183, restating D-065's rule:
*"passing transfers nothing, so an ordinary parameter is a value the callee may
read and may not keep"* — and `move` of one is `NITPICK-TYPE-047`. The compiler
does not hold the callee to the loan. **Overwriting an owning FIELD of a lent
parameter drops the CALLER's value** — D-186's unconditional field drop, whose
comment in the assignment lowering reasons that *"the struct's owner is exactly
who is overwriting it"* — and **`@` of a lent parameter lets the callee free or
grow the caller's container**. The committed reproduction, with no library code
and no `wild`, is
[`probe17_lent_field_drop.npk`](../tests/probe/refused/probe17_lent_field_drop.npk): the
caller reads its own string's body as the `0xAA` free poison, exit 70, at −O0
and through `opt -O2`.

*What it means here:* `SAFETY.md` S-23b's last two rows, and RX-162. RX-161
refuses a COPY of a `Vec`; a loan is not a copy, and no type in this library can
refuse it. Four units pin what a loan still reaches — `vec_alias_param_free`,
`vec_alias_param_grow`, `sparseset_alias_param_free` and `bytes_alias_param_grow`,
each PINNED, NOT ENDORSED, each saying what its reddening means — and nothing is
worked around. *(A fifth unit since the fifth cycle 0.0 audit's N-26: a `for`
binding over an array of containers is the same loan, `vec_alias_for_binding_free`
— RX-167. By 3g's source it should be refused `TYPE-085` too; the re-pin measures
it.)* **What it blocks (W-27):** nothing in `src/`, where every function
that changes a container takes it by pointer; any consumer that writes through a
container it was lent, the parser at cycle 0.1 first; and whether cycle 0.0's
close waits for the fix is the author's, the board's question 10.

### ~~O-N22 — **the workbench registry's**: `NITPICK-TYPE-047` is not asked of a lent `T` inside a generic body, so a generic function hands back its lent parameter as a second owner~~ — **DISCHARGED upstream: refused `NITPICK-TYPE-047` since the compiler's 1.6.0 step 3g (DEF-104), in our pin since `c970483`; RX-169 — and its reach here was wider than this entry said: RX-168**

*(2026-09-26, cycle 0.0.4e: measured at `c970483`, `vec_alias_generic_passout` is
refused `NITPICK-TYPE-047` at its `pass` and runs at `c3bdae2`. "Nothing in `src/`,
where no generic takes a lent bare `T`" below was true of a PARAMETER and not the
whole of it: the fixed gate also refuses a `T` PLACE passed out of a lent or
pointed-to container, which was `vec_get` and `vec_pop` — the tree did not compile
at `c970483` until `vec_get` took `T: Pod` and `vec_pop` spelled `move(...)`
(RX-168). The workbench registry's entry states the same "none" and is corrected
there, not here.)*

**Raised by this repository's fifth cycle 0.0 audit (N-25), 2026-09-25, at compiler
`c3bdae2`; reproduced by the orchestrator, filed in the workbench registry
(`../meta/OPEN_QUESTIONS.md` §"For the compiler") and sent to the compiler seat,
which confirmed it as its DEF-104, riding with its 1.6.0 step 3g.** The registry's
entry is the authority; this one restates it so a citation from this tree
resolves without leaving it.

`func:id<T> = T(T:x) never fails { pass x; };` compiles, and at an owning `T` the
result is a second owner of the argument: at `string`, both are dropped — **95**, a
double free — and a read of the result after the argument's drop is **70**, the free
poison; the same body written for `string` alone is refused `NITPICK-TYPE-047`,
*"this parameter was lent, not given"*. The mechanism, read at `c3bdae2`: the check
gates on `type_drops`, false for an unsubstituted `T`, and a generic body is
checked once — D-264 fixed the same gate for `TYPE-046` (DEF-23); this is its
`TYPE-047` sibling. **At a pin carrying 3g** both gates ask `type_owns_for_move`:
the pass-out refuses `TYPE-047` at the `pass`, as its `string` twin does, and `@x`
of a lent `T` refuses `TYPE-085`. `c3bdae2` carries neither.

*What it means here:* at `T = Vec<int64>` a generic identity is a second handle on
the block — after `vec_free(@a)` the read through the result is the free poison —
so a move-only `Vec` (RX-161) is not a one-handle `Vec`. Pinned, not endorsed, by
`../tests/unit/vec_alias_generic_passout.npk`, whose header says what its reddening
means, and given `SAFETY.md` S-23b's last row (RX-167). **What it blocks (W-27):**
nothing in `src/`, where no generic takes a lent bare `T` — `vec_push`, `vec_set`,
`vec_insert` and `drop_element` take `move T`; and it is not a clause of cycle
0.0's gate.


### O-N28 — **the workbench registry's**: an impl may declare `move` on a parameter its trait lends, and a call through the trait then hands the callee a value the caller still owns

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

Gaps this repository found and numbered itself. Where the workbench registry has
since filed the same item, its id is named in the entry — `O-G3` is the
registry's `O-N2`.

### O-G1 — `comptime` cannot index a string, so a compile-time-validated pattern is not expressible
**The most valuable thing on this list.** The obvious safety win for this
library is `#regex("…")` — a form that parses the pattern *while compiling the
program*, so a malformed pattern literal is a **compile error** and
`regex_compile` never fails at run time. No regex library in any language
offers that.

Nitpick has a real `comptime` interpreter with loops, mutable locals,
`comptime func:` calls and strings (`MACRO_REFERENCE.md` §8), so it looks
available. It is not. Measured at the compiler's 1.5.0, reading
`src/frontend/resolve_type.npk` — **renamed since to
`src/frontend/type_resolve.npk`; both claims below re-verified there at pin
`3d15ac9`, see the raisable form at the end of this entry**:

- `fold_expr` dispatches on integer, bool, char and string literals; `comptime`
  expressions; unary, binary, cast and unchecked-cast expressions; builtins;
  identifiers; calls; the iteration variable; and `raw` unwraps. **There is no
  arm for an index expression, a member access, an array literal or a struct
  literal.**
- `fold_string_builtin` handles exactly four names — `string_concat`,
  `string_equals`, `string_byte_length`, `string_is_empty`.

So a `comptime func:` can concatenate, compare and measure a pattern string and
**cannot look at a byte of it**. A pattern walker is not expressible.

**MEASURED BY PROBE 09, AND THE ASK IS SHARPER THAN THE READING ABOVE.** The
prediction from the source was "no arm for an INDEX expression". The wall is one
step earlier. Nine `comptime func:` bodies, each adding one construct, every one
compiled and its exit code recorded (`tests/probe/TRANSCRIPT.txt` §C1):

| construct | folds? |
|---|---|
| plain constant | **yes** |
| mutable local + arithmetic | **yes** |
| counted `while` loop | **yes** |
| `string_byte_length` | **yes** |
| `string_is_empty` | **yes** |
| `string_equals` | **yes** |
| `string_concat` | **yes** |
| `string_bytes`, then `.len` | **no** — `NITPICK-TYPE-004` |
| `string_bytes`, then an index | **no** — `NITPICK-TYPE-004` |

**`string_bytes` is the wall, and `.len` alone is already past it.** The index
never gets a chance, because the view is never produced — `string_bytes` is not
one of `fold_string_builtin`'s four names, and the four that fold are exactly
those four.

The diagnostic, verbatim from compiler commit `950bb1d`:

> `NITPICK-TYPE-004 …:77:16: `comptime` requires an expression that folds at
> compile time, and this one does not`

Clean about the fact, **silent about the cause** — it does not say which
sub-expression refused. Worth mentioning in the request, because the cost of
diagnosing this without the isolation table above is an afternoon.

**Ask, restated:** fold `string_bytes` (or add a comptime byte accessor), **and**
an index arm on the slice it yields. That is **two** arms rather than one. The
argument for it is what already works: loops, mutable locals and every string
operation a validator would need to *report* with are all available at compile
time today — `probe10_comptime_capabilities.npk` exercises all of them. What is
missing is exclusively the ability to look at a byte.

**And a fraction of it is buildable now.** `NREGEX_PATTERN_BYTES` (65536) and an
empty-pattern check are enforceable at compile time with `string_byte_length`
and `string_is_empty` alone — `probe10`'s `pattern_len_ok`. That is not
`#regex(…)`, and it is not nothing.

#### O-G1, re-verified at `3d15ac9` and written in raisable form — cycle 0.0.5

**Everything above was measured at `950bb1d`, and this section exists because
that is not good enough to raise on.** Two of this repository's probe verdicts
have already reversed under a re-pin (RX-125's derives, RX-127's `limit<Rules>`),
so a request built on a nine-month-old — here, three-day-old — source reading is
a request that can bounce. Re-measured 2026-09-06 at the working pin:

| Claim | At `3d15ac9` | How checked |
|---|---|---|
| the probe still refuses | **yes**, `NITPICK-TYPE-004`, exit 1, no `.ll` written | `npkc tests/probe/refused/probe09_comptime_walker.npk -o …` |
| the diagnostic's text | **byte-identical**, span included | stderr compared to the quotation above |
| `fold_string_builtin`'s names | **exactly four**, unchanged | the four `string_eq(name, …)` arms in its body |
| `fold_expr`'s dispatch | **fourteen `ExprKind` arms**, none for an index, a member access, an array literal or a struct literal | every `ExprKind.*` in the function body |
| **the file's NAME** | **CHANGED** — it is `src/frontend/type_resolve.npk` | `git -C ../../nitpick grep -l 'func:fold_expr' 3d15ac9` |

**The last row is the whole argument for re-verifying.** Everything above cites
`src/frontend/resolve_type.npk`, and **there is no such file at `3d15ac9`.** A
request naming a path the maintainer cannot open is a request that costs a round
trip before it is even read. Cite `fold_expr` and `fold_string_builtin` **by
name**, per `PLAYBOOK.md` §6 — a symbol survives a rename and a line number does
not survive anything.

---

**THE REQUEST, self-contained. Everything below is quotable into the compiler
repository as it stands; it names no file of ours and assumes nothing a reader
there does not have.**

> **Request: fold `string_bytes`, and add an index arm to `fold_expr`.**
>
> **What is wanted.** A `comptime func:` that can read a byte of a string
> literal. Today it can concatenate, compare and measure one, and cannot look
> inside it.
>
> **Measured at `3d15ac9`.** Nine `comptime func:` bodies, each adding one
> construct, each compiled and its exit code recorded. Seven fold: a plain
> constant, a mutable local with arithmetic, a counted `while`, and all four of
> `string_byte_length`, `string_is_empty`, `string_equals`, `string_concat`. Two
> do not: `string_bytes` followed by `.len`, and `string_bytes` followed by an
> index. **The wall is `string_bytes` and `.len` alone is already past it** —
> the view is never produced, so the index never gets a chance.
>
> **Where, by name rather than by line.** In `src/frontend/type_resolve.npk`:
> `fold_string_builtin` dispatches on exactly four names — `string_concat`,
> `string_equals`, `string_byte_length`, `string_is_empty` — and
> `string_bytes` is not one of them. `fold_expr` dispatches on fourteen
> `ExprKind`s and has **no arm for an index expression**, a member access, an
> array literal or a struct literal.
>
> **The diagnostic, verbatim:**
>
> ```
> NITPICK-TYPE-004 …:77:16: `comptime` requires an expression that folds at
> compile time, and this one does not
> ```
>
> **A second, smaller ask, and it may be the better-value one.** That message is
> exact about the fact and **silent about the cause** — it does not say which
> sub-expression refused to fold. Diagnosing this without building the
> nine-body isolation table above costs an afternoon; with one named
> sub-expression it costs a minute. The isolation table is the evidence that the
> silence is expensive, and it was built precisely because the message would not
> say.
>
> **Why a consumer wants it.** A regex library can then offer `#regex("…")`: a
> malformed pattern literal becomes a **compile error at the line that wrote
> it**, with no run-time error path and no `Result` for the caller to ignore.
> **No regex library in any language offers that**, and under REACH-002 it is
> worth more here than elsewhere — it removes an entire error identity from
> every consuming program's `failsafe`.
>
> **What already works is the argument for the size of the ask.** Loops, mutable
> locals and every string operation a validator needs to *report* with are
> foldable today. The missing capability is exclusively *reading a byte*, and the
> two arms above are the whole of it.
>
> **Not blocking anything.** The library ships without it; `regex_compile`
> returns `Result<Regex>` and always will, because a pattern can arrive at run
> time. This is a request, not a defect, and not a date.

### O-G2 — `MACRO_REFERENCE.md` §8 says `const`, which no longer exists
**A documentation defect, found in the same reading.** §8's "What a name means
inside one" says *"A `const` global folds; nothing else that is a name does
(D-130)"*, and `const` was retired from the language at 1.4.2c by D-222 —
`fixed` is the one immutability keyword in every position. The **implementation
is correct**: `fold_ident` checks `QUAL_FIXED()`. The prose beside it, and the
specification, are stale.
**Ask:** amend §8 to say `fixed`, and the comment above `fold_ident`.

### O-G3 — `npkg` cannot build a library, and `[dependencies]` resolves to nothing
As `nitpick-tui` records. `npkg build` is the compiler's own bootstrap ladder;
`target = "library"` is accepted by the schema and read by nothing; the
loader's dependency-root list is created empty and never populated.
**Consequence:** `nregex` builds through its own Python harness (RX-004) and
every import is relative until this closes.
**Ask:** `npkg build` honouring `target = "library"`, and the driver populating
the resolver's roots from `[dependencies]`. Neither is on the compiler's 1.5 or
1.6 map, so this is a request, not a date.

### O-G4 — `simd` reductions lower to extract chains, so SIMD scanning may not pay
Not a defect — a measurement to report. `simd<T, N>` exists (D-194) and a byte
scan is its textbook use, but `.any()` on a `simd<bool, N>` is specified as an
**ordered extract-and-fold chain**, not a movemask plus count-trailing-zeros,
and shuffles are out by decision. So a SIMD `memchr` is correct here and its
speed is unknown.
**Ask:** none yet. Cycle 0.13 measures scalar against SIMD and records the
number; if SIMD loses, *that measurement* is a consumer's evidence for a
movemask intrinsic, which is a better request than a speculative one.

---

## O-x — ours

### Safety and engines

- **O-R1 — a bounded backtracker with lookaround, behind an opt-in.** Declined
  at 1.0 as RX-009, with three reasons. **Open by design**, with the shape
  written down: a separate `RegexBacktrack` type, a separate compile entry
  point, a step budget in the options, an explicit error when it is exhausted,
  and a documentation page stating that the linear-time guarantee does not
  apply. Declining a feature is cheaper to revisit than removing one.
- **O-R2 — a reverse DFA to find a match's start.** It is how Rust's `regex`
  avoids the Pike VM for simple captures. It doubles the compiler's output and
  needs its own correctness argument. **Decide at cycle 0.8**, where the DFA's
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

### The pattern language

- **O-Y1 — leftmost-longest (POSIX) mode.** Cheap in a Pike VM — a different
  rule for which thread wins a slot — and wanted by nobody yet.
  **Recommendation:** deferred; revisit if a consumer asks.
- **O-Y2 — whether `x` mode ignores whitespace inside classes.** Rust does not;
  Perl does with `xx`. **Recommendation:** do not, matching Rust, and refuse
  `xx` with a message naming the escape. **Decide at cycle 0.1.**

### Unicode

- **O-U1 — full case folding.** Refused at 1.0 as RX-022, because it turns a
  class from a set of codepoints into a set of strings and changes the matching
  model. **Recommendation:** stay simple; revisit only with a concrete
  consumer, and as its own cycle.
- **O-U2 — the Unicode version to pin.** See Q-1. **Open by design:** it is
  data, chosen at cycle 0.3.
- **O-X1 — the overlap with `nitpick-tui`.** Both libraries generate range
  tables from the same UCD and both need `Vec` and `Bytes`. Today
  `[dependencies]` resolves to nothing (O-G3), so each carries its own.
  **Open by design:** when resolution lands, whether a shared `nunicode`
  package is worth extracting is a real question with a real cost — a third
  repository, a third release cadence — and pre-deciding it now would be
  deciding against tooling that does not exist.

### Compilation

- **O-C1 — sharing instruction suffixes across alternations.** A real size win
  on patterns with many similar branches, a real complication in emission. It
  is an optimisation subject to RX-041's off-switch rule, so it can be added
  later with the cross-check proving it changed nothing.
  **Recommendation:** not at 1.0.
- **O-C2 — reverse programs.** The compiler half of O-R2. **Decide at cycle
  0.8.**
- **O-H1 — a reverse literal suffix for reverse searching.** Only useful once a
  reverse engine exists. **Deferred to cycle 0.8** with O-R2.

### The API

- **O-A1 — whether `Matches` implements the prelude `Iterator` trait or only
  exposes `matches_next`.** *Probe 12 has reported, and the question changed
  shape.* The trait **can** be implemented on a struct holding a `Regex->`
  borrow and a `uint8[]` view — `tests/probe/probe12_iterator_borrowing.npk`
  compiles and runs. But **`for … in` over it is refused**,
  `NITPICK-BORROW-009`, *"a borrow cannot be iterated over: a `for` binding is
  not tracked by the escape analysis"*
  (`tests/probe/probe12b_for_over_borrow_refused.npk`).

  So the original argument — *"the trait gives `for … in`, which is
  ergonomic"* — **is void**. A `Matches` must borrow its `Regex`: a struct
  holding a borrow cannot be returned (D-004), and an owning `Matches` would
  consume the pattern it iterates with. The only `Matches` this library can have
  is exactly the one `for` will not drive.
  What the trait still buys is generic code written against `Iterator`, and
  nothing else; the explicit `next` is not a fallback but the sole driver.
  **Recommendation, revised:** implement `matches_next` for certain, and treat
  the trait impl as optional — worth it only if a consumer materialises that is
  generic over iterators. **Still decided at cycle 0.10**, now with the evidence
  rather than the assumption.
- **O-A2 — a `RegexSet` API.** See Q-3.
- **O-S1 — whether `RegexOptions` should be a `comptime` parameter rather than
  a value.** A `comptime` bound would let the program-size limit be a
  type-level fact and the arrays fixed. Against: it makes `Regex` generic over
  its options, infecting every signature that takes one.
  **Recommendation:** a plain value. **Decide at cycle 0.10.**

### Verification and performance

- **O-P1 — does the step counter ship, or is it a debug switch?** Shipping it
  makes `VERIFICATION.md` P-10's obligation about the real code and makes the
  guarantee measurable in production; not shipping saves one increment per
  inner iteration. **Recommendation: ship it**, and measure the cost at cycle
  0.13 before confirming. If it measures worse than 3%, revisit.
- **O-F1 — a SIMD `memchr`.** **Open by design:** it is a *measurement*, taken
  at cycle 0.13 against the scalar version. See O-G4.

### Build

- **O-B1 — when to migrate off the harness.** Gated on O-G3. **No action until
  then**; the harness and `npkg` run side by side with a parity check before
  the harness retires, exactly as in the compiler repository.
- **O-B2 — ship as source or as an object.** **Settled for now in favour of
  source**: it keeps the closed-world undefined-symbol scan seeing every symbol
  the program contains, and keeps whole-program verification available.
  Revisit only if build times become a real complaint from someone building a
  real program.

- **O-B3 — what a consumer's `failsafe` will actually owe once `api` reaches
  `core`, and whether S-8 survives it as written.** *Raised at cycle 0.0.4,
  2026-09-06.*

  `SAFETY.md` S-8 (RX-060) promises the strongest thing in this repository:
  *importing `nregex` costs your program's `failsafe` exactly one arm.* Cycle
  0.0.4 met **two** separate ways for that promise to be broken by something
  that is not an `error:` declaration at all, and both were measured rather than
  argued:

  - a **`limit<Rules>`** anywhere in the reachable graph arms `LimitViolated`,
    at `pub` and at module-private visibility alike (RX-127). Closed by
    declining the construct — **S-24**.
    *Dated 2026-09-25, cycle 0.0.4c: the construct is now declared ONCE, on
    purpose, and the bill says what it costs — the prelude's `ListLen` on the
    containers' four counts (`SAFETY.md` S-24a, RX-153), so `LimitViolated` is
    owed by every consumer of `vec.npk`, `bytes.npk` or `sparseset.npk` (9 →
    10) and of `core.npk` (10 → 11), measured with this entry's instrument.
    S-24 stands for every other binding.*
  - a **`/` or `%`** anywhere in a module arms `DivByZero` and `DivOverflow` in
    every importer, whether or not it calls the function containing it
    (RX-132). Closed by removing both from `src/` — **S-25**, with a tree check.

  Both are closed, and the pattern is not: **the budget is charged by anything
  that can reach `failsafe`, and this library has now found three kinds of
  charge where its own specification counts one.** Nothing today enumerates the
  bill. The instrument exists and it is the compiler itself —
  `NITPICK-REACH-003` on a program that imports a module and has no `failsafe`
  **lists every identity a consumer of that module will owe**, which is the
  mechanically checkable form of *"and no more"*, the half no build can catch
  because a superset of the required arms compiles and runs perfectly.

  **Recommendation:** at the cycle that first makes `api` reach `core`, run that
  diagnostic against `tests/conformance/import.npk` and diff the identities it
  names against `SAFETY.md` §4's table, as a harness check beside
  `check_error_budget` — which today counts `error:` declarations and would have
  reported green through both of the above. **The count is PER PROGRAM**, so the
  check reads each fixture's own bill and never generalises one. If the bill is
  larger than one plus the arms a program owes for its own arithmetic, S-8 is
  amended by a numbered decision rather than by hope; if it is not, S-8 has been
  verified for the first time instead of asserted.

  It is filed rather than done here because this subcycle builds `core` and
  `api` does not reach it yet: the diagnostic would report today's bill, which is
  one, and prove nothing about the one that is coming.

  *Dated 2026-09-25, cycle 0.0.4b: the instrument was run per public module at
  both pins and the bills are in `roadmap/0.0/0.0.4b.md` step 11 and
  `specs/SAFETY.md` §4.2 — `3d15ac9` → `c3bdae2`: `vec`, `bytes`, `sparseset`
  6 → 9; `byteset` and `core` 6 → 10; `limits`, `lib`, `api`, `syntax` 4 → 6,
  the language's floor. Two more kinds of charge met here (`DecreasesViolated`
  from a measured loop, `ShiftRange` from a computed shift) make five, and the
  question stands as written: `api` still does not reach `core`, so a consumer
  of `lib.npk` owes the floor and nothing of this library's.*

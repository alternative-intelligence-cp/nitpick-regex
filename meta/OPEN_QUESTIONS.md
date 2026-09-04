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

### O-N9 — **the workbench registry's**: a `uint8[]` view escapes its owning frame, silently
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
  grepping the pin for it finds nothing and that is expected:
  `string_bytes(string_concat(a, b))` returned must bind the intermediate first.
  That composes with D-246 — the `string_concat` is an owning temporary that
  leaks today — so the shape is doubly wrong and both faults have one fix.

This library needs none of the permitted shapes today, because `API.md` reports
matches as **offsets** (RX-050), which is correct under either regime. But a
later cycle must not adopt the conservative sentence as though it were the whole
truth.

### O-N10 — **the workbench registry's**: `#[derive(Eq)]` on a payload enum is refused; `#[derive(Ord)]` on one silently compares tags
**Not ours.** `Eq` fails inside the derive expansion with `NITPICK-TYPE-034`
pointing at a synthetic `<derived-1>` module the author cannot open; `Ord`
compiles and its `cmp` ignores the payload entirely.

*Confirmed against this library's own enum, and extended:* the arity makes no
difference. `tests/probe/probe02b_derive_eq_refused.npk` and
`probe02c_derive_ord_tag_only.npk` show a **two-field** payload compared no more
carefully than a one-field one, so `Repeat(2,5).cmp(Repeat(9,9))` is `Equal`.
Until it lands, no `Eq` or `Ord` derive goes on a payload enum here and the
comparison is written by hand (`probe02_payload_enum.npk`'s `hir_eq`). 02c is
green while the compiler is wrong and turns **red** the day it is fixed, which
is the signal that says the hand-written nesting can go.

### O-N11 — **the workbench registry's**: `npkc` exit 0 does not mean a program is well-formed
**Not ours.** A root file with `main` and no `failsafe` compiles at exit 0 and is
refused only by `llc`, a long way from the cause. Accepted as the compiler's
**DEF-5**.

*What it means here:* every probe in `tests/probe/` is run through **all four**
steps of `0.0.0.md` §2's recipe — `npkc`, `llc`, `ld.lld`, and the binary — and
a probe that was only compiled is a probe that has not been run. The transcript
in `tests/probe/TRANSCRIPT.txt` carries every step's exit code for exactly this
reason.

### O-N12 — **PROVISIONAL, awaiting the author's number**: the compiler's references document two constructs that do not exist
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

### O-N13 — **PROVISIONAL, awaiting the author's number**: a `pub use` is silently downgraded to a plain `use` when the same path was plain-`use`d first
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

### O-N14 — **PROVISIONAL, awaiting the author's number**: no library module can be assembled, because `npkc` never emits a `declare` for `@npk_failsafe`
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

### O-N15 — **PROVISIONAL, awaiting the author's number**: `npkg`'s expectation reader accepts an `expect-exit:` a run can never satisfy
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

---

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
`src/frontend/resolve_type.npk`:

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

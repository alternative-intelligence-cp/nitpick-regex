# Design decisions

Every settled design decision for `nregex`, with the reasoning, the
alternatives that were considered, and the date. **This is the file to read
when something in the specifications looks unusual**, because it is recorded
why.

Referenced as `RX-nnn` from the specifications. `D-nnn` in those documents
refers to the **compiler's** `meta/specs/DECISIONS.md`; those are language
decisions and are not ours to amend.

**Rule: a settled decision's text is never rewritten.** A decision that turns
out to be wrong is superseded by a new one that says so and says why; the old
text stays, dated, because it records what was true when it was made. This is
the compiler's D-085/D-202 pattern.

**Numbering is allocation order, grouped by area.** RX-001…RX-080 are the
founding batch, written with the specification set. Later batches are appended
whole with their own heading, because a batch ratified together is a unit.

---

## Foundations

### RX-001 — the library is `nregex`; the repository is `nitpick-regex`
**2026-09-03.** The module prefix, every public symbol's prefix and the
eventual package name are `nregex`, from `.internal/idea.txt` and matching the
ecosystem's `n`-prefix convention (`nfs`, `nproc`, `nio`, `ntui`, `nvec`). The
repository keeps the longer name because a repository name is a search term.

*Alternatives:* `nrx` (shorter, and unreadable in an import line); `regex` (no
prefix, collides with a user's own module and breaks the convention every other
library follows).

### RX-002 — the specifications are the authority
**2026-09-03.** Code that disagrees with `meta/specs/` is a defect in the code.
A specification that is wrong is amended by a decision recorded here, never by
editing the text and moving on. The compiler's own cycle notes record the same
finding repeatedly — the compiler and the thing that describes it have to be
diffed, because reading either alone never reveals the gap — and
`TESTING.md` §8's checks are that diff, applied here.

### RX-003 — automata only: linear time guaranteed, no backreferences, no lookaround
**2026-09-03. The decision the whole library is arranged around.**

The engine is a finite automaton — Thompson construction, a Pike VM, a lazy
DFA — and a search runs in `O(m · n)` where `m` is the program size and `n` is
the haystack length. There is no input and no pattern for which it is worse.

*Reasoning.* Catastrophic backtracking is a denial of service triggered by data
an attacker controls, against a pattern that looks entirely reasonable:
`(a+)+$` against thirty `a`s and a `!` runs longer than the age of the universe
on every backtracking engine in production. It is invisible to review, and in
Nitpick it is **not fixable by a timeout** — D-062 leaves no way to name a task,
so there is no cancellation, by design. In a language whose whole proposition
is that a stop is controlled and chosen by the programmer, a library that lets a
remote string hang the process does not belong in it.

*The price, which is real and is not softened:* backreferences, lookahead,
lookbehind, atomic groups, possessive quantifiers and recursion are **refused
at compile time, by name, with the byte offset**. None of them describes a
regular language; each is exactly what makes backtracking unavoidable.

*Alternatives:* a backtracking engine with a step budget — see RX-009, where it
is declined with three reasons; a hybrid that backtracks only for patterns
using the excluded constructs — the same objections, plus two engines that must
agree on the overlap.

### RX-004 — `harness/` builds and tests `nregex` until `npkg` can
**2026-09-03.** Measured at the compiler's 1.5.0: `npkg build` is the
compiler's own bootstrap ladder with no generic-project path, and
`[dependencies]` is parsed while the loader's dependency-root list
(`RootList`, `src/frontend/resolve_path.npk`) is created empty in
`src/driver/pipeline.npk` and `rootlist_add` is called from nowhere, so
cross-repository imports resolve against nothing. A Python harness drives
`npkc`, `llc` and `ld.lld` directly, mirroring `bootstrap/harness/`'s
relationship to `npkg`, and retires the same way — both running side by side
with a parity check before the older is removed.

*Not a dependency violation:* zero-dependency governs the artifact, not the
workbench (the compiler's `ORCHESTRATION.md` §6 says so in as many words).

### RX-005 — a second public error identity is a MAJOR version
**2026-09-03.** REACH-002 makes every public `error:` a mandatory `pick` arm in
every consuming program's `failsafe`, and forgetting one is a compile error.
Adding an identity is therefore a compiler-enforced source break in every
consumer. It is stated in the release policy and enforced by a harness check
that diffs the declarations against `SAFETY.md` §4.

### RX-006 — `nregex` declares its own storage primitives
**2026-09-03.** `Vec<T>`, `Bytes`, `ByteSet` and `SparseSet` live in
`src/core/` and are ours. The compiler's `List<T>` is not imported: it is a
compiler internal whose own header says it exists for the compiler's tables,
and reaching into another project's `src/` couples this library's correctness
to a file that is not a published interface. `Vec<T>` is `List<T>`'s shape,
deliberately, because that shape is right and has been exercised across
twenty-two families.

`SparseSet` is the one that is not a convenience: it is what makes the Pike VM
linear (`ENGINES.md` R-6) and it has no equivalent anywhere in the ecosystem.

### RX-007 — no dependencies, and `[dependencies]` stays empty
**2026-09-03.** The language and its prelude, and nothing else. Including, by
name: not the compiler's `src/`, not the compiler's `lib/` (scheduled to move
to an `nlibc` sibling, so importing it today is importing a path that will
change — and `nregex` needs nothing from it, since it makes no syscall), and
not `nitpick-tui` despite both generating Unicode range tables from the same
UCD. That overlap is recorded as O-X1 and revisited when dependency resolution
lands.

### RX-008 — `nregex` is target-independent
**2026-09-03.** No syscall, no endianness assumption in any committed table, no
pointer-width assumption in a serialised form. Only the Python harness is
Linux-specific, and only because it drives `llc` and `ld.lld`.

Recorded as a decision rather than an accident because it is a **constraint to
be preserved**: a future convenience that reads a file or an environment
variable would silently cost it, and the harness's `check_no_syscalls`
(`TESTING.md` §8) is what keeps it true. It is also unusual in this ecosystem —
`nitpick-tui` and `nitpick-sockets` are Linux-on-x86-64 by construction — so a
reader should not assume the local convention.

### RX-009 — a bounded backtracker with lookaround is declined at 1.0
**2026-09-03.** The tempting middle path is a second engine behind an opt-in
supporting lookaround with a step budget, failing rather than hanging.
Declined, on three grounds:

1. **It makes the guarantee conditional.** "Linear, always" is a property;
   "linear unless you used this feature" is a footnote every caller must read.
2. **A budget is a wrong answer, not a slow one.** A search that gives up
   returns no-match or an error for a haystack that *does* match, and which one
   depends on the input's size. That is worse than a refusal at compile time.
3. **It doubles the correctness surface** — a second engine that must agree
   with the first everywhere they overlap, for a feature set the first cannot
   express.

*Kept open as O-R1 rather than closed*, with the shape it would take written
down, because declining a feature is cheaper to revisit than removing one.

---

## The pattern language

### RX-010 — the accepted syntax is a stated grammar, not "PCRE-compatible"
**2026-09-03.** `SYNTAX.md` §1 is the grammar; `COMPAT.md` is an honest
difference list. No engine is PCRE-compatible, several claim to be, and the
claim is how a user discovers a difference at run time in production.

### RX-013 — leftmost-first, not leftmost-longest
**2026-09-03.** The alternation branch and quantifier expansion that come first
in the pattern win, as in Perl, PCRE, Python, Rust and RE2's default.
`sam|samwise` against `samwise` matches `sam`.

*Alternative:* POSIX leftmost-longest, which is more principled — the answer
does not depend on how the author ordered the alternatives — and which almost
nobody expects, because every pattern written in the last thirty years assumes
leftmost-first. Recorded as O-Y1: a `longest` option is cheap in a Pike VM (it
is a different rule for which thread wins a slot) and is deferred until asked
for.

### RX-015 — the repetition product is bounded, and checked as the HIR is built
**2026-09-03.** `((a{1000}){1000}){1000}` is thirty characters that would
demand a billion instructions. This is the program-size analogue of ReDoS and
it is closed the same way — by a bound, not a timeout.
`NREGEX_REPEAT_PRODUCT` multiplies nesting factors on the way down, so the
refusal happens **before** the memory is requested rather than after.

*Alternative:* bounding only the total program size, which is also done, and
which would allow the compiler to spend a long time discovering it. Checking
the product early is what makes the refusal fast.

### RX-017 — one spelling for a named group: `(?<name>…)`
**2026-09-03.** Python's `(?P<name>…)` and .NET's `(?'name'…)` are **refused**,
not accepted as aliases, with the right spelling named in the message. Two
spellings for one construct is the context-dependence the ecosystem's blueprint
philosophy refuses first, and a refusal that names the alternative costs a user
five seconds once.

---

## Unicode

### RX-020 — matching is over BYTES; a Unicode class becomes a UTF-8 byte automaton
**2026-09-03.** The haystack is `uint8[]` and is never validated. A codepoint
class is compiled into an automaton over UTF-8 byte sequences
(`COMPILE.md` §2).

*Reasoning, in order of weight:* a systems library must be able to search a
network buffer, a mapped file, or a log with one bad byte in it, and a library
that only searches validated `string` cannot; the DFA's alphabet is then 256
symbols, which is what makes a lazy DFA tractable at all (and compresses to 8
or 12 equivalence classes in practice); and every offset a Unicode-mode search
reports lands on a UTF-8 boundary **by construction**, because the byte
automaton only accepts well-formed encodings — no checking required.

*Alternative:* decoding codepoints as the engine runs, with the automaton over
codepoints. Simpler class compilation, and it forces a decision about what to do
with an invalid byte *at match time, on the hot path, in the middle of an
automaton* — plus an alphabet of 1.1 million symbols that needs class-based
compression anyway. Declined.

*Cost accepted:* the UTF-8 range compiler is a real piece of work and gets its
own cycle (0.4).

### RX-021 — Unicode tables are generated and committed as Nitpick source
**2026-09-03.** `tools/gen_unicode.py` reads a pinned UCD and writes
`src/unicode/*.npk`, which are committed. A build needs the compiler and
nothing else: no Python, no network, no `/usr/share/unicode`. The generator is
checked rather than trusted — the harness re-runs it and requires byte
identity, the same instrument the compiler uses for its builtin signature
table. The version lives in one file and upgrading it is a recorded decision
with a re-run corpus.

### RX-022 — simple case folding at 1.0; full folding refused by name
**2026-09-03.** `(?i)` folds classes by `CaseFolding.txt`'s `C` and `S`
entries, applied at HIR construction so the engine does no folding at all.

*Full folding is not merely omitted.* It maps one codepoint to several — `ß` to
`ss`, `ﬁ` to `fi` — which stops a case-insensitive class being a set of
codepoints and makes it a set of *strings*. That changes the automaton from
character-driven to sequence-driven and changes what a match offset means. It
is a different matching problem needing its own specification, and Rust's
`regex` makes the same choice. Documented as a limitation with the affected
codepoints published, since no compile-time refusal can detect a pattern that
would have depended on it. Recorded as O-U1.

*A consequence worth naming:* folding must be a table lookup, never `± 32`.
`(?i)k` matches `U+212A` KELVIN SIGN and `(?i)s` matches `U+017F` LONG S — both
correct Unicode behaviour, both surprising, both asserted by a test.

### RX-023 — the supported property set is stated exhaustively; blocks are refused
**2026-09-03.** General_Category, Script, Script_Extensions and the standard
binary properties, with UAX #44 loose name matching. **Unicode blocks are
refused**, naming `Script` in the message: a block is a historical range
assignment, not a set of characters used by one script — Greek letters appear
in four blocks and the Greek block contains Coptic — so every use of a block in
a real pattern is a bug that happens to work for the author's test data.

---

## Compilation

### RX-030 — the instruction set is a closed list
**2026-09-03.** Eight kinds, and a tree check asserts every one is emitted by
the compiler and handled by every engine and by the oracle. An `InstKind` an
engine does not handle is a wrong answer waiting for the pattern that emits it.

### RX-031 — the program is a flat POD array with no owning field
> **SUPERSEDED IN PART by RX-155 (2026-09-25)** — its clause that a pointer
> graph "is also refused by TYPE-046 the moment any node owns a string". Nothing
> refuses an owning node; the POD program is this library's design, and stands.
**2026-09-03.** A `Program` is therefore copyable, comparable and dumpable,
which is what makes a compiled program a committed fixture and a compiler
change a visible diff rather than behaviour nobody can inspect. The alternative
— a pointer graph — is also refused by TYPE-046 the moment any node owns a
string, and would dangle on the first `Vec` growth in any case.

### RX-032 — the parser uses an explicit stack, never native recursion
**2026-09-03.** A recursive-descent parser on `((((((…` blows the call stack,
and the language has no stack-depth guard — the failure is a segfault, not a
controlled stop, which is precisely what this ecosystem exists to prevent. The
same rule applies to every HIR and program walk, whose depth a pattern
controls.

---

## The engines

### RX-034 — the mutable search state is a `Cache` the caller owns
**2026-09-03.** `regex_find(@re, @cache, hay)`. The lazy DFA's state cache and
the Pike VM's thread sets live in a `Cache` value the caller allocates and
passes in.

*Three properties follow, and each is why this is the API rather than a hidden
field:* a `Regex` is immutable, so any number of threads may borrow one at once
with no lock and no atomic; a search allocates nothing, which is what makes
"matching cannot trap" true rather than merely likely; and the cost is visible,
so a caller decides for itself whether it wants one cache per thread or one per
request.

*Alternative:* an internal cache behind a mutex, which serialises every search
in the program on one lock; or an internal pool, which makes that decision for
the caller invisibly and is wrong for somebody. Rust's `regex-automata` exposes
the same explicit `Cache` for the same reasons.

### RX-040 — the 1.0 engine set is the Pike VM, the lazy DFA and prefilters
**2026-09-03.** The one-pass NFA and the bounded backtracker are cycle 0.11.
The Pike VM alone is correct and slow; the DFA makes `is_match` and `find`
fast; the prefilters make "search a big haystack for something rare" fast. The
other two are latency optimisations for capture-heavy workloads and are worth
having *after* there is something to measure.

### RX-041 — every engine produces the same answer, and the suite proves it
**2026-09-03.** For a given program, haystack and start offset, the match
offsets and every capture slot are identical whichever engine ran. An engine is
a performance decision and can never be a semantic one.

The corpus stage runs every case through **every** engine, forced, and requires
identical results — and again with each optimisation disabled in turn
(prefilters, alphabet compression, suffix sharing, the DFA). An optimisation
that changes an answer is caught by the run that turns it off and by nothing
else. This is the strongest correctness statement the library makes and it is
the analogue of `nitpick-tui`'s render-and-parse-back round trip.

### RX-042 — the DFA cache is bounded, and exhaustion is a fallback, never a failure
**2026-09-03.** At `NREGEX_DFA_CACHE_BYTES` the cache is cleared and rebuilding
continues; if clearing recurs so often that the DFA is doing more work than the
Pike VM would — measured as states created per byte against a stated threshold
— the meta-engine abandons the DFA for that search. The user never sees it: it
changes the time, never the answer, and RX-041's cross-engine run is what
proves that.

### RX-043 — a prefilter never decides a match
**2026-09-03.** It finds candidate start positions faster than an automaton
can; every candidate is confirmed by a real engine. A prefilter wrong in the
direction of "too many candidates" is slow; one wrong in the direction of "too
few" is a correctness defect, and the prefilters-off run is what catches it.

### RX-044 — the Pike VM is the reference; the naive oracle outranks it
**2026-09-03.** Where an engine and the Pike VM disagree, the Pike VM is right.
Where the Pike VM and the naive oracle disagree, the oracle is right. A stated
ordering means "which one is correct" is never a discussion.

---

## The public surface

### RX-050 — a `Match` is byte offsets, never a slice
**2026-09-03.** `struct:Match = { int64:lo; int64:hi; }`. A slice is a
second-class borrow and cannot pass **up** the call stack (D-004, D-070), so a
function cannot return one.

*Better than the alternative in three ways worth stating*, because a reader
arriving from Rust will expect `&str`: a `Match` is a plain 16-byte value that
can be stored in a `Vec`, sent through a channel and held across an `await`;
the haystack's lifetime stays the caller's business and is not encoded in a
type; and offsets are what a caller wants anyway when the haystack is a mapped
file.

*The fields are `lo` and `hi`*, not `start` and `end`, because `end` is the
`when`/`then`/`end` terminator and does not parse as a field name.

### RX-051 — replacement takes a template, not a callback
**2026-09-03.** The language has no closures (D-018), so `replace_with(|m| …)`
is unspellable. `regex_replace_all(…, "$year-$month", @out)` with a closed
template syntax, validated once before the first search rather than per match.
`regex_replace_with` takes a bare non-capturing function value; a caller
needing context passes it through the haystack or performs the replacement
itself over `regex_matches`.

That is the honest consequence of D-018 and it is stated rather than worked
around: an `any->` context pointer would be an untyped escape hatch in a
library whose selling point is that it has none.

### RX-052 — an iterator is a struct with `next`, not a callback
**2026-09-03.** And it borrows its `Regex` and `Cache`, so it is second-class:
it cannot be returned from a function, stored past the call, sent through a
channel, or held across an `await`. Stated in `API.md` A-15 because a consumer
arriving from Rust will expect to return one and will not be able to.

### RX-054 — `uint8[]` is the primitive; `string` is a convenience over it
**2026-09-03.** Every search entry point takes a haystack slice; a `string`
caller writes `string_bytes(s)`, which is the borrowed view the floor already
provides at no cost. Two reasons for this direction rather than the other: a
systems library is asked to search things that are not validated text, and
`string_bytes` is free while `string_from_bytes` over a subrange is not.

---

## Errors and bounds

### RX-060 — exactly ONE public error identity
**2026-09-03.** `pub error:ERegexPattern;` — the pattern could not be compiled.
**Importing `nregex` costs a program's `failsafe` exactly one arm.**

It falls out of RX-003 and RX-061 together: compilation is the only thing that
can fail, and a shutdown handler does not care *which* way a pattern was
malformed. The detail rides as a `PatternError` value with a closed
`PatternErrorKind` enum — thirty ways a pattern can be malformed are thirty
variants and one identity, because REACH-002 counts identities and not
variants.

*Alternative:* separate identities for syntax, limits and unsupported
constructs. Declined: a `failsafe` treats all three identically, and each extra
identity is a mandatory arm in every consuming program forever.

### RX-061 — matching cannot fail and cannot trap
**2026-09-03.** `regex_find` returns `Match?`, not `Result<Match?>`. There is
no error channel on the search path at all. No allocation (RX-034), no
division, no arithmetic that can overflow at haystack scale, and every index
through a checked accessor whose bound is established by construction.

This is the library's cleanest property and several other rules exist to
protect it — it is why the `Cache` is pre-allocated, why the DFA falls back
rather than failing, and why every bound is checked at compile time.

### RX-062 — every bound is a named constant in one file
**2026-09-03.** `src/core/limits.npk`, and a tree check enforces it. Nine
bounds, each overridable through `RegexOptions`, each with a test sitting
exactly on it and one exceeding it.

---

## Testing

### RX-070 — the oracle is a naive reference matcher, written before any engine
**2026-09-03.** A deliberately simple, obviously-correct backtracking matcher
over the HIR, in `tests/oracle/`, exponential in the worst case and run only on
tiny inputs. It imports nothing from `src/` but `core` and `hir`, because a
shared bug would make it agree with the thing it judges.

**Written and tested at cycle 0.5 — before the NFA compiler at 0.6** — so the
compiler and the Pike VM are developed against an instrument that already
works. This is the compiler's "instruments precede the constructs they guard",
and it is why this library's cycle order looks unusual.

*It is allowed to be exponential*: it runs with a step counter and reports a
case it cannot finish as *not compared* rather than as a failure. A pattern the
oracle cannot finish is exactly the pattern RX-003 exists to make fast.

### RX-071 — three corpus sources, each labelled
**2026-09-03.** Ours, written against `SYNTAX.md`; third-party, fetched by
pinned revision rather than vendored, with the suite and revision recorded; and
everything the fuzzer ever found, permanently.

The third-party candidates are decided at cycle 0.5: **RE2's test data**
(closest semantics — leftmost-first, no backreferences, so its expectations are
ours), **Rust `regex`'s suite** (closest feature set, including Unicode classes
and class set operations), and the **AT&T POSIX set** (broad, old, and its
leftmost-longest expectations must be filtered or reinterpreted — noted so
nobody adopts them wholesale).

### RX-072 — the linear-time guarantee is tested, not asserted
**2026-09-03.** For generated patterns including the classic catastrophic
family — `(a+)+$`, `(a|a)*$`, `(a|aa)*$`, `a?{n}a{n}` — and haystacks of
geometrically increasing length, the recorded **step count** must grow no
faster than linearly within a stated constant.

This is the test that would be quietly dropped when it goes red under a
refactor, so it is in the gate for every cycle from 0.7 onward. RX-003 is the
claim; this is the evidence.

---

## Performance

### RX-080 — the regression gate is on steps, not time
**2026-09-03.** Every benchmark reports both. Time varies with the machine;
step count does not, so a regression in steps is a real regression and a
regression in time alone may be the machine. Time is recorded and reported; the
gate is 20% on steps against the committed baseline.

---

# The second batch — ratified 2026-09-03

The three questions this plan put to the project's author, answered as
recommended, with one amendment the author made to where a consumer lives.

### RX-100 — the Unicode version is the latest stable UCD at cycle 0.3
**2026-09-03, settling Q-1.** Recorded in `src/unicode/version.npk` as a single
`pub fixed string:UNICODE_VERSION`, and in the header of every generated table.

**There is no floor**, unlike a grapheme segmenter's: nothing here depends on a
property that arrived in a particular release. What the version does control is
which patterns match — `\p{Script=Han}` gains codepoints between releases — so
a bump regenerates every table, re-runs the agreement suite, and is a recorded
decision rather than a refresh.

### RX-101 — the dogfood consumer is `grep`, and it lives in `nitpick-posix`
**2026-09-03, settling Q-2, with the author's amendment on location.** The
program is `grep`: it exercises the prefilters (the common case), the `Cache`
lifecycle across many searches, byte-mode matching over a file that may not be
valid UTF-8, and the replacement path.

It does **not** live in this repository's `examples/`. Consumers are real
programs with their own lifetimes, and they live in
[`nitpick-apps`](https://github.com/alternative-intelligence-cp/nitpick-apps);
`grep` is a POSIX utility, so it is built in
[`nitpick-posix`](https://github.com/alternative-intelligence-cp/nitpick-posix)
alongside the rest of the set rather than in a repository of its own.

*The consequence, which is not a cost:* cycle 0.14 is now gated on a program in
another repository, and the import is by relative path until the compiler's
dependency resolution lands (O-N…). That is the same workaround every other
cross-repository reference uses.

### RX-102 — `grep` will not be a conformant POSIX BRE implementation, and that is the right answer
**2026-09-03. A consequence of RX-101 and RX-003 meeting, found while settling
where the consumer lives — before either was written.**

POSIX **basic** regular expressions include back-references (`\(…\)` … `\1`).
RX-003 has none, because back-references are precisely what force a
backtracking engine. So a strictly conformant `grep -G` cannot be built on this
library, and the collision is real rather than a technicality.

*It resolves in this library's favour, and the argument is not "our library
matters more".* `grep` is the utility in the entire POSIX set **most likely to
be pointed at input somebody else controls** — that is what it is for. Adding a
backtracking engine to satisfy a conformance checkbox would put the exact
denial of service this library was designed to eliminate into the one program
that most needs it eliminated.

*So:* a pattern containing a back-reference is **refused at compile time, by
name, with the byte offset and the reason** — never silently accepted, never
quietly reinterpreted as a literal. `nitpick-posix` documents it as a stated
conformance departure. It is also the choice `ripgrep` makes, for the same
reason.

*What this does not change:* RX-009's refusal of a bounded backtracker stands,
and this is now the second independent argument for it. O-R1 keeps the shape on
file.

### RX-103 — `RegexSet` lands at 1.1, and the program format reserves for it from 1.0
**2026-09-03, settling Q-3.** Multi-pattern matching is a real feature with its
own semantics — which patterns matched, in what order — and it is deferred to
1.1.

The deferral costs nothing **because the compiled program format carries a
pattern id from 1.0** (`COMPILE.md` §6). Retrofitting one later would change
every engine's inner loop and invalidate every committed fixture; reserving the
field now costs a word nobody reads. This is the general shape worth copying:
**defer the API, not the representation.**

---

## Cycle 0.0.0 — what the language probes settled

*Appended 2026-09-03 by stream 1, working `meta/roadmap/0.0/0.0.0.md`. Every
decision here rests on a probe in `tests/probe/` that was run through all four
steps of the recipe — `npkc`, `llc`, `ld.lld`, and the binary — against pinned
toolchain `950bb1d` under LLVM 20.1.2. Where a probe refuted the plan's
hypothesis, the decision says so.*

### RX-110 — the leak gate says what it covers, everywhere it is stated
> **SUPERSEDED IN PART by RX-155 (2026-09-25)** — its parenthesis "TYPE-046
> forces it" of the POD structures. Nothing forces it; `SAFETY.md` S-23a now
> requires it of anything a `Vec` holds. The decision stands.
**2026-09-03, settling the workbench's tenth author question for this
repository.** *(That question is `../BOARD.md`'s, not this repository's; the
author ruled that the unfalsifiable leak gate is corrected in each repository
when its own stream claims it, and stream 1 claimed this one.)*

Four sites in this repository stated, and two more implied, that *"the suite's
programs exit 0, so a missing `free` on any path is a trap rather than a pass
(D-151)"*. **That is false for every managed body**, and the correct
formulation — the compiler's own, carried verbatim because it is exact — is:

> **D-151 counts `wild` blocks, D-188 counts live drivers, and neither sees a
> managed body.**

`nitpick-time`'s cycle 0.0.0 measured the gap: a `Vec<string>` whose block was
freed and whose elements were not retained **125 MiB over two million elements
and exited 0**, and only a 64 MiB address-space cap turned it into a `HeapOom`.

*The six sites, produced by `git grep -n 'D-151'` and not from recall* — the
dispatch that ordered this sweep named four, and the command found six:
`meta/specs/SAFETY.md:25`, `meta/roadmap/0.0/README.md:130`,
`meta/roadmap/0.0/0.0.4.md:14`, and **three** in `meta/roadmap/0.0/0.0.0.md`
(lines 54, 265 and 314). Two of the three were not on the list precisely
because they were phrased as the *correct* narrow claim in one case and as a
throwaway aside in the other. The general rule this instance is evidence for:
**a sweep list is generated by a command and pasted, never recalled.**

*What was added rather than merely weakened.* The correction is a statement
about **coverage**, not a retreat into vagueness — the model is
`nitpick-sockets`'s `ANCILLARY_MODEL.md` line 67, which says a path "takes no
`wild` bytes, so it cannot trip D-151 on any exit path". `SAFETY.md` §8b is the
new home of the rule (S-22), and it names which of this library's structures
are POD and therefore fully covered (`Program`, `Hir`, the engines' thread
lists — TYPE-046 forces it) and which are the exceptions to watch
(`Hir.names`, any future owning `Vec<GroupInfo>` or `Vec<string>`).

*The hook is deliberately left in.* The compiler's `NPK_HEAP_STATS` does not
exist yet. When it lands the real gate becomes a `peak_live` assertion and the
memory cap becomes a backstop; §8b says so, so that the day it arrives the
change is greppable rather than archaeological.

*Alternatives declined:* deleting the claim (it is true and useful of `wild`
storage, which is what `Vec<T>`'s block is); a house-rule harness check
standing in for the gate (the ecosystem's rule is that a compiler gap is raised
and waited on, not papered over library-side); leaving it and adding a note
(the wrong statement is in a **specification**, and RX-002 makes the
specification the authority — an authority known to be wrong and not corrected
is worse than none).

### RX-111 — D-070's bounds check does not reach a `wild T->` block, so the accessor pair is the check
**2026-09-03, from probes 08, 08b and 08c.**

`SAFETY.md` §1 said *"Indexing is bounds-checked and traps — an out-of-range
program counter is a **crash**, not a wrong answer"*. That is true of the
language and **false of this library's own container**.

D-070's check attaches to types that carry a length — a slice `T[]` and a fixed
array `T[N]`. A `wild T->` block is a bare pointer, and indexing it is raw
pointer arithmetic. Measured as a pair, same offset, same program shape:

| Probe | Type | Index | Result |
|---|---|---|---|
| `probe08c_slice_index_traps.npk` | `int64[]` slice, 4 elements | 999 | **exit 94**, `OutOfBounds` |
| `probe08b_wild_index_unchecked.npk` | `wild int64->`, 4 elements | 999 | **exit 0**, value returned |

**`Vec<T>.items` is a `wild T->`** (RX-006), so `Program.insts`, `Hir.nodes`,
`Program.classes`, every engine's thread list and the sparse set are all
unchecked.

*How it was found, because the route matters.* Probe 08 was written with a §B
asserting that the classic sparse-set trick traps in Nitpick where it is merely
undefined in C, and calling that a denial of service. Probe 08b was then written
to *prove* that claim and disproved it — it exited 10 where 94 was expected. The
corrected finding is strictly worse than the one it replaces: an unguarded index
does not stop the program, it **returns an unrelated heap word**, so a wrong
program counter is a silently wrong match rather than a controlled stop. This is
the third time in this ecosystem that a probe written to confirm a specification
sentence has refuted it, and it is the argument for writing the confirming probe
even when the sentence looks obvious.

*What changes.* `SAFETY.md` gains §5.3 (S-23) and §1's row is rewritten to name
the types the guarantee actually covers. The "one accessor pair" in §1 stops
being a tidiness measure and becomes the library's only bounds check, enforced
by a tree check that no `.items[` appears outside `src/core/vec.npk`. Every
accessor checks `0 <= i` **and** `i < count`, because an index derived from an
`int32` can be negative and a negative index reads backwards off the block
without complaint — the half a reader porting from C will leave out, since there
the index is `unsigned`.

*Not a compiler defect, and so not a stop (W-11).* Nothing is under-enforced:
`wild` is the language's unchecked primitive and says so in its name. The defect
was in this document.

*Alternatives declined:* making `Vec<T>.items` a slice `T[]` so the language
checks it — a slice cannot be returned from `vec_init` (D-004 rule 2, and O-N9
means the compiler would not even say so today), and the container would not
survive `ralloc`; keeping the accessor pair optional and relying on review — the
failure is silent, which is precisely the case review does not catch.

### RX-112 — RX-050 stands, and probe 06b's acceptance is not a licence
**2026-09-03, from probe 06b, overriding `0.0.0.md` §5's instruction to the
executor.**

`0.0.0.md` §4 wrote probe 06's second half — a function returning a `uint8[]`
subrange — as **"expected refused"**, and §5 told the executor that if it were
accepted, the correct response was to *"stop and re-plan `API.md` §2"*, because
an acceptance would mean RX-050 was over-cautious and a `Match` could carry a
slice.

**It is accepted, and the plan is not followed.** The plan predates the answer.

The acceptance is the workbench registry's **O-N9** — a confirmed, independently
verified compiler defect, accepted as the compiler's **DEF-3** and scheduled as
the second commit of its cycle 1.5.1b. D-004 rule 2 forbids a borrow in the
value of a `pass`; the compiler enforces it for `@`-borrows and not for slice
views, and `TYPE_REFERENCE.md` §9.2.1 already states that a slice **is** a
second-class borrow. So the compiler accepting this says nothing whatever about
whether RX-050 is right.

*Therefore:* **RX-050 stands unchanged.** `Match` carries byte offsets,
`API.md` §2 is not re-planned, and no function in `src/` returns a `uint8[]`.
Re-planning an API onto a rule that is known to be under-enforced and known to
be scheduled for repair is precisely the "workaround buried in library code that
outlives the bug" that W-11 forbids — the library would compile today and stop
compiling at the re-pin.

*What probe 06b contributes instead.* O-N9's six cases all escape a view of a
frame **local** and dangle, reading the runtime's `0xAA` free-poison. 06b's
shape is a subrange of a **parameter**, so the storage is the caller's and the
returned view is correct. **Today's rule and DEF-3's are different, and the
difference matters when quoting either.** The live check at `950bb1d` is
`borrows_only_param_rooted` (`src/frontend/analysis/escape.npk:507`, called at
:425 as the second look before `BORROW_RETURNED` is raised): *is every borrow
inside this expression rooted at a **parameter** of the current function*. That
is what accepts 06b — its view is rooted in a parameter. The **pointer-shaped
root** formulation (a wild pointer, a slice, a `cstring`) is DEF-3's *future*
rule, not today's. Under either, 06b is **confirmation that the naive fix was
avoided**, not a new request. The shape that will change under DEF-3 is
a view of a **temporary**: `string_bytes(string_concat(a, b))` returned becomes
**`NITPICK-BORROW-012`**, and D-246 already requires binding that intermediate
because the `string_concat` is an owning temporary that leaks today.

> **`NITPICK-BORROW-012` CANNOT BE REPRODUCED AGAINST THE PINNED TOOLCHAIN, AND
> ITS ABSENCE THERE IS NOT EVIDENCE.** It is allocated by DEF-3's **step 2** and
> exists only in the compiler's unlanded worktree commit; at `950bb1d` the
> highest allocated borrow code is `NITPICK-BORROW-011`
> (`src/frontend/analysis/analysis_codes.npk:106`), and a grep of the pin finds
> nothing. This subcycle greped the pin, found nothing, and briefly recorded the
> code as non-existent — twice wrong in one line, once in each direction.
> *Sourced from the compiler session through the coordinator; not verifiable
> from this repository until the re-pin.*
>
> The distinction it marks is real. DEF-3's plan said it adds no new code, and
> that holds for **every refusal shaped like "as if `@` had been written at that
> argument"** — a view of a local returned, held in a literal, laundered through
> a call, stored through a pointer parameter — all `BORROW-001`/`002`. Writing
> the rule found the one shape the `@`-equivalence has no arm for: **`@` of a
> temporary cannot be spelled**, so no existing code's text is true of it and
> tracking it would need a root with no name. It refuses outright, telling the
> author to bind the value first, after which the view is a borrow of that
> binding and is checked like any other.

*And the house rule is restated at the right strength.* `nitpick-time`'s "a view
is a parameter, never a return value" was deliberately conservative, written
when nothing could tell the safe cases from the dangerous ones. This library
adopts the narrower permanent rule instead: **`src/` returns VALUES and takes
views as parameters** — correct under either regime, and not a bet on how DEF-3
lands.

*Alternatives declined:* re-planning `API.md` §2 to carry a slice, as §5
instructed (it would break at the re-pin, and it builds the API on a defect);
recording the acceptance without a decision (§5 gave a standing instruction, and
an instruction not followed must be overridden in writing or the next reader
follows it).

---

## Cycle 0.0.1 — what building the skeleton settled

*Appended 2026-09-03 by stream 1, working `meta/roadmap/0.0/0.0.1.md`. Every
decision here rests on a command in
[`../tests/conformance/TRANSCRIPT.txt`](../tests/conformance/TRANSCRIPT.txt),
committed verbatim with its exit code, run against pinned toolchain `950bb1d`
under LLVM 20.1.2. Three of the four correct a specification; the fourth is
housekeeping the author asked for.*

### RX-113 — the umbrella re-exports with `pub use`, one name per line, and never plain-`use`s a path it re-exports
**2026-09-03, from building `src/lib.npk` and measuring what a consumer can
see.**

`0.0.1.md` §2's **P-7** said `src/lib.npk` re-exports deliberately, one line per
public name, "because `use` is not transitive". The premise is correct —
`MODULE_REFERENCE.md` §2.3 says so and the measurement confirms it — but the
mechanism was never checked, and two of the three ways to write it do not work.

**What was measured**, over a three-consumer matrix (a type, an `error:`
identity, a function), each consumer isolated so that a resolve-phase failure
could not mask a type-phase one:

| `src/lib.npk` contains | type | `error:` | function |
|---|---|---|---|
| nothing | ✗ | ✗ | ✗ |
| `use "./api/api.npk".*;` | ✗ | ✗ | ✗ |
| `pub use "./api/api.npk".*;` | ✓ | ✓ | ✓ |
| `pub use "./api/api.npk".Match;` | ✓ | ✗ | ✗ |
| `pub use "./api/api.npk".{Match, ERegexPattern, api_ping};` | ✓ | ✓ | ✓ |
| three separate `pub use "…".Name;` lines, either order | ✓ | ✓ | ✓ |

*Therefore, three rules, and `src/lib.npk`'s header states all three:*

1. **Every line in the umbrella is `pub use`.** A plain `use` re-exports
   nothing. An `error:` identity crosses a `pub use` exactly like a type does,
   so the one public name this library has today is re-exported by the same
   mechanism as the surface it will grow.
2. **The umbrella never plain-`use`s a path it also `pub use`s.** This is the
   sharp one. `symtab_bind_import` (`src/frontend/symbols.npk`) declines any
   name already bound and, on the "same declaration reached twice" path,
   **returns the prior binding without merging the new flags** — so the
   `SYM_PUB` bit a `pub use` carries is dropped whenever a plain `use` bound
   the name first. The re-export becomes a no-op, `npkc` reports **nothing** at
   any severity, and the failure appears in the consumer as *"cannot find
   `ERegexPattern` in this scope"*. Order-dependent, silent, and remote from
   its cause. Transcript §E2 and §E3 are the same two lines in the two orders:
   different behaviour, identical output. Raised as provisional workbench
   **O-N13**.
3. **One name per line.** Several single-name `pub use` lines from one path do
   compose, in either order, so the greppable form P-7 wanted is available and
   a removal is one line of diff. `API.md` §1's list is what it grows into.

*Alternatives declined:* the braced selective form
`pub use "./api/api.npk".{a, b, c};` — it works, and it makes a one-name change
a whole-line diff and invites the list to be reformatted, which is exactly what
a public surface should not invite; the wildcard `pub use "…".*;` — it works
and it re-exports whatever `api` happens to make public, which is the opposite
of a deliberate surface and would let an internal helper become part of the
API by the addition of one `pub`.

*The house rule generalises past the umbrella.* Any module that both consumes
and re-exports from one path is exposed to rule 2, and the ordering that saves
it (`pub use` first) is not something a reader can be expected to know.
`check_layering` at cycle 0.0.3 gains a check: **no file contains both a plain
`use` and a `pub use` of the same path.** It is a two-line check over the same
`use`-edge list that check already builds.

### RX-114 — the four legacy local `O-N` ids become `O-G1` … `O-G4`; `O-N` in this repository means the workbench registry
**2026-09-03, discharging the recommendation cycle 0.0.0's report made to the
author.**

`meta/OPEN_QUESTIONS.md` carried this repository's own `O-N1` … `O-N4` beside
the workbench registry's `O-N9` … `O-N12`, so `O-N` meant two different
numbering schemes in one file and `O-N4` meant two different findings.
0.0.0's report recommended renumbering the four legacy ids to a local prefix and
reserving `O-N` for the registry. Done, with one deviation and one refusal.

**The deviation: the recommended `O-C` prefix could not be used.** `O-C1` and
`O-C2` are already this repository's *compilation* questions — sharing
instruction suffixes, and reverse programs — cited across five files. Renumbering
the legacy four onto that prefix would have recreated, exactly, the collision it
was meant to remove. The prefix is **`O-G`**, for a **G**ap in the compiler, and
`meta/OPEN_QUESTIONS.md`'s prefix table gains a row saying so. The mapping is
one-for-one and in order: `O-N1`→`O-G1`, `O-N2`→`O-G2`, `O-N3`→`O-G3`,
`O-N4`→`O-G4`.

**The refusal: `meta/roadmap/0.0/0.0.0.md` was not renumbered.** It is a closed
subcycle's execution record, independently verified at `9b80d69`. Renumbering it
would make it say something that was not true on the day it was written, and a
verified artifact is not rewritten afterwards — the workbench's own `RECORD.md`
keeps a compiler-request id that was misnumbered on the day, for precisely this
reason. Two redirect entries in
`meta/OPEN_QUESTIONS.md` keep its `O-N1` and `O-N4` citations resolving, and each
says which registry item shares the number so the two cannot be confused.

**One correction to that file was made, because the author directed it and
because it moves the record toward its own evidence rather than away from it:**
the prose said "Five commits" where the same file's `commits:` list and `git log`
both say six. The correction is marked in place rather than made silently.

*What is left for the author, because this repository does not write the
workbench:* the registry's entry for the `npkg` gap lists this repository's local
id under its old number; it is now **`O-G3`**. The redirect table in
`meta/OPEN_QUESTIONS.md` names both sides.

*Alternatives declined:* `O-C`, as recommended (it collides — see above);
renumbering the *compilation* questions instead to free `O-C` (they are cited in
five files against the legacy ids' three, and they are ours by design where the
legacy four are the compiler's by subject, so the prefix table would still lie);
leaving the collision with the warning block 0.0.0 added (it made citations
resolve and did nothing about `O-N4` meaning two findings).

### RX-115 — no module of this library can be assembled on its own; the unit of emission is a program, and `BUILD.md` §2 is amended to say so
> **SUPERSEDED IN PART by RX-151 (2026-09-25)** — its mechanism, *"every one is
> refused by `llc`"*, which was `950bb1d`'s and has been false since `94874ce`.
> The conclusion — there is no library object, and the unit is a program root —
> stands, for a different reason: the link. *(Marker added at cycle 0.0.4b.)*

**2026-09-03, from compiling all eight files in `src/` through `npkc` and then
`llc`.** Transcript §A.

`BUILD.md` §2 drew the build as `src/lib.npk → npkc → build/nregex.ll → llc →
build/nregex.o`, and `nitpick.toml`'s `[build] output = "build/libnregex"` names
the artifact. **Neither is achievable at `950bb1d`, and the reason is not
`npkg`'s.**

Every file in `src/` compiles at `npkc` **exit 0** and every one is refused by
`llc`:

> `error: use of undefined value '@npk_failsafe'`

**The cause, counted rather than inferred.** `npkc` emits **seven call sites**
to `@npk_failsafe` into every translation unit — they are the prelude's own trap
paths — and emits **no `declare` for it, ever**. LLVM requires a `declare` for a
function that is called and not defined in the module, so the IR is not
well-formed text. A *program* is saved only because its own `failsafe`
declaration produces a `define`; a library file has nothing to produce one, and
under D-248 may not: `main` and `failsafe` are permitted only in a program's
root file. So **the shape the language mandates for a library is the shape whose
IR cannot be assembled**, and `npkc`'s usage line offers no library or module
mode to ask for anything else.

This is the same missing-`failsafe` machinery as the registry's **O-N11** (the
compiler's DEF-5) seen from the other side, and it sharpens that report: DEF-5
asks the frontend to refuse a *root* with no handler, and **one emitted
`declare i32 @npk_failsafe(i32)` would additionally make every library module
assemblable** and would turn DEF-5's own program case into an honest
undefined-symbol error at link time instead of an `llc` parse error. Raised as
provisional workbench **O-N14**, cross-referenced to O-N11.

*Therefore:*

- **`BUILD.md` §2's pipeline is amended**: the unit `npkc` accepts is a
  **program root**, the library reaches the compiler by being imported from one,
  and `build/nregex.o` is not a thing that exists today. `[build] output` in
  `nitpick.toml` is annotated as aspirational rather than removed, because it is
  the manifest key `npkg` will read the day O-G3 closes.
- **`tests/conformance/import.npk` is how `src/` is compiled at all**, which is
  why 0.0.1's acceptance is met by that program's exit code and not by
  `npkc src/lib.npk`'s. `npkc src/lib.npk` exiting 0 is worth keeping as a
  parse-and-resolve check; it is **not** evidence that the library builds, and
  the acceptance list says so now.
- **`O-B2` — ship as source or as an object — is not merely settled in favour of
  source; the object does not exist.** The entry gains that sentence.

*Not a stop, and the boundary is worth stating.* **It blocks** a per-module
object, a `libnregex.o` artifact, and separate compilation as
`BUILD_REFERENCE.md` §4.1 describes it. **It inconveniences** cycle 0.0.2's
harness, which must build through a program root rather than over `src/`, and
cycle 0.0.3's `parse` stage, which is unaffected only because parsing does not
emit. **It does not touch** the library's shape, its layering, its API, or any
rule in any specification: nothing is reshaped to dodge it, and the day the
`declare` is emitted, `BUILD.md` §2's original pipeline works as written.

*Alternatives declined:* giving `src/lib.npk` a `failsafe` so the IR assembles —
that is the workaround W-11 forbids, it is refused by D-248 in any case, and it
would put a second `failsafe` in every consuming program; treating `npkc` exit 0
on `src/lib.npk` as the acceptance and not running `llc` — that is exactly the
mistake registry O-N11 exists to prevent, and it would have shipped a green
subcycle over an unbuildable library.

### RX-116 — `check_no_syscalls` is differential against a committed baseline, not an absolute allowlist
**2026-09-03, from scanning the consumer's object.** Transcript §D.

`BUILD.md` rule B-2 and cycle 0.0.2's checklist specify the no-syscall check as
an object's undefined symbols *"held to a committed expected list — the
allocator, `memcpy`/`memset`, the string primitives"*. **A program containing no
library code at all fails that check.** The consumer's object has **29**
undefined symbols, among them `npk_open`, `npk_read`, `npk_write` and
`npk_sys6`. `nregex` calls none of them: they are the prelude's, emitted into
every translation unit, and `opt -O2` removes exactly one of the twenty-nine.

Combined with RX-115 — there is no library-only object to scan — an absolute
allowlist cannot express RX-008's rule.

*Therefore the check becomes a difference.* A **baseline** program — an empty
`main`, a `failsafe`, importing nothing — is built by the harness, and the
undefined-symbol set of any `nregex` program object must **equal** the
baseline's. Anything present in one and not the other is attributable to
`nregex` and is a red run. Measured today: baseline 29, consumer 29, symmetric
difference empty.

*Why this is better than the allowlist rather than merely possible.* The
allowlist would have to enumerate the prelude's floor, so every prelude change
in a moving compiler would fail the check for a reason that is not this
library's; the difference adapts, and a prelude change instead shows up as a
deliberate one-line update to the committed baseline, which is visible in review.
**RX-008's rule is unchanged** — `nregex` makes no syscall — and only its
enforcement moves.

*Alternatives declined:* scanning the optimised object and allowlisting what
survives (measured: 28 of 29 survive, so it buys nothing and makes the check
depend on the optimiser); dropping the check to cycle 1.0 (it is the cheapest
guard this library has and it belongs where it is).

### RX-117 — the conformance suite runs at stage `compile`, kind `positive`
**2026-09-03, reconciling `BUILD.md` §3 with the compiler's stage vocabulary and
with what 0.0.1 actually needs.**

`BUILD.md` §3 put `tests/conformance/` at stage **`accept`**, defined by
`BUILD_REFERENCE.md` §7.1 as *"accepted by `tools/check` in silence"*. Two
things are wrong with it. `tools/check` is a **compiler-repository** tool this
library does not have and, under RX-007, may not import. And `accept` neither
links nor runs, while 0.0.1's whole point is a consumer that **links and runs**
— `npkc` exit 0 does not mean a program is well-formed (registry O-N11), and
RX-115 is a fresh instance of exactly that.

The compiler's own `compile` stage with `kind = "positive"` means *"compiles,
links, runs, and exits with the expected code"*, which is the property wanted.
`BUILD.md` §3's table is amended: `accept` is struck, `compile`/`positive` takes
`tests/conformance/`, and the `program` row names `tests/probe/` beside
`tests/unit/`, since the probes are `program`-stage entries from 0.0.2. The two
stages the compiler's vocabulary does not have — `corpus` and `oracle` — are
marked as this library's own extensions rather than left to look inherited.

*Alternatives declined:* keeping `accept` and writing our own `tools/check`
(a frontend-only checker is the compiler's, not a regex library's, and
duplicating it to satisfy a table is the tail wagging the dog); putting
conformance at `program` stage (that stage additionally requires the `opt -O2`
re-run, which is right for a unit test and heavier than an import check needs —
though 0.0.1 ran it anyway, transcript §C, and it passed).

### RX-118 — a `buffer` is unchecked too, so `Bytes` owes the same accessor pair as `Vec`
**2026-09-03, correcting a claim relayed to this repository during 0.0.0 and
verified against the compiler's own specification before it was acted on.**

`SAFETY.md` §5.3's rule **S-23** (RX-111) said that indexing is checked on types
that carry a length and unchecked on a `wild T->` block, and named `Vec<T>` as
the library's exposure. A relayed claim held that a `buffer` was reached through
a `uint8[]` view and was therefore in the checked category. **It is not.**

`buffer_bytes` — the accessor that would produce that view — is on
`TYPE_REFERENCE.md` §23's *"Deliberately NOT landed"* list, beside
`buffer_resize` and `buffer_free`. §23's own example spells the byte access
`buf.ptr[0i64]`, and it documents `.ptr` as a **`uint8->`**. So there is no
slice route to a `buffer` at all, and every byte of one is reached through the
bare-pointer branch that S-23's third row describes.

*Therefore S-23's table gains a fourth row and its consequence list gains a
sentence.* **`Bytes` owes `bytes_get` / `bytes_set` exactly as `Vec` owes
`vec_get` / `vec_set`**, checked against `len`, with the same tree check
forbidding a raw `.ptr[` outside `src/core/bytes.npk`. This matters more than the
row count suggests: `Bytes` is B-11's byte sink, **every replacement this library
performs is composed into one**, and the bytes going into it come from a
haystack and a template the caller controls. It was the one structure in
`src/core/` that S-23 did not reach, and the reason it did not was a wrong belief
about the type rather than an oversight about the design.

*Why this is a new decision rather than an edit to RX-111:* RX-111 is settled and
its text stands. What changes is the **specification rule** it produced, which is
amended here — the pattern this repository uses for every correction (RX-002).

*Alternatives declined:* leaving it until cycle 0.0.4 writes `Bytes`, on the
grounds that no code exists yet (the whole value of finding it now is that the
accessor pair gets designed in rather than retrofitted, and 0.0.4's checklist
does not currently ask for one); giving `Bytes` a slice member to make the
language check it (there is no `buffer_bytes` to build it from, and a slice
cannot be returned from a constructor anyway — D-004 rule 2).

*And a note on the route, because it is the second time in two subcycles.* RX-111
was found when a probe written to **confirm** a specification sentence refuted
it. This one was found when a claim arrived by relay and was checked against
`TYPE_REFERENCE.md` before being written down. Both times the sentence was
plausible and wrong, and both times the cost of checking was minutes.

### RX-119 — the probe suite is not declared in the manifest yet, because no single `[[test]]` entry can judge it
**2026-09-03, from writing the manifest's first entries and reading the runner
that will one day consume them.**

`0.0.1.md` §3 step 3 asked for two entries: `conformance` at
`compile`/`positive`, and `probe` at stage `program` over `tests/probe`. The
first is written and is exercised by this subcycle. **The second cannot be
written truthfully.**

`tests/probe/` holds 23 files, and they are not one kind: **16 carry
`expect-exit:` and 7 carry `expect-error:`** — probe02b, probe09, probe12b and
the four probe13s are *refusals*, and being refused is the whole point of each.
Read in `npkg/suites.npk` at `950bb1d`, which is the runner the harness must
stay compatible with (B-4a):

- **`files_of` (:549) takes `path`/`paths` as directories**, listing by suffix;
  `recursive` defaults false, so a subdirectory is excluded.
- **`run_program` (:779) judges every file it finds**, skipping only those
  another file in the suite imports. It does **not** skip a file carrying
  `expect-error`, so the seven refusals would be built as programs and fail.
- **`run_compile` (:608) does not filter by expectation either.** `kind`
  selects the checker (`check_positive` / `check_negative` / `check_diagnostic`)
  and not the file set, so a `positive` entry and a `negative` entry over the
  same directory each judge all 23 rather than 16 and 7.

So a mixed directory is not expressible, and the compiler's own answer is a
directory per kind.

*Therefore:* the entry is **written out in `nitpick.toml` as a comment**, with
this evidence and the exact three-entry shape it becomes, and **cycle 0.0.2
makes the split**, because 0.0.2 builds the runner and the split is a runner
decision. `0.0/README.md`'s 0.0.2 checklist gains the item.

*Why not just move the seven files now.* The move is right and it is small —
`tests/probe/refused/`, seven files, content unchanged. What stopped it here is
that those paths are cited by **cycle 0.0.0's execution record**, which is a
closed, independently verified artifact (RX-114), and moving files out from
under a verified record is a larger step than a subcycle should take without
being asked. It costs nothing to defer: nothing reads this manifest today, and
`npkg` cannot build this library at all (O-G3).

*Alternatives declined:* declaring `probe` at `program` over the mixed
directory anyway, since nothing reads the manifest (that is precisely the
"manifest that appears when the tooling arrives is a manifest nobody reviewed"
failure the file's own header was written to prevent, and a knowingly-false
declaration is worse than an absent one); teaching **our** harness to skip a
`program`-stage file carrying `expect-error` (it would work, and it silently
diverges our stage vocabulary from the compiler's, which is the one thing
`BUILD.md` §3 exists to prevent — the migration to `npkg` is supposed to be a
change of runner, not of suite); listing the sixteen paths explicitly (`path`
names a directory, not a file — `files_of` lists by suffix).

## Cycle 0.0.2 — what building the runner settled

### RX-120 — `check_no_syscalls` gains a second layer, because the undefined-symbol difference cannot see a syscall
**2026-09-04, from measuring the check RX-116 specified against the thing it is
supposed to catch.** `meta/roadmap/0.0/0.0.2.md` §5.

RX-116 made the no-syscall check differential: an `nregex` program object's
undefined-symbol set must **equal** an empty baseline program's. That was the
right correction to an unrunnable allowlist and it stands. **It also cannot
detect a syscall**, and cycle 0.0.2's own acceptance list asked for exactly that
— *"a deliberately introduced `sys(…)` call fails `check_no_syscalls`, by
name"*.

Two four-line programs at `950bb1d`, differing only by a `sys(39i64)` call in
`main`:

| | undefined symbols | `call i64 @npk_sys6` sites |
|---|---|---|
| baseline | 29 | 2 |
| baseline + one `sys(…)` | 29 | 3 |

**Symmetric difference of the symbol sets: empty.** `npk_sys6` is in every
object already, because the prelude's `ByteReader.seek` and `std_dup` call it,
so a program that starts making syscalls adds no symbol at all. The specified
instrument would have reported a clean run over it, and the acceptance item
would have been ticked by a check that cannot do the thing the item names.

*Therefore a second layer, on the emitted IR rather than the object.* Every
`(enclosing function, callee)` edge whose callee is declared and not defined in
the module is the floor; the baseline's edge set is the floor's own; an edge the
program has and the baseline does not was written here. If its callee reaches
the kernel or a descriptor, the run is red and the message names the function.
`BUILD.md` rule **B-2a**; `harness/irscan.py`.

*Three things the first run over the real suite forced, and each was a false
positive on all sixteen probes:*

1. **`llvm.*` is not the floor.** `llvm.sadd.with.overflow.i64` is declared,
   never defined, and is an *instruction* — it never reaches a symbol table.
2. **Compiler-generated glue is numbered and the number moves.** The baseline's
   `npk.drop.365` is probe04's `npk.drop.367`, because the counter shifts with
   program content. The trailing digits are not part of a function's identity.
3. **A DENY list is smaller and truer than a permit list.** A permit list was
   written first and failed every probe: the residue is dominated by `npk_trap`
   (the trap path every bounds check reaches), `npk_chain_push` /
   `npk_chain_reset` (the `defer` machinery), the allocator and
   `npk_string_concat` — none of them a syscall. What RX-008 forbids is
   *reaching the kernel*, which is seven symbols: `npk_sys6`, `npk_open`,
   `npk_read`, `npk_write`, `npk_ofd_close`, `npk_io_register`,
   `npk_io_unwatch`. The list can be that short only because a floor symbol the
   baseline does **not** have is caught by RX-116's layer with no list at all.

*The boundary, stated rather than implied.* The async family — `npk_exec`,
`npk_run_until`, `npk_thread_join`, `npk_windup_*` — is deliberately **not**
denied. `await` is a language feature, `probe07` exercises it on purpose, and
refusing a language probe for using the language would be this check failing the
wrong thing. Matching in this library can never be async (RX-061) and that is
held by the error budget, not by a symbol scan.

*Why this is a new decision rather than an edit to RX-116:* RX-116 is settled,
its reasoning is correct, and its rule is unchanged — the undefined-symbol sets
must still be equal. What is added is a second question the first one was never
able to ask. The pattern this repository uses for every correction (RX-002).

*Alternatives declined:* counting `@npk_sys6` call sites and comparing the total
(measured: the count is 2 against 3 at -O0 but **5 against 6** after `opt -O2`,
because inlining duplicates the floor's own sites — a number that depends on the
optimiser is a number that will drift, and it names no function); scanning the
optimised object instead (same reason, plus `opt` legitimately removes symbols);
grepping the IR for the string `sys(` (that is source, not emission, and it
would miss a syscall reached through any wrapper).

### RX-121 — both scans apply to a program whose module graph reaches `src/`, and the harness says how many that was
**2026-09-04, from the first full run: sixteen probes red, and every one of them
correctly.**

RX-116's rule says *"the undefined-symbol set of every **`nregex` program
object**"*. Read as "every program the harness builds", it fails the language
probes, and it fails them for true statements: `probe01` needs `npk_ralloc`
because it grows an allocation; `probe07` reaches the async floor because it
`await`s; every probe with a `defer` calls `npk_chain_reset`.

**`tests/probe/` is not this library.** Its own README says so — *"They are not
tests of `nregex` — no probe imports anything from `src/`, and none will ever be
able to (P-1)"*. They are tests of the **language**, kept here because this
library's design rests on their answers. Holding them to a library's
zero-syscall rule is a category error, and the cost of getting it wrong is not
noise but blunting: making the probes green would have meant permitting
`npk_trap`, the `defer` chain, the allocator and the string primitives from any
function, which is most of what any program calls.

*Therefore the scans run on programs whose transitive `use` graph reaches
`src/`.* Today that is `tests/conformance/import.npk`, and it measures exactly
equal — 29 against 29, the number `tests/conformance/TRANSCRIPT.txt` §D2
recorded. **And the harness prints, every run, how many units each scan ran on
and how many it did not**, because a check that quietly did not apply reads
exactly like one that passed. `BUILD.md` rule **B-2b**.

*A latent bug this found, worth recording because it is the same shape:* the
first `reaches_src` compared a possibly-relative path against an absolute `src/`
prefix, so it answered **no** for every program when handed a relative path —
silently, and a silent no means the scans never run. Caught by running it on
four known files and checking both spellings, not by reading it.

*Alternatives declined:* widening the permit list until the probes pass (it
blunts the check to nothing, above); moving the probes out of the harness (they
are a permanent regression suite for the language shapes this library depends on
— `tests/probe/README.md` P-5 — and not running them is worse than not scanning
them); scanning them and reporting without failing (a check that reports and
never fails is a check nobody reads, which is the compiler project's own
recurring finding).

### RX-122 — the expectation reader refuses an `expect-exit:` above 255 and a `stress:` below 1
**2026-09-04, writing the marker grammar against `npkg/expect.npk` at the pin.**

`harness/expect.py` mirrors the compiler's reader marker for marker and in its
dispatch order, because the day this harness retires into `npkg` (RX-004, O-G3)
a parity stage diffs the two runners' verdicts and a grammar that drifted makes
every row a false difference. Two expectations are nevertheless **refused at
read time**, and both are refusals of something that can never be met rather
than a different judgement of something that can.

**`expect-exit:` above 255.** An exit status is one byte. A process that exits
321 reports **65**, silently; the compiler's reader accepts the 321 and then
compares it against a number that can only be 0–255, so the test can never pass
and nothing says why. Swept 2026-09-04: no `expect-exit` header in this
repository exceeds 255, so this refuses no test that exists — it refuses the one
somebody writes next. Negative values keep `npkg`'s meaning (`run_binary`
reports a killed process as `0 - signal`, so `expect-exit: -11` is SIGSEGV) and
below −64 there is no such signal.

**`stress:` below 1**, and this one is smaller than it first looked. The reason
first written here was that `npkg` loops `0...stress` and would therefore run
the program **no times and report green**. That is **false**, and it was
corrected before it was committed: `run_binary` opens
`int64:runs = stress; if (runs < 1i64) { runs = 1i64; }` — read in the source
rather than inferred from the loop. So it is not a hole there. What is left is
still worth refusing: a `stress: 0` is an expectation the runner silently
rewrites rather than honours.

*Recorded as a decision rather than left in a comment* because B-5 says the
grammar is the compiler's marker for marker, and a divergence from a rule that
says "no divergence" has to be visible in the same place the rule is. `BUILD.md`
rule **B-5a**.

*Alternatives declined:* accepting `expect-exit: 321` and reporting the mod-256
value the run would have to produce (that is guessing what the author meant, and
the two candidate meanings — 321 and 65 — are both plausible); refusing the
value at comparison time rather than read time (the message then arrives after a
build, attached to a run, and reads like the program did something wrong).

---

*Appended 2026-09-04 by stream 1, working `meta/roadmap/0.0/0.0.3.md`, against
pinned toolchain `94874ce` under LLVM 20.1.2. This is the first subcycle after
the re-pin from `950bb1d`, and three of the four decisions below exist because
the compiler moved under measurements this repository had already recorded.*

### RX-123 — the leak gate's correction reached the prose and stopped at the checklists
> **SUPERSEDED IN PART by RX-155 (2026-09-25)** — its citation of TYPE-046 as
> why `Inst` is POD. `Inst` is POD because C-1 declares it so. The decision stands.

**2026-09-04.** RX-110 corrected six sites that stated *"the suite's programs
exit 0, so a missing `free` on any path is a trap rather than a pass"*, which is
false of every managed body. **It missed two, and both are ACCEPTANCE CHECKLIST
lines** — the places where the claim stops being description and becomes a
condition somebody ticks:

- `meta/roadmap/0.0/README.md`, cycle 0.0.4's checklist: *"the leak tests exit
  0, so a missing `vec_free` is a trap and not a pass"*. It names **`vec_free`**,
  and so asserts the gate for precisely the managed case D-151 cannot see, in
  the cycle that builds `Vec<T>` and `Bytes`.
- `meta/roadmap/0.0/0.0.4.md` §6, the same line without the function name.

Both now carry the correct formulation, which is this repository's own from
`SAFETY.md` §8b (S-22): **D-151 counts `wild` blocks, D-188 counts live drivers,
and neither sees a managed body**; where the obligation is managed the gate is a
**memory cap**, not an exit code.

**Why RX-110's sweep missed them, and this is the durable half.** RX-110 records
that its site list was *"produced by `git grep -n 'D-151'` and not from recall"*
— the right instinct, honestly applied, and it was still short by two, **because
neither checklist line cites D-151**. A generating command is only as wide as
its pattern, and a claim restated without its citation is invisible to a search
for the citation. The sweep that found these two was `git grep -in` for the
CLAIM's own words — *"trap and not a pass"*, *"trap rather than a pass"* — and
then a third pass on the bare word `leak`, which is what turned up the two
further sites judged below.

*Two sites checked and deliberately NOT changed*, because a correction applied
where it is not needed is the next false document:

- `meta/roadmap/0.0/README.md`, cycle 0.0.0's probe-14 line — *"a `Vec<Inst>` at
  `NREGEX_PROGRAM_INSTRUCTIONS`, built and walked, exiting 0 so a leak is a
  trap"*. `Inst` is **POD** (TYPE-046), so for that probe the `wild` block **is**
  the whole obligation and `exit 0` covers it exactly — `SAFETY.md` §8b says so
  in as many words. The line names its concrete type, which is what makes it
  narrow rather than sloppy.
- `meta/DECISIONS.md` RX-110 and `meta/specs/SAFETY.md` §8b both **quote** the
  false sentence in order to forbid it. Rewriting a quotation of an error would
  destroy the record of the error.

*Alternatives declined:* fixing the two lines silently, without a number (the
first correction was numbered, and an unnumbered follow-up would make the second
miss invisible to exactly the search that would look for it); restating the
narrow rule inline at both sites rather than citing S-22 (four copies of a rule
are four things to keep in step — `SAFETY.md` §8b is the one home).

### RX-124 — the `parse` stage cannot use the compiler's tool either, for the reason B-4a already gave about `accept`

**2026-09-04, and it is a residue of exactly RX-123's shape.** `BUILD.md` §3's
stage table has six rows. Rule **B-4a (RX-117)** struck the `accept` row because
*"`accept` is defined as 'accepted by `tools/check` in silence', and `tools/check`
is a **compiler-repository** tool `nregex` does not have and, under RX-007, may
not import"*. **The `parse` row, two rows above it, says "accepted by
`tools/parse_check`" — the same tree, the same prohibition — and was left
standing.**

*Read at the pin rather than assumed.* `tools/parse_check.npk` at `94874ce`
opens with `mod:parse_check;` and then **nineteen** `use "../src/frontend/…"`
imports — the lexer, the parser, the AST, the diagnostics writer. Having it
means compiling the compiler's frontend: RX-007 forbids the dependency and W-18
forbids building the compiler from here. `npkc` has no parse-only flag either;
its usage line, read at the pin, is
`npkc <root.npk> [-o out.ll] [--obligations DIR] [--elide …] [--extra-picky=…]`.

**The decision.** The `parse` stage is `npkc` itself, and it is **strictly
stronger than parsing**: the whole frontend runs and IR is emitted. A file
carrying no `expect-error:` must be accepted at exit 0 **with an empty
diagnostic channel** — a warning on a clean exit is still a finding (B-6), and
exit 0 is the one place nobody looks for one. A file carrying `expect-error:` is
held to its own codes by the same equality rule (B-7), because the tree contains
deliberate refusals and exempting a directory is where a real refusal hides.
`accept` is now refused **by name** in the runner rather than reported as
unimplemented, because B-4a struck it — it is a manifest error, not a pending
feature.

**Every file is judged AS A ROOT**, including one that another file imports:
"each file once" means once *as itself*, and a file that only ever compiles
inside somebody else's module graph has never been checked on its own.

*And the stage earns its place rather than duplicating another.* `src/lib.npk`
`pub use`s exactly one name, from `src/api/api.npk`, so **six of this library's
eight `src/` files — `core`, `compile`, `engine`, `hir`, `syntax`, `unicode` —
are reached by no other suite in the manifest.** They compiled at exit 0 once,
at cycle 0.0.1, and nothing re-checked them until this entry existed.

*Alternatives declined:* vendoring `tools/parse_check.npk` (RX-007, and it would
be nineteen files of the compiler's frontend, not one); declaring the stage and
skipping it (a stage that silently does nothing is the green-while-checking-
nothing failure the manifest's own header exists to prevent); calling the stage
something other than `parse` (the stage vocabulary is the compiler's so the move
to `npkg` is a change of runner and not of suite — the name stays and the
divergence is written down here and in the runner).

### RX-125 — O-N10 is DISCHARGED on this repository's own measurement, and the probe that announced it was built to
> **SUPERSEDED IN PART by RX-155 (2026-09-25)** — its statement that "TYPE-046
> forbids an owning field in a value stored in an array", given as H-2's primary
> reason. It forbids a COPY of an owner; H-2 stands on its own words — a POD
> arena is copyable, comparable and a committable fixture. The decision stands.

**2026-09-04, at the re-pin from `950bb1d` to `94874ce`.** Workbench registry
**O-N10** had two halves and both are fixed:

| | at `950bb1d` | at `94874ce`, measured here |
|---|---|---|
| `#[derive(Eq)]` on a payload enum | **REFUSED**, `NITPICK-TYPE-034` at `<derived-1>:2:82` | **accepted, and correct** |
| `#[derive(Ord)]`'s `cmp` on one | **accepted and WRONG** — payload ignored, `Repeat(2,5).cmp(Repeat(9,9))` is `Equal` | **reads the payload, lexicographically** |

**How it was found is the part worth keeping.** Nobody went looking. The first
full harness run of this subcycle came back with two reds, and the second of
them was `probe02c` exiting 20 — the exit its own header had reserved five weeks
earlier for this exact event: *"If this line ever exits 20, O-N10 HAS LANDED …
Do not 'fix' the probe — read the header and delete the nesting."* **A probe
written to assert what the compiler actually does, rather than what it ought to
do, reported the fix on the day it arrived.** A probe asserting the correct
answer would have been green through the defective period and green afterwards
and would have said nothing on either day. This is the strongest argument in
this repository for the convention, and it is now paid for.

The other red was `probe02b`, whose `// expect-error: NITPICK-TYPE-034` no
longer held. It was caught by rule **B-7's** code-set equality reporting
*"expected NITPICK-TYPE-034, but it compiled cleanly (exit 0)"* — a stale
expectation surfacing as a failing test rather than a quietly passing one, which
is what B-7 is for.

*What was measured, before anything was written.* Six `eq` properties and seven
`cmp` properties, at one payload field and at two. **Two of them are this
repository's own and no test in `nitpick-time` can make them**: its enum has one
payload field per variant, so an implementation that read only the FIRST field
would have passed everything there. `Repeat(2,5)` is now correctly distinguished
from `Repeat(2,9)` and from `Repeat(9,5)`, and `Repeat(2,5) < Repeat(2,9)` — the
second field breaks the tie. `tests/probe/probe02b_derive_eq.npk` and
`tests/probe/probe02c_derive_ord.npk` carry all thirteen.

**A caller-visible fact that came with it: `.eq()` returns `Result<bool>` and
`.cmp()` returns `Result<Ordering>`.** `if (a.eq(b))` is `NITPICK-TYPE-007` —
*"this must be a `bool`, and is `Result<bool>`; there is no truthiness in
Nitpick"*. So the hand-written nesting in `probe02_payload_enum.npk`'s `hir_eq`
is **not** simply deleted in favour of a derive: the derive threads an error
channel, and `SAFETY.md` §4's budget is charged by channels. Whether `Hir`
comparison takes the derive is a cycle 0.2 decision with that cost on the table,
not a consequence of this one.

*One expired reason, marked rather than deleted.* `probe02b`'s old header argued
that `HIR.md` H-2's parallel-field node — a plain enum beside `int32` fields — is
*"the better shape under today's compiler"* **because** the derive was refused.
That supporting reason is now dead. **H-2 itself stands**, on its primary reason,
which never involved O-N10: TYPE-046 forbids an owning field in a value stored in
an array, and a flat POD arena is what makes the whole tree a committable
fixture. A later cycle must not re-derive H-2 from the dead premise, and must not
reopen it on the strength of the premise dying.

*The two files were RENAMED, and cycle 0.0.0's record was not rewritten.*
`probe02b_derive_eq_refused.npk` is not refused and `probe02c_derive_ord_tag_only.npk`
is not tag-only, so both names had become claims that are false; keeping them
would be the stale document this repository spends its effort avoiding. The
redirect table is `meta/roadmap/0.0/0.0.3.md` §6, in the pattern **RX-114** set
and **0.0.2** reused: a verified execution record and its transcript are
artifacts of a pin and are never edited to agree with a later one.

### RX-126 — D-247 does not reach this library's `Vec<T>`, so the three re-run probes establish something narrower than the re-pin note supposed

**2026-09-04.** The dispatch that opened this subcycle owed three measurements at
the re-pin — `probe03`'s `free_owning`, `probe04:89`'s `pass self.count` over a
`Vec<T>` **by value** (the compiler's DEF-8 shape exactly), and `probe08:121`'s
nested-container sibling — on the stated ground that *"`Vec<T>` did not own until
D-247, which landed in the same commit as DEF-8's fix"*.

**All three re-ran clean: `npkc` 0, `llc` 0, `ld.lld` 0, and the binary exited 0
at −O0 and again through `opt -O2`.** No `WildLeak` trap (exit 96), no
double-free trap.

**But the premise is false, and a green measurement under a false premise is
worth stating precisely rather than banking.** D-247 makes the **compiler-known
`List<T>`** owning, and its recognition is keyed — read in the pinned source,
`src/frontend/type_layout.npk`'s `decl_is_list` — on **all** of: a file in the
program whose basename is `list`; the declaration's home scope being that
module's; the struct being named **`List`**; and its fields being exactly
`items` (a pointer), `count`, `cap`, in that order, and no others. The predicate's
own comment settles it: *"A same-named struct anywhere else (a test's own `List`)
is an ordinary struct."*

**This repository has no file named `list.npk` and its container is named
`Vec`.** So `Vec<T>` is an ordinary struct holding a `wild T->` block, exactly as
it was at `950bb1d`, and **D-247 changed nothing about it**. It follows that:

- The three probes are **not** evidence that the DEF-8 fix is correct for this
  library's shape — they are evidence that the shape is **outside DEF-8's scope
  entirely**, because DEF-8 is about the drop flag of an **owning** local and
  `Vec<T>` does not drop.
- S-26 (a `move` or `pass` out of a field or element leaves the canonical vacant
  value) likewise does not change `free_owning`'s meaning here.
- Nothing about the `Vec<T>` design needs revisiting at cycle 0.0.4, and the
  obligations `SAFETY.md` §8b and `0.0.4.md` P-20 place on it are unchanged.
- **The 125 MiB managed-body gap is unchanged too.** D-247 would have closed it
  for a `List<string>`; it does not close it for a `Vec<OwningGroup>`, so
  RX-110's rule and RX-123's correction both stand at full strength.

*One inaccuracy in the compiler's own note, catalogued and not raised.* DEF-8's
entry says *"Blocks nothing of the workbench's: their recipes pass values, not
fields, out of owning locals."* `probe04_inherent_generic_impl.npk`'s `len2` is
`func:len2 = int64(Vec<T>:self) never fails { pass self.count; }` — a `pass` of a
**field**, out of a by-value local, which is the shape the sentence says the
workbench does not write. It is harmless **because** `Vec<T>` does not drop, not
because the recipe is absent. Registered as **O-N16** so the compiler's fix batch
can correct the note rather than carry a reason that does not hold.

*Alternatives declined:* recording the three greens as "DEF-8 verified here"
(they are not — the pin is silent about a defect whose precondition this library
never meets, and calling that verification is exactly the unfalsifiable green
this repository has now found four of); renaming `Vec<T>` to `List` to acquire
D-247's ownership (it would import a compiler-known type's drop semantics into a
container this library has deliberately specified itself, RX-006, and it would do
so by matching a filename — a coupling no reader would predict).

---

*Appended 2026-09-06 by stream 1, working `meta/roadmap/0.0/0.0.4.md`, against
pinned toolchain `3d15ac9` under LLVM 20.1.2. This is the second re-pin this
repository has absorbed, and — like the first — most of what follows exists
because the compiler moved under a measurement already recorded here.*

### RX-127 — `limit<Rules>` is live, enforced and import-scoped, so this library declines it: a limited binding charges every consumer a second `failsafe` arm
> **SUPERSEDED IN PART by RX-153 (2026-09-25)** — its decision *"No
> `limit<Rules>` appears anywhere in `src/`"*, for the containers' four counts
> only, which carry the prelude's `ListLen` since cycle 0.0.4c. Its reasons, and
> the rule for every other binding (`SAFETY.md` S-24), stand.

**2026-09-06, at the re-pin from `94874ce` to `3d15ac9`.** `probe13b` came back
red with *"expected `NITPICK-RUNG-001`, got `NITPICK-REACH-002`"*. It is not a
regression: `limit<Rules>` went live in the compiler's 1.5.2, the rung refusal
retired, and the probe now compiles **past** the construct and is refused at its
`failsafe` instead. The probe asked a two-way question — *refused, or lowered to
nothing?* — and the answer is a third thing it did not offer: **enforced.**

**What was measured here, on the pinned `npkc`, each against a control that
differs only in the clause.** The compiler session supplied three of these from
its own build; they are re-run here rather than banked, because a fact about the
toolchain we test against is only ours once we have taken it on that toolchain.

| # | Program | Result |
|---|---|---|
| 1 | `limit<r_pos>` parameter, in-range call | `npkc` 0, `llc` 0, `ld` 0, **run 0** at −O0 and under `opt -O2` |
| 2 | the same, argument violating the rule | **run 97** — this file's `LimitViolated` arm — at −O0 **and** under `opt -O2` |
| 3 | `never fails` **+** `limit`, in-range | `npkc` 0, **run 0** |
| 4 | `?\| 55i32` fallback over a violating call | **run 97**. The fallback never fires |
| 5 | `pub` limited callee imported by a root whose `failsafe` omits the arm | **`NITPICK-REACH-002`**; the same root over an unlimited callee, **exit 0** |
| 6 | **module-private** limited callee behind a `pub` wrapper, same root | **`NITPICK-REACH-002`**; unlimited control, **exit 0** |

**The decision. No `limit<Rules>` appears anywhere in `src/`, public or
private.** Rows 5 and 6 are the reason and row 6 is the one that settles it:
visibility does not contain the charge, because reachability follows the call
graph. `SAFETY.md` S-8 (RX-060) makes the strongest promise in this repository —
*importing `nregex` costs your program's `failsafe` exactly one arm* — and a
single limited binding anywhere in the reachable graph makes it two. Row 4 says
the second arm buys the caller nothing it could not have without it: the
violation takes the trap route (the compiler's D-241, its D-220/D-221 before
it), so no `?|`, `?!` or `is_err` at the call site can observe or recover it.
`SAFETY.md` gains **S-24** and §4.2; `VERIFICATION.md` gains **P-1a**.

*The extent was measured before the decision was written, not after.* Rows 5 and
6 are two different questions and only the first is the obvious one. Had the
sweep stopped at row 5 the rule would have read *"no `limit` on a `pub`
function"*, which is short by every private helper in `src/core/` — and it would
have been discharged by a green suite, because a private limited helper compiles
perfectly and only the **consumer** is refused. `PLAYBOOK.md`'s rule that an
extent is a separate measurement from an existence, applied to a rule rather
than to a defect.

*One inference drawn and RETRACTED here, because the retraction is the more
useful half.* A first reading of row 3 was that `limit` puts a `Result` at every
call site — the call to a `never fails` limited callee is `Result<int32>` and
needs `raw`, which looked like the clause's doing and would have killed
`SAFETY.md` S-4 (RX-061: *`regex_find` returns `Match?`, **not**
`Result<Match?>`*) on its own. **The control refutes it:** an unlimited
`never fails` callee's call site is `Result<int32>` too, and `raw` unwraps both
identically. That is D-163's own shape and has nothing to do with `limit`. The
control was run because the conclusion was large, and it is in
`probe13b_limit_enforced.npk` as `f_plain` so that the next reader meets the
refutation beside the temptation.

**What this does NOT decide.** `requires` and `ensures` — the clauses
`VERIFICATION.md` P-2 actually writes, and the ones every accessor in cycle
0.0.4 carries as a comment — still refuse `NITPICK-RUNG-001` at this pin
(`probe13c`, `probe13d`, both green). **Whether they charge a consumer an arm
cannot be measured here at all**, because the pin is silent about unlanded work
by construction; the compiler's own `VERIFICATION_REFERENCE.md` says a violated
precondition *"returns a `Result` error"* while D-241 says a contract violation
takes the trap route "never a `Result`", and those two cannot both be the whole
story. **The question is therefore left open and dated rather than guessed**,
and P-1a requires it to be re-measured before a single clause is uncommented.

*And it corrects a claim this repository shipped.* `probe13b`'s old header, and
three sites in cycle 0.0.0's execution record, said `never fails` and `limit`
are **mutually exclusive** — a *permanent* rule, `NITPICK-TYPE-037`, "a bound
rule needs an error channel". Row 3 falsifies it, and the compiler's **D-241**
(2026-09-03, its 1.5.1 step 5) is why: D-163 rule 2's contract row retired,
because a `never fails` body already admits the trap channel. The claim was
load-bearing — it was written down as deciding *which functions in `src/core/`
could carry an obligation at 1.5*, and `VERIFICATION.md` §4's own P-2 example is
`requires … never fails`, the very shape it forbade. **The record is not
edited**: those three sites are a verified artifact of pin `950bb1d`, corrected
by the redirect table in `meta/roadmap/0.0/0.0.4.md` §7 under W-28, in the
pattern RX-114 set and RX-125 reused.

*Alternatives declined:* adopting `limit` on `src/core/`'s accessors and
amending S-8 to "one arm, plus `LimitViolated`" (S-8 is the library's headline
API property and the second arm is a compiler-enforced source break in every
consumer, which RX-005 calls a major version — paying it for a bound this
library already checks by hand in `vec_get`/`vec_set` is a bad trade); using
`limit` only on module-private helpers (row 6 measured, and it does not work);
keeping `probe13b` red and expecting `NITPICK-REACH-002` in it (that makes a
positive result look like a refusal, which is exactly the false claim in a
filename RX-125 removed).

### RX-128 — `VERIFICATION.md` §3 discharged the bounds obligation for free, and it is the obligation cycle 0.0.4 exists to build

**2026-09-06.** `meta/specs/VERIFICATION.md` §3, *"What the language discharges
for free"*, opened with:

> **Every index traps** (D-070), so `nregex` never reads out of bounds. The
> question is only whether a *reachable* index is out of bounds — §4.

**RX-111 is the correction to exactly that sentence and it did not reach this
file.** RX-111 rewrote `SAFETY.md` §1's row and added §5.3 (S-23): D-070's check
attaches to types that carry a length, a `wild T->` block is a bare pointer,
`Vec<T>.items` is one, and an out-of-range index **reads and returns a heap
word**. Measured as a pair at the time — `probe08c` exit 94, `probe08b` exit 0,
same offset and same program shape.

**Why the miss is worse here than at any of the other sites.** §3's whole
function is to list what the library therefore does **not** have to check. So
the specification that governs cycle 0.0.4 discharged, for free, the single
obligation cycle 0.0.4 exists to discharge — and the sentence immediately after
it narrows the residue to *"whether a reachable index is out of bounds"*, which
is a solver's question, when the real residue is *every index in the library*.

*How it was found, and why the ordinary sweep would not have.* It surfaced while
re-reading §2 for an unrelated reason (`limit`'s rung status, RX-127). The sweep
that then confirmed it was run three ways over 62 tracked `.md` files —
`index.*trap|trap.*index`, `bounds.checked|out of bounds|never reads out`, and
`D-070` — and returned **19 candidate lines, of which reading confirmed exactly
one false site**, this one. Every other line is either correct (`SAFETY.md` §1
and §5.3, `CLAUDE.md`, `CONTRIBUTING.md`), a quotation of the error in order to
forbid it (RX-111 itself), or a closed execution record. **RX-111's own entry
names only `SAFETY.md` as what changes** — it never states a site list at all,
so there was nothing for a later reader to check against, and this is the
`PLAYBOOK.md` rule that a correction states its denominator arriving in the one
place it had not been applied: a decision that corrects a claim should say how
many sites it swept, not merely which one it fixed.

**The correction.** §3's row now names the types D-070 actually covers, says
plainly that this library's containers are not among them, and points at
`SAFETY.md` §5.3. The residue §4 states is enlarged to what it always was.

*Alternatives declined:* deleting the row (it is true of slices and fixed
arrays, and this library does index both — a `uint8[]` haystack is the hottest
one in the engine, and losing that discharge would put a redundant obligation on
every haystack read); leaving it and relying on `SAFETY.md` §5.3 to be read
first (a reader of `VERIFICATION.md` §4 is deciding what to prove, and §3 is the
list they are entitled to skip §4 for).

### RX-129 — the container API is FREE FUNCTIONS, and probe 04 measured both forms so this is a choice rather than a default

**2026-09-06.** Cycle 0.0.0's verdict table left this open in as many words:
*"the container API is a **choice**; cycle 0.0.4 settles it with both
measured."* `probe04_inherent_generic_impl.npk` compiles and runs BOTH — D-171's
inherent family impl `impl:<T>:Vec<T>` called as `v.push2(x)`, at two
instantiations, and the free-function form beside it — so neither is being
chosen because the other does not work.

**The decision: free functions**, `vec_push(@v, x)`, following the compiler's
own `list.npk` shape (its D-209).

Three reasons, in order of weight:

1. **`SAFETY.md` S-23 makes the accessor pair load-bearing, and a free function
   is what the tree check can see.** The rule is that no `.items[` appears
   outside `src/core/vec.npk`. That is a check over one file either way — but
   the *reason* it holds is that every read goes through `vec_get`, and a
   grep for a free function's name finds every call site in one pass, where a
   method call is `.get(` on any receiver.
2. **`VERIFICATION.md` P-2 writes the obligations on free functions.** Its
   worked example is `func:prog_inst = Inst(Program->:p, int32:pc) requires …`,
   and P-23 requires every accessor's obligation to be written NOW in the
   syntax it will take. Writing them on one shape and the code on another would
   make the switch at 1.5 a rewrite rather than a comment deletion.
3. **There are no static methods (D-185)**, so construction is a bare function
   whichever form the rest takes. A library that is half free functions and half
   methods reads worse than either.

*Alternatives declined:* the inherent impl form (it reads better at the call
site — `v.push(x)` — and that is the whole of its case; against it are the
three above, and the mutating receiver must be `Vec<T>->` rather than
`Vec<T>`, which a by-value slip turns into a silent no-op rather than an
error, as probe04's own header notes); a mix, methods for reading and free
functions for mutating (two vocabularies for one type).

### RX-130 — an out-of-range accessor TRAPS, and the trap is the language's own `OutOfBounds`
> **SUPERSEDED IN PART by RX-143 (2026-09-06)** — its sentence *"the helper is
> `vec_oob`, it never returns"*, which was false at `i == 0`. The decision — a
> violation traps `OutOfBounds`, the language's own trap — stands. *(Marker added
> 2026-09-25 at cycle 0.0.4b, when `check_refs` began requiring one; the third
> audit's N-17.)*

**2026-09-06.** `SAFETY.md` S-23 says `vec_get`/`vec_set` "check against
`count`" and does not say what a violation does. Three answers were available
and only one survives the specifications already in force.

**The decision: it traps `OutOfBounds`.** Spelled by indexing a one-element
fixed array — `int64[1]`, a type that DOES carry a length — out of range, so it
is the language's own trap and not a code this library invented. The helper is
`vec_oob`, it never returns, and the guard array is constructed inside the
failing branch so the fast path pays a compare and a branch.

**Why not a `Result`.** `SAFETY.md` S-4 (RX-061): *matching cannot fail*, and
`regex_find` returns `Match?` and **not** `Result<Match?>`. An accessor with an
error channel puts one on the search path — the hottest path in the library —
and every engine would thread it to no purpose, since a violated bound is a bug
in this library rather than a condition a caller can handle.

**Why not "leave it unchecked and rely on the contract".** That is the state
RX-111 found and called the worst outcome available: an unchecked index is *a
WRONG ANSWER, not a crash*, and it inverts the failure mode `SAFETY.md` §1
advertises.

**And it is where the language is going, which is the strongest reason.** When
the compiler's 1.5.3 lands `requires`, a contract violation takes the TRAP route
(its D-241, and D-220/D-221 before it) — measured for `limit` at this pin in
RX-127, where an explicit `?| 55i32` fallback did not fire and the program
exited through its `LimitViolated` arm. So writing the trap now means behaviour
does not change on the day the clause is uncommented, which is exactly what
P-23 promises when it says the switch is deleting a comment marker.

*Measured, four files, one case each because a trapping call cannot be followed
by an assertion in the same program:* `vec_get` at `i == count`, `vec_get` at a
negative index, `vec_set` at `i == count`, `vec_pop` on an empty `Vec` — all
four exit **94**, and each names a different code on the path where the check
was removed, so "the check fired" and "the check is gone" can never be confused.

*Alternatives declined:* a `Result<T>` accessor (above); an `error:` identity of
this library's own for it (RX-060 — a second identity is a major version, and
this one would be raised only by a bug); a debug-only check (the failure is
silent, which is precisely the case a build flag must not be able to turn off).

### RX-131 — the prelude trim turned B-2's first layer into an emptiness claim about nothing, so the difference becomes a REVIEWED RESIDUE LIST

**2026-09-06, forced by re-recording the floor at `3d15ac9`.** RX-116 made
`check_no_syscalls` differential: a program object's undefined-symbol set must
**equal** the empty baseline's. That was the right correction to an unrunnable
allowlist and its reasoning was sound — *"a program containing no library code
at all has 29 undefined symbols, so an absolute allowlist fails on this
file."*

**The compiler's D-262 removed the premise.** A prelude item is now emitted only
if referenced, so:

| | at `950bb1d` | at `3d15ac9` |
|---|---|---|
| the floor's undefined symbols | **29** | **2** — `npk_dalloc`, `npk_ofd_close` |
| the floor's call edges | **237** | **2**, both from the drop glue |
| a four-line program making one `wild` block | equal to the floor | **+3** — `npk_alloc`, `npk_chain_reset`, `npk_trap` |

So equality now fails on the first program that allocates, which is every
program this cycle adds. **A check that fails on correct code is a check that
gets switched off**, and the honest reading is that the thing being asserted
changed meaning: "equal to the floor" used to mean *added nothing*, and now
means *does nothing*.

**The decision.** The `got - base` direction is diffed against
`harness/baseline/RESIDUE.txt` — one line per symbol, `name<TAB>reason`,
committed and reviewed like a golden, and refused at read time if a line has no
reason. **This is the absolute allowlist RX-116 wanted and could not have**: an
object's undefined set is now exactly what the program uses, so the list is a
short, readable statement of what `nregex` needs from the runtime, which is what
RX-008 is actually about. Six entries today.

**Three failures, deliberately different.** A symbol not on the list is a review
event, named as one. A symbol on RX-120's **kernel deny list** is a finding
whatever the list says — checked independently, so no edit to `RESIDUE.txt` can
admit a syscall. And the baseline direction is unchanged: a floor symbol the
object lacks means the committed baseline is stale.

**BOTH DIRECTIONS, and the second one earned its place immediately.** An entry
no scanned program references fails the run. Two of the eight entries first
written here — `npk_chain_push` and `npk_int_to_string` — were added *by
reasoning* ("the `defer` pair travels together"; "interpolation must call the
integer formatter") and the check refused both, because no program references
them. That is `PLAYBOOK.md`'s named-exemption shape caught at the moment of
writing rather than three cycles later, and it happened to the session that had
just written the mechanism.

**AND THE FIRST LAYER CAN NOW SEE A SYSCALL, WHICH RX-120 MEASURED THAT IT
COULD NOT.** RX-120's finding was that a `sys(39i64)` program has *the same 29
undefined symbols* as the floor, because `npk_sys6` was already the prelude's.
Re-measured at this pin: the floor has two symbols and no `npk_sys6`, the
syscaller has three, and the symmetric difference is exactly `{npk_sys6}`.
**RX-120 is NOT retired by that** — the IR call-edge scan is strictly stronger
(it names the calling function, and it survives a prelude that starts emitting
`npk_sys6` again), and the decision stands. What has expired is one supporting
clause inside it: *"the deny list can be that short only because a floor symbol
the baseline does not have is caught by RX-116's layer with no list at all."*
That clause is corrected here rather than in RX-120, whose text is settled.

**The self-check's case 9 had to move, and it had PREDICTED that it would.**
That case proves this layer can name a symbol, and it leant on `npk_ralloc` —
whose fixture header said, in 2026-09-04: *"at 0.0.4 the right response will be
to add `npk_ralloc` to the permitted delta DELIBERATELY, in a decision, rather
than to discover it as a mysterious red."* `Vec<T>`'s doubling calls `ralloc`,
`npk_ralloc` is now a reviewed line, **and the old fixture would therefore have
gone GREEN — a self-check case whose red is unreachable.** It now uses
`mono_now`, chosen to be *unaddable* rather than merely unused: D-076 makes
determinism this ecosystem's property, so `npk_mono_now` can never legitimately
join the list and the case cannot decay the same way twice. The `ralloc` lines
are kept as a control that must NOT be reported.

*Alternatives declined:* widening `baseline.npk` until the floor covers what the
library uses (the baseline's own README forbids it — *"the moment it imports
anything, it stops being the floor and starts being a test"* — and a floor built
to swallow the library's symbols is unfalsifiable by construction); reporting
the residue without failing (printing is what green-because-it-never-ran looks
like, `PLAYBOOK.md` §6); per-program residue lists rather than the union (it
would catch more, and it would also make every new test file a two-file change,
which is how a check acquires a `--skip` flag).

### RX-132 — `src/` contains no `/` and no `%`, because a division charges every consumer two `failsafe` arms

**2026-09-06, found by a refusal nobody was looking for.** `bytes_put_uint` was
written the obvious way — `x % 10u64` for the digit, `x / 10u64` for the rest —
and compiled cleanly. Two OTHER files then refused to compile:
`tests/unit/bytes_oob_get_at_len.npk` and `tests/unit/bytes_oob_set_negative.npk`
**call only `bytes_init`, `bytes_push` and the accessor pair**, and were refused
`NITPICK-REACH-002` for both `DivByZero` and `DivOverflow`.

**Reachability is import-scoped.** A division anywhere in a module is a division
every importer pays for, whether or not it calls the function containing it. So
the cost of that `/` was not on `bytes_put_uint`'s callers; it was on **every
program that would ever import `nregex`**, and it is two arms against
`SAFETY.md` S-8's promise of exactly one.

| | consumer's bill |
|---|---|
| `bytes.npk` with `x / 10u64` | `NITPICK-REACH-002` × 2 — `DivByZero`, `DivOverflow` |
| the same file, digits by subtraction | compiles, ordinary arm set, both programs trap 94 as intended |

**Neither arm could ever have fired.** The divisor was the literal `10u64` and
the operands are unsigned: there is no zero and no `MIN / -1`. That is what
makes this worth a rule rather than a shrug — **a budget is charged by what CAN
reach `failsafe`**, the reachability walk does not reason about values, and
`(*)` discharges nothing. A library cannot buy the arm back by being careful.

**The decision.** No `/` and no `%` under `src/`. `SAFETY.md` gains **S-25**, and
`check_no_division` enforces it over 13 files on every full run — because
`PLAYBOOK.md`'s standing lesson is to prefer a check that fails to a rule that
asks for care, and this rule is exactly the kind a later cycle would break
without noticing, since the code that breaks it compiles perfectly and the
failure appears in a different file.

*The substitutes are exact, not approximations.* On a power of two a shift and a
mask are the same operation the emitter would have produced: `byteset.npk`'s
`b / 64` and `b % 64` are now `b >> 6` and `b & 63`. Where the divisor is not a
power of two, subtraction against a descending power of ten — at most nine
subtractions per digit, twenty digits, against an allocation the function exists
to avoid. The rewrite is also SHORTER, because emitting most-significant-first
removes the reversal staging array.

*Two things the rewrite ran into, both worth keeping.* The power table cannot be
spelled: 10^19 is `NITPICK-LEX-004`, *"outside the 64-bit literal envelope
(D-148); a type's outermost values are constructed arithmetically, not
spelled"* — the envelope is **signed** 64-bit, so the ceiling is about 9.22e18
even for a `u64` that holds 1.8e19 comfortably. That is the same rule that stops
`int64`'s minimum being written down, met at the other end of the range. And the
table's length is read as `p10.len` rather than written as `20`, because a fixed
array carries its length in its type — which is also why indexing it traps.

*A defect in `check_constants_named`, found by this change and fixed with it.*
Its pattern was `[<>]=?\s*(\d+)`, and on `x >> 6i64` the **second** `>` matched,
so it reported the shift width as an unnamed bound — three times in
`byteset.npk`, on the very lines this decision created. A shift is not a
comparison; the pattern now excludes `<<` and `>>` from both ends. The check was
right about its rule and wrong about its mechanism, which is the shape this
repository keeps finding.

*Scope, stated because a wider rule would be wrong.* `tests/` may divide. A test
declares its own arms and nobody imports a test, so the consumer cost this
decision is about does not exist there — and `sparseset_unit.npk`'s PRNG avoids
division anyway, to keep one habit rather than two.

*Alternatives declined:* declaring `DivByZero` and `DivOverflow` in the
consumer's expected arm set and amending S-8 to "one arm plus two" (S-8 is this
library's headline API property, and paying it for a division that cannot fail
is the worst possible trade); moving `bytes_put_uint` to its own module so only
its importers pay (it would work, and it splits `Bytes` in half for the sake of
one function — and `api` will import both, so the consumer pays anyway);
asking the compiler to prove the divisor non-zero and drop the arm (a real
request, and one this library should not block on: the rewrite costs nothing and
the arms are gone today).

---

### RX-133 — the compiler's emission is INVOCATION-independent and TREE-POSITION-dependent, so CI records its digest and the cross-machine comparison is legitimate

**2026-09-06, cycle 0.0.5.** The compiler side asked this workbench for one
measurement it cannot make itself: its own emission, `npkc.ll`, digested on a
second machine (its `OPEN_DECISIONS` S-42, recommendation (c);
`BUILD_REFERENCE.md` §5). Their claim is that the linked `npkc` **binary** may
differ across machines — D-204 pins LLVM by *version*, and a version is not a
binary — while the **emission** is the same text anywhere, so a difference there
would be a compiler defect.

**This decision is that CI prints it, and asserts nothing.** A workflow that
failed on a digest whose expected value it has never been told would be
asserting a guess. The step prints size and sha256 for every artefact the ladder
leaves, so the first one that differs names the stage.

**The reason it needed a decision rather than a line of YAML** is that
`PLAYBOOK.md` carries a rule which, read quickly, says the comparison cannot
work: *"an emitted `.ll`'s byte count is path-dependent; the object's is not.
Quote the object."* If an emission's bytes depend on where it was built, then
two machines must disagree and the measurement is worthless before it is taken.

**Measured here rather than reasoned about, with the pinned `npkc` and four
controls over one source file.**

| | working directory | argument | recorded site path | sha256 | bytes |
|---|---|---|---|---|---|
| A | repository root | absolute | `.internal/pathdep/aa/pd.npk` | `ee0dc87d…` | 52 467 |
| C | `…/aa` | **relative**, `pd.npk` | `.internal/pathdep/aa/pd.npk` | `ee0dc87d…` | 52 467 |
| E | `/tmp` | absolute, **not under cwd** | `.internal/pathdep/aa/pd.npk` | `ee0dc87d…` | 52 467 |
| B | repository root | the same file copied to `…/bbbbbbbbbb/` | `.internal/pathdep/bbbbbbbbbb/pd.npk` | `107da499…` | 52 491 |

**A, C and E are byte-identical.** Three invocations that share nothing —
different working directory, different argument form, one where the source is
not below the cwd at all — emit the same IR. **B differs by 24 bytes**, which is
8 characters of directory name across the file's 3 site rows, exactly the
one-byte-per-entry arithmetic the playbook describes.

**The mechanism, read out of the compiler at the pin rather than inferred.**
D-236 (its 1.4.8): a `SourceFile` carries two paths, and the one the site table
and every diagnostic print is `shown` — *"the same file rendered RELATIVE TO THE
MANIFEST ROOT, so the emitted bytes cannot depend on how the compiler was
invoked"*. `front_set_root` finds that root by walking up from the main file's
directory for a `nitpick.toml`. A control confirms the front half is live: an
absolute argument produces a **relative** diagnostic path.

**So the playbook's rule is right about the observation and imprecise about the
cause, and the difference decides this measurement.** The dependence is not on
the working directory and not on the absolute prefix; it is on the source file's
position **inside its own tree**. The compiler's `src/npkc.npk` sits at the same
position relative to its own `nitpick.toml` on every checkout in the world.
**Therefore its emission is checkout-path-independent by construction, and
comparing that digest across two machines is legitimate.** Had the dependence
been on the absolute prefix, the comparison would have been guaranteed to differ
for a reason that says nothing about any compiler.

**One difference deliberately left in place, and named so it is diagnosed rather
than discovered.** The compiler side's number comes from `npkg build`, which
writes `build/npkc.ll`. Our CI never runs `npkg build`; it runs the bootstrap
harness's `quickemit.py`, which has the **same committed snapshot builder**
compile the **same entry file** (`harness.EMIT_CHECK` is `src/npkc.npk`) and
leaves the result as `npkc.ll` in `.internal/quickemit/`. Same source, same
builder, different output directory — and the output directory does not enter the
IR. If the two disagree, **that** is the finding, and the candidate causes are
named in the workflow beside the step.

*Alternatives declined:* asserting the digest against the compiler's published
`05457db4…` (this workbench has not seen its own value yet, and a check whose
expected value is a number somebody reported is not a check — it is the same
mistake as an allowlist added by reasoning, which RX-131 already paid for);
running `npkg build` in CI to produce `build/npkc.ll` exactly (it is the
compiler's own bootstrap ladder, minutes of work for byte-equality with an
artefact we already have, and W-18 keeps this workbench out of the business of
building the compiler more than once); digesting the object or the binary
instead (those are the artefacts S-42 has already shown to differ legitimately —
the emission is the whole point).

---

### RX-134 — `end` is refused as a BINDING name and accepted as a FIELD name, so RX-050's field names stand and its justification does not

**2026-09-06, cycle 0.0.5, measured at three pins.** Cycle 0.0.0 recorded that
`Match.end` "does not parse" because `end` is a reserved word, and chose `lo`
and `hi`. The choice is right. **The reason was never measured and is false.**

| program | `950bb1d` | `94874ce` | `3d15ac9` |
|---|---|---|---|
| `pub struct:Match = { int64:start; int64:end; };`, built by struct literal, read as `m.end` | **npkc 0** | **npkc 0** | **npkc 0** |
| the same, through `llc`, `ld.lld`, and run | — | — | **0 / 0 / exit 3**, which is `4 - 1` read out of a field named `end` |
| `int64:end = 5i64;` as a local binding | **`NITPICK-PARSE-002`** | — | **`NITPICK-PARSE-002`**, *"expected an expression"* |
| `int64:hi = 5i64;` — the control | — | — | **0** |
| `pub struct:K = { int64:range; int64:limit; int64:in; };` | — | — | **0** |

**So a reserved word is refused in BINDING position and accepted as a STRUCT
FIELD NAME; fields are their own namespace.** This is not a pin-dependent
expiry like RX-125's derives or RX-127's `limit<Rules>` — it is false at the
oldest pin too, so it was false the day it was written.

**Where it came from is the useful part.** `end` *is* reserved, and cycle 0.0.0
met that fact for real: probe 05 lost about an hour to `Vec<Frame>:stack`, a
reserved word in binding position, whose diagnostic points at a brace dozens of
lines away. **The rule was learned correctly in one position and generalised to
another without a measurement** — and because the *decision* it justified was
right, nothing ever contradicted it.

**That is why it survived five subcycles and reached seven sites**: `CLAUDE.md`,
`meta/specs/API.md` A-3, `meta/specs/BUILD.md` §7, `meta/roadmap/0.10/README.md`
twice, `tests/probe/probe06a_offsets_returned.npk`, and RX-050's own text. **An
unmeasured justification attached to a correct decision is invisible**, because
every check that could fire is a check on the decision. Nothing in this
repository — not `check_refs`, not `check_specs_current`, not a green suite —
can see a true rule resting on a false reason. Only running it can.

**The decision.** `Match` keeps `lo` and `hi`: they are shorter, they match
`SYNTAX.md`'s half-open interval, and renaming a settled public field to prove a
point is worse than the wrong justification was. **RX-050's text is not edited**
(W-28) — it is a settled decision and this supersedes the one clause of it that
made a claim about the compiler. Every live site now states the choice as a
choice.

*Alternatives declined:* renaming the fields to `start`/`end` now that they are
known to be legal (`lo`/`hi` are better names, and `API.md` A-3 and `BUILD.md`
B-18 have shipped them since 0.0.0); deleting the justification silently (it has
travelled to a cycle-0.10 checklist that a future session will read as a
constraint, so it needs a correction with a number, not a deletion); adding a
harness check for reserved words in field position (there is nothing to check —
the compiler permits it, so the check would assert this repository's taste).

---

### RX-135 — cycle 0.0's probe verdicts reached some documents and not others, and the specifications were the ones left behind

**2026-09-06, cycle 0.0.5, step 1.** The close re-read all 23 verdicts in
`0.0.0.md` §7 against `meta/specs/` — **by reading the specifications, not by
remembering them** — and the pattern in what it found is worth more than the
individual fixes.

**Six verdicts had a consequence that landed somewhere and not in the document
that owns it:**

| Verdict | Landed in | Missing from |
|---|---|---|
| 08b — a `wild T->` index does not trap | `SAFETY.md` §1 and §5.3, `VERIFICATION.md` §3, two checklists | **`meta/specs/README.md`**, whose one-paragraph summary still read *"and so does an out-of-range index"* |
| 09 — the wall is `string_bytes`, not the index | `OPEN_QUESTIONS.md` O-G1 | **`SAFETY.md` §7**, which calls itself *"the evidence for the request"* |
| 12 / 12b — `for … in` over a borrowing iterator is refused | `OPEN_QUESTIONS.md` O-A1 | **`API.md` §8**, still saying *"decide … after probe 12 says what the trait actually admits"* |
| 06a — an `Optional` is not `pick`-able | `CLAUDE.md`, the roadmap | **`API.md` §2**, which the probe's own header named as the owner |
| 06a — the field names | `API.md` A-3, `BUILD.md` B-18 | **`SAFETY.md` §6**, the rule that *owns* the offsets-not-slices decision |
| 02 — `#size_of` = 24 | `CLAUDE.md`'s measured list | it is the size of the **payload spelling `HIR.md` H-2 declined**, quoted as the specified `HirNode`'s |

**Three shapes, and each defeats a different instrument.**

1. **The summary page is corrected last.** `meta/specs/README.md`'s "the
   language in one paragraph, for a reader arriving from C" cites no decision
   and no rule, so **no citation sweep can reach it** — the mechanism RX-123
   already named, arriving in the document a newcomer reads *first*.
2. **The discovering document is not the owning document.** A probe reports; the
   finding is written where it was found — an open question, a record — and the
   normative rule is amended later or not at all. Each page then reads
   complete. `SAFETY.md` §7 is the sharpest case: it says of itself that it is
   the evidence, and it was the stale copy.
3. **A number attached to the alternative that was declined.** `#size_of<HirNode>`
   = 24 measures the shape H-2 rejected. The accepted shape has never been
   measured and does not exist in `src/` until cycle 0.2 — so the honest entry is
   *unmeasured*, not a derived 20.

**The decision.** All six corrected in the owning document, each with a dated
note saying what it previously said, per W-28. `CLAUDE.md` drops `HirNode` from
the measured list rather than substituting an arithmetic answer, because
substituting one would be the exact error `PLAYBOOK.md` records costing 37% of a
decision's headline number.

**And one thing this reconciliation could not have found by grepping**, which is
why the step is specified as a re-read: every one of the six is a claim about
**tense or truth** rather than presence. The stale sentences contain no wrong
token. `check_specs_current` was green across all of them and correctly so — it
checks that citations resolve, and a citation to a stale section resolves
perfectly.

*Alternatives declined:* rewriting `0.0.0.md` §7's verdict table to match
today's specifications (it is a verified record of a run at `950bb1d`; RX-114 set
the redirect pattern and RX-125 reused it); leaving `API.md` O-A1 open on the
grounds that cycle 0.10 decides it anyway (the recommendation rested on an
argument the probe voided, and a plan carrying a dead argument is how the wrong
thing gets built three cycles later).

---

### RX-136 — `SAFETY.md` asserted two enforcements that did not exist, and the one guarding the only bounds check is now built

**2026-09-06, cycle 0.0.5.** Two sentences in `SAFETY.md` §5.3 described
machinery in the present tense that no file implemented.

**(a) The accessor confinement check — the serious one.** §5.3 has said since
0.0.0 that *"a tree check enforces that no `.items[` appears outside
`src/core/vec.npk`"*, and RX-118 added the identical sentence for `.ptr[` and
`src/core/bytes.npk`. **`treecheck.ALL` held four checks and neither of them.**

That is not a missing convenience. S-23 calls the accessor pair *"the only
bounds check this library has"*, because D-070's guard is emitted for a slice, a
fixed array and a SIMD lane and for nothing else — a `Vec<T>.items` is a
`wild T->` and a `buffer`'s bytes are reached through `.ptr`, so an out-of-range
index in either **reads and returns a heap word at exit 0**; probe 08b measured
7 992 bytes past the allocation. An accessor bypassed anywhere is a wrong answer
with a green suite beside it.

**`check_accessor_confinement` is built, registered, and seen to fail in both
directions**, with the denominator printed on every run:

| control | result |
|---|---|
| the clean tree | **0 failures** over 13 files, 2 confined accessors |
| `src/core/core.npk`, which names both patterns **in comments** | **not reported** — prose is blanked, so the file documenting the rule is not failed by it |
| a `.items[` added to `src/hir/hir.npk` | **failed**, naming `file:line:col` |
| `src/core/vec.npk` stops containing `.items[` | **failed** in the other direction |

The fourth row is the point. A confinement list is an exemption list wearing a
different hat, and `PLAYBOOK.md` records that such a list's **membership** is
checked while its **reason** decays silently. So the owning file must still
contain its own accessor: the day `vec.npk` reaches its storage some other way,
this check stops guarding anything, and it says so instead of passing.

**(b) The fuzzer invariant.** §5.3 also states *"`TESTING.md`'s fuzzer
invariants gain one: no accessor is ever called with an out-of-range index"* —
as something already done. `TESTING.md` V-17's haystack-fuzzer list did not have
it. Added there now.

**Both are the same failure and it is not carelessness.** A consequence is
written in the document that **discovered** it, in a tense that reads as
discharged, and never carried to the document that **owns** it. Each page reads
complete on its own. Nothing mechanical compares them — `check_specs_current`
verifies that citations resolve, and *"a tree check enforces this"* names no
citation at all.

**`TESTING.md` §8's check table was short in both directions** and is corrected
with them: it omitted `check_no_division`, which exists and which S-25 says
enforces a rule, and it omitted this one, which did not exist and which S-23
said enforced a rule. **A table that is wrong in both directions at once is the
clearest possible statement that nothing was comparing it to the code.**

*Alternatives declined:* weakening §5.3 to say the check is *planned* (the
specification is the authority under RX-002, so code that disagrees is the
defect — and the rule it guards is the library's only bounds check, which is the
last one to leave unenforced); deferring the check to cycle 0.2 when `src/hir/`
starts indexing (the sentence claiming it exists is in the tree today, and both
owning files exist today); checking `items[` and `ptr[` without the leading dot
(it would match `v.items[` and also any local named `items`, and a check with
false positives gets disabled — the playbook's own warning).

---

### RX-137 — `VERIFICATION.md` §5 planned to adopt `limit<Rules>`, and §2 of the same file already recorded that it was declined

**2026-09-06, cycle 0.0.5.** RX-127 measured `limit<Rules>` at the `3d15ac9`
re-pin and declined it: a limited binding anywhere in the reachable call graph
charges **every** consuming program a mandatory `(LimitViolated)` `failsafe`
arm, at module-private visibility as well as `pub`, and the violation takes
D-241's trap route so no `?|`, `?!` or `is_err` can decline it. `SAFETY.md`
gained **S-24**, and `VERIFICATION.md` §2's rung table was updated to read
*"LANDED, and §5 does NOT take it — RX-127."*

**§5 itself was not.** Its heading still read *"the types that carry their
range"*, and **Rule P-4 — a numbered, normative rule — still said "when 1.5.2
lands, these become `limit`ed"**, with P-5 supplying supporting evidence for
adopting it. 1.5.2 had landed. A reader opening §5, which is where a
verification question sends them, met a live rule contradicting S-24 in another
file, with the correction sitting eighty lines above it in the same document.

**The decision.** §5 is retitled *"the types this library DECLINED to carry"*,
P-4 is marked **superseded by S-24** and P-5's argument is kept as an argument
rather than a recommendation. **The four `Rules` declarations stay**, for two
reasons: they are the right *ranges*, and they are what `src/core/limits.npk`
and the accessor pairs now check by hand; and a later reader will propose
exactly this construct, so the section should hand them the measurement instead
of making them repeat it.

**What this instance adds to RX-135's pattern.** The other five were a
correction that reached one document and not another. **This one did not leave
the file.** §2 and §5 of `VERIFICATION.md` disagreed, one paragraph of §2 knew
it, and the disagreement survived a subcycle — because a rung table is read when
you want to know what the compiler supports and §5 is read when you want to know
what this library does, and nobody has both questions at once. **Proximity is
not review.**

*Alternatives declined:* deleting §5 (it is the record of a real decision and
the ranges are live); leaving P-4 as a conditional promise (it is written as
normative, it is numbered, and `VERIFICATION.md` is cited by `SAFETY.md` §3 as
the machine-checked form of S-5 — a dead rule in that position is exactly the
dormant-rule shape cycle 0.1's gate exists to catch).

---

### RX-138 — `bytes_take_string` returned a BORROWED VIEW while three documents called it owning; it is `bytes_copy_string` and it copies

**2026-09-06, cycle 0.0.5 audit triage.** The last function in
`src/core/bytes.npk` read:

```
pub func:bytes_take_string = string(Bytes->:b) never fails {
    pass string_from_bytes(b.buf.ptr, b.len);
};
```

`string_from_bytes` is a **view primitive**. The compiler's runtime sets `cap 0`
on the header it returns and its own comment beside the code reads *"cap 0 is
the not-mine bit"*; `BUILTIN_REFERENCE.md` §1 lists `string_bytes` and
`string_from_bytes` as *"the explicit view primitives"* and gives them a `Views`
column of 1. Read at `3d15ac9` with `git show`, not from a working tree.

**Three documents said the opposite**, and each was a live navigational claim
rather than a record: `0.0/README.md`'s cycle checklist (*"hands over an
**owning** `string`, which is the only shape that may leave the frame"*),
`harness/baseline/RESIDUE.txt`'s reason line for `npk_string_from_bytes`, and
`src/core/bytes.npk`'s own function comment. `core.npk` forbade the escape in a
comment and re-exported it fourteen lines lower.

**Measured, and both halves of the claim are false.**

| probe | result |
|---|---|
| take at len 5 over an 8-byte body, grow past capacity, read back by equality | **exit 46** — a wrong answer |
| the same with the exit code as the first byte | **exit 170 = `0xAA`**, D-183's free poison |
| return it from the frame that **owns** the `Bytes` | **REFUSED** `NITPICK-BORROW-001` |

`bytes.npk`'s `b.buf = move(bigger)` frees the old body on every growth, so
every `string` taken before a growth dangled. **Five public functions grow a
`Bytes`.**

**THE SUITE ALREADY BUILT THE STALE ALIAS AND DECLINED TO READ IT.**
`tests/unit/bytes_unit.npk` took `out` at line 55, reallocated at line 63, and
never read `out` again; it stayed in scope to the end of `main` and its cap-0
drop freed nothing, so nothing complained. **One added line turns the green run
into exit 46.** This is the third use-after-free this repository has shipped
under a green suite and the second to survive an independent VERIFIED PASS. A
leak gate cannot see it: it is a WRONG ANSWER, not a leak.

**The decision: COPY, and rename.** Route (ii) — keep the view, rename it to say
so, and write an invalidation contract — was declined. The library's own house
rule for O-N9 is *a view is a PARAMETER, never a return value*, it is written in
this very file's header, and a function returning one violates it eleven lines
from where it is stated. Keeping the hazard and documenting it would have made
the rule advisory in the one file that states it. `API.md` A-12 already says the
library's own output goes into a caller-owned `Bytes` and never a returned
`string`, so nothing on a hot path pays for the copy.

**The copy is spelled `string_concat("", view)` and not `string_slice`.**
`string_slice` is D-186's owned copy and would be the obvious choice, but it
returns `Result<string>` and unwrapping it needs `?!` — an error path that can
never fire, threaded through a function this file promises `never fails`. That
is the exact shape RX-132 spent a subcycle DELETING from `bytes_put_uint`, where
a division that could not divide by zero charged every consumer two `failsafe`
arms. `string_concat` is `never fails` at `3d15ac9`, always allocates and copies
(measured: no short-circuit on an empty operand), and charges the budget
nothing. `string_concat("", "")` allocates zero bytes and returns cap 0, so the
empty case needs no special path — measured, exit 0.

**Measured after the fix**: the copy survives two growths; 2 000 000 copies of
101 bytes — 202 MB if leaked — run to exit 0 under a 64 MiB `ulimit -v`, so the
allocation is reclaimed at each binding's scope exit.

**AND ONE CLAIM STILL DOES NOT HOLD, WHICH THE FIX DOES NOT RESCUE.** The value
is owning and outlives the `Bytes`, but the compiler still refuses
`pass raw bytes_copy_string(@b)` out of a frame that OWNS the `Bytes`, and it
refuses it for the SIGNATURE rather than for the body: a control function taking
`Bytes->` and returning `string_concat("small", "!")` — which cannot alias its
argument at all — is refused identically, while the same expression written
INLINE in the owning frame compiles and runs. The tracker taints any
view-capable return of a function that received a borrow. It is sound and it is
coarse, and it is raised as an open question rather than worked around. **So the
sentence "the only shape that may leave the frame" is deleted rather than
repaired**: the working shapes are build-and-consume in one frame, or take the
`Bytes` as a PARAMETER and return the string one level up, both measured
accepted.

*Alternatives declined:* keeping the name `bytes_take_string` (nothing is taken
— `b` keeps its bytes and its capacity — and the old name is why the return was
read as a hand-over); adding a second, honestly-named view function beside the
copy (it would be the first `pub` view return in the library, against the house
rule, for a caller that does not exist yet and can pass the `Bytes` instead).

---

### RX-139 — a `Vec` with `cap <= 0` is DEAD, every growth path traps on one, and `vec_init_zeroed` was the one constructor that could build an invalid `Vec`

**2026-09-06, cycle 0.0.5 audit triage.** `vec_free` sets `count = 0; cap = 0`
deliberately, as poison: it is what makes `vec_get`, `vec_set` and `vec_pop`
trap on a freed `Vec` instead of reading through a dangling `items`. **The
poisoning was right and incomplete.** The three growth paths read `cap` as an
arithmetic starting point and none checked it.

Measured at `3d15ac9` on a `Vec` that had been freed:

| entry point | before | after |
|---|---|---|
| `vec_reserve(@v, 1)` | **exit 124** under `timeout 6` — `while (nc < want) { nc = nc * 2 }` from `nc = 0` **DOES NOT TERMINATE** | **94** |
| `vec_push(@v, x)` | **exit 91**, `HeapBadRequest` | **94** |
| `vec_insert(@v, 0, x)` | **exit 91**, `HeapBadRequest` | **94** |
| `vec_init_zeroed(-5)` then `vec_push` | **exit 0**, having written five elements BEFORE the block | **94** |

The first is the blocking one and it is a **denial of service in the container
every engine in this library is built on**, reached with no backtracking at all
— against the first of `CLAUDE.md`'s non-negotiable rules, which exists because
catastrophic backtracking is a DoS and the language has no cancellation (D-062).

**THE AUDIT OVERSTATED THE OTHER TWO AND THE CORRECTION MATTERS.** It reported
that `vec_push` and `vec_insert` *"`ralloc(<dangling>, 0)` and then write"*.
They do not get that far: the runtime refuses `ralloc(p, 0)` outright — D-150,
*"freeing is spelled dalloc, and C's `realloc(p, 0)` is the
implementation-defined footgun this is not"* — so both were already a
deterministic controlled stop, not memory corruption. They stopped for the
ALLOCATOR's reason rather than this library's, and reported that the allocator
had been misused when what happened is that a freed container was written to.
Real, and less severe than filed.

**THE FIX IS A TRAP, NOT A FLOOR, AND THE SIBLING IS NOT THE PRECEDENT.** The
audit's first suggested remedy was to copy `bytes_reserve`'s
`if (nc < 1i64) { nc = 1i64; }`, which `vec_reserve` lacks. **That would have
been wrong here.** `Bytes` has no free, its `buf` is MANAGED, and
`bytes_reserve` allocates a fresh `buffer_new` — so flooring a zero capacity
there yields a valid buffer. In `vec_reserve` the block has already been
`dalloc`ed, so flooring `nc` to 1 would hand `ralloc` a **dangling pointer with
a plausible size** and let it succeed: a loud hang traded for silent heap
corruption. *The same guard in the two files would have been two different
decisions*, and "the sibling has it and this does not" is a reason to look, not
a reason to copy.

So `cap <= 0` traps `OutOfBounds` through `vec_oob`, like every other misuse in
the file, **at the top of the entry point** rather than inside the growth
branch: `vec_reserve(@v, 0)` on a freed `Vec` would otherwise return `NIL` and
report success about a container that no longer exists. No `Vec` this library
produces can reach the check — both constructors floor the block to one element
— so it costs one perfectly-predicted compare and fires only on a
use-after-free.

**`vec_init_zeroed`'s negative was found by this triage, not by the audit**,
while establishing the full extent rather than fixing the finding where it was
reported — and it is the worst of the four, because it **exited 0**.
`vec_init_zeroed(-5)` floored the ALLOCATION to one element and wrote `-5`
straight into `count`; `vec_push`'s guard is `v.count >= v.cap`, which read
`-5 >= 1` and was FALSE, so the push wrote at `items[-5]`. Every other entry
point in the file already trapped on a negative — `vec_reserve` on `need`,
`vec_truncate` on `n`, both accessors on `i`. The half of the sweep that was
missing is the one where **the negative goes into a FIELD rather than into an
index**, and no amount of checking indices would have found it.

Five unit programs, one per entry point plus `bytes_oob_get_after_clear.npk`,
each **seen to fail before it was trusted**.

*Alternatives declined:* the floor (above); guarding only inside the growth
branch (silently succeeds on a dead `Vec` when no growth is needed); making
`vec_free` null `items` so a later use faults (a fault is not this library's
controlled stop, and the field is `wild T->` with no null to mean anything).

---

### RX-140 — a refused close REVERSES its archive; `meta/roadmap/done/` is a claim, not a filing cabinet

**2026-09-06, cycle 0.0.5 audit triage.** Cycle 0.0 was marked DONE, moved to
`meta/roadmap/done/0.0/`, and its `ROADMAP.md` row struck through. Four hours
later the W-22 audit refused the close on two blocking findings in `src/core/`.

**The archive is reversed with one `git mv`, and the folder is back at
`meta/roadmap/0.0/`.** Three reasons, in order of weight.

1. **A cycle folder inside `done/` is a claim that the cycle is finished, and
   the claim was false.** A false statement in the tree is the defect class this
   cycle spent five subcycles finding; keeping one in order to preserve a tidy
   directory would be the cycle failing its own lesson at its own close.
2. **`done/README.md` says archived cycle notes are never rewritten, and the
   blocking fixes require rewriting this cycle's checklist.** `0.0/README.md`
   line 251 was one of RX-138's three false "owning" sentences. Editing it
   inside `done/` would have made the never-rewrite rule advisory, and the
   exception would have been granted by the session that wanted it. **A rule
   gets its force from being absolute.**
3. **The predecessor anticipated it.** `0.0.5.md`'s own REPORT block reads *"if
   the audit wants anything undone, it is one `git mv` back"* — so the reversal
   is the plan being followed, not a new judgement.

**What was rewritten and what was not**, because the distinction is the whole
decision: **live navigation is corrected, historical claims are not.** The
pointers that had been rewritten to `done/` were rewritten back (`CLAUDE.md`,
`harness/README.md`, `nitpick.toml`, `meta/OPEN_QUESTIONS.md`,
`tests/probe/README.md`, three probe headers,
`harness/selfcheck/syscall_consumer.npk`, `0.1/0.1.0.md`, `ROADMAP.md`), and
`0.0.0.md`/`0.0.1.md`'s relative link depth went back from `../../../../` to
`../../../` — the depth changed and no claim did, in both directions.
`0.0.5.md`'s committed REPORT block and its two statements that step 6
*performed* the move are untouched: they are true accounts of an action taken.

**The redirect note is deleted rather than corrected, and that closes the
audit's N-3.** It claimed *"41 such mentions across 15 files"*, present tense,
immediately before *"they are deliberately not rewritten"*. Re-derived: 49
across 17 files before the move, **33 across 9 at the state the note described**
— it matched no state the tree has ever had, because it was written from a count
taken before the same commit's own rewrites. The reversal removes its subject.
**The durable half is the lesson: a count written in the present tense about a
tree that is mid-edit is stale before the commit lands.** Write the count from
the tree you are about to commit, or do not write a count.

*Alternatives declined:* leaving the archive in place and editing inside it
(kills the never-rewrite rule); leaving it in place and fixing nothing until a
later cycle (the two blocking findings are a hang and a use-after-free in the
storage layer every later cycle builds on).

---

### RX-141 — the CI emission digest stays a PRINT; a same-machine comparison licenses the substitution and not the assertion

**2026-09-06, cycle 0.0.5 audit triage.** `.github/workflows/ci.yml` digests
`.internal/quickemit/npkc.ll` and prints it, for the compiler's S-42
cross-machine question. The audit verified the substitution byte-for-byte:
`build/npkc.ll` and `.internal/quickemit/npkc.ll` are both 21 514 197 bytes at
`05457db4e98b18a97033eac8bfbe1cfbcddf72f6cf5373dbb99d3693ce94d367`,
`cmp`-identical, and the reasoning behind it checks out at source
(`quickemit.py` → `build_tool` → the committed snapshot builder on
`src/npkc.npk`, with D-236 rendering site rows relative to the manifest root so
the output directory does not enter the IR). **The substitution is legitimate.**

The audit then noted, non-blockingly, that the step could name that digest and
become an assert. **It must not, and the reason is precisely what the
measurement settles and what it does not.**

**That comparison is SAME-MACHINE.** It establishes that `quickemit.py` and
`npkg build` produce the same emission on one machine, so
`.internal/quickemit/npkc.ll` stands in for `build/npkc.ll` honestly. It says
nothing about the CROSS-MACHINE claim — which is the open question the step
exists to answer and **which has never been observed**: the runner's value is
unknown until a run prints it.

Asserting the developer machine's number would **turn an open measurement into a
foregone one**. CI would go red on the first genuine cross-machine difference
and report it as a broken pin rather than as the finding it would be — and a
difference in the EMISSION would be a compiler defect, which is exactly the
thing worth learning. D-265 clause (4) asks pin notices to carry an expected
value; the value becomes an expectation on the day somebody holds both sides of
it and records that they matched, and not before.

*Alternatives declined:* asserting now (above); removing the step (it is the
compiler's own request, S-42 recommendation (c)); asserting only the SIZE (the
same argument one field narrower, and a size collision is cheaper than a digest
collision).

---

### RX-142 — a measurement is dated by a COMMIT or it is not dated, and a tree check now says so

**2026-09-06, cycle 0.0.5 audit triage.** "The pin" is a name that re-points. A
sentence saying a thing was measured *at the pin* becomes false the day the pin
moves, **while nobody edits it** and with nothing lexically wrong to find: it is
a true sentence about a different compiler.

This repository has now paid for it twice. RX-120 is the expensive one:
`check_no_syscalls`'s first layer *"cannot see a syscall"* was measured at
`950bb1d`, recorded as a permanent property, and carried to four sibling
repositories as current fact. At `3d15ac9` the compiler's D-262 trimmed the
prelude and the layer CAN see one. The claim reversed and no document moved.

**THE FIRST SWEEP CLOSED THE PHRASE AND NOT THE CLASS.** Cycle 0.0.5 corrected
the three sites carrying the exact words *"measured at the pin"* and recorded
the lesson. The cycle 0.0 audit then found **39 lines across 20 files** in the
same class, spot-checked the two most load-bearing and found **both still true**
— so nothing was wrong that day, and the class was thirteen times the size of
the sweep said to have closed it. **A grep is a sweep; only a check is a rule.**

`check_dated_measurements` is registered in `treecheck.ALL`, making seven, and
runs over 115 text files. Seventeen live sites were dated to `3d15ac9` in the
same commit. It was shown to fail before it was trusted: a planted
`measured at the pin` in `src/core/limits.npk` was named at `file:line:col`, and
a second plant proved the exemption marker is **per line and not per file**.

**Records are out of scope, and each exclusion has a reason rather than a
convenience.** `meta/roadmap/` holds execution records that say what was
measured when they were written; `meta/audits/` holds another session's filed
report reproduced verbatim; `TRANSCRIPT.txt` and `RX120.txt` are measurement
transcripts. **`meta/DECISIONS.md` is excluded too, and that one is a rule
rather than a courtesy**: a settled decision's text is never rewritten, it is
superseded by a numbered decision that says why. Seven lines in it are in this
class; a check demanding they be edited would be a check against this
repository's first rule about its own documents, and the remedy for a decision
whose dating went stale is a superseding decision, not a `sed`.

*Alternatives declined:* a third sweep (the second one is what produced this
finding); matching the bare word "pin" (false positives on "the pinned
compiler", "held to the pin", "the pin moves" — and a check with false positives
gets switched off, which the playbook records); a file-level exemption (an
escape hatch that grows; the marker is per line and has to be written on the
line that needs it).

### RX-143 — `vec_oob` RETURNED for `i == 0`, so nine `pub` entry points performed the access they had just refused; the stop's index is now negative for every `i`

**2026-09-06, forced by the SECOND cycle 0.0 audit (BL-3), which is the largest
defect this cycle found.** **This supersedes RX-130's sentence "the helper is
`vec_oob`, it never returns", which was false at the value that mattered from
the day it was written.** RX-130's *decision* — that a violation traps
`OutOfBounds`, spelled as the language's own trap rather than an invented code —
stands unchanged and is right. What did not hold was its claim about the
implementation.

The body was:

```
int64[1]:guard = [0i64];
discard(guard[i]);
```

**Index 0 is in range for a one-element array.** Measured at `3d15ac9`, with
controls: `vec_oob(0)` returns and the program runs on (exit 50), while
`vec_oob(1)` and `vec_oob(-1)` both exit 94. Identical at −O0 and through
`opt -O2`.

**And a stop that returns is not a weakened guard, it is no guard**, because
every one of the 28 call sites is `drop vec_oob(…)` and `drop` **continues**.
Of those 28, **19 are sound** — they can only pass a strictly negative value or
one ≥ 1 — and **9 are broken**: every guard of the form `i >= <count|len>`
reached with an empty or freed container, where `i` is 0. Measured, one program
each:

| entry point | what it did instead of stopping |
|---|---|
| `vec_get` | empty `Vec`: **returned a heap word**, exit 51 |
| `vec_set` | **freed** `Vec`: **completed the write through a dangling `items`**, exit 62 |
| `vec_remove` | empty `Vec`: left **`count == -1`**, exit 60 |
| `vec_swap_remove` | reads `items[-1]`, writes `items[0]`, `count` → −1, exit 61 |
| `bytes_get` | empty `Bytes`: returned a byte past `len`, exit 53 |
| `bytes_set` | wrote past `len`, inside `cap` — a wrong answer later, exit 54 |
| `sset_contains` | freed set: fell into `vec_get(s.sparse, 0)` on a freed block |
| `sset_insert` | freed set: two writes through a dangling `items` |
| `sset_at` | empty live set: **returned a phantom member**, exit 55 |

**Two of those chain into something worse than they look.** After
`vec_remove(@v, 0)` leaves `count == -1`, `vec_push`'s guard reads `-1 >= 4`,
is false, and the element is written at **`items[-1]` — before the block, over
the allocator's header** — surfacing later as **exit 95** from inside `dalloc`.
Verified here, not taken from the audit. And `sset_at`'s phantom member is
verbatim the failure `src/core/sparseset.npk`'s own header warns of: *a wrong
sparse-set probe adds a thread for a state the automaton is not in and the
library returns a match that is not there.*

**THE FIX: the index is NEGATIVE for every `i`, not merely non-zero.**

```
int64:below = 0i64 - 1i64 - (i & 1i64);   // -1 or -2
discard(guard[below]);
```

`i & 1i64` is 0 or 1, so `below` is −1 or −2. Two properties are wanted and both
are had: it is **total** — no overflow is possible, since only a mask and a
subtraction of a value in {0,1} are involved, verified at `int64`'s minimum and
maximum — and it is **out of range for an array of any length**, so the trap
does not depend on the guard array one line above staying one element long.
*The rejected alternative was `guard[i | 1i64]`*, which is odd and therefore
never 0 and is a correct one-operation fix today; it was declined because its
correctness is coupled to the array's declared length, so widening `int64[1]`
to `int64[2]` later would silently restore the defect. The negative form also
matches the model the file's own 19 sound call sites already use, where "out of
range" means "negative".

**THE PARAMETER SURVIVES AND ITS STATED REASON DID NOT.** `vec.npk` said `i` was
passed "only so the trap is reached with a value the optimiser cannot prove
constant". Measured at `3d15ac9`: a **literal** out-of-range index compiles at
exit 0, `npkc` folds it to an unconditional `call void @npk_trap(i32 -4099)`,
and the program exits 94 at both optimisation levels. Folding does not defeat
this trap at this pin. The parameter is kept for the two reasons that are true —
the call site records **which** index was out of range, and a compiler that later
refused a constant out-of-range index outright would break a parameterless
spelling — and the false reason is deleted rather than left standing.

**WHY 108 GREEN UNITS WERE GREEN OVER IT, AND THIS IS THE PART THAT TRANSFERS.**
All **twelve** out-of-range unit programs passed a non-zero argument: 3, 1, −1,
2, −1, 3, 16, −1, −1, −1, −1, −5. Twelve of twelve avoided the single value at
which the stop did not stop. `SAFETY.md` enumerated "four cases are gated" and
read as exhaustive; `i == count == 0` was the fifth. **A thirteenth case of the
same shape would not have found this.** So the remedy is not more boundary cases
but a case of a different kind: **`vec_oob_selfcheck_{zero,negative,positive}`
test the PRIMITIVE, asserting that `vec_oob(k)` does not return for
k ∈ {−1, 0, 1}.** That trio fails for the *next* spelling of the trap whatever
it is, and needs no extension when a tenth accessor is written. Nine further
units cover each broken entry point at exactly the empty-container boundary.
**Ten of the twelve were seen to fail against the shipped tree first, each with
its own distinct exit code**, and the two that pass on both trees are the
controls that would catch a fix which trapped at 0 by ceasing to trap elsewhere.

*Alternatives declined:* documenting the hole and guarding at the nine call
sites (nine copies of a rule is nine places for it to weaken — the argument
RX-123 makes, and the single definition is what made this a one-line fix);
`guard[i | 1i64]` (above); returning a `Result` from `vec_oob` (RX-130 settled
that an error channel here lands on the search path).

### RX-144 — the FREE paths stopped on the allocator's check and reported `Unreachable`, so "`cap <= 0` traps `OutOfBounds` like every other misuse in this file" was not true of two of them
> **SUPERSEDED IN PART by RX-156 (2026-09-25)** — its reading that 95 reported
> the wrong thing: `Unreachable` is the language's code for a double free. The
> guard and its 94 stand, as a trade RX-156 states.

**2026-09-06, from the second cycle 0.0 audit (N-11).** RX-139 put a `cap <= 0`
guard on the three GROWTH paths — `vec_reserve`, `vec_push`, `vec_insert` — and
wrote, in `vec.npk`'s header and in RX-139 itself, that `cap <= 0` traps
`OutOfBounds` *"like every other misuse in this file"*. It did not. Measured at
`3d15ac9`, three programs: `vec_free` twice → **exit 95, `Unreachable`**;
`vec_free_owning` after `vec_free` → **95**; `sset_free` twice → **95**.

They stop, deterministically — this was never silent — but they stop on the
**allocator's** double-free check and report a broken heap invariant where what
happened is that a freed container was used. **That is precisely the complaint
`vec.npk`'s own header makes six paragraphs earlier about `vec_push` and
`vec_insert`** — *they stop on the RUNTIME's check of a size, not on this
library's check of its own invariant, and they report the wrong thing* — fixed
there in the same subcycle and left standing here, in the same header that
states it.

**The decision: the same guard heads `vec_free` and `vec_free_owning`.**
`sset_free` inherits it by calling them and declares no poison of its own,
which is right: the guard belongs to the container that owns the block.
Three units, each **seen to fail at 95 before the fix and passing at 94 after**:
`vec_oob_free_twice`, `vec_oob_free_owning_after_free`,
`sparseset_oob_free_twice`.

`vec_free_owning` is the more important of the two and not the more obvious.
Without the guard it walks `0 .. count` **moving elements out of a freed block
and dropping them**, reaching `dalloc`'s check only afterwards. It is currently
survivable only because `vec_free` also sets `count = 0`, so the loop body runs
zero times — and `count` is a field a caller can write, since a `pub struct` has
no private fields (D-149). The poison that matters is `cap`.

**The transferable half is about the sentence, not the code.** *"Like every
other misuse in this file"* is a claim about a set, and **the set was never
enumerated**. It was written while five entry points were being fixed and read
as a summary of them; it was false about the two that had not been looked at. A
claim of the form "like every other X" should either name the X's or be replaced
by one that does not quantify.

*Alternatives declined:* documenting it as a known difference (the header
already documents the identical complaint about `vec_push` and calls it wrong,
so documenting would make that paragraph advisory); making `vec_free`
idempotent by returning early on `cap <= 0` (a double free is a bug in the
caller and D-123's reasoning applies — silently accepting it reports success
about a container that no longer exists, which is the same failure `vec_reserve`
was fixed for).

### RX-145 — `check_dated_measurements` pruned by leading dot, so the only file of a class it declares was unreachable; it prunes by NAME and reports per-extension denominators

**2026-09-06, from the second cycle 0.0 audit (N-10).** The check written to
close N-9 could not see the one file its own docstring names. It declared
`.yml` in `_UNDATED_EXTS` and its scope sentence ends *"the harness, `src/`, the
probe headers, the manifest **and the workflow**"* — then pruned every directory
whose name begins with a dot, which makes `.github/` unreachable. The tree's
only tracked `.yml` is `.github/workflows/ci.yml`.

Reproduced here rather than taken from the report: the shipped walk opens
**132 files, `.yml` 0**, and reports `failures: []`, while the check's own regex
finds **two** matches in that file (`ci.yml:221` and `ci.yml:253`). Both are now
dated — the cache-hit sentence names `NITPICK_COMMIT` and the `rx120.sh` step
name says `3d15ac9` — and the fixed check finds them before the fix and nothing
after.

**Two changes, and the second is the one that generalises.**

1. **Prune by NAME**, from `_UNDATED_PRUNE_DIRS = (".git", ".internal",
   "__pycache__", "build")`. The tell was already in the tree and the audit
   spotted it: `_UNDATED_SKIP_DIRS` carried `.internal/` and `.git/`, which the
   leading-dot prune had already removed, so **they were dead code** — and dead
   code in a skip list is evidence that the author expected the list to be doing
   the skipping. It is now doing it, and the two dead entries are gone.
2. **The check reports its denominator PER DECLARED EXTENSION**, with a note
   saying a zero is a finding. `treecheck.py`'s own module docstring already
   says a check that finds nothing because it **looked nowhere** is
   indistinguishable in the output from one that found nothing because there was
   nothing to find — and then this check declared seven extensions, opened zero
   of one of them for a whole subcycle, and reported a single healthy-looking
   aggregate. A class with a zero beside it is a question a reader can ask; a
   class absorbed into a total is not.

Shown to fail before it was trusted, in the directory that was unreachable: a
planted `measured at the pin` appended to `.github/workflows/ci.yml` is named at
`file:line:col`, and the check is clean again when it is removed.

**This is finding-shape N-6 — a rule wider than the mechanism enforcing it —
occurring inside the check that was built to retire a sweep.** RX-142 said *a
grep is a sweep; only a check is a rule*, and it is still true; what this adds
is that **a check is only a rule over the files it opens**, and the count of
those files belongs in its output.

*Alternatives declined:* adding `.github` back as a named exception to the
leading-dot prune (it fixes this file and not the class — the next dotted
directory holding a tracked text file is invisible again); dropping `.yml` from
the declared extensions (the workflow is exactly where a pin-dated claim is most
load-bearing, since it is the file that names the pin).

### RX-146 — `bytes_copy_string` LEAKS on an empty `Bytes`; the compiler is the defect, the comment claiming otherwise was wrong three times, and the gate is a memory cap that is PENDING rather than a guard
> **SUPERSEDED IN PART by RX-154 (2026-09-25)** — B-5b's one-token marker, and
> the claim that the run notices "the day the pin moves past the named commit":
> the commit was never read. The decision — a correct-and-red unit, run and
> printed, outside the denominator, red the day it passes — stands.

**2026-09-06, from the second cycle 0.0 audit (BL-4 and N-12).** RX-138 replaced
a borrowed view with `string_concat("", string_from_bytes(b.buf.ptr, b.len))`.
The copy is correct. **The empty path leaks 32.2 bytes per call**, and the
paragraph in `src/core/bytes.npk` that said it did not was wrong in three
separate ways at once, in a comment written to justify not writing a test:

1. *"`string_concat` of two empty strings allocates zero bytes."* Read at
   `3d15ac9` in the compiler's own source rather than in a document:
   `@npk_string_concat` (`runtime/npkrt.ll:6376`) has **no empty
   short-circuit** — it computes `n = al + bl` and calls
   `npk_alloc_internal(n)` unconditionally — and `@npk_alloc_impl` (:4808)
   substitutes 16 for a zero request deliberately, *"alloc(0) is a real, unique,
   freeable 16-byte block (D-150)"*. A real block is allocated and the cap-0
   result gives the drop nothing to free.
2. *"Measured — `bytes_clear` then this …"* — **the measurement was not in the
   tree.** No committed test called `bytes_copy_string` on an empty `Bytes`; all
   eleven call sites in `bytes_unit.npk` followed an `extend` or a `put_uint`.
   That is N-12, and it is the same shape as the fabricated transcript
   adjudication (a) found in `RX120.txt`: **a sentence formatted like evidence.**
3. *"exit 0"* — **the wrong instrument, by this repository's own rule.** S-22:
   D-151 counts `wild` blocks, D-188 counts live drivers, neither sees a managed
   body, and a `string`'s bytes are managed. `bytes_unit.npk` says so in as many
   words twenty lines away.

Measured here with the instrument S-22 requires: 8 000 000 calls under a 64 MiB
address-space cap, with `/bin/true` passing under the same cap — the **empty**
path exits **92, `HeapOom`**; the **non-empty** control exits **0** with no peak
growth. At 2 000 000 calls the empty path peaks at 62 592 KiB and the control at
0, which is where the 32.2 bytes per call comes from.

**THE ROOT CAUSE IS A COMPILER DEFECT AND IT WAS RAISED, NOT WORKED AROUND.**
The compiler's own source documents the asymmetry: `@npk_string_slice`
(`npkrt.ll:6530`) carries exactly the branch `string_concat` lacks — *"An empty
slice allocates nothing: len 0 is never dereferenced, and cap 0 gives the drop
nothing to free."* It was raised under W-11, confirmed by the compiler side as
**DEF-25**, and fixed and pushed at **`fe42dba`**, with their words: *nothing in
library code needs a guard.*

**SO THERE IS NO GUARD, AND THE ONE-LINE GUARD IS NAMED HERE SO THAT NOBODY ADDS
IT LATER.** `if (b.len == 0i64) { pass ""; }` would make the run green today and
would still be in the hottest accessor of the byte sink every replacement in this
library is composed into, long after the compiler stopped needing it.
`CLAUDE.md`'s last non-negotiable rule forbids it by name.

**THE GATE IS THE `Vec` MEMORY-CAP PAIR'S SHAPE, WITH ONE HALF DECLARED
PENDING.** `bytes_copy_string_nonempty.npk` is live and green.
`bytes_copy_string_empty.npk` is **correct and red at this tree's pin**, because
the fix is at a commit this tree is not pinned to, and it carries a new marker:
`pending-until: fe42dba`. A pending unit is built, linked and **run** like any
other, its actual exit printed, and counted as **neither a pass nor a failure** —
the rule `selfcheck.py`'s three pending cases already follow (P-18): *a pending
case is not a passing case*.

**AND THE MARKER RETIRES ITSELF, WHICH IS THE HALF THAT MATTERS.** If a pending
unit starts **meeting** its expectation the run goes **RED** and names the action
— delete the marker. That is the opposite of what a known-failure list usually
does, and it is deliberate: this ecosystem's recurring defect is the rule that
outlives its reason (a dead skip entry, an allowlist nobody re-derives, a check
whose scope drifted — N-6, N-10, RX-131 and RX-145 are all one shape). A marker
that survives the day it stops being true is one more of them. Here the run that
moves the pin is the run that says so. Shown able to fail on three mutations: a
pending unit meeting its expectation reddens with `IS NOW STALE`; a blank
`pending-until:` is UNREADABLE rather than a silent skip; and a pending unit that
does not compile is a failure, because the marker excuses a wrong exit code and
not a refusal.

*Alternatives declined:* the library-side guard (above, and forbidden);
re-pinning this repository to `fe42dba` inside this subcycle (the pin is the
board's to move and a re-pin is not a triage's to make — the whole tree's
measurements belong to one pin); writing the test only after the re-pin (that is
how a defect gets forgotten between the day it is understood and the day it
could be caught, and the pending file is the artefact that prevents it);
`string_slice` instead of `string_concat` (its `Result` is real, but swapping
primitives to route around a defect the compiler has already fixed would be the
workaround with extra steps).

---

## The adoption to compiler c3bdae2 — cycles 0.0.4b and 0.0.4c

*Appended 2026-09-25 by stream 1, working `meta/roadmap/0.0/0.0.4b.md`, against
pinned toolchain `c3bdae2` (the compiler's 1.5 close) under LLVM 20.1.2, with
`3d15ac9` kept for the old-pin baselines. The third re-pin this repository has
absorbed, and the first after the libraries' pause. The drafts are the plan's
§8, PD-1 … PD-6, numbered here in commit order.*

### RX-147 — the whole-tree walk prunes a nested repository, by shape and by name, and says what it pruned

**2026-09-25, cycle 0.0.4b (the plan's PD-1).** CI has been **red since
`ab93eae`** and the reason is not the pin. Read from the failing job's own log
(run `34047719942`, job `101525667445`, fetched through the API rather than the
summary): `check_dated_measurements` examined **1016 text files** and failed on
`.nitpick/meta/roadmap/1.5/1.5.2d.md:395:40` — the **compiler's** roadmap — and
the run ended `141/142 unit(s) passed`.

**The mechanism.** CI checks the pinned compiler out at `.nitpick/`, inside the
workspace, because `actions/checkout` cannot place a `path:` outside it. Since
RX-145 this check prunes by NAME (`.git`, `.internal`, `__pycache__`,
`build`), which reaches `.github/` as RX-145 intended — and reaches `.nitpick/`
as nobody did, so the one walk from the tree's root walked a second repository.
**Invisible on a developer machine**, where the compiler is a sibling directory
and not a child: every local run was green over it, and so was the third audit.

**The decision.** A directory holding a `.git` entry — file or directory, so a
worktree or submodule counts — is another repository and is not walked; so is a
directory named `.nitpick`, so an export of the compiler with no `.git` is caught
too. **The pruned list is the check's FIRST note**, `N nested repositor(y|ies)
pruned: …`, so *"133 files, 1 nested repository pruned"* and *"133 files"* are
different statements and only the first can be checked. Extends RX-145, whose
rule — by name, never by leading dot — stands: an ordinary dotted directory is
still walked. It is `nitpick-time`'s TM-146 lesson, carried here by the board's
SHARED FINDINGS row 5.

**Reproduced before it was fixed, and controlled both ways**, in a scratch clone
with a `.nitpick/` holding a `.git` and a planted `measured at the pin` —
`0.0.4b.md` step 1's `walk`:

| state | failures | first note |
|---|---|---|
| before the fix | **1**, `.nitpick/meta/n.md` — CI's red, on this machine | — |
| after the fix | 0 | `1 nested repository pruned: .nitpick` |
| plus the same plant in an ordinary `.plain/` | **1**, `.plain/meta/n.md` — still walked | `1 nested …: .nitpick` |
| plus a nested repository by shape only, `tools/other/.git` | 1, `.plain/…` | `2 nested repositories pruned: .nitpick, tools/other` |
| `.nitpick/` with its `.git` removed (an export) | 0 | `1 nested …: .nitpick` — by name |

**Why only this check.** It is the one walk from the tree's root. `npk_files`
walks named subtrees and already skips dotted directories; `stages.files_of`
walks the manifest's declared paths (`src`, `tests`, `harness`), none of which
holds a checkout; `check_specs_current` walks `meta/`. CI's log agrees: the only
failure in run `34047719942` was this check.

*Alternatives declined:* checking the compiler out outside the workspace
(`actions/checkout` refuses a `path:` outside it, and a hand-rolled clone would
move the pin assertion off the action that guarantees it); adding `.nitpick` to
the prune names alone (the next tool checked out beside it will not be called
`.nitpick` — TM-146's reason); walking `git ls-files` (the check exists to see
text nobody committed). *Deferred, not declined:* a standing self-check case for
the prune — `TESTING.md` V-20's case list is also the subject of the third
audit's BL-6 (ii), and one change to that list, made once by the close, is
better than two.

### RX-148 — the floor at `c3bdae2` is five symbols, two residue entries are the floor's now, and the `950bb1d` control compiles the floor programs without the arms that compiler does not have

**2026-09-25, cycle 0.0.4b (the plan's PD-2), re-recorded in a commit of its
own as RX-131 requires.** At `c3bdae2` every `failsafe` must name
`StackExhausted` and `MachineFault` — an empty `main` with a bare `(*)` is
refused six times, not four (measured with one bare file at both pins: the
compiler's D-305 checks every function's stack and traps `StackExhausted`;
D-307 routes SIGSEGV, SIGBUS, SIGILL and SIGFPE to `failsafe` as
`MachineFault`). The four floor-level programs — `baseline.npk`, the two
self-check consumers, `tests/conformance/import.npk` — and `selfcheck.py`'s
`FAILSAFE` template carry both arms, at 106 and 107.

**The floor, re-recorded** by `harness/run.py --record-baseline`:

| | `3d15ac9` | `c3bdae2` |
|---|---|---|
| `SYMBOLS.txt` | `npk_dalloc`, `npk_ofd_close` | **+ `__morestack`, `npk_chain_reset`, `npk_trap`** — 5 |
| `EDGES.txt` | 2, both from the drop glue | **+ `npk_failsafe → npk_chain_reset`, `npk_failsafe → npk_trap`** — 4 |
| a syscaller | 3 | 6 |
| syscaller − floor | `{npk_sys6}` | **`{npk_sys6}`** — the claim that matters, unchanged |

**`RESIDUE.txt` loses `npk_trap` and `npk_chain_reset`.** A residue entry is
what this library needs *beyond* the floor, and both are the floor's now —
`failsafe`'s own machinery reaches them — so RX-131's both-directions check
would fail each as permitted and referenced by no program's difference. Their
reasons are kept, dated, in `harness/baseline/README.md`, not deleted with the
lines. RX-120's and RX-131's rules stand; their numbers are dated and stay true
of `3d15ac9`.

**Found in execution, and the plan had not seen it: `rx120.sh`'s `950bb1d` leg
failed.** The historical control compiles the same two programs with the
superseded compiler, and `950bb1d` refuses the two new names
(`NITPICK-RESOLVE-002: cannot find StackExhausted`, and `MachineFault`), so the
script exited 1 and the harness — which runs it as a build step — stopped. The
planner's dry run did not meet it because it ran in a relocated copy of the
tree where that compiler is not found at `../.internal/toolchain/950bb1d/`, so
the leg printed SKIPPED there: **a leg that did not apply read exactly like one
that passed**, which is this repository's most-repeated finding, met by its own
rehearsal. **The decision: the leg compiles each program with exactly those arm
lines removed**, in a mirror of the tree's layout under the script's scratch
directory with `src/` copied beside it, so `syscall_consumer.npk`'s relative
import still resolves. Minus the two lines, both programs are byte-for-byte
what the leg compiled at `ab93eae` (checked with `diff`), so the control
measures what it always measured: **29 / 29, the sets identical, `npk_sys6` in
the floor.** The number of removed lines is asserted — two per file — so an arm
renamed or added later fails by name: seen to fail with one of the two arms
removed from a copy of the tree (`removed 1 arm line(s) … expected 2`), and the
SKIPPED path still prints SKIPPED where the compiler is absent.

*Alternatives:* keep the two entries and exempt them from the unused-entry
check — declined: RX-131's both-directions rule is what stops the list rotting
into permissions nobody needs. For the leg: let it SKIP when the programs
cannot be compiled at `950bb1d` — declined: it would retire the only live
demonstration of RX-120's original measurement while printing a word; keep
separate `950bb1d`-era copies of the two programs as committed files — declined:
the parse sweep judges every `.npk` in the tree as a root at the working pin,
where those copies are refused for the very arms they lack; retire the leg —
declined: removing a control is its own decision, and nothing here asks for it.

### RX-149 — the arm codes, the collision rule, and a deliberate refusal's single line

**2026-09-25, cycle 0.0.4b (the plan's PD-3).** At `c3bdae2` the compiler asks
for identities this repository had never named, and every `failsafe` answers
each with an exit code. **The codes are the ecosystem's, not this
repository's**: `StackExhausted` **106**, `MachineFault` **107**,
`DecreasesViolated` **108**, `LimitViolated` **109** by the orchestrator's
cross-stream table (the board, "THE RE-PIN IS DONE" (3)); `ShiftRange` **115**,
`RequiresViolated` **116**, `EnsuresViolated` **117** proposed by this
repository's planning and confirmed by the orchestrator for every stream before
this subcycle started. They extend the uniform 91–96 run rather than fork it.
`probe13b`/`probe13e`'s `LimitViolated` arm moves off **97**, which means
`DivByZero` in five other arms in this ecosystem. 110–114 and 120–122 are
ordinary failure exits in `tests/unit/vec_unit.npk`, which is why 115 and not
110 comes after 109.

**The arms were driven by the compiler's own `REACH-002` lines, never by a
list**: each root got exactly the identities its refusal named, above its
`(*)`. Measured: 60 roots edited by the plan's script (`StackExhausted` 60,
`MachineFault` 60, `DecreasesViolated` 48, `ShiftRange` 2 — `probe11` and
`byteset_unit`, the two that reach `byteset.npk`'s computed shifts), one by
hand (`failsafe_not_exhaustive.npk`, whose `(*)` is missing on purpose), and the
four floor-level programs in RX-148's commit.

**The collision rule: no test's expected exit equals an arm code unless the
test asserts that trap.** Checked with `git grep -hE '^// expect-exit: [0-9]+'
-- tests`, anchored at the line start: `0` ×26, `92` ×1, `94` ×28, `109` ×1,
`116` ×1, `117` ×1 — every non-zero one its own file's trap — and no ordinary
`exit` anywhere under `tests/` or `harness/` uses 106–109 or 115–117.

**A deliberate `REACH-002` refusal names every arm REACH asks except its
subject, so its ONE `REACH-002` line is its subject.** Rule B-7 checks a
refusal's codes, and a code cannot say which identity it is about: a
refusal that is also missing `StackExhausted` "passes" as a `REACH-002` for
the wrong reason — the masking `probe13a` met at this pin, where it was refused
for the two new arms before `prove` was ever judged. Checked per file after the
sweep: `probe13c` → `RequiresViolated`, `probe13d` → `EnsuresViolated`,
`probe13f` → `LimitViolated`, `failsafe_missing_system_arm` → `WildLeak`, one
line each.

*Alternatives:* 110 for the next code — declined: 110–114 are this repository's
own failure exits (and `nitpick-time`'s `0.1.1.md` proposal of 110 for
`EnsuresViolated` collides with this census, which is why 117 was proposed for
both streams); leaving the refusals without the new floor arms — declined: each
would pass B-7 for a second identity.

### RX-150 — every loop states the measure a reader can defend, and the reading is a committed record

**2026-09-25, cycle 0.0.4b (the plan's PD-4).** The compiler's D-304 makes every
`while` and `when` state `decreases E` or `unbounded`, refused `NITPICK-TYPE-072`
otherwise, and checks the measure in every build, trapping `DecreasesViolated`.
This tree had **61** loops — 11 in `src/core/`, 50 under `tests/` — and none
stated anything.

**The sweep is the compiler's own tool and the decisions are a file.** The
compiler's `decreases_sweep.py` writes only the shape it can prove monotone and
lists every other loop for a reader; `meta/roadmap/0.0/decreases_read.txt` is
that reading — one line per loop the tool listed, applied by the tool's
`--write`, so the decision, its reason and the text it produced are one
greppable record. Measured: **37** loops in the tool's shape, **24** read,
**0** `unbounded`, 0 listed and undecided, 0 stale, 0 errors; the third run saw
61 clausal and 3 stale directives, the three hoists having moved their loops
down a line, as predicted.

**In `src/`, a bound read through a pointer is hoisted into a local**
(`vec_remove`'s `last`, `vec_free_owning`'s `live`) so its `terminate` rows can
discharge — a measure over `v.count` through a pointer stays `open` under the
compiler's frame problem whatever the proof effort — and neither body writes
`v.count`, so the hoist changes nothing at run time. **The doublings are `want -
nc` over a floor of one**, so a zero capacity traps `DecreasesViolated` instead
of hanging — RX-139's hang turned into a trap by the measure itself.

**Every `src/` loop runs under the tests** — the recipe's own rule, *"a wrong
measure traps the first time the loop's head sees it"*, is only a proof for a
loop that runs. Measured by planting a measure that traps on first entry
(`decreases 0i64 - 1i64`) in each of the eleven in turn and building every unit
program and the conformance consumer: all eleven were caught, each by at least
one unit (`bytes_unit` for bytes.npk's five, `byteset_unit` for byteset.npk's
two, `vec_unit` for vec.npk's four, `vec_owning_freed` for the drain as well).

*Alternatives:* `decreases v.count - j` for the pointer bounds — declined: `open`
for ever; a trip budget such as `NREGEX_PROGRAM_INSTRUCTIONS - k` — declined:
D-304 refuses fuel as a measure, because it is not why the loop ends;
`unbounded` for the iterator drivers in `probe12` — declined: they end, and
`unbounded` would claim they may not.

### RX-151 — RX-115's mechanism expired at `94874ce`; its conclusion stands, for a different reason

**2026-09-25, cycle 0.0.4b (the plan's PD-5). Replaces RX-115 in part — its
mechanism — and discharges O-N14.** Found at planning, not by the pin. RX-115
recorded that every file in `src/` compiles at `npkc` exit 0 and every one is
refused by `llc`, because `npkc` never declares `@npk_failsafe`. Measured on
`src/api/api.npk` at every kept pin:

| pin | `npkc` | `llc` | `declare … @npk_failsafe` |
|---|---|---|---|
| `950bb1d` | 0 | **1** | 0 |
| `94874ce`, `0dfddac`, `aaffb87`, `3d15ac9`, `c3bdae2` | 0 | 0 | 1 |

and at `c3bdae2` all thirteen `src/` files compile **and assemble**. **The
conclusion — there is no library object; a library is consumed as source
through a program root (B-0) — still holds, for a different reason**:

```
ld.lld -static bytes_unit.o bytes.o npkrt.o         -> duplicate symbol: npk.bytes.bytes_init
ld.lld -static vec_unit.o vec.o npkrt.o             -> duplicate symbol: npk.vec.vec_oob
ld.lld -static sparseset_unit.o sparseset.o npkrt.o -> duplicate symbol: npk.sparseset.sset_init
ld.lld -static <module>.o npkrt.o                   -> undefined symbol: npk_failsafe, and main
```

— a program's object already carries every function it reaches, as a global, so
the module's object duplicates it. The same shape as RX-120: the evidence
changed and the conclusion did not. **The harness printed the false sentence on
every run** (`run.py`'s `libcheck` message, naming `3d15ac9`), so it was not
optional prose: the message, `build.py`'s and `stages.py`'s docstrings,
`harness/README.md`, `BUILD.md` B-0, `CLAUDE.md` and `CONTRIBUTING.md` now say
what was measured and at which pin. **O-N14** is struck with this number: its
recommendation was implemented upstream, and its expectation that *"the original
pipeline works unchanged"* did not follow.

*Alternative:* leave the sentence and date it `950bb1d` — declined: the harness
printed it on every run as a present-tense fact.

### RX-152 — the `probe13` family follows the language: `prove` is unchecked in a plain build, a live contract charges its consumer one arm, and a live `requires` would change RX-130's trap

**2026-09-25, cycle 0.0.4b (the plan's PD-6).** At `c3bdae2`, `prove`,
`requires` and `ensures` are all live, so the three probes that recorded their
refusal became false claims in their filenames.

- **`probe13a` moves out of `refused/` as `probe13a_prove_unchecked.npk`**: a
  plain build accepts `prove` and lowers it to nothing — `checked`'s IR carries
  no trace of the comparison — so a FALSE `prove` over a run-time value runs to
  exit 0 at −O0 and through `opt -O2`. Only the verified build judges a `prove`
  (the compiler's D-219, refusing an undischarged one `NITPICK-VERIFY-001`).
  The file now asserts the thing a reader must not assume, and it goes red the
  day a plain build starts checking `prove`.
- **`probe13c`/`probe13d` become `…_arm_missing.npk`**, refused
  `NITPICK-REACH-002` for exactly their contract's arm — `RequiresViolated`,
  `EnsuresViolated` — and nothing else (RX-149's rule).
- **`probe13g`/`probe13h` are new**: the contract checked, trapping 116 and 117
  at both optimisation levels, past a `?|` fallback — the violation takes the
  trap route. The same files with the clause deleted exit 60, so each tells
  "checked" from "not checked" by itself.

**This answers the question RX-127 left open and dated** — whether a live
`requires` or `ensures` charges a consumer an arm: **one arm per contract kind.**
It is the fact `OPEN_QUESTIONS.md` Q-6 is decided on. The redirect table is
`meta/roadmap/0.0/0.0.4b.md` §5 step 6 (RX-114's pattern, reused by RX-125 and
RX-127).

**And it retires one supporting reason of RX-130's**, measured here rather than
inferred: RX-130 argued that writing the trap by hand meant *"behaviour does not
change on the day the clause is uncommented"*. With `vec_get`'s comment-form
`requires` made live in a scratch copy, the read of an empty `Vec` traps
**`RequiresViolated` (116), not `OutOfBounds` (94)**, and a consumer that does
not name the new arm is refused `REACH-002`. So uncommenting the clause WOULD
change the behaviour — the trap's identity and every consumer's bill. RX-130's
decision stands on its other reasons for as long as the clauses stay comments,
which is Q-6's to decide; `SAFETY.md` S-23's bullet and `src/core/vec.npk`'s
header carry the dated correction.

*Alternatives:* re-point 13c/13d with no positive twin — declined: B-7 cannot see
which identity a `REACH-002` names, so a refusal alone could pass for a second
missing arm; turn 13c/13d into running programs — declined: the arm-missing
refusal is itself the fact Q-6 is decided on, and P-5 keeps a probe's file;
delete `probe13a` because P-1's question is moot — declined: P-5, and the file
now guards the day a plain build starts checking `prove`.

### RX-153 — `Vec`, `Bytes` and `SparseSet` carry the compiler's field qualifiers, and the containers' four counts are limited by the prelude's `ListLen`
> **SUPERSEDED IN PART by RX-163 (2026-09-25)** — `Bytes.buf` among the `sealed` fields: it is `hidden`, and the
> capacity is read through `bytes_capacity`. Every other qualifier, and `ListLen` on the counts, stands.

**2026-09-25, cycle 0.0.4c (the plan's PD-7).** `Vec.items` is `hidden`;
`Vec.count`, `Vec.cap`, `Bytes.buf`, `Bytes.len`, `SparseSet.dense`,
`SparseSet.sparse` and `SparseSet.count` are `sealed`; and the four counts are
`sealed limit<ListLen> int64` — the compiler's D-313, D-314 and D-308. The
qualifier goes first: `limit<ListLen> sealed int64:count` is
`NITPICK-PARSE-001`, *"expected a type"*, at the column of `sealed` (measured;
the compiler's own `TYPE_REFERENCE.md` §9.1.2 example has the other order, and
its 1.6.0 docs correct it). This is the board's re-pin worklist item 13 — the
container question, answered on safety by the compiler seat on 2026-09-19:
*keep our `Vec` and give it the three properties* — extended by this cycle's
planner to `SparseSet.count`, the same kind of field, which costs nothing more
because every `SparseSet` consumer already owes the arm through `vec.npk`.
`SAFETY.md` gains **S-24a**, and S-23's `Vec` half is the compiler's.

**It supersedes RX-127 in part** — the decision that no `limit<Rules>` appears
anywhere in `src/` — for the four counts and nothing else, and it answers
RX-127's argument rather than overruling it. RX-127 declined a limit on the
ACCESSORS' PARAMETERS: a bound `vec_get` already checks by hand, charged to
every consumer for nothing. This limits the COUNTS, which nothing checked and
which only this library writes, so no consumer can trip the check and it fires
only on this library's own defect. **The evidence is this cycle's worst
defect, re-planted**: the second audit's BL-3 (`vec_oob`'s old body,
`discard(guard[i]);`) under `tests/unit/vec_oob_remove_empty.npk` exits **109,
`LimitViolated`, at the bad write** in the sealed tree, where the unsealed tree
runs on to exit 60 with `count == -1` on a live `Vec` — at −O0 and through
`opt -O2` alike. The same holds for the other two counts, measured by driving
each negative inside its own module: `Bytes.len` 109, `SparseSet.count` 109.
`ListLen` admits the vacant value 0, so `vec_free`'s deliberate poison,
`cap = 0`, is legal and RX-139's guard is unaffected.

**What a consumer can and cannot do, measured at `c3bdae2`.** Five refusals in
`tests/rejection/`, each exactly one code at a measured position:
`NITPICK-TYPE-079` for a write to `Vec.count`, `Bytes.len` and
`SparseSet.count` and for the address `@s.dense` (an address is a write form
whatever the callee does with it — a read-only callee is refused too);
`NITPICK-TYPE-080` for a read of `Vec.items`. Their positive twin,
`tests/unit/sealed_reads.npk`, reads every field a consumer may — `v.count`,
`v.cap`, `b.len`, `b.buf.len`, `s.count`, `s.dense.count`, and `sparse` by
value through `vec_get` — and runs to exit 0 at both levels. **The control**:
against the tree before the declarations all five compile cleanly and fail
their headers, and the twin still runs — which is what makes each a test of the
seal and not of its own file. A consumer's struct literal is refused for every
field it names (`Vec{…}` TYPE-080 plus TYPE-079 twice; `Bytes{…}` TYPE-079
twice).

**The bill**, O-B3's instrument: `vec.npk`, `bytes.npk` and `sparseset.npk`
9 → 10 and `core.npk` 10 → 11 — `LimitViolated`, and nothing else; `byteset.npk`
10 and `limits.npk`, `lib.npk`, `api.npk`, `syntax.npk` 6, unchanged. The 34
roots REACH named gained the arm from their own `REACH-002` lines (RX-149's
rule), and `probe13f`, whose subject it is, stays refused for it alone. S-8 is
untouched while `lib.npk` does not reach `core`.

**What the qualifiers do not close — measured, stated, and not closed here**
(both are the board's question 9, which is the author's):

- **A write THROUGH a sealed pointer field.** A consumer's
  `b.buf.ptr[0i64] = 65u8;` compiles and runs: it writes the pointee, not the
  field. So S-23's `Bytes` half — no `.ptr[` outside `bytes.npk` — stays this
  library's rule and the tree check's.
- **A whole-struct copy.** `Vec<int64>:w = v;` names no field, so neither
  qualifier sees it, and it is a second handle on the block: after
  `vec_free(@v)`, `vec_get(w, 0i64)` reads the free poison (exit 170 at −O0 and
  through `opt -O2`) and `vec_free(@w)` is a double free (95, the third
  audit's N-15, which the cycle's close owns).

And `wild` storage reinterpreted by `=>!` still forges any `Vec` it likes — one
reads `count == -1` — which is the language's opt-out for every checked
property rather than a gap in this one.

*Alternatives declined:* a `VecLen` rule of this library's own (the prelude's
`ListLen` is the bound the compiler's own length facts use, and a second copy
is a second place to disagree); `$ > 0` (`NITPICK-TYPE-077`, measured: a field
rule must hold of the vacant value, and `vec_free`'s poison is 0); `count` and
`cap` hidden (they are read across modules and by tests); `items` merely sealed
(a read of the bare pointer outside `vec` IS the unchecked index RX-111 found,
and `hidden` makes it a compile error); `buf` hidden — declined for now, not
for good (item 13 decided sealed, the residue is stated in S-23 rather than
closed, and question 9 recommends it with an accessor in a subcycle of its
own); no limit at all, S-24 kept as it was (it leaves unchecked a count this
repository has already shipped negative).

---

## The cycle 0.0 close, re-attempted — the third audit's triage (cycle 0.0.5)

*Appended 2026-09-25 by stream 1, working `meta/roadmap/0.0/0.0.5.md` against
[`audits/nitpick-regex-0.0-2026-09-06-third.md`](audits/nitpick-regex-0.0-2026-09-06-third.md),
at pinned toolchain `c3bdae2` under LLVM 20.1.2. The audit measured at `3d15ac9`;
every number below was re-taken at `c3bdae2` unless it says otherwise.*

### RX-154 — the `pending-until:` marker names the exit it excuses, a reviewed list names every pending unit, and the commit is a label nothing reads
> **SUPERSEDED IN PART by RX-157 and RX-159 (2026-09-25)** — its sentence that the one other route out of
> the count "is closed by the language" (a sibling's `/* */` took a unit out, BL-7), and its scoping of
> `RESIDUE.txt`'s unused direction out of every inner run (N-20). The marker, the list and cases 11–13 stand.

**2026-09-25, the third audit's BL-6.** It supersedes RX-146 in part — B-5b's
one-token grammar, and the claim that the harness notices "the day the pin moves
past the named commit". RX-146's decision stands: a unit that is correct and red
because the pinned compiler is the defect is committed with a marker, run,
printed, counted as neither a pass nor a failure, and reddens the day it meets
its expectation.

**What the audit found, three full runs each exit 0.** M1: a marker naming a
string that is no commit was accepted and changed nothing — the commit was never
read, so the sentence in `expect.py` claiming the run notices the re-pin was
false. M2: a pending unit made to fail for a DIFFERENT reason (94, where its
leak gives 92) stayed pending; the marker excused any exit but the expected one.
M3: an ordinary unit given a wrong expectation plus one marker line left the
denominator — `140/140`, GREEN — which defeats the self-check's own case 1. No
self-check case covered the mechanism at all.

**Reproduced at `c3bdae2` before anything was changed**, each a full run over a
clone of this subcycle's first commit with the one-token marker planted:
M3 on `tests/unit/bytes_oob_get_empty.npk` (`expect-exit` 94 → 77) — **157/157,
GREEN, exit 0**; M2 on `tests/unit/bytes_copy_string_empty.npk` (a trapping
`bytes_get` added at the top of `main`) — **157/157, GREEN, exit 0**, its
PEND line reading *"this tree gives 94"*.

**The decision, one part per remedy the audit named.**

1. **The marker names the exit it is pending on**: `// pending-until: <commit>
   exit <N>`. A pending unit that gives any other exit, or hangs, is a failure —
   *"PENDING ON A DIFFERENT FAILURE"* — which is rule B-7's reasoning applied to
   this marker: a unit held only to "it failed" passes for the wrong reason. A
   marker pending on the exit the file expects is unreadable, because it would
   excuse the pass.
2. **Every pending unit is a line in `harness/baseline/PENDING.txt`**,
   `path<TAB>commit<TAB>exit<TAB>reason`, **checked both ways**: a marker the list
   does not name leaves its unit IN the denominator as a failure, and on a full
   run a line no pending unit matches is a failure. Taking a unit out of the count
   is then two edits in two files, one of them a reviewed line with a reason —
   `RESIDUE.txt`'s shape (RX-131). The list is empty today.
3. **The commit is a label.** It must have a commit's shape, 7 to 40 lowercase
   hex digits, and it is never resolved: this runner has no compiler checkout to
   resolve it against — W-18 and RX-007 keep the compiler's tree out of it — and
   resolving it would buy an answer the unit's exit already gives. The two
   sentences that said otherwise, `expect.py`'s docstring and B-5b, are
   corrected; `ci.yml`'s was rewritten at cycle 0.0.4b.
4. **Three self-check cases, one per red the mechanism owes** — 11, a marker
   the list does not name (M3); 12, a listed unit failing another way (M2); 13, a
   marker that has outlived its reason — so `TESTING.md` V-20's list grows with
   the mechanism, and each was seen to fail against a harness with its own check
   removed.

**Re-measured after, same plants in the new grammar**: M3 — **157/158, exit 1**,
*"is NOT ON THE REVIEWED PENDING LIST"*; M2, its line in the list — **157/159,
exit 1**, *"PENDING ON A DIFFERENT FAILURE -- the marker names exit 92 and this
tree gives 94"*, and the list line reported as matching no pending unit.

**Why the denominator is not asserted as a number**, which was the audit's
fourth remedy as it wrote it. A committed total changes with every test added,
so it would be edited on every commit and read by nobody; the list changes only
when a unit leaves the count, which is the event the audit is about. The one
other route by which a `program`-stage unit could leave the count — a sibling
importing it, which the `npkg`-compatible runner then does not run standalone —
**is closed by the language**: measured at `c3bdae2`, a file with `main` and
`failsafe` imported by another is refused `NITPICK-RESOLVE-013` (D-248), so the
importer goes red.

**And `V-20`'s list, which this grows, was out of step with `selfcheck.py` in
both directions**: it named an oracle case the runner never carried and omitted
four live ones (4, 8, 9, 10). Reconciled case for case — fifteen, eleven live and
four pending, the oracle case added as pending until 0.5 — and the run's GREEN
message now prints the counts from `CASES`: it said *"EIGHT"* and *"eleven"* as
prose, which is the stale-message shape `PLAYBOOK.md` §9 names. (`TESTING.md` §10's
performance rule, which shared the number V-22 with §8's since RX-145, is V-23:
nothing cited it, and two records cite the other.)

**Mutation-testing the three new cases found a hole in the self-check itself,
and it is the larger finding.** With case 12's own check deleted, case 12
PASSED: its required phrase was also printed by the PEND line, and its required
non-zero exit came from somewhere else — `RESIDUE.txt`'s unused-entry direction,
which `_lib` copies into every fixture tree and which no fixture can satisfy, so
**every inner run of every case was red for a reason that was not its case's**.
The exit-code half of the self-check had been vacuous since RX-131; `must_say`
alone was telling detection from noise, which 0.0.5's §C had seen for case 9 and
read as the mechanism working. Two changes: the unused-entry direction is scoped
to the real tree (skipped under `--selfcheck-inner`, the flag that already scopes
the tree checks and `rx120.sh` for the same reason, `PLAYBOOK.md`'s *"a
named-exemption list is a statement about one tree"*), and case 12 requires
*"PENDING ON A DIFFERENT FAILURE"*, which only its red prints.

*Alternatives declined:* retiring the mechanism because it has no user today — it
would be rebuilt under a deadline the next time a compiler defect needs a
correct-and-red unit, which is how BL-6's machinery was built — and DEF-25, the
defect it was built for, was found by this repository's own audit while the
compiler was mid-cycle, as it still is; resolving the
commit against the compiler's history — a dependency on another repository's
checkout for a label a human reads; a committed total of judged units (above);
the pending exit written in the list only — the marker is what a reader of the
unit sees, so it must say which failure it excuses.

### RX-155 — `Vec<T>` is for a `T` that owns nothing, because nothing in the language keeps an owner out; the restriction is stated per verb, measured per verb, and enforced over `src/`
> **SUPERSEDED IN PART by RX-158 (2026-09-25)** — the check's mechanism, a denylist of nine words the fourth
> audit walked twelve shapes past (N-18), and the unqualified "enforced over `src/`" made on it. The rule stands;
> the check is default-deny.
> *(A precision added the same day, by the subcycle that wrote it, before any
> verifier saw it: "Every `Vec` the specification declares already holds one"
> is true of `Inst`, `ByteSet`, `uint8`, `HirNode`, `ClassRange` and the
> engines' integers, and not established of `Literal` and `GroupInfo`, which
> `HIR.md` §2 names without fields — nor of the parser's `Frame`. S-23a now
> requires their cycles to shape them as H-2 shapes group names, as offsets into
> a `Bytes`; `SAFETY.md` S-23a says so. The decision is unchanged.)*

**2026-09-25, the third audit's BL-5.** It supersedes in part RX-031, RX-110,
RX-123 and RX-125 — each one's clause crediting `TYPE-046` with refusing,
forcing or forbidding an owning element in an array — and none of their
decisions, which stand on their other reasons.

**The false belief, and what the compiler does instead.** Four sites said a copy
of an owning element out of a `Vec` is "refused, TYPE-046" — `vec.npk`'s
`vec_get` comment, `vec_pop`'s "for `vec_get`'s reason", `0.0.4.md`'s Rule, and
`vec_unit.npk`, which cited the refusal as its reason not to read an element
back. `TYPE-046` is D-183's move-required diagnostic: a copy of an owning PLACE
must be spelled `move(...)`. `pass` moves implicitly, and D-264 checks a generic
body once with `T` treated as owning, so a body that compiles at any `T`
compiles at every `T` and nothing is refused. Re-measured at `c3bdae2`:
`Vec<string>`, one push, `vec_get` twice — the second read is empty and `count`
is still 1, **exit 70**; the same at `int64`, **81**; both at −O0 and through
`opt -O2`.

**Its extent is wider than the four sites**, because the belief underneath is
that the LANGUAGE keeps a stored value POD. Measured: a `string[2]` and a fixed
array of a struct holding a `string` compile, link and run at `950bb1d`,
`3d15ac9` and `c3bdae2` (exits 42 and 43 at all three); at `c3bdae2` so do a
`Vec` of that struct (41) and `Bytes[2]` (41). Swept with `git grep -n -i
'TYPE-046'` and a second phrasing (`owning field|forces it|forcing the|cannot be
stored|live in an array`): the live sites crediting the language are
`SAFETY.md` §1's move-only row and S-22's *"it is TYPE-046 forcing the
representation"*, `VERIFICATION.md` §3's *"so no program is aliased"*,
`CLAUDE.md`'s compiler-constraints bullet, the comments in `vec.npk` (four),
`sparseset.npk`, `bytes.npk`, `core.npk` and `hir.npk`, two units and two probe
headers — each corrected with a dated note. The candidates that are TRUE were
left: a binding-to-binding copy of an owner IS refused (`probe01`, `probe02`,
`probe03`), and `vec_fill<T>`'s refusal is real. So is a second false reason in
the same file: `vec_free_owning` was said to be separate from `vec_free` because
*"a `move` out of an element is refused for a `T` that does not own"* — but
`vec_free_owning::<int64>` compiles and runs at `3d15ac9` and `c3bdae2`, since a
`move` of a scalar is its copy. The two stay apart for cost: O(1) against
O(`count`).

**What each verb does at an owning `T`**, measured at `c3bdae2` with the
runtime's `NPK_HEAP_STATS` — 1 000 rounds, two 257-byte strings per round,
`vec_free_owning` at the end of each — and identical at −O0 and `opt -O2`:

| verb exercised mid-round | `peak_live` | |
|---|---|---|
| none — the control | 610 | flat |
| `vec_pop`, bound and dropped | 610 | correct |
| `vec_insert` of a third string | 867 | correct (three per round, all dropped) |
| `vec_get`, bound and dropped | 610 | "correct" only because it MOVED the element out |
| `vec_set` over a live element | 257 610 | the overwritten element orphaned, every round |
| `vec_remove`, `vec_swap_remove` | 257 353 | the removed element orphaned |
| `vec_truncate(0)`, `vec_clear` | 514 096 | both elements orphaned |

**The decision — `SAFETY.md` S-23a.** `Vec<T>` is for a `T` that drops nothing
and holds no block of its own. At such a `T` every verb is correct and a move is
a copy, and every `Vec` the specification declares already holds one — `Inst`,
`ByteSet`, `uint8` (C-1), `HirNode`, `ClassRange`, `Literal`, `GroupInfo` (H-2,
whose group names are offsets into a `Bytes`), and the engines' integers — so
the rule costs the design nothing. It is **stated at every verb** in `vec.npk`,
with a per-verb table in its header; **measured by one unit per verb** at
`Vec<string>`, each seen to fail against a planted `vec.npk` first —
`vec_owning_get_moves_out` (the second read empty, exit 0; planted: 22), five
orphaning units required to meet `HeapOom` under the managed-half cap (planted
with the compiler's `List<T>` discards: all five exit 0), and
`vec_owning_pop_moves_out` and `vec_owning_insert_moves`, ownership-correct at
0 under the same cap and checking order as well (planted orphans: 92; planted
misorders: 31, 41); and **enforced over `src/`** by
`check_vec_elements_own_nothing`, which refuses a `Vec<…>` whose element names
an owning type, directly or through a struct or enum declared under `src/`.
`tests/` is out of its scope because the units above instantiate `Vec<string>`
on purpose.

**The removing verb the audit offered is declined, and its shape is recorded.**
The audit's remedy (ii) was to rename `vec_get` to say it removes, or to restrict
it and add the removing verb the API lacks. Restricted, the removing verb has
nothing to remove. The day a cycle needs an owning element it lifts S-23a by a
decision, and the compiler's own `List<T>` at `c3bdae2` is the shape:
`list_remove` and `list_swap_remove` return the element, `list_truncate` and
`list_clear` drop what they discard, and there is no by-value get — `l[i]` is a
bounds-checked place. A scratch `vec.npk` given those discards was measured
turning the five orphaning units from 92 to 0, so the shape is known to work
here.

*Alternatives declined:* **making every verb ownership-correct now** — `vec_get`
still could not be (a by-value read of an owner is a move or a clone, and a
`Clone` bound puts a `Result` on the read), so the restriction would still be
needed for it, and `vec_truncate`/`vec_clear` would turn O(`count`) for every
POD caller to serve an owning caller that does not exist; **a marker-trait bound**
(`vec_get<T: Pod>`) — it would refuse `vec_get::<string>` at compile time, but
every element type would need an impl whose claim nothing verifies, and it is a
public API change for a rule a tree check enforces over the code that ships;
**renaming `vec_get`** — it is a plain read at every `T` this library may use;
**documentation alone** — the audit's (iii), done, and not enough: a rule a
later cycle can break by writing one `Vec<string>` is a rule that asks for care.

### RX-156 — a double free traps `OutOfBounds` at this library's guard, which is a TRADE against the language's own code; and the guard reaches one binding
> **SUPERSEDED IN PART by RX-160 (2026-09-25)** — its premise that R-8's capture copy at cycle 0.8 is the one
> place the specification copies a `Vec` (false three ways, BL-8), the reach it gave N-15, and N-15's disposition:
> DEFERRED TO 0.0.4d, before the close, by the author's decision on question 9. The guard and the 94 stand.

**2026-09-25, the third audit's N-14 and N-15.** It supersedes RX-144 in part —
its reading that the free paths' 95 "reported a broken heap invariant where
what happened is that a freed container was used", i.e. reported the wrong
thing. The decision — the `cap <= 0` guard heads `vec_free` and
`vec_free_owning`, and a dead `Vec` stops with `OutOfBounds` — stands.

**Read at `c3bdae2` with `git show`, not from a document.** `runtime/npkrt.ll`'s
trap table: `-4099 OUT_OF_BOUNDS` is *"a slice/array index past the end"*;
`-4102 HEAP_INTEGRITY` is *"double-free, foreign/misaligned/null pointer to
dalloc/ralloc, corrupted header or torn guard, or a UAF caught by a freed slot's
magic"*. The prelude: `OutOfBounds = 4099i32`, and `Unreachable = 4102i32`,
*"`#unreachable()` reached, and the runtime's integrity defects"*. So 95 was the
language's own code for a double free, reported from the allocator's check:
**right thing, wrong place** — where `vec_push`'s and `vec_insert`'s 91 was the
wrong thing.

**94 is kept, and the rationale now says what it trades.** Kept: the stop is
earlier, it is this library's, it names the value, and every use of a dead
`Vec` — growth paths since RX-139, free paths since RX-144 — stops with one
identity; and the guard is what keeps `vec_free_owning` from running destructors
over a freed block, which is RX-144's stronger reason and unaffected. Traded: a
consumer's `failsafe` can no longer tell a double free from an out-of-range
index in this library's containers. Stated in `vec.npk`'s header where RX-144's
paragraph is.

**N-15 — the guard reads the `cap` of the header it is handed, so it reaches the
same binding only.** A whole-`Vec` copy keeps the old `cap`. Measured at
`c3bdae2`, −O0 and `opt -O2`: `Vec<int64>:w = v;` then `vec_free(@v)` and
`vec_free(@w)` — **95**; the same at `Vec<string>` through `vec_free_owning`,
which walks the freed block first — **95**; and `vec_get(w, 0)` after
`vec_free(@v)` reads the free poison — **170**. The unqualified sentence is
qualified in place. **The finding is OPEN**, tracked to the board's question 9
and RX-153: making `Vec` move-only by construction closes all three, and the
alternative — accept and document it as the `wild` regime's behaviour — is the
author's to choose. The one place this library's specification copies a `Vec` is
`ENGINES.md` R-8's per-thread capture slots, cycle 0.8, and the spelling correct
under either answer is an element-wise copy into a fresh `Vec`.

*Alternatives declined:* **trapping `Unreachable` at the guard** (`#unreachable()`)
so the identity matches the language's — it would split the dead-`Vec` stop into
94 for growth and 95 for free, and change an identity every consumer's
`failsafe` sees, for a distinction no consumer can act on; **removing the guard
and letting `dalloc` answer** — it would reopen `vec_free_owning`'s walk over a
freed block.

---

## The cycle 0.0 close, re-attempted again — the fourth audit's triage (cycle 0.0.5)

*Appended 2026-09-25 by stream 1, working `meta/roadmap/0.0/0.0.5.md` against
[`audits/nitpick-regex-0.0-2026-09-25-fourth.md`](audits/nitpick-regex-0.0-2026-09-25-fourth.md),
at pinned toolchain `c3bdae2` under LLVM 20.1.2. Every number below was taken
here, at `c3bdae2`, and every audit measurement it rests on was reproduced
before anything was changed.*

### RX-157 — the harness reads Nitpick source ONE way, the compiler's, and a file that declares `main` is never skipped
> **SUPERSEDED IN PART by RX-165 (2026-09-25)** — its claim that the reading was the compiler's (every caller
> opened files in text mode, a lone CR ending a line, and a path was its literal's text), and its second part's
> "holds whatever the reader gets wrong next", which asked the same reader. The one reader and its lexer mirror stand.

**2026-09-25, the fourth cycle 0.0 audit's BL-7.** It supersedes RX-154 in part
— its sentence that the one other route by which a `program`-stage unit could
leave the count *"is closed by the language"*, and so its *"taking a unit out of
the count is then two edits in two files"*. RX-154's marker, list and cases
stand.

**Reproduced here before anything changed**, a full run over a clone of
`4420c45`: `tests/unit/bytes_oob_get_empty.npk`'s `expect-exit` 94 → 77 (it
exits 94), and in its sibling `tests/unit/vec_unit.npk`, after
`mod:vec_unit;`, a `/* */` block holding `use "bytes_oob_get_empty.npk".*;`.
The unit suite judged **43** units where the baseline judged 44, and the run
printed **`173/173 unit(s) passed`, GREEN, exit 0** — the red unit's only line
the parse sweep's `ok`. One edit, in a file other than the red one: no marker,
no `PENDING.txt` line.

**Why.** The program suites' "imported by a sibling" skip — `npkg`'s rule: a
file another file in the same suite imports is judged through its importer —
took an import to be any line whose stripped text began `use "`, and a line
inside `/* */` is such a line. The compiler reads it as a comment: the audit's
control compiles, links and runs it, and a REAL `use` of a file declaring `main`
is refused `NITPICK-RESOLVE-013` (D-248). So RX-154's argument was right about
the compiler and wrong about this harness. And the harness held **three** import
readers that disagreed — `stages._uses` and `build.reaches_src` matched `use "`
only and missed `pub use`, `treecheck._USE` matched both, none skipped a comment
or a string — plus a blanker, `treecheck._blank_prose`, that knew `//` and `"`
and nothing else, so a `'"'` character literal hid the rest of its line from
three checks (N-18's M12).

**The decision — the audit's remedies (1), (2) and (3).**

1. **One reading of source, `harness/lexical.py`**, mirroring the compiler's
   lexer at `c3bdae2` — `src/frontend/lexer.npk` read with `git show`, and
   `LEXICAL_REFERENCE.md` §2, §6.3 and §6.4: `//`; `/* */`, which does not nest;
   `"…"` with `\` escapes, ended by a newline; `""`; `"""…"""`; `r"…"` when the
   `r` begins a token; `'x'` with its escapes and the lexer's resync; and
   templates, whose text is literal and whose `&{…}` interpolations are code.
   `imports()` reads a `use` the way the parser's `p_parse_import` does — the
   keyword, then a plain string literal — with `pub` before it; `blank()`
   replaces every comment and literal with spaces and keeps every newline. The
   program suites' skip, B-2's reach and every tree check read through it, and
   there is no other reader.
2. **A file that declares `main` is never skipped.** It is a program, and a
   program is judged. D-248 already refuses a real import of one, so the
   exception costs nothing legitimate — and it holds whatever the reader gets
   wrong next, which part 1 cannot promise about itself. `npkg` has no such
   exception and needs none while its reader is the compiler's own.
3. **Self-check case 15** is the audit's plant — a red unit named only inside a
   sibling's `/* */` — and requires the run to go red naming it. **Case 18**
   feeds `lexical.py` one text holding every form, and requires exactly the
   imports the compiler reads and exactly the code it sees.

**Measured.** Case 15 over copies of the harness: the old reader alone restored
— it still passes, part 2 holding; the `main` exception alone removed — it still
passes, part 1 holding; both — *"THE HARNESS PASSED IT"*. The two defences are
independent, which is the point of keeping both. Case 18 with the character
literal's handling removed, and separately the block comment's: each fails
alone. On the real tree every denominator is unchanged — 63 `use` edges over 13
files, the same units scanned by B-2, every check green over the same files —
because the tree holds no block comment, raw or block string, template or
character literal in code (swept, 95 `.npk`).

**And the lexer disagrees with its own specification in one place**, found while
mirroring it: a block string closes at the first `""`, not at `"""` as §6.3's
grammar says, so `"""a""b"""` is refused `NITPICK-LEX-005`. `lexical.py` follows
the lexer, because agreeing with the compiler is its purpose; probe 15
(`tests/probe/refused/probe15_block_string_close.npk`) records the refusal, and
reddens the day the two agree — which is also the day `lexical.py` must change.
Nothing here uses a block string, so it blocks nothing (W-27).

The audit's remedy (4) — RX-154, `run.py`'s docstring, `PENDING.txt`'s header
and 0.0.5 §10's sentence — is done: the first by this supersession and its
marker, the next two in place, the last in §11, because §10's REPORT block is
W-28's.

*Alternatives declined:* **asserting per suite that the judged and pending units
equal the files declaring `main`** (the audit's alternative in its remedy 1) —
part 2 makes skipping a program impossible rather than detected, and a count
that cannot differ is a check of nothing; **blanking comments in the old line
reader only** — it leaves three readers, `pub use` unseen, and the next form (a
string, a template) as the next audit's finding; **reading imports from the
compiler** — `npkc` has no mode that prints a module graph (its usage line at
`c3bdae2`: a root, `-o`, `--obligations`, `--elide`, `--extra-picky`), and W-18
keeps the compiler's tree out of this harness.

### RX-158 — `check_vec_elements_own_nothing` is DEFAULT-DENY: it clears only what it can see owns nothing
> **SUPERSEDED IN PART by RX-166 (2026-09-25)** — three details of its mechanism: a macro splice was cleared as
> the POD type it was named after, `fixed`, `nodrop` and `move` were not stripped as qualifiers, and every
> parenthesis in an enum body was read as a payload. Default-deny, its scalars and its twelve shapes stand.

**2026-09-25, the fourth cycle 0.0 audit's N-18.** It supersedes RX-155 in part
— its check's mechanism (a denylist of nine words matched in the element's
text, following only Capitalised names declared under `src/`, the first
declaration of a name winning, `vec.npk` skipped whole) and the unqualified
*"enforced over `src/`"* made on it in `SAFETY.md` S-23a and `0.1/0.1.0.md`.
RX-155's rule stands; so do its verbs, units and table.

**What the audit found, reproduced here** by running the committed check over a
copy of `src/` with one change each: all twelve of its shapes PASS it — a
lowercase struct holding a `string`; the prelude's `Path` and `ByteReader`; an
enum with a `Path` payload; a struct holding an `arena`; a `wildx` pointer; a
generic `Stack<T>` over `Vec<T>`; a generic function's `Vec<T>` local;
`Vec <string>` with a space; a non-generic `Vec<string>` appended to `vec.npk`;
a POD `Frame` shadowing an owning namesake; and a `'"'` earlier on the line —
while its own control, `Vec<string>`, fails it. Eleven compile and run, and six
show BL-5's move-out (the audit's table). The compiler's owning kinds at
`c3bdae2` are twelve and the denylist named four.

**The decision — default-deny, the audit's remedy.** An element passes only if
every name in it is one of the language's non-owning scalars, or a struct or
enum declared under `src/` whose fields and payloads pass the same way. The
scalars are read at `c3bdae2` from `LEXICAL_REFERENCE.md` §4's `BuiltinType`
and `src/frontend/types.npk`'s `type_drops_recorded`: the integer,
balanced-ternary, fixed-point and floating families, `bool`, the characters, and
the kernel ids and flag families that function lists as plain integers. A
pointer, a slice, `wild`/`wildx`/`stack` storage, any other builtin, a prelude
type, a bare type parameter and a name the check cannot resolve all FAIL, each
with its reason. It examines `Vec<…>` with or without a space before the bracket,
**and every `vec_…::<…>` turbofish**, which instantiates a `Vec` without
writing one; it judges EVERY declaration of a name, because it does not resolve
imports; it exempts only `vec.npk`'s own `Vec<T>` over that file's type
parameter; and it reads source through RX-157's `lexical.py`.

**Measured.** The twelve plants fail, each naming why; the third triage's four
positive plants still fail; its comment plant and POD plant still pass, and so
do four more controls — a payload-less enum, an enum with scalar payloads,
`Vec<ByteSet>`, and `Vec<string>` inside a raw and a plain string. A slice
element and an owning turbofish fail. On the real tree it clears four element
types — `SparseSet`'s two `Vec<int32>` fields and its two
`vec_init_zeroed::<int32>` calls — and exempts fifteen in `vec.npk`.

**What it still cannot see, stated rather than implied:** an instantiation. A
generic struct is judged with its parameters unbound, so it fails; teaching the
check to substitute is the widening a decision would make if a cycle needs one.
Today that costs nothing — `src/` has no generic outside `vec.npk`.

*Alternatives declined:* **narrowing S-23a, RX-155 and `0.1.0.md` to what the
denylist enforced** (the audit's other remedy) — it leaves a check twelve shapes
wide of its rule on the day cycle 0.1 writes its first `Vec<Frame>`; **a reviewed
list of cleared prelude types, now** — no element under `src/` needs one, an
empty list checked both ways is N-20's shape with nothing to check, and its
first entry should be a decision; **the compiler's own ownership predicate** —
reachable only by building the compiler, which W-18 forbids.

### RX-159 — a pending unit is observed on every leg and every run, and both reviewed lists are held both ways in any tree that owns one

**2026-09-25, the fourth cycle 0.0 audit's N-19 and N-20.** It supersedes RX-154
in part — its scoping of `RESIDUE.txt`'s unused-entry direction out of every
self-check run by `--selfcheck-inner`, which left that direction with nothing
testing it. It amends `BUILD.md` B-5b.

**N-19.** `_program_like` returned a pending unit before its optimised leg was
built, so it had no `opt -O2`, no B-2 re-scan of the optimised object (where
`opt` MINTS libcalls), no optimised run, and one run whatever `stress` said —
while the summary counted it among the units B-2's scans ran on and GREEN said
every program agreed with itself under −O2. **The decision:** a pending unit is
built, scanned and linked on every leg an ordinary unit is, and run `stress`
times on each; it is PENDING only when every run on every leg gives the exit its
marker names, STALE only when every one meets its expectation, and RED
otherwise. **Measured on `stages._pending` itself**, with stand-in executables:
a unit giving the named 92 at −O0 and 94 through −O2 was PENDING under the
committed code and is red now; one whose second of three runs gives 94 was
PENDING (one run) and is red now. **Self-check case 11** now requires its
pending unit to have been seen *"through opt -O2"*, and with the −O2 leg removed
from the pending path it fails alone.

**What is still keyed on the exit alone**, stated in `expect.py` and B-5b: a code
is an identity, not a cause. A unit pending on 92 is excused for any `HeapOom`
under its cap, and one pending on a trap's code for any trap of that identity;
where the defect allows, a pending unit should exit with a code of its own.

**N-20.** Neither reviewed list's second direction had a case: deleting either
left the self-check green. **Case 16** — a `PENDING.txt` line naming a unit
with no marker — and **case 17** — a fixture's own `RESIDUE.txt` holding an
entry no scanned program references — must each redden the run. For case 17
the unused direction now runs in any tree that holds a list of its own, and is
skipped only in a self-check fixture that borrowed the library's list byte for
byte — a statement about another tree, which is RX-154's finding and stays
right. The real run is never an inner run, so it is always held. **Measured:**
each direction deleted in a copy of the harness fails its case alone; the
scoping put back on the flag fails case 17 alone.

*Alternatives declined:* **one observation of a pending unit** — the observation
taken once, at −O0, is the one that excused the −O2 leg; **a fixture list written
per case for cases 8 and 9** — their programs' symbols move with the pin, so the
lists would redden the self-check at re-pins for reasons not their own;
**stating the residue direction as unguarded** (the audit's other remedy) — a
guard costs one case.

### RX-160 — N-15's premise was false and its reach was wider; the author has decided it: `Vec` becomes MOVE-ONLY BY CONSTRUCTION at 0.0.4d, before cycle 0.0 closes
> **SUPERSEDED IN PART by RX-161 and RX-162 (2026-09-25)** — its hand-off's count, *"seven units that must STOP
> COMPILING"* and the swap beside them (the tree held seven `*_alias_*` units in all: six defect shapes and the
> swap), and its consequence that move-only *"changes `vec_get`'s signature and every by-value read in
> `src/core/`"* — measured false. Five of the six stop compiling; the sixth is a loan. The corrections and the
> reach stand.

**2026-09-25, the fourth cycle 0.0 audit's BL-8, and the author's answer to the
board's question 9, the same day.** It supersedes RX-156 in part — its statement
that *"the one place this library's specification copies a `Vec` is
`ENGINES.md` R-8's per-thread capture slots, cycle 0.8"*, the reach it gave
N-15 (*"a whole-`Vec` copy"*), and N-15's disposition, *"OPEN … the author's to
choose"*. RX-156's decisions on the guard and on 94 stand.

**The premise was false three ways**, read in the specifications rather than
inherited from the triage that stated it:

- `COMPILE.md` C-1 declares `Program = { Vec<Inst>; Vec<ByteSet>; Vec<uint8>; … }`
  *"copyable, comparable, and dumpable"* — a binding copy of one is three
  whole-`Vec` copies — and cycle 0.6 builds it (`roadmap/ROADMAP.md`);
- `ENGINES.md` R-5 swaps two `SparseSet`s, two `Vec` headers each, every
  haystack byte, at subcycle 0.7.0 (`roadmap/0.7/README.md`);
- R-8's capture copy is subcycle 0.7.2, not cycle 0.8, which is the lazy DFA;
- and from cycle 0.1 any struct holding a `Vec` is silently copyable — the
  parser holds a `Vec<Frame>` (`SYNTAX.md` Y-9).

The third triage's sweep phrases could not match *"copyable"* or *"swapped"*,
and the premise reached the board and a dispatch without being checked.

**The reach, measured at `c3bdae2`, −O0 and `opt -O2` alike, and committed as
units** so the next reader runs it rather than reads it:

| shape | unit | result |
|---|---|---|
| `Vec<int64>:w = v;`, then `vec_free(@v)` and `vec_free(@w)` | `vec_alias_double_free` | **95**, `Unreachable` — the guard sees `w`'s `cap` |
| the same, then `vec_get(w, 0)` | `vec_alias_read_after_free` | the `0xAA` free poison, no trap |
| a by-value `Vec<int64>` parameter the callee frees through | `vec_alias_param_free` | the caller's next read is the poison — no copy binding written |
| a struct holding a `Vec` (C-1's `Program` shape), copied | `vec_alias_struct_copy` | the copy's read is the poison |
| `SparseSet:t = s;`, then `sset_free` of both | `sparseset_alias_double_free` | **95** |
| the same, then `sset_contains(@t, 3)` and `sset_len(@t)` | `sparseset_alias_read_after_free` | **FALSE and 1: a member reads as absent while the count says one — a silent wrong answer in the Pike VM's thread set** |
| R-5's swap through a temporary, each block freed once | `sparseset_alias_swap` | 0 — harmless: the alias is never used |
| `Bytes:c = b;` | `tests/rejection/bytes_copy.npk` | refused `NITPICK-TYPE-046`: `Bytes` holds a `buffer` and is move-only already |

**The decision.** The premise and the reach are corrected wherever the tree
states them: RX-156, by this supersession and its marker; `src/core/vec.npk`'s
two paragraphs; `SAFETY.md` §5.3's two notes; `VERIFICATION.md` §3; `COMPILE.md`
C-1's *"copyable"*, flagged; `ENGINES.md` R-5 and R-8; `roadmap/0.7/README.md`;
`roadmap/0.0/0.0.5.md` §11, for §10's sentences and its REPORT block (W-28);
and `roadmap/0.1/0.1.0.md`, which carries N-15.

**N-15 is DEFERRED TO 0.0.4d, BEFORE CYCLE 0.0 CLOSES, by the author's decision
on the board's question 9 (2026-09-25): `Vec` becomes move-only by
construction.** The design and its plan are 0.0.4d's, from a planner dispatched
after this subcycle reports; nothing here implements it. What this subcycle
hands it: seven units that must STOP COMPILING — `TYPE-046`, as `bytes_copy.npk`
shows a `Bytes` copy already does — and become rejection fixtures; one,
`sparseset_alias_swap`, that must still run once spelled with `move(...)`; and
the consequence the audit named, that `vec_get` takes `Vec<T>` by value and
`sparseset.npk` reads `vec_get(s.sparse, k)` that way, so move-only changes
`vec_get`'s signature and every by-value read in `src/core/` — this cycle's own
deliverable, which is why it lands before the close and not after.

*Not decided here:* the shape of move-only — an owning field behind `items`, a
marker the compiler treats as owning, or another — which is 0.0.4d's plan's to
measure and choose.

---

## `Vec` move-only by construction — cycle 0.0.4d

*Appended 2026-09-25 by stream 1, working `meta/roadmap/0.0/0.0.4d.md` at pinned
toolchain `c3bdae2` under LLVM 20.1.2. Drafted at planning as PD-8 … PD-11; every
number below was measured at `c3bdae2`, at −O0 and through `opt -O2`.*

### RX-161 — `Vec` is MOVE-ONLY BY CONSTRUCTION: a hidden zero-length array of an owning type makes the compiler treat it as an owner, and the five COPY shapes stop compiling

**2026-09-25, cycle 0.0.4d (the plan's PD-8) — the author's decision on the board's
question 9 (2026-09-25 15:45), whose shape RX-160 left to this plan.** It supersedes
RX-160 in part: its count — *"seven units that must STOP COMPILING"* and the
swap beside them, eight, where the tree held seven `*_alias_*` units in all, six
defect shapes and one control — and, with RX-162, its consequence for
`vec_get`.

**The shape.** `struct:Vec<T>` ends in `hidden string[0]:move_only`, filled with
`[]` (the compiler's D-139, the zero array) by `vec_init` and `vec_init_zeroed`.
`type_drops_recorded` answers an array by its element whatever the length, and
layout marks a struct owning when any field is (D-183) — so `Vec<T>` owns at
every `T`, and an owner is move-only (TYPE-046). `SparseSet`, and any struct
holding a `Vec`, owns by containment. **It costs nothing measurable:**
`#size_of<Vec<int64>>()` stays 24 and `SparseSet` 56; the generated drop walks no
elements and frees nothing, so the block stays `wild`, `vec_free` is still its
release, and a `Vec` never freed still traps `WildLeak` at `exit 0` (96); no
module's `failsafe` bill moves (10, 10, 10, 10, 6, 11, 6, 6, 6).

**Measured.** The five copy shapes — `vec_alias_double_free`,
`vec_alias_read_after_free`, `vec_alias_struct_copy`,
`sparseset_alias_double_free`, `sparseset_alias_read_after_free` — are each
refused `NITPICK-TYPE-046`, exactly once, and move to `tests/rejection/`.
`sparseset_alias_swap`, spelled with `move(...)` as three locals and as two
fields of a struct through a pointer flipped a thousand times, runs 0.
`vec_moves` — a whole-`Vec` move, a struct holding one moved, loans, and
`ENGINES.md` R-8's element-by-element copy — runs 0. **Two controls, each a case
the wrong implementation gets wrong:** against the tree before this decision the
five fixtures compile cleanly; and with the marker's element made `int64`, which
owns nothing, they compile cleanly again — the ELEMENT's ownership is the
mechanism, not the zero-length array. `probe16` and `probe16b` record the
language fact the marker rests on, so a compiler that changes it is named by a
probe before five fixtures fail at once.

*Alternatives declined, each measured at `c3bdae2`:* **a `string` marker**
(`hidden string:move_only`, filled `""`, whose drop frees nothing) — identical
verdicts on every file, and `Vec` 48 bytes, `SparseSet` 104; it is the fallback
if a later compiler refuses a zero-length array or stops counting its element,
which probe 16 would show first; **a `buffer` marker** (`buffer_new(0i64)`) —
identical verdicts, 48 bytes, and a runtime call in every constructor:
`npk_buffer_new` joins the undefined symbols of every `Vec` program; **a
`string?` marker** (`NIL`) — identical, 56 bytes; **an `OwnedFd` marker** —
4 bytes, and its drop is a `close`, a syscall path under every `Vec` in a library
whose rule is no syscalls (RX-008); **the block itself in a managed `buffer`**,
an owning field behind `items` — move-only too, but the drop would free the
block, `vec_free` would be redundant, D-151's gate would stop covering `Vec`
(S-22), every element access would be cast off a `uint8->` with `=>!`, and a loan
would still reach it (RX-162): a redesign of this cycle's deliverable; **the
prelude's `List<T>` as the backing store** — owning and move-only by D-247, and
declined on 2026-09-19 when the container question was answered (keep our `Vec`,
give it the properties) on the cost of rewriting every call site in two
libraries; **a language marker for move-only** — there is none at `c3bdae2`
(only a field's type makes a struct own); **a harness check refusing a `Vec`
copy in `src/`** — a house rule where the compiler can refuse, blind to every
consumer; **accept and document** — the author declined it on question 9.

### RX-162 — a by-value parameter is a LOAN, not a copy: `vec_get` keeps its signature, and what a loan still reaches is a compiler defect, pinned and raised, not worked around
> **SUPERSEDED IN PART by RX-167 (2026-09-25)** — its count of what pins the loan, "the four loan units and
> probe 17": a `for` binding is a fifth loan unit, and a generic pass-out is a sixth second handle, O-N22. Its
> decision on `vec_get` and on loans stands.

**2026-09-25, cycle 0.0.4d (the plan's PD-9).** It supersedes
RX-160 in part — its placing of `vec_alias_param_free` among the shapes that
*"must STOP COMPILING"*, and its consequence that move-only changes `vec_get`'s
signature and every by-value read in `src/core/`.

**Measured.** An ordinary parameter is LENT — the compiler's D-065 and D-183,
*"passing transfers nothing"* — and `move` of one is `NITPICK-TYPE-047`. So a
move-only `Vec`, `SparseSet` or `Bytes` passes to a by-value parameter without
`move`, and (1) `vec_get<T>(Vec<T>:v, i)` and every by-value read in
`src/core/` compile unchanged: the fourth audit's expectation was false. (2) The
loan is still a second handle, because the callee may take its own parameter's
address and write through it: `vec_alias_param_free` still compiles and the
caller reads the free poison (0); a callee's growth leaves the caller's own
`vec_free` a double free the guard cannot see (`vec_alias_param_grow`, 95); a
callee's `sset_free` makes the caller read a member ABSENT while `sset_len` says
1 (`sparseset_alias_param_free`, 0) — each the same with the marker and without.
(3) For an owning FIELD the compiler drops the caller's value on the write —
`probe17_lent_field_drop`, no library code, reads the poison (70; returned
normally instead, the caller's drop is a double free, 95) — which is how a
`Bytes`, move-only all along, dies when lent to a callee that grows it
(`bytes_alias_param_grow`, 95). The controls: the same write on a `move`
parameter and on a local run clean. The mechanism, read at `c3bdae2`: D-186's
unconditional field drop reasons that *"the struct's owner is exactly who is
overwriting it"* (`src/backend/ir/ir_stmt.npk`), and a lent parameter's callee
is not its owner.

**The decision.** `vec_get` keeps `Vec<T>:v`: a loan is the language's read-only
convention, it lets a consumer read a sealed field without taking the address
D-313 counts as a write, and nothing in `vec_get` writes through `v`. The four
loan units and probe 17 pin today's behaviour — PINNED, NOT ENDORSED — and each
says what to do when it reddens. The defect is raised as the workbench registry's O-N21, and nothing in
`src/` works around it: every function that changes a container already takes
it by pointer. **The cycle 0.0 gate's "every alias shape refused" is met for the
five COPY shapes and cannot be met at `c3bdae2` for a loan**; whether the close
waits for the compiler's fix is the author's, asked at 0.0.4d's planning.

*Alternatives declined:* **`vec_get` by pointer** (`Vec<T>->`) — a consumer's
`vec_get(@s.sparse, k)` is then `NITPICK-TYPE-079`, since a sealed field's address
is a write, so `SparseSet` would need new accessors, and it would close nothing:
a consumer's own by-value parameter is still a loan; **consuming verbs** — a
`vec_free(move Vec<T>:v)` and growth paths that take and return the `Vec`, which
would make a callee's free and growth through a loan `TYPE-047` — reshaping the
whole API around a compiler defect (W-11), at a copy in and out on every call in
the Pike VM's inner loop, and not reaching (3), which needs no library verb;
**documentation alone** — the loan units are the documentation that runs.

### RX-163 — `Bytes.buf` is `hidden`, and the capacity is read through `bytes_capacity`

**2026-09-25, cycle 0.0.4d (the plan's PD-10) — the author's answer to question 9
let it ride with this subcycle where judged cheaper, and it is.** It supersedes
RX-153 in part: `buf` among the `sealed` fields. RX-153's other qualifiers,
and `ListLen` on the counts, stand.

A sealed field admits a write THROUGH its pointer: a consumer's
`b.buf.ptr[0i64] = 65u8;` compiled and ran at `c3bdae2`, and `bytes_get` then read
65. `hidden` refuses the member access itself (D-314):
`tests/rejection/bytes_buf_ptr_write.npk`, `NITPICK-TYPE-080`, which compiles
cleanly against the tree before this decision. The capacity the tests read as
`b.buf.len` — **nine** code lines in three files at `acaf99c` (cycle 0.0.4c
counted eight, before its own `sealed_reads.npk` added the ninth; the author's
answer carried the eight) — is `bytes_capacity(@b)`. Nothing in `src/` outside
`bytes.npk` reads `buf`. S-23's `Bytes` half is the compiler's for a consumer, as
`Vec`'s has been since 0.0.4c, and `check_accessor_confinement` stays for the
owning files.

*Alternatives declined:* **its own subcycle after the close** (the board's first
recommendation) — nine test lines and one accessor, beside the prose sweep this
subcycle runs anyway, and `nitpick-time` ports both at once; **`buf` sealed, as
0.0.4c left it** — a consumer corrupts the body with no diagnostic, the argument
that made `items` hidden.

### RX-164 — A′ replaces `VERIFICATION.md` P-1: an obligation is a comment unless a numbered decision accepts the arm its live clause costs every consumer; `prove` stays a comment until the verified build

**2026-09-25, cycle 0.0.4d (the plan's PD-11) — the author's answer to Q-6,
2026-09-25 15:56: *"the recommendation on q-6 seems fine to me."*** It replaces
`VERIFICATION.md` P-1 with rule P-1b, and Q-6 is struck with this number.

P-1's argument — every construct it names refuses, so a premature clause is a
build failure — is false at `c3bdae2` (RX-152): `requires`, `ensures`,
`invariant` and `limit` are live and each adds one identity to every consumer's
`failsafe` (`probe13c`, `probe13d`, `probe13f`), and `prove` is accepted and
lowers to nothing in a plain build (`probe13a_prove_unchecked`). **The rule, P-1b:**
a `requires`, `ensures`, `invariant` or `limit` is written live only where a
numbered decision says the check earns the identity it adds to every consumer —
the containers' `ListLen` (S-24a, RX-153) is the one today; every other
obligation stays a comment in the syntax it would take, is evidence of nothing,
and is stood in for by a property test; `prove` stays a comment until the
harness runs the verified build (cycle 0.8), because a plain build drops it; and
`decreases`/`unbounded` are the language's and always live (D-304). Nothing in
`src/` changes: the obligation comments are what A′ keeps, and RX-130's trap
identity stands — a live `requires` on `vec_get` would trap 116 where the stop
traps 94 (`roadmap/0.0/0.0.4b.md` §10).

*Alternatives declined (Q-6's own list):* **A, live now** — every `core` consumer
owes `RequiresViolated` and `EnsuresViolated`, and the accessors' stop changes
identity, so RX-130 would need a successor; **B, every obligation a comment until
0.8, `assert_static` included** — nothing checks a comment; **C, everything live,
`prove` included** — a plain build lowers `prove` to nothing, the silent no-op P-1
was written against.

---

## The cycle 0.0 close, re-attempted a fifth time — the fifth audit's triage (cycle 0.0.5)

*Appended 2026-09-25 by stream 1, working `meta/roadmap/0.0/0.0.5.md` §12 against
[`audits/nitpick-regex-0.0-2026-09-25-fifth.md`](audits/nitpick-regex-0.0-2026-09-25-fifth.md),
at pinned toolchain `c3bdae2` under LLVM 20.1.2. Every audit measurement these rest
on was reproduced here before anything changed, and every number below was taken
at `c3bdae2`, at −O0 and through `opt -O2` where a program ran.*

### RX-165 — the harness opens every `.npk` as the compiler does, decodes an import path by the compiler's escape rules, and the skip's second defence is the compiler's own answer

**2026-09-25, the fifth cycle 0.0 audit's BL-9, with N-28 and N-29's lexical
lines.** It supersedes RX-157 in part — its claim that `lexical.py` was the
compiler's reading of source, and its second part's claim that a file declaring
`main` "holds whatever the reader gets wrong next". RX-157's one-reader rule, its
lexer mirror and self-check cases 15 and 18 stand.

**Reproduced here before anything changed**, over clones of `40074b6` with the
committed harness: `// note<CR>use "does_not_exist.npk".*;` compiles and runs 3 at
both levels while the committed reader reads an import of it (its LF twin is
refused `NITPICK-RESOLVE-005`); `// note<CR>/*` above a `main` compiles and runs 4
while the committed reader finds no `main`; the audit's count plant judged 50
units where the baseline judges 51 and printed `209/209`, GREEN, exit 0; a
syscalling `src/core/zz_pid.npk` reached through `"..\x2f..\x2fsrc/core/zz_pid.npk"`
gave `213/213` GREEN with B-2 on 52 units, against `212/213` and 53 through the
plain path; the CR-hidden owning `Frame` was cleared (six element types, `210/210`
GREEN; its LF twin is refused `NITPICK-TYPE-026`); and an escaped `core` →
`engine` import passed `check_layering`, which fails the plain one.

**Why.** Every caller opened a `.npk` in Python's text mode (`newline=None`),
which makes a lone carriage return a line end before `lexical.py` sees the text;
the compiler ends a `//` comment at byte 10 only and treats byte 13 as whitespace
(`lexer_skip_trivia`, `is_space`). And `imports()` returned a path's text, while
`p_parse_import` takes the string literal's decoded value. RX-157's two defences
fell together because the second — "a file that declares `main` is never
skipped" — was `lexical.declares_main` over the same read: m15a–c had measured
their independence against a reader that read too many imports, and a reader that
blanks too much defeats both at once.

**The decision — the audit's remedies (1) to (4).**

1. **Bytes.** `lexical.read` opens a `.npk` as bytes, one character per byte:
   every offset is the compiler's, `\n` is the only line end, and whitespace is
   the lexer's `is_space`. It is the one way the harness opens a `.npk` — the
   skip, B-2's reach, every tree check, and the expectation markers, whose reader
   now splits at `\n` alone and trims as `npkg`'s `text_lines` and `text_is_ws`
   do (a fourth text-mode reader, which the audit did not name).
2. **A path is decoded, not refused.** `imports()` returns the literal's value by
   `escapes.npk`'s rules — nine escapes, each a code point written as UTF-8, an
   invalid one skipped at its backslash as the compiler does while refusing the
   file — as a filesystem path. An interior NUL is "not found" to the compiler
   (D-049), and to the harness.
3. **The second defence is the compiler's.** A file of a program suite is skipped
   only when the reader finds a sibling importing it AND `npkc`, compiling it as a
   root, exits 0 with no `@main` in its IR (`build.defines_main`, measured on a
   unit and on a module). A candidate `npkc` does not compile is judged. The run
   prints, per program suite, which files it judged through an importer —
   measured: with both defences removed, the plant's run is GREEN and that line
   names the red unit. `lexical.declares_main` is gone.
4. **Self-check cases 19 to 23, and case 18 through a file** (`TESTING.md` V-20):
   19 is the count plant; 20 and 21 are a lone CR and an escaped path hiding a
   syscall from B-2; 23 tests the second defence ALONE, with the reader stubbed to
   invent every import and see no code, because 19 goes red while either defence
   holds and so cannot see one deleted. Case 18 is written to a file and read back
   through `lexical.read`, and holds three CR lines, three escaped paths and a
   block string with `""` in its body, read the way the lexer at `c3bdae2` reads it
   — closed at the first `""`, three bytes consumed (DEF-98; N-28). Case 22,
   RX-159's every-run half, is N-27's and needs no decision of its own.

**Measured.** The count plant over copies of this harness: as committed here,
red — `exited 94, expected 77`, 51 units judged, in a full run with the
self-check first; with the reader put back in text mode, red; with the second
defence deleted, red; with both, `209/209`, GREEN, 50 judged. The escaped-path
plant: `212/213`, B-2 on 53, naming `npk.zz_pid.zz_pid` and `npk_sys6`; the CR
`Frame`: `check_vec_elements_own_nothing` fails it by name; the escaped layering
plant: `check_layering` names the `core` → `engine` edge. The self-check over
copies with each fix reverted (`roadmap/0.0/0.0.5.md` §12 has the table): the
committed reader, undecoded paths and the reader-based `main` together fail 18,
19, 20, 21 and 23. On the real tree nothing moved: every denominator is the
baseline's, 0 files skipped in either program suite, and the tree holds no byte
13 and no `\` in a `use` path.

**What it still does not mirror**, stated in `lexical.py` and each confined to a
file the compiler refuses — which the `parse` sweep, judging every `.npk` as a
root, turns red whatever the reader makes of it: a NUL byte, an interpolation
nested past eight, `_?`-family operators at a template part's start, `e+r"` after
a float, an invalid escape or UTF-8 sequence, and a path beginning neither `./`,
`../` nor `/`, which the compiler resolves against the empty dependency roots
(`NITPICK-RESOLVE-005`, measured) and the harness joins to the importer's
directory.

*Alternatives declined:* **refusing a `\` in an import path** (the audit's other
remedy for (b)) — every consumer would need a failure path of its own, the
reader would disagree with the compiler by design, and the escaped plant would go
red for the refusal rather than at the check it hid from; the decoding is the
compiler's own nine-escape table. **Taking "declares `main`" from the parse
sweep's IR** — the sweep runs after the program suites in manifest order, and a
suite's skip is decided before it runs; compiling the few candidates is the same
answer, sooner. **The object's symbol table** — an `llc` per candidate for the
answer the IR already gives. **Counting judged plus skipped against the files
declaring `main`** — the fourth triage's reason stands, a count that cannot
differ checks nothing; the printed skip line shows the set instead.

### RX-166 — the S-23a check refuses a macro splice, strips every field qualifier the parser has, and reads an enum payload only from `Name(…)`

**2026-09-25, the fifth cycle 0.0 audit's N-24.** It supersedes RX-158 in part —
three details of its mechanism: a member that is a macro splice was resolved as
the type it was named after, only `sealed`, `hidden` and `limit<…>` were stripped
as qualifiers, and every parenthesis in an enum body was read as a payload. Its
default-deny rule, its scalars and its twelve shapes stand.

**Reproduced first**, the committed check over copies of `src/`: a
`#ByteSet();` splice holding a `string` was cleared (0 failures; the same macro
named `name_fields` fails, 2), `struct:Span = { fixed int32:lo; int32:hi; }` was
refused as "holds `fixed`", and `enum:Kind = { Lit = (1i32); Dot = (2i32); }` as
"holds `i32`". The language facts, through four tools at two levels: the splice
compiles and its field reads back (exit 3), and a copy of that `Frame` is
`NITPICK-TYPE-046` — it owns; `Span` and `Kind` copy freely (3 / 3).

**The decision.** (1) A member holding a `#` — a macro splice, live in a struct
or enum body at `c3bdae2` (`p_parse_record`), or an attribute — fails: the check
does not expand macros, so it cannot see what one declares. (2) `fixed`,
`nodrop` and `move` join `sealed` and `hidden` as qualifiers — the parser's
`p_qualifier_bit` — and are stripped; the type after them is still judged, so
`fixed string` fails on `string`. (3) An enum payload is `Name(…)` and nothing
else; what follows `=` is a discriminant, a value, and is not read. And the stated
reason for leaving `simd` and `complex` uncleared is corrected: they own nothing
(`type_drops_recorded`: "lanes of plain scalars", "two plain components") and are
not cleared because nothing needs them — a widening is a decision.

**Measured**, the new check over the same copies: the splice fails, naming
itself; `Span` and `Kind` pass; `fixed string`, `nodrop string`, `move string`, a
payload `string` beside a discriminant and a spliced enum variant fail; scalar
payloads, a discriminant expression and a nested-bracket payload pass; the fourth
triage's M1, M4, M5, M6, M9, M12 and T4 still fail and C2, C3, C4, C5 still pass.
On the real tree it clears the same four element types and exempts the same
fifteen.

*Alternatives declined:* **stating the limits beside RX-158** (the audit's other
remedy) — three small rules against a check that cleared an owning field;
**expanding macros** — the check would need the compiler's macro engine, which
W-18 keeps out of this harness.

### RX-167 — two more shapes reach a move-only `Vec`'s block without a copy — a `for` binding, and a generic function passing out its lent `T` — each pinned as a unit and raised, not worked around

**2026-09-25, the fifth cycle 0.0 audit's N-25 and N-26.** It supersedes RX-162 in
part — its count of what pins the loan, "the four loan units and probe 17". Its
decision on `vec_get` and on loans stands, and so does RX-161: a COPY of a `Vec`
is refused.

**N-26, a `for` binding over an array of containers, is the same loan.**
`for (Vec<int64>:x in arr) { drop vec_free(@x); }` over `[move(a), move(b)]`
compiles, and the array's first element still says `count == 1` and reads the
free poison: `tests/unit/vec_alias_for_binding_free.npk`, exit 0 at both levels,
where its read-only twin exits 21 — the value survives. The parser builds the
binding as a `ParamDecl`, so by the compiler's 1.6.0 step 3g (DEF-102,
`NITPICK-TYPE-085`) `@x` should be refused; the re-pin measures it.

**N-25, a generic pass-out, is not a loan's write at all.** `func:id<T> = T(T:x)
{ pass x; }` compiles, and at `T = Vec<int64>` its result is a second owner of the
argument's block: after `vec_free(@a)` the read through it is the poison —
`tests/unit/vec_alias_generic_passout.npk`, exit 0 at both levels, 21 without the
free. Written for `Vec<int64>` alone, the same body is refused `NITPICK-TYPE-047`
at the `pass`. TYPE-047 is not asked of a lent `T` in a generic body: the
workbench registry's O-N22, confirmed as the compiler's DEF-104, riding with
3g — at a pin carrying it the pass-out refuses `TYPE-047` and `@x` of a lent `T`
refuses `TYPE-085`. `c3bdae2` carries neither.

**The decision.** Both are pinned, not endorsed, each header saying what its
reddening means; `SAFETY.md` S-23b gains two rows and says which defect each
row is; `src/core/vec.npk`'s "a `Vec` CANNOT BE COPIED" is qualified. Nothing in
`src/` changes: no generic there takes a lent bare `T` — `vec_push`, `vec_set`,
`vec_insert` and `drop_element` take `move T`, swept with `git grep -n -E '[(,]
*T:' -- src` (one hit, a comment) — and `src/` has no `for` in code.

*Alternatives declined:* **a harness check refusing a generic that passes out a
lent `T`** — a house rule where the compiler is already fixing it (W-11), blind to
every consumer; **holding the close for N-25** — it is no clause of cycle 0.0's
gate and `src/` has no exposure; whether it should become one is the author's.

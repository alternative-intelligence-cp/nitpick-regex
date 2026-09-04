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

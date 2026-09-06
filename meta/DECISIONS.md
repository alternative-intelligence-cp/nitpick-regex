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

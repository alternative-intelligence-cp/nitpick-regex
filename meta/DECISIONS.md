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
> *(Noted 2026-10-08, cycle 0.1.6a — RX-218: *"None of them describes a regular language; each is exactly what makes
> backtracking unavoidable"* is not true of lookahead and lookbehind: finite automata decide matching with them, and
> two 2024 algorithms match them in O(m·n) without backtracking. Their refusal stands on this decision's automata,
> which read no lookaround, and on `SAFETY.md` S-6.)*

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
> **SUPERSEDED IN PART by RX-191 (2026-10-01)** — its reason, *"the language has no stack-depth
> guard — the failure is a segfault"*: since `c3bdae2` every emitted function checks its stack
> before its frame exists (the compiler's D-305), so a recursion deeper than its stack traps
> `StackExhausted`, a controlled stop of the whole program. The rule stands, for RX-191's reasons.
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
> **SUPERSEDED IN PART by RX-188 (2026-09-28)** — its exception *"any future owning
> `Vec<GroupInfo>` or `Vec<string>`"*: a `Vec` refuses an owning element since cycle
> 0.1.1b. `Hir.names` and the rest of the decision stand.
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
> **SUPERSEDED IN PART by RX-171 (2026-09-26)** — its rule 2 and the every-file check its last paragraph asks
> for: a plain `use` above a `pub use` of the same path no longer cancels the re-export (the compiler's DEF-7,
> fixed at `94874ce`). Rules 1 and 3 stand.
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
> **SUPERSEDED IN PART by RX-180 (2026-09-27)** — its *"CI prints it, and asserts nothing"*: the value it had
> never been told was held at `c970483`, and the step asserts the pin's `npkc.ll` row since cycle 0.1.0b. Its
> measurement — the emission invocation-independent and tree-position-dependent — stands, and is what makes the
> assertion legitimate.

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
> **SUPERSEDED IN PART by RX-180 (2026-09-27)** — its "stays a print": the condition it set, both sides held and
> written down as matching, was met at `c970483`, and the step asserts the pin's `npkc.ll` row since cycle
> 0.1.0b. Its reasoning about the substitution stands.

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
> **SUPERSEDED IN PART by RX-189 (2026-09-28)** — `vec_free_owning` and its unit
> `vec_oob_free_owning_after_free`: removed at cycle 0.1.1b, a `Vec<T: Copy>` holding nothing
> to drop. The guard on `vec_free`, `sset_free`'s inheritance and the lesson about a claimed set
> stand.
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
> **SUPERSEDED IN PART by RX-189 (2026-09-28)** — *"The two stay apart for cost"*: `vec_free_owning`
> is removed at cycle 0.1.1b, a `Vec<T: Copy>` having nothing to drop.
> **SUPERSEDED IN PART by RX-188 (2026-09-28)** — *"nothing in the language keeps an owner out"*:
> `Vec` is `Vec<T: Copy>` since cycle 0.1.1b, so the compiler refuses one at the type and every
> verb; the units measuring each verb, which that bound refuses, are retired; and `tests/` is
> outside the check for a reason that is gone. The rule stands, and the table as a measurement.
> **SUPERSEDED IN PART by RX-168 (2026-09-26)** — its declined alternative, *"a marker-trait bound
> (`vec_get<T: Pod>`)"*: at `c970483` the old `vec_get` does not compile, and the language refuses an
> owning `Pod` impl written as declared, so the bound is taken. The rule, its check and its table stand.
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
> **SUPERSEDED IN PART by RX-189 (2026-09-28)** — its reason *"the guard is what keeps
> `vec_free_owning` from running destructors over a freed block"*: that function is removed at
> cycle 0.1.1b. The guard and its 94 stand on the others.
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
> **SUPERSEDED IN PART by RX-170 (2026-09-26)** — its paragraph that a block string closes at the first
> `""` and `lexical.py` follows that: the lexer closes at `"""` since the compiler's 1.6.0 step 3e.
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
> **SUPERSEDED IN PART by RX-190 (2026-09-28)** — its declined alternative *"the compiler's own
> ownership predicate"*, reachable since cycle 0.1.1b through the type's `T: Copy`: it runs
> beside this check, which stays for what `Copy` admits.
> **SUPERSEDED IN PART by RX-188 (2026-09-28)** — *"so do its verbs, units and table"*: the owning
> units are retired, `Vec<T: Copy>` refusing them since cycle 0.1.1b.
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
> **SUPERSEDED IN PART by RX-168 and RX-169 (2026-09-26)** — `vec_get` keeps its parameter and gains a
> bound, `T: Pod` (RX-168); and the loan is REFUSED at `c970483`, `NITPICK-TYPE-085`, so its pins are
> rejection fixtures and the gate's loan clause is met (RX-169). A loan is still a loan, and nothing was
> worked around.
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
> **SUPERSEDED IN PART by RX-170 (2026-09-26)** — item 4's case 18 *"read the way the lexer at `c3bdae2`
> reads it"*: the block string closes at `"""` at `c970483`, and line 23 is rewritten to read the two
> closes apart. Everything else stands.

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
> **SUPERSEDED IN PART by RX-168 and RX-169 (2026-09-26)** — both shapes are refused at `c970483`, and
> their units are rejection fixtures (RX-169); and "Nothing in `src/` changes" was true of a lent `T`
> PARAMETER and not the whole of DEF-104's reach — `vec_get` and `vec_pop` (RX-168).

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

### RX-168 — `vec_get` takes `T: Pod`, a trait an owning type cannot implement as it is declared, and `vec_pop` spells its move: DEF-104's gate reaches `src/`
> **SUPERSEDED IN PART by RX-188 (2026-09-28)** — its declined alternative `struct:Vec<T: Pod>`,
> O-R3: taken at cycle 0.1.1b as `Vec<T: Copy>`, its gate met since RX-176 and RX-177.
> **SUPERSEDED IN PART by RX-177 (2026-09-27)** — its trait: `vec_get`'s bound is the prelude's `Copy` (the
> compiler's D-327) since cycle 0.1.0b, and `Pod`, `pod_copy` and `core.npk`'s re-export are gone. The bound's
> reason, and `vec_pop`'s spelled move, stand.

**2026-09-26, cycle 0.0.4e (the plan's PD-12), at compiler `c970483`.** It supersedes
RX-155 in part — its declined alternative *"a marker-trait bound (`vec_get<T:
Pod>`)"*, both of whose reasons are false at `c970483`; RX-162 in part —
*"`vec_get` keeps its signature"*: it keeps its parameter and gains a bound; and
RX-167 in part — its reach, *"Nothing in `src/` changes: no generic there takes a
lent bare `T`"*, true of a parameter and not the whole of DEF-104's.

**Measured: the tree as it stood does not compile at `c970483`.** `src/core/vec.npk`
is refused `NITPICK-TYPE-047` twice — `vec_get`'s `pass v.items[i]` (*"this
parameter was lent, not given"*) and `vec_pop`'s `pass v.items[v.count]` (*"`T` is
owned by what this pointer reaches"*) — and so is every file that imports it: the
harness ran `78/223`. The mechanism, read at `c970483` with `git show`: DEF-104
made `refuse_move_of_borrowed` and `refuse_pass_of_pointee_owned` ask
`type_owns_for_move`, which answers yes for a bare `T` (D-264), and a generic body
is checked once — so a `T` PLACE passed out of a lent or pointed-to container is
refused at every `T`, a scalar included. The fifth audit's N-25 and RX-167 looked
at a lent `T` PARAMETER, of which `src/` has none, and not at a `T` place rooted
in one; the audit's post-re-pin item 8 expected `vec_get` to compile.

**`vec_pop` spells the move**: `pass move(v.items[v.count]);` — the prelude's own
`list_pop`, and what the implicit move did: diffed at `c3bdae2`, `vec_pop<string>`
writes the same vacancy into the slot past `count`, plus one temporary and its
flag. Ownership-correct at every `T`, as RX-155 found it.

**`vec_get` takes `T: Pod`.** `pub trait:Pod = { func:pod_copy = Self(Self:self)
never fails; };` is declared in `vec.npk` and re-exported by `core.npk`; `vec_get`
reads `pass raw v.items[i].pod_copy();`; nine impls cover `int8` to `int64`,
`uint8` to `uint64` and `bool`, each `pass self`. **The language decides who may
implement it**: `pass self` of a lent owner is `NITPICK-TYPE-047`, so written as
the trait declares it, `impl:string:Pod`, `impl:Bytes:Pod`, `impl:SparseSet:Pod`,
`impl:Vec<int64>:Pod` and an impl for a struct holding a `string` are each refused
(measured). So `vec_get` at an owning `T` is `NITPICK-TYPE-017` — S-23a's `vec_get`
row, which a later cycle's `Vec<string>` could only break at a harness check over
`src/`, is the compiler's now, for every consumer.
`tests/unit/vec_owning_get_moves_out.npk` moves to `tests/rejection/` as that
refusal. Measured at `c970483`: all thirteen `src/` files compile; the nine bills
are unchanged (10, 10, 10, 10, 6, 11, 6, 6, 6) — `pod_copy` is `never fails` and
adds no identity; `#size_of<Vec<int64>>()` 24, `SparseSet` 56, `Bytes` 32; the
floor 5 / 6 / `{npk_sys6}`; and a consumer of `core.npk` implements `Pod` for its
own POD struct in one line and reads it back. The same `src/` compiles at
`c3bdae2`, so the design is not the pin's.

**The one hole, a compiler defect found at planning** (the workbench registry's O-N28): an impl may
declare `move` on a parameter its trait lends, the compiler accepts it, and a
call through the trait then hands the callee a value the caller still owns — a
double free, 95, with no library code (`tests/probe/probe18_impl_adds_move.npk`,
at `c970483` and `c3bdae2`), and through `vec_get` a consumer's `impl:string:Pod`
written that way returns a second owner of the element (95, measured). No impl
in this repository does it, `check_vec_elements_own_nothing` still refuses an
owning element in `src/`, and `TRAITS_REFERENCE.md` §2 already says an impl must
have the signature the trait declares. Probe 18 reddens when the compiler agrees.

*Alternatives declined:* **`.clone()` under the prelude's `Clone`** — the language's
own spelling for a copy of a `T` place (D-264), and the prelude declares `clone`
MAY FAIL, so in a `never fails` body it is `Result<T>`: `NITPICK-TYPE-007` as
written, `NITPICK-TYPE-042` under `raw` (both measured); `?!` would put a trap
identity in every consumer's bill and `relay` would make `vec_get` fallible and
every `raw vec_get` a `TYPE-042` — an error channel on the search path, against
S-4. **`vec_get(Vec<T>->:v, …)` with `pass move(v.items[i])`** — RX-162's first
declined alternative with a third cost: at an owning `T` the read empties the
slot, and every reader holding a lent `Vec` would need `@v`, which is
`NITPICK-TYPE-085` now. **A local `#wild_slice` over the lent header's `items`**
(`nitpick-time`'s `vec_at` shape, which compiles at `c970483` because its root is
a pointer) — for a LENT `Vec` it moves an owning element out of the caller's block
through the loan, which is what `TYPE-085` refuses when it is written directly:
the refusal routed around, not answered. **A getter per element type** — a verb
per type, where S-23a's question is the generic one. **`struct:Vec<T: Pod>`** —
S-23a at the type, for every verb and every consumer; it refuses the seven
owning-element measurement units and removes `vec_free_owning`'s reason to exist —
a redesign, not an adoption. It is O-R3, open with a recommendation. **Waiting for
a never-failing `Clone` from the compiler** — a language decision (a `string`'s
clone allocates), raised as a design input, `0.0.4e.md` §6.2, and not waited on.
**Another name** — `Copy` is a name a prelude may yet declare, and D-239 would then
refuse ours; `Pod` is RX-155's own word for what it asks.

### RX-169 — the loan and the generic pass-out are REFUSED at `c970483`: the six pins and probe 17 move to their refusal homes, each shown to be the pin's, and the spellings the refusals prescribe run

**2026-09-26, cycle 0.0.4e (the plan's PD-13), at compiler `c970483`.** It supersedes
RX-162 in part — *"PINNED, NOT ENDORSED"* and *"cannot be met at `c3bdae2` for a
loan"*: they are refused and the gate's loan clause is met — and RX-167 in part —
its two units' *"pinned, not endorsed"*. Their decisions on `vec_get`'s loan and on
not working around a defect stand.

**Measured at `c970483`**, each file through `npkc` alone and each refusal
exactly its code under B-7, at the position its own `expect-error-at` records: a
write through a lent container is `NITPICK-TYPE-085` (DEF-102) —
`vec_alias_param_free` and `vec_alias_param_grow` at their callee's `@v`,
`sparseset_alias_param_free` at `@s`, `bytes_alias_param_grow` at `@b`,
`vec_alias_for_binding_free` at `@x` (the fifth audit's N-26: the `for` binding
is a loan to 3g, as its parser reading predicted), and probe 17 at its field
write; the generic identity's `pass x` is `NITPICK-TYPE-047` (DEF-104). The six
units move to `tests/rejection/` and probe 17 to `tests/probe/refused/`, under
their names, their headers rewritten. **Each refusal is the pin's**: every one
still compiles and runs at `c3bdae2` with the exit it asserted as a unit — 0, 95,
0, 95, 0, 0, and 70 — at −O0 and through `opt -O2`.

**Two frees name their `T`.** Written `vec_free(@v)`, the refused argument leaves
`T` nothing to be inferred from and the compiler adds `NITPICK-TYPE-022` at the
same call; `vec_free::<int64>(@v)` leaves `TYPE-085` alone. The cascade is the
compiler's diagnostic recovery, not the loan, and B-7's equality would have made it
part of what the file asserts.

**The positive twin, `tests/unit/loan_spellings.npk`**, runs what the refusals
prescribe — a callee that frees takes `move Vec<int64>:v` and its caller writes
`move(a)`; one that grows takes `Vec<int64>->`; the same for a `SparseSet` and a
`Bytes`; a `for` loop reads its binding and the array frees its elements by index;
a generic that passes its argument on takes `move T:x` — each value checked, every
block freed once: exit 0 at both levels, at `c970483` and at `c3bdae2`. Without it
the refusals would also pass a compiler that refused every container parameter.

**Cycle 0.0's gate** — every loan shape refused at a pin carrying DEF-102 — **is
met**: the four `*_alias_param_*` fixtures, probe 17 and the `for` binding.

*Alternatives declined:* **keeping `TYPE-022` in the two expectation sets** — it
pins the compiler's recovery after an error, which may change without the loan
changing; **new names for the moved files** — RX-160, RX-162 and RX-167 find them
by name, 0.0.4d's precedent; **leaving them in `tests/unit/` behind a marker** — a
refusal is a `check`-stage fact, and the rejection suite is where B-7 holds it.

### RX-170 — `harness/lexical.py` closes a block string at `"""`, as the compiler's lexer has since its 1.6.0 step 3e (DEF-98): probe 15 runs, and self-check case 18 reads the two closes apart in both directions

**2026-09-26, cycle 0.0.4e (the plan's PD-14), at compiler `c970483`.** It supersedes
RX-157 in part — its paragraph that the lexer closes a block string at the first
`""` and `lexical.py` follows it — and RX-165 in part — item 4's case 18 *"read the
way the lexer at `c3bdae2` reads it"*. The one-reader rule, the lexer mirror, the
bytes, the decoded path and both defences stand.

**Measured.** `lexer_next` at `c970483` breaks a block string only when the
current byte and the next two are quotes (`lexer_peek3`), and a backslash still
skips the byte after it; the lexer's diff from `c3bdae2` is that alone,
`escapes.npk` is unchanged, and `parse_decl.npk`'s change is DEF-103's declared-name
check, which reads no import. Probe 15, `"""a""b"""`, compiles and exits 4 at −O0
and through `opt -O2` at `c970483` and is refused `LEX-005`, `PARSE-001`,
`PARSE-003` at `c3bdae2`; it moves out of `refused/` with `expect-exit: 4`.

**Case 18's line 23 is rewritten, not only re-expected.** It read `"""a""b use
"./in_block_pin.npk".*; """x""!;` and required its import, the old close's
reading. Merely flipping the expectation to "no import" would also pass a reader
that never closed a block string at all. It now reads `"""a""b use
"./in_block.npk".*; """; use "./after_block.npk".*;` and requires
`./after_block.npk` alone: the new close reads the `use` after the literal; the
old one reads the `use` inside it and opens a block that never closes. Both
readings were measured against the compilers, in a module holding that line: at
`c970483` the only import is `./after_block.npk` (`NITPICK-RESOLVE-005` naming it,
nothing naming the other), and at `c3bdae2` the compiler reads `./in_block.npk`
and reports the second block unterminated (`LEX-005`). `c3bdae2`'s close, restored
in a copy of `lexical.py`, reddens case 18 alone.

*Alternatives declined:* **keeping the old close** — the module's purpose is to
agree with the compiler, and it no longer would; **following the grammar and not
the lexer** — they agree now, and the day they part the lexer is still what reads
the files; **flipping line 23's expectation alone** — measured above as a case a
never-closing reader passes.

### RX-171 — B-15a's rule 2 is retired: a plain `use` above a `pub use` of the same path no longer cancels the re-export, and nothing else gave the rule a reason

**2026-09-26, cycle 0.1.0 (the plan's PD-15), at compiler `c970483`.** It supersedes RX-113 in part — its
rule 2, *"the umbrella never plain-`use`s a path it also `pub use`s"*, and its last paragraph's promise of a
check that no file holds both. Rules 1 and 3 stand, and so does everything RX-113 measured.

**Why now.** Cycle 0.0's close found that the rule's one reason was a compiler defect — `symtab_bind_import`
returned a name's prior binding without merging a later `pub use`'s flags: the workbench registry's O-N13, the
compiler's DEF-7 — fixed at `94874ce` and struck as discharged at the fifth audit's triage, while live sites
still stated it as current (`meta/roadmap/done/0.0/0.0.5.md` §13, finding 1). It handed the decision to this
cycle, ahead of the first layer entry the library writes since the rule was made, `src/syntax/syntax.npk`.

**Measured**, each shape a one-line edit to a copy of the tree, each consumer through `npkc`, `llc`, `ld.lld`
and a run at −O0 and through `opt -O2`:

| the copy | at `950bb1d` | at `94874ce` | at `c970483` |
|---|---|---|---|
| unedited | runs 0 | runs 0 | runs 0 |
| `use "./api/api.npk".*;` above `src/lib.npk`'s `pub use` | **refused `NITPICK-RESOLVE-002`** at the consumer's `(ERegexPattern)` arm: the defect | runs 0 | runs 0 |
| `use "./api/api.npk".ERegexPattern;` above it: the same name | **refused `NITPICK-RESOLVE-002`** | runs 0 | runs 0 |
| that `pub use` made a plain `use` | refused `NITPICK-RESOLVE-002` | refused `NITPICK-RESOLVE-002` | refused `NITPICK-RESOLVE-002` |
| `use "./vec.npk".*;` above, and in another copy below, `src/core/core.npk`'s `pub use` lines | | | `vec_get_pod_struct` runs 0 |

The consumer at `950bb1d` and `94874ce` names the arms those compilers have, and at `c970483` the committed
`tests/conformance/import.npk` is the consumer. A file holding only `pub use` lines also uses the names it
re-exports, at `c970483` — a `pub use` binds its name in its own file — so no file needs a plain `use` of a path
for a name it re-exports.

**So rule 2 guarded against nothing, and its check never tested it alone.** `_check_umbrella` reads
`src/lib.npk` only, where rule 1's branch already fails every plain `use`; the check over every file that
RX-113 promised was never built. The branch goes and rule 1's stays. `BUILD.md` B-15a marks rule 2 retired,
and `CLAUDE.md`, `CONTRIBUTING.md` item 7, `harness/treecheck.py` and the headers of `src/core/core.npk` and
`src/lib.npk` stop stating the cancellation as current — eight sites: the seven the close named, and
`check_layering`'s docstring, which said the shape "produces NO DIAGNOSTIC" in the present tense.

*Alternatives declined:* **keeping rule 2 against a regression of DEF-7** — the compiler's own
`tests/accept/reexport/` guards the fix, and this library's consumer programs (`tests/conformance/import.npk`,
`tests/unit/vec_get_pod_struct.npk`) go red if a re-export they use stops working — RX-151 kept B-0 when its
mechanism expired because a second, true reason held it, and here none does; **keeping it as style** — a specification
states facts about the library, and this would state a lint with no failure behind it; **keeping it and
building the every-file check RX-113 promised** — a check needs a failure message, and this one could give no
true reason; **leaving it to the next audit** — the first layer entry written since is this subcycle's, and
cycle 0.0's close placed the decision before it.

### RX-172 — `PatternErrorKind` is `SYNTAX.md` §9 complete and in order; `PatternError` is sealed, so `pattern_error(…)` is the only way to build one, and it stops on a negative offset
> **SUPERSEDED IN PART by RX-181 (2026-09-27)** — its count: §9 lists thirty-six kinds since cycle 0.1.1, which
> retired `EmptyAlternate`. The seal, the one constructor and the order stand.

**2026-09-26, cycle 0.1.0 (the plan's PD-16), at compiler `c970483`.** `src/syntax/pattern_error.npk`:

- **`PatternErrorKind` holds all thirty-seven of `SYNTAX.md` §9, in its order, now** — before the parser
  produces any. `check_error_kinds_tested` (0.1.6) diffs the enum against the tests that provoke each kind,
  and cannot be written against a moving enum; a kind added later is one nobody notices is untested.
  `tests/unit/pattern_error_unit.npk` holds the enum to §9 with an exhaustive `pick`: a kind dropped, added or
  moved is a red run.
- **`PatternError` is `SAFETY.md` S-9's four fields, each `sealed`** (the compiler's D-313). Outside the
  file a `PatternError{ … }` literal is `NITPICK-TYPE-079` — measured, once per field, at the literal
  (`tests/rejection/pattern_error_literal.npk`) — so `pattern_error(kind, offset, span_len, detail)` is the one
  way to build an error, and `SYNTAX.md` Y-10's offset on every error is the compiler's to hold. The value is
  32 bytes (measured); S-9 fixes the fields' order, and nothing stores one in a `Vec`.
- **`pattern_error` stops on a negative `offset` or `span_len`**, through `core`'s `vec_oob` (94): either is
  a defect in the code that built the error, and a stop beats a position that is not in the user's pattern.
- **The file is `pattern_error.npk`, because `error.npk` cannot exist**: `error` is a keyword, a file's
  `mod:` name is its basename (B-13), and `mod:error;` is `NITPICK-RESOLVE-012` (measured). It imports `core`
  for `vec_oob`, so it — and the layer entry, `src/syntax/syntax.npk`, which re-exports its three names —
  costs a consumer `core`'s eleven arms.

*Alternatives declined:* **the fields open, with a tree check or a reviewed grep for other construction
sites** — the first draft of `0.1.0.md`'s acceptance; the seal makes the compiler refuse every other site,
where a grep only finds the ones that exist today; **a constructor that stores what it is given** — a
negative offset would reach the user as a position that is not there; **declaring each kind when the
subcycle that produces it lands** — the enum would move under the gate's check, and each late kind would be one
nothing notices is untested; **S-9's fields reordered to save the eight bytes of padding** — S-9 is the
specification, the value is never in an array, and a parse stops at its first error.

### RX-173 — the parser reads a pattern through a sealed cursor: `cursor_init` returns it, only its own functions move it, and it looks one byte ahead

**2026-09-26, cycle 0.1.0 (the plan's PD-17), at compiler `c970483`.** `src/syntax/cursor.npk`:
`struct:Cursor = { sealed uint8[]:src; sealed int64:pos; }`, built by `cursor_init(uint8[]:pat)` at offset 0,
read by `cursor_at_end`, `cursor_offset` and `cursor_peek`, moved by `cursor_bump` and `cursor_eat` and by
nothing else. A byte is answered as an `int32` from 0 to 255, and `CURSOR_END` (−1) when none is left; nothing
reads past the pattern.

- **Sealed, so the lookahead rule is the compiler's.** Cycle 0.1's checklist asks for "no lookahead beyond one
  byte except where the grammar names it". With both fields sealed (the compiler's D-313) a write of `pos`
  outside the file is `NITPICK-TYPE-079` (`tests/rejection/cursor_pos_write.npk`), and so is a `Cursor{ … }`
  literal, once per field (measured) — so a construct that needs more lookahead asks for a function here, by a
  decision, and there is no rewind to reach for.
- **Returned by `cursor_init`, because that is sound now.** `0.1.0.md`'s first draft (its D2) kept the cursor
  "a parameter everywhere, never a return value", for a reason cycle 0.0 met at `950bb1d`: a view that escaped
  its frame drew no diagnostic (O-N9, the compiler's DEF-3). DEF-3 was fixed at `94874ce`. Measured at
  `c970483`, `c3bdae2` and the next re-pin's control, `9f6f370`: a `Cursor` over a view of the constructor's
  PARAMETER is returned and reads correctly (0 / 0), and one over a view of a LOCAL is `NITPICK-BORROW-001` at
  the `pass` — the escape analysis sees through the struct. `SAFETY.md` §1's second row said a struct holding a
  borrow cannot be returned; it gains a dated note, since what D-004 bars is a borrow of a local.
- **What is NOT closed at `c970483`, and how it is kept out of reach.** A `string` reassigned while a `Cursor`
  holds its view leaves the cursor reading freed memory: the next byte read is the allocator's `0xAA` poison
  (170 at both legs). The compiler's view freeze refuses that write (its DEF-107, `NITPICK-BORROW-015` —
  measured at `9f6f370`), and no pin of ours carries it. The parser never holds the pattern's owner — it takes
  a view parameter — so nothing in `src/` can write it; a test keeps its pattern's owner unwritten while a
  cursor is live.
- **`int64` offsets, and every loop over a cursor is a `while` with an `int64` measure** (`decreases` the
  length less the offset, the compiler's D-304). No `for` over a range, no `loop`, no `till`: at `c970483` each
  has a shape that runs the wrong number of times at no diagnostic — a range ending at its type's maximum or
  crossing an unsigned type's sign bit runs zero times, `loop` and `till` widen an unsigned bound by its sign,
  `till` with a negative limit counts down, and a `for` binding sharing an outer local's name overwrites it
  (the compiler's DEF-127 … DEF-130, registered 2026-09-26 for its 1.6.1d). A byte loop is exactly where those
  shapes live; none is written here, and a design that needs one is a question for the author, not a
  workaround.

*Alternatives declined:* **the draft's D2 — a struct literal at every call site, its fields open** — the
position would be writable by anyone holding a cursor and the lookahead rule a convention; its reason, the
undiagnosed escape, is gone; **the offset alone, with the slice passed beside it to every call** — two things
to keep together at every site, and nothing to seal; **`cursor_peek` answering `uint8?`** — an `Optional` per
byte, read with `??` and a default, for what one sentinel says; **a two-byte peek or a rewind now** — no
construct 0.1.0 writes needs one, and the grammar names where one is needed when a subcycle meets it;
**`int32` offsets** — every one would be narrowed from an `int64` length, and the language has no checked
narrowing.

### RX-174 — the AST is a flat arena of sixteen kinds of 56-byte node that own nothing, every operand an `int64`, and only `ast.npk` touches its `Vec`
> **SUPERSEDED IN PART by RX-177 (2026-09-27)** — *"`AstNode` implements `Pod` in one line"*: `Pod` retired into the
> prelude's `Copy`, which `AstNode` and `AstKind` derive. Every other part is as this decision says. *(Marked
> 2026-10-08, cycle 0.1.6a — the cycle audit's S2: the marker was not added when RX-177 landed.)*

**2026-09-26, cycle 0.1.0 (the plan's PD-18), at compiler `c970483`.** `src/syntax/ast.npk`, and `SYNTAX.md`
rules Y-26 (the node) and Y-27 (the kinds):

- **`HIR.md` H-2's shape, for H-2's reason**: a `Vec<AstNode>`, and a node names another by index, because a
  `Vec` reallocates and a pointer into it would dangle. A node owns nothing — the S-23a check clears
  `Vec<AstNode>` (measured: six element types, ten declarations) — and `AstNode` implements `Pod` in one line,
  its `self` lent as the trait declares it, so `vec_get` hands a node back by value. A name or a property's
  text stays in the pattern, as an offset and a length.
- **Every operand is an `int64`.** The values come from `int64`s — the cursor's offset, a `Vec`'s count, a
  parsed bound — and `=>!` narrows in silence, so an `int32` field would need a hand-written range check at every
  write, against a bound `RegexOptions` may raise (`SAFETY.md` S-12, `API.md` A-7). The AST is compile-time
  scratch.
- **56 bytes, the same under any alignment rule**: `kind` and `flags` first, together, then six `int64`s —
  no padding (measured 56 at `c970483`, `c3bdae2` and the next re-pin's control; the order `kind`, operands,
  `flags` is 64). `tests/unit/ast_size.npk` exits with the size.
- **The sixteen kinds are declared now, with their operands** (Y-27's table): every construct of §1's grammar
  that survives parsing has a kind, and the node is shown to hold each before any is parsed. The flag bits are
  Y-26's: the five pattern flags, and `LAZY`, `NEGATED` and `BYTE`.
- **The arena is `Ast`: `hidden Vec<AstNode>:nodes`, `sealed int64:root`.** Outside `ast.npk` the `Vec`
  cannot even be read (`NITPICK-TYPE-080`, `tests/rejection/ast_nodes_read.npk`), so `ast_get`, `ast_set` and
  `ast_push` — `vec_get`, `vec_set` and `vec_push` underneath — are the only way in (S-23). `ast_set_root`
  checks its index; `ast_free` frees the block and resets the root.

*Alternatives declined:* **`int32` operands** — `0.1.0.md`'s first draft (its D1, "exactly like the HIR")
and the cycle README's checklist: every one would narrow an `int64` in silence, and the HIR is 0.2's to size;
**a payload enum per construct** — the spelling H-2 examined and declined, and the flat operands are what the
HIR mirrors; **declaring each kind when the subcycle that parses it lands** — the node would be proven
against the first constructs only, which is `0.1.0.md`'s own warning about a skeleton shaped by what fitted
first; **children in a side array** — a second arena and an index pair per parent, where H-2 links siblings;
**names copied into a `Bytes` in the `Ast`** (the first draft's D1) — the pattern is at hand for the AST's
whole life, and `Hir.names` is the HIR's copy; **`nodes` sealed rather than hidden** — a consumer could then
read the `Vec` and index it past `ast_get`; **`AstNode`'s fields sealed** — the parser, in another module,
builds nodes, and a node has no invariant a constructor would keep.

### RX-175 — the syntax layer answers a `PatternError` as a value, `PatternError?`, never as an identity; the pattern's length is refused first; and 0.1.0 writes no parser, only the entry's first refusal and a unit that composes the pieces

**2026-09-26, cycle 0.1.0 (the plan's PD-19), at compiler `c970483`.**

- **A value, because `syntax` is below the error.** The library's one `error:` identity, `ERegexPattern`, is
  `api`'s (`SAFETY.md` S-8), and `syntax` sits below `api` (`BUILD.md` B-16), so it cannot raise it. A parse
  answers `PatternError?` — `NIL`, or the first error — and `api` turns the first error into the identity.
  Cycle 0.1.1's parse is `parse_pattern(uint8[]:pat, Ast->:out)`: the pattern as a view, the tree by pointer,
  and the arena the caller's to free either way.
- **The length first** (the first draft's D5): `parse_check_length(uint8[]:pat)` answers `PatternTooLong`
  for a pattern longer than `NREGEX_PATTERN_BYTES` — its offset the first byte past the bound, its length the
  bytes over it, its detail the bound — and `NIL` otherwise, and the parse calls it before a cursor exists: it
  is the cheapest refusal, and it bounds everything after it, the arena included. Measured: on the bound
  `NIL`, one over refused (`tests/unit/parse_check_length.npk`), and a refused pattern pushes no node
  (`tests/unit/syntax_skeleton.npk`).
- **No parser in `src/` at 0.1.0.** The subcycle's acceptance — a skeleton that accepts `a` and reports offset
  0 for `(` — is a unit, `tests/unit/syntax_skeleton.npk`, built from `syntax.npk`'s re-exports alone.
  `src/syntax/parse.npk` holds the entry's first refusal and nothing else until 0.1.1.
- **The bill.** `src/syntax/syntax.npk` reaches `core`, so a program importing it owes `core`'s eleven arms
  (measured): the language's six, `IntOverflow`, `OutOfBounds`, `DecreasesViolated`, `LimitViolated` and
  `ShiftRange`. `SAFETY.md` S-11 says `syntax` is below the error too.

*Alternatives declined:* **an `error:` identity in `syntax`** — REACH-002 makes an identity an arm in every
program that can reach it, and S-8 allows the library exactly one; **`Result<Ast>` failing with
`ERegexPattern`** — `syntax` would import `api`, to its left (B-16); **a `bool` and a `PatternError`
out-parameter** — the caller would build a `PatternError` to pass in, and the closed list has no kind that
means "none"; **a skeleton parser in `src/`** — outside its two cases it would have to trap or answer a kind
about a pattern it did not parse, and 0.1.1 would delete it; **the length checked during the scan** — the
cheapest refusal would come after the most expensive work.

## The adoption to compiler 5fbaf4a, and the ecosystem audit's items — cycle 0.1.0b

### RX-176 — the adoption to compiler `5fbaf4a`: probe 18 refused `TYPE-014`, the manifest pins the target and the runner holds every emission to it, and every adoption re-reads what the lexical mirror mirrors

**2026-09-27, cycle 0.1.0b (the plan's PD-20), at compiler `5fbaf4a`, from `c970483`** — landings 67 … 82,
one re-pin at the author's go (the board's question 12: the latest). Measured on the unchanged tree first:
**248/250**, the two failures both probe 18 (its probe unit and its parse-sweep unit); every other verdict,
refusal position and site count as at `c970483`; the floor's five symbols unchanged; no `cstring` beyond
`main`'s `argv` in any file, so landing 78's move-only `cstring` refuses nothing here.

- **Probe 18 moves to `tests/probe/refused/`**, `NITPICK-TYPE-014` at 35:39, one site: the compiler's DEF-116
  (landing 69) makes a parameter's `move` part of a trait method's signature. Its header is rewritten as the
  refusal it now pins, with the double free it pinned as history. The probe split is 24 / 8.
- **`[toolchain]` gains `triple` and `datalayout`** (the compiler's E-8, D-322 (5), landing 71), verbatim from
  its advance notice F15, **and the runner reads both** — a key nothing reads is the next stale document
  (D-204): `harness/toolchain.py` holds the layout to what the pinned `opt` derives from the triple, and
  `harness/build.py` holds every linked program's two `target` lines to the pins — the compiler's own
  `check_datalayout_pin` and `check_module_header`, ported (`BUILD.md` B-1a). Self-check cases 24 and 25 are
  their reds: a layout that is not `opt`'s, and a tree pinned consistently to `i686`, where only the belt sees
  every emission state x86-64.
- **Every adoption re-reads what `harness/lexical.py` mirrors** (`BUILD.md` B-4e) — the ecosystem audit's
  ED1. This one: `lexer.npk` +13/−2, a character literal's width (DEF-145), not its span; `escapes.npk`,
  `p_parse_import` and the lexical reference unchanged; the mirror does not move.
- **The pin carries DEF-107 and DEF-143.** Cycle 0.1.0's block-3b controls, re-run: the pattern's owner
  written under a live cursor is `NITPICK-BORROW-015` (at `c970483` it compiled and read freed memory), and a
  cursor over a LOCAL's view, returned, is still `NITPICK-BORROW-001` — landing 72's relaxation (D-326) did not
  reach it. `mod:error;` is `NITPICK-PARSE-001` at 1:5. The notes that said otherwise are dated, not rewritten.
- **`harness/baseline/rx120.sh` asserts at `5fbaf4a`**: floor 5, syscaller 6, the difference `{npk_sys6}`.

*Alternatives declined:* **the two rows in the manifest, read by nothing until `npkg` builds the library** —
the harness refuses a key nothing reads, by design, and a pin nothing checks is a stated string; **the header
belt without the layout check** — a wrong layout in the manifest would then hold every emission to itself;
**probe 18 deleted** — P-5 forbids deleting a probe, and the refusal is the fact the double free's fix rests
on; **the lexer re-read left to the audit** — the audit found this repository had no rule for it, and a mirror
checked only when someone remembers is the time audit's E1 in this tree.

### RX-177 — `Pod` retires into the prelude's `Copy`: `vec_get` takes `T: Copy`, a node derives it, and a consumer implements it in one line
> **SUPERSEDED IN PART by RX-188 (2026-09-28)** — *"at the same position"*: since cycle 0.1.1b
> `Vec<string>` is refused at the type first, and the fixture names all fourteen sites.

**2026-09-27, cycle 0.1.0b (the plan's PD-21), at compiler `5fbaf4a`** — the replacement RX-168 was shaped for and
`nitpick-time`'s PD-49 planned for both libraries, now that the compiler's D-327 (landing 73) is in the pin.

- **`vec.npk`'s `Pod` block goes** — the trait and its nine scalar impls — and **`vec_get` takes `T: Copy`**, its
  read `pass v.items[i]`: in a generic body a `T: Copy` is copied plainly (D-327), where D-264 asks a move of
  every other `T`. At `Vec<string>` it is still `NITPICK-TYPE-017`, at the same position
  (`tests/rejection/vec_owning_get_moves_out.npk`). `core.npk` drops its `Pod` re-export; the prelude's name
  needs none.
- **`AstNode` and `AstKind` each `#[derive(Copy)]`.** Measured: `impl:AstNode:Copy = { };` alone is
  `NITPICK-TYPE-087`, *"the field `kind` of `AstNode` is a `AstKind` that does not implement `Copy`"* — a user
  enum is not `Copy` until it says so — and both the derived and the explicit forms compile once the kind is.
- **`tests/unit/vec_get_pod_struct.npk` pins the explicit form**, `impl:Pt:Copy = { };`, beside the AST's
  derived one; the name stays, since "POD" still says what the struct is.

*Alternatives declined:* **keep `Pod` beside `Copy`** — two names for one rule, and D-327 was decided so that
this one retires into the prelude's; **`T:x = v.items[i]; pass x;`** — the same copy with a binding for no
reason; **`impl:AstNode:Copy`** — the derive states it where the fields are, and a member that later owns is
refused at the declaration; **renaming the unit** — its subject is a plain-old-data struct, which it still is.

### RX-178 — a rejection file's sites are counted per code: one `expect-error` line per reported site, as the compiler's runners hold since its landing 82

**2026-09-27, cycle 0.1.0b (the plan's PD-22), at compiler `5fbaf4a`** — the compiler's D-332 (its S-113, the
author's decision), announced to the libraries as advance notice F24.

- **`harness/stages.py` adds the count to B-7's set equality** (`BUILD.md` B-7b): for every code both named and
  reported on the error channel, the number of reported sites equals the number of `expect-error` lines naming
  it, and a mismatch fails the file by name, with every site. Notes are outside it, as they are in the
  compiler's rule.
- **Measured before the rule was written**, over the thirty-one files here carrying `expect-error` — the
  twenty-four rejection fixtures, the eight refused probes but probe 18, which moved in at this subcycle — at
  `5fbaf4a` and at `c970483`: thirty agree, and `tests/rejection/pattern_error_literal.npk` names
  `NITPICK-TYPE-079` once where it is reported four times at 22:22, once per sealed field it writes. It names
  it four times now, at 31:22, the header nine lines longer. Probe 18's `TYPE-014` is one site.
- **Self-check cases 26 and 27** are the two directions: a code named once and reported twice, and the
  compiler's own `silent_site` shape — named twice, reported once, the lines carrying no position.

*Alternatives declined:* **keep B-7's sets and let the compiler's runners hold the count** — nothing runs our
fixtures under them until `npkg` can build this library (O-G3), and the parity stage that retires this runner
would then disagree on the first file it read; **name one line per distinct position** — the literal's four
sites share one position, and the compiler counts sites, not positions; **the count on notes as well** — D-332
holds the error channel.

### RX-179 — `check_error_budget` and `check_accessor_confinement` read the whole blanked text: every `error:` declaration keyed by its module, and every spaced form of an accessor

**2026-09-27, cycle 0.1.0b (the plan's PD-23)** — the ecosystem audit of 2026-09-26's EC4 and EC5
(`../meta/audits/ecosystem-2026-09-26.md` in the workbench), each a check that passed planted violations. Neither
had an instance in the tree: `src/` declares one identity and no spaced accessor, measured at `5fbaf4a`.

- **`check_error_budget`** matched one declaration per line with `re.match`, public ones by name only. It now
  finds every declaration over the whole blanked text — `pub` and `error` on two lines, two on one — keys each
  by its file's module, as `NITPICK-REACH-003` names them, and refuses every one but `api.ERegexPattern`,
  public, private ones included: a private identity a reachable `fail` raises charges every importer (the
  audit's EC3), and a check reading text cannot see reach, so it is default-deny (as RX-158 is).
- **`check_accessor_confinement`** looked for `.items[` and `.ptr[` exactly. It now matches
  `\\.\\s*(items|ptr)\\s*\\[` over the blanked text, across a line break.
- **Self-check cases 28 and 29** run each check on the instrument over the audit's plants, each alone, each
  required to fail by name, and over a clean tree required to pass.

*Alternatives declined:* **count private declarations and report them** — a report is read when someone
remembers, and the audit's plant compiles and charges every importer; **resolve reach to allow a private
identity nothing raises** — a call-graph walk in a tree check, for a shape `src/` has no use for; **plants as
units in `tests/`** — a tree check reads `src/`, and a planted `src/` file is a real one.

### RX-180 — CI asserts what it printed: the compiler's commit, its emission against the pin's row, and the harness's unqualified summary

**2026-09-27, cycle 0.1.0b (the plan's PD-24)** — the ecosystem audit of 2026-09-26's ED3 and EK2. It
supersedes RX-141 in part, and RX-133 in part: the print each kept. RX-133's measurement and RX-141's reasoning
about the substitution stand.

- **The emission is asserted** (ED3). RX-141 kept the `npkc.ll` digest a print until somebody held both sides
  and wrote down that they matched. At `c970483` CI run 36253106675 printed `d36a7e23…` / 28 188 736 B, the
  workbench's pin record held the same, and cycle 0.1.0's verifier recorded the match; the compiler's D-265 makes
  the emission the cross-machine claim. So the workflow carries the pinned commit's `npkc.ll` row —
  `5630c2b4…` / 30 232 291 B, notice 82's — and fails when the runner's differs, after printing every row. The
  binary rows stay prints.
- **The compiler's checkout is asserted AT the pinned commit, and clean** (EK2), `nitpick-time`'s step.
- **The harness's unqualified `GREEN.` line is asserted** (EK2), `nitpick-time`'s TM-125: a filtered run exits 0
  and prints no such line, so a flag added to the step reddens it.
- **The Node-24 annotation is triaged, not fixed** (EK2's third item): both CIs carry it, one verified research
  request serves both, and the bump is its own commit — the workbench's to schedule. It is a warning today.

*Alternatives declined:* **assert the workbench's binary digests** — D-265 says a version is not a binary, and
S-42 measured them differing; **keep the print** — ED3's point: the condition was met and nothing scheduled the
promotion; **bump the actions now, unverified** — a version this plan has not checked is a currency row nobody
dated.

## The core grammar — cycle 0.1.1

### RX-181 — `EmptyAlternate` is retired: an empty alternative is Y-27's `Empty`, accepted, so no pattern could provoke the kind

**2026-09-27, cycle 0.1.1 (the plan's PD-25), at compiler `5fbaf4a`.** `SYNTAX.md` §9 listed `EmptyAlternate` among
the structure kinds, and Y-27 (RX-174) already makes `Empty` "an empty pattern, alternative or group body" — the
same list declares a refusal and the node that accepts its every trigger. The grammar decides for the node: `a|`,
`|a`, `(|a)` and `()` parse, as in Rust, RE2, PCRE, Python and JavaScript, and an empty alternative is not
ambiguous, which is the thing this library refuses on principle. So the kind goes — the enum, its place in
`pattern_error_unit.npk`'s exhaustive `pick` (thirty-six now, every later kind one place earlier), and the
list — before a parser exists to leave it dormant (Y-25: every kind has a test that provokes it, and cycle
0.1.6's `check_error_kinds_tested` would have found this one with nothing to test).

*Alternatives declined:* **refuse empty alternatives** — every engine `COMPAT.md` compares against accepts them,
`(a|)` is a common spelling of an optional group, and Y-27 would need amending too; **keep the kind for a later
trigger** — none is in §1's grammar, and a kind held for a construct nobody has named is the dormant-rule pattern;
**leave it to cycle 0.1.6** — the decision is the grammar's, and 0.1.1 is where the grammar is written.

### RX-182 — the parse is one explicit-stack walk that builds the arena bottom-up, the last atom held pending for a quantifier
> **SUPERSEDED IN PART by RX-197 (2026-10-01)** — *"then one `while` over the cursor"*: a class is read by a `while` of
> its own, `parse_class`'s, which the walk's calls at a `[` — still once over the pattern, on an explicit stack of
> its own (`SYNTAX.md` Y-33's note). The walk, its stack and its pending atom are as this decision says.

**2026-09-27, cycle 0.1.1 (the plan's PD-26), at compiler `5fbaf4a`** — `SYNTAX.md` Y-33. `parse_pattern(uint8[]:pat,
Ast->:out)` answers `PatternError?` (RX-175's shape): the length, the encoding (RX-183), then one `while` over the
cursor. Its state is a `Parser` — the cursor, the frame being built, the next capture index, a `Vec<Frame>` of the
enclosing groups' frames and a `Vec<GroupName>` — built by `parse_pattern` and freed there on every path, since a
leaked `wild` block traps at exit (D-151). `Frame` and `GroupName` own nothing and `#[derive(Copy)]`
(`check_vec_elements_own_nothing` clears both). A frame's two lists are linked by rewriting the node before
(`ast_get`, then `ast_set`), and its last atom is PENDING, linked only when the next atom, `|`, `)` or the end
arrives, so a quantifier wraps it in place. Measured at `5fbaf4a`: a program importing `syntax.npk` still owes
`core`'s eleven arms, no new undefined symbol appears, and `tests/unit/parse_grammar.npk`'s fifty-nine shapes pass
at −O0 and through `opt -O2`; the stack is unbounded until cycle 0.1.2, the pattern's length bounding it, and 250
nested groups parse (`parse_limits.npk`).

*Alternatives declined:* **recursive descent** — RX-032, and a deep pattern would be a blown stack rather than a
refusal; **children gathered in a side array and copied at the close** — a second allocation per group and a
second pass; **the node before the last kept per frame, so a quantifier relinks it** — two fields where pending
is one, and the wrapped atom's link undone; **a frame per alternative** — a group owns its alternatives, and one
frame per group is what 0.1.2 bounds by `NREGEX_NEST_DEPTH`.

### RX-183 — a pattern is UTF-8 text checked whole before the grammar, and every character is a literal but the twelve metacharacters
> **SUPERSEDED IN PART by RX-205 (2026-10-01)** — *"`\` before ASCII punctuation is that punctuation"*, for `<` and `>`
> only: Rust's `regex` and GNU `grep` read `\<` and `\>` as word assertions, so each is refused (`SYNTAX.md` Y-40's
> note). Every other punctuation is as this decision says.

**2026-09-27, cycle 0.1.1 (the plan's PD-27)** — `SYNTAX.md` Y-28, per RFC 3629 (`meta/research/CURRENCY.md`).
`parse_check_encoding` runs after the length and before the walk, and refuses the first ill-formed sequence as
`InvalidPatternEncoding` with its offset, the bytes read through the one that broke it, and that byte (0 when the
pattern ended inside the sequence) — one case per way to be ill-formed in `tests/unit/parse_encoding.npk`, and
every boundary of the table decoded. The metacharacters are `\ . ^ $ | ? * + ( ) [ {`; a bare `]` or `}` is a
literal; `\` before ASCII punctuation is that punctuation (Y-2), and `\` as the last byte is `TrailingBackslash`.

*Alternatives declined:* **decode only inside a literal**, Y-11's first reading — an ill-formed byte in a group
name or after `\` would then be reported as another kind, and each later subcycle would re-check what 0.1.1 had
not; **a bare `]` or `}` refused** — §1 gives neither a meaning outside a class or a bound, and Rust and PCRE take
both literally; **an unfinished `{` taken as a literal**, PCRE's rule — a pattern whose meaning turns on whether a
brace completes is the context-dependence Y-2 refuses.

### RX-184 — quantifiers: the six forms and the lazy `?`, a `{` always a bound, and each refusal decided at the quantifier's first byte
> **SUPERSEDED IN PART by RX-213 (2026-10-02)** — *"a `{` that is not `{n}`, `{n,}` or `{n,m}` in decimal digits is
> `BadRepeatBounds` (detail 0)"*: after `\b` or `\B`, detail 2, which RX-215 gives only when a letter follows the `{`.
> Every other part is as this decision says. *(Marked 2026-10-08, cycle 0.1.6a — the cycle audit's S2: the marker was not
> added when RX-213 landed.)*

**2026-09-27, cycle 0.1.1 (the plan's PD-28)** — `SYNTAX.md` Y-32. `NothingToRepeat` and `DoubleRepeat` are decided at
the quantifier's first byte, before a bound is read; a `{` that is not `{n}`, `{n,}` or `{n,m}` in decimal digits
is `BadRepeatBounds` (detail 0); a bound over `NREGEX_REPEAT_MAX` is `RepeatTooLarge` at the number, the value
saturating as it is read (`a{99999999999999999999}` cannot overflow); a minimum over the maximum is
`BadRepeatBounds` (detail 1); a `+` straight after a quantifier is `AtomicGroupUnsupported` (Y-30). On the bound and
one past it: `a{1000}` parses, `a{1001}` is refused (`parse_grammar.npk` case 31, `parse_refusals.npk` case 33).

*Alternatives declined:* **the atom checked after the bound is read** — `{x` at the start would report bad bounds
where the author most likely meant a brace; **`{,n}` accepted as `{0,n}`** — not in §1, and one spelling is the
rule; **a possessive `+` read as `DoubleRepeat` until 0.1.5** — a kind 0.1.5 would change in a function 0.1.1
writes; **`RepeatTooLarge` at the `{`** — the number is what is wrong.

### RX-185 — groups: numbered at the `(`, named by §1's `Name`, closed innermost-first — and the refusals of §8 a group head spells are made at the head
> **SUPERSEDED IN PART by RX-193 (2026-10-01)** — for a `(` that would nest groups deeper than
> `NREGEX_NEST_DEPTH` only: *"the 251st is `TooManyCaptureGroups` at its `(`"*, and a head's refusal *"made
> where the head is read"* — that `(` is `NestTooDeep` before its number is taken or its head read (`SYNTAX.md`
> Y-35). Every other group is as this decision says.

**2026-09-27, cycle 0.1.1 (the plan's PD-29)** — `SYNTAX.md` Y-29 and Y-30, with Y-6, Y-7 and Y-8. The capture index
is handed out at the `(`, named groups included; the 251st is `TooManyCaptureGroups` at its `(` (detail the bound,
`parse_limits.npk`); a name is checked character by character and then against every earlier one
(`DuplicateGroupName`, detail the first group's number); `UnclosedGroup` names the innermost open `(` and says how
many are open; `(?P<` and `(?'` are `WrongNamedGroupSpelling`. The group-head refusals of §8 — lookaround, the
atomic group, recursion, `(?P=` and the comment group — are made where the head is read, with the kinds §8 names;
0.1.5 keeps the escape-shaped ones, the rejection tests and `regex_escape`.

*Alternatives declined:* **`UnclosedGroup` at the outermost `(`** — the innermost is the one whose `)` the author
forgot last and the one the walk holds; the detail still says how many; **`DuplicateGroupName` at the first
name** — the second is where the collision was written; **the group's number as `TooManyCaptureGroups`' detail** —
the bound is what the author can act on, and the number is one more; **§8's heads left provisional until 0.1.5** —
0.1.1 writes the dispatch, and a provisional branch there would be rewritten.

### RX-186 — until its parser exists, a class, an escape and a flag are refused provisionally, with the kind their parser gives an unknown member
> **SUPERSEDED IN PART by RX-193 (2026-10-01)** — for a `(` that would nest groups deeper than
> `NREGEX_NEST_DEPTH` only: it is `NestTooDeep` before the flag or other head it opens is read (`SYNTAX.md` Y-35).

**2026-09-27, cycle 0.1.1 (the plan's PD-30)** — `SYNTAX.md` Y-31. `[` is `UnclosedClass` until 0.1.3; `\` before
anything but ASCII punctuation is `UnknownEscape` until 0.1.4; `(?` before a flag, or anything Y-29 and Y-30 do not
name, is `UnknownFlag` until 0.1.4. Each is what that parser answers for a member it does not know, and 0.1.1's
knows none. No test pins one but `(?P` before a byte no head names — `UnknownFlag` at the `P`, which 0.1.4
cannot change, since `P` is no flag (`parse_refusals.npk` case 64); `parse_pattern` is not public until cycle
0.10, so no consumer meets one.

*Alternatives declined:* **the constructs read as literals** — a silent wrong acceptance, and Y-2 forbids `\q` as
`q`; **a temporary kind** — a thirty-seventh kind to retire at 0.1.5, and a closed list that changes twice;
**tests pinning them** — 0.1.3 and 0.1.4 would delete the tests they inherit.

### RX-187 — `pattern_error_text` says what is wrong, at which byte, and what to write instead; written with the kinds, in `src/syntax/`, from cycle 0.1.1

**2026-09-27, cycle 0.1.1 (the plan's PD-31)** — `SYNTAX.md` Y-34; the author's standing bar for a library's errors
(the dispatch of 2026-09-27: what is wrong, where, and the likely fix where the library can tell). `API.md` §1's
`pattern_error_text(PatternError) -> string` is written in `pattern_error.npk`, one `pick` arm per kind, each a
sentence naming the kind and `at byte` the offset, then the reason, then the fix: an unclosed group says add a `)`
or write `\(`; `(?P<name>…)` says it is Python's spelling and gives `(?<name>…)`; the 251st group says to make the
groups not read non-capturing; a possessive or atomic construct says nregex never backtracks and every search
takes linear time. It reads only the four fields — `detail` carries the quantifier's byte, the bound, the first
group's number — and builds in a `Bytes`, so no division and no new undefined symbol (measured: a program calling
it references `npk_string_concat` and `npk_string_from_bytes`, both on B-2's reviewed list, and owes no new arm).
`tests/unit/pattern_error_text.npk` holds twenty-two of 0.1.1's sentences to the letter and every kind to a
sentence naming its byte; `src/lib.npk` re-exports it at 0.10.5.

*Alternatives declined:* **the text at cycle 0.10.5, as the roadmap had it** — a message written nine cycles after
its kind is written by someone who no longer knows what the author meant; **the pattern as an argument, to quote
the construct** — `API.md` fixes the signature, and a caller holding the pattern can slice it at `offset` and
`span_len`; **a template with `&{…}`** — it references `npk_int_to_string`, a symbol B-2's reviewed list does not
hold, where `bytes_put_uint` already exists for this; **one generic sentence for the kinds later subcycles
produce** — every kind renders a real sentence now, and each subcycle holds its own to the letter when it
produces them.

## The bound on the type — cycle 0.1.1b, open question O-R3

### RX-188 — `Vec` is `Vec<T: Copy>`: S-23a is the type's, so an owning element is refused wherever it is written, and the units that measured one retire

**2026-09-28, cycle 0.1.1b (the plan's PD-32), at compiler `5fbaf4a` — open question O-R3, decided.** It
supersedes in part RX-155 — *"nothing in the language keeps an owner out"*, its per-verb units and its reason
for leaving `tests/` outside the check; RX-168 — its declined alternative `struct:Vec<T: Pod>`, O-R3 itself;
RX-177 — its fixture's single site; RX-158 — *"so do its verbs, units and table"*; and RX-110 — its exception
*"any future owning `Vec<GroupInfo>` or `Vec<string>`"*. Their rules stand.

**The gate O-R3 named is met** — the compiler refuses an impl that adds `move` to a lent parameter,
`NITPICK-TYPE-014` (RX-176), and `vec_get`'s bound is the prelude's `Copy`, a marker with no method to
mis-declare (RX-177) — **and the shape was measured before it was taken**, at `5fbaf4a`:

- **`pub struct:Vec<T: Copy>` compiles, and a generic naming `Vec<T>` must state the bound too**: without it
  each of the thirteen verbs that names `Vec<T>` is `NITPICK-TYPE-017` at its definition, *"`T` does not
  implement `Copy`, which `Vec`'s parameter `T` requires"*. With it, every file instantiating `Vec` at a scalar
  or a `Copy` struct compiles unchanged, and **the IR of all seventy-two programs and roots that compile before
  and after is byte-identical**: the bound changes no code.
- **At `Vec<string>` it is refused at every site**: where the type is first written, each turbofish, and each
  verb's call, the diagnostic naming the verb — `vec_owning_get_moves_out.npk`'s new body, one call per verb,
  reports fourteen. A consumer's struct field, a parameter and a generic wrapper's unbounded `Vec<U>` are refused
  the same way, and so is every element that is not `Copy` written as `T`: `Bytes`, a `Vec`, a `cstring`, a
  pointer, a slice, an optional and a fixed array.
- **What it refuses in this tree is twelve files, not O-R3's seven**: the ten `vec_owning_*` units — seven per
  verb, the managed-half pair `vec_owning_freed`/`vec_owning_leak`, and `vec_owning_freed_small_rounds` —
  `vec_unit.npk`'s `Vec<string>` section, and the rejection fixture's one site becoming fourteen.
- **The tree check misread the declaration**: `check_vec_elements_own_nothing` exempts `vec.npk`'s `Vec<T>`
  over its own parameter, and `struct:Vec<T: Copy>` put the bound inside the brackets, so the run failed on
  the declaration as an element. The exemption now reads the parameter before its bound.
- **A fill becomes expressible**: under `T: Copy` a generic `vec_fill` that copies its `x` into each slot
  compiles and runs, where `vec_init_zeroed`'s comment records it refused `NITPICK-TYPE-046`. None is written.

**The decision.** `Vec` is `Vec<T: Copy>`, the bound repeated on every verb. The ten units are deleted: their
measurements are RX-155's table, taken at `c3bdae2`, and nothing can reach them now. `vec_unit.npk` loses its
owning section, exits 130 and 131 with it. `vec_owning_get_moves_out.npk` keeps its name — RX-155's and RX-168's
citations find it — and pins the refusal at every verb. S-23a stands; the compiler holds its "drops nothing"
half for every consumer, and an element type derives `Copy`, as `AstNode`, `Frame` and `GroupName` do.

*Alternatives declined:* **the bound on `vec_get` alone, as since RX-168** — twelve verbs still compile at
`Vec<string>`, six of them orphaning, and a harness check over `src/` is all that stands there; **the units kept
as rejection fixtures** — ten copies of one refusal, each header describing a measurement the language no longer
admits; **kept as programs over a test-only unbounded copy of `Vec`** — they would measure a type that no longer
ships, and a cycle that lifts S-23a has RX-155's table and the compiler's `List<T>` to start from; **the fixture
renamed** — its name is its history, as probe 18's was (RX-176); **`move` dropped from the `T` that `vec_push`,
`vec_set` and `vec_insert` take** — under `T: Copy` it is a copy either way, and it would change every call site
for nothing; **waiting for a consumer that needs an owning element** — none is planned, and the bound is what
keeps a later cycle from writing one by accident.

### RX-189 — `vec_free_owning` and `drop_element` are removed: a `Vec<T: Copy>` holds nothing to drop, so `vec_free` is the whole free

**2026-09-28, cycle 0.1.1b (the plan's PD-33), at compiler `5fbaf4a`.** It supersedes in part RX-144 — the guard
heading `vec_free_owning`, and that function's unit; RX-156 — its reason that the guard keeps `vec_free_owning`
from running destructors over a freed block; and RX-155 — *"the two stay apart for cost"*. The guard on
`vec_free`, and its 94, stand.

**Measured at `5fbaf4a`, over RX-188's tree.** At every `T` the type admits, `vec_free_owning` does what
`vec_free` does, in O(`count`) where `vec_free` is O(1): each `move(v.items[j])` is a copy and `drop_element`
drops nothing. Its callers were the ten retired units, `vec_unit.npk`'s retired section, and
`tests/unit/vec_oob_free_owning_after_free.npk` — RX-144's unit for the guard's worse half, a walk over a freed
block that no `T: Copy` can make run a destructor. `src/` never called it, `core.npk` re-exported it, and the
public surface, `src/lib.npk`, never reached it. Removed, every remaining program's IR is RX-188's but for what
a removal moves, the site-line table and the generated drops' numbering; `vec_oob_free_twice.npk` holds 94.

**The decision.** `vec_free_owning`, `drop_element`, `core.npk`'s re-export and
`vec_oob_free_owning_after_free.npk` are deleted, and `vec.npk` keeps a paragraph where the managed half was.
`vec_free` is the one free.

*Alternatives declined:* **kept as an alias of `vec_free`** — two names for one operation, one of them saying
"owning" at a type that cannot own; **kept until a cycle lifts S-23a** — that cycle needs the compiler's
`List<T>` discards (RX-155), and the history keeps this one; **its unit kept, pointed at `vec_free`** —
`vec_oob_free_twice.npk` is that unit already.

### RX-190 — `check_vec_elements_own_nothing` stays: the belt for "drops nothing", which the compiler holds since RX-188, and the rule for "holds no block of its own", which `Copy` does not ask

**2026-09-28, cycle 0.1.1b (the plan's PD-34), at compiler `5fbaf4a`.** It supersedes in part RX-158 — its
declined alternative *"the compiler's own ownership predicate — reachable only by building the compiler"*: the
type's `T: Copy` reaches it at every build. O-R3 expected the check to retire into a belt; measured, it is half
belt.

**Measured at `5fbaf4a`, each shape planted in a copy of `src/`.** A `#[derive(Copy)]` struct holding a pointer
(`int64->`) or a slice (`uint8[]`) compiles as a `Vec` element — the compiler's `Copy` passes such a member by
kind (D-327) — and the check fails it by name: a pointer holds a block. The reverse: a struct of scalars that does not derive `Copy` is
`NITPICK-TYPE-017` as a `Vec` element, and the check clears it. So neither refusal contains the other. As `T`
itself a pointer, a slice, an optional, a `cstring` and an array are all refused by the compiler, and a
`#[derive(Copy)]` over a `cstring` member is `NITPICK-DERIVE-006` since D-328 made `cstring` own.

**The decision.** The check keeps its mechanism, its scope (`src/`) and its place in the run; its docstring, its
failure message and `TESTING.md`'s row say which half is whose: the compiler's `Copy` for "drops nothing", with
the check as its belt, and the check alone for "holds no block of its own".

*Alternatives declined:* **retiring the check, as O-R3 foresaw** — `Vec<Pp>` over a pointer-holding `Copy`
struct would then pass the run, the second half of S-23a unchecked; **narrowing S-23a to what `Copy` asks** — a
`Vec` of pointers is a `Vec` of blocks some other owner must free, which is the orphaning RX-155 measured, one
level down; **teaching the check the compiler's `Copy` rule** — a second copy of a rule the compiler already
enforces, which is what a belt is for and a rule is not.

## The explicit stack's bound — cycle 0.1.2

### RX-191 — RX-032's reason, measured: a recursion deeper than its stack traps `StackExhausted` since `c3bdae2`, and the explicit stack stands because a trap ends the whole program

**2026-10-01, cycle 0.1.2 (the plan's PD-35), at compiler `5fbaf4a`.** It supersedes in part RX-032 — its reason,
*"the language has no stack-depth guard — the failure is a segfault, not a controlled stop"* — and the same reason
restated in `SAFETY.md` S-18, `src/core/limits.npk` and probe 05. Each was true of the compiler RX-032 was written
against. Since `c3bdae2` every function the compiler emits carries LLVM's split-stack prologue, which compares the
stack against its thread's limit before the function's frame exists — only a leaf with no frame skips it, and a
recursive function is no leaf — and `failsafe` runs on a stack of its own (the compiler's D-305).

**Measured at `5fbaf4a`.** A recursive descent over nested `(` — one native frame per level, each holding a copy
of a frame the size of `parse.npk`'s `Frame` — handed more levels than its stack holds leaves through `failsafe`'s
`StackExhausted` arm, at −O0 and through `opt -O2`, never on a signal: `tests/probe/probe19_native_recursion_traps.npk`,
2^20 levels, exit 106 at both legs. The depth it stops at, the probe's `LEVELS` set by `sed`: it runs 16 911
levels and traps at 16 912 at −O0, and runs 52 425 and traps at 52 426 through `opt -O2`, each edge the same on
twenty runs of each side, because the main thread runs on the floor's own 8 MiB stack whatever the shell's
`ulimit` (D-305 (3)). So 10 000 levels trap at neither leg, and 65 536 — the longest pattern
`NREGEX_PATTERN_BYTES` admits, all `(` — traps at both.

**The decision.** RX-032 and S-18 stand, and their reason is restated. A trap is a controlled stop of the WHOLE
PROGRAM — `failsafe` does not return — so a consumer handed a hostile pattern would lose its process where S-9
owes it a `PatternError`. And the depth a recursion survives is the frame the optimiser sizes and the stack the
caller's thread was given — a spawned thread has 2 MiB (D-305 (3)) — and differs threefold between two legs of
one program, so the library cannot know it. The parser holds its nesting on an explicit stack and refuses at
`NREGEX_NEST_DEPTH`. Probe 19 records the language's answer and re-derives it on every run.

*Alternatives declined:* **leave RX-032's reason as written** — a rule whose stated reason is false is argued
with on that reason, and the next reader to meet the trap would take the rule for obsolete; **retire the explicit
stack because the language now stops a runaway recursion** — the stop is the process's and not the parse's, and
S-18 is about adversarial input, which is owed a refusal; **record the measured depths as the library's bound** —
they are the optimiser's and the thread's, a factor of three apart between the two legs; **a dated note on RX-032
without a probe** — a pin-dependent measurement recorded as a permanent property is RX-120's lesson, and a probe
re-measures it on every run.

### RX-192 — `check_no_recursion`: no function under `src/` is on a call cycle — every cycle, across files, over all of `src/`

**2026-10-01, cycle 0.1.2 (the plan's PD-36), at compiler `5fbaf4a`** — `SAFETY.md` S-18 and S-19's belt. The cycle
README asked for "a tree check that greps `src/syntax/` for a function that calls itself". The check built reads
wider on three counts, each measured: a mutual pair recurses as deep as a self-call does; two modules may import
each other, so a pair may span two files — a call cycle through `use` in both directions compiles and runs at
`5fbaf4a`; and S-19's walks will be written in `src/hir/` and `src/compile/`, where a check over `src/syntax/`
would never look.

**The check.** Every `func:` under `src/`, read in the blanked text (`lexical.py`); a call is a name, an optional
turbofish and `(`, resolved to its own file's function of that name, else to every function of that name under
`src/`; Tarjan's components, computed iteratively; a component holding a cycle fails, each member named at its
declaration. At this commit: 90 functions in 17 files, 135 distinct edges, no cycle. **And the compiler agrees,**
asked through its own recursion analysis — a `decreases` on a function in no recursive group is
`NITPICK-TYPE-075` (its D-304 (5)): with `decreases 0i64` written on every function of a copy of `src/`, all 90 are
TYPE-075, while a planted self-call and a planted mutual pair are not. Self-check case 30 plants five recursions
and a clean control; it goes red against a check that reads self-calls alone, and against one that resolves a
call to every function of its name rather than to its own file's first.

**What it cannot see,** stated in its docstring: a call through a `dyn` receiver or a function value, which the
compiler's analysis cannot see either — `src/` holds no `dyn`, no trait, no `impl` and no `func` as a type, and its
90 functions have 90 names (measured), so the graph is exact today; and whether a recursion's depth is one an input
controls, so it refuses every recursion — one that must exist is a decision, not an edit to the check.

*Alternatives declined:* **the README's grep of `src/syntax/` for a self-call** — blind to a mutual pair, to a pair
across files and to every directory but one, while S-19's walks come next; **the compiler's own analysis as the
check** — exact, but it rewrites the source it judges and costs a compile per module where every other tree check
reads text; it stays the plan's cross-check; **the call graph in the emitted IR** — `irscan.py` reads only the calls
to the floor (B-2's second layer), and widened it would give the emitter's names rather than the source's places,
at a compile per root; **the gate unit alone** — it shows the
parser refusing on the patterns it builds, and nothing about a function it never calls.

### RX-193 — `NREGEX_NEST_DEPTH` is decided at the `(`: a `(` that would nest groups deeper than 250 is `NestTooDeep` there, before a byte after it is read
> **SUPERSEDED IN PART by RX-198 (2026-10-01)** — the sentence it quotes, which named a `(` and groups alone: a `[` is
> refused at the same bound, counted with the groups around it, and the sentence names both (`SYNTAX.md` Y-35). Every
> `(` is as this decision says.

**2026-10-01, cycle 0.1.2 (the plan's PD-37), at compiler `5fbaf4a`** — `SYNTAX.md` Y-35, Y-9's bound. It supersedes in
part RX-185 and RX-186, for a `(` past the bound only, and completes RX-182's *"the stack is unbounded until cycle
0.1.2"*. `open_group`'s first line refuses a `(` read while the stack holds `NREGEX_NEST_DEPTH` frames:
`NestTooDeep` at that `(`, length 1, detail the bound. So no frame past the bound is pushed, nothing past that `(` is
read, and the parse stops where the bound is rather than where the pattern ends — probe 05's property, in the
parser. `pattern_error_text` says what to do, held to the letter by `tests/unit/pattern_error_text.npk` case 23:
*"nesting too deep at byte 250: this `(` would nest groups 251 deep, and they may nest at most 250 deep
(NREGEX_NEST_DEPTH). Nest fewer groups: a non-capturing group around one item, as in `(?:a)`, can be written without
it."*

**Measured at `5fbaf4a`** (`tests/unit/parse_limits.npk` cases 15–18). 250 nested groups parse, as before; 251
nested `(?:` are `NestTooDeep` at byte 750; 251 nested `(` are `NestTooDeep` at byte 250 — where the unbounded
parser answered `TooManyCaptureGroups` at the same byte, the capture bound being 250 too, so the deep pattern an
attacker writes first was refused for a reason that was not its own; and a lookahead, or a `(?` the pattern ends
on, opened by the 251st `(` is `NestTooDeep` at that `(`. No node is built in any of the four.

*Alternatives declined:* **the check in `push_group`, as 0.1.1's §8 suggested** — it runs after the head is read
and after the capture number is taken, so `(` repeated 10 000 times would answer `TooManyCaptureGroups` and never
its depth, and a named group's name would be read and judged first; **after the head is read and before the number
is taken** — a head refused at depth 251 would answer for its head and an accepted one for its depth, two rules
where one serves; **at the `)` or at the pattern's end** — the stack would hold every level first, which is what
the bound exists to prevent (probe 05: checked before the push); **a bound on the stack's bytes rather than its
frames** — `SAFETY.md` §5 names the count, and the count is what a pattern's author can read and act on.

### RX-194 — the gate: 10 000 levels, and the deepest pattern the length bound admits, are `NestTooDeep` at the 251st `(`, forty runs a leg; "not on a signal" is the runner's reading, shown red by self-check case 31

**2026-10-01, cycle 0.1.2 (the plan's PD-38), at compiler `5fbaf4a`.** The cycle README's gate — *"a 10 000-level
pattern produces a clean refusal, and a wrapper script confirms the process exited normally rather than on a
signal"*, with `// stress: 40` *"because a stack overflow is timing-shaped"* — is `tests/unit/parse_nest_deep.npk`,
and two of its premises were measured otherwise (RX-191). A recursive descent of the parser's frame size runs 10 000
levels at both legs and returns, so the unit adds the deepest pattern there is: `(` 65 536 times, the whole of
`NREGEX_PATTERN_BYTES`, where such a recursion traps at both legs; and `(?:` 21 845 times and `a`, where no capture
bound plays a part. Each is `NestTooDeep` at the 251st `(` — bytes 250, 250 and 750 — one byte long, its detail the
bound, with no node built. Against the unbounded parser the unit exits 2: the first pattern answered
`TooManyCaptureGroups`. And the depth a recursion traps at is the same on every run, so `stress: 40` holds the parse
itself to one answer, forty runs a leg — about half a second in all, measured.

**The wrapper is the runner.** `stages.run_binary` runs every program, reads a killed process as `0 - signal` and
requires the expected exit on every run, so `expect-exit: 0` is met by a normal exit alone. What nothing showed was
that the reading works: self-check case 31 runs stand-ins killed by SIGSEGV and by SIGKILL, three runs each, and
requires each red with its `0 - signal` named and a control exiting 0 to pass; against a runner that read a killed
process as a clean exit it fails.

*Alternatives declined:* **10 000 levels alone, as the README asked** — a recursive parser would pass it too, so it
could not tell the explicit stack from recursion; **a separate wrapper script** — a second runner judging one unit
by rules of its own, where the runner's reading needed a case, not a twin; **dropping `stress: 40` when its reason
was measured false** — the forty runs cost half a second and hold the parse to one answer; **the deep patterns in
`parse_limits.npk`** — `stress: 40` would then rerun every bound's cases, its two 65 536-byte length cases among
them, forty times a leg.

### RX-195 — B-4's two copies each carry the manifest, and one sits below a decoy: a `TMPDIR` inside a project no longer fails the step, and a copy that forgets its manifest fails on every run

**2026-10-01, cycle 0.1.2 (the plan's PD-39), at compiler `5fbaf4a`** — `BUILD.md` B-4. The cause of what cycle 0.1.1b
measured and left unestablished (its plan's §4 and §6): with `TMPDIR` inside this repository the `repro` step failed
on an unchanged tree in each of the nineteen self-check cases whose inner run reaches it — the other seven test an
instrument directly or, as case 24 does, stop at the toolchain check first — 57 472 against 57 792 bytes with the
scratch at `.internal/n12/tmp`, the sizes moving with its name; so the self-check failed and no suite ran, while
under `/tmp` it passed. The
compiler renders every source path relative to its manifest root, the first directory holding `nitpick.toml` above
the main file, or the main file's directory where there is none (its D-236, read in `front_set_root` at
`5fbaf4a`; this repository's B-4c). `repro` copied `src/` and the entry's directory and no manifest, so the walk
went on past each copy: under `/tmp` it found none and each copy's entry directory was its root, alike; inside
this repository it found the repository's own, and the copies' two directory names, 32 characters apart, entered
every path. No directory above this repository holds a manifest (measured), which is why only a `TMPDIR` inside a
library met it.

**The decision.** Each copy carries the tree's `nitpick.toml`, so each is its own manifest root and renders its
paths as the tree it came from — a copy's emission is the in-tree build's, byte for byte (measured), where before
it rendered paths no build of this library ever makes. And the second copy sits below a decoy manifest on every
run, so a copy that forgot its own would take the decoy for its root and fail the step every time, whatever
`TMPDIR` is. Measured: without the copy, under the decoy, the step fails under `/tmp` (57 250 against 57 822
bytes); with it, the two copies are byte-identical under `/tmp` and inside the repository, and the full run is
`242/242` GREEN with `TMPDIR` inside it. So a session needs no rule about `TMPDIR`: it may sit anywhere.

*Alternatives declined:* **refuse a `TMPDIR` inside a project, by name** — a clear message, and B-4 would still test
only the no-manifest branch, a configuration this library is never built in; **state the cause and a rule, `TMPDIR`
left at its default** — a trap for every session that keeps its scratch inside its write boundary, as the workbench
asks; **mask the site paths in the comparison** — B-4 exists to see a path in the emission, and a mask would hide a
real one; **build the copies under a fixed `/tmp`** — it overrides the environment the session chose and still
tests the no-manifest branch; **a self-check case that sets `TMPDIR` inside a project** — one environment, tested
in one case; the decoy puts the failing shape inside every run's own scratch.

## Classes — cycle 0.1.3

### RX-196 — class operators share one precedence and apply left to right, union binding tighter and negation last: Rust's order and UTS #18's, in place of Y-17's

**2026-10-01, cycle 0.1.3 (the plan's PD-40)** — `SYNTAX.md` Y-17, per `meta/research/class-syntax-reference-engines.md`,
as of 2026-10-01. Y-17 ranked the operators — union, then `--`, then `~~`, then `&&` — "because it differs between
engines". It does differ, and Y-17's order is no engine's. Rust's `regex` 1.13.1, this library's closest neighbour
(`COMPAT.md` §1), binds ranges, then union, then *"intersection, difference, symmetric difference. All three have
equivalent precedence, and are evaluated in left-to-right order"*, then negation. UTS #18 revision 25 requires no order,
binds every operator at one level in its own example syntax, names union binding tighter as the other choice, and tells
users to bracket. Measured with regex-syntax 0.8.11: `[a&&a~~b]` is `a` and `b` in Rust and would be `a` alone under
Y-17; `[ab~~b--a]` matches nothing in Rust and would match `a`. A pattern written for Rust would compile here and match
differently, with no word said.

**The decision.** Members side by side are their union, binding tightest; `&&`, `--` and `~~` share one precedence and
apply left to right, each to everything before it and the union after it; `^` complements the whole class, last. So
`[a--b&&c]` is `[[a--b]&&c]`, and any other reading is one `[…]` away. A mix of `&&` and `--` alone reads the same
either way; what moves is `~~` after `&&`, and `--` after `~~`. Cycle 0.1.3's parser builds the tree in this order, and
cycle 0.3.4 evaluates the tree as built.

*Alternatives declined:* **keep Y-17 and add a row to `COMPAT.md` §2** — a pattern that compiles in both engines and
matches differently is the silent difference this library refuses wherever it can; **refuse two different operators
in one class without brackets** — UTS #18's advice to users, but Rust's own documented example,
`[\pL--\p{Greek}&&\p{Uppercase}]`, would stop compiling, and left to right is unambiguous once it is stated;
**every operator and union at one level, UTS #18's illustrative syntax** — `[ab&&cd]` would be `[[[ab]&&c]d]`, where
Rust and every engine that has the operators read `[[ab]&&[cd]]`; **decide at cycle 0.3.4, where the sets are
computed** — the parser builds the tree the precedence shapes, so the parser's subcycle is where it is fixed.

### RX-197 — a class is read once, left to right: members, ranges and the operators between unions, each shape read as Rust reads it or refused

**2026-10-01, cycle 0.1.3 (the plan's PD-41), at compiler `5fbaf4a`** — `SYNTAX.md` Y-36, Y-37 and Y-38, with Y-16 and
RX-196's order; per `meta/research/class-syntax-reference-engines.md`. It completes RX-186 for `[`, whose provisional
`UnclosedClass` it replaces, and supersedes in part RX-182 — *"one `while` over the cursor"*.

**What chose the rules.** `SYNTAX.md` §1 says what a class may hold and §5 what it means; neither says how `]`, `-` or
a doubled `&`, `-` or `~` is read where it could be two things. Where Rust's `regex`, the closest neighbour (`COMPAT.md`
§1), reads a shape one way and the backtracking engines agree, this library reads it so: `]` straight after `[` or `[^`
is a member — so `[]` and `[^]` never close, as Rust, Perl and Python read them — and `-` first, last, after a range or
after an operator is a member; `X-Y` between two codepoints is a range. Where the engines disagree, or where Rust reads
a likely mistake in silence, it refuses with a sentence saying what to write: an operator with an empty side (`[a&&]`,
`[--a]`, `[!--]` — Rust takes the empty set or a run of members, Perl and Python read the last two as ranges); a class
at either end of a range (`[\w-.]`, which Rust and Python refuse and Perl reads as members; `[[a]-z]`, which Rust reads
as members), and a `[` ending a range (`[!-[]`, which Rust reads as the range `!`–`[`), since a `[` inside a class always
opens one; and `[:` that opens no known POSIX class (`[[:alpah:]]`, which Rust reads as a nested class of its bytes,
and which this parser could not read so without going back, which its cursor does not — RX-173). Measured with regex
1.13.1: Rust accepts every pattern `tests/unit/parse_classes.npk` accepts, and over 774 codepoints reads alike each of
its classes whose set needs no Unicode table (49 of 54); of the patterns `parse_class_refusals.npk` refuses, Rust
accepts those an operator's empty side, a bracketed class before a `-` or a `[:` makes, and refuses every other.

**The tree, and the walk.** Y-27's kinds, as its note says: a class's members in order under its `Class`, or one
`ClassOp` chain folded left, each union a `Class` of its own. Perl classes and properties stay unresolved (Y-37), so the
parser reads no table and cycle 0.1 needs nothing of cycle 0.3. `parse_class`, a `while` of its own that the walk's
calls at a `[`, reads the class to its `]`: a nested `[` saves the class being read on `Parser.classes`, a
`Vec<ClassFrame>`, and its `]` takes it back — the groups' shape one level down, with no function calling itself
(`check_no_recursion`: 110 functions, no cycle). `ClassFrame` owns nothing and derives `Copy`. The stack's bound is
RX-198's.

**The text.** Each refusal says what is wrong, at which byte, and what to write instead, held to the letter by
`tests/unit/pattern_error_text.npk` (cases 24–34): `UnclosedClass` says, when the class began with one, that the `]`
after `[` was a member; `BadClassRange` says to put a `-` first or last or write `\-`; `ClassOpMismatch` names its
operator, with an example and the escape; `UnknownPosixClass` gives the form, the fourteen names — which now live in
one place, `posix_class_name`, that the parser matches and the text renders — and `\:` for a `:`;
`UnknownUnicodeProperty` names the forms a name takes.

**Measured at `5fbaf4a`.** `parse_classes.npk` and `parse_class_refusals.npk` pass at −O0 and through `opt -O2`, and
against the parser before this decision exit 1 and 3; each rule broken in a copy exits as the plan's §1.11 records —
at the case written for it, or, with the test that keeps a `-` the pattern ends on out of a range removed, by the
`OutOfBounds` trap a read past the pattern makes. No pattern reaches `EmptyClass`: every class the parser builds holds a
member — open question O-Y3.

*Alternatives declined:* **a class read inside the walk's own `while`, by a mode** — every byte of the walk would ask
which mode it is in, where a class is a sub-language that never meets a group; **recursive descent for a nested
class** — RX-032; **`[:` read as a nested class when it opens no POSIX class, as Rust reads it** — the cursor would have
to go back over the name, which nothing else asks (RX-173), and a misspelt name would be a class of its bytes; **`]`
never a member, so `[]` is `EmptyClass`** — ECMAScript's reading, which takes `[]` for a class that matches nothing
(measured, node 24), where Rust, Perl and Python read `[]a]` as `]` and `a`; **an empty side of an operator taken as
the empty set, as Rust takes it** — `[a&&]` would match nothing with no word said, and UTS #18 notes it is "common … to
require a CHARACTER_CLASS on both sides"; **a run of `-` first in a class read as members, as Rust reads `[--a]`** —
Perl and Python read the same bytes as the range `-`–`a`, so either reading surprises someone; **a `-` after a range,
or before `]`, refused** — Rust, Perl and Python read both as a `-`.

### RX-198 — groups and classes nest at most `NREGEX_NEST_DEPTH` deep together, decided at the `(` or `[` that would go deeper
> **SUPERSEDED IN PART by RX-216 (2026-10-08)** — the sentence it quotes, *"the `(` or `[` here would nest groups and
> classes 251 deep"*, false for a `(` that begins `(?i)` or `(?#` at the bound: the sentence says what is open around
> the refused byte. The bound and where it is decided are as this decision says.

**2026-10-01, cycle 0.1.3 (the plan's PD-42), at compiler `5fbaf4a`** — `SYNTAX.md` Y-35's last sentence, *"a class
nests too from cycle 0.1.3, which bounds it"*, and `SAFETY.md` S-18. It supersedes in part RX-193 — the sentence that
decision quotes, held by `tests/unit/pattern_error_text.npk` case 23, which named a `(` and groups alone.

**The decision.** A `[` that would open a class while groups and classes — 250 together — are open around it is
`NestTooDeep` at that `[`, length 1, detail the bound, before a byte after it is read. The count is one sum: the groups
open, `p.stack.count`, and the classes open, the enclosing ones on `Parser.classes` and the one being read. A `(` is
checked as RX-193 checks it, since no class is open where a `(` opens a group, and a POSIX class's `[:` opens no class.
So the tree cycle 0.2 walks nests at most 250 groups and classes deep. The sentence names both: *"nesting too deep at
byte 250: the `(` or `[` here would nest groups and classes 251 deep, and they may nest at most 250 deep
(NREGEX_NEST_DEPTH). Nest fewer: write `(?:a)` as `a`, and `[[a]]` as `[a]`."*

**Measured at `5fbaf4a`.** 250 nested classes parse and the 251st `[` is `NestTooDeep` at byte 250; so is a `[` inside
250 groups, and the 126th `[` inside 125; 249 groups around a class parse (`parse_limits` cases 19–24). The gate,
forty runs a leg: `[` 10 000 times with 10 000 closers, `[` 65 536 times, and 200 groups then `[` 10 000 times, each
`NestTooDeep` at byte 250 (`parse_nest_deep` cases 7–12).

*Alternatives declined:* **a bound of its own for classes** — a second number for one hazard, and 250 groups could then
hold 250 classes, 500 levels where every walk was promised 250; **the two counted apart under one constant** — the same
500; **the sentence left naming a `(`** — false for every refusal at a `[`, and the text is built from the four fields,
none of which says which byte it was (Y-34); **a detail that says which** — a sentinel inside the bound's own domain,
where `RegexOptions` may set the bound (`SAFETY.md` S-12); **each operator counted as a level, as Rust's nest limit
counts every node** — a class's operators fold into a chain one node deeper per operator, which the pattern's length
already bounds, and a flat `[a--b--c…]` would be refused for its length; S-19's walks hold their own stacks for it.

### RX-199 — a Perl class and a property are atoms outside a class too, as Y-27 names them

**2026-10-01, cycle 0.1.3 (the plan's PD-43), at compiler `5fbaf4a`** — `SYNTAX.md` Y-37 and §1's `Atom`. Y-27 says a
`PerlClass` is *"`\d` `\w` `\s`, in a class or out"*, but §1's grammar lists `PerlClass` and `UnicodeClass` only among
a class's items, its `Atom` naming neither, and the cycle 0.1 README gives cycle 0.1.4 *"every escape in §1's `Escape`
production"*, which holds neither either — so `\d` outside a class was no subcycle's. It is this one's, which reads
the same two inside a class: outside one, `\d \D \w \W \s \S` and `\p…` `\P…` are atoms — a `PerlClass` or a
`UnicodeClass`, unresolved, which a quantifier may repeat — with Y-37's refusals at the `\`.

**Measured at `5fbaf4a`.** `tests/unit/parse_classes.npk` cases 70–77 and `parse_class_refusals.npk` cases 56–61 pass
at −O0 and through `opt -O2`, and `pattern_error_text.npk` case 36 holds the sentence outside a class; against the
parser before this decision the first two exit 70 and 56, each pattern refused provisionally, `UnknownEscape` (Y-31).

*Alternatives declined:* **left to cycle 0.1.4, with the other escapes** — the escapes 0.1.4 reads name codepoints and
anchors, and these two are read by the code the class parser already holds; **inside a class only** — `\d+` is the
commonest class there is, and Y-27 already says *"in a class or out"*; **each wrapped in a `Class`, so one class kind
stands outside a class** — a node per atom that no reader asks for, where cycle 0.2's desugaring makes every class a
`Class` anyway (`HIR.md` H-5).

### RX-200 — a whole class in a POSIX class's own form, `[:alpha:]`, is refused, saying a POSIX class goes inside a class

**2026-10-01, cycle 0.1.3 (the plan's PD-44), at compiler `5fbaf4a`** — `SYNTAX.md` Y-38. POSIX puts a POSIX class inside
a bracket expression, `[[:alpha:]]`, and so does this library (§5.1). Written as a class of its own, `[:alpha:]` is
valid in every engine — a class of `:`, `a`, `h`, `l` and `p`, measured in Rust's `regex` 1.13.1 — and is almost never
what was meant. GNU `grep` 3.11 refuses it, saying *"character class syntax is [[:space:]], not [:space:]"*: a bracket
expression whose first and last members are `:`, with a member between that is not, and no range, class or collating
element in it — the rule its source states, and thirty-one shapes measured
(`meta/research/class-syntax-reference-engines.md`). A pattern that compiles and matches something other than what was
written is the surprise this library refuses where it can (`\Z`, Y-18; `(?P<n>…)`, RX-017).

**The decision.** An outermost class, negated or not, whose every member is one codepoint written as itself, the first
and the last of them `:` and another not — `[:alpha:]`, `[:^digit:]`, `[^:alpha:]`, and a misspelt `[:alhpa:]` too — is
`UnknownPosixClass` at its `[`, spanning the class. A range, an escape, a nested, POSIX or Perl class, a property or an
operator in it makes it a class written as one. When the bytes between the colons, less a leading `^`, are one of §5.1's
names, the detail is that name's place plus one and the sentence names the POSIX class: *"POSIX class outside a class at
byte 0: `[:alpha:]` is the POSIX class alpha only inside a class, and written as a class of its own its bytes are its
members, `:` and the letters in `alpha`. Write `[[:alpha:]]` for the POSIX class, `[[:^alpha:]]` for its complement, or
`[\:alpha:]` for its bytes."* Otherwise the detail is 0 and the sentence is the one a misspelt name inside a class gets,
which ends *"Write `\:` to match a `:`"* — and a `\:` at either end makes a class written as one, as every escape does.
`[::]`, `[:::]`, `[:alpha]`, `[a:alpha:]`, `[:a-z:]` and `[:[:digit:]:]` are read as their members, as GNU `grep` reads
them; inside a class, `[:alpha:]` is the POSIX class. `grep`'s brackets have no escape, nested class or operator — a `\`
is a member there, so it refuses `[:foo\:]` and `[:\d:]`, and `&&` is two members — and a class holding one is read here
as Rust reads it.

**Measured at `5fbaf4a`.** `parse_class_refusals.npk` cases 62–75, `parse_classes.npk` cases 78–90 and
`pattern_error_text.npk` cases 37 and 38 pass at −O0 and through `opt -O2`; against the parser before this decision the
first and third exit 62 and 37. Of the thirty-one shapes GNU `grep` 3.11 was asked, the parser reads twenty-seven as
`grep` does — it refuses twelve and reads fifteen as their members — and the four it reads otherwise each hold an
escape or an operator.

*Alternatives declined:* **accept it, as Rust does** — a class that matches five bytes where every letter was asked for,
with no word said; **refuse only the fourteen names** — a misspelt `[:alhpa:]` would then be a class of its bytes, the
same surprise; **refuse every outermost class whose members begin and end with `:`** — `[:a-z:]` and `[:[:digit:]:]`
are classes written as classes, and `[:foo\:]` is the refusal's own advice followed; **refuse every outermost class that
begins with `:`** — `[:;,]` is a class of punctuation someone means; **a kind of its own** — `UnknownPosixClass` is the
POSIX class's kind already, and its detail says which case.

### RX-201 — under `x`, white space and `#` inside a class are refused: the engines disagree, so neither reading is guessed — open question O-Y2, decided

**2026-10-01, cycle 0.1.3 (the plan's PD-45)** — `SYNTAX.md` Y-39, per `meta/research/class-syntax-reference-engines.md`,
as of 2026-10-01. O-Y2 asked whether `x` mode ignores white space inside a class and recommended *"do not, matching
Rust, and refuse `xx` with a message naming the escape"*. Its premise is false: Rust's `regex` 1.13.1 ignores white
space "everywhere, including within character classes", and a `#` comment there too — measured, `(?x)[a b]` is `a` or
`b`, and `(?x)[a#b]` an unclosed class — and so does Java's `COMMENTS`. Perl's `/x`, PCRE2's `x`, Python's `VERBOSE` and
.NET's `IgnorePatternWhitespace` keep both as members, and Perl's and PCRE2's `xx` ignore a space or a tab only. So
`(?x)[a b]` matches a space in four engines and not in two, and the recommendation would have read Rust's patterns
otherwise than Rust, with no word said.

**The decision.** Under `x`, a white-space byte or a `#` inside a class is refused at that byte rather than read either
way, so a pattern from either family is told, not reinterpreted: `\x20` writes a space and `\#` a `#`. Outside a class
`x` does what §4 says. `(?xx)` is a flag written twice — cycle 0.1.4's, and Rust refuses a repeated flag — whose
sentence can say what `xx` means elsewhere and what to write here. Cycle 0.1.4, which parses flags, makes the refusal,
adds its kind to §9 and holds its sentence to the letter; until then no flag turns `x` on (Y-31), so the parser does
not change here.

*Alternatives declined:* **keep white space as members, the recommendation's reading** — Perl's, Python's and .NET's,
and a silent difference from Rust and Java for every `(?x)` pattern with a spaced class; **ignore it, as Rust and Java
do** — the closest neighbour's reading, and a silent difference from Perl, PCRE2, Python and .NET, where a spaced class
is how a space is often matched under `x`; **ignore a space and a tab only, as `xx` does** — a third reading, and each
family's surprise at once; **leave it to cycle 0.1.4, with the flags** — the cycle 0.1 README puts the question with
the class parser, whose reading of a class's bytes this is.

## Escapes and flags — cycle 0.1.4

### RX-202 — `check_constants_named` reads a literal as the compiler's lexer does: every base, separator and width suffix, on either side of the comparison

**2026-10-01, cycle 0.1.4 (the plan's PD-46), at compiler `5fbaf4a`** — `SAFETY.md` S-12 (RX-062), `TESTING.md` V-20.
The check found a bound by one pattern — `<`, `>`, `<=` or `>=`, then decimal digits and one of eight width
suffixes — so it read neither a literal written another way nor one left of the comparison. The compiler's
lexer reads more (`LEXICAL_REFERENCE.md` §6.2): `_` between digits, ignored; a base suffix, `hex`, `bin`,
`oct`, and the balanced `t`, `ter`, `tri` and `n`, `non`; and every width suffix it lists. Measured at
`5fbaf4a` on one file planted in `src/core/`: `n > 1_000_000i64`, `n > 10FFFFhexi64`, `n > 0D800hex`,
`n >= 1111_0100bin`, `n < 777oct`, `1_000_000i64 < n` and `n > 1_0i64` compile, link and run, each value as
written, and the check passed the file — seven bounds, no failure.

**The decision.** A literal is what the lexer reads as one — a token that begins with a decimal digit and runs
on through letters, digits and `_` (the compiler's D-147) — and its value is the lexer's: the separators
dropped, the width suffix stripped, the base its suffix names. The check reads a literal on either side of a
comparison, never at a shift or an arrow, and passes it only when its value is one of the small values it always
passed; a token it cannot read is reported by its text, never passed. Self-check case 32 plants six spellings,
each alone — a digit-separated decimal, a hex, a binary and an octal literal, a width suffix past `u64`, and a
literal left of the comparison — each required to fail naming its text and its value, and a clean control holding
each spelling at a small value, a shift, a bound in a comment and in a string, and one in `limits.npk`. Against
the check before this decision all six pass; against a reader that skips the left side, or one that never reads
a base suffix, the case is red. `BUILD.md` B-4e's re-read takes in §6.2, which this reader mirrors.

*Alternatives declined:* **`_` added to the old pattern** — the measured case alone, leaving hex, binary, octal,
the wider widths and the left side as blind as before; **every literal above some size outside `limits.npk`,
compared or not** — another check, the one its own docstring says would be switched off within a week; **the
reader in `harness/lexical.py`** — that module finds the spans that are not code and nothing else, and one check
reads numbers; **the blindness left to the compiler** — the rule is this library's (S-12), not the language's.

### RX-203 — a detail whose domain is a codepoint says the pattern ended with `NOT_A_CODEPOINT`, U+110000, which no codepoint is — so a NUL in a group name reads right

**2026-10-01, cycle 0.1.4 (the plan's PD-47), at compiler `5fbaf4a`** — `SYNTAX.md` Y-29 and §9; the cycle 0.1.1 record's
finding, carried since by every stream-1 dispatch. `BadGroupName`'s detail is the codepoint where a name goes wrong,
and was 0 where the pattern ended inside the name — and 0 is U+0000's value too. Measured at `5fbaf4a`: `(?<a` NUL
`>x)` is `BadGroupName` at byte 4, one byte, detail 0, and `(?<a` at the end is `BadGroupName` at byte 3, one byte,
detail 0; the text reads only the detail, so the NUL read *"the name has no closing `>`"*, at the right byte with the
wrong reason.

**The decision.** `pattern_error.npk` declares `NOT_A_CODEPOINT`, U+110000, one past the last codepoint, and a detail
whose domain is a codepoint uses it to say what no codepoint can: that the pattern ended where one was due. An
unfinished name is `BadGroupName` with it, and a NUL in a name keeps 0 and reads *"a name is ASCII letters, digits
and `_`, and does not begin with a digit"* (`tests/unit/pattern_error_text.npk` case 39). The kinds this cycle's
escapes produce take it too. `UnknownUnicodeProperty`'s details are reasons, not codepoints, and do not move: 1, 2
and 3 cycle 0.1.3's, 0 left for cycle 0.3's unknown name.

*Alternatives declined:* **`0xFFFFFFFF`, the largest detail** — outside the domain as well, but U+110000 is the
nearest value no codepoint takes, and the one a value past U+10FFFF needs, so one constant serves both;
**the length to tell them apart** — measured, both are one byte; **a kind of its own for an unfinished name** — a
kind per sentinel, where one constant serves every kind with a codepoint for a detail; **a NUL refused before the
name is read** — the name's rule refuses it already, and what was wrong was the field.

### RX-204 — every escape of §1 is read — a codepoint, a class, an anchor, or a refusal saying what to write — in a class and out
> **SUPERSEDED IN PART by RX-210 (2026-10-02)** — for `\g` and `\K` alone: *"a test for each letter no rule assigns:
> `c g h …` and `C F H I J K …`"*. Outside a class `\g` is Perl's and PCRE's backreference and PCRE's call of a
> group, refused by those kinds, and `\K`, Perl's and PCRE's reset of a match's start, is refused as lookaround —
> the author's amendment of 2026-10-02 (`SYNTAX.md` Y-44). Every other letter is as this decision says.

**2026-10-01, cycle 0.1.4 (the plan's PD-48), at compiler `5fbaf4a`** — `SYNTAX.md` Y-40, with Y-2, Y-27, Y-28 and Y-36;
per `meta/research/escape-flag-syntax-reference-engines.md`, as of 2026-10-01. It completes RX-186 for escapes, whose
provisional `UnknownEscape` it replaces — all but §8's, which cycle 0.1.5 refuses by their own kinds.

**What chose the rules.** §1 lists what an escape may be. It does not say what ends one, what an escape the pattern
ends inside is, or what a `\` before a space or a codepoint past ASCII means. Measured in Rust's `regex` 1.13.1, Perl
5.38.2, Python 3.12.3, Java 21.0.12.1, node 24.21.0 and PCRE2 10.42 (through GNU `grep -P`): where Rust and the
backtracking engines agree, this library reads the shape so — `\x41` and `\x{1F600}`, `\u0041`, `\U0001F600`, the
control escapes, `\ ` a space. Where they disagree it refuses, saying what to write: `\0` before a digit, an octal
escape in Perl, PCRE, Python and Java, refused by Rust, and U+0000 and the digit if §1 were read as written; `\x4`,
U+0004 in Perl and PCRE, refused by Rust, Python and Java; `[\b]`, a backspace in Perl, Python, PCRE and node,
refused by Rust and Java; `\uD83D\uDE00`, one codepoint in Java and node, two lone surrogates in Python, refused by
Rust; `\é`, `é` in Perl and Python, refused by Rust. `\e` and `\0`, which Rust refuses, are §1's, and read as Perl,
PCRE and Python read them; `\u{41}`, Rust's and node's second spelling of `\x{41}`, is refused naming the first.

**The decision.** Y-40, rule by rule. An escape naming a codepoint is a `Literal` spanning the escape, and in a class
a member, which a `-` may make either end of a range; `\A`, `\z`, `\b` and `\B` are anchors outside a class, and in
one `UnknownEscape`, a position a class cannot hold. A `\` before any other letter or digit, or a codepoint past
ASCII, is `UnknownEscape` — no longer provisional but Y-2's refusal, with a test for each letter no rule assigns:
`c g h i j l m o q y` and `C F H I J K L M N O R T V X Y`. A `\` before ASCII that is neither a letter nor a digit is
that byte: Y-2 said punctuation, and every engine measured reads a space, a control and DEL so — Rust's own
documentation writes a space under `x` as `\ `. The refusals carry the codepoint found, or `NOT_A_CODEPOINT` where
the pattern ended (RX-203); a value stops growing past U+10FFFF, so `\x{FFFFFFFFFFFFFFFFFFFF}` overflows nothing.

**The text.** Each says what is wrong, at which byte, and what to write instead, held to the letter by
`tests/unit/pattern_error_text.npk` cases 41–52: an unknown letter says to write the letter, or `\\` for a backslash;
`\0` before a digit names the hex form, `\x0A` for `\012`; `[\b]` says a class holds codepoints and names `\x08`; a
bad hex or Unicode escape names the byte found and the forms each escape takes; a surrogate names what the pair
stands for, `\x{1F600}` for `\uD83D\uDE00`. A codepoint a sentence names is printable ASCII between backticks, or
`U+` and its hex digits, so no sentence carries a byte a reader cannot see.

**Measured at `5fbaf4a`.** `tests/unit/parse_escapes.npk` and `parse_escape_refusals.npk` pass at −O0 and through
`opt -O2`, and against the parser before this decision each exits 1; each rule broken in a copy exits as the plan's
§1.10 records — at its case, or, with the stop past U+10FFFF removed, by the `IntOverflow` trap twenty hex digits make.

*Alternatives declined:* **`\0` and a digit read as octal** — a second way to write a codepoint, which Rust refuses;
**`\0` and a digit read as U+0000 and the digit, §1 as written** — `\012` would match U+0000, `1`, `2` where five
engines match a line feed, silently; **`\0` refused altogether, as Rust refuses it** — §1 names it, and Perl, PCRE,
Python and node read it as U+0000; **`\u{…}` and `\U{…}` accepted** — two spellings for `\x{…}`, Y-7's reasoning, so
refused naming the one; **`[\b]` as a backspace** — one spelling meaning two things by where it stands, and Rust and
Java refuse it; **a `\` before a space or a control refused, Y-2 as written** — every engine measured reads the byte,
and it is how a space is written under `x`; **`\x` and one hex digit** — Rust, Python and Java refuse it; **a UTF-16
pair of `\u` escapes joined, as Java and node join it** — Rust refuses each half, and Python reads two lone surrogates.

### RX-205 — `\<` and `\>` are refused: Rust's `regex` and GNU `grep` read word assertions, Perl, PCRE, Python and Java the bytes

**2026-10-01, cycle 0.1.4 (the plan's PD-49), at compiler `5fbaf4a`** — `SYNTAX.md` Y-2's and Y-40's notes; per
`meta/research/escape-flag-syntax-reference-engines.md`, as of 2026-10-01. It supersedes in part RX-183 — *"`\`
before ASCII punctuation is that punctuation"* — for `<` and `>`. Since cycle 0.1.1 `\<` has been `<` here. Rust's
`regex`, this library's closest neighbour, reads `\<` and `\>` as the start and the end of a word — its 1.13.1
documentation: *"`\b{start}, \<` start-of-word boundary assertion"* — and regex-syntax 0.8.11 keeps both out of what a `\`
may escape, *"since the escape sequence is significant"*; GNU `grep` 3.11 reads them as word
boundaries too. Perl, PCRE2, Python and Java read the bytes, and node refuses both under `u`. Measured on `a <b>`:
Rust's `\<` matches the empty positions 0 and 3, and Perl's, Python's and Java's the `<` at 2 — as this parser did. A
pattern written for Rust or `grep` compiled here and matched something else, with no word said.

**The decision.** A `\` before `<` or `>` is `UnknownEscape` at the `\`, spanning both bytes, its detail the byte —
in a class and out, as Rust refuses `[\<]` too. The sentence names both readings and what to write: *"`\<` is a
start-of-word assertion in Rust's `regex` and GNU grep, and a `<` in Perl, PCRE, Python and Java, so nregex reads it
neither way. Write `\b` for a word boundary, or `<` to match a `<`."* (`tests/unit/pattern_error_text.npk` cases 53,
54). Every other punctuation is itself, as RX-183 says.

*Alternatives declined:* **the bytes, RX-183 as written** — a pattern from Rust or `grep` would match `<` where it
asked for a word's start, silently; **the assertions, as Rust reads them** — two more boundary kinds and their engine
work in every later cycle for a spelling the families read two ways, where `\b` exists; refusing keeps the choice open,
which is why regex-syntax refused `\<` before it read it (its comment: *"we can turn them into something else in the
future without it being a backwards incompatible change"*); **refused outside a class and the bytes inside** — one
spelling with two answers by where it stands, and Rust refuses it in a class as well.

### RX-206 — flags: `(?flags)` and `(?flags:…)` read as Y-41 says, scoped to the enclosing group across `|`, and a flag named twice is `DuplicateFlag`

**2026-10-01, cycle 0.1.4 (the plan's PD-50), at compiler `5fbaf4a`** — `SYNTAX.md` Y-41, with Y-12, Y-26, Y-27, Y-29,
Y-31, Y-33 and §9; per `meta/research/escape-flag-syntax-reference-engines.md`, as of 2026-10-01. It completes RX-186
for flags, whose provisional `UnknownFlag` it replaces, and adds a kind to §9.

**What chose the rules.** §1's `Flags` and Y-12 say what a flag group is and how far it reaches — not what a flag
named twice, an empty head or a `-` with nothing after it is, nor what the tree records. Measured in Rust's `regex`
1.13.1: `(?ii)`, `(?i-i)` and `(?xx)` are *"duplicate flag"*; `(?-)` and `(?i-)` *"dangling flag negation operator"*;
`(?--i)` and `(?i-m-s)` *"flag negation operator repeated"*; `(?)` and `(?i)*` are refused, nothing to repeat; and
`a(?i)b|c` matches `C` — a flag holds across `|` to the group's end, as Perl and PCRE2 read it too — while
`(a(?i)b)c` does not match `aBC`. Rust's `U`, which swaps greed, and `R`, CRLF mode, are flags nregex does not have.

**The decision.** Y-41. The parse keeps the flags in force in each frame: a scoped head starts the group's frame with
them changed, and a `Flags` node changes the current frame's from there on, so a `|` keeps them and the `)` restores
the parent's. Each node carries the flags in force where it is built, and a `Group` its parent's — the flags at its
`(` — where until now it took the frame being closed, which no flag had changed. A `Flags` node is linked into its
alternative at once, never pending. The refusals: `UnknownFlag` for a byte that is no flag where one may be, its
detail that codepoint — so a `)` or `:` where a flag is due, and a second `-`, each read a sentence of their own;
`DuplicateFlag`, a new kind after `UnknownFlag` — thirty-seven kinds — for a flag named twice in one head, set or
cleared, at the second; and `UnclosedGroup` for a pattern that ends inside the flags. `(?Px)` stays `UnknownFlag` at
the `P` (`tests/unit/parse_refusals.npk` case 64).

**The text.** `tests/unit/pattern_error_text.npk` cases 55–59: an unknown flag names the five; a missing one says
where a flag is due; a second `-` gives `(?i-ms)` for `(?i-m-s)`; a flag named twice says to name each once, and for
`x` says what `(?xx)` does in Perl and PCRE2 and what to write here — `(?x)`, and `\x20` or `\#` in a class (RX-201).

**Measured at `5fbaf4a`.** `tests/unit/parse_flags.npk` and `parse_flag_refusals.npk` pass at −O0 and through
`opt -O2`, and against the parser before this decision exit 1 and 2; each rule broken in a copy exits as the plan's
§1.10 records.

*Alternatives declined:* **flags reset at `|`** — Python's reading, where an inline flag is global and must lead the
pattern; Rust and PCRE carry it to the group's end, as Y-12 says; **`(?)` accepted as an empty flag group** — Rust
refuses it, and it changes nothing; **a flag named twice as `UnknownFlag`, its letter the detail** — one kind fewer,
but a kind that calls a known flag unknown, where `DuplicateGroupName` beside `BadGroupName` is the precedent; **`(?i`
at the end as `UnknownFlag`, as Rust's "expected flag"** — `(?` at the end is `UnclosedGroup` already (Y-29), and so
is this; **the `Flags` node pending, like an atom** — a quantifier would repeat a change of flags; **a `Group` with the
flags of the frame it closes** — those say what its last alternative ended with, where its `(`'s say what was in force
around it.

### RX-207 — `x`: white space and comments are skipped between constructs and nowhere else, and what the engines read two ways is `ExtendedAmbiguity` — in a class, and past ASCII

**2026-10-01, cycle 0.1.4 (the plan's PD-51), at compiler `5fbaf4a`** — `SYNTAX.md` Y-42 and Y-39, with §4's table and §9;
per `meta/research/escape-flag-syntax-reference-engines.md`, as of 2026-10-01, and the UCD's `PropList.txt`, whose
White_Space and Pattern_White_Space are the same in 16.0.0, 17.0.0 and 18.0.0. It makes RX-201's refusal, and adds
the kind RX-201 said this cycle would.

**What chose the rules.** §4 says `x` ignores white space and `#` to the end of the line — not where, nor which white
space. Measured in Rust's `regex` 1.13.1, Perl 5.38.2, Python 3.12.3 and Java 21.0.12.1 (the plan's §1.6): between
constructs all four skip the six ASCII white-space bytes and a `#` comment, and agree — `(?x)a b`, `a *`, `a | b`, a
comment between an atom and its quantifier. Inside a construct they part: Rust skips white space inside `\x4 1`,
`\x{ 41}`, `a{2, 3}` and `( ?:a)`, and between `a*` and its lazy `?`; Perl reads `\x4 1` as U+0004 and `1` and refuses
`( ?:a)`; Python refuses `a* ?` and `( ?:a)` and reads `a{2, 3}` as text; Java reads `( ?:a)` as Rust does and refuses
`a{ 2}`. Past ASCII they part again: Rust skips U+00A0, U+3000, U+2028 and U+0085 and not U+200E; Perl skips U+2028,
U+0085 and U+200E and not U+00A0 or U+3000; Python and Java skip none.

**The decision.** Y-42. Under `x` the walk skips the six ASCII white-space bytes, and a `#` through the next line
feed, where a construct may begin — the reading all four share — and nowhere else: inside a construct white space is
that construct's byte, read as without `x`, which refuses each shape the engines read two ways. A codepoint past ASCII
in White_Space or Pattern_White_Space is `ExtendedAmbiguity` under `x`, in a class or out; inside a class every
white-space byte and `#` is too (RX-201), a range's end included. `ExtendedAmbiguity` is a new kind after
`WrongNamedGroupSpelling` — thirty-eight kinds — at the codepoint, spanning it, its detail the codepoint: 9 … 13 or 32
for ASCII white space, 35 for `#`. The twenty-one codepoints past ASCII are named in `parse.npk` from `PropList.txt`,
not taken from one of cycle 0.3's generated tables, since the parser reads no table (Y-37); Pattern_White_Space is
closed by Unicode's stability policy, and cycle 0.3, which generates White_Space, can hold the list to it.

**The text.** `tests/unit/pattern_error_text.npk` cases 60–63: white space in a class names what Rust and Java do with
it, what Perl, Python and .NET do, and the escape to write — `\x20`, `\t`, `\n`, `\v`, `\f` or `\r`; a `#` in a
class names `\#`; white space past ASCII names the codepoint, what each engine skips, and `\x{A0}`.

**Measured at `5fbaf4a`.** `tests/unit/parse_flags.npk` cases 30–47 and `parse_flag_refusals.npk` cases 60–85 pass at
−O0 and through `opt -O2`, and against the parser before this decision exit 30 and 60; each rule broken in a copy
exits as the plan's §1.10 records.

*Alternatives declined:* **Rust's reading, white space skipped inside constructs too** — Perl, Python and Java each
read some of those shapes otherwise, so a pattern would change meaning between them with no word said; **white space
past ASCII read as itself** — Python's and Java's reading, and a silent difference from Rust for U+00A0 and from Perl
for U+2028; **skipped, as Rust skips it** — a silent difference from Perl, Python and Java; **a kind for each case —
white space in a class, `#` in a class, white space past ASCII** — three kinds for one ambiguity, which the detail
tells apart; **`UnknownFlag` or `ByteModeNonAscii` reused** — kinds named for something else.

### RX-208 — `(?-u)`: every literal a byte, `\xHH` any byte, and a codepoint past ASCII written any other way refused, naming its UTF-8 bytes

**2026-10-01, cycle 0.1.4 (the plan's PD-52), at compiler `5fbaf4a`** — `SYNTAX.md` Y-43, with Y-13, Y-14 and Y-26; per
`meta/research/escape-flag-syntax-reference-engines.md`, as of 2026-10-01. Y-14 refuses a non-ASCII literal under
`(?-u)` and asks the refusal to name the codepoint; it does not say what an escape names there. Measured in Rust's
`regex` 1.13.1 (regex-syntax 0.8.11, with `utf8` off, as for a search over bytes): `(?-u)é` and `(?-u)\x{E9}` are é's
two UTF-8 bytes, C3 A9, and `(?-u)\xE9` the one byte E9 — two escapes of one value naming different bytes; `(?-u)[é]`
and `(?-u)\pL` are refused, *"Unicode not allowed here"*.

**The decision.** Y-43. Under `(?-u)` a literal is one byte, and every `Literal` carries `AST_FLAG_BYTE` — Y-26 named
the bit for "a `Literal` that is a byte under `(?-u)`", and each is. `\x` and two hex digits name a byte whatever its
value; any other way to write a codepoint past ASCII — as itself, `\x{…}`, `\u…`, `\U…` — is `ByteModeNonAscii`, in a
class or out, as a member or a range's end, so the two readings of Rust's that disagree are each a refusal here. `\p`
and `\P` are refused at the `\`, their detail the letter, which no codepoint past ASCII is, so one kind carries both
cases. The sentence names the codepoint, as Y-14 asks, and its UTF-8 bytes as escapes, and the one byte when the
codepoint is below U+0100: *"non-ASCII literal at byte 5 under `(?-u)`: U+00E9 takes 2 bytes in UTF-8, and in byte
mode a literal is one byte. Write its UTF-8 bytes as `\xC3\xA9`, the byte E9 as `\xE9`, or turn `u` back on around
it, as in `(?u:...)`."*

**Measured at `5fbaf4a`.** `tests/unit/parse_flags.npk` cases 50–61, `parse_escape_refusals.npk` cases 78–90 and
`pattern_error_text.npk` cases 64–66 pass at −O0 and through `opt -O2`, and against the parser before this decision
the first two exit 50 and 78; each rule broken in a copy exits as the plan's §1.10 records.

*Alternatives declined:* **`\x{E9}` as the byte E9, one rule for every hex escape** — Rust reads it as two bytes, so a
pattern would change meaning between the two, silently; **a codepoint past ASCII as its UTF-8 bytes, as Rust reads
`é`** — Y-14 calls that silent nonsense in a class, and a literal and a class member would differ; **`\p` under
`(?-u)` left to cycle 0.3, which resolves properties** — the parser knows the flags, no reading of a property is a
byte class, and Rust refuses it when it parses; **`AST_FLAG_BYTE` on a byte past ASCII only** — every literal under
`(?-u)` is a byte, and a bit on some would leave a reader asking the flags for the rest.

## The refusals — cycle 0.1.5

### RX-209 — the escapes §8 declines are refused by their own kinds, and the cycle's "rejection test per refusal" is a unit holding each one's four fields

**2026-10-02, cycle 0.1.5 (the plan's PD-53), at compiler `5fbaf4a`** — `SYNTAX.md` Y-44, with Y-23, Y-30, Y-31 and Y-40;
per `meta/research/refusal-syntax-reference-engines.md`, as of 2026-10-01. It completes RX-186 for escapes: RX-204 left
§8's escapes `UnknownEscape`, the last refusal anything here made provisionally.

**What chose the rules.** Measured in Rust's `regex` 1.13.1, Perl 5.38.2, Python 3.12.3, Java 21.0.12.1, node 24.21.0
and PCRE2 10.42: outside a class every engine that reads `\1` … `\9` reads a backreference, and Rust refuses each,
*"backreferences are not supported"*; `\k<n>`, `\k'n'` and `\k{n}` are named backreferences in Perl and PCRE, and Java
and node read `\k<n>`; `\G` and `\Z` are anchors in Perl, PCRE and Java; `\Q…\E` quotes in Perl, PCRE and Java, and a
lone `\E` is ignored by Perl and PCRE and refused by Java. Rust refuses every one; Python reads `\1` … `\9` and
`\Z`, and node under `u` `\1` … `\9` and `\k<n>`, and each refuses the rest. Inside a class no engine reads a
group or a position: `[\1]` … `[\7]` are octal in Perl, PCRE and Python, `[\8]` the digit in Perl and PCRE, and
`[\k]`, `[\G]` and `[\Z]` the letter in Perl, refused by PCRE, Python, Java and Rust; and `\Q…\E` quotes in a
class too.

**The decision.** Y-44. Outside a class `\1` … `\9` and `\k` are `BackreferenceUnsupported`, `\G` and `\Z`
`UnsupportedAnchor`, and `\Q` and `\E` `UnsupportedQuoting`, each at the `\`, spanning it and the byte after it, its
detail that byte, whatever follows. Inside a class `\Q` and `\E` are `UnsupportedQuoting` as outside, and a digit,
`\k`, `\G` and `\Z` stay `UnknownEscape` — Y-40's refusal, final now. No construct is refused provisionally any more
(Y-31).

**A rejection test per refusal.** The cycle README asks for *"a rejection test per refusal in `tests/rejection/`, with
the exact-code rule"*, a line written with the cycle plan, before that directory held anything. `tests/rejection/` is
the `check` stage: each file must be refused by the COMPILER with exactly the codes it names (`BUILD.md` B-6, B-7). A
refused pattern is a value `parse_pattern` answers at run time — no pattern is compiled when the program is (O-G1) —
so a fixture there compiles, measured at `5fbaf4a`, and the stage fails it. The rule's terms for a value are its four
fields: `tests/unit/parse_declined.npk` holds one case per spelling, each requiring exactly the kind, the offset, the
length and the detail, so a construct refused for the wrong reason is red, as B-7's code-set equality makes a fixture
refused for the wrong code red. Every construct of §8's table has such a case: the escapes there, the group heads and
the possessive quantifier in `parse_refusals.npk` cases 21–23 and 51–63, since cycle 0.1.1.

**Measured at `5fbaf4a`.** `parse_declined.npk` passes at −O0 and through `opt -O2`, and against the parser before this
decision exits 1 (`\1` was `UnknownEscape`); each rule broken in a copy exits as the plan's §1.12 records.

*Alternatives declined:* **`\12` read as group 12, spanning its digits** — Python reads group 12, Java group 1 and a
`2`, Perl and PCRE octal or a group by how many groups precede it, so the refusal at its first digit is right whichever
was meant; **a digit in a class refused as a backreference, as Rust refuses it** — no engine reads a group there and
four read octal; **`\G` and `\Z` in a class refused as anchors** — a class holds no position, as RX-204 made `\A` and
`\z` there `UnknownEscape`; **a lone `\E` as `UnknownEscape`** — its one reading anywhere is the end of a quotation;
**the tests in `tests/rejection/`** — a pattern's refusal is not the compiler's, and a fixture there would be red;
**§8's group heads repeated in the new unit** — two homes for one assertion drift, and `parse_refusals.npk` has held
them since 0.1.1.

### RX-210 — `\g` is refused as what it is where it means anything: a backreference, and before `<` or `'` a call of a group — and `\K`, by the author's amendment, as lookaround
> **SUPERSEDED IN PART by RX-217 (2026-10-08)** — the attribution of `\K`'s in-class half, which its paragraph *"The
> author's amendment, 2026-10-02"* holds as his: that `[\K]` stays `UnknownEscape` was cycle 0.1.5's worker's reading of
> RX-209, which the author accepted on 2026-10-02 as the workbench's question 23. What `\K` and `\g` are, in a class and
> out, is as this decision says.

**2026-10-02, cycle 0.1.5 (the plan's PD-54), at compiler `5fbaf4a`** — `SYNTAX.md` Y-44; per
`meta/research/refusal-syntax-reference-engines.md`, as of 2026-10-01, and for `\K` its addendum of 2026-10-02.
RX-204 refused `\g` as a letter no rule names, `UnknownEscape`, whose sentence tells the author to write `g`.
Measured: Perl 5.38.2 and PCRE2 10.42 read `\g1`,
`\g{1}`, `\g{-1}` and `\g{name}` as backreferences, and PCRE2 reads `\g<1>` and `\g'1'` as a call of group 1, which
Perl refuses; Python, Java, Rust and node under `u` refuse every `\g`. So wherever `\g` means anything it is one of
§8's constructs, and its author wanted a backreference or a call — never a `g`.

**The decision.** Outside a class `\g` is `BackreferenceUnsupported` at the `\`, spanning it and the `g`, its detail
`g` (103) — but before `<` or `'` it is `RecursionUnsupported`, spanning the three bytes, its detail the third, as
Y-30's `(?P>` and `(?1)` are. In a class `\g` stays `UnknownEscape`: Perl and PCRE read `[\g]` as `g`, and no engine
reads a group there. `tests/unit/parse_declined.npk` cases 50–57; `parse_escape_refusals.npk`'s case 33, which held
`\g` as an unknown letter, is retired.

**The author's amendment, 2026-10-02 — `\K`.** The plan kept Perl's `\K` a letter no rule names, `UnknownEscape`,
whose sentence says *"Write `K` to match it"*, since it is no construct §8 names, and asked the author whether it
should be refused as lookaround instead (its §6). He answered on 2026-10-02 that it should, with the lookaround's
sentence. Measured on 2026-10-02 (the digest's addendum): Perl 5.38.2 and PCRE2 10.42 read `\K` as a reset of the
match's start — `foo\Kbar` matches `bar` in `foobar`, what matched before the `\K` kept out of the match, as a
lookbehind would keep it — and Python 3.12.3, Java 21.0.12.1 and node 24.21.0 under `u` refuse it, where node without
`u` reads a `K`. So outside a class `\K` is `LookaroundUnsupported` at the `\`, spanning it and the `K`, its detail
`K` (75), and its text is the lookaround's. In a class it stays `UnknownEscape`, as `\G` and `\Z` do: Perl
reads `[\K]` as `K`, with a warning, PCRE2, Python, Java and node under `u` refuse it, and no engine reads a
position there. `tests/unit/parse_declined.npk` cases 60–63; `parse_escape_refusals.npk`'s case 47, which held `\K`
as an unknown letter, is retired.

**Measured at `5fbaf4a`.** `parse_declined.npk` passes at −O0 and through `opt -O2`, and against the parser before this
decision exits 50; with `\g` dropped from the backreference's letters it exits 50, and with the call read as a
backreference 55; with `\K` left a letter no rule names it exits 60, and with `\K` read as lookaround in a class
too 63.

*Alternatives declined:* **`\g` left `UnknownEscape`** — its sentence tells a Perl author to write `g`; **every `\g` a
backreference** — PCRE's `\g<1>` runs group 1's pattern again, not its text, and the backreference's sentence would
say the wrong thing; **`\K` left `UnknownEscape`, as the plan proposed** — its sentence tells a Perl or PCRE author
to write `K`, and the author amended the plan on 2026-10-02; **`\K` refused as lookaround in a class too** — a
class holds codepoints, and no engine reads a position there.

### RX-211 — `regex_escape(text)` puts a `\` before every byte that means something in a pattern and writes white space past ASCII as `\x{…}`, so the text means itself whole, in a piece, in a class and under `x`
> **SUPERSEDED IN PART by RX-214 (2026-10-08)** — the set of bytes it escapes: `:` joins them, since straight after a
> nested class's `[` a text that began `:alpha:` was read as the POSIX class, with no error; and the claim *"between `[`
> and `]`"*, which held for none of those texts. Every other byte, and every other form, is as this decision says.
> *(Noted 2026-10-08, cycle 0.1.6a — the cycle audit's S4: its *"as it does `pattern_error_text`"* reads as the present;
> `src/lib.npk` re-exports `ERegexPattern` alone today, and both at cycle 0.10.5 (`API.md` §1, RX-187).)*

**2026-10-02, cycle 0.1.5 (the plan's PD-55), at compiler `5fbaf4a`** — `SYNTAX.md` Y-24 and Y-45, `API.md` §1; per
`meta/research/refusal-syntax-reference-engines.md`, as of 2026-10-01. Y-24 names `regex_escape` the way to match a
literal string, §8's refusal of `\Q…\E` points at it, and `API.md` §1 gives it as `regex_escape(string) -> string`;
nothing said what it writes. Rust's `regex::escape` (regex-syntax 0.8.11's `escape_into` and `is_meta_character`)
writes a `\` before eighteen bytes — `\ . + * ? ( ) | [ ] { } ^ $ # & - ~` — so its text is a literal in a pattern and
in a class; it leaves white space bare, and regex-syntax reads `(?x)a b` as `ab`, so under `x` its text loses its
spaces. nregex's `x` skips the same white space between constructs (Y-42), refuses white space past ASCII (Y-42), and
refuses white space or `#` in a class (Y-39).

**The decision.** Y-45: a `\` before Rust's eighteen and before the six white-space bytes; each of Y-42's twenty-one
white-space codepoints past ASCII as `\x{…}`; every other byte copied, `<` and `>` too (RX-205 refuses a `\` before
either). Each codepoint of the text then parses back as itself — whole, in a piece of a pattern, between `[` and `]`,
under `x` or not. A text that is not well-formed UTF-8 is copied with only its ASCII escaped, and its pattern is
refused where the text breaks. It is written in `parse.npk`, beside the parser whose reading it inverts, so the
twenty-one codepoints have one home, and re-exported by `syntax.npk`; `pattern_error.npk`'s `hex` is `pub` for it, so a
codepoint is written in one way. `src/lib.npk` re-exports it at cycle 0.10.5, as it does `pattern_error_text`.

**Measured at `5fbaf4a`.** `tests/unit/regex_escape.npk` passes at −O0 and through `opt -O2`: every ASCII byte alone in
all four places, the pairs a class reads as a range, an end or an operator, all twenty-one codepoints under `x`, a text
an overlong form makes ill-formed, and the text written for each kind of byte. Against the tree before this decision it
is refused `NITPICK-RESOLVE-002` at its four calls; each byte dropped from the set, each form changed, exits as the
plan's §1.12 records.

*Alternatives declined:* **Rust's eighteen alone** — under `x` the text's white space is skipped; **Y-28's twelve
metacharacters alone** — between `[` and `]` a `-`, `]`, `&` or `~` becomes a range, an end or an operator; **every
ASCII byte that is neither a letter nor a digit** — a `\` before `<` or `>` is refused; **every byte past ASCII as
`\x{…}`** — the text unreadable for nothing, since only the twenty-one mean anything; **an ill-formed text decoded as it
is** — an overlong form would be read as a codepoint the text does not hold, `E0 82 85` as U+0085; **a `Bytes` sink
rather than a `string`** — `API.md` §1 gives a `string`, and A-12's sink is for replacement, which runs per match.

### RX-212 — a refusal of what §8 declines says what it is, where, the guarantee or the reading it would take, and what to write, and never that it is unsupported

**2026-10-02, cycle 0.1.5 (the plan's PD-56), at compiler `5fbaf4a`** — `SYNTAX.md` Y-34, with Y-18 and Y-37, `COMPAT.md`
K-1 and `UNICODE.md` U-8; per `meta/research/refusal-syntax-reference-engines.md` and
`meta/research/lookaround-linear-time.md`, as of 2026-10-01. The cycle README asks that each message name the guarantee
or the alternative, *"never 'unsupported'"*, and holds four to the letter: the backreference says the pattern could not
be matched in linear time, the quotation names `regex_escape()`, `\Z` names `\n?\z`, and `\p{InGreek}` names
`\p{Script=Greek}`. Cycle 0.1.1's sentences said *"is not supported:"* before the reason, one began *"unsupported
anchor"*, and the backreference's said *"matching one is NP-hard in general"*. The lookaround's said it *"cannot be
matched in linear time"*, and two peer-reviewed algorithms match lookahead and lookbehind in O(m·n) — Mamouras and
Chattopadhyay, POPL 2024; Barrière and Pit-Claudel, PLDI 2024 — so that reason is false as stated, though RE2, Rust's
`regex` and nregex read no lookaround.

**The decision.** Each sentence of §8's kinds says what the construct is and its byte, why nregex refuses it — the
guarantee it would break, or how the engines read it — and what to write instead; none says it is unsupported, and the
text's unit holds that over every kind. A backreference *"matches the text a group captured, which no automaton can,
so the pattern could not be matched in linear time, as every nregex search is"*; lookaround: *"nregex's automata read
no lookahead or lookbehind, and they are what make every search take linear time"* — and `\K`, refused as lookaround
by the author's amendment of 2026-10-02 (RX-210), reads the same sentence, held with its kind and its byte by the
text's unit, case 82; a possessive `+` and an atomic group
each *"stops backtracking"*, and the fix says it may match more; recursion and `\g<…>` let a pattern match nested text; `(?R)`
names Rust's CRLF mode beside PCRE's recursion — 0.1.4's hand-on — and says to write `\r?$` under `m`; `\Z` names the
three readings and both `\z` and `\n?\z`; `\G` names `regex_find_at` and the check on the match's start; `\Q` and a
lone `\E` name `regex_escape()`; the comment group says `#` begins a comment outside a class — 0.1.4's record's
hand-on. And two refusals that are not §8's kinds: `[\1]` … `[\7]`, `UnknownEscape` in a class, says Perl, PCRE and
Python read octal there and names the hex form; and `UnknownUnicodeProperty` gains detail 4, a Unicode block, its
sentence naming `\p{Script=Greek}` for `\p{InGreek}`. The parser cannot raise it: only the tables tell a block from a
script, `\p{Inherited}` being one, so cycle 0.3.1 raises it where it resolves a name, and this cycle holds its sentence
to the letter by building the error. Each new or changed sentence is listed in the plan's §6, for the author.

**Measured at `5fbaf4a`.** `tests/unit/pattern_error_text.npk` passes at −O0 and through `opt -O2`, and against the text
before this decision exits 16, the lookaround's sentence; each branch lost, and the word put back, exits as the plan's
§1.12 records; and with `\K` left a letter no rule names it exits 82.

*Alternatives declined:* **"is not supported" kept beside the reason, K-1 read as "not unsupported alone"** — the
checklist says never; **the NP-hardness of backreferences** — true, Aho's 1990 result as the PLDI 2024 paper cites
it, but not the guarantee an author reads the sentence for, and the checklist asks for linear time; **"cannot be
matched in linear time" kept for lookaround** — false since 2024; **the block refused by the parser at an `In` or `Block=` prefix** — `\p{Inherited}`
and `\p{Inscriptional_Pahlavi}` are scripts, and the parser reads no table; **a kind of its own for a block** — U-7
names `UnknownUnicodeProperty`, and a detail tells the sentence which, as RX-200's does for `UnknownPosixClass`; **the
block's sentence left to cycle 0.3.1 with its trigger** — the checklist holds it here, and the author reads the
sentences together.

### RX-213 — a `{` after `\b` or `\B` that holds no number is `BadRepeatBounds` with detail 2, its sentence naming Rust's `\b{start}` and Perl's `\b{wb}`
> **SUPERSEDED IN PART by RX-215 (2026-10-08)** — *"no digit follows it"*: detail 2 when an ASCII letter follows the `{`,
> since `\b{,3}` and `\b{ 3}` hold a number and the sentence said they held none; and the sentence, which says the brace
> begins with a letter, not a number. Every other part is as this decision says.

**2026-10-02, cycle 0.1.5 (the plan's PD-57), at compiler `5fbaf4a`** — `SYNTAX.md` Y-32; per
`meta/research/refusal-syntax-reference-engines.md`, as of 2026-10-01; cycle 0.1.4's hand-on, *"`\b{start}` Rust's
start-of-word assertion, read as a bad bound"*. Measured: Rust's `regex` 1.13.1 reads `\b{start}`, `\b{end}`,
`\b{start-half}` and `\b{end-half}` as word assertions and refuses any other name in the braces; Perl 5.38.2 reads
`\b{wb}`, `\b{sb}`, `\b{gcb}`, `\b{lb}` and `\B{wb}` as Unicode boundaries and refuses any other, `\b{2}` included;
PCRE2 and Python read `\b` and then the braces as text; Java refuses `\b{start}`. Here `\b` then `{` begins a
repetition (Y-32), so `\b{start}` was `BadRepeatBounds`, detail 0, telling the author to write `\{` for a brace —
PCRE's and Python's reading, and silent about the two engines that read a boundary.

**The decision.** The same kind at the same byte, spanning what was read; when the atom the `{` follows is `\b` or
`\B` and no digit follows it, detail 2, and the sentence names Rust's `\b{start}` and `\b{end}`, Perl's `\b{wb}`, and
what to write: `\b` or `\B` alone, or `\{` for a brace. `\b{2}` stays a repetition of `\b`, legal (Y-22), as in Rust
and Java; a bound that goes wrong later, `\b{2,x}`, keeps detail 0.

**Measured at `5fbaf4a`.** `parse_refusals.npk` cases 72–75 and `pattern_error_text.npk` case 81 pass at −O0 and
through `opt -O2`, and against the parser and text before this decision exit 72 and 81; with the detail dropped the
first exits 72, with `\B` left out 74, and with the sentence's branch lost the second exits 81.

*Alternatives declined:* **`\b{start}` read as Rust's assertion** — a construct nregex's engines do not have yet, and
Perl reads the same braces otherwise; **`UnknownEscape` at the `\`** — the `\b` is a word boundary, and what is wrong
is the brace; **detail 2 after any atom** — `a{start}` is a brace no engine reads as a boundary; **`\b` alone, without
`\B`** — Perl's `\B{wb}` is the same reading of the same shape.

## The cycle audit's findings — cycle 0.1.6a

### RX-214 — `regex_escape` escapes `:` too: a text that began `:alpha:`, put straight after a nested class's `[`, was the POSIX class `[:alpha:]`, with no error

**2026-10-08, cycle 0.1.6a (the plan's PD-58), at compiler `5fbaf4a`** — `SYNTAX.md` Y-45; the cycle audit's C1 and C2
(`meta/audits/nitpick-regex-0.1-2026-10-02.md`), and the first of cycle 0.1.5's verifier's three findings. RX-211 put a
`\` before Rust's eighteen bytes and the six white-space bytes and left `:` bare, as Rust's `regex::escape` does. But
straight after a `[` that opens a class, `[:` begins a POSIX class (Y-38): `[a[` and `regex_escape(":alpha:")` and `]]`
make `[a[:alpha:]]`, which parses — `a` or a letter — and `[\w--[` and `regex_escape(":digit:")` and `]]` make `\w`
less the digits, not less `:`, `d`, `i`, `g` and `t`. A wrong answer with no error, for the fourteen texts `:name:`, in
a nested class only; their `:^name:` twins, whose `^` it escapes, were refused there, `UnknownPosixClass`. After the
outermost `[` the fourteen, and every text that begins and ends with `:`, holds a codepoint not `:` and is written with no `\`, were refused
(RX-200): loud, and Y-45's *"between `[` and `]` one member each"* false for them. Measured on 2026-10-08, regex-syntax 0.8.11's `is_meta_character` holds no `:`, and it reads
`[[:alpha:]]` and `[a[:alpha:]]` as the POSIX class, so Rust's escaped text is misread there too
(`meta/research/refusal-syntax-reference-engines.md`, its addendum of 2026-10-08).

**The decision.** `:` joins the bytes `regex_escape` writes a `\` before. `\:` is `:` in a class and out (Y-2), so a
text's first byte is never a `[:`'s `:`, and every text parses back to one `Literal` per codepoint as a whole pattern,
as a piece of one and between `[` and `]`, nested or not — but where Y-45's note says it cannot promise that, after a
`\0`, past the length bound and for the empty text, each a refusal. `tests/unit/regex_escape.npk` holds §5.1's fourteen
names, as `:name:` and `:^name:`, in a nested class (13) and in the outermost one (14), every ASCII byte alone in a
nested class (15) and `:a:` in the outermost class (16), and case 31's text holds `\:`.

**Measured at `5fbaf4a`.** `regex_escape.npk` passes at −O0 and through `opt -O2`, and against the parser before this
decision exits 13: `[[` and the text `:alpha:` and `]]` parsed, to a class holding the POSIX class. With `:` left bare
again it exits 13. Cycle 0.1.5's mutant `esc-extra`, which escaped `:` and was required to fail at case 31, is this
decision.

*Alternatives declined:* **Y-45's claim narrowed to the places measured** — a silent misreading left standing behind a
caveat, as the audit put it; **every ASCII byte that is neither a letter nor a digit escaped** — RX-211's own
alternative, declined for `<` and `>`, which a `\` makes refused (RX-205); **`[:` read as a nested class after a nested
`[`, as Rust reads `[[:alpah:]]`** — a change to Y-38 for every pattern, when only the escaped text went wrong;
**`regex_escape` refusing a text that begins with `:`** — it never fails (`API.md` §1), and the text is not wrong.

### RX-215 — a `{` after `\b` or `\B` gives detail 2 only when an ASCII letter follows it, and the sentence says the brace begins with a letter, not a number

**2026-10-08, cycle 0.1.6a (the plan's PD-59), at compiler `5fbaf4a`** — `SYNTAX.md` Y-32 and §9; the cycle audit's C3.
RX-213 gave detail 2 when *"no digit follows"* the `{`, where its title and Y-32's note said the brace *"holds no
number"*: so `\b{,3}`, `\b{ 3}` and `\B{,2}` were each `BadRepeatBounds` with detail 2, and the sentence said *"and this
one holds no number"* of a brace holding `3` — the right byte with the wrong reason, the shape RX-203 corrected for a NUL
in a group name. Measured on 2026-10-08 (`meta/research/refusal-syntax-reference-engines.md`, its addendum):
regex-syntax 0.8.11 reads `\b{` and a letter or `-` as the start of a word boundary's name and anything else as a
repetition — its `maybe_parse_special_word_boundary`: *"if the first non-whitespace character isn't in [-A-Za-z] (i.e.,
this can't be a special word boundary), then we bail and let the counted repetition parser deal with this"* — so
`\b{,3}` is its repetition's error and `\b{x3}` its word boundary's; and Perl 5.38.2 reads every `\b{…}` as a boundary,
refusing `\b{,3}` as *"',3' is an unknown bound type"*. Every name either engine reads begins with a letter.

**The decision.** Detail 2 when the atom before the `{` is `\b` or `\B` and an ASCII letter follows the `{` — one byte
of lookahead, the cursor's own (RX-173). Any other byte there, and the end of the pattern, is detail 0, as after any
atom. The sentence says the brace *"begins with a letter, not a number"*, where it said it *"holds no number"*, so it
is true of `\b{x3}` too. `tests/unit/parse_refusals.npk` cases 76–79 hold `\b{,3}`, `\b{ 3}`, `\B{,2}` and `\b{` at the
end, each detail 0, and `pattern_error_text.npk` case 81 the sentence.

**Measured at `5fbaf4a`.** Both units pass at −O0 and through `opt -O2`, and against the parser and the text before
this decision exit 76 and 81. With the letter test dropped `parse_refusals` exits 76, and with it made after any atom,
25 (`a{x}`).

*Alternatives declined:* **the detail kept and the sentence reworded, "is not followed by a number"** — the audit's other
way, which keeps a detail naming Rust's and Perl's word boundaries for a brace that begins like a bound, and Rust reads
it as one; **a letter or `-`, as Rust tests** — no name either engine reads begins with `-`, and `\b{-1}` reads better as
a bound gone wrong; **every brace a digit does not begin, as Perl reads every `\b{…}` as a boundary** — RX-213's rule,
whose sentence was false for `\b{,3}`.

### RX-216 — `NestTooDeep` says what is open around the `(` or `[` it refuses, not what that `(` would nest

**2026-10-08, cycle 0.1.6a (the plan's PD-60), at compiler `5fbaf4a`** — `SYNTAX.md` Y-34 and Y-35; the cycle audit's K7.
RX-198's sentence says *"the `(` or `[` here would nest groups and classes 251 deep"*. Y-35 decides the bound at the
`(`, before a byte after it is read, so a `(` that begins a flags head or a comment group inside 250 levels — `(?i)`,
`(?#` — is `NestTooDeep` as well, and neither nests anything: for those the sentence is false, measured at `5fbaf4a`.
Deciding after the head would undo what RX-193 chose — one rule, and the parse stopping where the bound is — so the
sentence moves and the rule stays.

**The decision.** The sentence says what is true at the refused byte: *"nesting too deep at byte 250: groups and
classes are open 250 deep around the `(` or `[` here, as deep as they may nest (NREGEX_NEST_DEPTH), so nregex refuses
it before reading what it begins. Nest fewer: write `(?:a)` as `a`, and `[[a]]` as `[a]`."* — its number the bound,
the detail. `tests/unit/pattern_error_text.npk` holds it for 251 groups (23) and 251 classes (35), and with its kind and
its byte for `(?i)` inside 250 groups (83).

**Measured at `5fbaf4a`.** `pattern_error_text.npk` passes at −O0 and through `opt -O2`, and against the text before
this decision exits 23.

*Alternatives declined:* **the bound decided after the head is read, so `(?i)` there parses** — two rules where RX-193
chose one, and `(?i:` opens a group, which the bound must still refuse before its body; **the sentence kept, and a note in
Y-35** — a sentence a user reads, false for an input the rule names; **"would open a group or a class"** — false for
the same two.

### RX-217 — `\K` in a class stays `UnknownEscape`: cycle 0.1.5's worker's reading of RX-209, which the author accepted as the workbench's question 23 — recorded as that, not as his amendment

**2026-10-08, cycle 0.1.6a (the plan's PD-61), at compiler `5fbaf4a`** — `SYNTAX.md` Y-44 and §9, `COMPAT.md` §3; the
cycle audit's C6 and K1, and the second and third of cycle 0.1.5's verifier's findings. The author amended cycle 0.1.5's
plan on 2026-10-02: `\K` refused as lookaround, with the lookaround's sentence (RX-210). What `\K` is inside a class he
did not say. The worker read RX-209's rule — a class holds codepoints, and no engine reads a group or a position in one —
as keeping `[\K]` `UnknownEscape`, as `[\G]` and `[\Z]` are, and its record said so: *"That half is this worker's
reading of RX-209's rule, not the author's words"*. But RX-210's paragraph *"The author's amendment, 2026-10-02"* and
Y-44's note *"the author's amendment of 2026-10-02"* hold that half as his. He accepted the reading at 09:45 on
2026-10-02, the workbench's question 23 — *"im fine with your recomendation for question 23"* — and the workbench's
record asked that this repository record it beside RX-209.

**The decision.** No pattern moves: `[\K]` is `UnknownEscape` at the `\`, spanning two bytes, its detail `K` (75), and
`\K` outside a class `LookaroundUnsupported` (RX-210). The record moves: this decision is the in-class half, the
worker's reading the author accepted as question 23; RX-210 carries its marker, and Y-44's note and
`tests/unit/parse_declined.npk`'s header a dated note each. And every list of what stays `UnknownEscape` in a class
names `\g` and `\K` beside `\k`, `\G` and `\Z` — `SYNTAX.md` §9's row, `COMPAT.md` §3's row, and the comment over
`class_escape`, which each named three.

**Measured at `5fbaf4a`.** `[\K]` is `UnknownEscape` at byte 1, length 2, detail 75, and `[\g]` the same with detail
103 — `tests/unit/parse_declined.npk` cases 63 and 57, unchanged.

*Alternatives declined:* **RX-210's text rewritten** — a settled decision's text is never rewritten, and the marker says
what changed and why; **a dated note at each of the three places and no decision** — the audit's other way, but the
answer is the author's, and a decision is where this repository records one, beside RX-209, as the workbench asked.

### RX-218 — `SAFETY.md` S-2's lookaround row says what is true: automata can match lookaround, and in linear time — the refusal stands on RX-003 and S-6, not on its being "not regular"

**2026-10-08, cycle 0.1.6a (the plan's PD-62), at compiler `5fbaf4a`** — `SAFETY.md` S-2; per
`meta/research/lookaround-linear-time.md`, as of 2026-10-01; the cycle audit's C8; and the author's answer to the
workbench's question 20 (d), 2026-10-02: a dated note on S-2's row, by a decision, at the next subcycle that touches
`SAFETY.md` — this one, since the audit found that place named no cycle. S-2 says lookahead and lookbehind are *"not
regular either"*, that automata express *"some"* of it at exponential cost, and that *"the general case needs
backtracking"*. The digest's primaries say otherwise: finite automata decide matching with lookaround, a deterministic
one doubly exponential in the worst case (Mamouras and Chattopadhyay, citing Morihata 2012), and two peer-reviewed 2024
algorithms match it in O(m·n) without backtracking. RX-212 took the false claim out of the sentence a user reads; the
safety document kept it, and cycle 0.1.5's plan named it for the author.

**The decision.** A dated note under S-2's table, its text kept: what the algorithms ask — Mamouras and Chattopadhyay's
right-to-left passes over the haystack for a lookahead, and Barrière and Pit-Claudel's general one an oracle as long as
the haystack, memory a search may not take (S-6), while a lookbehind alone streams and their captureless lookbehind
needs no extra space, whatever the pattern syntax — and what the refusal stands on: RX-003 keeps the engines automata
that read no lookaround, and S-6 keeps every search from allocating. The note names the class the row's two examples
stand for, `(?!…)`, `(?<!…)` and `\K` with them (`SYNTAX.md` Y-30, Y-44). And O-R1's record takes in that a captureless
lookbehind is known to fit S-6, if a consumer ever asks for one. No refusal and no sentence moves.

*Alternatives declined:* **S-2's row rewritten** — its text was the reason the refusal was first written, and how that
reason was wrong is kept beside what is true; **the note left for a later subcycle that touches `SAFETY.md`** — the audit
found that place named no cycle, and this one touches it; **the refusal of lookbehind reconsidered here** — RX-003 and
S-6 decide it today, and a consumer's need is O-R1's question, not a close's.

## The instruments — cycle 0.1.6b

### RX-219 — the cycle 0.1 Gate amended: every kind is provoked by a test or listed with the cycle that will provoke it, and `check_error_kinds_tested` holds the list both ways

**2026-10-08, cycle 0.1.6b (the plan's PD-63), at compiler `5fbaf4a`** — `SYNTAX.md` Y-25, `TESTING.md` §8 and V-19, and the
cycle README's Gate and `ROADMAP.md`'s; the cycle audit's C4, S1 and K9. The Gate reads *"every kind in `SYNTAX.md` §9
has a test that produces it, and `check_error_kinds_tested` is green"*. Of the thirty-eight kinds, thirty-four have a
producer in `src/` and a unit that provokes them, and four have neither, and no parser can raise them: a product of
repetitions is counted as the HIR is built (cycle 0.2.2), a class's ranges where it is resolved and a class that
resolves to nothing is open question O-Y3 (both 0.3.4), and a program's instructions where it is compiled (0.6.2). So
the Gate could not pass as written, and the cycle README's 0.1.6 box and O-Y3 named two of the four.

**The decision.** Every kind in §9 is provoked by a test, or is a row of Y-25's table naming the cycle that will provoke
it and why the parser cannot. `check_error_kinds_tested`, a tree check on every run, holds the table both ways: a kind
no test provokes and no row lists fails it; so does a row whose kind a test provokes — stale, and read as a promise still
owed — a row naming no kind `PatternErrorKind` declares, a row naming no cycle, and a row whose cycle's README does not
name its kind, so every row's destination is a checklist's. A test provokes a kind when a unit under `tests/unit/` that
parses a pattern names it outside a `pattern_error(…)` it builds — as a `refused` helper's argument, beside `.kind`, or
as a `pick` arm. Self-check case 33 plants each way to be wrong beside a clean tree. The 0.2 and 0.3 READMEs name the
kinds their subcycles raise, and the 0.3 README O-Y3. And two records the audit found beside the Gate: `TESTING.md`
V-19's *"cycle 0.4"* for the second check reads cycle 0.6.1, as §8's table does (S1), and §9's RX-172 note is dated as
the oldest of its four (K9).

**Measured at `5fbaf4a`.** Over the tree the check reads thirty-eight kinds, thirty-four provoked by sixteen units that
parse and four listed, and finds nothing; each of case 33's eight plants fails it by name and the clean tree passes; and
each of the plan's §1.6 mutants of the check is red at case 33 or over the tree.

*Alternatives declined:* **the four provoked now** — none is the parser's: each needs the HIR, the resolver or the
compiler; **the four retired, as RX-181 retired `EmptyAlternate`** — each has a trigger a later cycle is planned to
build, and `EmptyClass`'s is O-Y3's to decide; **the Gate kept, and cycle 0.1 left open until cycle 0.6** — a cycle held
open by kinds it cannot reach; **the check made live where the last kind is provoked** — thirty-four kinds unguarded
until then, the dormant-rule pattern the check exists to refuse; **the list in the check's own code** — a tree check
diffs the library against a document, and which kinds wait is the specification's to say.

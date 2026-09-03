# The engines

Several ways to run one program, one answer.

---

## 1. The rule that governs all of them

**Rule R-1 — every engine produces the same answer.** For a given program,
haystack and start offset, the match offsets and every capture slot are
identical whichever engine ran. An engine is a **performance** decision and can
never be a semantic one.

**Rule R-2 (RX-044) — the Pike VM is the reference.** Where an engine and the Pike VM
disagree, the Pike VM is right and the other engine has a defect. Where the
Pike VM and the naive oracle (`TESTING.md` §3) disagree, the oracle is right.
That ordering is what makes "which one is correct" never a discussion.

**Rule R-3 — every optimisation is switchable off, and the suite runs with each
off.** Prefilters, alphabet compression, suffix sharing, the one-pass engine,
the DFA — each has a switch, and the corpus stage runs the whole corpus with
each disabled in turn. An optimisation that changes an answer is caught by the
run that turns it off, and by nothing else.

---

## 2. The ladder

| Engine | Handles | Time | In 1.0 |
|---|---|---|---|
| **Pike VM** | everything, including captures | `O(m·n)` | **yes** — cycle 0.7 |
| **lazy DFA** | match *presence* and match *end*; no captures | `O(n)` amortised | **yes** — cycle 0.8 |
| **prefilters** | skipping to candidate positions | sublinear in practice | **yes** — cycle 0.9 |
| **one-pass NFA** | captures, when the program is one-pass | `O(n)` | cycle 0.11 |
| **bounded backtracker** | captures on short haystacks | `O(m·n)` bounded | cycle 0.11 |

**Rule R-4 (RX-040) — a Pike VM plus a lazy DFA plus prefilters is a defensible
1.0.**
The Pike VM alone is correct and slow; the DFA makes the common `is_match` and
`find` fast; the prefilters make the common "search a big haystack for
something rare" fast. The other two are latency optimisations for capture-heavy
workloads and they are worth having *after* there is something to measure.

---

## 3. The Pike VM

**Rule R-5 — the Pike VM simulates the NFA by keeping a set of program counters
and advancing all of them one haystack byte at a time.** Two `SparseSet`s (the
current thread list and the next), swapped each byte.

**Rule R-6 — the set is deduplicated by program counter, and that is what makes
it linear.** A program counter already in the set is not added again. A
program has `m` instructions, so a set holds at most `m` threads, and the loop
runs `n` times: `O(m·n)`, with no dependence on the pattern's ambiguity. This
single rule is the whole difference from a backtracker, and it is why `(a*)*`
against a thousand `a`s is a thousand steps here and heat death elsewhere
(`SAFETY.md` §2).

**Rule R-7 — thread priority is the order of insertion**, and `Split`'s
preferred branch is inserted first. Leftmost-first semantics
(`SYNTAX.md` Y-3) and greediness (Y-5) fall out of that ordering and are not
implemented anywhere else.

**Rule R-8 — captures are per thread**, a `Vec<int64>` of slots copied when a
thread splits. This copy is the Pike VM's real cost and is why the DFA exists
for searches that do not need captures. A program with no `Save` instructions
(`COMPILE.md` C-16) skips the machinery entirely.

**Rule R-9 — zero-width instructions are followed transitively when a thread is
added**, in one bounded walk, so the thread set only ever holds threads at
byte-consuming instructions. The walk terminates because the set is
deduplicated: `SYNTAX.md` Y-22's `(a*)*` is exactly this case.

**Rule R-10 — the Pike VM allocates nothing during a search.** Both `SparseSet`s
and the capture arena live in the caller's `Cache` (§5), sized at compile time
from the program.

---

## 4. The lazy DFA

**Rule R-11 — the DFA computes, on demand, the set of NFA states reachable
after each byte, and caches the transition.** A DFA state *is* a set of NFA
program counters; a transition is `(state, byte class) → state`. Built as the
haystack is scanned, so a pattern's exponential worst-case state count is never
constructed — only the states an actual haystack reaches.

**Rule R-12 — the DFA answers presence and end offset, never captures.** A DFA
state is a set and has lost which thread got there. `find` therefore uses the
DFA to locate the match end and then runs the Pike VM (or, from cycle 0.11, a
reverse DFA) to find the start and the captures; `is_match` needs only the DFA.

**Rule R-13 — the cache is bounded and clearing is not a failure**
(`SAFETY.md` S-14). At `NREGEX_DFA_CACHE_BYTES` the cache is cleared and
rebuilding continues. If clearing recurs so often that the DFA is doing more
work than the Pike VM would — measured as states created per byte scanned,
against a stated threshold — the meta-engine abandons the DFA **for that
search**.

**Rule R-14 — the cache is in the caller's `Cache`, never in the `Regex`**
(§5). This is what keeps a `Regex` immutable and shareable, and it is the
reason the API has a `Cache` parameter at all.

**Rule R-15 — a DFA state is looked up by the sorted set of NFA program
counters it represents.** Determinism requires the sort: two different orders
for one state set would be two cache entries for one state, which is a
correctness-neutral but reproducibility-fatal difference, and `TESTING.md` §6's
cache-behaviour assertions would be untestable.

---

## 5. The `Cache`

**Rule R-16 (RX-034) — the mutable state a search needs is a `Cache` value the
caller owns and passes in.**

```nitpick
Regex:re = regex_compile("…") ?! ERegexPattern;
Cache:cache = regex_cache(@re);              // sized from the program

Match?:m = regex_find(@re, @cache, hay);
```

Three properties follow, and every one of them is why this is the API rather
than a hidden field:

- **A `Regex` is immutable**, so any number of threads may borrow one at once
  with no lock and no atomic. The alternative — a mutex around an internal
  cache — serialises every search in the program on one lock.
- **A search allocates nothing** (`SAFETY.md` S-6). The cache is allocated once
  and reused; a search touches no allocator, which is what makes S-5's
  "matching cannot trap" true rather than merely likely.
- **The cost is visible.** A caller that wants one cache per thread writes one
  per thread; a caller that wants one per request pays for one per request. A
  hidden pool would make that decision for them, invisibly, and would be wrong
  for somebody.

**Rule R-17 — a `Cache` is not required to match its `Regex`.** A cache too
small for a program is grown at the call; a cache from another `Regex` is
reset. Mismatching one is a performance mistake, never a wrong answer and never
a trap. The alternative — refusing — would make the type carry an identity
nobody wants to manage.

**Rule R-18 — `regex_find` and friends take `@cache` by pointer**, mutate it,
and the caller keeps it. A borrow, passing down the call stack, which is the
only direction D-004 allows.

---

## 6. Prefilters

**Rule R-19 (RX-043) — a prefilter finds candidate start positions faster than
the automaton can, and never decides a match.** Every candidate is confirmed by a
real engine. A prefilter that is wrong in the direction of "too many
candidates" is slow; one that is wrong in the direction of "too few" is a
correctness defect, and R-3's off-switch run is what catches it.

**Rule R-20 — three prefilters at 1.0**, from `HIR.md` §5's extracted literals:

| Prefilter | When |
|---|---|
| **memchr** — scan for a single byte | the pattern's first-byte set has one member |
| **first-byte set** — scan for any of a small byte set | the set is small |
| **literal prefix** — scan for a required byte string | every match starts with the same literal |

**Rule R-21 — SIMD is a measurement, not an assumption.** The language has
`simd<T, N>` (D-194) and a byte scan is its textbook use. But the reductions —
`.any()` on a `simd<bool, N>` — are specified as **ordered extract-and-fold
chains**, not a movemask-and-count-trailing-zeros, and shuffles are out by
decision. So a SIMD memchr is *correct* here and its speed is unknown.

Cycle 0.13 measures a scalar and a SIMD memchr against each other and records
the number. Whichever wins ships; if SIMD loses, the finding is worth reporting
to the compiler project, because "the reduction lowering makes SIMD scanning
unprofitable" is a real consumer's evidence for a movemask intrinsic.

---

## 7. The meta-engine

**Rule R-22 — the choice is deterministic**: the same program, haystack and
start offset choose the same engine every time. No timing, no randomness, no
adaptive state that carries between searches. A caller can therefore reproduce
what happened.

**Rule R-23 — the choice is inspectable and forceable.**
`regex_last_engine(@cache)` reports what ran; `RegexOptions.force_engine`
pins one. Both exist for the test suite (`TESTING.md` §5 runs every case
through every engine) and both are public, because a user diagnosing a
performance problem needs the same information the test suite does.

**Rule R-24 — the decision order.**

1. If the program is anchored at the start and the haystack is short, the
   backtracker (when it exists), else the Pike VM.
2. If captures are wanted and the program is one-pass (when that engine
   exists), the one-pass NFA.
3. If a prefilter exists, run it to find a candidate, then confirm.
4. If the DFA is usable and its cache is healthy, the DFA — for the end, then
   the Pike VM for the start and captures if wanted.
5. Otherwise the Pike VM.

Each step's condition is a property of the program computed at compile time or
of the cache, never of the wall clock.

---

## 8. Open items

- **O-R1 — a bounded backtracker with lookaround, behind an opt-in.** Declined
  at 1.0 with the reasoning in `SAFETY.md` S-3. If a consumer arrives with a
  real need, the shape is: a separate `RegexBacktrack` type, a separate
  `compile` entry point, a step budget in the options, an explicit error when
  the budget is exhausted, and a documentation page that says the linear-time
  guarantee does not apply to it. Kept open because declining a feature is
  cheaper to revisit than removing one.
- **O-R2 — reverse DFA for capture start.** Cycle 0.8 decides; `COMPILE.md`
  O-C2 is the compiler half.

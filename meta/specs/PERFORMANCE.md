# Performance

What is promised, what is measured, and what is explicitly not promised.

---

## 1. What is promised

**Rule F-1 — the only promise is the asymptotic one.** A search is `O(m · n)`
in the worst case and `O(n)` amortised when the DFA is running
(`SAFETY.md` S-1). Nothing else about speed is a guarantee, and this document
exists so that the difference between a guarantee and a measurement is never
blurred.

**Rule F-2 — what is explicitly NOT promised**, stated because a reader
arriving from a mature engine will assume otherwise:

- **constant factors comparable to RE2 or Rust's `regex`.** Those have had a
  decade of tuning, hand-written SIMD, and a memchr the platform provides.
- **SIMD acceleration**, until it is measured to help (`ENGINES.md` R-21).
- **that the meta-engine picks the fastest engine.** It picks by a stated rule
  (`ENGINES.md` R-24) that is deterministic and inspectable, which is more
  useful than adaptive and is sometimes slower.
- **compile-time speed.** Compiling `\p{L}{100}` is allowed to be slow; it is
  bounded, which is the property that matters.

---

## 2. The benchmark set

**Rule F-3.** Six benchmarks, each with a committed baseline, run by
`harness/bench.py`:

| Benchmark | Measures |
|---|---|
| `literal` — a fixed string in 1 MiB of text | the prefilter path, which is the common case in real programs |
| `class_scan` — `\p{Greek}+` over 1 MiB of mixed script | the DFA with a compressed alphabet |
| `captures` — a date pattern with three groups over 100 000 lines | the Pike VM's capture copying, its dominant cost |
| `alternation` — a 50-branch literal alternation | the multi-literal prefilter and the DFA's state growth |
| `pathological` — `(a+)+$` over 100 KiB of `a` | **the guarantee.** It must finish, and its time must be linear |
| `compile` — `\p{L}{100}` and a 500-branch alternation | compile-time bounds |

**Rule F-4 (RX-080) — every benchmark reports steps as well as time.** Time varies with
the machine; **step count does not**, so a regression in steps is a real
regression and a regression in time alone may be the machine. The gate is on
steps; time is recorded and reported.

**Rule F-5 — the gate is 20% against the committed baseline on the same
machine**, and a baseline is re-recorded by a deliberate act, like a golden
(`TESTING.md` §10).

---

## 3. Where the costs are, and what to do about them

Recorded now so that cycle 0.13 measures the right things rather than
discovering them.

**The Pike VM's capture copying** (`ENGINES.md` R-8) is the dominant cost of
any search that wants captures, because a thread's capture slots are copied on
every split. The mitigations, in the order they are worth trying: compile
without `Save` when captures are not wanted (already, C-16); the one-pass NFA
for programs that never split ambiguously (cycle 0.11); a reverse DFA to find
the start so the Pike VM runs over the match only (O-C2).

**The DFA's cache pressure** is why alphabet compression exists
(`COMPILE.md` C-7). The measurement that matters is states-created-per-byte,
which is also the number R-13's fallback keys on.

**A large Unicode class is a large program** (`COMPILE.md` C-5) and shows up as
both compile time and DFA state count. `\p{L}` is the benchmark.

**Allocation is not a cost on the search path at all** (`SAFETY.md` S-6), which
is unusual and is worth protecting: a benchmark that shows allocation in a
search is a defect, and the harness asserts zero allocator calls during the
search phase of every benchmark.

---

## 4. Open items

- **O-F1 — a SIMD memchr.** `ENGINES.md` R-21. Measured at cycle 0.13 against
  the scalar version; whichever wins ships, and a loss is a finding worth
  reporting to the compiler project as a consumer's evidence for a movemask
  intrinsic.

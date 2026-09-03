# Testing

The instruments. The compiler project's recurring finding is that **the checks
that diff two lists found the holes and the tests did not**, and that a suite
which only ever agrees with what it is handed reports green while checking
nothing. This is `nregex`'s answer to both.

---

## 1. The stages

`BUILD.md` §3 lists them; this is what each is *for*.

| Stage | Answers |
|---|---|
| `parse` | every source in the tree is readable by the real parser |
| `accept` | the public API compiles in a program that only imports it |
| `check` | every documented refusal actually refuses, with exactly its code |
| `program` | the library does what it says, judged by exit code, at -O0 and under `opt -O2` |
| `corpus` | every committed pattern/haystack/expectation triple gives the expected answer **through every engine** |
| `oracle` | the naive reference matcher and every real engine agree over a generated corpus |

---

## 2. Everything is headless

**Rule V-1.** `nregex` makes no syscall, opens no file and reads no
environment. There is no device to double and nothing to skip: **the entire
suite runs anywhere, under a debugger, forty times over.**

This is worth stating because it removes the largest structural risk from every
other library in this ecosystem. The only external inputs are the pattern and
the haystack, both of which a test supplies.

**Rule V-2 — the harness asserts that.** The undefined-symbol scan
(`BUILD.md` B-2) is held to a **committed expected symbol list**: the
allocator, `memcpy`/`memset`, and the string primitives. A syscall appearing in
a `nregex` object is a red run.

---

## 3. The naive oracle

**Rule V-3 (RX-070) — a deliberately simple, obviously-correct backtracking
matcher over the HIR**, in `tests/oracle/`, exponential in the worst case and
run only on tiny inputs.

```
pattern ──► HIR ──┬──► naive matcher ──► answer A
                  └──► compile ──► engine ──► answer B
                                                 A == B, or a defect
```

**Rule V-4 — it imports nothing from `src/` but `core` and `hir`.** A shared
bug would make it agree with the thing it judges. `check_layering`
(`BUILD.md` B-17) enforces the boundary.

**Rule V-5 — it is written and tested BEFORE any real engine** (cycle 0.5,
before the NFA compiler at 0.6), against hand-written pattern/haystack cases,
so that the compiler and the Pike VM are developed against an instrument that
already works. This is the compiler's "instruments precede the constructs they
guard", and it is the reason this library's cycle order looks unusual.

**Rule V-6 — it is allowed to be slow and it is allowed to be exponential.** It
runs with a step counter and abandons a case that exceeds it, reporting the
case as *not compared* rather than as a failure. A pattern the oracle cannot
finish is exactly the pattern the whole design exists to make fast, and losing
the comparison on those is the price of having an independent reference at all.

---

## 4. The corpus

**Rule V-7 — a fixture is a committed triple**: the pattern, the haystack, and
the expected match offsets and capture slots. Text, diffable, byte-stable.

**Rule V-8 (RX-071) — three sources, and each says what it is:**

- **Ours**, written against `SYNTAX.md` — every construct, every refusal, every
  bound sat on exactly and exceeded by one.
- **Third-party**, fetched by pinned revision rather than vendored, with
  `meta/research/corpora/README.md` recording which suite and which revision.
  The candidates, decided at cycle 0.5: **RE2's test data** (closest semantics
  — leftmost-first, no backreferences, so its expectations are ours), **Rust
  `regex`'s test suite** (closest feature set, including Unicode classes and
  class set operations), and the **AT&T POSIX test set** (broad, old, and its
  leftmost-longest expectations must be filtered or reinterpreted — noted so
  nobody adopts them wholesale).
- **The fuzzer's**, permanently, every case it ever found (§7).

**Rule V-9 — a fixture that came from a bug names the bug** in a comment. A
corpus of anonymous cases is a corpus nobody dares delete from.

**Rule V-10 — compiled programs are fixtures too** (`COMPILE.md` C-19). The
program's stable text dump is committed for a set of representative patterns,
so a compiler change is a visible three-line diff rather than a mystery, and a
change that was not intended fails a test.

---

## 5. Cross-engine agreement

**Rule V-11 (RX-041) — the corpus stage runs every case through every
engine**, forced by `RegexOptions.force_engine`, and requires identical
offsets and identical capture slots. Not "the meta-engine's choice was right"
— *every* engine, on *every* case.

**Rule V-12 — and with each optimisation off in turn** (`ENGINES.md` R-3):
prefilters off, alphabet compression off, suffix sharing off, DFA off. An
optimisation that changes an answer is caught by the run that disables it, and
by nothing else.

**Rule V-13 — this is the strongest correctness statement the library makes**,
and it is the analogue of `nitpick-tui`'s render-and-parse-back round trip: a
defect that produces a plausible answer survives a hand-written expectation and
does not survive four independent implementations being required to agree.

---

## 6. The linear-time property test

**Rule V-14 (RX-072) — the guarantee is tested, not asserted.**

For a generated set of patterns — including the classic catastrophic family
`(a+)+$`, `(a|a)*$`, `(a|aa)*$`, `a?{n}a{n}` — and haystacks of geometrically
increasing length, the test records the **step count** each engine reports and
requires it to grow no faster than linearly in the haystack length, within a
stated constant.

**Rule V-15 — engines count their steps** and expose the count for this test.
A step counter on the hot path is a cost, so it is behind a build switch that
the property test turns on and nothing else does.

**Rule V-16 — this test is the reason the library exists**, and it is the one
that would be quietly dropped when it goes red under a refactor. It is in the
gate for every cycle from 0.7 onward.

---

## 7. Fuzzing

**Rule V-17 — two fuzzers**, because the two inputs fail differently.

**The pattern fuzzer** generates structured patterns — random trees over the
`SYNTAX.md` grammar, biased toward nesting, large repetitions, and large
classes — and requires: the compiler either produces a program or a
`PatternError` with a valid offset; it never traps; it never exceeds a bound
without reporting it; it always terminates.

**The haystack fuzzer** takes a corpus pattern and generates haystacks —
random bytes, invalid UTF-8, very long runs, and strings derived from the
pattern itself — and requires: every engine agrees; the naive oracle agrees
where it finishes; no search allocates; no search traps; offsets are within the
haystack and, in Unicode mode, on UTF-8 boundaries.

**Rule V-18 — anything a fuzzer finds becomes a permanent fixture**, minimised,
with the defect named.

---

## 8. What the harness checks about the tree

Not tests. Checks that diff the library against the documents describing it,
run on every full invocation.

| Check | Diffs |
|---|---|
| `check_tables_regenerate` | the committed Unicode tables against a fresh generator run |
| `check_table_invariants` | every range table sorted, disjoint, `lo <= hi`, within `U+10FFFF` |
| `check_error_budget` | public `error:` declarations against `SAFETY.md` §4 — **exactly one** |
| `check_error_kinds_tested` | every `PatternErrorKind` against the tests that provoke it (`SYNTAX.md` Y-25) |
| `check_inst_kinds_total` | every `InstKind` emitted by the compiler and handled by every engine and the oracle |
| `check_hir_kinds_total` | the same for `HirKind` |
| `check_layering` | every `use` edge against `BUILD.md` §6, including the oracle's restriction |
| `check_constants_named` | no bound outside `src/core/limits.npk` |
| `check_no_syscalls` | the object's undefined symbols against the committed list |
| `check_byte_class_partition` | `COMPILE.md` C-9's property, over every corpus program |
| `check_specs_current` | reports, does not fail: spec citations that no longer resolve |

**Rule V-19 — `check_error_kinds_tested` and `check_inst_kinds_total` are the
two that matter most.** A `PatternErrorKind` nothing can produce is a promise
the documentation makes and the code does not keep; an `InstKind` an engine
does not handle is a wrong answer waiting for the pattern that emits it.

---

## 9. The harness is tested

**Rule V-20 — the self-check** feeds the harness wrong expectations and
requires it to report every one as a failure:

- a `program` case with the wrong `expect-exit`;
- a `check` case expecting a code the compiler does not report;
- a `check` case reporting a code no expectation names (the D-237 rule);
- a corpus fixture whose expected offsets are off by one;
- a corpus fixture that passes under one engine and fails under another —
  **the case that proves V-11 is doing work**;
- a generated table differing from the generator's output by one line;
- an oracle disagreement.

**Rule V-21 — the self-check runs first in every full invocation.** A harness
that has not proven it can fail has not proven anything.

---

## 10. Performance regression

**Rule V-22.** `harness/bench.py` writes a line per benchmark into
`meta/bench/<date>.txt` and the harness fails on a regression worse than 20%
against the committed baseline on the same machine. `PERFORMANCE.md` has the
benchmark set. A baseline is re-recorded by a deliberate act, like a golden.

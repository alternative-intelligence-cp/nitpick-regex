# Cycle 0.13 — Performance

**Benchmarks, baselines, the regression gate, and the two measurements the plan
has been deferring.**

## Why after hardening

Measuring an implementation that is still changing measures noise. Both open
measurements — the SIMD scanner and the step counter's cost — are decisions
that want a stable subject.

## Decisions in

RX-080. Settled.

**Open questions to settle:** O-F1 / O-G4 (does SIMD scanning pay?), O-P1 (does
the step counter ship?). **Both are measurements**, and this is the cycle that
takes them.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.13.0 | **The bench harness** — the six benchmarks, steps and time | numbers before any optimisation |
| 0.13.1 | **The baselines and the gate** — committed, 20% on steps | a regression is a red run |
| 0.13.2 | **The SIMD measurement** — scalar against `simd<uint8, N>` | O-F1 decided by a number |
| 0.13.3 | **The step-counter measurement** — the cost of shipping it | O-P1 decided by a number |
| 0.13.4 | **Whatever the numbers say** — the optimisations they justify | recorded, each with its measurement |
| 0.13.5 | **Close** | `done/0.13/`, `0.14.0.md` written |

## Checklist

### 0.13.0 — the bench harness
- [ ] `harness/bench.py` writing one line per benchmark into `meta/bench/<date>.txt`
- [ ] the six from `PERFORMANCE.md` §2: `literal`, `class_scan`, `captures`, `alternation`, `pathological`, `compile`
- [ ] **each reports steps as well as time** (RX-080) — step count is machine-independent and is what the gate uses
- [ ] the allocator counter asserted at zero for the search phase of every benchmark
- [ ] `pathological` — `(a+)+$` over 100 KiB — **must finish**, and its time must be linear. It is the guarantee, measured

### 0.13.1 — the baselines and the gate
- [ ] committed baselines, per machine, with the machine recorded
- [ ] 20% regression gate on **steps**; time recorded and reported but not gated
- [ ] a baseline re-recorded by a deliberate act, like a golden
- [ ] the gate has been seen to fail, by a deliberate pessimisation

### 0.13.2 — the SIMD measurement
- [ ] a `simd<uint8, N>`-based `memchr` behind 0.9.0's stable scanner signature
- [ ] measured against the scalar version on the `literal` benchmark at several haystack sizes
- [ ] **the known unknown**: `.any()` on a `simd<bool, N>` lowers to an ordered extract-and-fold chain, not a movemask plus count-trailing-zeros, and shuffles are out by decision (D-194). So SIMD may lose here, and that is a legitimate result
- [ ] whichever wins ships
- [ ] **if SIMD loses, the measurement is written up as O-G4's evidence** and raised in the compiler repository — a consumer's number is a much better request than a speculative one

### 0.13.3 — the step-counter measurement
- [ ] the cost of the counter measured on `class_scan` and `captures`
- [ ] O-P1 decided: **ship it** unless it measures worse than 3%
- [ ] if it ships, `VERIFICATION.md` P-10's obligation becomes about the real code, and the guarantee becomes measurable in production
- [ ] the decision recorded either way, with the number

### 0.13.4 — whatever the numbers say
- [ ] the benchmarks will point somewhere — capture copying, DFA state growth, class compilation. Follow the largest, once
- [ ] **every optimisation is subject to RX-041**: it gets an off-switch and the corpus runs with it off
- [ ] resist optimising what the benchmarks do not point at

### 0.13.5 — close
- [ ] `PERFORMANCE.md` updated with the measured numbers, replacing the prose about where the costs are with where they actually were
- [ ] findings written; `0.14.0.md` written; archived

## Gate

All six benchmarks with committed baselines, the gate seen to fail, and both
open measurements taken and recorded as decisions.

## Watch for

- **Do not gate on time.** It varies with the machine, the thermal state and
  the phase of the moon; steps do not.
- **`pathological` is a correctness benchmark wearing a performance costume.**
  If it ever stops finishing, that is RX-003 broken, not a slow day.
- **The SIMD result may be negative and that is fine.** A measured "no" is
  worth more than an unmeasured "probably", and it is the strongest form the
  compiler request can take.

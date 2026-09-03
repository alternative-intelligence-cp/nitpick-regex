# Cycle 1.0 — Release

**Documentation, the API freeze, the one-arm contract, and versioning.**

## Decisions in

RX-005 (a second error identity is a major version). The version policy itself
is settled here.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 1.0.0 | **The API freeze** — the public surface enumerated and reviewed | `src/lib.npk` as the contract |
| 1.0.1 | **The one-arm contract** — the `failsafe` cost, published | a consumer knows exactly what importing costs |
| 1.0.2 | **The guide** — `docs/`: the model, the syntax, the guarantee, the limits | a person can use it from the documentation alone |
| 1.0.3 | **Examples** — one per entry point, plus the `grep` | every example built and run by the harness |
| 1.0.4 | **Versioning** — the policy, written where a consumer reads it | a stated policy including what a major version means |
| 1.0.5 | **Close** — the post-1.0 map reviewed | `done/1.0/` |

## Checklist

### 1.0.0 — the API freeze
- [ ] `src/lib.npk` lists every public name, one per line, grouped by module
- [ ] each reviewed: is it needed, is it named right, does it belong at this layer?
- [ ] anything not needed removed **now** — removing a public name after 1.0 is a major version
- [ ] the conformance test touches every name

### 1.0.1 — the one-arm contract
- [ ] published prominently: **importing `nregex` costs your `failsafe` exactly one arm**, `ERegexPattern`
- [ ] `check_error_budget` proving the published claim is what a program actually owes
- [ ] the rule that a second identity is a **major version** (RX-005), with the reason: REACH-002 makes it a compiler-enforced source break in every consumer
- [ ] `PatternErrorKind`'s full list published, so a caller can report precisely without a second identity ever being wanted

### 1.0.2 — the guide
- [ ] getting started: compile, search, capture, replace, in under thirty lines
- [ ] **the guarantee, first**: what linear time means, what it costs, and why
- [ ] the syntax reference, generated from `SYNTAX.md` so it cannot drift
- [ ] **a page on what `nregex` deliberately does not do, and why** — no backreferences, no lookaround, no atomic groups, no recursion, simple folding only, no blocks — each naming the alternative, and each reachable in one click from the refusal it produces (K-2)
- [ ] the `Cache` explained: why it exists, how many you want, and that a mismatched one is never wrong
- [ ] the `COMPAT.md` difference lists, as measured
- [ ] performance: what is promised (the asymptotic bound) and what is not (constant factors)

### 1.0.3 — examples
- [ ] one per entry point, minimal
- [ ] the `grep` from 0.14
- [ ] every example built **and run** by the harness, so a broken example is a red run

### 1.0.4 — versioning
- [ ] the policy recorded as a decision: `0.x` until the API has survived 0.14's consumer, then semantic versioning
- [ ] **adding a public error identity is a major version** — stated where a consumer reads it, because it is a rule no other language's library has to have
- [ ] the Unicode version bump policy: a new UCD is a **minor** version and re-runs the corpus, because a property that changes is a set of patterns that match differently

## Gate

A person who has not seen the code can write a working program from `docs/`
alone, and every example is green in the harness.

## After

The post-1.0 map in `ROADMAP.md`: `RegexSet` (1.1), the reverse DFA if 0.13's
numbers ask for it (1.2), full case folding if a consumer needs it (1.3), and
the verified build once `npkg verify` reaches libraries (1.4).

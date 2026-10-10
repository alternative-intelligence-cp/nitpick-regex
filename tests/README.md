# `tests/`

| Directory | Stage | Contents |
|---|---|---|
| `probe/` | `program` | the cycle-0.0 language probes; **never deleted** |
| `conformance/` | `compile`, `positive` | the public API compiles, links and runs in a program that only imports it |
| `unit/` | `program` | behaviour, judged by exit code |
| `oracle/` | `program` — *not declared yet* | the naive reference matcher, and the cross-engine agreement runner |
| `rejection/` | `check` | programs the compiler must refuse, with exactly the expected codes |
| `fixtures/` | `fixture` — *not declared yet* | pattern/haystack/expectation triples, including everything the fuzzer found |

Expectations live in the test file. Governed by `../meta/specs/TESTING.md`.
*(2026-10-10, cycle 0.2.2 — the documents audit's RA-1: `conformance/` is judged at `compile`, `positive`, as
`../nitpick.toml` declares it — `accept` is not available to this library (`BUILD.md` B-4a, RX-117) — and `oracle/` and
`fixtures/` are in no suite `nitpick.toml` declares yet: the cycles that fill them declare them. Until then this table
named `accept`, and gave both stages as if declared.)*

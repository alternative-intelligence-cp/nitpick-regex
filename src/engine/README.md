# `src/engine/` — the engines

The Pike VM (the reference implementation every other engine is checked
against), the lazy DFA with its bounded cache, the literal prefilters, and the
deterministic meta-engine that chooses. **No engine may change an answer.**
Governed by `meta/specs/ENGINES.md`. Built in cycles 0.7 to 0.9 and 0.11.

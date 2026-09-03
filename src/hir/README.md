# `src/hir/` — the high-level intermediate

Desugaring and normalisation: repetitions expanded under a bound, classes
folded into codepoint ranges, literals extracted for the prefilters, and the
whole tree flattened into a POD arena. Governed by `meta/specs/HIR.md`. Built
in cycle 0.2.

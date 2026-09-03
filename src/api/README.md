# `src/api/` — the public surface

`Regex`, `Cache`, `Match`, `Captures`, the match iterators, and template
replacement. A `Match` carries byte offsets, never a slice, because a slice is
a second-class borrow that cannot be returned (D-004). Governed by
`meta/specs/API.md`. Built in cycle 0.10.

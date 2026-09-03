# `src/core/` — storage primitives

`Vec<T>`, `Bytes`, `ByteSet` (a 256-bit class bitmap), `SparseSet` (the Pike
VM's thread set), and `limits.npk` — every named bound in the library, in one
file. Depends on nothing. Governed by `meta/specs/BUILD.md` §5. Built in cycle
0.0.4.

# `tests/oracle/`

The **naive reference matcher**: a deliberately simple, obviously-correct
backtracking matcher over the HIR, exponential in the worst case and run only
on tiny inputs. It is what the Pike VM is developed against, and it is this
library's equivalent of `nitpick-tui`'s miniature VT.

It imports nothing from `src/` but `core` and `hir`, so a shared bug cannot
make it agree with the thing it judges. Built in cycle 0.5, **before** any real
engine.

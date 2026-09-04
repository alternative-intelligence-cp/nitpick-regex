# `harness/baseline/` — the floor, measured

`baseline.npk` is an empty Nitpick program: an empty `main`, a `failsafe`, and
no import at all. It is not a test and nothing in `nitpick.toml` declares it.

It exists because **`check_no_syscalls` is a difference and not a list**
(`../../meta/DECISIONS.md` RX-116). A program containing no library code has 29
undefined symbols — among them `npk_open`, `npk_read`, `npk_write` and
`npk_sys6` — because they are the prelude's, emitted into every translation
unit. An absolute allowlist fails on this file; a difference against it is
exactly "what did `nregex` add".

Two sets are recorded, both by `python3 harness/run.py --record-baseline`:

| File | What | Catches |
|---|---|---|
| `SYMBOLS.txt` | the object's undefined symbols | a floor symbol the library newly **needs** |
| `EDGES.txt` | every `function → floor symbol` call edge in the −O0 IR | a floor symbol the library newly **calls** |

**The second exists because the first cannot see a syscall** (RX-120). Measured
at `950bb1d`: a four-line program with a `sys(39i64)` call in `main` has the
same 29 undefined symbols as this one and the same empty symmetric difference,
because `npk_sys6` is already here. It has one more `call i64 @npk_sys6` site,
and that site is in `main`.

**Re-recording is a deliberate act**, like re-recording a golden. A difference
here is a **prelude change** in a moving compiler, not a library change, and it
belongs in its own commit where a reviewer sees it as a one-line diff.

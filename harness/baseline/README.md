# `harness/baseline/` — the floor, measured

`baseline.npk` is an empty Nitpick program: an empty `main`, a `failsafe`, and
no import at all. It is not a test and nothing in `nitpick.toml` declares it.

It exists because **`check_no_syscalls` is a difference and not a list**
(`../../meta/DECISIONS.md` RX-116). At compiler `950bb1d` a program containing
no library code had 29 undefined symbols — among them `npk_open`, `npk_read`,
`npk_write` and `npk_sys6` — because they were the prelude's, emitted into every
translation unit. An absolute allowlist fails on this file; a difference against
it is exactly "what did `nregex` add". *(The count is one compiler's: 2 at
`3d15ac9` and 5 at `c3bdae2`, below.)*

Two sets are recorded, both by `python3 harness/run.py --record-baseline`:

| File | What | Catches |
|---|---|---|
| `SYMBOLS.txt` | the object's undefined symbols | a floor symbol the library newly **needs** |
| `EDGES.txt` | every `function → floor symbol` call edge in the −O0 IR | a floor symbol the library newly **calls** |

**The second exists because the first cannot say WHERE a syscall is** (RX-120,
as amended by RX-131).

Measured at `950bb1d`, when the reason was stronger still: a four-line program
with a `sys(39i64)` call in `main` had the same 29 undefined symbols as this one
and the same empty symmetric difference, because `npk_sys6` was already here. It
had one more `call i64 @npk_sys6` site, and that site was in `main`.

**At `3d15ac9` the first layer CAN see that a syscall exists** — D-262 emits a
prelude item only when it is referenced, so this file's floor is 2 symbols with
no `npk_sys6` and a syscaller's is 3. The reproduction of both pins, command by
command with every exit code, is [`RX120.txt`](RX120.txt). The second layer is
not retired by that and is not weaker for it: it names the calling function,
which no symbol set can, and it is indifferent to what the prelude emits — so a
future prelude that carries `npk_sys6` again blinds the first layer and not
this one.

**At `c3bdae2` the floor is five symbols** — measured 2026-09-25 at cycle
0.0.4b and re-recorded in a commit of its own (RX-148): `__morestack`,
`npk_chain_reset`, `npk_dalloc`, `npk_ofd_close` and `npk_trap`; four call
edges, the two new ones `npk_failsafe → npk_chain_reset` and
`npk_failsafe → npk_trap`; a syscaller is **6**, and the difference is still
exactly `{npk_sys6}`, which is the claim that matters. What moved, and why:

- **`__morestack`** is the compiler's D-305: every function it emits carries
  LLVM's `split-stack` prologue, which compares the stack pointer less the
  function's frame against a per-thread limit before the frame exists, and the
  floor's `__morestack` turns an overflow into the controlled trap
  `StackExhausted`. So every program references it, the empty one included —
  and every `failsafe` must now name `StackExhausted`, with D-307's
  `MachineFault` beside it.
- **`npk_trap` and `npk_chain_reset` were `RESIDUE.txt` entries and are the
  floor's now**: `failsafe`'s own machinery reaches both, so the empty program
  has them, and a residue entry is what this library needs *beyond* the floor.
  Their reasons, kept here rather than deleted with the lines, as `RESIDUE.txt`
  gave them at `3d15ac9`:
  - `npk_trap` — *"the trap path. EVERY bounds check in this library reaches
    it: `vec_oob` is a deliberate `OutOfBounds`, and D-210's overflow and
    D-007's division traps land here too. It is not a syscall; it is the
    controlled stop this ecosystem exists to produce."*
  - `npk_chain_reset` — *"the `defer` machinery (D-014), emitted for scope exits
    rather than written by hand here. Note that `npk_chain_push` is NOT on this
    list: it was added on the assumption that the pair travels together, and the
    both-directions check refused it because no scanned program references it.
    That is the list working -- an entry added by reasoning rather than by
    measurement is exactly what it exists to catch."*

`rx120.sh` asserts 5 / 6 / `{npk_sys6}` at `c3bdae2`, and its `950bb1d` leg
still reproduces RX-120 as first measured — 29 / 29, identical, `npk_sys6` in
the floor — by compiling both programs with the two arms that compiler does not
have removed (RX-148).

**Re-recording is a deliberate act**, like re-recording a golden. A difference
here is a **prelude change** in a moving compiler, not a library change, and it
belongs in its own commit where a reviewer sees it as a one-line diff.

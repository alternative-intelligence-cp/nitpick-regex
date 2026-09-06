#!/usr/bin/env python3
"""The emitted IR's CALL EDGES to the floor -- `check_no_syscalls`, second layer.

WHY THIS EXISTS, AND IT WAS MEASURED RATHER THAN REASONED. RX-116 made the
no-syscall check differential: an `nregex` program object's undefined-symbol
set must equal an empty baseline program's. That catches a floor symbol the
library newly NEEDS. It cannot catch a floor symbol the library newly CALLS,
because at 950bb1d every syscall in the language goes through ONE symbol the
baseline already carries.

Measured 2026-09-04 AT COMPILER `950bb1d` -- naming the commit rather than
saying "at the pin", because the pin moves and a measurement dated to a moving  # check_dated_measurements: exempt
name goes false with nobody editing it (cycle 0.0.5). Two four-line programs
differing only in a `sys(39i64)` call in `main`:

    baseline    29 undefined symbols   2 `call i64 @npk_sys6` sites
    syscaller   29 undefined symbols   3 `call i64 @npk_sys6` sites
    symmetric difference of the symbol sets: EMPTY

So the symbol scan alone reported a clean run on a program that had just made a
syscall, and 0.0.2's acceptance item -- "a deliberately introduced `sys(...)`
call fails `check_no_syscalls`, by name" -- could not have been met by the
instrument that was specified for it. RX-120.

AT `3d15ac9` THAT HALF HAS EXPIRED AND THIS MODULE IS STILL THE ANSWER. D-262
emits a prelude item only when it is referenced, so the floor is 2 symbols with
no `npk_sys6`, the syscaller is 3, and the difference IS that symbol -- both
pins run back to back in `harness/baseline/RX120.txt`. What does not expire is
the reason this scan exists in the form it has: the symbol layer reports THAT a
kernel symbol is needed and can never report WHERE it is called from, and a
prelude that starts emitting `npk_sys6` again would blind it a second time.
RX-131 corrects the clause; RX-120's decision stands.

WHAT THIS SCANS. Every `(enclosing function, callee)` edge in the -O0 IR whose
callee is DECLARED and not DEFINED in the module. The baseline's edge set is
the floor's own, emitted into every translation unit; an edge a program has and
the baseline does not was written here.

THREE THINGS MEASUREMENT FORCED, and each was a false positive on the first run
over the real suite (16 of 16 probes red):

  1. `llvm.*` IS NOT THE FLOOR. `llvm.sadd.with.overflow.i64` is declared and
     not defined, and it is an INSTRUCTION, not a symbol the linker resolves --
     it never reaches the object's symbol table at all. Excluded by prefix.
  2. COMPILER-GENERATED GLUE IS NUMBERED, AND THE NUMBER MOVES. The baseline
     has `npk.drop.365` calling `npk_ofd_close`; probe04 has the same drop glue
     as `npk.drop.367`, because the counter shifts with program content. The
     trailing `.<digits>` is not part of a function's identity, so it is
     normalised away before the difference is taken. A library function --
     `npk.nregex.core.vec.vec_push` -- never normalises onto a generated name.
  3. THE DENY LIST IS SMALLER AND TRUER THAN A PERMIT LIST. A permit list was
     tried first and failed all 16 probes: the residue is dominated by
     `npk_trap` (the trap path every bounds check reaches), `npk_chain_push` /
     `npk_chain_reset` (the `defer` machinery every function with a `defer`
     gets), the allocator, and `npk_string_concat` -- none of which is a
     syscall. What RX-008 actually forbids is REACHING THE KERNEL, and that is
     seven symbols, named below.
"""
import re

# Reaching the kernel, or touching a descriptor. Drawn from the baseline's own
# 29 undefined symbols, which is why this list can be short: a floor symbol the
# baseline does NOT have is caught by the other layer (`build.zero_dep`), with
# no list at all.
#
# The async family -- `npk_exec`, `npk_run_until`, `npk_thread_join`,
# `npk_park_until`, `npk_join_deadline`, `npk_windup_*` -- is deliberately NOT
# here. `await` is a language feature, `probe07` exercises it on purpose, and
# refusing a language probe for using the language would be this check failing
# the wrong thing. Matching in this library can never be async (RX-061), and
# that is held by the error budget rather than by a symbol scan.
DENIED = {
    "npk_sys6",                       # every syscall in the language
    "npk_open", "npk_read", "npk_write",
    "npk_ofd_close", "npk_io_register", "npk_io_unwatch",
}

_SYM = r'@(?:"([^"]*)"|([\w.$\-]+))'
_DEFINE = re.compile(r'^\s*define\b.*?' + _SYM + r'\s*\(')
_DECLARE = re.compile(r'^\s*declare\b.*?' + _SYM + r'\s*\(')
_CALL = re.compile(r'\b(?:call|invoke)\b.*?' + _SYM + r'\s*\(')
_GENERATED = re.compile(r'\.\d+$')


def _name(m):
    return m.group(1) if m.group(1) is not None else m.group(2)


def normalise(fn):
    """`npk.drop.365` and `npk.drop.367` are the same glue -- finding 2 above."""
    return _GENERATED.sub(".N", fn)


def edges(ir_text):
    """{(normalised function, callee)} for every call to a floor symbol."""
    defined, declared = set(), set()
    for line in ir_text.split("\n"):
        m = _DEFINE.match(line)
        if m:
            defined.add(_name(m))
            continue
        m = _DECLARE.match(line)
        if m:
            declared.add(_name(m))
    floor = {s for s in (declared - defined) if not s.startswith("llvm.")}

    out, cur = set(), None
    for line in ir_text.split("\n"):
        m = _DEFINE.match(line)
        if m:
            cur = _name(m)
            continue
        if line.startswith("}"):
            cur = None
            continue
        if cur is None:
            continue
        m = _CALL.search(line)
        if m and _name(m) in floor:
            out.add((normalise(cur), _name(m)))
    return out


def scan(ir_text, baseline_edges, name):
    """Failures, one line each, naming the function AND the symbol."""
    fl = []
    for fn, callee in sorted(edges(ir_text) - baseline_edges):
        if callee not in DENIED:
            continue
        fl.append(f"{name}: `{fn}` calls `{callee}`, and the baseline does not. "
                  f"`nregex` makes no syscall and touches no descriptor (RX-008); "
                  f"this is the check that NAMES THE CALLING FUNCTION, which the "
                  f"undefined-symbol layer cannot do at any pin (RX-120, RX-131). "
                  f"If this call is legitimate, removing the symbol from "
                  f"`harness/irscan.py` DENIED is a decision, not a fix.")
    return fl

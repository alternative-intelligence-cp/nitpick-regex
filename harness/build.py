#!/usr/bin/env python3
"""The build pipeline, and `npkc`'s exit alphabet -- `BUILD.md` §2, rules B-0..B-3.

THE UNIT IS A PROGRAM ROOT AND THERE IS NO LIBRARY OBJECT (B-0, RX-115). Every
file in `src/` compiles at `npkc` exit 0 and every one is refused by `llc` with
`use of undefined value '@npk_failsafe'`, because `npkc` emits calls to that
symbol into every translation unit and never a `declare` for it; only a
program's own `failsafe` produces the `define`. So there is no
`build/nregex.o`, nothing to link against, and cycle 0.0.2's planning decision
P-14 -- "one build of the library per run, reused by every program" -- is not
achievable at this pin. Each program root compiles the whole graph it reaches.
Provisional workbench O-N14 would make P-14's shape possible again; it is
accepted into the compiler's 1.5.1b step 3c, and this file is what changes.

`npkc`'s EXIT CODES ARE AN ALPHABET AND EVERY STAGE ASSERTS THE SPECIFIC
INTEGER (`tests/conformance/TRANSCRIPT.txt` §F, measured in §G):

    0  success
    1  REFUSED, with diagnostics -- the compiler judged the program and said no
    2  the driver COULD NOT PROCEED and judged nothing, SILENTLY
    3  a `failsafe` trap in the compiler itself

`2` IS NOT A REFUSAL. A test expecting 1 that receives 2 was never compiled, so
it proved nothing while reporting that it did -- and 2 arrives with an empty
stderr, so a runner that logs only what the compiler said shows no reason at
all. Every message this module produces for a 2 says so in as many words.
"""
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import elf                                                    # noqa: E402
import irscan                                                 # noqa: E402

NPKC_OK, NPKC_REFUSED, NPKC_BROKEN, NPKC_TRAPPED = 0, 1, 2, 3

COMPILE_TIMEOUT = 300
TOOL_TIMEOUT = 300
RUN_TIMEOUT = 30


class Run:
    def __init__(self, argv, cwd=None, timeout=TOOL_TIMEOUT, stdin_null=True):
        self.argv = argv
        self.timed_out = False
        try:
            r = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=timeout,
                               stdin=subprocess.DEVNULL if stdin_null else None)
            self.code = r.returncode
            self.out = r.stdout
            self.err = r.stderr.decode("utf-8", "replace")
        except subprocess.TimeoutExpired:
            self.timed_out = True
            self.code = None
            self.out = b""
            self.err = ""

    @property
    def status(self):
        """The process's exit status, or `0 - signal` when it was killed -- npkg's
        convention, so `expect-exit: -11` means SIGSEGV in both runners."""
        if self.code is None:
            return None
        return self.code if self.code >= 0 else self.code

    def shown(self):
        return " ".join(self.argv)


# --- diagnostics, as the harness reads them ---------------------------------------
#
# `CODE path:line:col: message`, with `note ` / `warning ` in front for those
# severities: the code is token 0, the span token 1, THE MESSAGE IS NEVER
# ASSERTED (rule B-6). A note goes to its own channel; a warning is a finding.
# Mirrors `npkg/suites.npk`'s `findings_of` at 950bb1d.

def findings_of(stderr):
    out = []
    for line in stderr.split("\n"):
        parts = line.split()
        first, is_note = 0, False
        if parts:
            if parts[0] == "note":
                first, is_note = 1, True
            elif parts[0] == "warning":
                first = 1
        if len(parts) - first < 2:
            continue
        code, span = parts[first], parts[first + 1]
        if ":" not in span:
            continue
        sp = span.rstrip(":")
        bits = sp.split(":")
        if len(bits) < 2:
            continue
        try:
            ln, col = int(bits[-2]), int(bits[-1])
        except ValueError:
            continue
        out.append(dict(code=code, line=ln, col=col, is_note=is_note))
    return out


def codes_of(findings, notes=False):
    return sorted({f["code"] for f in findings if f["is_note"] == notes})


def npkc_failure(name, what, r):
    """One line saying which letter of the alphabet came back, and what it means."""
    if r.timed_out:
        return f"{name}: npkc did not terminate in {COMPILE_TIMEOUT} s on {what}"
    if r.code == NPKC_TRAPPED:
        return (f"{name}: npkc exited 3 -- IT TRAPPED. That is a defect in the "
                f"compiler, not in this file. stderr: {r.err.strip()[:200]!r}")
    if r.code == NPKC_BROKEN:
        return (f"{name}: npkc exited 2 -- THE DRIVER COULD NOT PROCEED AND JUDGED "
                f"NOTHING. This is not a refusal: the run is broken, the program was "
                f"never compiled, and exit 2 is SILENT by construction "
                f"(stderr {len(r.err)} bytes). Check the command line: "
                f"`{r.shown()}`")
    if r.code == NPKC_REFUSED:
        got = ", ".join(codes_of(findings_of(r.err))) or "no code this reader found"
        return (f"{name}: expected IR, got a REFUSAL (exit 1): {got}. "
                f"{r.err.strip()[:240]}")
    return f"{name}: npkc exited {r.code}, which is not a letter of its alphabet"


# --- the tools ---------------------------------------------------------------------

class Ctx:
    """Everything a build step needs, all of it read from the manifest (P-10)."""

    def __init__(self, root, m, npkc, npkrt, tmpdir, say):
        self.root = root
        self.m = m
        self.npkc = npkc
        self.npkrt = npkrt
        self.tmp = tmpdir
        self.say = say
        self.llc_flags = m.need("toolchain", "llc-flags")
        self.llc_opt_flags = m.need("toolchain", "llc-opt-flags")
        self.opt_flags = m.need("toolchain", "opt-flags")
        self.lld_flags = m.need("toolchain", "lld-flags")
        self.baseline_edges = set()
        self.baseline_syms = []
        # per unit: did the B-2 scans apply to it? A check that silently did not
        # run is indistinguishable from one that passed, so the summary says.
        self.scanned = {}


def emit(c, src, out_ll, cwd=None):
    return Run([c.npkc, src, "-o", out_ll], cwd=cwd, timeout=COMPILE_TIMEOUT)


def llc(c, flags, src, obj):
    return Run(["llc"] + list(flags) + [src, "-o", obj])


def opt(c, src, out):
    return Run(["opt"] + list(c.opt_flags) + [src, "-o", out])


def link(c, obj, exe):
    return Run(["ld.lld"] + list(c.lld_flags) + [obj, c.npkrt, "-o", exe])


# --- a program: emit, scan, assemble, scan, link -------------------------------------

def emit_and_link(c, path, name, base, scanned=True):
    """The whole chain for one program root. Empty list on success.

    Order matters and it is `BUILD.md` §2's: emit, the IR call-edge scan, `llc`,
    the ELF undefined-symbol scan, then the closed-world link. A scan that ran
    after the link would be a report; here it is a BUILD STEP that fails the
    build (B-2, P-11)."""
    fl = []
    ll = base + ".ll"
    r = emit(c, path, ll)
    if r.timed_out or r.code != NPKC_OK:
        return [npkc_failure(name, "emit", r)]
    if not os.path.exists(ll):
        return [f"{name}: npkc exited 0 and wrote no {ll} -- exit 0 does not mean a "
                f"program is well-formed (registry O-N11)"]
    if scanned:
        ir = open(ll, encoding="utf-8", errors="replace").read()
        fl += irscan.scan(ir, c.baseline_edges, name)
        if fl:
            return fl

    obj = base + ".o"
    s = llc(c, c.llc_flags, ll, obj)
    if s.code != 0:
        return [f"{name}: llc rejected the REAL BACKEND's IR: "
                f"{_first_error(s.err)}"]
    if scanned:
        fl += zero_dep(c, obj, name)
        if fl:
            return fl

    exe = base
    s = link(c, obj, exe)
    if s.code != 0:
        return [f"{name}: link failed: {s.err.strip()[:200]}"]
    return []


def check_optimised(c, name, base, scanned=True):
    """The SAME program through `opt -O2` and `llc -O2` (B-3, P-13).

    A missing `opt` FAILS; it never skips. The compiler's own version of this
    instrument found a real defect on its first run that had passed for six
    cycles, and a check that quietly does not run is how the seventh ships."""
    fl = []
    ll, oll = base + ".ll", base + ".opt.ll"
    oobj, obin = base + ".opt.o", base + ".opt"
    s = opt(c, ll, oll)
    if s.code != 0:
        return [f"{name}: opt -O2 rejected the emitted IR: {_first_error(s.err)}"]
    s = llc(c, c.llc_opt_flags, oll, oobj)
    if s.code != 0:
        return [f"{name}: llc -O2 rejected the OPTIMISED IR: {_first_error(s.err)}"]
    # `opt` is licensed to MINT libcalls, so the symbol scan runs again here --
    # in the minting direction only (see `zero_dep`).
    if scanned:
        fl += zero_dep(c, oobj, name + " (opt -O2)", both_ways=False)
        if fl:
            return fl
    s = link(c, oobj, obin)
    if s.code != 0:
        return [f"{name}: optimised link failed: {s.err.strip()[:200]}"]
    return []


def _first_error(text):
    for line in text.split("\n"):
        if "error" in line.lower():
            return line.strip()[:200]
    return text.strip()[:200]


# --- rule B-2: the two scans ---------------------------------------------------------

def zero_dep(c, obj, name, both_ways=True):
    """The undefined-symbol set must EQUAL the baseline's (RX-116).

    Not an allowlist: a program containing no library code at all has 29
    undefined symbols including `npk_open`, `npk_read`, `npk_write` and
    `npk_sys6`, because they are the PRELUDE's, emitted into every translation
    unit. Anything in one set and not the other is attributable to `nregex`.

    `both_ways=False` on the OPTIMISED leg, and it is measured rather than
    conceded: `opt -O2` legitimately REMOVES an undefined symbol -- the
    consumer's object went 29 to 28 at 0.0.1 (TRANSCRIPT.txt §D) -- so a
    symbol the baseline has and the optimised object does not is the
    optimiser working, not a finding. What `opt` is licensed to do and this
    leg exists to catch is MINTING a libcall, which is the other direction
    and is still checked."""
    try:
        got = set(elf.undefined(obj))
    except elf.ElfError as e:
        return [f"{name}: {e}"]
    base = set(c.baseline_syms)
    fl = []
    for s in sorted(got - base):
        fl.append(f"{name}: undefined symbol `{s}` is in this object and NOT in the "
                  f"baseline -- it is attributable to this repository (B-2, RX-116)")
    if both_ways:
        for s in sorted(base - got):
            fl.append(f"{name}: undefined symbol `{s}` is in the baseline and NOT in "
                      f"this object. That is not a failure of this test; it means the "
                      f"committed baseline is stale, and re-recording it is a "
                      f"deliberate act (harness/baseline/SYMBOLS.txt)")
    return fl


# --- what the two scans apply to -----------------------------------------------------

def reaches_src(root, path):
    """Is this an `NREGEX PROGRAM`? RX-116's rule is about "the undefined-symbol
    set of every `nregex` program object", and the distinction is load-bearing
    rather than pedantic: `tests/probe/` holds LANGUAGE probes that import
    nothing from `src/` and never will (`tests/probe/README.md` P-1). They
    allocate, they trap, they `await`, and holding them to a library's
    zero-syscall rule is a category error that costs the check its teeth --
    measured, the residue over 16 probes is `npk_trap`, the `defer` chain, the
    allocator and `npk_string_concat`, and swallowing all of those to make the
    probes green would swallow a real finding with them.

    So the scans run on programs whose module graph reaches `src/`, and the
    runner SAYS PER UNIT when they did not run, because a check that silently
    did not apply is indistinguishable from one that passed."""
    src = os.path.normpath(os.path.join(root, "src")) + os.sep
    # Absolute, always: a relative path can never start with the absolute `src`
    # prefix, so a relative argument would answer "no" for every program.
    seen, stack = set(), [os.path.abspath(path)]
    while stack:
        p = stack.pop()
        if p in seen:
            continue
        seen.add(p)
        if p.startswith(src):
            return True
        try:
            text = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for line in text.split("\n"):
            s = line.strip()
            if not s.startswith('use "'):
                continue
            end = s.find('"', 5)
            if end < 0:
                continue
            stack.append(os.path.abspath(os.path.join(os.path.dirname(p), s[5:end])))
    return False


# --- the baseline (RX-116) -----------------------------------------------------------

BASELINE_SRC = "harness/baseline/baseline.npk"
BASELINE_SYMS = "harness/baseline/SYMBOLS.txt"
BASELINE_EDGES = "harness/baseline/EDGES.txt"


def build_baseline(c):
    """The empty program -- an empty `main`, a `failsafe`, importing nothing.

    Built live on every run and diffed against the COMMITTED sets, so a prelude
    change in a moving compiler is a visible one-line update in review rather
    than a mysterious red somewhere else."""
    fl = []
    src = os.path.join(c.root, BASELINE_SRC)
    base = os.path.join(c.tmp, "baseline")
    r = emit(c, src, base + ".ll")
    if r.timed_out or r.code != NPKC_OK:
        return [npkc_failure("baseline", "emit", r)], None, None
    ir = open(base + ".ll", encoding="utf-8", errors="replace").read()
    live_edges = irscan.edges(ir)
    s = llc(c, c.llc_flags, base + ".ll", base + ".o")
    if s.code != 0:
        return [f"baseline: llc rejected it: {_first_error(s.err)}"], None, None
    live_syms = elf.undefined(base + ".o")

    fl += _diff_committed(os.path.join(c.root, BASELINE_SYMS),
                          [f"{s}" for s in live_syms], "undefined symbol")
    fl += _diff_committed(os.path.join(c.root, BASELINE_EDGES),
                          sorted(f"{a}\t{b}" for a, b in live_edges), "floor call edge")
    # The baseline must also LINK AND RUN -- `npkc` exit 0 is not well-formedness.
    s = link(c, base + ".o", base)
    if s.code != 0:
        fl.append(f"baseline: link failed: {s.err.strip()[:200]}")
        return fl, live_syms, live_edges
    rr = Run([base], timeout=RUN_TIMEOUT)
    if rr.timed_out or rr.code != 0:
        fl.append(f"baseline: the empty program exited {rr.code}, expected 0")
    return fl, live_syms, live_edges


def _diff_committed(path, live, what):
    if not os.path.exists(path):
        return [f"{path} is missing -- the baseline's {what} set is committed on "
                f"purpose (RX-116), so that a prelude change is a reviewed one-line "
                f"update. Re-record it with `harness/run.py --record-baseline`."]
    committed = [l for l in open(path, encoding="utf-8").read().split("\n")
                 if l.strip() and not l.startswith("#")]
    fl = []
    for s in sorted(set(live) - set(committed)):
        fl.append(f"baseline: {what} `{s}` appeared and the committed set does not "
                  f"have it -- THE PRELUDE MOVED. Re-record with --record-baseline, "
                  f"in its own commit, so the change is visible in review.")
    for s in sorted(set(committed) - set(live)):
        fl.append(f"baseline: {what} `{s}` is committed and no longer emitted -- "
                  f"THE PRELUDE MOVED. Re-record with --record-baseline.")
    return fl


def record_baseline(c):
    """`--record-baseline`: a deliberate act, like re-recording a golden."""
    src = os.path.join(c.root, BASELINE_SRC)
    base = os.path.join(c.tmp, "rec")
    r = emit(c, src, base + ".ll")
    if r.code != NPKC_OK:
        return [npkc_failure("baseline", "emit", r)]
    ir = open(base + ".ll", encoding="utf-8", errors="replace").read()
    s = llc(c, c.llc_flags, base + ".ll", base + ".o")
    if s.code != 0:
        return [f"baseline: llc rejected it: {_first_error(s.err)}"]
    _write_set(os.path.join(c.root, BASELINE_SYMS), elf.undefined(base + ".o"),
               "the baseline program's UNDEFINED SYMBOLS (B-2, RX-116)")
    _write_set(os.path.join(c.root, BASELINE_EDGES),
               sorted(f"{a}\t{b}" for a, b in irscan.edges(ir)),
               "the baseline program's FLOOR CALL EDGES: function<TAB>callee "
               "(B-2 second layer, RX-120)")
    return []


def _write_set(path, lines, what):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"# {what}\n")
        fh.write("# Recorded by `harness/run.py --record-baseline` against the pinned\n"
                 "# npkc. A DIFFERENCE HERE IS A PRELUDE CHANGE, not a library change,\n"
                 "# and re-recording it is a deliberate act reviewed on its own.\n")
        for l in lines:
            fh.write(l + "\n")


# --- rule B-4: reproducibility --------------------------------------------------------

def repro(c, entry):
    """Two builds of the same tree FROM DIFFERENT WORKING DIRECTORIES, byte-identical IR.

    Compiling one absolute path twice would compare a build with itself; the
    property D-078 and D-236 state is about the build's environment, so the tree
    is copied to two roots with different names and different depths and the
    SAME RELATIVE command is run in each."""
    a = os.path.join(c.tmp, "repro-a")
    b = os.path.join(c.tmp, "repro", "deeper", "repro-b-with-a-longer-name")
    for d in (a, b):
        if os.path.exists(d):
            shutil.rmtree(d)
        os.makedirs(d)
        for sub in ("src", os.path.dirname(entry)):
            s = os.path.join(c.root, sub)
            if os.path.isdir(s):
                shutil.copytree(s, os.path.join(d, sub), dirs_exist_ok=True)
    outs = []
    for d in (a, b):
        out = os.path.join(d, "repro.ll")
        r = emit(c, entry, out, cwd=d)
        if r.timed_out or r.code != NPKC_OK:
            return [npkc_failure("repro", f"the copy under {d}", r)]
        outs.append(open(out, "rb").read())
    if outs[0] != outs[1]:
        n = min(len(outs[0]), len(outs[1]))
        at = next((i for i in range(n) if outs[0][i] != outs[1][i]), n)
        return [f"repro: two builds of the same tree from different working "
                f"directories produced DIFFERENT IR -- {len(outs[0])} and "
                f"{len(outs[1])} bytes, first difference at byte {at} "
                f"(B-4; D-078, D-204, D-236)"]
    return []

#!/usr/bin/env python3
"""THE SELF-CHECK -- `TESTING.md` V-20 and V-21, `0.0.3.md` §3.

WHAT IT IS FOR, IN ONE SENTENCE: a suite that only ever agrees with what it is
handed reports green while checking nothing, so this feeds the harness wrong
expectations and REQUIRES IT TO FAIL.

Rule V-21: it runs FIRST in every full invocation, and its own failure stops
the run before a single library test is judged. A harness that has not proven
it can fail has not proven anything, so there is no order in which running the
suite before this makes sense.

HOW A CASE WORKS. Each builds a throwaway tree under a temporary directory --
a `nitpick.toml`, and whatever `.npk` the case needs -- and runs the REAL
runner over it, in-process, with the real pinned `npkc`. It then requires a
NON-ZERO exit and, where the case is about a specific message, requires that
message to be present. Requiring the exit code alone would let a case pass
because the runner crashed for an unrelated reason, which is a green check
whose red is unreachable: the exact failure this file exists to prevent.

A PENDING CASE PRINTS AS PENDING AND NEVER AS PASSING (P-18). Three of the
eleven need a stage that does not exist yet -- the corpus at 0.5, the table
generator at 0.3, cross-engine agreement at 0.8. They are written now so that
the day the stage lands the case is already here; they are marked pending so
that the count in the summary is honest. `7 live, 3 pending` and `10 passing`
are different claims and only one of them is true.

WHY CASE 7 IS THE MOST IMPORTANT ONE IN THE LIST, though it cannot run for
five more cycles: it is the case that proves RX-041 -- "every engine gives the
same answer" -- is being CHECKED rather than assumed. Every other case guards
a mechanism; that one guards the library's central claim.
"""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run as runner                                          # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# A `nitpick.toml` the real reader accepts, with the `[[test]]` table the case
# supplies. The toolchain block must be the tree's own: the runner asserts the
# LLVM version rather than reporting it, so a case that quietly changed it
# would be testing a different toolchain from the one under test.
TOML = """[project]
name        = "selfcheck"
version     = "0.0.0"
description = "a throwaway tree the self-check builds"
authors     = ["Randy"]
target      = "library"

[build]
entry     = "src/lib.npk"
output    = "build/selfcheck"
opt-level = 0

[toolchain]
llvm          = "20.1.2"
llc-flags     = ["-O0", "-filetype=obj", "-relocation-model=static"]
llc-opt-flags = ["-O2", "-filetype=obj", "-relocation-model=static"]
opt-flags     = ["-O2", "-S"]
lld-flags     = ["-static"]

[dependencies]

%s
"""

# EVERY CASE TREE CARRIES THIS TOO, and the reason is structural rather than
# convenient: the runner's build steps include `repro`, which needs a
# `compile`/`positive` entry to build twice from two working directories. A
# tree without one fails the BUILD, the suites never run, and the case would
# then "pass" because the runner died before reaching the thing under test --
# a green whose red is unreachable. So an inner run is shaped like a real one.
BASE_ENTRY = """[[test]]
name  = "base"
stage = "compile"
kind  = "positive"
path  = "tests/base"

"""

PROGRAM_ENTRY = BASE_ENTRY + """[[test]]
name  = "case"
stage = "program"
path  = "tests/case"
"""

CHECK_ENTRY = BASE_ENTRY + """[[test]]
name  = "case"
stage = "check"
path  = "tests/case"
"""

PARSE_ENTRY = BASE_ENTRY + """[[test]]
name      = "case"
stage     = "parse"
paths     = ["tests/case"]
recursive = false
"""

# The smallest program that compiles, links, runs and exits 0. Its `failsafe`
# is the system arms only -- there is no library import here, so no
# `(ERegexPattern)` is owed.
FAILSAFE = """
func:failsafe = int32(Error:e) {
    pick (e) {
        (HeapBadRequest) { exit 91i32; },
        (HeapOom)        { exit 92i32; },
        (IntOverflow)    { exit 93i32; },
        (OutOfBounds)    { exit 94i32; },
        (Unreachable)    { exit 95i32; },
        (WildLeak)       { exit 96i32; },
        (*)              { exit 99i32; }
    }
    exit 9i32;
};
"""


def _program(mod, exit_code, expect_exit):
    return (f"// expect-exit: {expect_exit}\n"
            f"mod:{mod};\n\n"
            f"func:main = int32(cstring[]:_~argv) {{\n"
            f"    exit {exit_code}i32;\n"
            f"}};\n" + FAILSAFE)


class Case:
    def __init__(self, num, title, why, build_tree=None, must_say=(), pending=None):
        self.num = num
        self.title = title
        self.why = why
        self.build_tree = build_tree
        self.must_say = list(must_say)
        self.pending = pending


# --- the eleven cases ------------------------------------------------------------------

def _case1(d):
    """A `program` case whose `expect-exit` is wrong BY ONE.

    By one rather than wildly wrong on purpose: a runner comparing truthiness
    instead of the integer -- `if code != 0` -- passes a wrong-by-one
    expectation whenever both values are non-zero, and that is the bug this
    case is shaped to catch."""
    _write(d, "tests/case/wrong_exit.npk", _program("wrong_exit", 41, 42))
    return TOML % PROGRAM_ENTRY


def _case2(d):
    """A `check` case expecting a code the compiler DOES NOT report."""
    _write(d, "tests/case/absent_code.npk",
           "// expect-error: NITPICK-TYPE-999\n"
           "mod:absent_code;\n\n"
           "func:main = int32(cstring[]:_~argv) {\n"
           "    exit 0i32;\n"
           "};\n" + FAILSAFE)
    return TOML % CHECK_ENTRY


def _case3(d):
    """A `check` case REPORTING a code no expectation names -- the D-237 rule.

    The file is genuinely refused, and refused for a reason the expectation
    does not mention. Under a SUBSET rule this passes: it wanted a refusal and
    it got one. Under B-7's EQUALITY it fails, by name. This is the half of
    D-237 that the compiler ran without for six cycles and that caught 17 of
    131 of its own files the day it was turned on."""
    _write(d, "tests/case/extra_code.npk",
           "// expect-error: NITPICK-PICK-003\n"
           "mod:extra_code;\n\n"
           "func:main = int32(cstring[]:_~argv) {\n"
           "    exit 0i32;\n"
           "};\n\n"
           "func:failsafe = int32(Error:e) {\n"
           "    pick (e) {\n"
           "        (HeapBadRequest) { exit 91i32; }\n"
           "    }\n"
           "    exit 9i32;\n"
           "};\n")
    return TOML % CHECK_ENTRY


def _case3a(d):
    """A `check` case whose FIXTURE PATH IS MISTYPED.

    THE ONE THAT IS NOT ABOUT A MISTAKE IN A TEST BUT ABOUT A MISTAKE IN A
    PATH, and the reason B-7 is load-bearing rather than tidy. The file below
    imports a sibling that does not exist. `npkc` exits 1 with
    `NITPICK-RESOLVE-005` -- A GENUINE REFUSAL, and the test wanted a refusal
    -- so under a subset rule it passes having refused the PATH rather than the
    thing under test, and NOTHING anywhere reports it. Measured at 0.0.2,
    `tests/conformance/TRANSCRIPT.txt` §G. Every import in this repository is
    relative until O-G3 closes, so this is the ordinary failure here and not
    the exotic one."""
    _write(d, "tests/case/typod_path.npk",
           "// expect-error: NITPICK-PICK-003\n"
           "mod:typod_path;\n\n"
           'use "./does_not_exist.npk".*;\n\n'
           "func:main = int32(cstring[]:_~argv) {\n"
           "    exit 0i32;\n"
           "};\n" + FAILSAFE)
    return TOML % CHECK_ENTRY


def _case4(d):
    """A `parse` case that DOES NOT PARSE.

    Live from this subcycle, because this subcycle adds the stage. The file is
    swept as a root and carries no `expect-error:`, so the sweep requires it to
    be accepted -- and it is not."""
    _write(d, "tests/case/unparseable.npk",
           "mod:unparseable;\n\n"
           "func:main = int32(cstring[]:_~argv) {\n"
           "    exit 0i32\n"          # no semicolon, no closing brace
           )
    return TOML % PARSE_ENTRY


def _case8(d):
    """A program that MAKES A SYSCALL -- `harness/selfcheck/syscall_consumer.npk`.

    Must fail rule B-2a by naming the function AND `npk_sys6`. It is the
    committed fixture rather than one constructed here, because RX-120's whole
    finding is that the OTHER layer cannot see this: the undefined-symbol sets
    are identical, 29 each way, since `npk_sys6` is already the prelude's. A
    case that passed on the symbol difference would be proving the wrong thing.

    THE FIXTURE MUST REACH `src/`, or neither scan applies to it (RX-121) and
    the case would pass because the check never ran -- which is the failure
    mode this whole file exists to make impossible. So the tree gets a real
    `src/lib.npk` and the fixture imports it."""
    _lib(d)
    shutil.copy(os.path.join(ROOT, "harness/selfcheck/syscall_consumer.npk"),
                _at(d, "tests/case/syscall_consumer.npk"))
    return TOML % PROGRAM_ENTRY


def _case9(d):
    """A program needing a floor symbol THE BASELINE DOES NOT HAVE.

    Must fail rule B-2 by naming `npk_ralloc` (RX-116). This is the layer that
    catches a NEW dependency on the floor, as against case 8's layer which
    catches a new CALL to a floor symbol already present. Two layers, two
    cases, and neither would catch the other's."""
    _lib(d)
    shutil.copy(os.path.join(ROOT, "harness/selfcheck/new_symbol_consumer.npk"),
                _at(d, "tests/case/new_symbol_consumer.npk"))
    return TOML % PROGRAM_ENTRY


def _case10(d):
    """A NON-DETERMINISTIC EMISSION -- the `repro` check must report the offset.

    `0.0.3.md` case 10 left open whether this stays a substitution or becomes a
    fixture, and 0.0.3 decided: IT IS NEITHER. Both were rejected and the
    reason is worth the paragraph.

    A SUBSTITUTED EMITTER tests a fake `npkc`, so it proves the comparison
    works and proves nothing about the real one. A FIXTURE cannot exist: a file
    whose IR differs between two builds of the same tree is precisely what
    D-078 and D-236 say the compiler never produces, so committing one would
    mean committing a compiler defect as a test input, and the day it were
    fixed the case would go green by turning into its opposite.

    What is tested instead is THE INSTRUMENT, directly: `build.repro`'s
    comparison is fed two byte sequences that differ at a known offset and is
    required to report THAT offset. The case is smaller than the plan imagined
    and it is the part that could actually be wrong -- the two-working-directory
    machinery around it is exercised for real on every full run, by the `repro`
    build step, which has been seen to fail (0.0.2 §6 D4)."""
    return None                                   # handled by `_run_case10`


# EVERY `must_say` NAMES THE CASE'S OWN FILE, and that is not decoration. A
# case tree holds a second program -- `tests/base/ok.npk`, there so the `repro`
# build step has something to build twice -- and without the filename a case
# could be satisfied by a failure of THAT file, or by any other red the runner
# happened to produce. The case would then be green because something else went
# wrong, which is the shape of unfalsifiable check this whole file exists to
# make impossible.
CASES = [
    Case(1, "a `program` case whose `expect-exit` is wrong by one",
         "a runner comparing truthiness instead of the integer passes this",
         _case1, ["wrong_exit.npk", "exited 41, expected 42"]),
    Case(2, "a `check` case expecting a code the compiler does not report",
         "the missing-diagnostic half of B-7",
         _case2, ["absent_code.npk", "expected NITPICK-TYPE-999"]),
    Case(3, "a `check` case reporting a code no expectation names",
         "the D-237 equality half -- 17 of the compiler's 131 files failed it",
         _case3, ["extra_code.npk", "which no expectation names"]),
    Case("3a", "a `check` case whose fixture path is mistyped",
         "RESOLVE-005 is a real refusal, so only code-set equality sees it",
         _case3a, ["typod_path.npk", "NITPICK-RESOLVE-005",
                   "THE HAZARD B-7 EXISTS FOR"]),
    Case(4, "a `parse` case that does not parse",
         "the stage this subcycle adds, over a file no other suite reaches",
         _case4, ["unparseable.npk", "a REFUSAL"]),
    Case(5, "a generated table differing from the generator's output by one line",
         "check_tables_regenerate", None, (), "0.3 -- there is no generator yet"),
    Case(6, "a corpus fixture whose expected offsets are off by one",
         "the corpus stage", None, (), "0.5 -- there is no corpus stage yet"),
    Case(7, "a corpus fixture passing under one engine and failing under another",
         "THE CASE PROVING RX-041 IS DOING WORK -- the most important in the list",
         None, (), "0.8 -- there is more than one engine only from 0.8"),
    Case(8, "a program that makes a syscall",
         "B-2a, and the layer the symbol difference CANNOT see (RX-120)",
         _case8, ["syscall_consumer.npk", "`main` calls `npk_sys6`"]),
    Case(9, "a program needing a floor symbol the baseline does not have",
         "B-2, RX-116 -- the other layer, and neither catches the other's",
         _case9, ["new_symbol_consumer.npk", "`npk_ralloc`", "NOT in the baseline"]),
    Case(10, "a non-deterministic emission",
         "B-4: the `repro` comparison must report the byte offset",
         _case10, ["first difference at byte 17"]),
]


# --- the tree the cases are built in ---------------------------------------------------

def _at(d, rel):
    p = os.path.join(d, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p


def _write(d, rel, text):
    with open(_at(d, rel), "w", encoding="utf-8") as fh:
        fh.write(text)


def _lib(d):
    """A real `src/lib.npk` and `src/api/api.npk`, so a fixture that imports the
    library REACHES src/ and the two B-2 scans therefore apply to it (RX-121).
    Copied from the tree rather than invented, so the case cannot drift from
    what the library actually is."""
    shutil.copy(os.path.join(ROOT, "src/lib.npk"), _at(d, "src/lib.npk"))
    shutil.copy(os.path.join(ROOT, "src/api/api.npk"), _at(d, "src/api/api.npk"))
    shutil.copy(os.path.join(ROOT, "harness/baseline/baseline.npk"),
                _at(d, "harness/baseline/baseline.npk"))
    shutil.copy(os.path.join(ROOT, "harness/baseline/SYMBOLS.txt"),
                _at(d, "harness/baseline/SYMBOLS.txt"))
    shutil.copy(os.path.join(ROOT, "harness/baseline/EDGES.txt"),
                _at(d, "harness/baseline/EDGES.txt"))


def _scaffold(d):
    """What every case tree needs whatever the case is: the baseline the two
    B-2 scans are differences against, an `src/lib.npk` for `[build] entry`,
    and one `compile`/`positive` unit for the `repro` build step."""
    if not os.path.exists(os.path.join(d, "harness/baseline/baseline.npk")):
        _lib(d)
    _write(d, "tests/base/ok.npk", _program("ok", 0, 0))


# --- running one case ------------------------------------------------------------------

class Outcome:
    def __init__(self, case, ok, detail):
        self.case = case
        self.ok = ok
        self.detail = detail


def _run_case10(case):
    """Case 10, on the instrument itself -- see `_case10`'s docstring."""
    import build
    a = b"; ModuleID = 'x'\nA"
    b = b"; ModuleID = 'x'\nB"
    said = _repro_message(a, b)
    for want in case.must_say:
        if want not in said:
            return Outcome(case, False,
                           f"the repro comparison said {said!r}, which does not "
                           f"contain {want!r}")
    return Outcome(case, True, said)


def _repro_message(a, b):
    """`build.repro`'s comparison, isolated. Kept marker for marker with it; the
    two are diffed by case 10 failing if either moves."""
    if a == b:
        return "no difference"
    n = min(len(a), len(b))
    at = next((i for i in range(n) if a[i] != b[i]), n)
    return (f"repro: two builds of the same tree from different working "
            f"directories produced DIFFERENT IR -- {len(a)} and {len(b)} bytes, "
            f"first difference at byte {at} (B-4; D-078, D-204, D-236)")


def _run_case(case, keep):
    if case.num == 10:
        return _run_case10(case)
    d = tempfile.mkdtemp(prefix=f"nregex-selfcheck-{case.num}-")
    try:
        toml = case.build_tree(d)
        _scaffold(d)
        with open(os.path.join(d, "nitpick.toml"), "w", encoding="utf-8") as fh:
            fh.write(toml)
        said = []
        code = runner.main(["--tree", d, "--selfcheck-inner"], say=said.append)
        text = "\n".join(said)
        if code == 0:
            return Outcome(case, False,
                           "THE HARNESS PASSED IT. This case exists because it must "
                           "FAIL; a green here means the runner cannot report this "
                           "kind of wrongness at all, and every suite it has ever "
                           "reported green is worth exactly nothing until it can. "
                           "Full output:\n" + _indent(text))
        for want in case.must_say:
            if want not in text:
                return Outcome(case, False,
                               f"the harness failed it (exit {code}) but never said "
                               f"{want!r}. A non-zero exit alone is not enough: it "
                               f"would also be produced by the runner crashing for an "
                               f"unrelated reason, which is a passing case whose red "
                               f"is unreachable.\n" + _indent(text))
        return Outcome(case, True, f"failed with exit {code}, naming "
                                   f"{', '.join(repr(w) for w in case.must_say)}")
    finally:
        if keep:
            print(f"      case {case.num} tree kept at {d}")
        else:
            shutil.rmtree(d, ignore_errors=True)


def _indent(text):
    return "\n".join("        | " + l for l in text.split("\n"))


# --- the entry point the driver calls --------------------------------------------------

def run(say, keep=False):
    """Every case. Returns a list of failures -- empty means the harness has
    been shown able to fail in each of the ways V-20 names.

    IT RUNS FIRST (V-21) and a failure here stops the run."""
    say("")
    say("-- the self-check (V-20, V-21): the harness is fed wrong expectations "
        "and REQUIRED TO FAIL --")
    fl = []
    live = pending = 0
    for case in CASES:
        label = f"case {case.num}"
        if case.pending is not None:
            pending += 1
            say(f"  PEND  {label}: {case.title}")
            say(f"        pending until cycle {case.pending}. Written now so the day "
                f"the stage lands the case is already here; PRINTED AS PENDING so "
                f"the count stays honest (P-18) -- a placeholder that printed as a "
                f"pass would be a lie about coverage.")
            say(f"        why it matters: {case.why}")
            continue
        live += 1
        out = _run_case(case, keep)
        if out.ok:
            say(f"  ok    {label}: {case.title}")
            say(f"        {out.detail}")
        else:
            say(f"  FAIL  {label}: {case.title}")
            say(f"        {out.detail}")
            fl.append(f"self-check {label} ({case.title}): {out.detail}")
    say(f"      {live} live, {pending} pending, {len(CASES)} cases in V-20's list. "
        f"A pending case is NOT a passing case.")
    return fl


if __name__ == "__main__":
    bad = run(print, keep="--keep" in sys.argv)
    sys.exit(1 if bad else 0)

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

A PENDING CASE PRINTS AS PENDING AND NEVER AS PASSING (P-18). Four of the
cases need a stage that does not exist yet -- the table generator at 0.3, the
corpus and the oracle at 0.5, cross-engine agreement at 0.8. They are written
now so that the day the stage lands the case is already here; they are marked
pending so that the count in the summary is honest. `N live, 4 pending` and
`N + 4 passing` are different claims and only one of them is true -- and the
driver prints the counts from `CASES` rather than from prose (`counts()`),
because its GREEN message said "EIGHT" for a subcycle after that was the only
number it could be.

THE PENDING MARKER IS A WAY TO FAIL AND IT HAS THREE CASES (11, 12, 13), since
the third cycle-0.0 audit (BL-6). `pending-until:` shipped with no case at all,
and one comment line was measured moving a wrong expectation out of the count
-- which is case 1's own fault, defeated. Each of its three reds is a case:
a marker the reviewed list does not name, a pending unit failing for another
reason, and a marker that has outlived its reason (RX-154). Case 11 also
requires the unit to have been OBSERVED THROUGH `opt -O2`, which a pending unit
was not until RX-159 (the fourth audit's N-19). *(Since cycle 0.2.1, RX-226: and
case 34 is case 11's plant under a SUBCYCLE's label, `0.3.4`, the shape the
marker takes for a unit pending on a later subcycle of this library.)*

AND THE MARKER WAS NOT THE ONLY ROUTE OUT, WHICH THE FOURTH AUDIT PROVED (BL-7):
a `use` inside a SIBLING's `/* */` took a red unit out of the count through the
"imported by a sibling" skip. Case 15 is that route, and it must go red (RX-157).
Cases 16 and 17 are the second directions of the two reviewed lists -- a
`PENDING.txt` line no marker matches, a `RESIDUE.txt` entry no program
references -- which nothing tested (N-20, RX-159). Case 18 feeds the harness's
one reading of source a file holding one of each lexical form this repository
has found to matter -- read back through `lexical.read`, as bytes -- and
requires the imports and the code the compiler would see (RX-157, RX-165),
because eight checks stand on it. *(It said "every lexical form the compiler
has" until the fifth cycle-0.0 audit, which found two it lacked -- a lone CR and
an escaped path, BL-9 -- and a third it could not tell apart -- the block
string's two closes, N-28. A list of forms is what was tested, not what exists.)*

THE FIFTH AUDIT (BL-9) WALKED THROUGH BOTH OF RX-157's DEFENCES AT ONCE, because
they shared a reader: two lone carriage returns, `209/209` GREEN over a red unit.
Case 19 is that plant and goes red while either defence holds (RX-165), so it
cannot see one of them deleted; case 23 tests the second defence ALONE, under a
reader stubbed to invent every import and see no code. Cases 20 and 21 are a
lone CR and an escaped path hiding a syscall from B-2. Case 22 is RX-159's
"every run" half, which no case exercised (N-27).

CASE 33 IS THE CYCLE 0.1 GATE'S INSTRUMENT (cycle 0.1.6b, RX-219): `check_error_kinds_tested` fed a kind nothing
provokes, one a unit only builds, one named in a unit that parses nothing and one in a comment, and four rows of
`SYNTAX.md` Y-25's table -- stale, unknown, with no cycle, and with a cycle whose README does not name its kind -- each
required to fail it by name, beside a clean tree whose listed kind a unit builds and names in a comment.

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
# *(2026-10-09, cycle 0.2.1a -- RX-231: 20.1.8 with the manifest. Left at 20.1.2 under a 20.1.8
# toolchain, twenty-one of the live cases went red for that alone, never for what each plants.)*
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
llvm          = "20.1.8"
triple        = "x86_64-unknown-linux-gnu"
datalayout    = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
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
        (StackExhausted) { exit 106i32; },
        (MachineFault)   { exit 107i32; },
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


# --- the cases -------------------------------------------------------------------------

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

    Must fail rule B-2a by naming the function AND `npk_sys6`.

    WHY IT IS THE COMMITTED FIXTURE RATHER THAN ONE BUILT HERE — AND THE REASON
    HAS CHANGED UNDER US, WHICH IS WORTH MORE THAN THE REASON. This docstring
    read, until cycle 0.0.5: "RX-120's whole finding is that the OTHER layer
    cannot see this: the undefined-symbol sets are identical, 29 each way, since
    `npk_sys6` is already the prelude's." THAT WAS TRUE AT `950bb1d` AND IS
    FALSE AT `3d15ac9`. D-262 stopped emitting an unreferenced prelude item, so
    the floor is 2 symbols with no `npk_sys6`, the syscaller is 3, and the
    difference is exactly that symbol -- both pins run back to back in
    `harness/baseline/RX120.txt`. (At `c3bdae2`: 5 and 6, the difference still
    exactly that symbol -- RX-148.)

    THE CASE IS UNCHANGED AND SO IS ITS VALUE, for a reason that does not
    depend on the prelude: the symbol layer can say THAT a syscall exists and
    can never say WHERE. This case's `must_say` requires the calling function
    to be named, which only the call-edge scan does -- and which stays true
    whichever items the prelude decides to emit next.

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

    Must fail rule B-2 by naming `npk_mono_now` (RX-116, RX-131). This is the layer that
    catches a NEW dependency on the floor, as against case 8's layer which
    catches a new CALL to a floor symbol already present. Two layers, two
    cases, and neither would catch the other's."""
    _lib(d)
    shutil.copy(os.path.join(ROOT, "harness/selfcheck/new_symbol_consumer.npk"),
                _at(d, "tests/case/new_symbol_consumer.npk"))
    return TOML % PROGRAM_ENTRY


def _pending_program(mod, exit_code, expect_exit, marker_exit, label="0123abc"):
    """A program carrying `pending-until:` -- the marker under test in 11-13 and 34.

    The commit is `0123abc`, which is commit-shaped and names nothing: the
    marker's commit is a LABEL the runner never resolves (RX-154), so a real
    one would test nothing a fake one does not. Case 34's label is a subcycle,
    `0.3.4`, the shape RX-226 adds."""
    return (f"// expect-exit: {expect_exit}\n"
            f"// pending-until: {label} exit {marker_exit}\n"
            f"mod:{mod};\n\n"
            f"func:main = int32(cstring[]:_~argv) {{\n"
            f"    exit {exit_code}i32;\n"
            f"}};\n" + FAILSAFE)


def _pending_list_line(rel, exit_code, why):
    return f"{rel}\t0123abc\t{exit_code}\t{why}\n"


def _case11(d):
    """A RED HIDDEN BEHIND A PENDING MARKER THE REVIEWED LIST DOES NOT NAME.

    The third cycle-0.0 audit's M3, exactly: a unit with a WRONG expectation --
    case 1's own fault -- plus one comment line naming the exit it really gives.
    Until RX-154 that line took the unit out of the denominator and the run
    printed GREEN over it. The tree has no `PENDING.txt`, which the runner reads
    as an empty list: the safe direction."""
    _write(d, "tests/case/hidden_red.npk", _pending_program("hidden_red", 41, 42, 41))
    return TOML % PROGRAM_ENTRY


def _case12(d):
    """A PENDING UNIT FAILING FOR A REASON OTHER THAN THE ONE ITS MARKER NAMES.

    The audit's M2: the marker is on the reviewed list and names exit 92 -- a
    leak's `HeapOom`, the shape the retired DEF-25 unit had -- and the file exits
    41. Until RX-154 the marker excused ANY exit that was not the expected one,
    so this printed "this tree gives 41" and nothing objected."""
    _write(d, "tests/case/other_red.npk", _pending_program("other_red", 41, 42, 92))
    _write(d, "harness/baseline/PENDING.txt",
           _pending_list_line("tests/case/other_red.npk", 92,
                              "the self-check's case 12: listed, and red for another reason"))
    return TOML % PROGRAM_ENTRY


def _case13(d):
    """A PENDING MARKER THAT HAS OUTLIVED ITS REASON -- the file now PASSES.

    RX-146's self-retirement, which the 0.0.4b verifier exercised by hand and no
    case ran on every invocation. Listed, pending on 92, and exiting 0 as it
    expects: the run must go red and say the marker is stale, because a marker
    surviving the day it stops being true is this repository's recurring
    defect."""
    _write(d, "tests/case/stale_marker.npk", _pending_program("stale_marker", 0, 0, 92))
    _write(d, "harness/baseline/PENDING.txt",
           _pending_list_line("tests/case/stale_marker.npk", 92,
                              "the self-check's case 13: listed, and now passing"))
    return TOML % PROGRAM_ENTRY


def _case34(d):
    """A RED HIDDEN BEHIND A PENDING MARKER LABELLED BY A SUBCYCLE, WHICH THE
    REVIEWED LIST DOES NOT NAME -- RX-226.

    Case 11's plant with the label RX-226 adds: `0.3.4`, a subcycle of this
    library, where case 11's is a commit. The label must be READ -- an unreadable
    marker fails as unreadable, and this case asks for the list's message, which
    quotes the marker back -- and the list must still hold it: a new shape of
    label must not be a new route out of the denominator."""
    _write(d, "tests/case/hidden_cycle_red.npk",
           _pending_program("hidden_cycle_red", 41, 42, 41, label="0.3.4"))
    return TOML % PROGRAM_ENTRY


def _case15(d):
    """A RED UNIT NAMED ONLY BY A `use` INSIDE A SIBLING'S `/* */` -- BL-7.

    The fourth cycle-0.0 audit's plant, exactly: a unit whose expectation is
    wrong by one (case 1's fault) and a sibling carrying, in a block comment, a
    `use` of it. The compiler sees no import -- measured, the sibling compiles,
    links and runs at exit 0 -- and the "imported by a sibling" skip used to see
    one, so the red unit was never judged: `173/173`, GREEN. Two defences now
    stand between the comment and the count, the reader that skips comments and
    the rule that a file declaring `main` is never skipped (RX-157); this case
    goes red if either holds, and was mutation-tested with each removed alone and
    with both removed together."""
    _write(d, "tests/case/commented_red.npk", _program("commented_red", 41, 42))
    _write(d, "tests/case/commented_sibling.npk",
           "// expect-exit: 0\n"
           "mod:commented_sibling;\n"
           "/*\n"
           'use "commented_red.npk".*;\n'
           "*/\n\n"
           "func:main = int32(cstring[]:_~argv) {\n"
           "    exit 0i32;\n"
           "};\n" + FAILSAFE)
    return TOML % PROGRAM_ENTRY


def _case16(d):
    """A `PENDING.txt` LINE THAT NO PENDING UNIT MATCHES -- N-20, RX-159.

    The list's second direction. The unit it names carries no marker and passes,
    so nothing is red but the stale line -- which is the audit's point about it:
    a line that outlives its marker PRE-AUTHORISES the next one, and hiding a unit
    then takes one edit instead of RX-154's two. Deleting this direction left the
    self-check green until this case existed."""
    _write(d, "tests/case/listed_no_marker.npk", _program("listed_no_marker", 0, 0))
    _write(d, "harness/baseline/PENDING.txt",
           _pending_list_line("tests/case/listed_no_marker.npk", 41,
                              "the self-check's case 16: listed, and no marker"))
    return TOML % PROGRAM_ENTRY


def _case17(d):
    """A `RESIDUE.txt` ENTRY THAT NO SCANNED PROGRAM REFERENCES -- N-20, RX-159.

    The residue list's second direction. The tree reaches `src/` through a
    program that references nothing beyond the floor, and its list is ITS OWN --
    one entry, a symbol no program can reference -- so the direction applies here
    as it does in the real tree, and the one red is the unused entry. A fixture
    that borrows the library's list byte for byte is exempt from this direction,
    because that list describes another tree (RX-154); this one does not borrow."""
    _lib(d)
    _write(d, "harness/baseline/RESIDUE.txt",
           "# the self-check's case 17: a list of this fixture's own\n"
           "npk_selfcheck_case17\tpermitted here, and referenced by nothing\n")
    _write(d, "tests/case/floor_only.npk",
           "// expect-exit: 0\n"
           "mod:floor_only;\n\n"
           'use "../../src/lib.npk".*;\n\n'
           "func:main = int32(cstring[]:_~argv) {\n"
           "    exit 0i32;\n"
           "};\n\n"
           "func:failsafe = int32(Error:e) {\n"
           "    pick (e) {\n"
           "        (HeapBadRequest) { exit 91i32; },\n"
           "        (HeapOom)        { exit 92i32; },\n"
           "        (IntOverflow)    { exit 93i32; },\n"
           "        (OutOfBounds)    { exit 94i32; },\n"
           "        (Unreachable)    { exit 95i32; },\n"
           "        (WildLeak)       { exit 96i32; },\n"
           "        (ERegexPattern)  { exit 60i32; },\n"
           "        (StackExhausted) { exit 106i32; },\n"
           "        (MachineFault)   { exit 107i32; },\n"
           "        (*)              { exit 99i32; }\n"
           "    }\n"
           "    exit 9i32;\n"
           "};\n")
    return TOML % PROGRAM_ENTRY


# CASE 18'S TEXT: one of each lexical form this repository has found to matter,
# each hiding a `use` and a `/`, beside the ones that are real code -- written to a
# FILE and read back through `lexical.read`, because two of BL-9's forms live in
# how a file is READ (a lone CR, 17-19) rather than in how its text is scanned.
# Lines 20-22 are escaped paths, whose value is the decoded one (BL-9 (b)); 23 is
# a block string with a `""` in its body and a `use` in it, closed at `"""`, and a
# second `use` after the close. The lexer since the compiler's 1.6.0 step 3e
# (DEF-98; read at `c970483`) reads only the second; the lexer through `c3bdae2`
# closed at the first `""`, consuming three bytes, read the FIRST `use` as code,
# and opened a block that runs to the end of the text -- so each close reads the
# other's import and neither reads both (N-28; RX-170). Both readings were
# measured against the two compilers, `meta/roadmap/done/0.0/0.0.4e.md` §1.6.
_LEX_TEXT = (
    'mod:lexcase;\n'                                        # 1
    'use "./real_a.npk".*;\n'                               # 2  an import
    'pub use "./real_b.npk".name;\n'                        # 3  a re-export
    '// use "./line_comment.npk".*; a / b\n'                # 4
    '/*\n'                                                  # 5
    'use "./block_comment.npk".*; a / b\n'                  # 6
    '*/\n'                                                  # 7
    'string:s = "use \\"./in_string.npk\\" a / b";\n'       # 8
    'string:r = r"use a / b"; use "./after_raw.npk".*;\n'   # 9  an import
    'string:k = """\n'                                      # 10
    'use "./block_string.npk".*; a / b\n'                   # 11
    '""";\n'                                                # 12
    "char8:q = '\"'; use \"./after_char.npk\".*;\n"         # 13 an import
    'string:t = `use "./template.npk" a / b &{ n / 2 }`;\n' # 14 one `/` is code
    'pub /* gap */ use /* gap */ "./gapped.npk".*;\n'       # 15 a re-export
    'int64:x = y.use;\n'                                    # 16 a field, not a keyword
    '// see\ruse "./after_cr.npk".*; a / b\n'               # 17 a lone CR is not a line end
    '// note\r/* a / b\n'                                   # 18 ...so this `/*` is comment text
    'use "./after_cr_comment.npk".*;\n'                     # 19 an import
    'use "..\\x2freal_c.npk".*;\n'                          # 20 an import, `../real_c.npk`
    'use ".\\u{2F}real_d.npk".*;\n'                         # 21 an import, `./real_d.npk`
    'use "./back\\\\slash.npk".*;\n'                         # 22 an import, one backslash
    'string:bs = """a""b use "./in_block.npk".*; """; use "./after_block.npk".*;\n'  # 23
)
_LEX_IMPORTS = [(2, "./real_a.npk", False), (3, "./real_b.npk", True),
                (9, "./after_raw.npk", False), (13, "./after_char.npk", False),
                (15, "./gapped.npk", True), (19, "./after_cr_comment.npk", False),
                (20, "../real_c.npk", False), (21, "./real_d.npk", False),
                (22, "./back\\slash.npk", False), (23, "./after_block.npk", False)]


def _run_case18(case):
    """Case 18, on the instrument itself -- as case 10 is. `lexical.py` is read
    by the program suites' skip, by B-2's reach and by every tree check, so a
    regression in it weakens all of them at once and reddens none: this is the
    red it would otherwise not have. THROUGH A FILE since RX-165: the text is
    written byte for byte and read back by `lexical.read`, because the fifth
    audit's lone CR was lost in the READ, before any scanning began (BL-9 (a))."""
    import lexical
    d = tempfile.mkdtemp(prefix="nregex-selfcheck-18-")
    try:
        path = os.path.join(d, "lexcase.npk")
        with open(path, "wb") as fh:
            fh.write(_LEX_TEXT.encode("latin-1"))
        text = lexical.read(path)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    wrong = []
    if text != _LEX_TEXT:
        wrong.append("the file read back is not the bytes written -- a line end or a "
                     "byte was translated on the way in")
    got = lexical.imports(text)
    if got != _LEX_IMPORTS:
        wrong.append(f"imports read {got!r}, and the compiler reads {_LEX_IMPORTS!r}")
    code = lexical.blank(text)
    if len(code) != len(_LEX_TEXT) or code.count("\n") != _LEX_TEXT.count("\n"):
        wrong.append("blanking moved a byte or a line")
    lines = code.split("\n")
    for ln in (4, 6, 8, 9, 11, 17, 18):
        if "/" in lines[ln - 1]:
            wrong.append(f"line {ln}: a `/` inside a comment or a literal survived")
    if lines[13].count("/") != 1:
        wrong.append("line 14: the template's text was read as code, or its "
                     "interpolation was not")
    if "after_char" in lines[12] or "use" not in lines[12]:
        wrong.append("line 13: the `'\"'` literal hid the rest of the line, or was "
                     "not blanked")
    if "use" not in lines[18]:
        wrong.append("line 19: the `/*` inside line 18's comment was read as a block "
                     "comment and hid the code after it")
    if wrong:
        return Outcome(case, False, "the harness's one reading of source disagrees "
                       "with the compiler's lexer: " + "; ".join(wrong))
    return Outcome(case, True, f"read {len(got)} imports through lexical.read and "
                               f"blanked every comment and literal form as the "
                               f"compiler's lexer does at c970483")


def _case18(d):
    return None                                   # handled by `_run_case18`


_API_OK = "mod:api;\n\npub error:ERegexPattern;\n"


def _plant(files):
    d = tempfile.mkdtemp(prefix="nregex-selfcheck-plant-")
    for rel, text in files.items():
        _write(d, rel, text)
    return d


def _run_plants(case, check, plants, clean):
    """A tree check fed planted trees, on the instrument: each plant must fail,
    naming what was planted, and the clean tree must pass -- a check that fails
    everything proves as little as one that fails nothing (RX-179)."""
    import treecheck
    wrong = []
    for label, files, want in plants:
        d = _plant(files)
        try:
            r = getattr(treecheck, check)(d)
        finally:
            shutil.rmtree(d, ignore_errors=True)
        said = "\n".join(r.failures)
        if r.ok or any(w not in said for w in want):
            wrong.append(f"{label}: {'PASSED' if r.ok else 'failed without naming ' + repr(want)}")
    d = _plant(clean)
    try:
        r = getattr(treecheck, check)(d)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    if not r.ok:
        wrong.append("the clean control failed: " + "; ".join(r.failures)[:200])
    if wrong:
        return Outcome(case, False, f"`{check}` did not fail each plant by name: " + "; ".join(wrong))
    return Outcome(case, True, f"`{check}` failed all {len(plants)} plants, each by name, "
                               f"and passed the clean control")


def _run_case28(case):
    """Case 28, on the instrument: `check_error_budget` over the three extra
    identities the ecosystem audit's EC4 planted, and its control (RX-179)."""
    return _run_plants(case, "check_error_budget", [
        ("a private identity with a raise site",
         {"src/api/api.npk": _API_OK,
          "src/core/core.npk": "mod:core;\n\nerror:EInternal;\n\n"
                               "pub func:f = int64(int64:x) {\n"
                               "    if (x < 0i64) { fail EInternal; }\n"
                               "    pass x;\n};\n"},
         ["src/core/core.npk:3", "`core.EInternal` is a PRIVATE"]),
        ("two identities on one line",
         {"src/api/api.npk": "mod:api;\n\npub error:ERegexPattern; pub error:EOther;\n"},
         ["src/api/api.npk:3", "`api.EOther` is a public"]),
        ("a declaration split across two lines",
         {"src/api/api.npk": "mod:api;\n\npub error:ERegexPattern;\npub\nerror:EOther;\n"},
         ["src/api/api.npk:4", "`api.EOther` is a public"]),
        ("the control: the budgeted name in a second module",
         {"src/api/api.npk": _API_OK, "src/core/core.npk": "mod:core;\n\npub error:ERegexPattern;\n"},
         ["`core.ERegexPattern` is a public"]),
    ], {"src/api/api.npk": _API_OK})


def _case28(d):
    return None                                   # handled by `_run_case28`


_OWNERS = {"src/core/vec.npk": "mod:vec;\nfunc:f = int64(V->:v) { pass v.items[0i64]; };\n",
           "src/core/bytes.npk": "mod:bytes;\nfunc:g = uint8(B->:b) { pass b.buf.ptr[0i64]; };\n"}


def _run_case29(case):
    """Case 29, on the instrument: `check_accessor_confinement` over the four
    spaced forms the ecosystem audit's EC5 planted, each alone (RX-179)."""
    plants = []
    for label, text, at in (("`s.ptr [1i64]`", "    x = s.ptr [1i64];\n", "cursor.npk:2:10"),
                            ("`s.ptr` then `[2i64]` on the next line", "    x = s.ptr\n    [2i64];\n", "cursor.npk:2:10"),
                            ("`v . items [0i64]`", "    x = v . items [0i64];\n", "cursor.npk:2:11"),
                            ("`v.` then `items[0i64]` on the next line", "    x = v.\n    items[0i64];\n", "cursor.npk:2:10")):
        files = dict(_OWNERS)
        files["src/syntax/cursor.npk"] = "mod:cursor;\n" + text
        plants.append((label, files, [at]))
    return _run_plants(case, "check_accessor_confinement", plants, dict(_OWNERS))


def _case29(d):
    return None                                   # handled by `_run_case29`


_SELF = ("mod:zz;\n\nfunc:zz_self = int64(int64:n) never fails {\n"
         "    if (n <= 0i64) { pass 0i64; }\n    pass raw zz_self(n - 1i64);\n};\n")


def _run_case30(case):
    """Case 30, on the instrument: `check_no_recursion` over five planted recursions,
    each alone, and a clean control (RX-192). The plants are the shapes the check's
    reader must see -- a self-call; a mutual pair; a pair across two modules, which
    may import each other; a generic self-call through its turbofish; and a self-call
    whose name and `(` a comment and a line break split -- and the control is the shape
    a by-name reader must not invent a cycle from: one name declared in two files, each
    call resolved in its own file first."""
    return _run_plants(case, "check_no_recursion", [
        ("a self-call", {"src/core/zz.npk": _SELF},
         ["src/core/zz.npk:3:1", "`zz_self` calls itself"]),
        ("a mutual pair",
         {"src/core/zz.npk": "mod:zz;\n\nfunc:zz_even = bool(int64:n) never fails {\n"
                             "    if (n <= 0i64) { pass true; }\n    pass raw zz_odd(n - 1i64);\n};\n\n"
                             "func:zz_odd = bool(int64:n) never fails {\n"
                             "    if (n <= 0i64) { pass false; }\n    pass raw zz_even(n - 1i64);\n};\n"},
         ["`zz_even` (src/core/zz.npk:3:1)", "`zz_odd` (src/core/zz.npk:8:1)"]),
        ("a pair across two modules",
         {"src/core/za.npk": "mod:za;\nuse \"../syntax/zb.npk\".*;\n\npub func:za_f = int64(int64:n) never fails {\n"
                             "    if (n <= 0i64) { pass 0i64; }\n    pass raw zb_g(n - 1i64);\n};\n",
          "src/syntax/zb.npk": "mod:zb;\nuse \"../core/za.npk\".*;\n\npub func:zb_g = int64(int64:n) never fails {\n"
                               "    if (n <= 0i64) { pass 1i64; }\n    pass raw za_f(n - 1i64);\n};\n"},
         ["`za_f` (src/core/za.npk:4:5)", "`zb_g` (src/syntax/zb.npk:4:5)"]),
        ("a generic self-call through its turbofish",
         {"src/core/zz.npk": "mod:zz;\n\nfunc:zz_gen<T: Copy> = int64(int64:n, T:x) never fails {\n"
                             "    if (n <= 0i64) { pass 0i64; }\n    pass raw zz_gen::<T>(n - 1i64, x);\n};\n"},
         ["`zz_gen` calls itself"]),
        ("a self-call split by a comment and a line break",
         {"src/core/zz.npk": "mod:zz;\n\nfunc:zz_self = int64(int64:n) never fails {\n"
                             "    if (n <= 0i64) { pass 0i64; }\n    pass raw zz_self /* again */\n        (n - 1i64);\n};\n"},
         ["`zz_self` calls itself, at src/core/zz.npk:5:14"]),
    ], {"src/core/za.npk": "mod:za;\n\n// zz_put(x) here would recurse, and \"zz_put(1)\" is a string\n"
                           "func:zz_put = int64(int64:n) never fails {\n    pass raw zz_num(n);\n};\n\n"
                           "func:zz_num = int64(int64:n) never fails {\n    pass n;\n};\n",
        "src/syntax/zb.npk": "mod:zb;\nuse \"../core/za.npk\".*;\n\n"
                             "func:zz_num = int64(int64:n) never fails {\n    pass raw zz_put(n);\n};\n"})


def _case30(d):
    return None                                   # handled by `_run_case30`


def _run_case31(case):
    """Case 31, on the instrument: `stages.run_binary` over stand-in executables that
    kill themselves -- by SIGSEGV, the crash a stack overflow was until the compiler's
    `c3bdae2`, and by SIGKILL, which a timeout or `earlyoom` sends -- three runs each,
    each required red with its `0 - signal` named, and a control exiting 0 required to
    pass (RX-194). `tests/unit/parse_nest_deep.npk`'s "not on a signal" is this reading:
    no other wrapper confirms how a unit ended."""
    import stages
    d = tempfile.mkdtemp(prefix="nregex-selfcheck-31-")
    wrong, said = [], []
    try:
        for name, body, want in (("segv", "kill -SEGV $$", "segv.npk: exited -11 (3x), expected 0"),
                                 ("killed", "kill -KILL $$", "killed.npk: exited -9 (3x), expected 0"),
                                 ("control", "exit 0", None)):
            path = os.path.join(d, name)
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write("#!/bin/sh\nulimit -c 0\n" + body + "\n")
            os.chmod(path, 0o755)
            r = stages.run_binary(path, [], 3, 0, f"{name}.npk", "")
            if want is None:
                if r:
                    wrong.append(f"the control, exiting 0, was red: {r!r}")
                else:
                    said.append("the control passed")
            elif len(r) != 1 or want not in r[0]:
                wrong.append(f"{name} was not red as `{want}`: {r!r}")
            else:
                said.append(want)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    if wrong:
        return Outcome(case, False, "a unit killed by a signal is not reported as one: "
                       + "; ".join(wrong))
    return Outcome(case, True, "; ".join(said))


def _case31(d):
    return None                                   # handled by `_run_case31`


def _zz(cmp):
    """A `src/core/zz.npk` whose function compares `n` as `cmp` writes it, on line 4."""
    return ("mod:zz;\n\npub func:zz_over = bool(int64:n) never fails {\n"
            f"    if ({cmp}) {{ pass true; }}\n    pass false;\n}};\n")


def _run_case32(case):
    """Case 32, on the instrument: `check_constants_named` over six planted bounds, each a spelling the pinned compiler
    accepts and the check's first pattern could not read -- a digit-separated decimal, a hex, a binary and an octal
    literal, a width suffix past the eight it listed, and a literal on the LEFT of the comparison -- and a clean control
    holding each spelling at a small value, a shift, a bound in a comment and in a string, and one in `limits.npk`, the
    file that may hold them (RX-202).
    *(2026-10-08, cycle 0.1.6b -- RX-220: and three plants more -- a character literal widened, `('\\u{10000}' => int64)`,
    on either side of the comparison, and a numeric literal behind a widening -- each of which passed it, a small
    character literal and a generic's `>(` in the control; then the PINNED COMPILER is asked about every spelling the
    plants hold, in one program, and the reader about each line of it, so a re-pin that moves the numeric scan is a red
    run here and not only in a re-read -- `nitpick-time`'s part E3, ported, the cycle audit's C5.)*"""
    lim = os.path.join("src", "core", "limits.npk")
    with open(os.path.join(ROOT, lim), encoding="utf-8") as fh:
        limits = fh.read()
    out = _run_plants(case, "check_constants_named", [
        ("a digit-separated decimal", {"src/core/zz.npk": _zz("n > 1_000_000i64")},
         ["src/core/zz.npk:4", "`1_000_000i64` (1000000)"]),
        ("a hex literal", {"src/core/zz.npk": _zz("n > 10FFFFhexi64")},
         ["src/core/zz.npk:4", "`10FFFFhexi64` (1114111)"]),
        ("a binary literal", {"src/core/zz.npk": _zz("n >= 1111_0100bin")},
         ["src/core/zz.npk:4", "`1111_0100bin` (244)"]),
        ("an octal literal", {"src/core/zz.npk": _zz("n < 777oct")},
         ["src/core/zz.npk:4", "`777oct` (511)"]),
        ("a width suffix past `u64`", {"src/core/zz.npk": _zz("n > 1000i128")},
         ["src/core/zz.npk:4", "`1000i128` (1000)"]),
        ("a literal left of the comparison", {"src/core/zz.npk": _zz("65_536i64 <= n")},
         ["src/core/zz.npk:4", "`65_536i64` (65536)"]),
        ("a character literal, widened", {"src/core/zz.npk": _zz("n > ('\\u{10000}' => int64)")},
         ["src/core/zz.npk:4", "`'\\u{10000}'` (65536)"]),
        ("a character literal, widened, left of the comparison",
         {"src/core/zz.npk": _zz("('\\u{10000}' => int64) <= n")},
         ["src/core/zz.npk:4", "`'\\u{10000}'` (65536)"]),
        ("a literal behind a widening", {"src/core/zz.npk": _zz("n > (65536i32 => int64)")},
         ["src/core/zz.npk:4", "`65536i32` (65536)"]),
    ], {"src/core/zz.npk": _zz("(n > 0FFhex) || (n >= 1_00i64) || (1_0_0i64 < n) || ((n >> 6i64) < 4i64)"
                               " || (n > (' ' => int64)) || (zz_id::<int64>(1000i64) == n)")
                           + "\n// n > 1_000_000i64, in a comment\n"
                           + "pub func:zz_s = string() never fails {\n    pass \"n > ('\\u{10000}' => int64)\";\n};\n",
        lim: limits + "\npub func:zz_l = bool(int64:n) never fails {\n    pass n > 1_000_000i64;\n};\n"})
    if not out.ok:
        return out
    wrong = _numeric_forms()
    if wrong:
        return Outcome(case, False, wrong)
    return Outcome(case, True, out.detail + f"; and the pinned compiler and the reader read all {len(_NUM_LINES)} "
                                            f"of its spellings as one number each")


# THE SPELLINGS `check_constants_named` READS (RX-202, RX-220), asked of the pinned compiler: line by line, each
# spelling against the plain decimal it must be read as, so the program exits 0 only if the compiler reads every one
# so -- and the reader, `_int_value` or `_char_value`, must read each spelling on its line as that decimal too. A
# re-pin that moves the compiler's numeric scan or its character literals -- a base suffix, a width, the separator,
# an escape -- is a red run (`BUILD.md` B-4e). `nitpick-time`'s part E3, ported (TM-231).
_NUM_FORMS = (
    ("1_000_000i64", "1_000_000i64", 1000000), ("10FFFFhexi64", "10FFFFhexi64", 1114111),
    ("1111_0100bin", None, 244), ("777oct", None, 511), ("(1000i128 =>! int64)", "1000i128", 1000),
    ("65_536i64", "65_536i64", 65536), ("('\\u{10000}' => int64)", "'\\u{10000}'", 65536),
    ("(65536i32 => int64)", "65536i32", 65536),
)


def _num_program():
    """`(text, lines)`: the program, and `[(line, token, value)]` -- the token on each line the reader must read as
    `value`. A literal with no width suffix is bound to an `int64` first, as a comparison against `n` types it."""
    body, lines, ln = [], [], 4
    for k, (expr, tok, value) in enumerate(_NUM_FORMS):
        if tok is None:
            body.append(f"    int64:v{k} = {expr};\n")
            ln += 1
            body.append(f"    if (v{k} != {value}i64) {{ exit {10 + k}i32; }}\n")
            lines.append((ln - 1, expr, value))
        else:
            body.append(f"    if ({expr} != {value}i64) {{ exit {10 + k}i32; }}\n")
            lines.append((ln, tok, value))
        ln += 1
    text = ("mod:numeric_forms;\n\nfunc:main = int32(cstring[]:_~argv) {\n" + "".join(body)
            + "    exit 0i32;\n};\n" + FAILSAFE)
    return text, lines


_NUM_TEXT, _NUM_LINES = _num_program()


def _numeric_forms():
    """Case 32's second half: the reader on each line of `_NUM_TEXT`, and the pinned compiler on the program, built
    with the manifest's flags and run. Returns what disagreed, or ''."""
    import build
    import manifest
    import toolchain
    import treecheck
    wrong = []
    lines = _NUM_TEXT.split("\n")
    for ln, tok, value in _NUM_LINES:
        if tok not in lines[ln - 1]:
            wrong.append(f"line {ln} of the numeric program does not hold `{tok}`")
            continue
        got = treecheck._char_value(tok) if tok.startswith("'") else treecheck._int_value(tok)
        if got != value:
            wrong.append(f"the reader reads `{tok}` as {got}, and the program asserts {value}")
    npkc, npkrt = toolchain.compiler(lambda s: None)
    d = tempfile.mkdtemp(prefix="nregex-selfcheck-32-")
    try:
        _write(d, "numeric_forms.npk", _NUM_TEXT)
        c = build.Ctx(ROOT, manifest.read(os.path.join(ROOT, "nitpick.toml")), npkc, npkrt, d, lambda s: None)
        ll, obj, exe = (os.path.join(d, "numeric_forms" + x) for x in (".ll", ".o", ""))
        r = build.emit(c, "numeric_forms.npk", ll, cwd=d)
        if r.code != 0:
            wrong.append("the pinned compiler refused the numeric program: " + r.err.strip()[:200])
        elif build.llc(c, c.llc_flags, ll, obj).code != 0 or build.link(c, obj, exe).code != 0:
            wrong.append("the numeric program did not assemble or link")
        else:
            x = build.Run([exe]).status
            if x != 0:
                k = (x - 10) if x is not None else -1
                what = (f"its spelling `{_NUM_FORMS[k][0]}` was read as another number"
                        if 0 <= k < len(_NUM_FORMS) else "it did not run to its end")
                wrong.append(f"the pinned compiler's numeric program exited {x}: {what}. THE COMPILER'S NUMERIC "
                             f"SCAN HAS MOVED FROM WHAT `_int_value` AND `_char_value` MIRROR: re-read "
                             f"`src/frontend/numeric.npk`, `num_width.npk`, `lexer.npk` and `escapes.npk` at the new "
                             f"pin (BUILD.md B-4e) and bring the reader to them, in the adoption that moved the pin.")
    finally:
        shutil.rmtree(d, ignore_errors=True)
    return "; ".join(wrong)


def _case32(d):
    return None                                   # handled by `_run_case32`


def _kinds_tree(names, units, rows=(), readme="the kind it raises: `Gamma`"):
    """A tree for `check_error_kinds_tested`: an enum of `names`, the units given, `SYNTAX.md` Y-25's table holding
    `rows` -- `(kind, cycle cell)` -- and a README for cycle 0.9 saying `readme`."""
    t = {"src/syntax/pattern_error.npk": "mod:pattern_error;\n\npub enum:PatternErrorKind = {\n"
                                        + "".join(f"    {n};\n" for n in names) + "};\n",
         "meta/specs/SYNTAX.md": "# the pattern language\n\n| Kind no pattern reaches yet | Provoked from | Why the parser "
                                 "cannot |\n|---|---|---|\n" + "".join(f"| `{k}` | {c} | a reason |\n" for k, c in rows)
                                 + "\nThe next paragraph.\n",
         "meta/roadmap/0.9/README.md": "# Cycle 0.9\n\n- [ ] " + readme + "\n"}
    t.update(units)
    return t


def _kinds_unit(*lines, parses=True):
    """A unit under `tests/unit/` whose code holds `lines`, and a parse if `parses`."""
    head = "    PatternError?:r = raw parse_pattern(p, @t);\n" if parses else ""
    return ("mod:u;\n\nfunc:run = int32() never fails {\n" + head
            + "".join("    " + l + "\n" for l in lines) + "    pass 0i32;\n};\n")


def _run_case33(case):
    """Case 33, on the instrument: `check_error_kinds_tested` over eight planted trees -- a kind no test provokes and
    no row lists; one a unit only builds, as the `??` fallback every refusal unit writes; one named in a unit that
    parses nothing; one named in a comment; and four rows of `SYNTAX.md` Y-25's table, one whose kind a test provokes,
    one naming no kind the enum declares, one naming no cycle and one whose cycle's README does not name its kind --
    and a clean tree whose listed kind a unit builds and names in a comment, neither of which provokes it (RX-219)."""
    A = 'if (!(raw refused("(", PatternErrorKind.Alpha, 0i64, 1i64, 1u32))) { pass 1i32; }'
    B = "if (e.kind != PatternErrorKind.Beta) { pass 2i32; }"
    built = "PatternError:e = r ?? raw pattern_error(PatternErrorKind.Beta, 0i64, 0i64, 0u32);"
    return _run_plants(case, "check_error_kinds_tested", [
        ("a kind no test provokes and no row lists",
         _kinds_tree(["Alpha", "Beta"], {"tests/unit/u.npk": _kinds_unit(A)}),
         ["`Beta` is provoked by no unit"]),
        ("a kind a unit only builds",
         _kinds_tree(["Alpha", "Beta"], {"tests/unit/u.npk": _kinds_unit(A, built)}),
         ["`Beta` is provoked by no unit"]),
        ("a kind named in a unit that parses nothing",
         _kinds_tree(["Alpha", "Beta"], {"tests/unit/u.npk": _kinds_unit(A),
                                         "tests/unit/v.npk": _kinds_unit(B, parses=False)}),
         ["`Beta` is provoked by no unit"]),
        ("a kind named in a comment",
         _kinds_tree(["Alpha", "Beta"], {"tests/unit/u.npk": _kinds_unit(A, "// " + B)}),
         ["`Beta` is provoked by no unit"]),
        ("a row whose kind a test provokes",
         _kinds_tree(["Alpha", "Beta"], {"tests/unit/u.npk": _kinds_unit(A, B)}, [("Beta", "cycle 0.9.1")],
                     "the kind it raises: `Beta`"),
         ["lists `Beta` as a kind no pattern reaches yet"]),
        ("a row naming no kind the enum declares",
         _kinds_tree(["Alpha"], {"tests/unit/u.npk": _kinds_unit(A)}, [("Delta", "cycle 0.9.1")]),
         ["lists `Delta`, which `PatternErrorKind` does not declare"]),
        ("a row naming no cycle",
         _kinds_tree(["Alpha", "Gamma"], {"tests/unit/u.npk": _kinds_unit(A)}, [("Gamma", "later")]),
         ["gives `Gamma` no cycle"]),
        ("a row whose cycle's README does not name its kind",
         _kinds_tree(["Alpha", "Gamma"], {"tests/unit/u.npk": _kinds_unit(A)}, [("Gamma", "cycle 0.9.1")],
                     "the kind it raises: none named"),
         ["does not name it"]),
    ], _kinds_tree(["Alpha", "Beta", "Gamma"],
                   {"tests/unit/u.npk": _kinds_unit(A, B, "PatternError:g = r ?? raw pattern_error(PatternErrorKind.Gamma, 0i64, 0i64, 0u32);",
                                                    "// PatternErrorKind.Gamma is listed, and this comment provokes nothing")},
                   [("Gamma", "cycle 0.9.1")]))


def _case33(d):
    return None                                   # handled by `_run_case33`


def _case19(d):
    """A RED UNIT HIDDEN BY TWO LONE CARRIAGE RETURNS -- the fifth audit's BL-9 (a).

    The plant that walked through both of RX-157's defences at once, `209/209`
    GREEN: the red unit (case 1's fault) carries `// note<CR>/*` above its `main`,
    and a sibling carries `// see<CR>use "cr_red.npk".*;`. To the compiler both
    are line comments -- each file compiles, links and runs. To a reader that
    makes a CR a line end, the sibling imports the red unit and the red unit's
    `main` sits inside an unterminated block comment, so the old skip judged it
    a helper. RX-165 gives the two defences no reader in common: the bytes reader
    sees no import, and the COMPILER sees the red unit's `main`. This case goes
    red while EITHER holds, and was mutation-tested with each removed alone and
    with both removed together (`0.0.5.md` §12)."""
    _write(d, "tests/case/cr_red.npk",
           "// expect-exit: 42\n"
           "mod:cr_red;\n\n"
           "// note\r/*\n"
           "func:main = int32(cstring[]:_~argv) {\n"
           "    exit 41i32;\n"
           "};\n" + FAILSAFE)
    _write(d, "tests/case/cr_sibling.npk",
           "// expect-exit: 0\n"
           "mod:cr_sibling;\n"
           '// see\ruse "cr_red.npk".*;\n\n'
           "func:main = int32(cstring[]:_~argv) {\n"
           "    exit 0i32;\n"
           "};\n" + FAILSAFE)
    return TOML % PROGRAM_ENTRY


def _syscaller(d, name, before_use, path):
    """Case 8's fixture, renamed, with `before_use` written above its one `use`
    and its path spelled `path` -- the two ways BL-9 hid B-2's reach."""
    text = open(os.path.join(ROOT, "harness/selfcheck/syscall_consumer.npk"),
                encoding="utf-8", newline="").read()
    for old, new in (("mod:syscall_consumer;", f"mod:{name};"),
                     ('use "../../src/lib.npk".*;', before_use + f'use "{path}".*;')):
        if text.count(old) != 1:
            raise RuntimeError(f"case fixture: `{old}` is not in syscall_consumer.npk "
                               f"exactly once, so the substitution did not happen")
        text = text.replace(old, new)
    _lib(d)
    _write(d, f"tests/case/{name}.npk", text)


def _case20(d):
    """A SYSCALL BEHIND `// note<CR>/*` -- BL-9 (a) on B-2's reach.

    The real `use` of `src/` follows a line comment whose text holds a lone CR
    and a `/*`. The compiler reads a comment and then the import; a reader that
    makes the CR a line end sees an unterminated block comment swallow the
    import, answers "does not reach src/", and neither scan runs -- so the
    `sys(39i64)` in `main` passes. It must be named."""
    _syscaller(d, "cr_syscall_consumer", "// note\r/*\n", "../../src/lib.npk")
    return TOML % PROGRAM_ENTRY


def _case21(d):
    """A SYSCALL BEHIND AN ESCAPED IMPORT PATH -- BL-9 (b).

    `"..\\x2f..\\x2fsrc/lib.npk"` is `"../../src/lib.npk"` to the compiler, which
    takes a string literal's DECODED value as the path; a reader that follows
    the literal's text finds no `src/` and neither scan runs. It must be named."""
    _syscaller(d, "esc_syscall_consumer", "", "..\\x2f..\\x2fsrc/lib.npk")
    return TOML % PROGRAM_ENTRY


def _stand_in(d, name, codes):
    """A stand-in executable exiting `codes[k % len(codes)]` on its k-th run -- a
    counter file beside it -- so a 'program' whose answer changes from run to run
    is DETERMINISTIC here, which no real program could promise."""
    path = os.path.join(d, name)
    arms = "".join(f"if [ $((n % {len(codes)})) -eq {k} ]; then exit {c}; fi\n"
                   for k, c in enumerate(codes))
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write('#!/bin/sh\nn=$(cat "$0.n" 2>/dev/null || echo 0)\n'
                 'echo $((n + 1)) > "$0.n"\n' + arms + "exit 1\n")
    os.chmod(path, 0o755)
    return path


def _run_case22(case):
    """Case 22, on the instrument -- `stages._pending` with stand-in executables,
    as the fourth audit's triage measured N-19 by hand and no case repeated.

    RX-159 holds a pending unit to its named exit on EVERY LEG and EVERY RUN. The
    −O2 leg has had a case since then (11); "every run" and "the legs disagree"
    had none, and `range(exp.stress)` narrowed to one run left the self-check
    green (the fifth audit's N-27). Three calls, `stress: 3`, pending on 92:
    92, 94, 92 on each leg must be red; 92 at −O0 and 94 through −O2 must be red;
    and the control, 92 on every run of both, must be PENDING -- so the case
    cannot pass by calling everything red."""
    import stages
    import expect as expect_mod
    exp = expect_mod.read("// expect-exit: 0\n// pending-until: 0123abc exit 92\n"
                          "// stress: 3\n")
    d = tempfile.mkdtemp(prefix="nregex-selfcheck-22-")
    wrong = []
    try:
        trials = (
            ("flips.npk", [("at -O0", _stand_in(d, "flip_a", [92, 94])),
                           ("through opt -O2", _stand_in(d, "flip_b", [92, 94]))], False,
             "a unit giving 92, 94, 92 on each leg"),
            ("legs.npk", [("at -O0", _stand_in(d, "leg_a", [92])),
                          ("through opt -O2", _stand_in(d, "leg_b", [94]))], False,
             "a unit giving 92 at -O0 and 94 through opt -O2"),
            ("steady.npk", [("at -O0", _stand_in(d, "steady_a", [92])),
                            ("through opt -O2", _stand_in(d, "steady_b", [92]))], True,
             "the control, 92 on every run of both legs"),
        )
        said = []
        for name, legs, pending, what in trials:
            r = stages._pending(None, legs, name, exp)
            is_pending = len(r) == 1 and isinstance(r[0], stages.Pending)
            is_red = (len(r) == 1 and isinstance(r[0], str)
                      and "PENDING ON A DIFFERENT FAILURE" in r[0])
            if pending and not is_pending:
                wrong.append(f"{what} was not PENDING: {r!r}")
            elif not pending and not is_red:
                shown = r[0].line() if is_pending else repr(r)
                wrong.append(f"{what} was not red: {shown}")
            else:
                said.append(what + (" PENDING" if pending else " red"))
    finally:
        shutil.rmtree(d, ignore_errors=True)
    if wrong:
        return Outcome(case, False, "a pending unit is not held on every run and every "
                       "leg: " + "; ".join(wrong))
    return Outcome(case, True, "; ".join(said))


def _case22(d):
    return None                                   # handled by `_run_case22`


def _run_case23(case):
    """Case 23, on the instrument -- `stages.imported_by_others` with its READER
    STUBBED OUT, so the second defence is tested ALONE (RX-165).

    RX-157 said its second defence "holds whatever the reader gets wrong next",
    and it shared the reader: the fifth audit's BL-9 walked through both at once.
    A case that exercises the pair together cannot see that -- case 19 goes red
    while either holds, so it stays green with defence 2 deleted. Here the reader
    is replaced by the worst one possible: `_uses` says every file imports every
    other, and `lexical.blank` blanks every byte, so no reader-based rule could
    see a `main` anywhere. The compiler still must: of a red program, a clean
    program and a helper with no `main`, only the helper may be skipped. With
    defence 2 deleted all three are skipped; asked of the reader again, the same."""
    import types
    import build
    import lexical
    import stages
    import toolchain
    npkc, _ = toolchain.compiler(lambda s: None)
    d = tempfile.mkdtemp(prefix="nregex-selfcheck-23-")
    real_uses, real_blank = stages._uses, lexical.blank
    try:
        files = {"prog_red.npk": _program("prog_red", 41, 42),
                 "prog_ok.npk": _program("prog_ok", 0, 0),
                 "helper.npk": "mod:helper;\n\npub func:h = int64() never fails {\n"
                               "    pass 7i64;\n};\n"}
        paths = []
        for name, text in files.items():
            _write(d, name, text)
            paths.append(os.path.join(d, name))
        c = types.SimpleNamespace(root=d, tmp=d, npkc=npkc)
        stages._uses = lambda path: [q for q in paths if q != path]
        lexical.blank = lambda text, sp=None: "".join(
            ch if ch == "\n" else " " for ch in text)
        skip = stages.imported_by_others(c, paths)
    finally:
        stages._uses, lexical.blank = real_uses, real_blank
        shutil.rmtree(d, ignore_errors=True)
    want = {os.path.normpath(os.path.join(d, "helper.npk"))}
    if skip != want:
        shown = sorted(os.path.basename(k) for k in skip) or ["nothing"]
        return Outcome(case, False, f"with a reader that invents every import and sees "
                       f"no code, the skip took {', '.join(shown)} -- only helper.npk "
                       f"may go: the compiler's `main` is the second defence's whole "
                       f"question, and it must not need the reader")
    return Outcome(case, True, "with a reader that invents every import and sees no "
                               "code, the compiler kept both programs and let the "
                               "helper go")


def _case23(d):
    return None                                   # handled by `_run_case23`


def _case26(d):
    """A `check` case naming a code ONCE where it is reported at TWO sites -- the
    compiler's D-332, ported (RX-178). Under B-7's set equality this passes: the
    code is named and reported. `tests/rejection/pattern_error_literal.npk` named
    its `NITPICK-TYPE-079` once for four sites until cycle 0.1.0b."""
    _write(d, "tests/case/two_sites.npk",
           "// expect-error: NITPICK-TYPE-007\n"
           "mod:two_sites;\n\n"
           "func:main = int32(cstring[]:_~argv) {\n"
           "    int32:a = true;\n"
           "    int32:b = true;\n"
           "    exit 0i32;\n"
           "};\n" + FAILSAFE)
    return TOML % CHECK_ENTRY


def _case27(d):
    """A `check` case naming a code at TWO sites where it is reported at ONE --
    the compiler's own `silent_site` self-check case (D-332), ported (RX-178). Its
    lines carry no position, so only the count can see the missing site."""
    _write(d, "tests/case/silent_site.npk",
           "// expect-error: NITPICK-TYPE-007\n"
           "// expect-error: NITPICK-TYPE-007\n"
           "mod:silent_site;\n\n"
           "func:main = int32(cstring[]:_~argv) {\n"
           "    int32:a = true;\n"
           "    int32:b = 1i32;\n"
           "    exit 0i32;\n"
           "};\n" + FAILSAFE)
    return TOML % CHECK_ENTRY


def _case24(d):
    """A manifest whose LAYOUT PIN is not what the pinned `opt` derives from its
    triple -- one field of the layout dropped (RX-176). The compiler's
    `check_datalayout_pin`, ported: a stated layout proves nothing about itself,
    because `opt` keeps a wrong one as written and `llc` accepts one in silence."""
    _write(d, "tests/case/fine.npk", _program("fine", 0, 0))
    return (TOML % PROGRAM_ENTRY).replace("-n8:16:32:64-S128", "-n8:16:32-S128")


def _case25(d):
    """A tree pinned CONSISTENTLY to another target -- `i686-unknown-linux-gnu`
    and the layout the pinned `opt` derives for it -- so the pin check passes and
    only the header belt can see that every module this compiler emits states
    x86-64 (RX-176). The compiler's `check_module_header`, ported."""
    _write(d, "tests/case/fine.npk", _program("fine", 0, 0))
    return ((TOML % PROGRAM_ENTRY)
            .replace('"x86_64-unknown-linux-gnu"', '"i686-unknown-linux-gnu"')
            .replace('"e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"', '"e-m:e-p:32:32-p270:32:32-p271:32:32-p272:64:64-'
                     'i128:128-f64:32:64-f80:32-n8:16:32-S128"'))


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
#
# AND EVERY PHRASE MUST BE ONE ONLY THE RED CAN PRINT. Case 12 was first written
# requiring "the marker names exit 92 and this tree gives 41" -- which the PEND
# line prints as well -- and, with the check it guards deleted, it PASSED: the
# PEND line supplied the words and an unrelated red supplied the exit (the
# residue list firing in the fixture tree, since scoped to the real one in
# `run.py`). Mutation-tested at the third cycle-0.0 audit's triage; it now also
# requires "PENDING ON A DIFFERENT FAILURE", which nothing else prints.
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
         "B-2a: the symbol difference can see THAT, never WHERE (RX-120, RX-131)",
         _case8, ["syscall_consumer.npk", "`main` calls `npk_sys6`"]),
    Case(9, "a program needing a floor symbol neither the baseline nor the residue list has",
         "B-2, RX-116 as amended by RX-131 -- the other layer, and neither "
         "catches the other's",
         _case9, ["new_symbol_consumer.npk", "`npk_mono_now`",
                  "NOT ON THE REVIEWED RESIDUE LIST"]),
    Case(10, "a non-deterministic emission",
         "B-4: the `repro` comparison must report the byte offset",
         _case10, ["first difference at byte 17"]),
    Case(11, "a red hidden behind a pending marker the reviewed list does not name",
         "RX-154: one comment line must not move a red out of a green run's "
         "denominator -- the third audit's M3, which defeated case 1 -- and RX-159: "
         "the unit is observed through opt -O2 as well, which it was not (N-19)",
         _case11, ["hidden_red.npk", "NOT ON THE REVIEWED PENDING LIST",
                   "41 through opt -O2"]),
    Case(12, "a pending unit failing for a reason other than the one its marker names",
         "RX-154: the marker excuses the failure it names and no other -- the "
         "third audit's M2, B-7's reasoning applied to the marker",
         _case12, ["other_red.npk", "PENDING ON A DIFFERENT FAILURE",
                   "the marker names exit 92 and this tree gives 41"]),
    Case(13, "a pending marker that has outlived its reason",
         "RX-146's self-retirement, run on every invocation instead of once by hand",
         _case13, ["stale_marker.npk", "IS NOW STALE"]),
    Case(14, "an engine and the naive oracle disagreeing on a generated case",
         "the oracle stage -- V-20 has named it since 0.0.0 and this list did not "
         "carry it until the third audit's triage",
         None, (), "0.5 -- there is no oracle stage yet"),
    Case(15, "a red unit named only by a `use` inside a sibling's block comment",
         "RX-157: a comment in ANOTHER file must not move a red out of a green run "
         "-- the fourth audit's BL-7, 173/173 GREEN through the fix for BL-6",
         _case15, ["commented_red.npk", "exited 41, expected 42"]),
    Case(16, "a PENDING.txt line that no pending unit matches",
         "RX-159: the list's second direction, which nothing tested (N-20) -- a "
         "stale line pre-authorises the next marker",
         _case16, ["listed_no_marker.npk", "no PENDING unit matches it"]),
    Case(17, "a RESIDUE.txt entry that no scanned program references",
         "RX-159: the residue list's second direction, which nothing tested since "
         "the third triage scoped it out of every inner run (N-20)",
         _case17, ["`npk_selfcheck_case17` is permitted and NO SCANNED PROGRAM "
                   "REFERENCES IT"]),
    Case(18, "the harness's one reading of source, fed each form that has mattered",
         "RX-157, RX-165: the program suites' skip, B-2's reach and every tree check "
         "stand on it, so its regression would weaken all of them and redden none",
         _case18, ()),
    Case(19, "a red unit hidden by two lone carriage returns",
         "RX-165: the fifth audit's BL-9 (a), 209/209 GREEN through both of RX-157's "
         "defences at once, because they shared a reader",
         _case19, ["cr_red.npk", "exited 41, expected 42"]),
    Case(20, "a syscall behind a `/*` that follows a lone CR in a line comment",
         "RX-165: BL-9 (a) on B-2's reach -- the reader blanked the real import",
         _case20, ["cr_syscall_consumer.npk", "`main` calls `npk_sys6`"]),
    Case(21, "a syscall behind an escaped import path",
         "RX-165: BL-9 (b) -- the reader followed the path's text, not its value",
         _case21, ["esc_syscall_consumer.npk", "`main` calls `npk_sys6`"]),
    Case(22, "a pending unit whose answer changes from run to run, or leg to leg",
         "RX-159's every-run half, which no case exercised (the fifth audit's N-27)",
         _case22, ()),
    Case(23, "the skip's second defence alone, under a reader that invents every import",
         "RX-165: a defence 'that holds whatever the reader gets wrong' is tested with "
         "the reader wrong -- RX-157's shared it, and BL-9 passed both at once",
         _case23, ()),
    Case(24, "a manifest whose layout pin is not what the pinned opt derives",
         "RX-176: the compiler's pin check, ported -- a stated layout proves nothing "
         "about itself",
         _case24, ["pins the layout", "but the pinned `opt` derives"]),
    Case(25, "a tree pinned consistently to another target",
         "RX-176: the pin check passes, so only the header belt can see every "
         "emission state x86-64",
         _case25, ["the module's header is not the pinned one",
                   "i686-unknown-linux-gnu"]),
    Case(26, "a `check` case naming a code once where it is reported at two sites",
         "RX-178: the compiler's D-332 -- a set of codes cannot see a count",
         _case26, ["two_sites.npk", "is reported at 2 site(s)"]),
    Case(27, "a `check` case naming a code at two sites where it is reported at one",
         "RX-178: the compiler's `silent_site`, ported -- the hazard D-332 was "
         "decided for",
         _case27, ["silent_site.npk", "is reported at 1 site(s)"]),
    Case(28, "an extra error identity: private with a raise site, two on one line, split across two",
         "RX-179: the ecosystem audit's EC4 -- `check_error_budget` passed all three "
         "and caught only the control",
         _case28, ()),
    Case(29, "an accessor reached by a spaced form: `.ptr [`, `. items [`, and across a line break",
         "RX-179: the ecosystem audit's EC5 -- 'the only bounds check this library has' "
         "passed all four",
         _case29, ()),
    Case(30, "a function on a call cycle: a self-call, a mutual pair, a pair across two "
             "modules, a generic self-call, a self-call split by a comment",
         "RX-192: `SAFETY.md` S-18's explicit stack has a belt -- no function under src/ "
         "recurses -- and a by-name reader must neither miss a cycle nor invent one",
         _case30, ()),
    Case(31, "a unit killed by a signal: SIGSEGV and SIGKILL, three runs each",
         "RX-194: the gate's 'not on a signal' is the runner reading a killed process "
         "as `0 - signal` -- shown red here, so `expect-exit: 0` is met by a normal exit alone",
         _case31, ()),
    Case(32, "a bound compared in each spelling the compiler accepts: digit-separated, hex, "
             "binary, octal, a wide width suffix, and left of the operator -- and a character "
             "literal and a literal behind a widening, either side, each spelling asked of the compiler",
         "RX-202: `check_constants_named` read a literal as decimal digits after the operator "
         "and passed all six -- a spelling it cannot read is a bound it cannot see; RX-220: and a "
         "re-pin that moves the numeric scan is red here",
         _case32, ()),
    Case(33, "a kind no test provokes, one a unit only builds, one named where nothing parses or in a comment, "
             "and a stale, an unknown, an undated and an unplanned row of Y-25's table",
         "RX-219: the cycle 0.1 Gate -- every kind provoked or listed with the cycle that will provoke it, held "
         "both ways; a kind nothing produces is the dormant-rule pattern the compiler's `check_codes_tested` refuses",
         _case33, ()),
    Case(34, "a red hidden behind a pending marker labelled by a subcycle, which the reviewed list does not name",
         "RX-226: the marker names a subcycle of this library too, for a unit pending on a later subcycle's "
         "hook -- and a new shape of label is no new route out of the denominator: case 11's plant, read "
         "and held to the list",
         _case34, ["hidden_cycle_red.npk", "`pending-until: 0.3.4 exit 41` is NOT ON THE REVIEWED PENDING LIST",
                   "41 through opt -O2"]),
]


def counts():
    """(live, pending, total) -- read from `CASES`, so the driver's summary can
    never again print a count that the list has moved away from."""
    pending = sum(1 for c in CASES if c.pending is not None)
    return len(CASES) - pending, pending, len(CASES)


# --- the tree the cases are built in ---------------------------------------------------

def _at(d, rel):
    p = os.path.join(d, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p


def _write(d, rel, text):
    # `newline=""`: what the case writes is what the file holds, byte for byte --
    # cases 19 and 20 plant a lone CR, and a translating write would move it.
    with open(_at(d, rel), "w", encoding="utf-8", newline="") as fh:
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
    # RX-131: B-2's first layer diffs against this, so a scratch tree without it
    # fails at the BUILD step and every case's red becomes the same red.
    shutil.copy(os.path.join(ROOT, "harness/baseline/RESIDUE.txt"),
                _at(d, "harness/baseline/RESIDUE.txt"))


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
    if case.num == 18:
        return _run_case18(case)
    if case.num == 22:
        return _run_case22(case)
    if case.num == 23:
        return _run_case23(case)
    if case.num == 28:
        return _run_case28(case)
    if case.num == 29:
        return _run_case29(case)
    if case.num == 30:
        return _run_case30(case)
    if case.num == 31:
        return _run_case31(case)
    if case.num == 32:
        return _run_case32(case)
    if case.num == 33:
        return _run_case33(case)
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

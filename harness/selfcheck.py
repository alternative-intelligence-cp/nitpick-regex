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
was not until RX-159 (the fourth audit's N-19).

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


def _pending_program(mod, exit_code, expect_exit, marker_exit):
    """A program carrying `pending-until:` -- the marker under test in 11-13.

    The commit is `0123abc`, which is commit-shaped and names nothing: the
    marker's commit is a LABEL the runner never resolves (RX-154), so a real
    one would test nothing a fake one does not."""
    return (f"// expect-exit: {expect_exit}\n"
            f"// pending-until: 0123abc exit {marker_exit}\n"
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

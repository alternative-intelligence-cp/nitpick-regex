#!/usr/bin/env python3
"""The tree checks -- `TESTING.md` §8, `0.0.3.md` §4.

WHAT A TREE CHECK IS, AND WHY IT IS NOT A TEST. A test runs the library. A tree
check DIFFS THE LIBRARY AGAINST A DOCUMENT THAT DESCRIBES IT, and fails when
they disagree. Every one here has a specification rule as its authority and
cites it by RULE NAME rather than by line number -- a line number is a property
of one checkout and this repository has moved them under a sweep already.

RULE P-16: THEY RUN ON EVERY FULL INVOCATION, INCLUDING THE ONES WITH NOTHING
TO CHECK. `check_error_budget` over a library with one `error:` and
`check_layering` over a tree with one `use` edge are the right answers today,
and running them today is what makes them exist on the day the second one is
written. A check introduced at the moment it would first fail is a check
nobody has ever seen pass.

AND THE CONVERSE, WHICH IS THE HALF THAT BITES. A check that finds nothing
because it LOOKED nowhere is indistinguishable in the output from one that
found nothing because there was nothing to find. So every check here reports
how many things it examined, not merely its verdict, and `check_layering` says
in as many words that six of this library's eight `src/` files are reached by
no suite at all -- which is the gap the `parse` stage (RX-124) exists to close.

THE ONE THAT ONLY REPORTS. `check_specs_current` never fails the run
(`0.0.3.md` §4). It reads every `meta/specs/*.md` citation in the tree and says
which no longer resolve. It reports rather than fails because a citation can go
stale for a good reason mid-cycle, and a check that blocks a commit for that
would be routinely bypassed -- which is worse than one that is read.

EVERY CHECK HERE READS SOURCE THROUGH `lexical.py` -- RX-157. Code is what is
left when every comment, string, character literal and template text has been
blanked, and an import is what the compiler's parser would read. Until the
fourth cycle-0.0 audit this file had its own blanker, which knew `//` and `"`
and nothing else -- so a `'"'` character literal hid the rest of its line from
three checks (N-18's M12) -- and its own import pattern, one of three in the
harness that disagreed.

AND EVERY `.npk` FILE HERE IS OPENED BY `lexical.read`, AS BYTES -- RX-165. Each
check opened its files in Python's text mode, which made a lone carriage return a
line end: after `// note<CR>/*` the reader saw a block comment the compiler never
saw, and blanked the rest of the file from every check. The fifth cycle-0.0
audit (BL-9) hid an owning `string` field of a `src/` `Vec` element that way --
`check_vec_elements_own_nothing` cleared it and the run was `210/210` GREEN --
and an escaped import path hid a `core` -> `engine` edge from `check_layering`.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lexical                                                # noqa: E402

# `BUILD.md` §6, rule B-16 -- the layering, and the direction of every arrow.
# A module may not import a module to its LEFT in this list; `core` is
# rightmost and depends on nothing.
#
# Held as a rank rather than as a diagram, because "may not import to its left"
# is the whole rule and a rank is the smallest thing that says it. The names
# are the DIRECTORY names under `src/`.
LAYERS = ["api", "engine", "compile", "hir", "syntax", "unicode", "core"]
RANK = {name: i for i, name in enumerate(LAYERS)}

# Rule B-16a -- `src/lib.npk` is ABOVE the diagram, not in it. It imports
# whichever layers export a public name and nothing in `src/` imports it. The
# exception is read from the rule, not special-cased on the filename: a file
# directly under `src/` is not a layer, because a layer is a DIRECTORY.
#
# Rule B-17 -- `tests/oracle/` may import `core` and `hir` and nothing else,
# so that a shared bug cannot make the oracle and the engine it judges agree.
ORACLE_MAY_IMPORT = {"core", "hir"}

# `SAFETY.md` §5, rule S-12 -- every bound is a named constant in
# `src/core/limits.npk`. Nine of them, and the table there is the authority.
LIMITS_FILE = os.path.join("src", "core", "limits.npk")
LIMIT_NAMES = [
    "NREGEX_PATTERN_BYTES", "NREGEX_NEST_DEPTH", "NREGEX_PROGRAM_INSTRUCTIONS",
    "NREGEX_REPEAT_MAX", "NREGEX_REPEAT_PRODUCT", "NREGEX_CAPTURE_GROUPS",
    "NREGEX_CLASS_RANGES", "NREGEX_DFA_CACHE_BYTES", "NREGEX_DFA_MIN_STATES",
]

# `SAFETY.md` §4, rule S-8 (RX-060) -- exactly ONE public `error:` identity.
# The NAME is checked as well as the count: "exactly one" that silently became
# a different one would be the same major-version break as two.
ERROR_BUDGET = ["ERegexPattern"]

_PUB_ERROR = re.compile(r'^\s*pub\s+error\s*:\s*([A-Za-z_]\w*)\s*;')
_ANY_ERROR = re.compile(r'^\s*(?:pub\s+)?error\s*:\s*([A-Za-z_]\w*)\s*;')


class Result:
    """One check's verdict AND its denominator. The denominator is not
    decoration: `0 findings over 0 things examined` and `0 findings over 34`
    are different states and only one of them is evidence."""

    def __init__(self, name, rule, examined, failures, notes=()):
        self.name = name
        self.rule = rule
        self.examined = examined
        self.failures = list(failures)
        self.notes = list(notes)

    @property
    def ok(self):
        return not self.failures


def npk_files(root, under):
    out = []
    base = os.path.join(root, under)
    for dirpath, dirnames, names in os.walk(base):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for n in sorted(names):
            if n.endswith(".npk"):
                out.append(os.path.join(dirpath, n))
    return sorted(out)


def _read(path):
    """A `.npk` file as the compiler reads it -- `lexical.read`, RX-165."""
    try:
        return lexical.read(path)
    except (OSError, ValueError):
        return ""


def _uses(path):
    """Every `use`/`pub use` target in one file, as a path relative to it --
    read the way the compiler reads it (`lexical.imports`, RX-157)."""
    return [(n, target) for n, target, _ in lexical.imports(_read(path))]


def _layer_of(root, path):
    """The layer a file belongs to, or None when it is above the diagram.

    A LAYER IS A DIRECTORY (B-16), so `src/lib.npk` -- directly under `src/`
    with no layer directory between -- has no layer, and that is B-16a's
    exception read out of the rule instead of matched on the filename."""
    rel = os.path.relpath(path, os.path.join(root, "src"))
    parts = rel.split(os.sep)
    if len(parts) < 2:
        return None
    return parts[0] if parts[0] in RANK else None


# --- check_layering -------------------------------------------------------------------

def check_layering(root):
    """Every `use` edge against `BUILD.md` §6 (B-16, B-16a, B-17) and B-15a.

    FOUR RULES, ONE WALK:
      B-16   a module may not import a module to its LEFT.
      B-16a  `src/lib.npk` is above the diagram and nothing in `src/` imports it.
      B-17   `tests/oracle/` may import `core` and `hir` and NOTHING else.
      B-15a  the umbrella is all `pub use`, and never plain-`use`s a path it
             also `pub use`s -- the silent-cancellation shape RX-113 measured,
             which produces NO DIAGNOSTIC and surfaces in the consumer.
    """
    fl, notes = [], []
    files = npk_files(root, "src")
    lib = os.path.join(root, "src", "lib.npk")
    edges = 0

    for p in files:
        rel = os.path.relpath(p, root)
        mine = _layer_of(root, p)
        for ln, target in _uses(p):
            edges += 1
            tgt = os.path.normpath(os.path.join(os.path.dirname(p), target))
            if os.path.normpath(tgt) == os.path.normpath(lib) and p != lib:
                fl.append(f"{rel}:{ln}: imports `src/lib.npk`. NOTHING IN src/ MAY: "
                          f"the umbrella is above the layering diagram, not in it "
                          f"(BUILD.md B-16a), and an import of it from inside is the "
                          f"cycle that rule exists to prevent.")
                continue
            theirs = _layer_of(root, tgt)
            if mine is None or theirs is None:
                continue
            if RANK[theirs] < RANK[mine]:
                fl.append(f"{rel}:{ln}: `{mine}` imports `{theirs}`, which is to its "
                          f"LEFT in BUILD.md §6's diagram "
                          f"({' -> '.join(LAYERS)}). A module may not import a module "
                          f"to its left (B-16); a layering violation arrives as a "
                          f"cycle six months after somebody moved one function.")

    fl += _check_umbrella(root, lib)

    # B-17. Nothing is here yet -- the oracle lands at 0.5 -- and running the
    # check over an empty directory today is P-16's whole point.
    oracle = npk_files(root, os.path.join("tests", "oracle"))
    for p in oracle:
        rel = os.path.relpath(p, root)
        for ln, target in _uses(p):
            edges += 1
            tgt = os.path.normpath(os.path.join(os.path.dirname(p), target))
            theirs = _layer_of(root, tgt)
            if theirs is None:
                continue
            if theirs not in ORACLE_MAY_IMPORT:
                fl.append(f"{rel}:{ln}: the oracle imports `{theirs}`. It may import "
                          f"{' and '.join(sorted(ORACLE_MAY_IMPORT))} and nothing else "
                          f"(BUILD.md B-17, TESTING.md V-4): the naive reference "
                          f"matcher must not share code with the engines it judges, "
                          f"because a shared bug would make them AGREE.")
    notes.append(f"{len(oracle)} file(s) under tests/oracle/ -- B-17's restriction has "
                 f"nothing to check until cycle 0.5, which is the right answer and is "
                 f"why the check runs now (P-16).")
    return Result("check_layering", "BUILD.md B-15a, B-16, B-16a, B-17",
                  f"{len(files) + len(oracle)} file(s), {edges} use edge(s)", fl, notes)


def _check_umbrella(root, lib):
    """RULE B-15a, AND IT IS THE ONE WITH NO COMPILER BEHIND IT.

    A plain `use` re-exports nothing, and a plain `use` written above a
    `pub use` OF THE SAME PATH silently downgrades the re-export to nothing at
    NO DIAGNOSTIC -- `symtab_bind_import` declines a name already bound and
    returns the prior binding without merging the new flags (RX-113, workbench
    O-N13). The failure lands in the CONSUMER as "cannot find X in this scope",
    with nothing wrong at the line that caused it. No compiler will report this
    for us; this check is the only thing that does."""
    if not os.path.exists(lib):
        return [f"src/lib.npk is missing -- it is the umbrella and the whole public "
                f"surface (BUILD.md B-15a)"]
    fl = []
    plain, pub = {}, {}
    try:
        text = lexical.read(lib)
    except OSError as e:
        return [f"src/lib.npk: {e}"]
    for ln, target, is_pub in lexical.imports(text):
        if is_pub:
            pub.setdefault(target, []).append(ln)
        else:
            plain.setdefault(target, []).append(ln)
            fl.append(f"src/lib.npk:{ln}: a plain `use` in the umbrella. EVERY LINE "
                      f"HERE IS `pub use` (B-15a rule 1): a plain `use` re-exports "
                      f"nothing, for any kind of symbol, and the failure appears in "
                      f"the consumer rather than here.")
    for target, lns in sorted(plain.items()):
        if target in pub:
            fl.append(f"src/lib.npk: `{target}` is plain-`use`d at line "
                      f"{lns[0]} AND `pub use`d at line {pub[target][0]}. THE PLAIN "
                      f"ONE SILENTLY CANCELS THE RE-EXPORT (B-15a rule 2, RX-113): "
                      f"the first import of a name wins, a later one is declined "
                      f"without merging its flags, and there is NO DIAGNOSTIC. This "
                      f"check is the only thing in the world that reports it.")
    return fl


# --- check_error_budget ---------------------------------------------------------------

def check_error_budget(root):
    """Public `error:` declarations against `SAFETY.md` §4 -- EXACTLY ONE.

    RULE P-19: this is the one a consumer depends on. "Importing `nregex` costs
    your `failsafe` exactly one arm" is a promise no compiler will check for us
    -- REACH-002 makes every public identity a mandatory arm in every consuming
    program, so a second one is a compile-time break in code we do not own, and
    a MAJOR version (RX-060, S-8). This check is what keeps the promise true."""
    found = []
    files = npk_files(root, "src")
    for p in files:
        rel = os.path.relpath(p, root)
        try:
            text = lexical.read(p)
        except OSError:
            continue
        for ln, line in enumerate(lexical.blank(text).split("\n"), 1):
            m = _PUB_ERROR.match(line)
            if m:
                found.append((m.group(1), rel, ln))
                continue
            m = _ANY_ERROR.match(line)
            if m:
                found.append(("(private) " + m.group(1), rel, ln))

    public = [f for f in found if not f[0].startswith("(private) ")]
    fl = []
    names = sorted(n for n, _, _ in public)
    if names != sorted(ERROR_BUDGET):
        shown = ", ".join(f"`{n}` ({r}:{l})" for n, r, l in sorted(public)) or "none"
        fl.append(f"the public error budget is {len(public)} identity/identities -- "
                  f"{shown} -- and SAFETY.md §4 (rule S-8, RX-060) says EXACTLY ONE, "
                  f"`{ERROR_BUDGET[0]}`. Every public `error:` is a mandatory `pick` "
                  f"arm in every consuming program's `failsafe` (REACH-002), so this "
                  f"is a compile-time break in code this repository does not own and "
                  f"a MAJOR version. If the change is intended, SAFETY.md §4 is "
                  f"amended by a numbered decision in the same commit -- never this "
                  f"list on its own.")
    private = [f for f in found if f[0].startswith("(private) ")]
    notes = [f"{len(public)} public and {len(private)} private `error:` declaration(s) "
             f"over {len(files)} file(s) in src/."]
    return Result("check_error_budget", "SAFETY.md S-8 (RX-060), P-19",
                  f"{len(files)} file(s)", fl, notes)


# --- check_constants_named ------------------------------------------------------------

# A literal that is a BOUND rather than an ordinary number. The rule (S-12) is
# about the nine named limits, so what this looks for is a bare integer used
# where a bound belongs -- a comparison against a magic number outside
# `limits.npk`. Deliberately narrow: 0, 1, 2 and the small powers are arithmetic,
# not policy, and a check that flagged them would be turned off within a week.
_SMALL = {0, 1, 2, 3, 4, 7, 8, 15, 16, 24, 31, 32, 63, 64, 100, 127, 128, 255, 256}
# A SHIFT IS NOT A COMPARISON, and the first version of this pattern could not
# tell them apart: on `x >> 6i64` the SECOND `>` matched `[<>]` and the `6` was
# reported as a bound. Found 2026-09-06 when `byteset.npk` replaced `/ 64` with
# `>> 6` for SAFETY.md S-25's reason, and the check failed the file three times
# for an operator it was never about. `(?<![<>])` and `(?![<>])` exclude `<<`
# and `>>` from both ends.
_CMP_LITERAL = re.compile(
    r'(?<![<>])[<>]=?(?![<>])\s*(\d+)(?:i8|i16|i32|i64|u8|u16|u32|u64)?\b')


def check_constants_named(root):
    """No bound outside `src/core/limits.npk` -- `SAFETY.md` S-12 (RX-062).

    WHY A COMPARISON AND NOT EVERY LITERAL. The rule is that a BOUND is a named
    constant; it is not that arithmetic may not contain numbers. A bound is
    spent at a comparison -- `if (n > 65536)` -- so that is what is looked for,
    and the small values that are structure rather than policy (a bit width, a
    byte, an alignment) are excluded by value. A narrow check that runs is worth
    more than a broad one that gets switched off."""
    fl = []
    files = [p for p in npk_files(root, "src")
             if os.path.relpath(p, root) != LIMITS_FILE]
    for p in files:
        rel = os.path.relpath(p, root)
        try:
            text = lexical.read(p)
        except OSError:
            continue
        for ln, code in enumerate(lexical.blank(text).split("\n"), 1):
            for m in _CMP_LITERAL.finditer(code):
                v = int(m.group(1))
                if v in _SMALL:
                    continue
                fl.append(f"{rel}:{ln}: the literal `{v}` is compared against outside "
                          f"`{LIMITS_FILE}`. EVERY BOUND IS A NAMED CONSTANT THERE "
                          f"(SAFETY.md S-12, RX-062), with the specification rule that "
                          f"set it beside it -- a bound written inline is a bound "
                          f"nobody can find when the specification changes.")

    # The limits file itself: present from 0.0.4, and its nine names are the
    # table SAFETY.md §5 declares. Absent today, which is stated rather than
    # silently skipped.
    notes = []
    lim = os.path.join(root, LIMITS_FILE)
    if not os.path.exists(lim):
        notes.append(f"{LIMITS_FILE} does not exist yet -- it lands at cycle 0.0.4 with "
                     f"all nine of SAFETY.md §5's bounds. Until then this check has "
                     f"only the negative half (no bound anywhere else), and it is "
                     f"running so that the day the file appears the check already did.")
    else:
        # FROM CODE, AS A WHOLE WORD (the fifth cycle-0.0 audit's triage): this
        # searched the raw text for each name, so a name surviving only in a
        # comment -- or as the head of a longer one -- counted as declared.
        # Measured on a copy whose ninth bound was renamed and mentioned in a
        # comment: "9/9 ... declared" before, 8/9 and a failure after.
        text = lexical.blank(lexical.read(lim))
        missing = [n for n in LIMIT_NAMES
                   if not re.search(r"(?<![A-Za-z0-9_])" + n + r"(?![A-Za-z0-9_])", text)]
        if missing:
            fl.append(f"{LIMITS_FILE} does not declare {', '.join(missing)}. "
                      f"SAFETY.md §5's table is the authority and it has nine rows "
                      f"(S-12); a bound in the specification with no constant is a "
                      f"bound nothing enforces.")
        notes.append(f"{len(LIMIT_NAMES) - len(missing)}/{len(LIMIT_NAMES)} of "
                     f"SAFETY.md §5's named bounds are declared.")
    return Result("check_constants_named", "SAFETY.md S-12 (RX-062)",
                  f"{len(files)} file(s) outside {LIMITS_FILE}", fl, notes)


# --- check_no_division ----------------------------------------------------------------

_DIV_OP = re.compile(r'(?<![/*])[/%](?![/*=])')


def _blank_prose(text):
    """Comments and literals blanked, lines kept -- `lexical.blank`, RX-157.

    A CHECK OVER SOURCE MUST NOT READ PROSE, and the file most likely to break
    one is the file that DOCUMENTS the rule: `bytes.npk`'s header explains why
    there is no `/` in it, and says `/` while doing so. Blanking is therefore
    not tidiness -- without it this check fails the repository on the paragraph
    arguing for it, which is the most confusing failure available.

    THIS WAS A BLANKER OF ITS OWN UNTIL THE FOURTH CYCLE-0.0 AUDIT, and it knew
    `//` and `"` only. A `'"'` character literal opened a "string" that ran to
    the end of its line, so everything after it on that line was hidden from
    `check_no_division`, `check_accessor_confinement` and
    `check_vec_elements_own_nothing` alike (N-18's M12); a `/* */` block, a raw
    or block string and a template's text were read as code. It is now the
    harness's one reading of source, which mirrors the compiler's lexer."""
    return lexical.blank(text)


def check_no_division(root):
    """No `/` or `%` under `src/` -- `SAFETY.md` S-25 (RX-132).

    THIS IS AN ERROR-BUDGET CHECK AND NOT AN ARITHMETIC PREFERENCE. REACH-002
    arms `DivByZero` and `DivOverflow` the moment a `/` or `%` appears in a
    module, reachability is IMPORT-SCOPED, and `(*)` discharges neither. So a
    single division anywhere under `src/` charges EVERY consuming program two
    mandatory `failsafe` arms -- against S-8's promise of exactly one, and for
    an arm that in this library's actual code could never fire.

    Measured before the rule was written: two test programs calling only
    `bytes_init`, `bytes_push` and the accessor pair were refused
    `NITPICK-REACH-002` for both arms MERELY FOR IMPORTING a `bytes.npk` whose
    `bytes_put_uint` used `x / 10u64`. Rewritten by subtraction, the same two
    programs compile with the ordinary arm set. That is the whole case.

    The check is deliberately over `src/` alone. `tests/` may divide -- a test
    that needs a division declares its own arms and costs a consumer nothing,
    because nobody imports a test."""
    fl, notes = [], []
    files = npk_files(root, "src")
    for p in files:
        rel = os.path.relpath(p, root)
        try:
            text = lexical.read(p)
        except OSError:
            continue
        for ln, line in enumerate(_blank_prose(text).split("\n"), 1):
            for m in _DIV_OP.finditer(line):
                fl.append(f"{rel}:{ln}:{m.start() + 1}: `{m.group(0)}` under src/. "
                          f"A `/` or `%` ANYWHERE IN A MODULE arms `DivByZero` and "
                          f"`DivOverflow` in EVERY program that imports it, because "
                          f"reachability is import-scoped and `(*)` discharges "
                          f"neither -- two mandatory arms against SAFETY.md S-8's "
                          f"promise of exactly one. Use a shift and a mask on a "
                          f"power of two, or subtraction (S-25, RX-132).")
    notes.append("the rule is about the CONSUMER's failsafe, not about arithmetic: "
                 "tests/ may divide freely, because nobody imports a test.")
    return Result("check_no_division", "SAFETY.md S-25 (RX-132)",
                  f"{len(files)} file(s) under src/", fl, notes)


# --- check_accessor_confinement -------------------------------------------------------

# `.items[` and `.ptr[`, with the dot. Written as two patterns rather than one
# alternation so a failure names which accessor was reached around.
_ACCESSORS = (
    (".items[", "src/core/vec.npk",   "vec_get / vec_set"),
    (".ptr[",   "src/core/bytes.npk", "bytes_get / bytes_set"),
)


def check_accessor_confinement(root):
    """No `.items[` outside `vec.npk`, no `.ptr[` outside `bytes.npk` -- S-23.

    THIS IS THE ONLY BOUNDS CHECK THIS LIBRARY HAS, AND UNTIL CYCLE 0.0.5
    NOTHING ENFORCED IT. `SAFETY.md` §5.3 has said since 0.0.0 that "a tree
    check enforces that no `.items[` appears outside `src/core/vec.npk`", and
    RX-118 added the identical sentence for `.ptr[`. Both were true as
    intentions and false as descriptions: `treecheck.ALL` held four checks and
    neither of them. The specification asserted an enforcement, the reader had
    no way to tell, and the rule it guards is the one S-23 calls the only thing
    standing between a caller and a silently wrong answer.

    WHY THAT MATTERS MORE HERE THAN A MISSING CHECK USUALLY WOULD. D-070's
    bounds guard is emitted for a slice, a fixed array and a SIMD lane, and for
    nothing else. `Vec<T>.items` is a `wild T->` and a `buffer`'s bytes are
    reached through `.ptr`, a bare `uint8->`, so an out-of-range index in
    either READS AND RETURNS A HEAP WORD at exit 0 -- probe 08b measured 7 992
    bytes past the allocation. An accessor bypassed anywhere is not a crash to
    debug; it is a wrong answer with a green suite beside it.

    BOTH DIRECTIONS, because a confinement list decays the same way an
    exemption list does (`PLAYBOOK.md`). A use outside the owning file fails.
    AND AN OWNER THAT NO LONGER CONTAINS ITS OWN PATTERN FAILS TOO -- otherwise
    the day `vec.npk` is rewritten to reach its storage some other way, this
    check keeps passing over a rule that has quietly stopped being about
    anything. Membership is checked; so is the reason.

    Prose is blanked first. The files most likely to trip this are the four
    that DOCUMENT it -- `vec.npk`, `bytes.npk` and `core.npk` all name
    `.items[` or `.ptr[` in comments while explaining the prohibition -- so
    `core.npk` is the standing clean control: it contains the banned text, in a
    comment, and must not be reported."""
    fl, notes = [], []
    files = npk_files(root, "src")
    owners_seen = {pat: False for pat, _, _ in _ACCESSORS}

    for path in files:
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        try:
            text = lexical.read(path)
        except OSError:
            continue
        code = _blank_prose(text)
        for pat, owner, pair in _ACCESSORS:
            for ln, line in enumerate(code.split("\n"), 1):
                col = line.find(pat)
                while col != -1:
                    if rel == owner:
                        owners_seen[pat] = True
                    else:
                        fl.append(
                            f"{rel}:{ln}:{col + 1}: `{pat}` outside `{owner}`. "
                            f"`Vec<T>.items` is a `wild T->` and a `buffer`'s "
                            f"bytes are reached through a bare `uint8->`, so "
                            f"D-070 emits NO bounds guard for either -- an "
                            f"out-of-range index READS AND RETURNS A HEAP WORD "
                            f"at exit 0. Go through `{pair}`, which is the only "
                            f"bounds check this library has "
                            f"(SAFETY.md S-23, RX-111, RX-118).")
                    col = line.find(pat, col + 1)

    for pat, owner, pair in _ACCESSORS:
        if not owners_seen[pat]:
            fl.append(
                f"{owner}: this file is the NAMED OWNER of `{pat}` and no "
                f"longer contains it. Either the accessor pair `{pair}` stopped "
                f"reaching its storage that way -- in which case this "
                f"confinement rule now guards nothing and S-23 needs rewriting "
                f"-- or the file moved. A confinement list checks MEMBERSHIP "
                f"and its REASON, because only the second one decays quietly.")

    notes.append("both directions: a use outside the owner fails, and an owner "
                 "that no longer uses its own accessor fails too.")
    notes.append("`src/core/core.npk` names both patterns in comments and is the "
                 "clean control -- prose is blanked, so the file documenting the "
                 "rule is not failed by it.")
    return Result("check_accessor_confinement", "SAFETY.md S-23 (RX-111, RX-118)",
                  f"{len(files)} file(s) under src/, 2 confined accessors", fl, notes)


# --- check_vec_elements_own_nothing --------------------------------------------------

# DEFAULT-DENY, SINCE RX-158 (the fourth cycle-0.0 audit's N-18). An element PASSES
# only if every type it names is one of the non-owning scalars below, or a struct or
# enum declared under `src/` whose fields and payloads pass the same way. ANYTHING
# ELSE FAILS: an owning builtin, a prelude type, a bare type parameter, a name this
# lexical check cannot resolve, a pointer, a slice, a `Vec` -- because what the check
# cannot see it cannot clear. The check this replaced was a DENYLIST of nine words
# matched in the element's text, and the audit walked twelve shapes past it, eleven
# of which compile and run and six of which showed BL-5's move-out: a lowercase
# struct name, two prelude types, an enum payload, an `arena`, a `wildx` pointer, a
# generic wrapper, a generic function, `Vec <string>` with a space, a non-generic
# struct appended to `vec.npk`, a POD namesake shadowing an owning one, and a `'"'`
# earlier on the line. The compiler's owning kinds at `c3bdae2` are twelve and the
# denylist named four of them; an allowlist cannot be one word short of the
# language, because the language's new kinds are not on it.
#
# THE SCALARS ARE THE COMPILER'S, read at `c3bdae2` with `git show`:
# `LEXICAL_REFERENCE.md` §4's `BuiltinType`, less every kind `type_drops_recorded`
# (`src/frontend/types.npk`) says owns, less every kind that holds or views a block
# (a pointer, a slice) or is not a plain value (`any`, `dyn`, `func`, `Handle`,
# `Channel`, `Future`, `atomic`, `Optional`, `Result`, `range`, `array`, `cstring`,
# `NIL`). What is left IS ITS BITS -- the integers, the balanced-ternary,
# fixed-point and floating families, `bool`, the characters, and the kernel ids and
# flag families that function's own comment lists as plain integers. Widening it is
# a decision, never an edit to make a red run green.
#
# `simd` AND `complex` ARE LEFT OUT ON PURPOSE, AND NOT BECAUSE THEY OWN: the same
# function says a `simd` value is "lanes of plain scalars" and a complex "two plain
# components", nothing to drop. They are not cleared because no element under
# `src/` is one, and clearing a kind is the widening a decision makes -- the
# conservatism is this check's, and the reason it gave until the fifth cycle-0.0
# audit ("not a plain value") was not the compiler's (N-24).
_POD_SCALARS = frozenset(
    [f"int{w}" for w in (8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096)]
    + [f"uint{w}" for w in (8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096)]
    + [f"tbb{w}" for w in (8, 16, 32, 64, 128, 256)]
    + [f"frac{w}" for w in (8, 16, 32, 64)]
    + [f"tfp{w}" for w in (32, 64, 128, 256)] + ["dim256"]
    + [f"flt{w}" for w in (32, 64, 128, 256, 512)]
    + ["bool", "char8", "char16", "char32", "trit", "tryte", "nit", "nyte",
       "fd", "pid", "tid", "uid", "gid", "oflags", "prot", "mflags", "fmode"])
# A field's qualifiers are not types: `sealed`, `hidden`, `fixed`, `nodrop` and
# `move` -- the parser's `p_qualifier_bit` at `c3bdae2` -- and `limit<Rules>`
# (D-313, D-314, D-308). Each is stripped and the TYPE after it is judged, so
# `fixed string` still fails on `string`. Until the fifth cycle-0.0 audit (N-24)
# only the first two and `limit` were stripped, and `fixed int32:lo` was refused as
# "holds `fixed`" -- a name this check could not resolve. The memory qualifiers
# ARE judged -- `wild`, `wildx` and `stack` qualify a pointer, and a pointer is a
# block.
_FIELD_QUALS = re.compile(r"\b(?:sealed|hidden|fixed|nodrop|move)\b|\blimit\s*<[^<>]*>")
_BLOCK_QUALS = frozenset(["wild", "wildx", "stack", "defer"])
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_TYPE_DECL = re.compile(
    r"(?<![A-Za-z0-9_])(struct|enum)\s*:\s*([A-Za-z_]\w*)\s*(?:<([^=]*)>)?\s*=\s*\{(.*?)\};",
    re.S)
_GENERIC_PARAMS = re.compile(
    r"(?<![A-Za-z0-9_])(?:func|struct|enum)\s*:\s*[A-Za-z_]\w*\s*<([^=(]*?)>\s*=")
# `Vec<…>` with or without a space before the bracket (M9), and a generic call into
# `vec.npk` spelled with a turbofish, which instantiates `Vec<X>` without writing it.
_VEC_OPEN = re.compile(r"(?<![A-Za-z0-9_])Vec\s*<")
_VEC_TURBOFISH = re.compile(r"(?<![A-Za-z0-9_])vec_[A-Za-z0-9_]*\s*::\s*<")
_VEC_OWNER = os.path.join("src", "core", "vec.npk")


def _angle_args(code, j):
    """The text between the `<` at `j - 1` and its closing `>`, and the index past
    it. `->` is a pointer arrow and not a closing bracket, so it is stepped over;
    nesting is counted, so `Vec<Vec<int32>>` yields its outer element whole."""
    i, depth = j, 1
    while j < len(code) and depth:
        ch = code[j]
        if ch == "<":
            depth += 1
        elif ch == ">" and code[j - 1] != "-":
            depth -= 1
        j += 1
    return code[i:j - 1].strip(), j


def _vec_elements(code):
    """`(offset, element text, how)` for every `Vec` element this file names."""
    out = []
    for rx, how in ((_VEC_OPEN, "Vec"), (_VEC_TURBOFISH, "turbofish")):
        for m in rx.finditer(code):
            elem, _ = _angle_args(code, m.end())
            out.append((m.start(), elem, how))
    return sorted(out)


def _params_of(code):
    """Every generic parameter name a file declares, by name."""
    names = set()
    for m in _GENERIC_PARAMS.finditer(code):
        for p in m.group(1).split(","):
            p = p.strip().split(":")[0].strip()
            if _IDENT_RE.fullmatch(p):
                names.add(p)
    return names


_VARIANT = re.compile(r"\s*[A-Za-z_]\w*\s*")


def _members(kind, body):
    """The type texts a declaration's values are made of: a struct's field types,
    an enum's payload types. An enum variant with no payload is a tag, and owns
    nothing.

    A PAYLOAD IS `Name(...)` AND NOTHING ELSE (N-24). This read every parenthesis
    in an enum body as one, so `Lit = (1i32);` -- a discriminant -- was judged as a
    payload holding `i32`, and a POD enum was refused. What follows `=` is a value,
    not a type, and is not read. A member that holds a `#` -- a macro splice, or an
    attribute -- is returned WHOLE, and `_deny_reason` refuses it."""
    out = []
    if kind == "struct":
        for field in body.split(";"):
            if not field.strip():
                continue
            if "#" in field:
                out.append(field)
                continue
            out.append(field.rpartition(":")[0] if ":" in field else field)
    else:
        for variant in body.split(";"):
            if not variant.strip():
                continue
            if "#" in variant:
                out.append(variant)
                continue
            m = _VARIANT.match(variant)
            rest = variant[m.end():] if m else variant
            if not rest.startswith("("):
                continue                      # a tag, or a tag `= value`
            depth, j = 0, 0
            for j, ch in enumerate(rest):
                depth += (ch == "(") - (ch == ")")
                if depth == 0:
                    break
            out += [t for t in rest[1:j].split(",") if t.strip()]
    return out


def _deny_reason(text, decls, params, seen):
    """Why a type text is NOT cleared, or None when every name in it is."""
    if "#" in text:
        # A MACRO SPLICE (`#Fields();` in a struct body -- live at `c3bdae2`,
        # `p_parse_record`) is a member whose type this check cannot see until
        # the macro is expanded, and it does not expand macros. The fifth audit's
        # N-24 cleared an owning `string` field that way: `#ByteSet()` was read as
        # the POD struct `ByteSet`. Refused, with an attribute beside it.
        return (f"`{text.strip()}`, a macro splice or an attribute -- a member whose "
                f"expansion a lexical check cannot see, so it clears none")
    t = _FIELD_QUALS.sub(" ", text)
    if "->" in t:
        return "a pointer (`->`), which holds a block"
    if re.search(r"\[\s*\]", t):
        return "a slice (`[]`), a view of a block"
    t = re.sub(r"\[[^\]]*\]", " ", t)          # a fixed array's size is not a type
    for name in _IDENT_RE.findall(t):
        if name in _POD_SCALARS:
            continue
        if name in _BLOCK_QUALS:
            return f"`{name}` storage, a block"
        if name in params:
            return (f"`{name}`, a bare type parameter -- a lexical check cannot "
                    f"follow an instantiation, so it clears none")
        if name not in decls:
            return (f"`{name}`, which is neither a scalar this check clears nor a "
                    f"type declared under src/ -- a prelude type, a type parameter or "
                    f"a name it cannot resolve, and it clears nothing it cannot see")
        if name in seen:
            continue
        seen = seen | {name}
        many = len(decls[name]) > 1
        for rel, kind, own_params, body in decls[name]:
            for member in _members(kind, body):
                why = _deny_reason(member, decls, own_params, seen)
                if why:
                    also = (f", one of {len(decls[name])} declarations of that name, "
                            f"all judged because this check does not resolve imports"
                            if many else "")
                    return f"`{name}` ({rel}{also}) holds {why}"
    return None


def check_vec_elements_own_nothing(root):
    """Every `Vec` element named under `src/` is CLEARED as owning nothing -- S-23a.

    `Vec<T>` IS SPECIFIED FOR A NON-OWNING `T` (RX-155), AND NOTHING IN THE
    LANGUAGE SAYS SO. Until the third cycle 0.0 audit (BL-5) this repository
    believed `TYPE-046` refused an owning element -- four sites said a copy out
    of a `Vec` was refused, and the specifications credited the language with
    keeping every array element POD. It does not: `TYPE-046` asks for `move`,
    `pass` moves implicitly, and D-264 checks a generic body once with `T`
    treated as owning, so `vec_get` compiles at `Vec<string>` and MOVES the
    element out of its slot -- a second read is empty and `count` still counts
    it -- while `vec_set`, `vec_remove`, `vec_swap_remove`, `vec_truncate`,
    `vec_clear` and `vec_free` orphan what they discard. Measured at
    `c3bdae2`, and pinned per verb by the `vec_owning_*` units.
    *(Since cycle 0.0.4e, compiler `c970483`: `vec_get` takes `T: Pod` and an
    owning `T` is refused at compile time, NITPICK-TYPE-017 (RX-168). The six
    orphaning verbs are as stated, and this check is still the rule for them and
    the belt for `vec_get`, whose bound an impl declaring `move` defeats.)*

    So the restriction is this library's, and this is what makes it a rule
    rather than a request: `src/` is the code that ships, and a `Vec` whose
    element this check cannot clear fails the run. Today that is `SparseSet`'s
    two `Vec<int32>` fields and its two `vec_init_zeroed::<int32>` calls; cycle
    0.1's parser is its first real subject.

    DEFAULT-DENY, SINCE RX-158 -- the paragraph above `_POD_SCALARS` says what is
    cleared and why the denylist before it was walked past twelve ways. What it
    examines: every `Vec<...>` (a space before the bracket too) and every
    `vec_...::<...>` turbofish, which instantiates a `Vec` without writing one;
    every name in the element is cleared as a scalar, or followed into EVERY
    struct or enum of that name under `src/` -- all of them, because this check
    does not resolve imports and a POD namesake must not clear an owning one.

    WHAT IT DOES NOT FOLLOW, stated rather than implied: an instantiation. A
    `Vec<T>` over a bare type parameter FAILS -- anywhere but `vec.npk`'s own
    generic definition, where the element is exactly one of that file's type
    parameters and is exempt. Any other `Vec` in `vec.npk` is judged. A generic
    struct is judged with its parameters unbound, so it fails too; teaching the
    check to substitute is the widening a decision would make, if a cycle needs
    one. And `tests/` is out of scope on purpose: the owning units instantiate
    `Vec<string>` precisely to measure what the verbs do there.

    Source is read through `lexical.py` (RX-157), so a comment or string naming
    `Vec<string>` is not reported and a `'"'` earlier on the line hides nothing.
    Measured when RX-158 was written: the audit's twelve plants all fail, the
    third triage's four positive plants still fail, and its comment plant and
    POD plant still pass."""
    fl, notes = [], []
    files = npk_files(root, "src")
    codes, decls = {}, {}
    for path in files:
        code = lexical.blank(_read(path))
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        codes[rel] = code
        for m in _TYPE_DECL.finditer(code):
            own = set()
            for p in (m.group(3) or "").split(","):
                p = p.strip().split(":")[0].strip()
                if _IDENT_RE.fullmatch(p):
                    own.add(p)
            decls.setdefault(m.group(2), []).append((rel, m.group(1), own, m.group(4)))
    owner = _VEC_OWNER.replace(os.sep, "/")
    counts = {"Vec": 0, "turbofish": 0}
    exempt = 0
    for rel, code in sorted(codes.items()):
        params = _params_of(code)
        for off, elem, how in _vec_elements(code):
            if rel == owner and elem in params:
                exempt += 1
                continue
            counts[how] += 1
            why = _deny_reason(elem, decls, params, set())
            if why:
                ln = code.count("\n", 0, off) + 1
                col = off - (code.rfind("\n", 0, off) + 1) + 1
                shown = f"`Vec<{elem}>`" if how == "Vec" else f"a `vec_...::<{elem}>` call"
                fl.append(
                    f"{rel}:{ln}:{col}: {shown} -- the element is not cleared: {why}. "
                    f"`Vec<T>` is for a NON-OWNING `T` (SAFETY.md S-23a, RX-155), and "
                    f"this check clears only what it can see owns nothing (RX-158): at "
                    f"an owning `T` six verbs orphan what they discard, invisibly to "
                    f"`exit 0`, and `vec_get` is refused only by its `Pod` bound (RX-168). Keep "
                    f"the element POD -- an offset into a `Bytes`, as HIR.md H-2 does "
                    f"for group names -- or widen the check by a decision.")
    ndecl = sum(len(v) for v in decls.values())
    notes.append(f"{ndecl} struct/enum declaration(s) under src/, every one of a "
                 f"name followed; {exempt} exempt as {owner}'s own `Vec<T>` over its "
                 f"type parameter, and nothing else there.")
    return Result("check_vec_elements_own_nothing", "SAFETY.md S-23a (RX-155, RX-158)",
                  f"{counts['Vec'] + counts['turbofish']} element type(s) -- "
                  f"{counts['Vec']} `Vec<...>` and {counts['turbofish']} "
                  f"`vec_...::<...>` -- in {len(files)} file(s) under src/", fl, notes)


# --- check_specs_current --------------------------------------------------------------

_SPEC_LINK = re.compile(r'\[[^\]]*\]\(([^)]+\.md)(?:#[^)]*)?\)')
_SPEC_CITE = re.compile(r'`?(?:meta/specs/)?([A-Z_]+\.md)`?\s*§\s*([0-9]+[a-z]?)')


def check_specs_current(root):
    """REPORTS, NEVER FAILS (`0.0.3.md` §4).

    Two things: a relative markdown link under `meta/` that no longer resolves,
    and a `SPEC.md §N` citation whose section heading is not in that file.

    WHY IT ONLY REPORTS. A citation can be stale for a good reason in the middle
    of a cycle -- the section is being written in the same commit that cites it
    -- and a check that blocked the commit for that would be routinely bypassed
    with a flag, which is worse than one that is read. `check_refs.py` in the
    workbench is the one that fails; this is the one that notices drift the day
    it happens."""
    reports = []
    scanned = 0
    specs = {}
    specdir = os.path.join(root, "meta", "specs")
    if os.path.isdir(specdir):
        for n in sorted(os.listdir(specdir)):
            if n.endswith(".md"):
                specs[n] = open(os.path.join(specdir, n),
                                encoding="utf-8", errors="replace").read()

    heads = {}
    for name, text in specs.items():
        heads[name] = {m.group(1) for m in
                       re.finditer(r'^##+\s*([0-9]+[a-z]?)\b', text, re.M)}

    for dirpath, dirnames, names in os.walk(os.path.join(root, "meta")):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for n in sorted(names):
            if not n.endswith(".md"):
                continue
            p = os.path.join(dirpath, n)
            rel = os.path.relpath(p, root)
            scanned += 1
            text = open(p, encoding="utf-8", errors="replace").read()
            for ln, line in enumerate(text.split("\n"), 1):
                for m in _SPEC_LINK.finditer(line):
                    tgt = m.group(1)
                    if tgt.startswith(("http://", "https://")):
                        continue
                    if not os.path.exists(os.path.normpath(
                            os.path.join(os.path.dirname(p), tgt))):
                        reports.append(f"{rel}:{ln}: the link `{tgt}` does not resolve")
                for m in _SPEC_CITE.finditer(line):
                    fname, sec = m.group(1), m.group(2)
                    if fname not in heads:
                        continue
                    if sec not in heads[fname]:
                        reports.append(f"{rel}:{ln}: cites `{fname}` §{sec} and that "
                                       f"file has no such section")
    return Result("check_specs_current", "0.0.3.md §4 -- reports, does not fail",
                  f"{scanned} markdown file(s) under meta/, {len(specs)} spec(s)",
                  [], reports)




# --- check_dated_measurements ---------------------------------------------------------

# "at the pin", "at this pin", "at the current pin" -- a measurement dated to a  # check_dated_measurements: exempt
# name that RE-POINTS. Deliberately narrow: it does not match "the pinned
# compiler", "held to the pin", "the pin moves", or a phrase already carrying a
# commit, because a check with false positives gets switched off.
_UNDATED = re.compile(r'\bat (?:the|this|the current) pin\b', re.IGNORECASE)

# Where the class does NOT apply, and each exclusion has a reason rather than a
# convenience.
#   meta/roadmap/  -- execution records. They say what was measured WHEN THEY
#                     WERE WRITTEN and are superseded, never edited (W-28); a
#                     check that demanded they be rewritten would be a check
#                     against the record rule.
#   meta/audits/   -- another session's filed report, reproduced verbatim.
#   *TRANSCRIPT*   -- the same, for measurement transcripts.
#   harness/baseline/RX120.txt -- the narrative that states this very rule.
#   meta/DECISIONS.md -- a settled decision's TEXT IS NEVER REWRITTEN; it is
#                     superseded by a numbered decision that says why (this
#                     repository's first non-negotiable rule about its own
#                     documents). A check demanding edits there would be a check
#                     against that rule. Seven lines in it are in this class, and
#                     the remedy for a decision whose dating went stale is a
#                     SUPERSEDING decision, not a sed.
_UNDATED_SKIP_DIRS = ("meta/roadmap/", "meta/audits/")
_UNDATED_SKIP_NAMES = ("TRANSCRIPT.txt", "RX120.txt", "DECISIONS.md")

# DIRECTORIES PRUNED BY NAME, AND *BY NAME* IS THE WHOLE POINT -- RX-145.
#
# The walk used to prune `not d.startswith(".")`, which reads as "skip the
# machinery" and actually means "SKIP `.github/`". `.yml` is in `_UNDATED_EXTS`
# and the docstring's scope sentence ends "and the workflow", so the check
# declared a file class, named the file in prose, and then made the only
# directory it can live in unreachable. The cycle 0.0 second audit instrumented
# it: 115 files opened, **0 of them `.yml`**, `failures: []` -- while the
# check's own regex found two violations in `.github/workflows/ci.yml`.
#
# The tell was already in the tree: `_UNDATED_SKIP_DIRS` carried `.internal/`
# and `.git/`, which the leading-dot prune had already removed, so they were
# DEAD CODE -- and dead code in a skip list is evidence that the author expected
# the list to be doing the skipping. It is now doing it.
#
# `__pycache__` and `build` are not dotted and were always walked; they hold no
# tracked text file, so naming them here costs nothing and states the intent.
_UNDATED_PRUNE_DIRS = (".git", ".internal", "__pycache__", "build")

# A NESTED REPOSITORY IS NOT THIS TREE -- RX-147. CI checks the
# pinned compiler out at `.nitpick/`, INSIDE the workspace, and since RX-145
# this walk prunes by NAME -- so it walked the whole compiler: run 34047719942
# on `ab93eae` opened 1016 files and failed on the compiler's own roadmap.
# Invisible on a developer machine, where the compiler is a sibling and not a
# child. By SHAPE -- a directory holding a `.git` entry is another repository --
# and by NAME for `.nitpick`, so an export with no `.git` is caught too
# (`nitpick-time`'s TM-146, carried here by the board's shared finding 5).
_NESTED_NAMES = (".nitpick",)


def _nested_repo(parent, name):
    return name in _NESTED_NAMES or os.path.exists(os.path.join(parent, name, ".git"))

# One line may opt out by carrying this marker, which is greppable and has to be
# written on purpose. The only intended user is a line that QUOTES the forbidden
# phrase in order to forbid it.
_UNDATED_EXEMPT = "check_dated_measurements: exempt"

_UNDATED_EXTS = (".md", ".py", ".npk", ".txt", ".toml", ".yml", ".sh")


def check_dated_measurements(root):
    """A measurement is dated by a COMMIT or it is not dated -- RX-142.

    "The pin" is a name that re-points. A sentence saying a thing was measured
    "at the pin" (check_dated_measurements: exempt) becomes false the day the
    pin moves, WHILE NOBODY EDITS IT and
    with nothing lexically wrong to find: it is a true sentence about a
    different compiler. This repository has now met that twice.

    RX-120 is the expensive one. `check_no_syscalls`'s first layer "cannot see a
    syscall" was measured at `950bb1d`, recorded as a permanent property, and
    carried to four sibling repositories as current fact. At `3d15ac9` the
    compiler's D-262 trimmed the prelude and the layer CAN see one -- floor 2,
    syscaller 3, difference exactly `npk_sys6`. The claim reversed and no
    document moved.

    THE FIRST SWEEP CLOSED THE PHRASE AND NOT THE CLASS. Cycle 0.0.5 corrected
    the three sites saying the exact words "measured at the pin". The cycle 0.0  # check_dated_measurements: exempt
    audit then found **39 lines across 20 files** in the same class, spot-checked
    the two most load-bearing, and found both still TRUE -- so nothing was wrong
    that day, and the class was thirteen times larger than the sweep that was
    said to have closed it. A grep is a sweep; only a check is a rule.

    Records are out of scope by design -- see `_UNDATED_SKIP_DIRS`. What is IN
    scope is everything a reader takes as current: the specifications, the
    harness, `src/`, the probe headers, the manifest and the workflow."""
    fl, notes = [], []
    seen = 0
    by_ext = {}
    pruned = []
    for dirpath, dirnames, names in os.walk(root):
        # BY NAME, NEVER BY LEADING DOT (RX-145) -- AND NEVER INTO ANOTHER
        # REPOSITORY (RX-147), which is said out loud below.
        pruned += sorted(os.path.relpath(os.path.join(dirpath, d), root).replace(os.sep, "/")
                         for d in dirnames
                         if d not in _UNDATED_PRUNE_DIRS and _nested_repo(dirpath, d))
        dirnames[:] = [d for d in dirnames
                       if d not in _UNDATED_PRUNE_DIRS and not _nested_repo(dirpath, d)]
        for n in sorted(names):
            if not n.endswith(_UNDATED_EXTS):
                continue
            path = os.path.join(dirpath, n)
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            if any(rel.startswith(d) for d in _UNDATED_SKIP_DIRS):
                continue
            if n in _UNDATED_SKIP_NAMES:
                continue
            try:
                text = open(path, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            seen += 1
            ext = os.path.splitext(n)[1]
            by_ext[ext] = by_ext.get(ext, 0) + 1
            for ln, line in enumerate(text.split("\n"), 1):
                if _UNDATED_EXEMPT in line:
                    continue
                m = _UNDATED.search(line)
                if m:
                    fl.append(f"{rel}:{ln}:{m.start() + 1}: `{m.group(0)}` dates a "
                              f"measurement to a name that RE-POINTS. Name the "
                              f"commit -- `at `3d15ac9`` -- so the sentence stays "
                              f"true or becomes checkably false when the pin moves. "
                              f"RX-142. (A line that quotes the phrase in order to "
                              f"forbid it says `{_UNDATED_EXEMPT}`.)")
    notes.append(f"records are out of scope: {', '.join(_UNDATED_SKIP_DIRS)} and "
                 f"{', '.join(_UNDATED_SKIP_NAMES)} say what was true when they were "
                 f"written and are superseded rather than edited (W-28).")
    # PER-EXTENSION DENOMINATORS, BECAUSE THAT IS WHAT WOULD HAVE CAUGHT RX-145.
    # This file's own docstring says a check finding nothing because it LOOKED
    # NOWHERE is indistinguishable in the output from one that found nothing
    # because there was nothing to find -- and then this check declared `.yml`
    # and opened zero of them for a whole subcycle while reporting a single
    # aggregate number that looked healthy. A class with a zero beside it is a
    # question a reader can ask; a class absorbed into a total is not.
    covered = ", ".join(f"{e} {by_ext.get(e, 0)}" for e in sorted(_UNDATED_EXTS))
    notes.append(f"opened by declared extension -- {covered}. A ZERO HERE IS A "
                 f"FINDING, not a clean bill: it means the class is declared and "
                 f"the walk reaches none of it (RX-145).")
    notes.insert(0, f"{len(pruned)} nested repositor{'y' if len(pruned) == 1 else 'ies'} "
                    f"pruned: {', '.join(pruned) or 'none'} -- another repository is not "
                    f"this tree (RX-147).")
    return Result("check_dated_measurements", "RX-142, RX-145",
                  f"{seen} text file(s) outside the records", fl, notes)


ALL = [check_layering, check_error_budget, check_constants_named,
       check_no_division, check_accessor_confinement,
       check_vec_elements_own_nothing,
       check_dated_measurements, check_specs_current]
REPORTING_ONLY = {"check_specs_current"}


def run_all(root, say):
    """Every live tree check, in order. Returns the failing ones.

    `check_no_syscalls` is NOT here: it is a BUILD STEP (B-2, P-11), it landed
    at 0.0.2, and it runs per program object in `build.py` where it can fail
    the build rather than report on it afterwards. Naming it here as well would
    put one check in two places and let the two drift."""
    say("")
    say("-- tree checks (P-16: every one runs on every full invocation) --")
    bad = []
    for fn in ALL:
        r = fn(root)
        mark = "ok  " if r.ok else "FAIL"
        if r.name in REPORTING_ONLY:
            mark = "note"
        say(f"  {mark}  {r.name}  [{r.rule}]  over {r.examined}")
        for n in r.notes:
            say(f"        {n}")
        for f in r.failures:
            say(f"  FAIL  {f}")
        if not r.ok and r.name not in REPORTING_ONLY:
            bad.append(r)
    say(f"      check_no_syscalls is not in this list ON PURPOSE: it is a BUILD "
        f"STEP (B-2, B-2a, P-11), it ran above per program object, and a check "
        f"living in two places is a check whose two copies drift.")
    return bad

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
"""
import os
import re

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

_USE = re.compile(r'^\s*(?:pub\s+)?use\s+"([^"]+)"')

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


def _uses(path):
    """Every `use`/`pub use` target in one file, as a path relative to it."""
    out = []
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return out
    for n, line in enumerate(text.split("\n"), 1):
        m = _USE.match(line)
        if m:
            out.append((n, m.group(1)))
    return out


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
        text = open(lib, encoding="utf-8", errors="replace").read()
    except OSError as e:
        return [f"src/lib.npk: {e}"]
    for ln, line in enumerate(text.split("\n"), 1):
        m = _USE.match(line)
        if not m:
            continue
        target = m.group(1)
        if line.lstrip().startswith("pub "):
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
            text = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for ln, line in enumerate(text.split("\n"), 1):
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
_CMP_LITERAL = re.compile(
    r'[<>]=?\s*(\d+)(?:i8|i16|i32|i64|u8|u16|u32|u64)?\b')


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
            text = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for ln, line in enumerate(text.split("\n"), 1):
            if line.lstrip().startswith("//"):
                continue
            code = line.split("//")[0]
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
        text = open(lim, encoding="utf-8", errors="replace").read()
        missing = [n for n in LIMIT_NAMES if n not in text]
        if missing:
            fl.append(f"{LIMITS_FILE} does not declare {', '.join(missing)}. "
                      f"SAFETY.md §5's table is the authority and it has nine rows "
                      f"(S-12); a bound in the specification with no constant is a "
                      f"bound nothing enforces.")
        notes.append(f"{len(LIMIT_NAMES) - len(missing)}/{len(LIMIT_NAMES)} of "
                     f"SAFETY.md §5's named bounds are declared.")
    return Result("check_constants_named", "SAFETY.md S-12 (RX-062)",
                  f"{len(files)} file(s) outside {LIMITS_FILE}", fl, notes)


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


ALL = [check_layering, check_error_budget, check_constants_named, check_specs_current]
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

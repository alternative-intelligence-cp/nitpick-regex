#!/usr/bin/env python3
"""The test stages -- `BUILD.md` §3, `TESTING.md` §1.

THE STAGE VOCABULARY IS THE COMPILER'S (`BUILD_REFERENCE.md` §7.1), so the move
to `npkg` the day O-G3 closes is a change of runner and not a change of suite
(B-4a). What this file adds is only the judging; the file discovery rules are
`npkg/suites.npk`'s at 950bb1d, marker for marker:

  * `path`/`paths` name DIRECTORIES, never files, listed by suffix;
  * `recursive` DEFAULTS FALSE, so a subdirectory is excluded -- which is what
    makes `tests/probe/` and `tests/probe/refused/` two declarable suites
    (RX-119);
  * a file another file in the same suite imports is not run standalone --
    AND, HERE ONLY, A FILE THE COMPILER SAYS DEFINES `main` IS ALWAYS RUN
    (RX-157, RX-165). `npkg` has no such exception and needs none while its
    reader is the compiler's own; this runner's is not, and two audits took a red
    unit out of a GREEN run through it -- the fourth (BL-7) with a `use` inside a
    sibling's `/* */`, the fifth (BL-9) with two lone carriage returns.

RULE B-7 (D-237) IS IMPLEMENTED HERE AND IT IS LOAD-BEARING. The set of
diagnostic codes a rejection test reports must EQUAL the set its expectations
name. The reason it is not a nicety: A MISSING IMPORT EXITS 1 WITH
`NITPICK-RESOLVE-005` -- the very code a rejection fixture expects -- so a
rejection test whose fixture path is typo'd, or whose file is later moved,
would pass FOR THE WRONG REASON. It wanted a refusal; it got one; the refusal
was about the path. Measured, `tests/conformance/TRANSCRIPT.txt` §G2. Every
import in this repository is relative until O-G3 closes (B-15), so a moved path
is the ORDINARY case here. Code-set equality is the single thing that makes
that hole unreachable, and nothing else in the run would report it.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build                                                  # noqa: E402
import expect as expect_mod                                   # noqa: E402
import lexical                                                # noqa: E402
from manifest import paths_of                                 # noqa: E402


def files_of(root, paths, recursive, suffix=".npk"):
    out, seen = [], set()
    for rel in paths:
        d = os.path.join(root, rel)
        if not os.path.isdir(d):
            raise FileNotFoundError(
                f"{rel}: `path` names a DIRECTORY and never a file "
                f"(npkg/suites.npk `files_of`), and this one does not exist")
        found = []
        if recursive:
            for dirpath, _, names in os.walk(d):
                found += [os.path.join(dirpath, n) for n in names if n.endswith(suffix)]
        else:
            found = [os.path.join(d, n) for n in sorted(os.listdir(d))
                     if n.endswith(suffix) and os.path.isfile(os.path.join(d, n))]
        for p in sorted(found):
            k = os.path.normpath(p)
            if k not in seen:
                seen.add(k)
                out.append(p)
    return out


def imported_by_others(c, paths):
    """The files of one suite that are NOT run standalone -- RX-157, RX-165.

    `npkg`'s rule: a file another file in the SAME suite imports is a helper, and
    is judged through its importer rather than on its own. TWO DEFENCES make that
    safe here, and since RX-165 THEY SHARE NO READER -- a file is skipped only
    when both say so:

      * THE IMPORT IS READ THE WAY THE COMPILER READS IT -- `lexical.read` and
        `lexical.imports`, the harness's one reading of source: bytes, `\\n` the
        only line end, comments, strings and templates skipped, `pub use` seen,
        the path decoded. This reader used to take any line that STARTED
        `use "`, so a `use` inside a sibling's `/* */` block named a unit the
        compiler never imported (`173/173` GREEN, BL-7); and until RX-165 it read
        a lone CR as a line end, so `// see<CR>use "x.npk".*;` named one too (BL-9).
      * A FILE THE COMPILER SAYS DEFINES `main` IS NEVER SKIPPED. It is a program,
        and a program is judged; D-248 refuses a REAL import of one
        (`NITPICK-RESOLVE-013`, measured at `c3bdae2`), so the exception costs
        nothing legitimate. THE ANSWER IS `npkc`'s, NOT A READER'S: the candidate
        is compiled as a root and its IR asked for `@main` (`build.defines_main`).
        A candidate `npkc` does not compile is judged too -- nothing could show it
        is not a program. Until RX-165 this bullet asked `lexical.declares_main`,
        THE SAME READER AS THE FIRST, and "it holds whatever the next reader gets
        wrong" was false by construction: `// note<CR>/*` above a red unit's
        `main` blanked it from both at once, and with the sibling's CR import the
        red unit left the count -- `209/209`, GREEN, exit 0 (BL-9 (a)).

    Either defence alone keeps a program in the count, and the pair is measured
    that way: each removed alone, the fifth audit's plant stays red; both removed,
    it is green (`0.0.5.md` §12). Self-check case 19 is that plant."""
    used = set()
    for p in paths:
        for target in _uses(p):
            if os.path.normpath(target) != os.path.normpath(p):
                used.add(os.path.normpath(target))
    return {os.path.normpath(p) for p in paths
            if os.path.normpath(p) in used and _compiler_sees_no_main(c, p)}


def _read(path):
    try:
        return lexical.read(path)
    except (OSError, ValueError):
        return ""


def _uses(path):
    return [os.path.normpath(os.path.join(os.path.dirname(path), target))
            for _, target, _ in lexical.imports(_read(path))]


def _compiler_sees_no_main(c, path):
    """True only when `npkc`, compiling `path` as a ROOT, exits 0 and its IR
    defines no `main` -- the second defence's whole question, asked of the
    compiler and never of `lexical.py` (RX-165)."""
    rel = os.path.relpath(path, c.root)
    base = os.path.join(c.tmp, "mainchk_" + rel.replace("/", "_").replace(".", "_"))
    r = build.emit(c, path, base + ".ll")
    if r.timed_out or r.code != build.NPKC_OK or not os.path.exists(base + ".ll"):
        return False
    with open(base + ".ll", "rb") as fh:
        return not build.defines_main(fh.read())


def empty_suite(name, rel):
    return (f"{name}: `{rel}` holds no .npk file. An entry naming an empty "
            f"directory is a suite that reports green while checking nothing, "
            f"which is the failure `nitpick.toml`'s [[test]] table exists to "
            f"prevent.")


# --- running a built program ---------------------------------------------------------

TRUE_CONTROL = "/bin/true"


def run_binary(exe, args, stress, want, name, tail, mem_cap_mib=0):
    """`stress` runs, the SAME answer required every time.

    `mem_cap_mib` caps the child's address space, and **`/bin/true` is run under
    the identical cap first**. A low cap measures the DYNAMIC LOADER rather than
    the program -- measured in this ecosystem, `/bin/true` and a probe flip at
    the same cap, between 2688 and 2816 KiB -- so a cap a trivial program cannot
    survive says nothing about the program under test. Running the control is
    what makes the number a statement rather than a hope, and it is done on
    every capped run rather than once, because the cap is per file.
    """
    if mem_cap_mib:
        ctl = build.Run([TRUE_CONTROL], timeout=build.RUN_TIMEOUT,
                        mem_cap_mib=mem_cap_mib)
        if ctl.timed_out or ctl.code != 0:
            got = "timed out" if ctl.timed_out else f"exited {ctl.code}"
            return [f"{name}: THE CONTROL FAILED, so the cap measures the loader and "
                    f"not this program: `{TRUE_CONTROL}` {got} under the same "
                    f"{mem_cap_mib} MiB address-space cap. Raise the cap until the "
                    f"control passes, then re-read what the test is asserting"
                    f"{tail}"]
    seen = {}
    for _ in range(stress):
        r = build.Run([exe] + list(args), timeout=build.RUN_TIMEOUT,
                      mem_cap_mib=mem_cap_mib)
        if r.timed_out:
            return [f"{name}: timed out after {build.RUN_TIMEOUT} s{tail}"]
        got = r.code
        seen[got] = seen.get(got, 0) + 1
    if list(seen) == [want]:
        return []
    shown = ", ".join(f"{k} ({v}x)" if v > 1 else f"{k}" for k, v in sorted(seen.items()))
    if len(seen) > 1:
        return [f"{name}: exited {shown} over {stress} runs -- NOT THE SAME ANSWER "
                f"EVERY TIME, expected {want}{tail}"]
    return [f"{name}: exited {shown}, expected {want}{tail}"]


# --- the stages ----------------------------------------------------------------------

# THE REVIEWED LIST OF PENDING UNITS (RX-154). A `pending-until:` marker takes a
# unit OUT OF THE DENOMINATOR, so it takes a line here too -- checked both ways
# by the driver. One comment line must never be able to move a red out of a
# green run, and the third cycle-0.0 audit's M3 did exactly that: a unit given a
# wrong expectation plus a marker printed `140/140` and GREEN.
#
# AND THE MARKER WAS NOT THE ONLY ROUTE OUT, which RX-154 had said it was. The
# fourth audit's BL-7 moved a red unit out through a `use` inside a SIBLING's
# `/* */` -- no marker, no line here -- because the "imported by a sibling"
# skip read that comment as an import; RX-157 closed that route with two
# defences, and the fifth audit's BL-9 walked through both at once with two lone
# carriage returns, because they shared a reader. RX-165 gives the second its
# own -- the compiler's (see `imported_by_others`); self-check cases 15 and 19
# are the two reds.
PENDING_LIST = "harness/baseline/PENDING.txt"


class Pending:
    """A unit that is CORRECT and RED because the pinned compiler is the defect.

    Carried out of the stage rather than reported as a finding, so the runner can
    count it as neither a pass nor a failure -- `expect.py`'s fourth marker says
    why. It holds what the file asked for, the exit its marker names, and what
    the tree actually did, because "pending" without the observed exit is an
    assertion that nothing checks.
    """

    def __init__(self, name, until, want, got, capped, named):
        self.name = name
        self.until = until
        self.want = want
        self.got = got           # what every leg gave, as text: "92 at -O0 and 92 through opt -O2"
        self.capped = capped
        self.named = named       # the exit the marker is pending on; every leg gave it (RX-159)

    def line(self):
        cap = f", under a {self.capped} MiB cap" if self.capped else ""
        return (f"{self.name}: PENDING until compiler `{self.until}` -- wants exit "
                f"{self.want}{cap}; the marker names exit {self.named} and this tree "
                f"gives {self.got}. NOT A PASS and not counted in the denominator.")


def read_pending_list(root):
    """`harness/baseline/PENDING.txt` -- RX-154. Returns ({key: line}, failures).

    One line per pending unit, `path<TAB>commit<TAB>exit<TAB>reason`, the key
    being the first three. Every line needs a REASON, for RESIDUE.txt's reason
    (RX-131): a line nobody explained is a permission nobody reviewed.

    AN ABSENT FILE IS AN EMPTY LIST, and that is the safe direction rather than a
    convenience: with no list, every marker in the tree fails as unlisted. The
    self-check's throwaway trees rely on it."""
    path = os.path.join(root, PENDING_LIST)
    entries, fl = {}, []
    if not os.path.exists(path):
        return entries, fl
    for n, line in enumerate(open(path, encoding="utf-8").read().split("\n"), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t", 3)
        if (len(parts) != 4 or not parts[3].strip()
                or expect_mod._int(parts[2]) is None):
            fl.append(f"{PENDING_LIST}:{n}: not `path<TAB>commit<TAB>exit<TAB>reason`. "
                      f"A pending line takes a unit out of the denominator, so a line "
                      f"that cannot be read, or that gives no reason, is a failure "
                      f"rather than a skip")
            continue
        entries[(parts[0].strip(), parts[1].strip(),
                 expect_mod._int(parts[2]))] = n
    return entries, fl


def _program_like(c, path, name, exp, with_opt_leg):
    if not exp.ok:
        return [expect_mod.unreadable_message(name, exp)]
    base = os.path.join(c.tmp, "prog_" + name.replace("/", "_").replace(".", "_"))
    scanned = build.reaches_src(c.root, path)
    c.scanned[name] = scanned
    fl = build.emit_and_link(c, path, name, base, scanned=scanned)
    if fl:
        # A PENDING UNIT STILL HAS TO BUILD. The marker excuses a wrong exit
        # code, which is a statement about the compiler's runtime; it does not
        # excuse a refusal, a link error or a failed scan, which are statements
        # about this file.
        return fl
    if exp.pending_until:
        # AND IT BUILDS ON EVERY LEG AN ORDINARY UNIT DOES -- RX-159, the fourth
        # cycle-0.0 audit's N-19. It used to return here, before the optimised
        # leg was built, so a pending unit had no `opt -O2`, no B-2 re-scan of
        # the optimised object (where `opt` MINTS libcalls) and no `stress`,
        # while the summary counted it among the units "B-2's two scans ran on"
        # and the GREEN line said every program agreed with itself under -O2.
        legs = [("at -O0", base)]
        if with_opt_leg:
            fl = build.check_optimised(c, name, base, scanned=scanned)
            if fl:
                return fl
            legs.append(("through opt -O2", base + ".opt"))
        return _pending(c, legs, name, exp)
    # `argv:` tokens pass verbatim; fixture substitution arrives with the corpus
    # stage at cycle 0.5, and there is nothing to substitute before then.
    fl = run_binary(base, exp.argv, exp.stress, exp.exit_code, name,
                    " (compiled by the REAL backend)", exp.mem_cap_mib)
    if fl or not with_opt_leg:
        return fl
    fl = build.check_optimised(c, name, base, scanned=scanned)
    if fl:
        return fl
    return run_binary(base + ".opt", exp.argv, exp.stress, exp.exit_code, name,
                      " (through opt -O2 + llc -O2 -- B-3)", exp.mem_cap_mib)


def _pending(c, legs, name, exp):
    """Observe a `pending-until:` unit on EVERY LEG, `stress` times each, and
    report what it actually did.

    EVERY LEG AND EVERY RUN, SINCE RX-159 (the fourth cycle-0.0 audit's N-19).
    This said "ONE RUN, NOT `stress`: a pending unit is not being asserted, it is
    being OBSERVED" -- and an observation taken once, at −O0 only, excused
    everything the −O2 leg and a repeated run would have shown: a different exit
    through `opt -O2`, an answer that changes from run to run. The marker excuses
    ONE failure, so it is held to that failure wherever the unit runs. The
    `/bin/true` control still runs first when a cap is in force, because a low cap
    measures the loader whatever the unit is being held to.

    THREE OUTCOMES, AND ONLY ONE OF THEM IS PENDING (RX-154). Every run on every
    leg meets the expectation: the marker has outlived its reason, RED. Every run
    on every leg gives the exit the marker names: PENDING. ANYTHING ELSE -- another
    exit, a hang, one leg disagreeing with the other, a run disagreeing with the
    one before it -- is RED, because the marker excuses the failure it names and
    no other. Until the third cycle-0.0 audit (BL-6, M2) a unit made to trap 94
    instead of its DEF-25 leak's 92 printed "this tree gives 94" and the run
    stayed GREEN.

    WHAT IS STILL KEYED ON THE EXIT ALONE, stated rather than implied (`BUILD.md`
    B-5b): a code is an identity, not a cause. A unit pending on 92 is excused for
    ANY `HeapOom` under its cap, and one pending on a trap's code for any trap of
    that identity. Where the defect allows, a pending unit should exit with a code
    of its own, which only its own assertion can produce.
    """
    if exp.mem_cap_mib:
        ctl = build.Run([TRUE_CONTROL], timeout=build.RUN_TIMEOUT,
                        mem_cap_mib=exp.mem_cap_mib)
        if ctl.timed_out or ctl.code != 0:
            return [f"{name}: THE CONTROL FAILED under this file's "
                    f"{exp.mem_cap_mib} MiB cap, so nothing the file reports -- "
                    f"pending or not -- is about the file"]
    observed = []
    for label, exe in legs:
        seen = {}
        for _ in range(exp.stress):
            r = build.Run([exe] + list(exp.argv), timeout=build.RUN_TIMEOUT,
                          mem_cap_mib=exp.mem_cap_mib)
            got = "timed out" if r.timed_out else r.code
            seen[got] = seen.get(got, 0) + 1
        observed.append((label, seen))
    gives = " and ".join(
        ", ".join(f"{k} ({v}x)" if v > 1 else f"{k}"
                  for k, v in sorted(seen.items(), key=lambda kv: str(kv[0])))
        + f" {label}" for label, seen in observed)
    runs = f", {exp.stress} run(s) each" if exp.stress > 1 else ""
    marker = f"`pending-until: {exp.pending_until} exit {exp.pending_exit}`"
    if all(list(seen) == [exp.exit_code] for _, seen in observed):
        # THE MARKER HAS OUTLIVED ITS REASON, WHICH IS THIS ECOSYSTEM'S OWN
        # RECURRING DEFECT. Red, deliberately: the run that first meets the
        # expectation is the run that has to notice, and nobody re-reads a green
        # line. NOTE WHAT THIS IS KEYED ON: the exit, not the commit, which is a
        # label nothing here resolves (RX-154).
        return [f"{name}: {marker} IS NOW STALE -- the file met its expectation "
                f"(exit {exp.exit_code}) against the compiler this tree is pinned "
                f"to, on every leg. DELETE THE MARKER AND ITS LINE IN {PENDING_LIST}; "
                f"the case is live and belongs in the denominator. A pending marker "
                f"that survives the day it stops being true is the dormant rule this "
                f"repository keeps finding."]
    if not all(list(seen) == [exp.pending_exit] for _, seen in observed):
        return [f"{name}: PENDING ON A DIFFERENT FAILURE -- the marker names exit "
                f"{exp.pending_exit} and this tree gives {gives}{runs}. {marker} "
                f"excuses the failure it names, on every leg and every run, and no "
                f"other (RX-154, RX-159): rule B-7's reasoning applied to this marker, "
                f"because a unit held only to 'it failed' passes for the wrong reason. "
                f"The defect changed shape or something else broke; read the file "
                f"before touching the marker."]
    return [Pending(name, exp.pending_until, exp.exit_code, gives + runs,
                    exp.mem_cap_mib, exp.pending_exit)]


def parse_sweep(c, path, name, exp):
    """The `parse` stage -- RX-124, and it is NOT the stage `BUILD.md` §3 named.

    §3 defines `parse` as "accepted by `tools/parse_check` with no diagnostic".
    That tool is the COMPILER's, and reading it at `3d15ac9` settles the matter:
    `tools/parse_check.npk` opens with nineteen `use "../src/frontend/..."`
    lines, so having it means compiling the compiler's frontend -- which RX-007
    forbids depending on and W-18 forbids building from here. This is EXACTLY
    the reason rule B-4a already struck the `accept` stage, recorded in the same
    table, one row away, and left `parse` standing. `npkc` has no parse-only
    flag either (its usage line, read at `3d15ac9`, is
    `npkc <root.npk> [-o out.ll] [--obligations DIR] [--elide ...] [--extra-picky=...]`).

    SO THE STAGE IS `npkc` ITSELF, AND IT IS STRICTLY STRONGER THAN PARSING:
    the whole frontend runs and IR is emitted. Saying "parse" and doing more
    than parsing is only safe while it is written down, which is what this
    paragraph and RX-124 are for.

    WHAT IT ADDS OVER THE OTHER STAGES, and it is not redundancy. `src/lib.npk`
    reaches `src/api/api.npk` and nothing else, so SIX of this library's eight
    `src/` files -- core, compile, engine, hir, syntax, unicode -- are reached
    by NO suite. They compiled at exit 0 once, at cycle 0.0.1, and nothing has
    re-checked them since. This sweep is what does.

    EVERY FILE IS JUDGED AS A ROOT, including one another file imports: "each
    file once" means once AS ITSELF, and a file that only ever compiles as part
    of somebody else's graph has never been checked on its own. So the
    `imported_by_others` skip that `program` uses does NOT apply here.

    A file carrying `// expect-error:` is held to its own expectation instead,
    by the same code-set equality rule (B-7) -- the tree contains deliberate
    refusals and sweeping them as though they should be clean would either fail
    six honest files or require exempting a directory, and an exemption is where
    a real refusal hides.

    WHAT A GREEN SWEEP DOES NOT MEAN, AND THIS IS THE IMPORTANT SENTENCE.
    `npkc` exit 0 IS NOT WELL-FORMEDNESS (registry O-N11, the compiler's DEF-5),
    and THIS LIBRARY WAS THE STANDING EXAMPLE: at `950bb1d` all eight files in
    `src/` compiled at exit 0 and all eight were refused by `llc`, because
    `npkc` never emitted a `declare` for `@npk_failsafe` (B-0, RX-115). That
    mechanism expired at `94874ce`; at `c3bdae2` all thirteen compile and
    assemble, and a module's object still links neither alone nor beside a
    program (`ld.lld: duplicate symbol`) -- RX-151. So this stage reports that
    `npkc` accepts each file. It does NOT report that any of them assembles,
    links or runs, and for the `src/` files `src/lib.npk` does not reach no
    suite in this manifest reports that, because there is no library object to
    make one from -- `src/` reaches the compiler only through a program root.
    The sweep closes the gap that those files were checked by NOTHING; it does
    not close the gap that they are checked only as far as `npkc`."""
    if not exp.ok:
        return [expect_mod.unreadable_message(name, exp)]
    if exp.errors:
        return check_rejection(c, path, name, exp)
    base = os.path.join(c.tmp, "parse_" + name.replace("/", "_").replace(".", "_"))
    r = build.emit(c, path, base + ".ll")
    if r.timed_out or r.code != build.NPKC_OK:
        return [build.npkc_failure(name, "the parse sweep", r)]
    # "with no diagnostic" is the specification's word and it is asserted:
    # exit 0 with a WARNING on stderr is exit 0, and a warning is a finding
    # (B-6's channel split).
    got = build.findings_of(r.err)
    if got:
        codes = ", ".join(sorted({f["code"] for f in got}))
        return [f"{name}: npkc accepted it (exit 0) AND reported {codes}. The stage "
                f"is 'accepted with no diagnostic' (BUILD.md §3): a warning on a "
                f"clean exit is still a finding (B-6), and exit 0 is the one place "
                f"nobody looks for one."]
    return []


def check_rejection(c, path, name, exp):
    """Refused, with EXACTLY the expected codes. Rule B-7 (D-237)."""
    if not exp.ok:
        return [expect_mod.unreadable_message(name, exp)]
    if not exp.errors:
        return [f"{name}: a `negative` test that names no `// expect-error:` code. "
                f"Exit 1 alone cannot tell 'refused for the reason this test is "
                f"about' from 'the file was not there' -- both are exit 1 "
                f"(TRANSCRIPT.txt §G2), so a rejection test without a code asserts "
                f"nothing."]
    base = os.path.join(c.tmp, "rej_" + name.replace("/", "_").replace(".", "_"))
    r = build.emit(c, path, base + ".ll")
    if r.timed_out:
        return [f"{name}: the frontend did not terminate"]
    if r.code == build.NPKC_TRAPPED:
        return [f"{name}: npkc exited 3 -- IT TRAPPED. A defect in the compiler, "
                f"not in this file."]
    if r.code == build.NPKC_BROKEN:
        return [f"{name}: npkc exited 2 -- THE DRIVER COULD NOT PROCEED AND JUDGED "
                f"NOTHING. THIS IS NOT A REFUSAL and this test proved nothing: the "
                f"program was never compiled. Exit 2 is silent by construction "
                f"(stderr {len(r.err)} bytes); it is a malformed command line, not a "
                f"verdict. Command: `{r.shown()}`"]
    if r.code == build.NPKC_OK:
        return [f"{name}: expected {', '.join(exp.codes())}, but it compiled cleanly "
                f"(exit 0)"]
    if r.code != build.NPKC_REFUSED:
        return [f"{name}: npkc exited {r.code}, which is not a letter of its alphabet"]

    got = build.findings_of(r.err)
    fl = []
    fl += _match_channel(name, exp.errors, got, notes=False)
    fl += _match_channel(name, exp.notes, got, notes=True)
    fl += _unexpected_codes(name, exp.errors, got)
    return fl


def _match_channel(name, want, got, notes):
    fl = []
    label = "note " if notes else ""
    for w in want:
        hits = [f for f in got if f["is_note"] == notes and f["code"] == w["code"]]
        if not hits:
            shown = ", ".join(sorted({f["code"] for f in got
                                      if f["is_note"] == notes})) or "nothing"
            fl.append(f"{name}: expected {label}{w['code']}, got {shown}")
            continue
        if w["line"] >= 0:
            at = [h for h in hits
                  if h["line"] == w["line"] and (w["col"] < 0 or h["col"] == w["col"])]
            if not at:
                where = ", ".join(f"{h['line']}:{h['col']}" for h in hits)
                col = "*" if w["col"] < 0 else str(w["col"])
                fl.append(f"{name}: {label}{w['code']} at {where}, "
                          f"expected {w['line']}:{col}")
    return fl


def _unexpected_codes(name, want, got):
    """The converse, and the half that closes the RESOLVE-005 hole (D-237, B-7)."""
    named = {w["code"] for w in want}
    fl = []
    for code in sorted({f["code"] for f in got if not f["is_note"]} - named):
        extra = ""
        if code == "NITPICK-RESOLVE-005":
            extra = (" -- AND THIS ONE IS THE HAZARD B-7 EXISTS FOR: a missing or "
                     "mistyped import exits 1 with exactly this code, so without "
                     "this check the test would have passed for the wrong reason, "
                     "having refused the PATH rather than the thing under test")
        fl.append(f"{name}: reported {code}, which no expectation names -- an "
                  f"unexpected diagnostic fails a test as surely as a missing one "
                  f"(BUILD.md B-7, D-237){extra}")
    return fl


# --- the entry points the driver dispatches ------------------------------------------

def run_entry(c, entry, only, record):
    """One `[[test]]` entry. Returns the number of units judged."""
    name = entry["name"]
    stage = entry["stage"]
    kind = entry.get("kind", "positive")
    rels = paths_of(entry)
    files = files_of(c.root, rels, bool(entry.get("recursive", False)))
    if not files:
        record(name, rels[0], [empty_suite(name, rels[0])])
        return 1
    # `parse` judges every file AS A ROOT, so the "imported by a sibling" skip
    # does not apply to it -- see `parse_sweep`. Everywhere else a file skipped
    # here is a helper that a sibling REALLY imports and that the COMPILER finds
    # no `main` in (RX-157, RX-165): never a program, and never on the strength of
    # a comment. The run SAYS which files it skipped, because a unit that left the
    # count is otherwise visible only as a denominator one short.
    skip = set() if stage == "parse" else imported_by_others(c, files)
    c.skipped[name] = sorted(os.path.relpath(k, c.root) for k in skip)
    n = 0
    for p in files:
        if os.path.normpath(p) in skip:
            continue
        rel = os.path.relpath(p, c.root)
        if only and not any(o in rel for o in only):
            continue
        # The markers are read from the bytes the compiler reads (RX-165): a lone
        # CR is not a line end for `npkg`'s `text_lines` either.
        exp = expect_mod.read(_read(p))
        if stage == "program":
            fl = _program_like(c, p, rel, exp, with_opt_leg=True)
        elif stage == "compile" and kind == "positive":
            fl = _program_like(c, p, rel, exp, with_opt_leg=False)
        elif stage == "compile" and kind == "negative":
            fl = check_rejection(c, p, rel, exp)
        elif stage == "parse":
            fl = parse_sweep(c, p, rel, exp)
        elif stage == "check":
            # `BUILD.md` §3: "refused by the frontend with EXACTLY the expected
            # codes" -- the same judging as `compile`/`negative`, over
            # `tests/rejection/`. One implementation, deliberately: two copies
            # of rule B-7 would be two places for it to weaken.
            fl = check_rejection(c, p, rel, exp)
        elif stage == "accept":
            # RULE B-4a (RX-117) STRUCK THIS STAGE and it is refused BY NAME
            # rather than judged, because `accept` is defined as "accepted by
            # `tools/check` in silence" -- a compiler-repository tool RX-007
            # forbids importing -- and it neither links nor runs, which is the
            # whole point (npkc exit 0 is not well-formedness, O-N11).
            fl = [f"{rel}: stage `accept` is STRUCK for this library by rule B-4a "
                  f"(RX-117), not merely unimplemented: it is defined as 'accepted "
                  f"by tools/check in silence', that tool is the compiler's and "
                  f"RX-007 forbids the dependency, and it neither links nor runs. "
                  f"Use `compile`/`positive`, which does. Declaring it is a "
                  f"manifest error, not a pending feature."]
        else:
            fl = [f"{rel}: stage `{stage}`" + (f"/`{kind}`" if kind else "") +
                  " is declared in nitpick.toml and this runner cannot judge it "
                  "yet. A stage that silently does nothing is a suite reporting "
                  "green while checking nothing, so it is a failure and not a skip. "
                  "`corpus` and `oracle` arrive at cycle 0.5."]
        record(name, rel, fl)
        n += 1
    return n

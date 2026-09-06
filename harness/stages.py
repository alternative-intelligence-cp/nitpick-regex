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
  * a file another file in the same suite imports is not run standalone.

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
from manifest import paths_of                                 # noqa: E402

_USE = 'use "'


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


def imported_by_others(paths):
    """A file another file in the SAME SUITE imports is not run standalone."""
    used = set()
    for p in paths:
        for target in _uses(p):
            if os.path.normpath(target) != os.path.normpath(p):
                used.add(os.path.normpath(target))
    return used


def _uses(path):
    out = []
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return out
    for line in text.split("\n"):
        s = line.strip()
        if not s.startswith(_USE):
            continue
        rest = s[len(_USE):]
        end = rest.find('"')
        if end < 0:
            continue
        out.append(os.path.normpath(os.path.join(os.path.dirname(path), rest[:end])))
    return out


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

def _program_like(c, path, name, exp, with_opt_leg):
    if not exp.ok:
        return [expect_mod.unreadable_message(name, exp)]
    base = os.path.join(c.tmp, "prog_" + name.replace("/", "_").replace(".", "_"))
    scanned = build.reaches_src(c.root, path)
    c.scanned[name] = scanned
    fl = build.emit_and_link(c, path, name, base, scanned=scanned)
    if fl:
        return fl
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
    and THIS LIBRARY IS THE STANDING EXAMPLE: all eight files in `src/` compile
    at exit 0 and all eight are refused by `llc`, because a library file cannot
    define `@npk_failsafe` and `npkc` never emits a `declare` for it (B-0,
    RX-115). So this stage reports that the FRONTEND accepts each file. It does
    NOT report that any of them assembles, links or runs, and for the six `src/`
    files no suite in this manifest reports that, because there is no library
    object to make one from -- `src/` reaches the compiler only through a
    program root. The sweep closes the gap that those six were checked by
    NOTHING; it does not close the gap that they are checked only as far as the
    frontend. O-N14 is what would change that."""
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
    # does not apply to it -- see `parse_sweep`.
    skip = set() if stage == "parse" else imported_by_others(files)
    n = 0
    for p in files:
        if os.path.normpath(p) in skip:
            continue
        rel = os.path.relpath(p, c.root)
        if only and not any(o in rel for o in only):
            continue
        exp = expect_mod.read(open(p, encoding="utf-8", errors="replace").read())
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

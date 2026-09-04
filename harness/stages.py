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

def run_binary(exe, args, stress, want, name, tail):
    """`stress` runs, the SAME answer required every time."""
    seen = {}
    for _ in range(stress):
        r = build.Run([exe] + list(args), timeout=build.RUN_TIMEOUT)
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
                    " (compiled by the REAL backend)")
    if fl or not with_opt_leg:
        return fl
    fl = build.check_optimised(c, name, base, scanned=scanned)
    if fl:
        return fl
    return run_binary(base + ".opt", exp.argv, exp.stress, exp.exit_code, name,
                      " (through opt -O2 + llc -O2 -- B-3)")


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
    skip = imported_by_others(files)
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
        else:
            fl = [f"{rel}: stage `{stage}`" + (f"/`{kind}`" if kind else "") +
                  " is declared in nitpick.toml and this runner cannot judge it "
                  "yet. A stage that silently does nothing is a suite reporting "
                  "green while checking nothing, so it is a failure and not a skip. "
                  "`parse`, `accept` and `check` arrive at cycle 0.0.3; `corpus` "
                  "and `oracle` at 0.5."]
        record(name, rel, fl)
        n += 1
    return n

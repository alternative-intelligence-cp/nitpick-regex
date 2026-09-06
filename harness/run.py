#!/usr/bin/env python3
"""`nregex`'s build and test runner -- cycles 0.0.2 and 0.0.3.

WHY PYTHON AND WHY HERE. `npkg build` is the compiler's own bootstrap ladder --
it assembles `runtime/npkrt.ll` and `bootstrap/seed/stage1.ll`, has the builder
compile `[build] entry`, and names the result `npkc` -- and `[dependencies]`
resolves against a root list that is created empty and never populated. So
nothing that exists can build this library (`meta/specs/BUILD.md` §1, O-G3),
and RX-004 puts a Python runner here until that closes, exactly as
`bootstrap/harness/` sits beside `npkg` in the compiler repository. It retires
the same way, with a parity stage first.

WHAT A GREEN RUN HERE ASSERTS, and the boundary is worth stating because the
stub this replaced could assert almost nothing:

  * every declared suite's every file was built by the PINNED npkc, assembled by
    `llc`, scanned, linked closed-world against `npkrt.o`, and RUN;
  * every `program`-stage file gave the SAME exit code at -O0 and again through
    `opt -O2` + `llc -O2` (rule B-3);
  * every rejection fixture was refused with EXACTLY the codes it names, no more
    and no fewer (rule B-7, D-237);
  * no object gained an undefined symbol the empty baseline program does not
    have, and no function outside the baseline called a floor symbol this
    library is not permitted to call (rule B-2, RX-116 and RX-120);
  * the same tree built from two different working directories produced
    byte-identical IR (rule B-4);
  * EVERY `.npk` IN THE TREE was swept as a ROOT by the `parse` stage -- which
    is `npkc` and not `tools/parse_check` (B-4b, RX-124), and which is what
    re-checks the six `src/` files `src/lib.npk` does not reach;
  * the four live TREE CHECKS agreed with the specifications they diff against
    (`check_layering`, `check_error_budget`, `check_constants_named`, and
    `check_specs_current` which reports rather than fails);
  * AND THE RUNNER WAS SHOWN ABLE TO FAIL FIRST (V-21, cycle 0.0.3): the
    self-check feeds it eight kinds of wrong expectation and requires a red for
    each, before any suite runs.

WHAT IT STILL DOES NOT ASSERT: three of V-20's eleven self-check cases are
PENDING on stages that do not exist -- the generated-table case (0.3), the
corpus off-by-one (0.5) and the cross-engine disagreement (0.8, and the most
important one in the list, because it is what proves RX-041 is being checked
rather than assumed). They print as PENDING and never as passing, so the count
in the summary is honest about what the green covers.

USAGE
    NPKC=... NPKRT=... python3 harness/run.py [options]

    --only PATTERN        run only units whose path contains PATTERN (repeatable).
                          A FILTERED RUN CONCLUDES NOTHING and says so twice.
    --verdicts PATH       write one line per unit judged
    --record-baseline     re-record harness/baseline/SYMBOLS.txt and EDGES.txt
    --keep                keep the scratch directory and print its path
    --tree PATH           run against a different tree root (the self-check's)
    --selfcheck-inner     "you are being run BY the self-check": skip the
                          self-check itself, and skip the tree checks. Both for
                          one reason -- the tree under test is a throwaway
                          fixture and not this library -- and it is ONE flag so
                          that no ordinary invocation can turn either off.
"""
import argparse
import os
import shutil
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build                                                  # noqa: E402
import manifest                                               # noqa: E402
import stages                                                 # noqa: E402
import toolchain                                              # noqa: E402
import treecheck                                              # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FILTERED = ("A FILTERED RUN CONCLUDES NOTHING. `--only` iterates; it never "
            "decides. Nothing is committed on the strength of one.")


class Report:
    def __init__(self):
        self.rows = []          # (suite, unit, ok, msg)
        self.build_failures = []

    def unit(self, suite, name, fl):
        self.rows.append((suite, name, not fl, " | ".join(fl)))

    def step(self, what, fl):
        for f in fl:
            self.build_failures.append(f"{what}: {f}")
        return not fl

    @property
    def failed(self):
        return [r for r in self.rows if not r[2]]

    @property
    def ok(self):
        return not self.failed and not self.build_failures


def main(argv=None, say=print):
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--only", action="append", default=[])
    ap.add_argument("--verdicts")
    ap.add_argument("--record-baseline", action="store_true")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--tree", default=None)
    ap.add_argument("--selfcheck-inner", action="store_true")
    a = ap.parse_args(argv)

    t0 = time.time()
    root = os.path.abspath(a.tree) if a.tree else ROOT
    say(f"nregex harness -- cycle 0.0.3. tree: {root}")

    try:
        m = manifest.read(os.path.join(root, "nitpick.toml"))
    except manifest.ManifestError as e:
        say(f"FAIL  nitpick.toml: {e}")
        return 1
    say(f"ok    nitpick.toml: {len(m.tables)} tables, {len(m.tests)} [[test]] entries")

    try:
        toolchain.check(m.need("toolchain", "llvm"), say)
        npkc, npkrt = toolchain.compiler(say)
    except (toolchain.ToolchainError, manifest.ManifestError) as e:
        say(f"FAIL  toolchain: {e}")
        return 1

    # RULE V-21 -- THE SELF-CHECK RUNS FIRST, before a single library test is
    # judged, and its failure stops the run. There is no order in which running
    # the suite before this makes sense: a harness that has not been shown able
    # to fail has not shown anything about what it reported green.
    #
    # `--record-baseline` is the one invocation that skips it, because it judges
    # nothing and writes a file.
    if not a.selfcheck_inner and not a.record_baseline:
        import selfcheck                                       # noqa: E402
        fl = selfcheck.run(say, keep=a.keep)
        if fl:
            say("")
            say("THE SELF-CHECK FAILED, so no suite ran (V-21). The harness could "
                "not be shown to report these kinds of wrongness, and until it can, "
                "a green run below would mean nothing.")
            for f in fl:
                say(f"FAIL  {f}")
            return 1

    tmp = tempfile.mkdtemp(prefix="nregex-harness-")
    c = build.Ctx(root, m, npkc, npkrt, tmp, say)
    rep = Report()
    try:
        if a.record_baseline:
            fl = build.record_baseline(c)
            for f in fl:
                say(f"FAIL  {f}")
            if not fl:
                say(f"ok    recorded {build.BASELINE_SYMS} and {build.BASELINE_EDGES}")
                say("      This is a deliberate act. Commit it on its own, with the "
                    "compiler commit that moved, so a reviewer sees the diff.")
            return 1 if fl else 0

        if a.only:
            say("")
            say(f"NOTE  --only {a.only}: {FILTERED}")
            say("")

        _build_steps(c, rep, say)
        if rep.build_failures:
            say("")
            say("THE BUILD FAILED, so no suite ran. A build step is not a test and "
                "cannot be skipped (rule B-2, P-11).")
            for f in rep.build_failures:
                say(f"FAIL  {f}")
            return 1

        # RULE P-16 -- the tree checks run on EVERY full invocation, including
        # the ones with nothing to check. They diff the library against the
        # documents describing it, so they are neither build steps nor tests and
        # they get their own section.
        if not a.selfcheck_inner:
            for r in treecheck.run_all(root, say):
                for f in r.failures:
                    rep.unit("tree-checks", r.name, [f])

        _suites(c, m, rep, a.only, say)
    finally:
        if a.keep:
            say(f"      scratch kept at {tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)

    return _summary(c, rep, a, say, time.time() - t0)


def _build_steps(c, rep, say):
    """Build steps, in order. Every one of these FAILS the run; none is a test."""
    say("")
    say("-- build steps (B-2, B-4; a failure here stops the run) --")

    fl, syms, edges = build.build_baseline(c)
    if rep.step("baseline", fl):
        c.baseline_syms, c.baseline_edges = syms, edges
        say(f"ok    baseline: {len(syms)} undefined symbols, {len(edges)} floor call "
            f"edges, and it links and runs")
    else:
        return

    entry = c.m.need("build", "entry")
    r = build.emit(c, os.path.join(c.root, entry), os.path.join(c.tmp, "libcheck.ll"))
    if r.timed_out or r.code != build.NPKC_OK:
        rep.step("libcheck", [build.npkc_failure(entry, "emit", r)])
        return
    say(f"ok    libcheck: npkc accepted {entry} (exit 0)")
    say("      AND THAT IS NOT EVIDENCE THAT THE LIBRARY BUILDS. There is no library")
    say("      object at this pin: every file in src/ compiles at exit 0 and every")
    say("      one is refused by llc, because a library file cannot define")
    say("      @npk_failsafe and npkc never declares it (B-0, RX-115; O-N14). The")
    say("      library reaches the compiler only through a program root, and the")
    say("      conformance suite below is the smallest one.")

    conformance = None
    for t in c.m.tests:
        if t.get("stage") == "compile" and t.get("kind") == "positive":
            conformance = t
            break
    if conformance is None:
        rep.step("repro", ["no compile/positive entry to build twice"])
        return
    files = stages.files_of(c.root, manifest.paths_of(conformance),
                            bool(conformance.get("recursive", False)))
    if not files:
        rep.step("repro", ["the compile/positive suite is empty"])
        return
    rel = os.path.relpath(files[0], c.root)
    fl = build.repro(c, rel)
    if rep.step("repro", fl):
        say(f"ok    repro: two builds of {rel} from different working directories "
            f"are byte-identical (B-4)")


def _suites(c, m, rep, only, say):
    say("")
    say("-- suites, in the order nitpick.toml writes them --")
    for t in m.tests:
        kind = f"/{t['kind']}" if "kind" in t else ""
        try:
            n = stages.run_entry(c, t, only, rep.unit)
        except FileNotFoundError as e:
            rep.unit(t["name"], t.get("path", "?"), [str(e)])
            n = 1
        say(f"      {t['name']}  ({t['stage']}{kind})  {n} unit(s)")
        for suite, name, ok, msg in rep.rows:
            if suite != t["name"]:
                continue
            say(f"  {'ok  ' if ok else 'FAIL'}  {name}" + ("" if ok else f": {msg}"))


def _summary(c, rep, a, say, secs):
    say("")
    total = len(rep.rows)
    bad = len(rep.failed)
    scanned = sorted(k for k, v in c.scanned.items() if v)
    unscanned = sorted(k for k, v in c.scanned.items() if not v)
    say(f"      B-2's two scans ran on {len(scanned)} unit(s) -- the ones whose "
        f"module graph reaches src/: {', '.join(scanned) or 'none'}.")
    say(f"      They did NOT run on {len(unscanned)}: the language probes import "
        f"nothing from src/ (tests/probe/README.md P-1), so RX-008's rule is not "
        f"about them. Saying so is the point -- a check that quietly did not apply "
        f"reads exactly like one that passed.")
    say(f"      Of B-2's reviewed residue list, {len(c.residue_seen)} of "
        f"{len(c.residue_allowed)} entries were referenced by a scanned program "
        f"(RX-131): {', '.join(sorted(c.residue_seen)) or 'none'}.")
    # The unused half is only meaningful over the WHOLE tree: `--only` scans a
    # subset, so every filtered run would report the rest as dead entries.
    if not a.only:
        for m in build.residue_unused(c):
            rep.rows.append(("baseline", "residue", False, m))
            rep.failed.append(("baseline", "residue", False, m))
            bad += 1
            total += 1
    if a.verdicts:
        with open(a.verdicts, "w", encoding="utf-8") as fh:
            for suite, name, ok, msg in rep.rows:
                fh.write(f"{'PASS' if ok else 'FAIL'}\t{suite}\t{name}\t{msg}\n")
        say(f"      {total} verdict line(s) written to {a.verdicts}")
    say(f"{total - bad}/{total} unit(s) passed in {secs:.1f} s.")
    for suite, name, ok, msg in rep.failed:
        say(f"FAIL  {suite}/{name}: {msg}")
    if a.only:
        say(f"NOTE  --only {a.only}: {FILTERED}")
        return 1 if bad else 0
    if bad or rep.build_failures:
        return 1
    say("GREEN. Every declared suite built, linked, ran and was judged by its exit "
        "code; every program agreed with itself under opt -O2; every rejection "
        "reported exactly the codes it names; every .npk in the tree was swept as "
        "a root; and the tree checks agreed with the specifications.")
    if not a.selfcheck_inner:
        say("      AND THE RUNNER WAS SHOWN ABLE TO FAIL FIRST (V-21): the "
            "self-check above fed it EIGHT kinds of wrong expectation and required "
            "a red for each. Three of V-20's eleven cases are PENDING on stages "
            "that do not exist yet (0.3, 0.5, 0.8) and printed as pending, not as "
            "passing -- so this green covers eight of the eleven ways the harness "
            "is meant to be able to fail, not eleven.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

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
  * RX-120's numbers still hold at the pinned compiler -- `harness/baseline/rx120.sh`
    ASSERTS floor == 5, syscaller == 6 and difference == {npk_sys6} (at
    `c3bdae2`; 2 and 3 at `3d15ac9` -- RX-148), as a build step, so a re-pin
    that moves the prelude reddens a run instead of silently invalidating a
    committed sentence (RX-142's neighbourhood);
  * the SEVEN live TREE CHECKS agreed with the specifications they diff against
    (`check_layering`, `check_error_budget`, `check_constants_named`,
    `check_no_division`, `check_accessor_confinement`,
    `check_dated_measurements`, and `check_specs_current` which reports rather
    than fails);
  * every unit a `pending-until:` marker took out of the denominator is on the
    reviewed list `harness/baseline/PENDING.txt`, gave exactly the exit its
    marker names, and did not meet its expectation (RX-154) -- so one comment
    line cannot move a red out of a green run;
  * AND THE RUNNER WAS SHOWN ABLE TO FAIL FIRST (V-21, cycle 0.0.3): the
    self-check feeds it every live kind of wrong expectation `TESTING.md` V-20
    names and requires a red for each, before any suite runs.

WHAT IT STILL DOES NOT ASSERT: some of V-20's self-check cases are PENDING on
stages that do not exist -- the generated table (0.3), the corpus and oracle
cases (0.5), and the cross-engine disagreement (0.8, the most important in the
list, because it is what proves RX-041 is being checked rather than assumed).
They print as PENDING and never as passing, and the summary prints the counts
from `selfcheck.CASES` itself -- until the third cycle-0.0 audit's triage it
printed "EIGHT" and "eleven" as prose, true on the day each was written.

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
        self.pending = []       # stages.Pending -- neither a pass nor a failure

    def unit(self, suite, name, fl):
        # A `pending-until:` unit leaves the stage as a single `Pending` and is
        # kept OUT of `rows` entirely, so it is counted as neither passing nor
        # failing. `selfcheck.py` P-18 states the rule this follows: a pending
        # case is not a passing case, and a denominator that quietly absorbs one
        # is a denominator that lies. It is printed in the summary regardless, so
        # "not counted" never means "not seen".
        if len(fl) == 1 and isinstance(fl[0], stages.Pending):
            fl[0].suite = suite
            self.pending.append(fl[0])
            return
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
    sc_counts = None
    if not a.selfcheck_inner and not a.record_baseline:
        import selfcheck                                       # noqa: E402
        fl = selfcheck.run(say, keep=a.keep)
        sc_counts = selfcheck.counts()
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

        _build_steps(c, rep, say, a.selfcheck_inner)
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
        listed = _pending_list(c, rep, full=not a.only)
    finally:
        if a.keep:
            say(f"      scratch kept at {tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)

    return _summary(c, rep, a, say, time.time() - t0, sc_counts, listed)


def _build_steps(c, rep, say, inner=False):
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

    # RX-120's EXPIRY, ASSERTED. `harness/baseline/rx120.sh` builds the floor
    # and a syscaller at the pinned compiler and REQUIRES floor == 5,
    # syscaller == 6 and the difference == {npk_sys6} (at `c3bdae2`; 2 and 3 at
    # `3d15ac9` -- RX-148); with the superseded
    # `950bb1d` present it also requires 29/29/identical, which is RX-120 as
    # originally measured. It is a build step and not a test for the reason
    # SYMBOLS.txt's diff is one: a number moving there is a PRELUDE change, and
    # a prelude change invalidates what every suite below it means.
    #
    # It replaced a hand-copied transcript that recorded a command which could
    # not have produced the output beside it (cycle 0.0 audit, adjudication a).
    # Exit 2 is "could not proceed and judged nothing" -- npkc's own alphabet --
    # and it is NOT a pass, so it stops the run like any other build failure.
    # SKIPPED under `--selfcheck-inner`, for the reason the tree checks are: the
    # tree under test is a throwaway fixture with no pinned-compiler baseline to
    # be a difference against, so the assertion would be about the fixture and
    # not about this library. One flag turns both off, so no ordinary
    # invocation can lose either.
    if inner:
        rx = None
    else:
        rx = build.Run([os.path.join(c.root, build.BASELINE_RX120)], cwd=c.root,
                       timeout=180, env={**os.environ, "NPKC": c.npkc})
    if rx is None:
        pass
    elif rx.timed_out:
        rep.step("rx120", [f"{build.BASELINE_RX120} TIMED OUT after 180 s"])
        return
    elif rx.code == 0:
        say(f"ok    rx120: {build.BASELINE_RX120} asserted the floor, the "
            f"syscaller and their difference at the pinned compiler")
        for line in rx.out.decode("utf-8", "replace").split("\n"):
            if line.startswith("SKIPPED") or line.startswith("         "):
                say(f"      {line}")
    else:
        rep.step("rx120", [f"{build.BASELINE_RX120} exit={rx.code}\n"
                           + rx.out.decode("utf-8", "replace") + rx.err])
        return

    entry = c.m.need("build", "entry")
    r = build.emit(c, os.path.join(c.root, entry), os.path.join(c.tmp, "libcheck.ll"))
    if r.timed_out or r.code != build.NPKC_OK:
        rep.step("libcheck", [build.npkc_failure(entry, "emit", r)])
        return
    say(f"ok    libcheck: npkc accepted {entry} (exit 0)")
    # WHAT THE GREEN LINE ABOVE DOES NOT MEAN -- RX-115, AS CORRECTED BY RX-151.
    # This message said for three re-pins that every src/ file "is refused by
    # llc", which was `950bb1d`'s mechanism and has been false since `94874ce`,
    # where npkc began declaring @npk_failsafe (measured at six pins at cycle
    # 0.0.4b). The conclusion stands for a different reason, measured at
    # `c3bdae2`: a module's object links neither alone nor beside a program.
    say("      AND THAT IS NOT EVIDENCE THAT THE LIBRARY BUILDS. Every file in src/")
    say("      compiles at npkc exit 0 and assembles at llc exit 0 (since 94874ce;")
    say("      RX-115's llc refusal was 950bb1d's), but the object is not a library:")
    say("      it links neither alone (no npk_failsafe, no main) nor beside a")
    say("      program, which already carries everything it reaches (ld.lld:")
    say("      duplicate symbol). B-0; RX-115 as corrected by RX-151.")
    say("      The library reaches the compiler only through a program root, and")
    say("      the conformance suite below is the smallest one.")

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
        # Pending units are not in `rows`, and the entry's unit count above DOES
        # include them, so they are listed here or the two numbers disagree with
        # nothing to explain the gap.
        for p in rep.pending:
            if getattr(p, "suite", None) == t["name"]:
                say(f"  PEND  {p.line()}")


def _pending_list(c, rep, full):
    """Every pending unit against `harness/baseline/PENDING.txt`, BOTH WAYS -- RX-154.

    A MARKER THE LIST DOES NOT NAME IS A FAILURE. That is the whole of the
    control the third cycle-0.0 audit found missing (BL-6, M3): one comment line
    on a unit with a wrong expectation took it out of the denominator and the
    run printed `140/140` and GREEN. Now the same line leaves the unit IN the
    denominator, as a failure, until a reviewed line with a reason exists.

    A LINE NO UNIT MATCHES IS A FAILURE TOO, on a full run -- RX-131's
    both-directions rule for a named list, because a list whose entries outlive
    their markers is a list nobody reads. A filtered run judges a subset, so
    that half would fire on every `--only`; the caller passes `full`.

    Returns the number of lines the list holds, which the summary prints."""
    entries, fl = stages.read_pending_list(c.root)
    for f in fl:
        rep.rows.append(("pending-list", stages.PENDING_LIST, False, f))
    seen = set()
    for p in rep.pending:
        key = (p.name, p.until, p.named)
        if key in entries:
            seen.add(key)
            continue
        rep.rows.append((
            "pending-list", p.name, False,
            f"`pending-until: {p.until} exit {p.named}` is NOT ON THE REVIEWED "
            f"PENDING LIST ({stages.PENDING_LIST}). A pending marker takes a unit "
            f"OUT OF THE DENOMINATOR, so it takes a reviewed line with a reason as "
            f"well -- one comment line must never be able to move a red out of a "
            f"green run (RX-154). This unit gives {p.got} and is counted as a "
            f"FAILURE until that line exists."))
    if full:
        for key, n in sorted(entries.items(), key=lambda kv: kv[1]):
            if key in seen:
                continue
            rep.rows.append((
                "pending-list", stages.PENDING_LIST, False,
                f"{stages.PENDING_LIST}:{n} names `{key[0]}` pending on `{key[1]}` "
                f"exit {key[2]}, and no PENDING unit matches it -- the marker is "
                f"gone, differs, went stale, or failed another way (its own line "
                f"says which). Delete or correct the line: an entry that outlives "
                f"its marker is RX-131's dead-entry shape (RX-154)."))
    return len(entries)


def _summary(c, rep, a, say, secs, sc_counts=None, listed=0):
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
    #
    # AND ONLY OVER THIS TREE. The list is a statement about this library, and
    # `PLAYBOOK.md` says such a list fires on every run against any other tree --
    # which the self-check's fixture trees are. `_lib` copies `RESIDUE.txt` into
    # each (the other direction needs it), no fixture references more than two of
    # its entries, and so EVERY inner run was red here for a reason that was not
    # its case's: the exit-code half of every case was vacuous and `must_say` was
    # the only thing telling a detection from noise. Found at the third cycle-0.0
    # audit's triage, when case 12 passed with its own check removed (RX-154).
    if not a.only and not a.selfcheck_inner:
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
    for p in rep.pending:
        say(f"PEND  {p.line()}")
    say(f"      {len(rep.pending)} unit(s) PENDING and {listed} line(s) on the "
        f"reviewed list {stages.PENDING_LIST}, checked both ways (RX-154). A "
        f"pending unit is OUTSIDE the denominator below, and it goes RED the day it "
        f"meets its expectation or gives any exit but the one its marker names.")
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
    if sc_counts is not None:
        live, pend, total = sc_counts
        say(f"      AND THE RUNNER WAS SHOWN ABLE TO FAIL FIRST (V-21): the "
            f"self-check above fed it {live} kinds of wrong expectation and required "
            f"a red for each. {pend} of V-20's {total} cases are PENDING on stages "
            f"that do not exist yet and printed as pending, not as passing -- so "
            f"this green covers {live} of the {total} ways the harness is meant to "
            f"be able to fail, not {total}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

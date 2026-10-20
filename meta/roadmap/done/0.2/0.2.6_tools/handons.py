#!/usr/bin/env python3
"""0.2.6 -- THE HAND-ON SWEEP: every line of every markdown file in cycle 0.2's folder that names `0.2.6`, and of
those every HAND-ON -- a line that says `To 0.2.6`, or `**To the close` / `**To the cycle's close` -- held to
`handons.txt`, the plan's §2 list of the six, both ways: a hand-on the list lacks is UNLISTED, a listed one the folder
lacks is MISSING, and either exits 1. Every other line naming `0.2.6` is printed by file and line for §1.7's reading. This plan's own file is no
source of a hand-on, and is not read.

    python3 -B handons.py sweep   <folder>     # meta/roadmap/0.2 before step 5, done/0.2 after
    python3 -B handons.py control <folder>     # the same over a copy holding one planted hand-on: it must be UNLISTED

The control copies the folder's markdown files to `$A/ctl/handons/` and appends ONE line to `0.2.3.md`, a file with no
hand-on of its own -- `- **To 0.2.6, planted by the control:** a hand-on no list holds.` -- and passes only if the sweep
finds exactly that line UNLISTED and exits 1. Reads with `newline=""`; writes only under `$A`.
"""
import os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = re.compile(r"(?<![0-9.])0\.2\.6(?![0-9])")
HANDON = re.compile(r"\bTo 0\.2\.6(?![0-9])|\*\*To the (?:cycle's )?close\b")
PLANT = "- **To 0.2.6, planted by the control:** a hand-on no list holds."


def listed():
    rows = []
    for line in open(os.path.join(HERE, "handons.txt"), encoding="utf-8"):
        if line.strip() and not line.startswith("#"):
            name, prefix = line.rstrip("\n").split("|", 1)
            rows.append((name, prefix))
    return rows


def sweep(folder):
    rows, found, other, files, naming = listed(), [], [], 0, 0
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".md") or name == "0.2.6.md":
            continue
        files += 1
        with open(os.path.join(folder, name), encoding="utf-8", newline="") as fh:
            for n, line in enumerate(fh.read().split("\n"), 1):
                if not NAMES.search(line):
                    continue
                naming += 1
                (found if HANDON.search(line) else other).append((name, n, line))
    print("swept %s: %d markdown file(s), %d line(s) naming 0.2.6, %d hand-on line(s)"
          % (os.path.basename(os.path.normpath(folder)), files, naming, len(found)))
    bad, hit = 0, set()
    for name, n, line in found:
        k = next((i for i, (f, p) in enumerate(rows) if f == name and line.startswith(p)), None)
        if k is None:
            bad += 1
            print("  UNLISTED %s:%d  %s" % (name, n, line.strip()[:90]))
        else:
            hit.add(k)
            print("  LISTED   %s:%d  %s" % (name, n, line.strip()[:90]))
    for i, (f, p) in enumerate(rows):
        if i not in hit:
            bad += 1
            print("  MISSING  %s  %s" % (f, p[:90]))
    print("other lines naming 0.2.6: %d -- %s" % (len(other), ", ".join("%s:%d" % (f, n) for f, n, _ in other)))
    return bad


def main(argv):
    if len(argv) != 3 or argv[1] not in ("sweep", "control"):
        print(__doc__)
        return 2
    folder = os.path.realpath(argv[2])
    if argv[1] == "sweep":
        return 1 if sweep(folder) else 0
    d = os.path.join(os.environ["A"], "ctl", "handons")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    for name in os.listdir(folder):
        if name.endswith(".md"):
            shutil.copyfile(os.path.join(folder, name), os.path.join(d, name))
    with open(os.path.join(d, "0.2.3.md"), "a", encoding="utf-8", newline="") as fh:
        fh.write("\n" + PLANT + "\n")
    bad = sweep(d)
    shutil.rmtree(d, ignore_errors=True)
    ok = bad == 1
    print("control: %s" % ("the planted hand-on UNLISTED, and the sweep exits 1" if ok else "FAILED -- %d finding(s)" % bad))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

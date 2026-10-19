#!/usr/bin/env python3
"""0.2.6 -- THE SWEEP (block 6s): every pattern of `sweep_patterns.txt` over a tree's LIVE text files, and its control.

    python3 -B sweep.py run     <tree>   # each hit as `label  file:line  text`, then the counts per pattern
    python3 -B sweep.py control <tree>   # a copy with `sweep_twins.txt`'s lines appended: every twin must be caught

LIVE is every tracked text file but the records -- `meta/DECISIONS.md` (a settled decision's text is never rewritten),
the archives `meta/roadmap/done/0.0/` and `done/0.1/`, cycle 0.2's own subcycle files and their tools under
`meta/roadmap/done/0.2/` (every one but its README), the audit reports and the transcripts -- and the patterns' own
files. A hit is a line to READ against the plan's §6b classes, not a finding by itself. The control copies the
tree's tracked files to `$A/ctl/sweep/` (the working tree as it stands), plants each twin, and passes only if every
twin is caught, by any pattern, at the line it was planted on.
"""
import os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKIP = re.compile(r"^meta/DECISIONS\.md$|^meta/roadmap/done/0\.[01]/|^meta/roadmap/(done/)?0\.2/0\.2\.|"
                  r"^meta/audits/|TRANSCRIPT\.txt$")


def patterns():
    out = []
    for line in open(os.path.join(HERE, "sweep_patterns.txt"), encoding="utf-8"):
        if line.strip() and not line.startswith("#"):
            label, rx = line.rstrip("\n").split("|", 1)
            out.append((label, re.compile(rx, re.I)))
    return out


def live(tree):
    out = subprocess.run(["git", "-C", tree, "ls-files", "-co", "--exclude-standard"], stdout=subprocess.PIPE,
                         text=True).stdout.split("\n")
    return sorted(f for f in out if f and not SKIP.search(f))


def sweep(tree, quiet=False):
    pats, hits, files = patterns(), [], 0
    for rel in live(tree):
        try:
            with open(os.path.join(tree, rel), encoding="utf-8", newline="") as fh:
                lines = fh.read().split("\n")
        except (UnicodeDecodeError, IsADirectoryError, FileNotFoundError):
            continue
        files += 1
        for n, line in enumerate(lines, 1):
            for label, rx in pats:
                if rx.search(line):
                    hits.append((label, rel, n, line))
    if not quiet:
        for label, rel, n, line in hits:
            print("%-14s %s:%d  %s" % (label, rel, n, line.strip()[:100]))
        print("swept %d live text file(s); %d hit(s): %s" % (files, len(hits), ", ".join(
            "%s %d" % (l, sum(1 for h in hits if h[0] == l)) for l, _ in pats)))
    return hits


def main(argv):
    if len(argv) != 3 or argv[1] not in ("run", "control"):
        print(__doc__)
        return 2
    tree = os.path.realpath(argv[2])
    if argv[1] == "run":
        sweep(tree)
        return 0
    d = os.path.join(os.environ["A"], "ctl", "sweep")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    for rel in subprocess.run(["git", "-C", tree, "ls-files", "-co", "--exclude-standard"], stdout=subprocess.PIPE,
                              text=True).stdout.split("\n"):
        if rel and os.path.isfile(os.path.join(tree, rel)):
            os.makedirs(os.path.dirname(os.path.join(d, rel)) or d, exist_ok=True)
            shutil.copyfile(os.path.join(tree, rel), os.path.join(d, rel))
    subprocess.run(["git", "init", "-q", d], check=True)
    subprocess.run(["git", "-C", d, "add", "-A"], check=True)
    planted = []
    for line in open(os.path.join(HERE, "sweep_twins.txt"), encoding="utf-8"):
        if line.strip() and not line.startswith("#"):
            rel, text = line.rstrip("\n").split("|", 1)
            p = os.path.join(d, rel)
            with open(p, encoding="utf-8", newline="") as fh:
                body = fh.read()
            with open(p, "a", encoding="utf-8", newline="") as fh:
                fh.write(("" if body.endswith("\n") else "\n") + text + "\n")
            planted.append((rel, body.count("\n") + (0 if body.endswith("\n") else 1) + 1, text))
    hits = {(h[1], h[2]) for h in sweep(d, quiet=True)}
    missed = [(rel, n, text) for rel, n, text in planted if (rel, n) not in hits]
    shutil.rmtree(d, ignore_errors=True)
    for rel, n, text in missed:
        print("control: MISSED %s:%d  %s" % (rel, n, text))
    print("control: %d of %d twins caught" % (len(planted) - len(missed), len(planted)))
    return 1 if missed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

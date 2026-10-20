#!/usr/bin/env python3
"""Apply one step's patch -- all-or-nothing -- and say which of three states the tree
was in. The plan beside this directory names the steps; `stepN.patch` is each one's
text, a `git diff` of the tree the plan was rehearsed on, and the review surface: a
worker may tighten a text, never change what it says, and amends THE PATCH, never
the tree by hand (the workbench `PLAYBOOK.md` §12).

    python3 -B apply.py <N> "$REPO"

`@@DATE021A@@` in a patch is replaced by THE RUN'S DATE before anything is compared: the
day the run's first step applied, which that step records in `.internal/w021a/date`, so
every dated note carries the day the worker began and every step of one run the same day
-- a later step's context holds an earlier step's date. Then `git apply --index` (the
index and the working tree together, renames included).

THE PLACEHOLDER IS THIS SUBCYCLE'S OWN, `@@DATE021A@@`: the tree holds 0.2.1's
`@@DATE021@@` and 0.2.0's `@@RUN_DATE@@` in their plans and tools, and a placeholder a
touched file already held would be replaced in a patch's context too, so the context
would no longer match the file. No file these patches touch holds `@@DATE021A@@`
before they are applied -- block 0b counts it.

  * the patch applies IN REVERSE  -> ALREADY: the step is in the tree; nothing written
  * the patch applies             -> APPLY: written and staged, every file of it
  * neither                       -> STOP: the tree is not the one the patch was measured
                                     on, and nothing was written; read `git status` and
                                     the message, find the drift, and amend the patch

`git apply` checks every hunk before it writes any, so a STOP writes nothing. A re-run
reports ALREADY on any day, since the run's date is the one recorded. Remove
`.internal/w021a/date` only to begin the run again from its first step.
`../0.2.1_tools/apply.py`, pointed here.
"""
import datetime
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    n, root = argv[1], os.path.realpath(argv[2])
    path = os.path.join(HERE, f"step{n}.patch")
    if not os.path.isfile(path):
        print(f"STOP step{n}: no {os.path.basename(path)} beside this tool")
        return 1
    stamp = os.path.join(root, ".internal", "w021a", "date")
    if os.path.isfile(stamp):
        with open(stamp, encoding="utf-8") as fh:
            date = fh.read().strip()
    else:
        date = datetime.date.today().isoformat()
    with open(path, encoding="utf-8", newline="") as fh:
        text = fh.read().replace("@@DATE021A@@", date)

    def git(*args):
        return subprocess.run(["git", "-C", root, "apply", "--index", *args, "-"],
                              input=text, text=True, capture_output=True)

    if git("--reverse", "--check").returncode == 0:
        print(f"ALREADY step{n}")
        return 0
    r = git("--check")
    if r.returncode == 0:
        r = git()
    if r.returncode != 0:
        print(f"STOP step{n}: " + " | ".join(r.stderr.strip().splitlines()[:6]))
        return 1
    if not os.path.isfile(stamp):
        os.makedirs(os.path.dirname(stamp), exist_ok=True)
        with open(stamp, "w", encoding="utf-8") as fh:
            fh.write(date + "\n")
    print(f"APPLY step{n}: {text.count(chr(10) + 'diff --git') + text.startswith('diff --git')} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

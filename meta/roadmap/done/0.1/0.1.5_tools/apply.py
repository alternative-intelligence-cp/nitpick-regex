#!/usr/bin/env python3
"""Apply one step's patch -- all-or-nothing -- and say which of three states the tree
was in. The plan beside this directory names the steps; `stepN.patch` is each one's
text, a `git diff` of the tree the plan was rehearsed on, and the review surface: a
worker may tighten a text, never change what it says, and amends THE PATCH, never
the tree by hand (the workbench `PLAYBOOK.md` §12).

    python3 -B apply.py <N> "$REPO"

`@@DATE@@` in a patch is replaced by THE RUN'S DATE before anything is compared: the day
the run's first step applied, which that step records in `.internal/n15/date`, so a dated
note carries the day the worker began, and every step of one run carries the same day.
*(0.1.4's tool used each step's own day, so a run that crossed midnight STOPPED at the first
step whose context held an earlier step's date -- measured in cycle 0.1.5's confirmation, whose
step 2 applied at 23:58 and whose step 3, after midnight, STOPPED at `SYNTAX.md` and
`parse_escape_refusals.npk`; with the run's date recorded, it applied.)* Then, with
`git apply --index` (the index and the working tree together, renames included):

  * the patch applies IN REVERSE  -> ALREADY: the step is in the tree; nothing written
  * the patch applies             -> APPLY: written and staged, every file of it
  * neither                       -> STOP: the tree is not the one the patch was measured
                                     on, and nothing was written; read `git status` and
                                     the message, find the drift, and amend the patch

`git apply` checks every hunk before it writes any, so a STOP writes nothing. A re-run
reports ALREADY on any day, since the run's date is the one recorded. Remove
`.internal/n15/date` only to begin the run again from its first step.
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
    stamp = os.path.join(root, ".internal", "n15", "date")
    if os.path.isfile(stamp):
        with open(stamp, encoding="utf-8") as fh:
            date = fh.read().strip()
    else:
        date = datetime.date.today().isoformat()
    with open(path, encoding="utf-8", newline="") as fh:
        text = fh.read().replace("@@DATE@@", date)

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

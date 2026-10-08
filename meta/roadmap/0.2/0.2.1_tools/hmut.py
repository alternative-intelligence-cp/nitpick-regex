#!/usr/bin/env python3
"""0.2.1 -- the self-check's cases run against a MUTANT OF THE HARNESS: `TESTING.md` V-20's "seen to fail" for a case
that guards a harness change, asked on every run of the block rather than once by hand.

    python3 -B hmut.py <tree> <cases> [<file> <old> <new>]

<tree> -- its tracked and untracked files, not the ignored -- is copied to `$A/hmut/`; with a replacement, the text
<old> of <file> is replaced ONCE (any other count is a STOP, and nothing runs; `\\n` in a text is a newline). Then each
case of <cases> (`11,34`) is run through the copy's own `harness/selfcheck.py`, exactly as `selfcheck.run` runs it, and
one line printed per case: `case N: red as required` -- the harness failed the planted tree and named what the case
asks for -- or `case N: NOT red as required` and the first line of why. The copy is removed at the end.
"""
import os
import shutil
import subprocess
import sys


def main(argv):
    if len(argv) not in (3, 6):
        print(__doc__)
        return 2
    tree, cases = os.path.realpath(argv[1]), argv[2].split(",")
    d = os.path.join(os.environ["A"], "hmut")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    out = subprocess.run(["git", "-C", tree, "ls-files", "-co", "--exclude-standard", "-z"],
                         capture_output=True, text=True).stdout
    for f in out.split("\0"):
        if f:
            os.makedirs(os.path.dirname(os.path.join(d, f)) or d, exist_ok=True)
            shutil.copy2(os.path.join(tree, f), os.path.join(d, f))
    if len(argv) == 6:
        p = os.path.join(d, argv[3])
        old, new = argv[4].replace("\\n", "\n"), argv[5].replace("\\n", "\n")
        s = open(p, encoding="utf-8").read()
        if s.count(old) != 1:
            shutil.rmtree(d, ignore_errors=True)
            print("STOP: %d occurrence(s) of %r in %s" % (s.count(old), old[:60], argv[3]))
            return 1
        open(p, "w", encoding="utf-8").write(s.replace(old, new))
    sys.path.insert(0, os.path.join(d, "harness"))
    os.chdir(d)
    import selfcheck
    for c in selfcheck.CASES:
        if str(c.num) in cases:
            o = selfcheck._run_case(c, False)
            print("case %s: %s" % (c.num, "red as required" if o.ok
                                   else "NOT red as required -- " + o.detail.split("\n")[0][:110]))
    os.chdir(tree)
    shutil.rmtree(d, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

#!/usr/bin/env python3
"""0.2.1a -- the compiler's D-332 over a tree, as this runner holds it since RX-178 (`BUILD.md` B-7b): for every tracked
`.npk` carrying `expect-error`, compile it with each named pin's `npkc` and compare, per code on the error channel,
the number of reported SITES with the number of `expect-error` lines naming it.

    python3 -B sitecount.py <tree> <pin> [<pin> ...]

Reads through <tree>'s OWN harness reader and parser (`harness/expect.py`, `harness/build.py`'s `findings_of`), so it
counts what that tree's runner counts. Prints the denominator, then one line per file whose count differs at any pin,
then nothing else -- a file that agrees everywhere is in the total. `$WB` names the workbench (`env.sh`).
`../../done/0.1/0.1.0b_tools/sitecount.py`, its toolchain found through `$WB` so a copy of a tree can be counted.
"""
import collections
import os
import re
import subprocess
import sys


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    root, pins = os.path.realpath(argv[1]), argv[2:]
    sys.path.insert(0, os.path.join(root, "harness"))
    import build
    import expect
    r = subprocess.run(["git", "-C", root, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if r.returncode == 0 and os.path.realpath(r.stdout.strip()) == root:
        files = subprocess.run(["git", "-C", root, "grep", "-l", "-E", r"^\s*//\s*expect-error:",
                                "--", "*.npk"], capture_output=True, text=True).stdout.split()
    else:                                   # a copy that is no work tree: every `.npk` in it that names a code
        files = []
        for d, dirs, names in os.walk(root):
            dirs[:] = [x for x in dirs if x not in (".git", ".internal")]
            for n in names:
                if n.endswith(".npk") and re.search(r"^\s*//\s*expect-error:", open(os.path.join(d, n), errors="replace").read(), re.M):
                    files.append(os.path.relpath(os.path.join(d, n), root))
    differ = []
    for rel in sorted(files):
        p = os.path.join(root, rel)
        e = expect.read(open(p, "rb").read().decode("utf-8", "surrogateescape"))
        named = collections.Counter(w["code"] for w in e.errors)
        for pin in pins:
            cc = os.path.join(os.environ["WB"], ".internal", "toolchain", pin, "npkc")
            r = subprocess.run([cc, os.path.basename(p), "-o", "/dev/null"],
                               cwd=os.path.dirname(p), capture_output=True, text=True)
            sites = {}
            for f in build.findings_of(r.stderr):
                if not f["is_note"]:
                    sites.setdefault(f["code"], []).append(f"{f['line']}:{f['col']}")
            for code in sorted(named):
                got = sites.get(code, [])
                if got and len(got) != named[code]:
                    differ.append(f"{rel} at {pin}: {code} named x{named[code]}, reported "
                                  f"x{len(got)} at {' '.join(got)}")
    print(f"{len(files)} file(s) carry `expect-error`; {len(differ)} count(s) differ")
    for d in differ:
        print("    " + d)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

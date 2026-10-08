#!/usr/bin/env python3
"""0.1.0b -- the compiler's D-332 over this tree, before our runner holds it: for every
tracked `.npk` carrying `expect-error`, compile it with each named kept compiler and
compare, per code on the error channel, the number of reported SITES with the number of
`expect-error` lines naming it.

    python3 -B sitecount.py "$REPO" <pin> [<pin> ...]

Reads through the harness's own reader and parser (`harness/expect.py`,
`harness/build.py`'s `findings_of`), so it counts what the runner will count. Prints
the denominator, then one line per file whose count differs at any pin, then nothing
else -- a file that agrees everywhere is in the total.
"""
import collections
import os
import subprocess
import sys


def main(argv):
    root, pins = os.path.realpath(argv[1]), argv[2:]
    wb = os.path.dirname(root)
    sys.path.insert(0, os.path.join(root, "harness"))
    import build
    import expect
    files = subprocess.run(["git", "-C", root, "grep", "-l", "-E", r"^\s*//\s*expect-error:",
                            "--", "*.npk"], capture_output=True, text=True).stdout.split()
    differ = []
    for rel in sorted(files):
        p = os.path.join(root, rel)
        e = expect.read(open(p, "rb").read().decode("utf-8", "surrogateescape"))
        named = collections.Counter(w["code"] for w in e.errors)
        for pin in pins:
            cc = os.path.join(wb, ".internal", "toolchain", pin, "npkc")
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

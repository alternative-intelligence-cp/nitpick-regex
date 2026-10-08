#!/usr/bin/env python3
"""0.2.0 -- the fourteen code fences cycle 0.1's close wrote in this plan's §4, as it wrote them, put into a tree at
the paths they name: the close's measured code, PD labels and all, which block 0b re-derives §1 over.

    python3 -B fences.py <plan-file> <tree>

<plan-file> is `0.2.0.md` as the close committed it -- `git show 94b3072:meta/roadmap/0.2/0.2.0.md` -- whose §4 holds
the fences: a `src/` file's path is its first comment's, a unit's or a refusal's is its `mod:` name under
`tests/unit/` or `tests/rejection/`, by its `expect-` header. It prints the count and each path.
"""
import os
import re
import sys


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    text = open(argv[1], encoding="utf-8").read()
    sec = text[text.index("## 4. The code"):text.index("## 5. Acceptance")]
    paths = []
    for m in re.finditer(r"^```nitpick\n(.*?)^```", sec, re.S | re.M):
        body = m.group(1)
        pm = re.match(r"// `([^`]+)`", body.split("\n", 1)[0])
        if pm:
            path = pm.group(1)
        else:
            mod = re.search(r"^mod:([a-z_0-9]+);", body, re.M).group(1)
            exp = re.search(r"^// expect-(exit|error):", body, re.M)
            path = "tests/%s/%s.npk" % ("rejection" if exp and exp.group(1) == "error" else "unit", mod)
        paths.append(path)
        full = os.path.join(argv[2], path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        open(full, "w", encoding="utf-8").write(body)
    print("%d fence(s): %s" % (len(paths), " ".join(paths)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

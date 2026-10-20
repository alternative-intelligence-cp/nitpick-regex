#!/usr/bin/env python3
"""0.2.6 -- V-20's case 32 (block 2), asked twice of the tree's own harness: as it stands, where it must be green with
its tenth plant, a bare `64i64`; and with 64 put back in `check_constants_named`'s small numbers, in memory, where that
plant passes the check and the case must go RED (RX-247). `$NPKC` and `$NPKRT` from the environment, for the case's
question to the pinned compiler; nothing is written but the case's own scratch.

    python3 -B case32.py <tree>
"""
import os, sys, types

OLD = "_SMALL = {0, 1, 2, 3, 4, 7, 8, 15, 16, 24, 31, 32, 63, 100, 127, 128, 255, 256}"


def main(tree):
    h = os.path.join(os.path.realpath(tree), "harness")
    sys.path.insert(0, h)
    import treecheck, selfcheck
    case = [c for c in selfcheck.CASES if c.num == 32][0]
    o = selfcheck._run_case32(case)
    print("case 32 as the tree holds it: %s -- %s" % ("green" if o.ok else "RED", o.detail[:110]))
    src = open(os.path.join(h, "treecheck.py"), encoding="utf-8").read()
    if src.count(OLD) != 1:
        print("the small numbers are not as RX-247 leaves them")
        return 1
    mod = types.ModuleType("treecheck")
    mod.__file__ = treecheck.__file__
    exec(compile(src.replace(OLD, OLD.replace("63, 100", "63, 64, 100")), "treecheck-64", "exec"), mod.__dict__)
    sys.modules["treecheck"] = mod
    m = selfcheck._run_case32(case)
    print("case 32 with 64 put back:     %s --%s" % ("green, MISSED" if m.ok else "RED", m.detail[m.detail.find(":") + 1:][:110]))
    return 0 if (o.ok and not m.ok) else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))

#!/usr/bin/env python3
"""0.2.6 -- six mutants of `check_hir_kinds_total`, each run against V-20's case 35 (block 1): the check broken one way
at a time, in memory, and the case asked again with the broken check -- each must go RED through the plant it names
(RX-246; `TESTING.md` V-14: an instrument is seen to fail before it is trusted). The tree's own harness is read, and
nothing is written.

    python3 -B kinds_mutants.py <tree>
"""
import os, sys, types

MUTANTS = [
    ("reads-count-as-writes",
     "        if built[:u.start()].rstrip().endswith(_HIR_READ_OPS) or built[u.end():].lstrip().startswith(_HIR_READ_OPS):\n"
     "            continue\n", ""),
    ("window-bounded",
     "        if built[:u.start()].rstrip().endswith(_HIR_READ_OPS) or built[u.end():].lstrip().startswith(_HIR_READ_OPS):\n",
     "        if built[max(0, u.start() - 8):u.start()].rstrip().endswith(_HIR_READ_OPS) or "
     "built[u.end():u.end() + 8].lstrip().startswith(_HIR_READ_OPS):\n"),
    ("builder-read-raw", "        built = lexical.blank(lexical.read(os.path.join(root, _HIR_BUILDER)))",
     "        built = lexical.read(os.path.join(root, _HIR_BUILDER))"),
    ("unowned-half-passes", "            fl.append(f\"meta/roadmap: no cycle's README holds a box",
     "            notes.append(f\"meta/roadmap: no cycle's README holds a box"),
    ("tick-ignored", "        ticked = [r for r in rows if r[1]]", "        ticked = []"),
    ("half-read-raw", "            names |= {u.group(1) for u in _HIR_USE.finditer(lexical.blank(_read(path)))}",
     "            names |= {u.group(1) for u in _HIR_USE.finditer(_read(path))}"),
]


def main(tree):
    h = os.path.join(os.path.realpath(tree), "harness")
    sys.path.insert(0, h)
    import treecheck, selfcheck
    src = open(os.path.join(h, "treecheck.py"), encoding="utf-8").read()
    case = [c for c in selfcheck.CASES if c.num == 35][0]
    bad = 0
    for name, old, new in MUTANTS:
        if src.count(old) != 1:
            print("%-22s NOT FOUND in treecheck.py" % name)
            bad += 1
            continue
        mod = types.ModuleType("treecheck")
        mod.__file__ = treecheck.__file__
        exec(compile(src.replace(old, new), "treecheck-" + name, "exec"), mod.__dict__)
        sys.modules["treecheck"] = mod
        o = selfcheck._run_case35(case)
        bad += o.ok
        print("%-22s case 35 %s --%s" % (name, "green, MISSED" if o.ok else "RED", o.detail[o.detail.find(":") + 1:][:140]))
    sys.modules["treecheck"] = treecheck
    o = selfcheck._run_case35(case)
    bad += not o.ok
    print("unmutated              case 35 %s" % ("green" if o.ok else "RED"))
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))

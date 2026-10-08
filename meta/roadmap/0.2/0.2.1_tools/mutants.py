#!/usr/bin/env python3
"""0.2.1 -- the mutants of `mutants.tsv`, each one rule broken in a copy of a tree, every unit the
table's `# units:` line names built and run at both legs in the copy -- `npkc`, `llc`, `ld.lld`,
the binary, at -O0 and through `opt -O2`, the harness's flags -- and compared with the same units
built from the tree unchanged.

    python3 -B mutants.py <tree> <step> [<jobs>]

<tree> is copied (`src/`, `tests/unit/` and the manifest) into `$A/mut/<name>/` per row whose step
list holds <step>, the row's text replaced ONCE -- any other count is a STOP, printed, and nothing built -- and the copies are
removed at the end. It prints the unchanged copy's exits first, then one line per row in the table's
order: the units whose exits differ from the unchanged copy's, `-O0/-O2`, or `NO UNIT RED`, which is
a mutant no test can see. A unit the table names and <tree> does not hold is not built. `$NPKC`, `$NPKRT` and `$A` come from the environment (`env.sh`), and
`llc`, `opt` and `ld.lld` from `PATH`. Rows run <jobs> at a time (4 by default): a row is eleven
builds, and the machine is shared. `../0.2.0_tools/mutants.py`, its table this subcycle's.
"""
import concurrent.futures
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NPKC, NPKRT, A = os.environ["NPKC"], os.environ["NPKRT"], os.environ["A"]


def table(step):
    units, rows = [], []
    for line in open(os.path.join(HERE, "mutants.tsv"), encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("# units:"):
            units = line.split(":", 1)[1].split()
        if not line or line.startswith("#"):
            continue
        st, name, path, old, new = line.split("\t")
        if step in st.split(","):
            rows.append((name, path, old.replace("\\n", "\n"), new.replace("\\n", "\n")))
    return units, rows


def build(d, unit):
    """One unit at both legs in tree <d>: (exit -O0, exit -O2), or ('npkc', codes) if refused."""
    u = os.path.join(d, "tests", "unit")
    o = os.path.join(d, "bin", unit)
    os.makedirs(os.path.dirname(o), exist_ok=True)
    r = subprocess.run([NPKC, unit + ".npk", "-o", o + ".ll"], cwd=u, capture_output=True, text=True)
    if r.returncode != 0:
        codes = sorted({w for w in (r.stdout + r.stderr).split() if w.startswith("NITPICK-")})
        return ("npkc", " ".join(codes) or "exit %d" % r.returncode)
    def sh(*a):
        subprocess.run(a, check=True, capture_output=True)
    sh("llc", "-O0", "-filetype=obj", "-relocation-model=static", o + ".ll", "-o", o + ".o")
    sh("ld.lld", "-static", o + ".o", NPKRT, "-o", o + ".x0")
    sh("opt", "-O2", "-S", o + ".ll", "-o", o + ".2.ll")
    sh("llc", "-O2", "-filetype=obj", "-relocation-model=static", o + ".2.ll", "-o", o + ".2.o")
    sh("ld.lld", "-static", o + ".2.o", NPKRT, "-o", o + ".x2")
    e0 = subprocess.run([o + ".x0"], capture_output=True).returncode
    e2 = subprocess.run([o + ".x2"], capture_output=True).returncode
    return (e0, e2)


def copy(tree, d):
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    shutil.copytree(os.path.join(tree, "src"), os.path.join(d, "src"))
    shutil.copytree(os.path.join(tree, "tests", "unit"), os.path.join(d, "tests", "unit"))
    shutil.copy(os.path.join(tree, "nitpick.toml"), d)


def one(tree, units, row):
    name, path, old, new = row
    d = os.path.join(A, "mut", name)
    copy(tree, d)
    p = os.path.join(d, path)
    s = open(p, encoding="utf-8").read()
    if s.count(old) != 1:
        shutil.rmtree(d, ignore_errors=True)
        return name, "STOP: %d occurrence(s) of %r in %s" % (s.count(old), old[:50], os.path.basename(path))
    open(p, "w", encoding="utf-8").write(s.replace(old, new))
    got = {u: build(d, u) for u in units}
    shutil.rmtree(d, ignore_errors=True)
    return name, got


def fmt(e):
    return "npkc refused (%s)" % e[1] if e[0] == "npkc" else "%d/%d" % e


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    tree, step = os.path.realpath(argv[1]), argv[2]
    jobs = int(argv[3]) if len(argv) > 3 else 4
    units, rows = table(step)
    units = [u for u in units if os.path.isfile(os.path.join(tree, "tests", "unit", u + ".npk"))]
    d = os.path.join(A, "mut", "unchanged")
    copy(tree, d)
    base = {u: build(d, u) for u in units}
    shutil.rmtree(d, ignore_errors=True)
    print("unchanged: " + ", ".join("%s %s" % (u, fmt(base[u])) for u in units))
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as ex:
        results = list(ex.map(lambda r: one(tree, units, r), rows))
    for name, got in results:
        if isinstance(got, str):
            print("%s: %s" % (name, got))
            continue
        red = [u for u in units if got[u] != base[u]]
        if not red:
            print("%s: NO UNIT RED -- every unit as the unchanged copy" % name)
            continue
        rest = len(units) - len(red)
        print("%s: %s -- the other %d as unchanged" % (name, ", ".join("%s %s" % (u, fmt(got[u])) for u in red), rest))
    shutil.rmtree(os.path.join(A, "mut"), ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

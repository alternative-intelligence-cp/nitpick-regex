#!/usr/bin/env python3
"""0.2.5 -- THE OPERATOR SWEEP, the planner's sweep beneath the mutant table (§4.1), over these mutations and no others:
each relational operator written between spaces replaced by one other (`<` and `<=`, `>` and `>=`, `==` and `!=`, each
by its partner); each `&&`, `||`, `+`, `-`, `|` and `&` between spaces by its counterpart; each typed integer literal
one up and, above 0, one down; each `!` before a name or a `(` dropped; each `true` and `false` flipped; and each
statement that assigns, `drop`s or `discard`s removed -- in the literals' code: `repr.npk` from its `---- the literals`
section to `hir_literal_byte`, `hir_free`'s two lines, and `dump.npk`'s `write_literals`, `read_literals`, `read_run`'s
tail and `hir_dump`'s call -- each ONCE, in a copy of <tree>, built at -O0 and run against the eight units of
`mutants.tsv`'s `# units:` line in that order, stopping at the first whose exit differs from the unchanged copy's.
Mutations of other kinds -- a relational operator's other replacements, `*`, a named constant, a call's argument, a
field read for another, a condition forced, a variable for another -- it does not make; §4.1 says what lies there.

    python3 -B opsweep.py <tree> [<jobs>]

It prints how many mutants were red, refused by `npkc` and left, and then every one left -- file, line and edit -- for
§4.1 to name: each is an equivalent mutant there, or a facet the units do not hold. `$NPKC`, `$NPKRT` and `$A` come from
the environment (`env.sh`), `llc` and `ld.lld` from PATH; the copies are made under `$A/ops/` and removed. Not a block:
no Expect quotes it, and its count is the plan's §4.1 and §8.
"""
import concurrent.futures
import os
import re
import shutil
import subprocess
import sys

NPKC, NPKRT, A = os.environ["NPKC"], os.environ["NPKRT"], os.environ["A"]
HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(A, "ops")
REL = {"<": ["<="], "<=": ["<"], ">": [">="], ">=": [">"], "==": ["!="], "!=": ["=="]}


def units():
    for line in open(os.path.join(HERE, "mutants.tsv"), encoding="utf-8"):
        if line.startswith("# units:"):
            return line.split(":", 1)[1].split()
    return []


def span(lines, start):
    a = next(i for i, l in enumerate(lines) if l.startswith(start))
    b = a
    while not lines[b].startswith("};"):
        b += 1
    return a, b


def regions(tree):
    out = []
    s = open(os.path.join(tree, "src/hir/repr.npk"), encoding="utf-8").read().split("\n")
    a = next(i for i, l in enumerate(s) if l.startswith("// ---- the literals (H-11"))
    out.append(("src/hir/repr.npk", a, span(s, "pub func:hir_literal_byte")[1]))
    for i, l in enumerate(s):
        if l.strip() in ("drop vec_free(@h.literals);", "drop vec_free(@h.lits);"):
            out.append(("src/hir/repr.npk", i, i))
    d = open(os.path.join(tree, "src/hir/dump.npk"), encoding="utf-8").read().split("\n")
    for name in ("func:write_literals", "func:read_literals"):
        out.append(("src/hir/dump.npk",) + span(d, name))
    a = next(i for i, l in enumerate(d) if "what the dump writes after a tree is the literals' section" in l) - 1
    out.append(("src/hir/dump.npk", a, a + 8))
    a = next(i for i, l in enumerate(d) if l.strip() == "drop write_literals(h, out);")
    out.append(("src/hir/dump.npk", a, a))
    return out


def mutants(tree):
    ms = []
    for path, a, b in regions(tree):
        lines = open(os.path.join(tree, path), encoding="utf-8").read().split("\n")
        for ln in range(a, b + 1):
            line = lines[ln]
            code = line.split("//", 1)[0]
            if not code.strip():
                continue

            def add(start, end, new, kind):
                ms.append((path, ln, line[:start] + new + line[end:], "%s %s -> %s" % (kind, line[start:end], new)))
            for m in re.finditer(r" (<=|>=|<|>|==|!=) ", code):
                for new in REL[m.group(1)]:
                    add(m.start(1), m.end(1), new, "rel")
            for m in re.finditer(r"(?<![\w.])(\d+)(i64|u32|u8|i32|u64)\b", code):
                for nv in (int(m.group(1)) + 1, int(m.group(1)) - 1):
                    if nv >= 0:
                        add(m.start(), m.end(), "%d%s" % (nv, m.group(2)), "const")
            for m in re.finditer(r" (&&|\|\|) ", code):
                add(m.start(1), m.end(1), "||" if m.group(1) == "&&" else "&&", "logic")
            for m in re.finditer(r" ([+-]) ", code):
                add(m.start(1), m.end(1), "-" if m.group(1) == "+" else "+", "arith")
            for m in re.finditer(r" ([|&]) ", code):
                add(m.start(1), m.end(1), "&" if m.group(1) == "|" else "|", "bit")
            for m in re.finditer(r"!(?=[(\w])", code):
                add(m.start(), m.end(), "", "not")
            for m in re.finditer(r"\b(true|false)\b", code):
                add(m.start(), m.end(), "false" if m.group(1) == "true" else "true", "bool")
            st = code.strip()
            if st.endswith(";") and "{" not in st and "}" not in st and not st.startswith("pass ") and (
                    st.startswith("drop ") or st.startswith("discard(") or re.match(r"^[a-z_][\w.]*\s*=\s", st)):
                ms.append((path, ln, line[:len(line) - len(line.lstrip())] + "discard(0i64);", "stmt " + st))
    return ms


def build(d, unit):
    u = os.path.join(d, "tests", "unit")
    o = os.path.join(d, "bin", unit)
    os.makedirs(os.path.dirname(o), exist_ok=True)
    if subprocess.run([NPKC, unit + ".npk", "-o", o + ".ll"], cwd=u, capture_output=True).returncode != 0:
        return "npkc"
    subprocess.run(["llc", "-O0", "-filetype=obj", "-relocation-model=static", o + ".ll", "-o", o + ".o"],
                   check=True, capture_output=True)
    subprocess.run(["ld.lld", "-static", o + ".o", NPKRT, "-o", o + ".x"], check=True, capture_output=True)
    try:
        return subprocess.run([o + ".x"], capture_output=True, timeout=120).returncode
    except subprocess.TimeoutExpired:
        return "timeout"


def copy(tree, d, names):
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(os.path.join(d, "tests", "unit"))
    shutil.copytree(os.path.join(tree, "src"), os.path.join(d, "src"))
    for u in names:
        shutil.copy(os.path.join(tree, "tests", "unit", u + ".npk"), os.path.join(d, "tests", "unit"))


def one(job):
    tree, k, (path, ln, newline, what), base, names = job
    d = os.path.join(W, "m%04d" % k)
    copy(tree, d, names)
    p = os.path.join(d, path)
    lines = open(p, encoding="utf-8").read().split("\n")
    lines[ln] = newline
    open(p, "w", encoding="utf-8").write("\n".join(lines))
    res = "left"
    for u in names:
        e = build(d, u)
        if e == "npkc":
            res = "refused"
            break
        if e != base[u]:
            res = "red"
            break
    shutil.rmtree(d, ignore_errors=True)
    return path, ln, what, res


def main(argv):
    if len(argv) not in (2, 3):
        print(__doc__)
        return 2
    tree = os.path.realpath(argv[1])
    jobs = int(argv[2]) if len(argv) == 3 else 8
    names = units()
    ms = mutants(tree)
    os.makedirs(W, exist_ok=True)
    d = os.path.join(W, "unchanged")
    copy(tree, d, names)
    base = {u: build(d, u) for u in names}
    shutil.rmtree(d, ignore_errors=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as ex:
        res = list(ex.map(one, [(tree, k, m, base, names) for k, m in enumerate(ms)]))
    shutil.rmtree(W, ignore_errors=True)
    count = {"red": 0, "refused": 0, "left": 0}
    for r in res:
        count[r[3]] += 1
    print("%d mutants: %d red, %d refused by npkc, %d left" % (len(ms), count["red"], count["refused"], count["left"]))
    for path, ln, what, r in res:
        if r == "left":
            print("left: %s:%d %s" % (os.path.basename(path), ln + 1, what))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

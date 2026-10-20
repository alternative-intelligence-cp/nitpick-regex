#!/usr/bin/env python3
"""0.2.5a -- every tracked `.npk` of a tree EMITTED by a pin's `npkc`, and two such emissions compared through the
compiler's own normalisers. Three verbs:

    python3 -B emit.py run <pin> <tree> <outdir>
    python3 -B emit.py compare <dir-a> <dir-b> <norm-dir> [--show <file>...]
    python3 -B emit.py edges <dir-a> <dir-b> <harness-dir>

`run` compiles each file as a ROOT from its own directory, as the parse sweep and `census.py` do, into
`<outdir>/<path, every / as %>.ll`, and keeps the ones that compile; it prints how many did, and how many of those
define `@main` -- the programs. The emission is invocation-independent and tree-position-dependent (the compiler's
D-236, this repository's RX-133), so a copy of the tree emits what the checkout emits.

`compare` pairs the two directories' files by name. A file emitted on one side only is named. Each pair is read
three ways, in order, and counted by the first that holds:

  identical         the bytes agree;
  attribute only    they agree with landing 115's `null_pointer_is_valid` stripped from every `define` -- the
                    compiler's `attrnorm.py`, from `<norm-dir>`, run over every pair at once;
  flag tests only   they agree once, besides, every scope-exit drop's flag test is stripped from both and the
                    temporaries and labels renumbered -- `dropnorm.py`, run over `attrnorm.py`'s own `.norm` texts;
                    the line gives the flag tests each side held, so base minus new is the drops landing 105 made
                    unconditional;
  DIFFERENT         anything else, each named -- READ it.

Both normalisers are the compiler's, written into <norm-dir> by `env.sh`'s `normtools`; nothing here restates their
rules. The flag tests are summed: each `src/` file by name, the rest together, and the drops made unconditional in all.

`edges` reads each pair with the tree's own `harness/irscan.py` -- B-2's second layer, the one emission reader whose
answer a moved drop could change -- and compares the edge sets, and each side's two `target` lines (B-1a). `--show` prints the `.norm` diff of the files named. `$WB` names the workbench whose toolchain directory holds
the pin (`env.sh` exports it). Nothing here writes into <tree>.
"""
import os
import re
import subprocess
import sys


def npk_files(tree):
    """The tree's tracked `.npk` files -- or, for a copy that is no work tree, every `.npk` in it."""
    r = subprocess.run(["git", "-C", tree, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if r.returncode == 0 and os.path.realpath(r.stdout.strip()) == os.path.realpath(tree):
        return subprocess.run(["git", "-C", tree, "ls-files", "*.npk"], capture_output=True, text=True).stdout.split()
    out = []
    for d, dirs, names in os.walk(tree):
        dirs[:] = sorted(x for x in dirs if x not in (".git", ".internal"))
        out += [os.path.relpath(os.path.join(d, n), tree) for n in names if n.endswith(".npk")]
    return sorted(out)


def run(pin, tree, outdir):
    npkc = os.path.join(os.environ["WB"], ".internal", "toolchain", pin, "npkc")
    os.makedirs(outdir, exist_ok=True)
    for f in os.listdir(outdir):
        os.remove(os.path.join(outdir, f))
    fs = npk_files(tree)
    done = progs = 0
    for f in fs:
        p = os.path.join(os.path.realpath(tree), f)
        o = os.path.join(os.path.realpath(outdir), f.replace("/", "%") + ".ll")
        r = subprocess.run([npkc, os.path.basename(p), "-o", o], cwd=os.path.dirname(p),
                           capture_output=True, text=True, errors="replace")
        if r.returncode != 0:
            if os.path.exists(o):
                os.remove(o)
            continue
        done += 1
        if re.search(r"^define [^@\n]*@main\(", open(o, errors="replace").read(), re.M):
            progs += 1
    print("%d file(s) at %s: %d emitted, %d of them programs" % (len(fs), pin, done, progs))


def compare(a, b, norm, show):
    na = {f for f in os.listdir(a) if f.endswith(".ll")}
    nb = {f for f in os.listdir(b) if f.endswith(".ll")}
    for f in sorted(na - nb):
        print("  emitted on the first side only: %s" % f[:-3].replace("%", "/"))
    for f in sorted(nb - na):
        print("  emitted on the second side only: %s" % f[:-3].replace("%", "/"))
    both = sorted(na & nb)
    ident = [f for f in both if open(os.path.join(a, f), "rb").read() == open(os.path.join(b, f), "rb").read()]
    rest = [f for f in both if f not in ident]
    attr, flag, diff, stripped = [], [], [], 0
    for f in rest:                          # stale `.norm` texts from an earlier compare would be read as this one's
        for d in (a, b):
            if os.path.exists(os.path.join(d, f + ".norm")):
                os.remove(os.path.join(d, f + ".norm"))
    if rest:
        args = []
        for f in rest:
            args += [os.path.join(a, f), os.path.join(b, f)]
        r = subprocess.run([sys.executable, "-I", os.path.join(norm, "attrnorm.py")] + args,
                           capture_output=True, text=True)
        stripped = int(re.search(r"\((\d+) attributes stripped", r.stdout).group(1))
        moved = [f for f in rest if os.path.exists(os.path.join(a, f + ".norm"))]
        attr = [f for f in rest if f not in moved]
        if moved:
            args = []
            for f in moved:
                args += [os.path.join(a, f + ".norm"), os.path.join(b, f + ".norm")]
            r = subprocess.run([sys.executable, "-I", os.path.join(norm, "dropnorm.py")] + args,
                               capture_output=True, text=True)
            for line in r.stdout.splitlines():
                m = re.match(r"^(same|flag-tests-only|DIFFERENT) (\S+?)\.norm( \(flag tests: base (\d+), new (\d+)\))?$",
                             line)
                if not m:
                    continue
                f = os.path.basename(m.group(2))
                (flag if m.group(1) in ("same", "flag-tests-only") else diff).append(
                    (f, int(m.group(4) or 0), int(m.group(5) or 0)))
    print("%d pair(s): %d identical, %d the attribute only, %d flag tests only, %d DIFFERENT -- %d attribute(s) "
          "stripped from the second side" % (len(both), len(ident), len(attr), len(flag), len(diff), stripped))
    if flag:
        src = [(f[:-3].replace("%", "/"), x, y) for f, x, y in flag if f.startswith("src%")]
        rest = [(f, x, y) for f, x, y in flag if not f.startswith("src%")]
        print("  flag tests only, in src/: " + ", ".join("%s %d then %d" % t for t in src))
        dirs = {}
        for f, x, y in rest:
            d = f.replace("%", "/").rsplit("/", 1)[0]
            dirs[d] = dirs.get(d, 0) + 1
        print("  flag tests only, elsewhere: %d file(s) -- %s -- %d flag test(s) then %d"
              % (len(rest), ", ".join("%s/ %d" % kv for kv in sorted(dirs.items())),
                 sum(x for f, x, y in rest), sum(y for f, x, y in rest)))
        print("  flag tests in all %d: %d then %d -- %d drop(s) made unconditional"
              % (len(flag), sum(x for f, x, y in flag), sum(y for f, x, y in flag),
                 sum(x - y for f, x, y in flag)))
    for f, x, y in diff:
        print("  DIFFERENT: %s" % f[:-3].replace("%", "/"))
    for s in show:
        k = s.replace("/", "%") + ".ll"
        subprocess.run(["diff", os.path.join(a, k + ".norm"), os.path.join(b, k + ".norm")])


def edges(a, b, harness):
    """Each pair's `irscan.edges` -- B-2's second layer, the harness's own reader -- and its two `target` lines."""
    sys.path.insert(0, harness)
    import irscan
    both = sorted(f for f in os.listdir(a) if f.endswith(".ll") and os.path.exists(os.path.join(b, f)))
    differ, tdiff = [], []
    for f in both:
        x = open(os.path.join(a, f), errors="replace").read()
        y = open(os.path.join(b, f), errors="replace").read()
        if set(irscan.edges(x)) != set(irscan.edges(y)):
            differ.append(f[:-3].replace("%", "/"))
        if [l for l in x.split("\n") if l.startswith("target ")] != [l for l in y.split("\n") if l.startswith("target ")]:
            tdiff.append(f[:-3].replace("%", "/"))
    print("%d pair(s): irscan's edge set the same in %d, its two `target` lines the same in %d"
          % (len(both), len(both) - len(differ), len(both) - len(tdiff)))
    for f in differ:
        print("  edges differ: %s" % f)
    for f in tdiff:
        print("  target lines differ: %s" % f)


def main(argv):
    if len(argv) == 5 and argv[1] == "edges":
        edges(argv[2], argv[3], argv[4])
        return 0
    if len(argv) == 5 and argv[1] == "run":
        run(argv[2], argv[3], argv[4])
    elif len(argv) >= 5 and argv[1] == "compare":
        show = argv[6:] if len(argv) > 6 and argv[5] == "--show" else []
        compare(argv[2], argv[3], argv[4], show)
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

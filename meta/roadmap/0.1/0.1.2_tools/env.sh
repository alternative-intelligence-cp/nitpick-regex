# meta/roadmap/0.1/0.1.2_tools/env.sh -- sourced at the top of EVERY command block of
# `0.1.2.md`, because a Bash call keeps no variables and no functions from the call
# before it. Set REPO first, to the dispatch's REPO line:
#
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/0.1/0.1.2_tools/env.sh"
#
# 0.1.1b's helpers -- `codes`, `harness`, `ctl`, `run4` -- and this subcycle's: `harness_in`
# (the full run with its scratch inside this repository), `probe19` (probe 19 at a depth,
# both legs, once or twenty times), `nrcheck` (`check_no_recursion` alone), `selfcase` (one
# self-check case alone, on the harness as it is or mutated), `repro_once` (B-4's step
# alone) and `t075` (the compiler's own recursion analysis over a tree's `src/`). `$NPK_TREE`
# is read with `git` read commands only. Every `rm` names its target through `${VAR:?}`.
# Nothing prints a path above the repository, so no output carries a home directory into
# a record.
#
# THE WORKBENCH IS `$REPO/..`, as for every plan before this one, unless `PLAN_WB` names
# it -- which only a rehearsal in a clone outside the workbench does (the plan's §9).
: "${REPO:?set REPO to the REPO line of the dispatch, first}"
REPO=$(realpath "$REPO")
WB=$(realpath "${PLAN_WB:-$REPO/..}")
NPK_TREE=$(realpath "$WB/../nitpick")
PIN=5fbaf4a                                   # the pin this subcycle is planned and rehearsed at
PIN_FULL=5fbaf4a40a2f6b213754cd71b6c69700f8aa2c87
NPKC=$WB/.internal/toolchain/$PIN/npkc
NPKRT=$WB/.internal/toolchain/$PIN/npkrt.o
# `harness/baseline/rx120.sh`'s historical leg looks for `950bb1d` under
# `$REPO/../.internal/toolchain/`; it is named here, so the leg runs wherever the clone is.
NPKC_950BB1D=$WB/.internal/toolchain/950bb1d/npkc
T=$REPO/meta/roadmap/0.1/0.1.2_tools        # these tools
A=$REPO/.internal/n12                         # gitignored scratch
export NPKC NPKRT NPKC_950BB1D                 # the harness reads them from the ENVIRONMENT
# The harness's scratch is `tempfile`'s, so `TMPDIR` decides where it is. Every block runs
# with it unset -- `/tmp` -- but the two that put it inside this repository on purpose.
unset TMPDIR
mkdir -p "$A"

# Compile each file as a root from its own directory and print `<file> at <pin>:` and
# each diagnostic's code and site -- `L:C` in the file itself, `<name>:L:C` in another
# -- or `compiles`.        codes <pin> <file>...     (a relative file is the repository's)
codes() {
  local pin=$1; shift
  local cc=$WB/.internal/toolchain/$pin/npkc f src out b
  for f in "$@"; do
    src=$f; [ "${f#/}" = "$f" ] && src="$REPO/$f"
    b=$(basename "$src")
    out=$(cd "$(dirname "$src")" && "$cc" "$b" -o /dev/null 2>&1)
    if [ -z "$out" ]; then echo "$b at $pin compiles"; continue; fi
    echo "$b at $pin: $(echo "$out" | grep -oE '^NITPICK-[A-Z]+-[0-9]+ [^ ]+:[0-9]+:[0-9]+' \
      | sed -E "s|^(NITPICK-[A-Z]+-[0-9]+) ([^ ]*/)?([^/ ]+):([0-9]+):([0-9]+)$|\1 \3:\4:\5|; s| $b:| |" \
      | tr '\n' ' ' | sed 's/ $//')"
  done
}

# The full harness at the pin, its log kept, its summary printed: the exit, the target, the
# self-check's count, every tree check by name, the repro step, the units and the verdict.
#     harness <label>            (its scratch in /tmp)
#     harness_in <label>         (its scratch in $A/tmp, inside this repository)
harness() {
  free -g | awk '/^Mem:/ {print "available GiB:", $7}'
  ( cd "$REPO" && python3 -B harness/run.py ) > "$A/$1.log" 2>&1
  echo "harness exit $?"
  _summary "$A/$1.log"
}
harness_in() {
  free -g | awk '/^Mem:/ {print "available GiB:", $7}'
  rm -rf "${A:?}/tmp"; mkdir -p "$A/tmp"
  ( cd "$REPO" && TMPDIR="$A/tmp" python3 -B harness/run.py ) > "$A/$1.log" 2>&1
  echo "harness exit $? (TMPDIR inside the repository)"
  echo "left in its scratch: $(find "$A/tmp" -mindepth 1 | wc -l)"
  rm -rf "${A:?}/tmp"
  _summary "$A/$1.log"
}
_summary() {
  grep -E '^ok    target|live, [0-9]+ pending|^ok    repro|unit\(s\) passed|^GREEN|^THE SELF-CHECK FAILED' "$1" | cut -c1-150
  grep -E '^FAIL  [a-z]' "$1" | grep -v '^FAIL  self-check case' | cut -c1-150
  echo "self-check cases failed: $(grep -c '^FAIL  self-check case' "$1"); lines naming repro's failure: $(grep -c '| FAIL  repro: repro: two builds' "$1")$(grep -m1 '| FAIL  repro: repro: two builds' "$1" | sed -E 's/.*DIFFERENT IR -- ([0-9]+ and [0-9]+ bytes).*/, the first \1/')"
  echo "tree checks: $(grep -oE '^  (ok  |FAIL|note)  check_[a-z_]+' "$1" | awk '{print $2}' | tr '\n' ' ')"
}

# A copy of the working tree AS IT STANDS -- tracked and new files, not the ignored --
# at $A/ctl/<name>, for a control to change one thing in. Prints nothing.
#     ctl <name>
ctl() {
  local d="$A/ctl/$1"
  rm -rf "${d:?}"; mkdir -p "$d"
  ( cd "$REPO" && git ls-files -co --exclude-standard -z | xargs -0 tar -cf - ) | tar -xf - -C "$d"
}

# Build a program and run it at -O0 and through `opt -O2`: `npkc`, `llc`, `ld.lld`, the
# binary -- all four, because `npkc` exit 0 is not well-formedness (O-N11).
#     run4 <file>...     (at $PIN)
run4() {
  local f src b o r0 r2
  mkdir -p "$A/run4"
  for f in "$@"; do
    src=$f; [ "${f#/}" = "$f" ] && src="$REPO/$f"
    b=$(basename "$src" .npk); o="$A/run4/$b"
    if ! ( cd "$(dirname "$src")" && "$NPKC" "$(basename "$src")" -o "$o.ll" ) > "$o.npkc" 2>&1; then
      echo "$b: npkc refused -- $(grep -oE '^NITPICK-[A-Z]+-[0-9]+' "$o.npkc" | sort -u | tr '\n' ' ')"; continue
    fi
    llc -O0 -filetype=obj -relocation-model=static "$o.ll" -o "$o.o" && ld.lld -static "$o.o" "$NPKRT" -o "$o"
    "$o" > /dev/null 2>&1; r0=$?
    opt -O2 -S "$o.ll" -o "$o.2.ll" && llc -O2 -filetype=obj -relocation-model=static "$o.2.ll" -o "$o.2.o" \
      && ld.lld -static "$o.2.o" "$NPKRT" -o "$o.2"
    "$o.2" > /dev/null 2>&1; r2=$?
    echo "$b: -O0 $r0, -O2 $r2"
  done
}

# Probe 19 as the working tree holds it, its `LEVELS` set to each depth, built at both legs
# and run once -- or, with -20, twenty times a leg, each exit counted.
#     probe19 [-20] <levels>...
probe19() {
  local n=1 lv d o r0 r2 k
  [ "$1" = -20 ] && { n=20; shift; }
  d="$A/p19"; mkdir -p "$d"
  for lv in "$@"; do
    sed "s/^fixed int64:LEVELS = 1048576i64;$/fixed int64:LEVELS = ${lv}i64;/" \
      "$REPO/tests/probe/probe19_native_recursion_traps.npk" > "$d/probe19_native_recursion_traps.npk"
    o="$d/p"
    ( cd "$d" && "$NPKC" probe19_native_recursion_traps.npk -o p.ll ) || { echo "$lv: npkc refused"; continue; }
    llc -O0 -filetype=obj -relocation-model=static "$o.ll" -o "$o.o" && ld.lld -static "$o.o" "$NPKRT" -o "$o.0"
    opt -O2 -S "$o.ll" -o "$o.2.ll" && llc -O2 -filetype=obj -relocation-model=static "$o.2.ll" -o "$o.2.o" \
      && ld.lld -static "$o.2.o" "$NPKRT" -o "$o.2"
    r0=$(for k in $(seq $n); do "$o.0" > /dev/null 2>&1; echo $?; done | sort | uniq -c | awk '{printf "%s%s", (NR>1?"+":""), ($1>1?$1" x ":"") $2}')
    r2=$(for k in $(seq $n); do "$o.2" > /dev/null 2>&1; echo $?; done | sort | uniq -c | awk '{printf "%s%s", (NR>1?"+":""), ($1>1?$1" x ":"") $2}')
    echo "$lv levels: -O0 $r0, -O2 $r2"
  done
}

# `check_no_recursion` alone over a tree (the working tree by default): its verdict, what it
# examined, and each failure's first 160 characters.        nrcheck [<tree>]
nrcheck() {
  python3 -B - "${1:-$REPO}" <<'PY'
import os, sys
root = sys.argv[1]
sys.path.insert(0, os.path.join(root, "harness"))
import treecheck
r = treecheck.check_no_recursion(root)
print("check_no_recursion:", "ok" if r.ok else "FAIL", "|", r.examined)
for f in r.failures:
    print("   ", f[:160])
PY
}

# One self-check case alone, on the instrument, on the working tree's harness -- or on a
# harness with one thing broken, to show the case can fail:
#   self-only    check_no_recursion reports a self-call and no other cycle
#   global       a call resolves to every function of its name, its own file's not first
#   signal-as-0  the runner reads a process killed by a signal as a clean exit
#     selfcase <n> [<mutation>]
selfcase() {
  python3 -B - "$REPO" "$1" "${2:-}" <<'PY'
import os, sys, types
root, num, mut = sys.argv[1], int(sys.argv[2]), sys.argv[3]
sys.path.insert(0, os.path.join(root, "harness"))
import treecheck, build
if mut == "self-only":
    treecheck._cyclic_groups = lambda nodes, edges: [[v] for v in nodes if v in edges.get(v, ())]
elif mut == "global":
    src = open(os.path.join(root, "harness", "treecheck.py"), encoding="utf-8").read()
    old = "targets = [rel] if rel in owners[callee] else owners[callee]"
    assert src.count(old) == 1
    m = types.ModuleType("treecheck")
    m.__file__ = os.path.join(root, "harness", "treecheck.py")
    exec(compile(src.replace(old, "targets = owners[callee]"), m.__file__, "exec"), m.__dict__)
    sys.modules["treecheck"] = m
elif mut == "signal-as-0":
    real = build.Run.__init__
    def masked(self, *a, **k):
        real(self, *a, **k)
        if isinstance(self.code, int) and self.code < 0:
            self.code = 0
    build.Run.__init__ = masked
import selfcheck
case = [c for c in selfcheck.CASES if c.num == num][0]
o = selfcheck._run_case(case, False)
print(f"case {num}{' against ' + mut if mut else ''}:", "passes" if o.ok else "RED", "|", o.detail[:170])
PY
}

# B-4's `repro` step alone, over the working tree, its scratch made under `<where>` --
# `tmp` for /tmp, `in` for $A/tmp inside this repository -- and, with `forget`, the copies
# made WITHOUT their manifest, as the step made them until cycle 0.1.2. Prints the verdict.
#     repro_once tmp|in [forget]
repro_once() {
  local base=""
  if [ "$1" = in ]; then rm -rf "${A:?}/tmp"; mkdir -p "$A/tmp"; base="$A/tmp"; fi
  python3 -B - "$REPO" "$base" "${2:-}" <<'PY'
import os, sys, shutil, tempfile
root, base, forget = sys.argv[1], sys.argv[2] or None, sys.argv[3] == "forget"
sys.path.insert(0, os.path.join(root, "harness"))
import build, manifest
m = manifest.read(os.path.join(root, "nitpick.toml"))
tmp = tempfile.mkdtemp(prefix="nregex-harness-", dir=base)
c = build.Ctx(root, m, os.environ["NPKC"], os.environ["NPKRT"], tmp, lambda s: None)
real = shutil.copy
if forget:
    shutil.copy = lambda a, b, *k, **kw: None if a.endswith("nitpick.toml") else real(a, b, *k, **kw)
import re
paths = []
try:
    fl = build.repro(c, "tests/conformance/import.npk")
    a = os.path.join(tmp, "repro-a", "repro.ll")
    size = os.path.getsize(a) if os.path.exists(a) else 0
    for d in ("repro-a", os.path.join("repro", "deeper", "repro-b-with-a-longer-name")):
        ll = open(os.path.join(tmp, d, "repro.ll"), encoding="utf-8", errors="replace").read()
        m = re.search(r'^@npk\.sitep\.[0-9]+ = .*c"([^"]*import\.npk)"', ll, re.M)
        paths.append(m.group(1) if m else "?")
    intree = os.path.join(tmp, "intree.ll")
    build.emit(c, "tests/conformance/import.npk", intree, cwd=root)
    same = open(intree, "rb").read() == open(a, "rb").read()
finally:
    shutil.copy = real
    shutil.rmtree(tmp)
where = "in the repository" if base else "in /tmp"
how = "without their manifest" if forget else "as the step makes them"
print(f"repro {where}, the copies {how}:", fl[0][:112] if fl else f"byte-identical, {size} B")
print("   copy A against the in-tree build:", "byte-identical" if same else "DIFFERENT")
if fl:
    tail = os.path.basename(tmp)
    print("   the entry's site path, copy A:", paths[0].replace(tail, "<scratch>"))
    print("   the entry's site path, copy B:", paths[1].replace(tail, "<scratch>"))
PY
  [ "$1" = in ] && rm -rf "${A:?}/tmp"
  return 0
}

# The compiler's own recursion analysis over a copy of a tree's `src/` (the working tree's by
# default): `decreases 0i64` written on every function, every module compiled as a root, and
# the functions reported `NITPICK-TYPE-075` -- "a `decreases` on a function in no recursive
# group" (the compiler's D-304 (5)) -- counted against the functions written on.
#     t075 [<tree>]
t075() {
  local t=${1:-$REPO} d="$A/t075" f
  rm -rf "${d:?}"; mkdir -p "$d"; cp -r "$t/src" "$d/src"
  python3 -B - "$d" "$REPO/harness" <<'PY'
import os, re, sys
root = sys.argv[1]
sys.path.insert(0, sys.argv[2])
import lexical
n = 0
for dp, dn, fn in os.walk(os.path.join(root, "src")):
    for f in sorted(fn):
        if not f.endswith(".npk"):
            continue
        p = os.path.join(dp, f)
        text = lexical.read(p)
        code = lexical.blank(text)
        out, last = [], 0
        for m in re.finditer(r"(?<![A-Za-z0-9_])func\s*:\s*[A-Za-z_]\w*", code):
            i, depth = m.end(), 0
            while i < len(code):
                if code[i] == "(":
                    depth += 1
                elif code[i] == ")":
                    depth -= 1
                elif code[i] == "{" and depth == 0:
                    break
                i += 1
            k = code[m.end():i].rfind("never fails")
            at = m.end() + k if k >= 0 else i
            out.append(text[last:at]); out.append("decreases 0i64 "); last = at
            n += 1
        out.append(text[last:])
        with open(p, "w", encoding="latin-1", newline="") as fh:
            fh.write("".join(out))
open(os.path.join(root, "count"), "w").write(str(n))
PY
  for f in $(cd "$d" && find src -name '*.npk' | sort); do
    ( cd "$d/$(dirname "$f")" && "$NPKC" "$(basename "$f")" -o /dev/null 2>&1 )
  done | grep -oE '^NITPICK-[A-Z]+-[0-9]+ [^ ]+:[0-9]+:[0-9]+' | sort -u > "$d/sites"
  echo "decreases written on $(cat "$d/count") function(s); NITPICK-TYPE-075 at $(grep -c '^NITPICK-TYPE-075 ' "$d/sites"); any other code: $(grep -vc '^NITPICK-TYPE-075 ' "$d/sites")"
}

# meta/roadmap/0.2/0.2.0_tools/env.sh -- sourced at the top of EVERY command block of `0.2.0.md`, because a Bash call
# keeps no variables and no functions from the call before it. Set REPO first, to the dispatch's REPO line:
#
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/0.2/0.2.0_tools/env.sh"
#
# 0.1.6b's helpers -- `codes`, `harness`, `ctl`, `run4`, `dryrun` and `tcheck` -- with `reach`, a `harness` that takes a
# tree, a Python `mutants` over all nine of this subcycle's units, and `price`, pointed at this subcycle's tools and its
# scratch, `.internal/w020`. The paths are the CHECKOUT's: `WB` is the directory above it and `NPK_TREE` the compiler
# beside that, so a block run in a relocated copy finds another workbench or none -- run the blocks in the checkout the
# dispatch names (the plan's §0). `$NPK_TREE` is read with `git show` alone. Every `rm` names its target through
# `${VAR:?}`. Nothing prints a path above the repository, so no output carries a home directory into a record.
#
# THE LIBRARIES' PRIVATE LLVM 20.1.2 IS FIRST ON PATH (the workbench's question 24, option (c)): byte-identical to the
# release this machine ran when the libraries pinned it, so the harness's `llc`, `opt` and `ld.lld` stay the pinned patch
# release when the machine's own LLVM moves to 20.1.8. Block 0a prints what `llc` reports through it; anything but
# 20.1.2 is a toolchain mismatch, and a stop.
#
# TMPDIR IS THE REPOSITORY'S OWN SCRATCH, `$A/tmp`, as for 0.1.6b: the sandbox refuses a plain `/tmp`, and RX-195 made a
# `TMPDIR` inside the repository safe for B-4's `repro`. THE RUN IS DATED ONCE: `apply.py` writes the first step's day
# to `$A/date`, and every `@@RUN_DATE@@` of every step becomes that day.
: "${REPO:?set REPO to the REPO line of the dispatch, first}"
REPO=$(realpath "$REPO")
WB=$(realpath "$REPO/..")
NPK_TREE=$(realpath "$WB/../nitpick")
PIN=5fbaf4a                                   # the pin this subcycle is planned and rehearsed at
PIN_FULL=5fbaf4a40a2f6b213754cd71b6c69700f8aa2c87
NPKC=$WB/.internal/toolchain/$PIN/npkc
NPKRT=$WB/.internal/toolchain/$PIN/npkrt.o
LLVM_BIN=$WB/.internal/toolchain/llvm-20.1.2/root/usr/lib/llvm-20/bin
T=$REPO/meta/roadmap/0.2/0.2.0_tools          # these tools
A=$REPO/.internal/w020                         # gitignored scratch
CHECK=$HOME/.claude/skills/npk/skills/check/scripts
mkdir -p "$A/tmp"
TMPDIR=$A/tmp
case ":$PATH:" in *":$LLVM_BIN:"*) ;; *) PATH=$LLVM_BIN:$PATH ;; esac
export NPKC NPKRT TMPDIR PATH A                 # the harness reads them from the ENVIRONMENT

# Compile each file as a root from its own directory and print `<file> at <pin>:` and each diagnostic's code and
# site -- `L:C` in the file itself, `<name>:L:C` in another -- or `compiles`.
#     codes <pin> <file>...     (a relative file is the repository's)
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

# The identities `NITPICK-REACH-003` names for a root that imports <file> and declares no `failsafe`: the root is
# written in `$A/reach`, importing the file by its relative path, compiled, and removed.
#     reach <file>...     (a relative file is the repository's)
reach() {
  local f src d="$A/reach" r
  mkdir -p "$d"; r="$d/zz_reach_root.npk"
  for f in "$@"; do
    src=$f; [ "${f#/}" = "$f" ] && src="$REPO/$f"
    printf 'mod:zz_reach_root;\n\nuse "%s".*;\n\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n' \
      "$(realpath --relative-to="$d" "$src")" > "$r"
    echo "$(basename "$src"): $(cd "$d" && "$NPKC" zz_reach_root.npk -o /dev/null 2>&1 \
      | grep -oE '[0-9]+ identities: [^-]*' | sed 's/ *$//')"
  done
  rm -rf "${d:?}"
}

# The full harness over a tree -- the checkout by default -- its log kept as `$A/<label>.log`, and its summary printed:
# the exit, the target, the self-check's count, the repro step, the units and the verdict, every FAIL line, the six
# suites' sizes and B-2's scan count, and every tree check by name.
#     harness <label> [<tree>]
harness() {
  free -g | awk '/^Mem:/ {print "available GiB:", $7}'
  ( cd "${2:-$REPO}" && python3 -B harness/run.py ) > "$A/$1.log" 2>&1
  echo "harness exit $?"
  grep -E '^ok    target|live, [0-9]+ pending|^ok    repro|unit\(s\) passed|^GREEN|^THE SELF-CHECK FAILED' "$A/$1.log" | cut -c1-150
  grep -E '^FAIL  [a-z]|^  FAIL  ' "$A/$1.log" | cut -c1-150
  echo "suites: $(grep -E '^      [a-z-]+  \([a-z/]+\)  [0-9]+ unit\(s\)$' "$A/$1.log" | awk '{print $1, $3}' \
    | paste -sd, - | sed 's/,/, /g'); B-2's scans on $(grep -oE "B-2's two scans ran on [0-9]+" "$A/$1.log" | grep -oE '[0-9]+$')"
  echo "tree checks: $(grep -oE '^  (ok  |FAIL|note)  check_[a-z_]+' "$A/$1.log" | awk '{print $2}' | tr '\n' ' ')"
}

# A copy of the working tree AS IT STANDS -- tracked and new files, not the ignored -- at $A/ctl/<name>, for a control
# or a mutant to change one thing in. Prints nothing.
#     ctl <name>
ctl() {
  local d="$A/ctl/$1"
  rm -rf "${d:?}"; mkdir -p "$d"
  ( cd "$REPO" && git ls-files -co --exclude-standard -z | xargs -0 tar -cf - ) | tar -xf - -C "$d"
}

# Build a program and run it at -O0 and through `opt -O2`: `npkc`, `llc`, `ld.lld`, the binary -- all four, because
# `npkc` exit 0 is not well-formedness (O-N11).
#     run4 <file>...     (a relative file is the repository's)
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

# The steps' patches applied in order to a throwaway clone of HEAD -- the check that the tree is the one they were
# cut from, before any is applied here. `--shared`, so it costs no object copy.
#     dryrun <step>...
dryrun() {
  local d="$A/dry" n
  rm -rf "${d:?}"; git clone -q --shared "$REPO" "$d"
  for n in "$@"; do python3 -B "$T/apply.py" "$n" "$d" | sed 's/^/dry run: /'; done
  rm -rf "${d:?}"
}

# A tree check over the working tree -- or a tree given -- with the checks of the working tree or of another: its
# verdict, what it examined, and each finding's first line.
#     tcheck <name> [<tree>] [<checks-tree>]
tcheck() {
  python3 -B - "${3:-$REPO}" "$1" "${2:-$REPO}" <<'PY'
import os, sys
sys.path.insert(0, os.path.join(sys.argv[1], "harness"))
import treecheck
r = getattr(treecheck, sys.argv[2])(sys.argv[3])
print("%s: %s | %s" % (r.name, "ok" if r.ok else "FAIL", r.examined))
for f in r.failures:
    print("  " + f.splitlines()[0][:150])
PY
}

# Every tree check's `examined` line, over a tree with that tree's own checks -- a check reads its tree, and run from
# another tree's harness it reads the wrong one's exemptions -- and the notes of the two that count declarations.
#     tchecks <tree>
tchecks() {
  python3 -B - "$1" <<'PY'
import os, sys
root = sys.argv[1]
sys.path.insert(0, os.path.join(root, "harness"))
import treecheck
for fn in treecheck.ALL:
    r = fn(root)
    print("  %s: %s | %s" % (r.name, "ok" if r.ok else "FAIL", r.examined))
    if r.name in ("check_vec_elements_own_nothing", "check_no_recursion"):
        for n in r.notes[1:] if r.name == "check_no_recursion" else r.notes[:1]:
            print("      " + n[:150])
PY
}

# The mutants of `$T/mutants.tsv` whose step list holds <step>, over <tree>: `mutants.py`, four rows at a time.
#     mutants <step> [<tree>]
mutants() {
  python3 -B "$T/mutants.py" "${2:-$REPO}" "$1" 4
}

# The README's price paragraph, as it stands: its lines -- a link's `](` printed `] (`, so the block's Expect quoting it
# is no link `check_refs` must resolve from the plan, which reads fenced text too -- whether each link resolves from the
# README, and whether, its one parenthetical aside apart, it is the author's words of `$T/price_paragraph.txt`, word for
# word.
price() {
  python3 -B - "$REPO/README.md" "$T/price_paragraph.txt" <<'PY'
import os, re, sys
lines = open(sys.argv[1], encoding="utf-8").read().split("\n")
i = next(k for k, l in enumerate(lines) if l.startswith("**The price is stated plainly"))
j = next(k for k in range(i, len(lines)) if not lines[k].strip())
print("README.md %d-%d:" % (i + 1, j))
for l in lines[i:j]:
    print("  " + l.replace("](", "] ("))
para = " ".join(lines[i:j])
for t in re.findall(r"\]\(([^)]+)\)", para):
    print("its link to %s: %s from README.md" % (t, "resolves" if os.path.exists(os.path.join(os.path.dirname(sys.argv[1]), t)) else "DOES NOT RESOLVE"))
aside = " ([`meta/specs/SAFETY.md`](meta/specs/SAFETY.md) S-2, RX-218)"
words = " ".join(open(sys.argv[2], encoding="utf-8").read().split())
print("its aside: %s" % ("present, once" if para.count(aside) == 1 else "MISSING"))
print("the rest, against the author's words: %s" % ("word for word" if para.replace(aside, "") == words else "DIFFERS"))
PY
}

# meta/roadmap/0.2/0.2.2_tools/env.sh -- sourced at the top of EVERY command block of `0.2.2.md`, because a Bash call
# keeps no variables and no functions from the call before it. Set REPO first, to the dispatch's REPO line:
#
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/0.2/0.2.2_tools/env.sh"
#
# 0.2.1's helpers -- `codes`, `reach`, `harness`, `run4`, `dryrun`, `tchecks` and `mutants` -- pointed at this
# subcycle's tools, its scratch `.internal/w022` and the pin `7e91730`, whose LLVM, 20.1.8, is the machine's own:
# `llc`, `opt` and `ld.lld` are found on PATH as the shell has it, and block 0a prints what each reports -- anything but
# 20.1.8 is a toolchain mismatch, and a stop. `run4` and the mutants run a unit under its own `mem-cap-mib` cap, as the
# harness does, so the capped pair's control -- which asks for 12 GB -- never runs uncapped.
#
# The paths are the CHECKOUT's: `WB` is the directory above it and `NPK_TREE` the compiler beside that, so a block run
# in a relocated copy finds another workbench or none -- run the blocks in the checkout the dispatch names (the plan's
# §0). `$NPK_TREE` is read with `git show` and `git rev-parse` alone. Every `rm` names its target through `${VAR:?}`.
# Nothing prints a path above the repository, so no output carries a home directory into a record. TMPDIR is the
# repository's own scratch, `$A/tmp` (the sandbox refuses a plain `/tmp`; RX-195 made one inside the repository safe for
# B-4's `repro`). THE RUN IS DATED ONCE: `apply.py` writes the first step's day to `$A/date`, and every `@@DATE022@@` of
# every step becomes that day.
: "${REPO:?set REPO to the REPO line of the dispatch, first}"
REPO=$(realpath "$REPO")
WB=$(realpath "$REPO/..")
NPK_TREE=$(realpath "$WB/../nitpick")
PIN=7e91730                                   # the pin this subcycle is planned and rehearsed at
PIN_FULL=7e91730d19cffd35fcff25c36893cfaa2c01509e
NPKC=$WB/.internal/toolchain/$PIN/npkc
NPKRT=$WB/.internal/toolchain/$PIN/npkrt.o
T=$REPO/meta/roadmap/0.2/0.2.2_tools          # these tools
A=$REPO/.internal/w022                         # gitignored scratch
CHECK=$HOME/.claude/skills/npk/skills/check/scripts
mkdir -p "$A/tmp"
TMPDIR=$A/tmp
export NPKC NPKRT TMPDIR A T                   # the harness reads them from the ENVIRONMENT

# Compile each file as a root from its own directory and print `<file> at <pin>:` and each diagnostic's code and
# site -- `L:C` in the file itself, `<name>:L:C` in another -- or `compiles`.
#     codes <file>...     (a relative file is the repository's)
codes() {
  local f src out b
  for f in "$@"; do
    src=$f; [ "${f#/}" = "$f" ] && src="$REPO/$f"
    b=$(basename "$src")
    out=$(cd "$(dirname "$src")" && "$NPKC" "$b" -o /dev/null 2>&1)
    if [ -z "$out" ]; then echo "$b at $PIN compiles"; continue; fi
    echo "$b at $PIN: $(echo "$out" | grep -oE '^NITPICK-[A-Z]+-[0-9]+ [^ ]+:[0-9]+:[0-9]+' \
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

# The full harness over the checkout, its log kept as `$A/<label>.log`, and its summary printed: the exit, the LLVM
# it held, the target, the self-check's count, the repro step, rx120, the pending units, the units and the verdict,
# every FAIL line, the six suites' sizes and B-2's scan count, and every tree check by name.
#     harness <label>
harness() {
  free -g | awk '/^Mem:/ {print "available GiB:", $7}'
  ( cd "$REPO" && python3 -B harness/run.py ) > "$A/$1.log" 2>&1
  echo "harness exit $?"
  grep -E '^ok    llc |^ok    target|live, [0-9]+ pending|^ok    repro|^ok    rx120|^PEND  tests/|unit\(s\) PENDING and|unit\(s\) passed|^GREEN|^THE SELF-CHECK FAILED' "$A/$1.log" | cut -c1-150
  grep -E '^FAIL  [a-z]|^  FAIL  ' "$A/$1.log" | cut -c1-150
  echo "suites: $(grep -E '^      [a-z-]+  \([a-z/]+\)  [0-9]+ unit\(s\)$' "$A/$1.log" | awk '{print $1, $3}' \
    | paste -sd, - | sed 's/,/, /g'); B-2's scans on $(grep -oE "B-2's two scans ran on [0-9]+" "$A/$1.log" | grep -oE '[0-9]+$')"
  echo "tree checks: $(grep -oE '^  (ok  |FAIL|note)  check_[a-z_]+' "$A/$1.log" | awk '{print $2}' | tr '\n' ' ')"
}

# Build a program and run it at -O0 and through `opt -O2`: `npkc`, `llc`, `ld.lld`, the binary -- all four, because
# `npkc` exit 0 is not well-formedness (O-N11). A file that carries `// mem-cap-mib: N` runs under that address-space
# cap, `ulimit -v`, as the harness runs it -- after `/bin/true` under the same cap, whose exit is printed.
#     run4 <file>...     (a relative file is the repository's)
run4() {
  local f src b o r0 r2 cap pre
  mkdir -p "$A/run4"
  for f in "$@"; do
    src=$f; [ "${f#/}" = "$f" ] && src="$REPO/$f"
    b=$(basename "$src" .npk); o="$A/run4/$b"
    cap=$(grep -m1 -oE '^// mem-cap-mib: [0-9]+' "$src" | grep -oE '[0-9]+$')
    if ! ( cd "$(dirname "$src")" && "$NPKC" "$(basename "$src")" -o "$o.ll" ) > "$o.npkc" 2>&1; then
      echo "$b: npkc refused -- $(grep -oE '^NITPICK-[A-Z]+-[0-9]+' "$o.npkc" | sort -u | tr '\n' ' ')"; continue
    fi
    llc -O0 -filetype=obj -relocation-model=static "$o.ll" -o "$o.o" && ld.lld -static "$o.o" "$NPKRT" -o "$o"
    opt -O2 -S "$o.ll" -o "$o.2.ll" && llc -O2 -filetype=obj -relocation-model=static "$o.2.ll" -o "$o.2.o" \
      && ld.lld -static "$o.2.o" "$NPKRT" -o "$o.2"
    if [ -n "$cap" ]; then
      ( ulimit -v $((cap * 1024)); /bin/true ); pre="under ${cap} MiB, /bin/true $?: "
      ( ulimit -v $((cap * 1024)); "$o" > /dev/null 2>&1 ); r0=$?
      ( ulimit -v $((cap * 1024)); "$o.2" > /dev/null 2>&1 ); r2=$?
    else
      pre=""; "$o" > /dev/null 2>&1; r0=$?; "$o.2" > /dev/null 2>&1; r2=$?
    fi
    echo "$b: $pre-O0 $r0, -O2 $r2"
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

# The mutants of `$T/mutants.tsv` whose step list holds <step>, over the checkout: `mutants.py`, four rows at a time.
#     mutants <step>
mutants() {
  python3 -B "$T/mutants.py" "$REPO" "$1" 4
}

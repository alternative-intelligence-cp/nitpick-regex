# meta/roadmap/0.1/0.1.6a_tools/env.sh -- sourced at the top of EVERY command block of `0.1.6a.md`, because a Bash
# call keeps no variables and no functions from the call before it. Set REPO first, to the dispatch's REPO line:
#
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/0.1/0.1.6a_tools/env.sh"
#
# 0.1.5's helpers -- `codes`, `harness`, `ctl`, `run4` and `nrcheck` -- with `nitpick-time` 0.3.0's `dryrun` and a
# table-driven `mutants`, both legs, pointed at this subcycle's tools and its scratch, `.internal/n16a`. The paths
# are the CHECKOUT's: `WB` is the directory above it and `NPK_TREE` the compiler beside that, so a block run in a
# relocated copy finds another workbench or none -- run the blocks in the checkout the dispatch names (the plan's
# §0). `$NPK_TREE` is read with `git` read commands only. Every `rm` names its target through `${VAR:?}`. Nothing
# prints a path above the repository, so no output carries a home directory into a record.
#
# TMPDIR IS THE REPOSITORY'S OWN SCRATCH, `$A/tmp`, as for 0.1.5: the sandbox refuses a plain `/tmp`, and RX-195
# made a `TMPDIR` inside the repository safe for B-4's `repro`. THE RUN IS DATED ONCE: `apply.py` writes the first
# step's day to `$A/date`, and every `@@DATE@@` of every step becomes that day.
: "${REPO:?set REPO to the REPO line of the dispatch, first}"
REPO=$(realpath "$REPO")
WB=$(realpath "$REPO/..")
NPK_TREE=$(realpath "$WB/../nitpick")
PIN=5fbaf4a                                   # the pin this subcycle is planned and rehearsed at
PIN_FULL=5fbaf4a40a2f6b213754cd71b6c69700f8aa2c87
NPKC=$WB/.internal/toolchain/$PIN/npkc
NPKRT=$WB/.internal/toolchain/$PIN/npkrt.o
T=$REPO/meta/roadmap/0.1/0.1.6a_tools        # these tools
A=$REPO/.internal/n16a                        # gitignored scratch
CHECK=$HOME/.claude/skills/npk/skills/check/scripts
mkdir -p "$A/tmp"
TMPDIR=$A/tmp
export NPKC NPKRT TMPDIR                       # the harness reads them from the ENVIRONMENT

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

# The full harness at the pin, its log kept, its summary printed: the exit, the target, the self-check's count,
# every tree check by name, the repro step, the units and the verdict.
#     harness <label>
harness() {
  free -g | awk '/^Mem:/ {print "available GiB:", $7}'
  ( cd "$REPO" && python3 -B harness/run.py ) > "$A/$1.log" 2>&1
  echo "harness exit $?"
  grep -E '^ok    target|live, [0-9]+ pending|^ok    repro|unit\(s\) passed|^GREEN|^THE SELF-CHECK FAILED' "$A/$1.log" | cut -c1-150
  grep -E '^FAIL  [a-z]' "$A/$1.log" | cut -c1-150
  echo "tree checks: $(grep -oE '^  (ok  |FAIL|note)  check_[a-z_]+' "$A/$1.log" | awk '{print $2}' | tr '\n' ' ')"
}

# A copy of the working tree AS IT STANDS -- tracked and new files, not the ignored -- at $A/ctl/<name>, for a
# control or a mutant to change one thing in. Prints nothing.
#     ctl <name>
ctl() {
  local d="$A/ctl/$1"
  rm -rf "${d:?}"; mkdir -p "$d"
  ( cd "$REPO" && git ls-files -co --exclude-standard -z | xargs -0 tar -cf - ) | tar -xf - -C "$d"
}

# Build a program and run it at -O0 and through `opt -O2`: `npkc`, `llc`, `ld.lld`, the binary -- all four,
# because `npkc` exit 0 is not well-formedness (O-N11).
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

# A unit against the tree before this step: a copy of the tree as it stands with the named files put back to
# HEAD's, the unit built and run at both legs -- the red-first control.
#     control <name> <unit> <file>...
control() {
  local name=$1 unit=$2 f; shift 2
  ctl "$name"
  for f in "$@"; do git -C "$REPO" show "HEAD:$f" > "$A/ctl/$name/$f"; done
  run4 "$A/ctl/$name/$unit"
  rm -rf "${A:?}/ctl/$name"
}

# `check_no_recursion` alone over the working tree: its verdict and what it examined.
nrcheck() {
  python3 -B - "$REPO" <<'PY'
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

# The steps' patches applied in order to a throwaway clone of HEAD -- the check that the tree is the one they were
# cut from, before any is applied here. `--shared`, so it costs no object copy.
#     dryrun <step>...
dryrun() {
  local d="$A/dry" n
  rm -rf "${d:?}"; git clone -q --shared "$REPO" "$d"
  for n in "$@"; do python3 -B "$T/apply.py" "$n" "$d" | sed 's/^/dry run: /'; done
  rm -rf "${d:?}"
}

# The mutants of `$T/mutants.tsv` for one step -- each row a step, a name, a file, the text, its replacement and a
# unit, TAB-separated, `\n` a newline -- one replacement in a copy of the tree as it stands, counted as matching
# ONCE, and the unit built and run on both legs. Prints `<name>: <unit> -O0 <exit>, -O2 <exit>`.
#     mutants <step>
mutants() {
  local want=$1 step name file old new unit d r0 r2 u
  while IFS=$'\t' read -r step name file old new unit; do
    case "$step" in ''|'#'*) continue;; esac
    [ "$step" = "$want" ] || continue
    ctl "mut_$name"; d="$A/ctl/mut_$name"
    python3 -B - "$d/$file" "$old" "$new" <<'PY' || { echo "$name: not applied"; rm -rf "${A:?}/ctl/mut_$name"; continue; }
import sys
p, old, new = sys.argv[1], sys.argv[2].replace("\\n", "\n"), sys.argv[3].replace("\\n", "\n")
s = open(p, encoding="utf-8").read()
if s.count(old) != 1:
    print("STOP: %d occurrence(s) of %r in %s" % (s.count(old), old[:60], p.split("/")[-1]))
    sys.exit(1)
open(p, "w", encoding="utf-8").write(s.replace(old, new))
PY
    u="$d/tests/unit/$unit.npk"
    if ! ( cd "$(dirname "$u")" && "$NPKC" "$unit.npk" -o "$d/u.ll" ) > "$d/u.npkc" 2>&1; then
      echo "$name: $unit npkc refused -- $(grep -oE '^NITPICK-[A-Z]+-[0-9]+' "$d/u.npkc" | sort -u | tr '\n' ' ')"
    else
      llc -O0 -filetype=obj -relocation-model=static "$d/u.ll" -o "$d/u.o" && ld.lld -static "$d/u.o" "$NPKRT" -o "$d/u0" \
        && opt -O2 -S "$d/u.ll" -o "$d/u2.ll" && llc -O2 -filetype=obj -relocation-model=static "$d/u2.ll" -o "$d/u2.o" \
        && ld.lld -static "$d/u2.o" "$NPKRT" -o "$d/u2"
      "$d/u0" > /dev/null 2>&1; r0=$?; "$d/u2" > /dev/null 2>&1; r2=$?
      echo "$name: $unit -O0 $r0, -O2 $r2"
    fi
    rm -rf "${A:?}/ctl/mut_$name"
  done < "$T/mutants.tsv"
}

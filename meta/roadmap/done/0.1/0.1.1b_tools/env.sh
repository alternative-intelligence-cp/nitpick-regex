# meta/roadmap/0.1/0.1.1b_tools/env.sh -- sourced at the top of EVERY command block of
# `0.1.1b.md`, because a Bash call keeps no variables and no functions from the call
# before it. Set REPO first, to the dispatch's REPO line:
#
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/0.1/0.1.1b_tools/env.sh"
#
# `0.1.1_tools/env.sh`'s helpers, and three for this subcycle: `irsame` (the IR of
# every program before and after a step), `vcheck` (the element check alone over a
# tree) and `bound` (the type's bound written into a copy). `$NPK_TREE` is read with
# `git` read commands only. Every `rm` names its target through `${VAR:?}`. Nothing
# prints a path above the repository, so no output carries a home directory into a
# record. TMPDIR is left alone: the harness's repro check fails when its scratch sits
# under this repository (measured at planning -- the plan's §4).
: "${REPO:?set REPO to the REPO line of the dispatch, first}"
REPO=$(realpath "$REPO")
WB=$(realpath "$REPO/..")
NPK_TREE=$(realpath "$WB/../nitpick")
PIN=5fbaf4a                                   # the pin this subcycle is planned and rehearsed at
PIN_FULL=5fbaf4a40a2f6b213754cd71b6c69700f8aa2c87
NPKC=$WB/.internal/toolchain/$PIN/npkc
NPKRT=$WB/.internal/toolchain/$PIN/npkrt.o
T=$REPO/meta/roadmap/0.1/0.1.1b_tools        # these tools
A=$REPO/.internal/r3b                          # gitignored scratch
export NPKC NPKRT                              # the harness reads them from the ENVIRONMENT
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

# The full harness at the pin, its log kept, its summary lines printed.
#     harness <label>
harness() {
  free -g | awk '/^Mem:/ {print "available GiB:", $7}'
  ( cd "$REPO" && python3 -B harness/run.py ) > "$A/$1.log" 2>&1
  echo "harness exit $?"
  grep -E 'unit\(s\) passed|^FAIL  [a-z]|^GREEN|RUNNER WAS SHOWN|^ok    target|^  (ok|FAIL)  +check_vec_elements_own_nothing|exempt as' \
    "$A/$1.log" | cut -c1-150
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

# The type's bound written into a copy's `vec.npk` and nothing else: `struct:Vec<T:
# Copy>`, and with `all`, every `pub func:vec_*<T>` too.      bound <tree> [all]
bound() {
  sed -i 's/^pub struct:Vec<T> = {$/pub struct:Vec<T: Copy> = {/' "$1/src/core/vec.npk"
  [ "$2" = all ] && sed -i -E 's/^(pub func:vec_[a-z_]+)<T> = /\1<T: Copy> = /' "$1/src/core/vec.npk"
  return 0
}

# Every program and root under src/, tests/unit, tests/conformance and harness/selfcheck
# that compiles both in HEAD's tree and in <tree> (the working tree by default), its IR
# compared after two masks: the site-line table, which a comment line moves, and the
# number in each generated `npk.drop.N`/`npk.vacant.N` name, which a removed
# declaration moves. Prints the count and every file whose masked IR differs.
#     irsame [<tree>]
irsame() {
  local t=${1:-$REPO} h="$A/ir/head" w="$A/ir" f k a b n=0 same=0 diff=""
  rm -rf "${h:?}" "${w:?}/x" "${w:?}/y"; mkdir -p "$h" "$w/x" "$w/y"
  git -C "$REPO" archive HEAD | tar -x -C "$h"
  for f in $(cd "$t" && find src tests/unit tests/conformance harness/selfcheck -name '*.npk' | sort); do
    [ -f "$h/$f" ] || continue
    k=$(echo "$f" | tr '/' '_')
    ( cd "$h/$(dirname "$f")" && "$NPKC" "$(basename "$f")" -o "$w/x/$k.ll" ) > /dev/null 2>&1; a=$?
    ( cd "$t/$(dirname "$f")" && "$NPKC" "$(basename "$f")" -o "$w/y/$k.ll" ) > /dev/null 2>&1; b=$?
    [ $a -eq 0 ] && [ $b -eq 0 ] || continue
    n=$((n + 1))
    if cmp -s <(_irmask "$w/x/$k.ll") <(_irmask "$w/y/$k.ll"); then same=$((same + 1)); else diff="$diff $f"; fi
  done
  echo "IR: $same of $n identical, HEAD against the tree, masked${diff:+; differs:$diff}"
}
_irmask() { grep -v '^@npk\.site\.lines = ' "$1" | sed -E 's/@"npk\.(drop|vacant)\.[0-9]+"/@"npk.\1.N"/g'; }

# `check_vec_elements_own_nothing` alone over a tree: its verdict, and its first failure
# or what it examined and exempted.        vcheck <tree>
vcheck() {
  python3 -B - "$1" <<'PY'
import os, sys
root = sys.argv[1]
sys.path.insert(0, os.path.join(root, "harness"))
import treecheck
r = treecheck.check_vec_elements_own_nothing(root)
if r.failures:
    f = r.failures[0]
    print("check_vec_elements_own_nothing: FAIL |", f.split(" -- the element")[0], "--",
          f.split("is not cleared: ")[1].split(". `Vec<T>`")[0])
else:
    ex = r.notes[0].split("; ")[1].split(" as ")[0] if r.notes else "?"
    print("check_vec_elements_own_nothing: ok |", r.examined.split(" -- ")[0] + ";", ex)
PY
}

# Every file under tests/ that imports `src/`, its verdict in the repository and in
# <tree>, printed where the two differ: `<file>: <before> -> <after>`, each a list of
# codes with their site counts, or `compiles`.        moved <tree>
moved() {
  local t=$1 f a b
  for f in $(cd "$REPO" && git grep -l -E '^use "(\.\./)+src/' -- 'tests/*.npk' | sort); do
    a=$(_verdict "$REPO/$f"); b=$(_verdict "$t/$f")
    [ "$a" = "$b" ] || echo "$(basename "$f"): $a -> $b"
  done
}
_verdict() {
  local out
  out=$(cd "$(dirname "$1")" && "$NPKC" "$(basename "$1")" -o /dev/null 2>&1)
  [ -z "$out" ] && { echo compiles; return; }
  echo "$out" | grep -oE '^NITPICK-[A-Z]+-[0-9]+' | sort | uniq -c | awk '{printf "%s x%s ", $2, $1}' | sed 's/ $//'
}

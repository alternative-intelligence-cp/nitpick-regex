# meta/roadmap/0.2/0.2.5a_tools/env.sh -- sourced at the top of EVERY command block of `0.2.5a.md`, because a Bash call
# keeps no variables and no functions from the call before it. Set REPO first, to the dispatch's REPO line:
#
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/0.2/0.2.5a_tools/env.sh"
#
# TWO PINS, ONE LLVM. The pin this subcycle adopts is `c9baa9e` (landing 118, carrying 104 … 118) and the pin it leaves
# is `7e91730` (landing 103), kept in the workbench's toolchain directory for the old pin's runs and the controls. BOTH
# run under the machine's own LLVM 20.1.8 -- the compiler's D-349 since its landing 99, which both commits carry -- so
# `leg <pin>` sets the compiler and the runtime object and nothing else: `llc`, `opt` and `ld.lld` are found on PATH as
# the shell has it, and `tools <pin>` prints what each reports under that pin. Anything but 20.1.8 is a toolchain
# mismatch, and a stop. The runtime object is byte-identical at both pins (`npkrt.o`, `c8e5033a…`, the anchor since
# landing 78), and block 0a says so with `cmp`.
#
# EVERY BYTE COMPARISON OF AN EMISSION ACROSS THE TWO PINS READS THROUGH THE COMPILER'S OWN NORMALISERS. Landing 115
# (DEF-251 half (i)) puts `null_pointer_is_valid` on every emitted `define`, so every program's text moves by that
# attribute; `attrnorm.py` strips it. Landing 105 (DEF-159) drops an address-taken owning binding's slot at every scope
# exit with no flag test; `dropnorm.py` strips the flag tests from both sides. `normtools` writes both, from `c9baa9e`
# by `git show`, into `$A/norm/` -- never run from the compiler's tree.
#
# The paths are the CHECKOUT's: `WB` is the directory above it, `NPK_TREE` the compiler beside that, and `CHECK` the
# workbench's own `skills/check/scripts` -- so a block run in a relocated copy finds another workbench or none: run the
# blocks in the checkout the dispatch names (the plan's §0). `$NPK_TREE` is read with `git show`, `git diff`,
# `git rev-parse`, `git merge-base` and `git cat-file` alone; nothing here fetches there or asks its status. Every `rm`
# names its target through `${VAR:?}`. Nothing prints a path above the repository, so no output carries a home
# directory into a record. TMPDIR is the repository's own scratch, `$A/tmp` (RX-195 made one inside the repository
# safe for B-4's `repro`). THE RUN IS DATED ONCE: `apply.py` writes the first step's day to `$A/date`, and every
# `@@DATE025A@@` of every step becomes that day.
: "${REPO:?set REPO to the REPO line of the dispatch, first}"
REPO=$(realpath "$REPO")
WB=$(realpath "$REPO/..")
NPK_TREE=$(realpath "$WB/../nitpick")
PIN=c9baa9e                                   # the pin this subcycle adopts
PIN_FULL=c9baa9e91c553d8db2a2a62f09c36b30a984b07f
OLD=7e91730                                   # the pin it leaves, kept for the old pin's runs and the controls
OLD_FULL=7e91730d19cffd35fcff25c36893cfaa2c01509e
T=$REPO/meta/roadmap/0.2/0.2.5a_tools         # these tools
A=$REPO/.internal/w025a                        # gitignored scratch
CHECK=$WB/skills/check/scripts
mkdir -p "$A/tmp"
TMPDIR=$A/tmp
export TMPDIR A T WB PIN OLD

# Inside the CALLER'S subshell: the compiler and the runtime object of <pin>. Prints nothing.
#     ( leg <pin>; ... )
leg() {
  NPKC=$WB/.internal/toolchain/$1/npkc
  NPKRT=$WB/.internal/toolchain/$1/npkrt.o
  export NPKC NPKRT
}

# What `llc`, `opt` and `ld.lld` report under <pin>'s PATH.
#     tools <pin>
tools() {
  ( leg "$1"
    for t in llc opt ld.lld; do
      echo "$1 $t: $("$t" --version | grep -oE '(LLVM version|LLD) [0-9.]+' | head -1)"
    done )
}

# Compile each file as a root from its own directory with <pin>'s compiler, and print `<file> at <pin>:` and each
# diagnostic's code and site -- `L:C` in the file itself, `<name>:L:C` in another -- or `compiles`.
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

# The full harness over a tree -- the checkout by default -- at <pin>, its log kept as `$A/<label>.log`, and its summary
# printed: the exit, the LLVM it held, the target, the self-check's count, the repro step, rx120, the pending units, the
# units and the verdict, every FAIL line, the six suites' sizes and B-2's scan count, the tree checks counted by their
# status and named -- and what the run left in `harness/__pycache__/`, which is removed first (0.2.5's helper).
#     harness <label> <pin> [<tree>]
harness() {
  local tree=${3:-$REPO}
  free -g | awk '/^Mem:/ {print "available GiB:", $7}'
  rm -rf "${tree:?}/harness/__pycache__"
  ( leg "$2"; cd "$tree" && python3 -B harness/run.py ) > "$A/$1.log" 2>&1
  echo "harness exit $?"
  grep -E '^ok    llc |^ok    target|live, [0-9]+ pending|^ok    repro|^ok    rx120|^PEND  tests/|unit\(s\) PENDING and|unit\(s\) passed|^GREEN|^THE SELF-CHECK FAILED|^FAIL  toolchain' "$A/$1.log" | cut -c1-150
  grep -E '^FAIL  [a-z]|^  FAIL  ' "$A/$1.log" | grep -v '^FAIL  toolchain' | cut -c1-150
  echo "suites: $(grep -E '^      [a-z-]+  \([a-z/]+\)  [0-9]+ unit\(s\)$' "$A/$1.log" | awk '{print $1, $3}' \
    | paste -sd, - | sed 's/,/, /g'); B-2's scans on $(grep -oE "B-2's two scans ran on [0-9]+" "$A/$1.log" | grep -oE '[0-9]+$')"
  echo "tree checks: $(grep -oE '^  (ok  |FAIL|note)  check_[a-z_]+' "$A/$1.log" | awk '{print $1}' | sort | uniq -c \
    | awk '{printf "%s %s, ", $1, $2}' | sed 's/, $//') -- $(grep -oE '^  (ok  |FAIL|note)  check_[a-z_]+' "$A/$1.log" \
    | awk '{print $2}' | tr '\n' ' ' | sed 's/ $//')"
  echo "left in harness/__pycache__/: $(ls "$tree/harness/__pycache__" 2>/dev/null | sed -E 's/cpython-[0-9]+/cpython-N/' | tr '\n' ' ' | sed 's/ $//')"
}

# A copy of the working tree AS IT STANDS -- tracked and new files, not the ignored -- at $A/ctl/<name>, for a control
# or a measurement to change one thing in. Prints nothing. A copy is not in the checkout's position: its rx120 step
# finds no `950bb1d` and says SKIPPED, and its `check_refs` finds no `../BOARD.md`.
#     ctl <name>
ctl() {
  local d="$A/ctl/$1"
  rm -rf "${d:?}"; mkdir -p "$d"
  ( cd "$REPO" && git ls-files -co --exclude-standard -z | xargs -0 tar -cf - ) | tar -xf - -C "$d"
}

# Every tracked `.npk` of <tree> compiled as a root at <pin> -- `census.py` -- into $A/<out>.tsv, and its summary.
#     census <pin> <tree> <out>
census() {
  python3 -B "$T/census.py" run "$1" "$2" "$A/$3.tsv"
}

# The compiler's two normalisers, from `c9baa9e` by `git show`, into $A/norm/. Prints each one's digest.
#     normtools
normtools() {
  local f
  mkdir -p "$A/norm"
  for f in attrnorm.py dropnorm.py; do
    git -C "$NPK_TREE" show "$PIN:meta/roadmap/1.6/tools/$f" > "$A/norm/$f"
    echo "$f from $PIN: $(sha256sum "$A/norm/$f" | cut -c1-16)"
  done
}

# Every program of <tree> -- each tracked `.npk` the census compiled whose IR defines `@main` -- emitted at <pin> into
# $A/emit/<label>/, one `.ll` per program named by its path with `/` as `%`: `emit.py`.
#     emits <pin> <tree> <label>
emits() {
  python3 -B "$T/emit.py" run "$1" "$2" "$A/emit/$3"
}

# The steps' patches applied in order to a throwaway clone of HEAD -- the check that the tree is the one they were cut
# from, before any is applied here. `--shared`, so it costs no object copy.
#     dryrun <step>...
dryrun() {
  local d="$A/dry" n
  rm -rf "${d:?}"; git clone -q --shared "$REPO" "$d"
  for n in "$@"; do python3 -B "$T/apply.py" "$n" "$d" | sed 's/^/dry run: /'; done
  rm -rf "${d:?}"
}

# The rename's mutants of `$T/mutants.tsv` whose step is <step>: `mutants.py`, each compiled at both pins in a copy.
#     mutants <step>
mutants() {
  python3 -B "$T/mutants.py" "$REPO" "$1"
}

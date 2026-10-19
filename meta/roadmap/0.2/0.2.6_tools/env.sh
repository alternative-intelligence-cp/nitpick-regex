# 0.2.6_tools/env.sh -- sourced at the top of EVERY command block of `0.2.6.md`, because a Bash call keeps no
# variables and no functions from the call before it. Set REPO first, to the dispatch's REPO line:
#
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/0.2/0.2.6_tools/env.sh"        # blocks 0a ... 5
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/done/0.2/0.2.6_tools/env.sh"   # every block after the move
#
# `T` IS THIS FILE'S OWN DIRECTORY, so the tools are found before step 5 moves them to `done/0.2/` and after (time's
# 0.3.4 `env.sh`, the shape). ONE PIN: `c9baa9e`, landing 118, the pin since cycle 0.2.5a (RX-245), under the machine's
# LLVM 20.1.8 (the compiler's D-349). `leg` sets the compiler and the runtime object and nothing else; `llc`, `opt` and
# `ld.lld` are found on PATH as the shell has it, and `tools` prints what each reports.
#
# The paths are the CHECKOUT's: `WB` is the directory above it, `NPK_TREE` the compiler beside that, and `CHECK` the
# workbench's own `skills/check/scripts` -- so a block run in a relocated copy finds another workbench or none, and
# `check_refs` there finds no `../BOARD.md`: run the blocks in the checkout the dispatch names (the plan's §0).
# `$NPK_TREE` is read with `git show` and `git rev-parse` alone; nothing here fetches there or asks its status. Every
# `rm` names its target through `${VAR:?}`. Nothing prints a path above the repository, so no output carries a home
# directory into a record. TMPDIR is the repository's own scratch, `$A/tmp` (RX-195 made one inside the repository
# safe for B-4's `repro`). THE RUN IS DATED ONCE: `apply.py` writes the first step's day to `$A/date`, and every
# `@@DATE026@@` of every patch becomes that day.
: "${REPO:?set REPO to the REPO line of the dispatch, first}"
REPO=$(realpath "$REPO")
WB=$(realpath "$REPO/..")
NPK_TREE=$(realpath "$WB/../nitpick")
PIN=c9baa9e
PIN_FULL=c9baa9e91c553d8db2a2a62f09c36b30a984b07f
T=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
A=$REPO/.internal/w026                         # gitignored scratch
CHECK=$WB/skills/check/scripts
mkdir -p "$A/tmp"
TMPDIR=$A/tmp
export TMPDIR A T WB PIN REPO

# Inside the CALLER'S subshell: the pin's compiler and runtime object. Prints nothing.
leg() {
  NPKC=$WB/.internal/toolchain/$PIN/npkc
  NPKRT=$WB/.internal/toolchain/$PIN/npkrt.o
  export NPKC NPKRT
}

# What `llc`, `opt` and `ld.lld` report on PATH.
tools() {
  local t
  for t in llc opt ld.lld; do
    echo "$t: $("$t" --version | grep -oE '(LLVM version|LLD) [0-9.]+' | head -1)"
  done
}

# The full harness over a tree -- the checkout by default -- at the pin, its log kept as `$A/<label>.log`, and its
# summary printed: the exit, the LLVM it held, the target, the self-check's count, the repro step, rx120, the pending
# units, the units and the verdict, every FAIL line, the six suites' sizes and B-2's scan count, the tree checks counted
# by their status and named -- and what the run left in `harness/__pycache__/`, which is removed first (0.2.5a's helper).
#     harness <label> [<tree>]
harness() {
  local tree=${2:-$REPO}
  free -g | awk '/^Mem:/ {print "available GiB:", $7}'
  rm -rf "${tree:?}/harness/__pycache__"
  ( leg; cd "$tree" && python3 -B harness/run.py ) > "$A/$1.log" 2>&1
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

# Every tree check of <tree>, by that tree's own `treecheck.py`, with its verdict and what it examined, and every
# failure's first 150 characters -- seconds, where the harness takes minutes, and no substitute for one: a step's
# commit stands on CI's full run of its push and on the gating run (§3), never on this alone.
#     tchecks [<tree>]
tchecks() {
  python3 -B - "${1:-$REPO}" <<'PY'
import os, sys
root = sys.argv[1]
sys.path.insert(0, os.path.join(root, "harness"))
import treecheck
for fn in treecheck.ALL:
    r = fn(root)
    mark = "note" if r.name in treecheck.REPORTING_ONLY else ("ok" if r.ok else "FAIL")
    print("  %s: %s | %s" % (r.name, mark, r.examined))
    for f in r.failures:
        print("      FAIL " + f[:150])
PY
}

# A copy of the working tree AS IT STANDS -- tracked and new files, not the ignored -- at $A/ctl/<name>, for a control
# or a measurement to change one thing in. Prints nothing.
#     ctl <name>
ctl() {
  local d="$A/ctl/$1"
  rm -rf "${d:?}"; mkdir -p "$d"
  ( cd "$REPO" && git ls-files -co --exclude-standard -z | xargs -0 tar -cf - ) | tar -xf - -C "$d"
}

# The close's mechanical steps made in order in a throwaway clone of HEAD -- steps 1 to 4's patches, the move and the
# plain mentions (`archive.py`), steps 6 and 7's patches -- the check that the tree is the one they were cut from,
# before any is applied here. `--shared`, so it costs no object copy. Run before the move only.
#     dryrun
dryrun() {
  local d="$A/dry" n
  rm -rf "${d:?}"; git clone -q --shared "$REPO" "$d"
  for n in 1 2 3 4; do python3 -B "$T/apply.py" "$n" "$d" | sed 's/^/dry run: /'; done
  REPO="$d" python3 -B "$T/archive.py" move | tail -1 | sed 's/^/dry run: /'
  git -C "$d" commit -q -m "dry run: the move" && echo "dry run: committed the move"
  REPO="$d" python3 -B "$T/archive.py" mentions | tail -1 | sed 's/^/dry run: /'
  for n in 6 7; do python3 -B "$T/apply.py" "$n" "$d" | sed 's/^/dry run: /'; done
  rm -rf "${d:?}"
}

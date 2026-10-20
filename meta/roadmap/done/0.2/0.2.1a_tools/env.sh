# meta/roadmap/0.2/0.2.1a_tools/env.sh -- sourced at the top of EVERY command block of `0.2.1a.md`, because a Bash call
# keeps no variables and no functions from the call before it. Set REPO first, to the dispatch's REPO line:
#
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/0.2/0.2.1a_tools/env.sh"
#
# THE LLVM IS CHOSEN BY THE PIN A HELPER RUNS, AND ONLY THERE. Each pin is held to its own exact release (D-204): the
# unchanged tree's manifest says 20.1.2, the release the libraries pinned with `5fbaf4a`, and the adopted tree's says
# 20.1.8, the compiler's since its D-349 and `7e91730`'s -- and `harness/toolchain.py` refuses any other. The machine's
# own `llc`, `opt` and `ld.lld` are 20.1.8 since 2026-10-08, so the NEW pin runs under PATH as the shell has it, and the
# OLD pin under the libraries' private 20.1.2 copy put first on PATH -- inside the helper's own subshell, so no other
# command of a block ever sees it. `tools <pin>` prints what each of the three reports under that pin's PATH; a release
# other than the pin's is a toolchain mismatch, and a stop.
#
# The paths are the CHECKOUT's: `WB` is the directory above it and `NPK_TREE` the compiler beside that, so a block run
# in a relocated copy finds another workbench or none -- run the blocks in the checkout the dispatch names (the plan's
# §0). `$NPK_TREE` is read with `git show` and `git diff` alone. Every `rm` names its target through `${VAR:?}`. Nothing
# prints a path above the repository, so no output carries a home directory into a record. TMPDIR is the repository's
# own scratch, `$A/tmp` (the sandbox refuses a plain `/tmp`; RX-195 made one inside the repository safe for B-4's
# `repro`). THE RUN IS DATED ONCE: `apply.py` writes the first step's day to `$A/date`.
: "${REPO:?set REPO to the REPO line of the dispatch, first}"
REPO=$(realpath "$REPO")
WB=$(realpath "$REPO/..")
NPK_TREE=$(realpath "$WB/../nitpick")
PIN=7e91730                                   # the pin this subcycle adopts
PIN_FULL=7e91730d19cffd35fcff25c36893cfaa2c01509e
OLD=5fbaf4a                                   # the pin it leaves, kept for the old pin's runs and the controls
OLD_FULL=5fbaf4a40a2f6b213754cd71b6c69700f8aa2c87
OLD_LLVM=$WB/.internal/toolchain/llvm-20.1.2/root/usr/lib/llvm-20/bin   # the old pin's LLVM, the private copy
T=$REPO/meta/roadmap/0.2/0.2.1a_tools         # these tools
A=$REPO/.internal/w021a                        # gitignored scratch
CHECK=$HOME/.claude/skills/npk/skills/check/scripts
mkdir -p "$A/tmp"
TMPDIR=$A/tmp
export TMPDIR A T WB PIN OLD

# Inside the CALLER'S subshell: the compiler and the LLVM of <pin>. Prints nothing.
#     ( leg <pin>; ... )
leg() {
  NPKC=$WB/.internal/toolchain/$1/npkc
  NPKRT=$WB/.internal/toolchain/$1/npkrt.o
  case "$1" in "$OLD") PATH=$OLD_LLVM:$PATH ;; esac
  export NPKC NPKRT PATH
}

# What `llc`, `opt` and `ld.lld` report under <pin>'s PATH, and where each was found, relative to the workbench when
# it is the private copy.
#     tools <pin>
tools() {
  ( leg "$1"
    for t in llc opt ld.lld; do
      w=$(command -v "$t"); case "$w" in "$WB"/*) w=${w#"$WB"/} ;; *) w="the machine's" ;; esac
      echo "$1 $t: $w -- $("$t" --version | grep -oE '(LLVM version|LLD) [0-9.]+' | head -1)"
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
# printed: the exit, the LLVM it held, the target, the self-check's count, the repro step, the pending units, the units
# and the verdict, every FAIL line, the six suites' sizes and B-2's scan count, and every tree check by name.
#     harness <label> <pin> [<tree>]
harness() {
  free -g | awk '/^Mem:/ {print "available GiB:", $7}'
  ( leg "$2"; cd "${3:-$REPO}" && python3 -B harness/run.py ) > "$A/$1.log" 2>&1
  echo "harness exit $?"
  grep -E '^ok    llc |^ok    target|live, [0-9]+ pending|^ok    repro|^ok    rx120|^      SKIPPED|^PEND  tests/|unit\(s\) PENDING and|unit\(s\) passed|^GREEN|^THE SELF-CHECK FAILED|^FAIL  toolchain' "$A/$1.log" | cut -c1-150
  grep -E '^FAIL  [a-z]' "$A/$1.log" | grep -v '^FAIL  toolchain' | cut -c1-150
  echo "suites: $(grep -E '^      [a-z-]+  \([a-z/]+\)  [0-9]+ unit\(s\)$' "$A/$1.log" | awk '{print $1, $3}' \
    | paste -sd, - | sed 's/,/, /g'); B-2's scans on $(grep -oE "B-2's two scans ran on [0-9]+" "$A/$1.log" | grep -oE '[0-9]+$')"
  echo "tree checks: $(grep -oE '^  (ok  |FAIL|note)  check_[a-z_]+' "$A/$1.log" | awk '{print $2}' | tr '\n' ' ')"
}

# A copy of the working tree AS IT STANDS -- tracked and new files, not the ignored -- at $A/ctl/<name>, for a control
# or a measurement to change one thing in. Prints nothing. A copy is not in the checkout's position: its rx120 step
# finds no `950bb1d` and says SKIPPED, and every other step is the checkout's.
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

# The steps' patches applied in order to a throwaway clone of HEAD -- the check that the tree is the one they were cut
# from, before any is applied here. `--shared`, so it costs no object copy.
#     dryrun <step>...
dryrun() {
  local d="$A/dry" n
  rm -rf "${d:?}"; git clone -q --shared "$REPO" "$d"
  for n in "$@"; do python3 -B "$T/apply.py" "$n" "$d" | sed 's/^/dry run: /'; done
  rm -rf "${d:?}"
}

# The view mutants of `$T/vmutants.tsv` whose step is <step>: `vmut.py`, each compiled at both pins in a copy.
#     vmut <step>
vmut() {
  python3 -B "$T/vmut.py" "$REPO" "$1"
}

# Every live self-check case run against <tree>'s own harness at <pin>: how many are red as required, and the distinct
# first line each NOT-red case's inner run failed with.
#     cases <pin> <tree>
cases() {
  ( leg "$1"; cd "$2" && python3 -B - <<'PY'
import collections, sys
sys.path.insert(0, "harness")
import selfcheck
red, why = 0, collections.Counter()
for c in selfcheck.CASES:
    if c.pending is not None:
        continue
    o = selfcheck._run_case(c, False)
    if o.ok:
        red += 1
        continue
    first = [l for l in o.detail.split("\n") if "FAIL  " in l]
    why[(first[0].split("FAIL  ", 1)[1][:96] if first else o.detail.split("\n")[0][:96])] += 1
print("live cases red as required: %d of %d" % (red, red + sum(why.values())))
for w, n in why.most_common():
    print("  %d NOT red, the inner run's first FAIL: %s" % (n, w))
PY
  )
}

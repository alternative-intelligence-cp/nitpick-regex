# meta/roadmap/0.1/0.1.6_tools/env.sh -- sourced at the top of EVERY command block of `0.1.6.md`; after step 1 both
# live at `meta/roadmap/done/0.1/`. Set REPO first, to the dispatch's REPO line:
#
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/0.1/0.1.6_tools/env.sh"          (block 0a, block 1)
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/done/0.1/0.1.6_tools/env.sh"     (every block after)
#
# `T` is this file's own directory, so it is found before the archive and after it. 0.1.6b's `codes`, `harness`,
# `tcheck` and `scase`, and a `dryrun` that makes the close in a throwaway clone: the move, the mentions and step 2's
# patch. The paths are the CHECKOUT's: `WB` is the directory above it. `$NPK_TREE` is read with `git` read commands
# only; every `rm` names its target through `${VAR:?}`; nothing prints a path above the repository. TMPDIR is the
# repository's own scratch, `$A/tmp` (RX-195). The run is dated once, by `apply.py`, in `$A/date`.
: "${REPO:?set REPO to the REPO line of the dispatch, first}"
REPO=$(realpath "$REPO")
WB=$(realpath "$REPO/..")
NPK_TREE=$(realpath "$WB/../nitpick")
PIN=5fbaf4a
PIN_FULL=5fbaf4a40a2f6b213754cd71b6c69700f8aa2c87
NPKC=$WB/.internal/toolchain/$PIN/npkc
NPKRT=$WB/.internal/toolchain/$PIN/npkrt.o
T=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)    # these tools, wherever the archive put them
A=$REPO/.internal/n16                         # gitignored scratch
CHECK=$HOME/.claude/skills/npk/skills/check/scripts
mkdir -p "$A/tmp"
TMPDIR=$A/tmp
export NPKC NPKRT TMPDIR

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

harness() {
  free -g | awk '/^Mem:/ {print "available GiB:", $7}'
  ( cd "$REPO" && python3 -B harness/run.py ) > "$A/$1.log" 2>&1
  echo "harness exit $?"
  grep -E '^ok    target|live, [0-9]+ pending|^ok    repro|unit\(s\) passed|^GREEN|^THE SELF-CHECK FAILED' "$A/$1.log" | cut -c1-150
  grep -E '^FAIL  [a-z]' "$A/$1.log" | cut -c1-150
  echo "tree checks: $(grep -oE '^  (ok  |FAIL|note)  check_[a-z_]+' "$A/$1.log" | awk '{print $2}' | tr '\n' ' ')"
}

tcheck() {
  python3 -B - "${3:-$REPO}" "$1" "${2:-$REPO}" <<'PY'
import os, sys
sys.path.insert(0, os.path.join(sys.argv[1], "harness"))
import treecheck
r = getattr(treecheck, sys.argv[2])(sys.argv[3])
print("%s: %s | %s" % (r.name, "ok" if r.ok else "FAIL", r.examined))
for f in r.failures:
    print("  " + f.splitlines()[0][:150])
for n in r.notes:
    print("  note: " + n[:150])
PY
}

# The close made in a throwaway clone of HEAD -- the move, the plain mentions, and step 2's patch -- the check that
# the tree is the one they were cut from, before any is made here. The clone's `check_refs` cannot resolve
# `CLAUDE.md`'s two links to the workbench from where the clone stands, so it is not asked there.
dryrun() {
  local d="$A/dry"
  rm -rf "${d:?}"; git clone -q --shared "$REPO" "$d"
  REPO="$d" python3 -B "$T/archive.py" move | tail -1 | sed 's/^/dry run: /'
  REPO="$d" python3 -B "$T/archive.py" mentions | tail -1 | sed 's/^/dry run: /'
  git -C "$d" add -A
  python3 -B "$T/apply.py" 2 "$d" | sed 's/^/dry run: /'
  rm -rf "${d:?}"
}

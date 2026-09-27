# meta/roadmap/0.1/0.1.0b_tools/env.sh -- sourced at the top of EVERY command block of
# `0.1.0b.md`, because a Bash call keeps no variables and no functions from the call
# before it. Set REPO first, to the dispatch's REPO line:
#
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/0.1/0.1.0b_tools/env.sh"
#
# `$NPK_TREE` is read with `git` read commands only -- never written, built or
# fetched in. Every `rm` names its target through `${VAR:?}`. Nothing prints a path
# above the repository, so no output carries a home directory into a record.
: "${REPO:?set REPO to the REPO line of the dispatch, first}"
REPO=$(realpath "$REPO")
WB=$(realpath "$REPO/..")
NPK_TREE=$(realpath "$WB/../nitpick")
PIN=5fbaf4a                                   # the pin this subcycle adopts
PIN_FULL=5fbaf4a40a2f6b213754cd71b6c69700f8aa2c87
OLD=c970483                                   # the pin it leaves, kept for controls
NPKC=$WB/.internal/toolchain/$PIN/npkc
NPKRT=$WB/.internal/toolchain/$PIN/npkrt.o
T=$REPO/meta/roadmap/0.1/0.1.0b_tools         # these tools
A=$REPO/.internal/b10                          # gitignored scratch
export NPKC NPKRT                              # the harness reads them from the ENVIRONMENT
mkdir -p "$A"

# Compile each file as a root with a kept pin's compiler, from its own directory, and
# print `<file> at <pin>: CODE L:C ...` per diagnostic (errors only), or `compiles`.
#     codes <pin> <file>...     (a relative file is the repository's)
codes() {
  local pin=$1; shift
  local cc=$WB/.internal/toolchain/$pin/npkc f src out
  for f in "$@"; do
    src=$f; [ "${f#/}" = "$f" ] && src="$REPO/$f"
    out=$(cd "$(dirname "$src")" && "$cc" "$(basename "$src")" -o /dev/null 2>&1)
    if [ -z "$out" ]; then echo "$(basename "$src") at $pin compiles"; continue; fi
    echo "$(basename "$src") at $pin: $(echo "$out" | grep -oE '^NITPICK-[A-Z]+-[0-9]+ [^ ]+:[0-9]+:[0-9]+' \
      | sed -E 's|^(NITPICK-[A-Z]+-[0-9]+) [^ ]*:([0-9]+):([0-9]+)$|\1 \2:\3|' | tr '\n' ' ' | sed 's/ $//')"
  done
}

# The full harness at the pin, its log kept, its summary lines printed.
#     harness <label>
harness() {
  free -g | awk '/^Mem:/ {print "available GiB:", $7}'
  ( cd "$REPO" && python3 -B harness/run.py ) > "$A/$1.log" 2>&1
  echo "harness exit $?"
  grep -E 'unit\(s\) passed|^FAIL  [a-z]|^GREEN|RUNNER WAS SHOWN|^ok    target' "$A/$1.log" | cut -c1-150
}

# A copy of the working tree AS IT STANDS -- tracked and new files, not the ignored --
# at $A/ctl/<name>, for a control to change one thing in. Prints nothing.
#     ctl <name>
ctl() {
  local d="$A/ctl/$1"
  rm -rf "${d:?}"; mkdir -p "$d"
  ( cd "$REPO" && git ls-files -co --exclude-standard -z | xargs -0 tar -cf - ) | tar -xf - -C "$d"
}

# Cycle 0.1.0's block-3b programs, into a control copy: the pattern's owner written
# while a cursor holds its view, and a cursor over a LOCAL's view, returned.
#     cursor_programs <control-dir>
cursor_programs() {
  sed -n '/^func:failsafe/,$p' "$REPO/tests/unit/pattern_error_unit.npk" > "$A/fs11.txt"
  { printf '%s\n' 'mod:zz_owner_written;' 'use "../../src/syntax/syntax.npk".*;' \
      'func:main = int32(cstring[]:_~argv) {' \
      '    string:s = string_concat("abbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "c");' \
      '    Cursor:c = raw cursor_init(string_bytes(s));' \
      '    s = string_concat("xyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy", "z");' \
      '    int32:b = raw cursor_bump(@c);' '    exit b;' '};'
    cat "$A/fs11.txt"; } > "$1/tests/unit/zz_owner_written.npk"
  { printf '%s\n' 'mod:zz_local_returned;' 'use "../../src/syntax/syntax.npk".*;' \
      'func:make = Cursor() never fails {' '    string:s = string_concat("ab", "c");' \
      '    pass raw cursor_init(string_bytes(s));' '};' \
      'func:main = int32(cstring[]:_~argv) {' '    Cursor:c = raw make();' \
      '    int32:b = raw cursor_bump(@c);' '    exit b;' '};'
    cat "$A/fs11.txt"; } > "$1/tests/unit/zz_local_returned.npk"
}

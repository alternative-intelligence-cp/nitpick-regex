# meta/roadmap/0.1/0.1.1_tools/env.sh -- sourced at the top of EVERY command block of
# `0.1.1.md`, because a Bash call keeps no variables and no functions from the call
# before it. Set REPO first, to the dispatch's REPO line:
#
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/0.1/0.1.1_tools/env.sh"
#
# `$NPK_TREE` is read with `git` read commands only -- never written, built or
# fetched in. Every `rm` names its target through `${VAR:?}`. Nothing prints a path
# above the repository, so no output carries a home directory into a record.
: "${REPO:?set REPO to the REPO line of the dispatch, first}"
REPO=$(realpath "$REPO")
WB=$(realpath "$REPO/..")
NPK_TREE=$(realpath "$WB/../nitpick")
PIN=5fbaf4a                                   # the pin this subcycle is planned and rehearsed at
PIN_FULL=5fbaf4a40a2f6b213754cd71b6c69700f8aa2c87
OLD=c970483                                   # the pin it leaves, kept for controls
NPKC=$WB/.internal/toolchain/$PIN/npkc
NPKRT=$WB/.internal/toolchain/$PIN/npkrt.o
T=$REPO/meta/roadmap/0.1/0.1.1_tools         # these tools
A=$REPO/.internal/f11                          # gitignored scratch
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

# O-B3's instrument: `NITPICK-REACH-003` on a program that imports one module and has
# no `failsafe` lists every identity a consumer of that module owes.
#     bills <module>...     (relative to the repository)
bills() {
  local d="$A/bills/x" m n ids
  mkdir -p "$d"
  for m in "$@"; do
    n=$(echo "$m" | tr '/.' '__')
    printf 'mod:b_%s;\nuse "../../../../%s".*;\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n' "$n" "$m" > "$d/b_$n.npk"
    ids=$(cd "$d" && "$NPKC" "b_$n.npk" -o /dev/null 2>&1 | grep -o 'NITPICK-REACH-003.*' | head -1 \
          | sed -n 's/.* identities: \(.*\) -- with.*/\1/p' | tr -d ',' | tr ' ' '\n' | grep -v '^$' | sort | tr '\n' ' ')
    printf '%-26s %2d  %s\n' "$m" "$(echo $ids | wc -w)" "$ids" | sed 's/ *$//'
  done
}

# The undefined symbols of a program's object: what B-2's scan compares with the floor
# and the reviewed residue list.
#     undefs <file>     (at $PIN)
undefs() {
  local src=$1 b; [ "${1#/}" = "$1" ] && src="$REPO/$1"
  b=$(basename "$src" .npk)
  ( cd "$(dirname "$src")" && "$NPKC" "$(basename "$src")" -o "$A/$b.u.ll" ) > /dev/null 2>&1 \
    && llc -O0 -filetype=obj -relocation-model=static "$A/$b.u.ll" -o "$A/$b.u.o" \
    && echo "$b: $(llvm-nm --undefined-only "$A/$b.u.o" | awk '{print $NF}' | sort | tr '\n' ' ')"
}

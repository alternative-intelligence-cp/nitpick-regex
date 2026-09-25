# meta/roadmap/0.0/0.0.4d_tools/env.sh -- sourced at the top of EVERY command block
# of `0.0.4d.md`, because a Bash call keeps no variables and no functions from the
# call before it. Set REPO first, to the dispatch's REPO line:
#
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/0.0/0.0.4d_tools/env.sh"
#
# `$NPK_TREE` is read with `git show` only -- never written, built or fetched in.
: "${REPO:?set REPO to the REPO line of the dispatch, first}"
REPO=$(realpath "$REPO")
WB=$(realpath "$REPO/..")
NPK_TREE=$(realpath "$WB/../nitpick")
NPKC=$WB/.internal/toolchain/c3bdae2/npkc
NPKRT=$WB/.internal/toolchain/c3bdae2/npkrt.o
T=$REPO/meta/roadmap/0.0/0.0.4d_tools          # these tools
A=$REPO/.internal/d4d                          # gitignored scratch
export NPKC NPKRT                              # the harness reads them from the ENVIRONMENT
mkdir -p "$A"

# Every tracked and untracked-but-not-ignored `.npk`, each compiled as a root by
# `npkc` alone (0.0.4b step 0's instrument). Writes $A/<label>.log, prints the tally.
sweep() {
  local log="$A/$1.log"; : > "$log"
  local f out st
  for f in $( { git -C "$REPO" ls-files '*.npk'; git -C "$REPO" ls-files --others --exclude-standard '*.npk'; } | sort -u ); do
    out=$(cd "$REPO/$(dirname "$f")" && "$NPKC" "$(basename "$f")" -o /dev/null 2>&1); st=$?
    printf '=== %s (exit %s)\n%s\n' "$f" "$st" "$out" >> "$log"
  done
  echo "files $(grep -c '^=== ' "$log")  exit-0 $(grep -c '^=== .*(exit 0)' "$log")"
  grep -oE '^NITPICK-[A-Z]+-[0-9]+' "$log" | sort | uniq -c
}

# O-B3's instrument: NITPICK-REACH-003 on a program that imports one module and has
# no failsafe lists every identity a consumer of that module owes (0.0.4b step 11).
bills() {
  local d="$A/bills"; rm -rf "$d"; mkdir -p "$d"
  local m n ids
  for m in src/core/vec.npk src/core/bytes.npk src/core/byteset.npk src/core/sparseset.npk \
           src/core/limits.npk src/core/core.npk src/lib.npk src/api/api.npk src/syntax/syntax.npk; do
    n=$(echo "$m" | tr '/.' '__')
    # the probe program sits two levels below the repository, like tests/unit/
    mkdir -p "$d/x"
    printf 'mod:b_%s;\nuse "../../../../%s".*;\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n' "$n" "$m" > "$d/x/b_$n.npk"
    ids=$(cd "$d/x" && "$NPKC" "b_$n.npk" -o /dev/null 2>&1 | grep -o 'NITPICK-REACH-003.*' | head -1 \
          | sed -n 's/.* identities: \(.*\) -- with.*/\1/p' | tr -d ',' | tr ' ' '\n' | grep -v '^$' | sort | tr '\n' ' ')
    printf '%-24s %2d  %s\n' "$m" "$(echo $ids | wc -w)" "$ids"
  done
}

# Pin every `// expect-error-at: 0:0` under tests/ by MEASUREMENT (0.0.4c step 3):
# compile the file, read its one diagnostic's L:C, write it in. A file giving other
# than exactly one diagnostic is printed and LEFT at 0:0, which the harness reddens.
pin() {
  ( cd "$REPO" && { git grep -l '^// expect-error-at: 0:0$' -- tests; \
      git ls-files --others --exclude-standard tests | xargs -r grep -l '^// expect-error-at: 0:0$'; } | sort -u ) > "$A/pin_list.txt"
  local f out pos n
  while read -r f; do
    out=$(cd "$REPO/$(dirname "$f")" && "$NPKC" "$(basename "$f")" -o /dev/null 2>&1)
    pos=$(echo "$out" | grep -oE '^NITPICK-[A-Z]+-[0-9]+ [^ ]+:[0-9]+:[0-9]+' | sed -E 's/.*:([0-9]+):([0-9]+)$/\1:\2/')
    n=$(echo "$pos" | grep -c .)
    echo "$f -> $pos ($n diagnostic(s))"
    if [ "$n" = 1 ]; then sed -i "s/^\/\/ expect-error-at: 0:0$/\/\/ expect-error-at: $pos/" "$REPO/$f"; fi
  done < "$A/pin_list.txt"
}

# The seven prose searches of step 7, over tracked AND untracked-not-ignored files,
# THIS PLAN AND ITS TOOLS EXCLUDED (they quote every pattern). Writes $A/sweeps_<label>/.
sweeps() {
  local d="$A/sweeps_$1"; rm -rf "$d"; mkdir -p "$d"
  _s() { git -C "$REPO" grep --untracked -n -i -E "$2" -- . ':!meta/roadmap/0.0/0.0.4d.md' ':!meta/roadmap/0.0/0.0.4d_tools' > "$d/$1.txt"
         printf '%-3s %4d lines %3d files   %s\n' "$1" "$(wc -l < "$d/$1.txt")" "$(cut -d: -f1 "$d/$1.txt" | sort -u | wc -l)" "$2"; }
  _s S1 'whole-.Vec. copy|header copy|second handle|copies it silently|copyable'
  _s S2 '0\.0\.4d'
  _s S3 'vec_get.{0,40}signature|signature.{0,60}vec_get|by-value read'
  _s S4 'Q-6|until it is answered|is unanswered'
  _s S5 'b\.buf|buf\.ptr|buf\.len|sealed .?buf|hidden .?buf'
  _s S6 '\*\*194|194 units|\b52 unit|\*\*28\*\* language|22 / 6|eight consumer|all seven import'
  _s S7 'seven (units|alias)|seven pinning'
}

# `#size_of<Vec<int64>>()` and `#size_of<SparseSet>()` in one exit code, a*4+b:
# 152 is 24*4 + 56, the sizes before AND after the marker.
sizes() {
  mkdir -p "$A/sz/x"
  cat > "$A/sz/x/sz.npk" <<'NPK'
mod:sz;
use "../../../../src/core/vec.npk".*;
use "../../../../src/core/sparseset.npk".*;
func:main = int32(cstring[]:_~argv) {
    int64:a = #size_of<Vec<int64>>();
    int64:b = #size_of<SparseSet>();
    exit ((a * 4i64 + b) =>! int32);
};
func:failsafe = int32(Error:e) {
    pick (e) {
        (HeapBadRequest)    { exit 91i32; },
        (HeapOom)           { exit 92i32; },
        (IntOverflow)       { exit 93i32; },
        (OutOfBounds)       { exit 94i32; },
        (Unreachable)       { exit 95i32; },
        (WildLeak)          { exit 96i32; },
        (StackExhausted)    { exit 106i32; },
        (MachineFault)      { exit 107i32; },
        (DecreasesViolated) { exit 108i32; },
        (LimitViolated)     { exit 109i32; },
        (*)                 { exit 99i32; }
    }
    exit 9i32;
};
NPK
  ( cd "$A/sz/x" && "$NPKC" sz.npk -o "$A/sz/sz.ll" ) && llc -O0 -filetype=obj -relocation-model=static "$A/sz/sz.ll" -o "$A/sz/sz.o" \
    && ld.lld -static "$A/sz/sz.o" "$NPKRT" -o "$A/sz/sz" && "$A/sz/sz"; echo "sizes: exit $?"
}

# Does a program's failsafe name EXACTLY what REACH asks -- no arm missing, none
# extra? Derived independently of the file: the same program with its failsafe cut
# off, compiled four levels deep under $A so its `../../src/` imports still resolve,
# makes NITPICK-REACH-003 list the identities it owes; the file's own arms are read
# off its text. Prints one line per file: EQUAL, or both lists.
arms_check() {
  local f src b ids arms
  mkdir -p "$A/arms/x"
  for f in "$@"; do
    src=$f; [ "${f#/}" = "$f" ] && src="$REPO/$f"      # a relative path is the repository's
    b=$(basename "$f" .npk)
    python3 - "$src" "$A/arms/x/zz_$b.npk" "zz_$b" <<'PY'
import re, sys
s = open(sys.argv[1], encoding="utf-8").read()
s = s[:s.index("func:failsafe")]
s = re.sub(r"^mod:[A-Za-z0-9_]+;", "mod:" + sys.argv[3] + ";", s, count=1, flags=re.M)
s = s.replace('"../../src/', '"../../../../src/')
open(sys.argv[2], "w", encoding="utf-8").write(s)
PY
    ids=$(cd "$A/arms/x" && "$NPKC" "zz_$b.npk" -o /dev/null 2>&1 | grep -o 'NITPICK-REACH-003.*' | head -1 \
          | sed -n 's/.* identities: \(.*\) -- with.*/\1/p' | tr -d ',' | tr ' ' '\n' | grep -v '^$' | sort | tr '\n' ' ')
    arms=$(sed -n '/^func:failsafe/,$p' "$src" | grep -oE '^\s+\(([A-Za-z]+)\)' | tr -d ' ()' | sort | tr '\n' ' ')
    if [ "$ids" = "$arms" ]; then echo "EQUAL  $f  ($(echo $ids | wc -w))"; else echo "DIFF   $f  bill: $ids | arms: $arms"; fi
  done
}

# meta/roadmap/0.0/0.0.4e_tools/env.sh -- sourced at the top of EVERY command block
# of `0.0.4e.md`, because a Bash call keeps no variables and no functions from the
# call before it. Set REPO first, to the dispatch's REPO line:
#
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/0.0/0.0.4e_tools/env.sh"
#
# `$NPK_TREE` is read with `git show` only -- never written, built or fetched in.
# Every `rm` below names its target through `${VAR:?}`, so an unset variable stops
# the shell instead of widening the removal.
: "${REPO:?set REPO to the REPO line of the dispatch, first}"
REPO=$(realpath "$REPO")
WB=$(realpath "$REPO/..")
NPK_TREE=$(realpath "$WB/../nitpick")
PIN=c970483                                    # the pin this subcycle adopts
PIN_FULL=c9704830ea9c738f523bf6646a355f52679b3aee
OLD=c3bdae2                                    # the pin it leaves, kept for controls
NPKC=$WB/.internal/toolchain/$PIN/npkc
NPKRT=$WB/.internal/toolchain/$PIN/npkrt.o
OLD_NPKC=$WB/.internal/toolchain/$OLD/npkc
OLD_NPKRT=$WB/.internal/toolchain/$OLD/npkrt.o
T=$REPO/meta/roadmap/0.0/0.0.4e_tools          # these tools
A=$REPO/.internal/d4e                          # gitignored scratch
export NPKC NPKRT                              # the harness reads them from the ENVIRONMENT
mkdir -p "$A"

# The registry number of the defect `0.0.4e.md` §6.1 raises, if the dispatch names
# one. Written ONCE, in step 0, as `echo O-N<n> > "$A/defect_id"`; every script
# then writes "the workbench registry's O-N<n>" where it would write "raised by
# path". Absent, the texts cite the plan's §6.1. The scripts read this file too.
E4E_DEFECT_ID=$(cat "$A/defect_id" 2>/dev/null || true)
export E4E_DEFECT_ID

# Compile one file as a root with the compiler of a pin, from its own directory, and
# print `<root>: <file> CODE L:C` per diagnostic -- never a path, so nothing printed here
# carries a home directory into a record (`PLAYBOOK.md` §6).
#     codes <c970483|c3bdae2> <file>...     (a relative file is the repository's)
codes() {
  local pin=$1; shift
  local cc=$WB/.internal/toolchain/$pin/npkc f src out
  for f in "$@"; do
    src=$f; [ "${f#/}" = "$f" ] && src="$REPO/$f"
    out=$(cd "$(dirname "$src")" && "$cc" "$(basename "$src")" -o /dev/null 2>&1)
    if [ -z "$out" ]; then echo "$(basename "$src") compiles"; continue; fi
    echo "$out" | grep -oE '^NITPICK-[A-Z]+-[0-9]+ [^ ]+:[0-9]+:[0-9]+' \
      | sed -E "s|^(NITPICK-[A-Z]+-[0-9]+) ([^ ]*/)?([^ /]+):([0-9]+):([0-9]+)$|$(basename "$src"): \3 \1 \4:\5|"
  done
}

# Build one program with the compiler of a pin and run it at -O0 and through
# `opt -O2`: `npkc`, `llc`, `ld.lld`, the binary -- all four, because `npkc` exit 0
# is not well-formedness (O-N11). Prints `<basename> at <pin>: npkc N, llc N, -O0 X,
# -O2 Y`; `llc`'s refusal is named by its kind, never by a path.
#     run4 <c970483|c3bdae2> <file>...
run4() {
  local pin=$1; shift
  local cc=$WB/.internal/toolchain/$pin/npkc rt=$WB/.internal/toolchain/$pin/npkrt.o
  local f src b o nc lc r0 r2 why
  mkdir -p "$A/run4"
  for f in "$@"; do
    src=$f; [ "${f#/}" = "$f" ] && src="$REPO/$f"
    b=$(basename "$src" .npk); o="$A/run4/${b}_$pin"
    ( cd "$(dirname "$src")" && "$cc" "$(basename "$src")" -o "$o.ll" ) > "$o.npkc" 2>&1
    nc=$?
    if [ "$nc" -ne 0 ]; then
      echo "$b at $pin: npkc $nc -- $(grep -oE '^NITPICK-[A-Z]+-[0-9]+' "$o.npkc" | sort -u | tr '\n' ' ')"
      continue
    fi
    llc -O0 -filetype=obj -relocation-model=static "$o.ll" -o "$o.o" 2> "$o.llc"
    lc=$?
    if [ "$lc" -ne 0 ]; then
      why=$(grep -oE 'Cannot allocate unsized type' "$o.llc" | head -1)
      [ -n "$why" ] || why=$(grep -oE 'error: [A-Za-z ,]+$' "$o.llc" | head -1)
      echo "$b at $pin: npkc 0, llc $lc -- $why"
      continue
    fi
    ld.lld -static "$o.o" "$rt" -o "$o"
    "$o"
    r0=$?
    opt -O2 -S "$o.ll" -o "$o.opt.ll" && llc -O2 -filetype=obj -relocation-model=static "$o.opt.ll" -o "$o.o2" \
      && ld.lld -static "$o.o2" "$rt" -o "$o.bin2"
    "$o.bin2"
    r2=$?
    echo "$b at $pin: npkc 0, llc 0, -O0 $r0, -O2 $r2"
  done
}

# Every tracked and untracked-but-not-ignored `.npk`, each compiled as a root by
# `npkc` alone (0.0.4b step 0's instrument), at the pin named (default: the new one).
# Writes $A/<label>.log, prints the tally.
#     sweep <label> [pin]
sweep() {
  local log="$A/$1.log" pin=${2:-$PIN}; : > "$log"
  local cc=$WB/.internal/toolchain/$pin/npkc f out st
  for f in $( { git -C "$REPO" ls-files '*.npk'; git -C "$REPO" ls-files --others --exclude-standard '*.npk'; } | sort -u ); do
    [ -f "$REPO/$f" ] || continue
    out=$(cd "$REPO/$(dirname "$f")" && "$cc" "$(basename "$f")" -o /dev/null 2>&1); st=$?
    printf '=== %s (exit %s)\n%s\n' "$f" "$st" "$out" >> "$log"
  done
  echo "files $(grep -c '^=== ' "$log")  exit-0 $(grep -c '^=== .*(exit 0)' "$log")"
  grep -oE '^NITPICK-[A-Z]+-[0-9]+' "$log" | sort | uniq -c
}

# The refused files of a sweep, with the codes each gave, one line per file.
#     refused <label>
refused() {
  python3 - "$A/$1.log" <<'PY2'
import re, sys
cur, st, codes, out = None, "0", [], []
def flush():
    if cur is not None and st != "0":
        out.append(f"{cur}: exit {st}: {' '.join(sorted(set(codes)))}")
for line in open(sys.argv[1], encoding="utf-8", errors="replace").read().split("\n"):
    m = re.match(r"^=== (\S+) \(exit (\d+)\)$", line)
    if m:
        flush()
        cur, st, codes = m.group(1), m.group(2), []
        continue
    m = re.match(r"^(NITPICK-[A-Z]+-\d+) ", line)
    if m:
        codes.append(m.group(1))
flush()
print("\n".join(sorted(out)))
PY2
}

# O-B3's instrument: NITPICK-REACH-003 on a program that imports one module and has
# no failsafe lists every identity a consumer of that module owes (0.0.4b step 11).
bills() {
  local d="$A/bills"; rm -rf "${d:?}"; mkdir -p "$d/x"
  local m n ids
  for m in src/core/vec.npk src/core/bytes.npk src/core/byteset.npk src/core/sparseset.npk \
           src/core/limits.npk src/core/core.npk src/lib.npk src/api/api.npk src/syntax/syntax.npk; do
    n=$(echo "$m" | tr '/.' '__')
    # the probe program sits four levels below the repository's scratch, like tests/unit/ below it
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

# `#size_of<Vec<int64>>()` and `#size_of<SparseSet>()` in one exit code, a*4+b (152 is
# 24*4 + 56), and `#size_of<Bytes>()` in a second program's (32).
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
  sed -e 's/^mod:sz;$/mod:szb;/' -e 's|^use "../../../../src/core/vec.npk".\*;$|use "../../../../src/core/bytes.npk".*;|' \
      -e '/sparseset.npk/d' -e 's/^    int64:a = #size_of<Vec<int64>>();$/    int64:a = #size_of<Bytes>();/' \
      -e '/^    int64:b = #size_of<SparseSet>();$/d' -e 's/^    exit ((a \* 4i64 + b) =>! int32);$/    exit (a =>! int32);/' \
      "$A/sz/x/sz.npk" > "$A/sz/x/szb.npk"
  local p
  for p in sz szb; do
    ( cd "$A/sz/x" && "$NPKC" "$p.npk" -o "$A/sz/$p.ll" ) && llc -O0 -filetype=obj -relocation-model=static "$A/sz/$p.ll" -o "$A/sz/$p.o" \
      && ld.lld -static "$A/sz/$p.o" "$NPKRT" -o "$A/sz/$p" && "$A/sz/$p"; echo "sizes $p: exit $?"
  done
}

# Does a program's failsafe name EXACTLY what REACH asks -- no arm missing, none
# extra? The same program with its failsafe cut off, compiled four levels deep
# under $A so its `../../src/` imports still resolve, makes NITPICK-REACH-003 list
# the identities it owes; the file's own arms are read off its text.
arms_check() {
  local f src b ids arms
  mkdir -p "$A/arms/x"
  for f in "$@"; do
    src=$f; [ "${f#/}" = "$f" ] && src="$REPO/$f"
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

# The prose searches of steps 0 and 7, over tracked AND untracked-not-ignored
# files, THIS PLAN AND ITS TOOLS EXCLUDED (they quote every pattern). Writes
# $A/sweeps_<label>/<S>.txt and prints one line per search.
sweeps() {
  local d="$A/sweeps_$1"; rm -rf "${d:?}"; mkdir -p "$d"
  _s() { git -C "$REPO" grep --untracked -n -i -E "$2" -- . ':!meta/roadmap/0.0/0.0.4e.md' ':!meta/roadmap/0.0/0.0.4e_tools' > "$d/$1.txt"
         printf '%-3s %4d lines %3d files   %s\n' "$1" "$(wc -l < "$d/$1.txt")" "$(cut -d: -f1 "$d/$1.txt" | sort -u | wc -l)" "$2"; }
  _s S1 'TYPE-085|DEF-102|O-N21'
  _s S2 'DEF-104|O-N22'
  _s S3 'block string|block-string|DEF-98|probe ?15|in_block_pin'
  _s S4 'TYPE-083|DEF-96'
  _s S5 'DEF-97|N-21\b'
  _s S6 'O-N17|O-N27'
  _s S7 'vec_owning_get_moves_out|moves? the element out|second read'
  _s S8 'lent bare|reach here is nil|nothing in .src/. changes'
  _s S9 'vec_alias_param_free|vec_alias_param_grow|sparseset_alias_param_free|bytes_alias_param_grow|vec_alias_for_binding_free|vec_alias_generic_passout|probe17_lent_field_drop|probe15_block_string_close'
  _s S10 'not in the pin|no pin of ours|not our pin|which the pin'
}

# The same, per file: `<S> <count> <file>` lines, sorted -- what step 7 diffs.
sweeps_by_file() {
  local d="$A/sweeps_$1" s
  for s in S1 S2 S3 S4 S5 S6 S7 S8 S9 S10; do cut -d: -f1 "$d/$s.txt" | sort | uniq -c | sed "s/^/$s /"; done
}

# The full harness, its log kept, its summary lines printed.
#     harness <label>
harness() {
  python3 "$REPO/harness/run.py" > "$A/$1.log" 2>&1
  echo "harness exit $?"
  grep -E 'unit\(s\) passed|^GREEN|^RED|^      (conformance|probe|probe-refused|parse|rejection|unit) +\(' "$A/$1.log"
}

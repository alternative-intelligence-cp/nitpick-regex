# meta/roadmap/0.1/0.1.0_tools/env.sh -- sourced at the top of EVERY command block
# of `0.1.0.md`, because a Bash call keeps no variables and no functions from the
# call before it. Set REPO first, to the dispatch's REPO line:
#
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/0.1/0.1.0_tools/env.sh"
#
# `$NPK_TREE` is read with `git show` only -- never written, built or fetched in.
# Every `rm` below names its target through `${VAR:?}`, so an unset variable stops
# the shell instead of widening the removal. Nothing here prints a path above the
# repository, so no output carries a home directory into a record (`PLAYBOOK.md` §6).
: "${REPO:?set REPO to the REPO line of the dispatch, first}"
REPO=$(realpath "$REPO")
WB=$(realpath "$REPO/..")
NPK_TREE=$(realpath "$WB/../nitpick")
PIN=c970483                                    # the pin this subcycle is planned at
PIN_FULL=c9704830ea9c738f523bf6646a355f52679b3aee
CTL=9f6f370                                    # the workbench's CONTROL copy: notices 67, 69, 70 -- NOT the pin
PRE=950bb1d                                    # a kept pin carrying the compiler's DEF-7 (B-15a rule 2's reason)
FIX=94874ce                                    # the first kept pin carrying its fix
NPKC=$WB/.internal/toolchain/$PIN/npkc
NPKRT=$WB/.internal/toolchain/$PIN/npkrt.o
T=$REPO/meta/roadmap/0.1/0.1.0_tools          # these tools
A=$REPO/.internal/f10                          # gitignored scratch
export NPKC NPKRT                              # the harness reads them from the ENVIRONMENT
mkdir -p "$A"

# Compile each file as a root with the compiler of a kept pin, from its own
# directory, and print `<file>: CODE L:C` per diagnostic, or `<file> compiles`.
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

# Build each program with the compiler of a kept pin and run it at -O0 and through
# `opt -O2`: `npkc`, `llc`, `ld.lld`, the binary -- all four, because `npkc` exit 0
# is not well-formedness (O-N11). Prints `<name> at <pin>: npkc N, llc N, -O0 X, -O2 Y`.
#     run4 <pin> <file>...
run4() {
  local pin=$1; shift
  local cc=$WB/.internal/toolchain/$pin/npkc rt=$WB/.internal/toolchain/$pin/npkrt.o
  local f src b o nc lc r0 r2
  mkdir -p "$A/run4"
  for f in "$@"; do
    src=$f; [ "${f#/}" = "$f" ] && src="$REPO/$f"
    b=$(basename "$src" .npk); o="$A/run4/${b}_$pin"
    ( cd "$(dirname "$src")" && "$cc" "$(basename "$src")" -o "$o.ll" ) > "$o.npkc" 2>&1
    nc=$?
    if [ "$nc" -ne 0 ]; then
      echo "$b at $pin: npkc $nc -- $(grep -oE '^NITPICK-[A-Z]+-[0-9]+' "$o.npkc" | sort -u | tr '\n' ' ' | sed 's/ $//')"
      continue
    fi
    llc -O0 -filetype=obj -relocation-model=static "$o.ll" -o "$o.o" 2> "$o.llc"
    lc=$?
    if [ "$lc" -ne 0 ]; then echo "$b at $pin: npkc 0, llc $lc"; continue; fi
    ld.lld -static "$o.o" "$rt" -o "$o"
    "$o" > "$o.out0" 2>&1
    r0=$?
    opt -O2 -S "$o.ll" -o "$o.opt.ll" && llc -O2 -filetype=obj -relocation-model=static "$o.opt.ll" -o "$o.o2" \
      && ld.lld -static "$o.o2" "$rt" -o "$o.bin2"
    "$o.bin2" > "$o.out2" 2>&1
    r2=$?
    echo "$b at $pin: npkc 0, llc 0, -O0 $r0, -O2 $r2"
  done
}

# O-B3's instrument: NITPICK-REACH-003 on a program that imports one module and has
# no failsafe lists every identity a consumer of that module owes (0.0.4b step 11).
#     bills <pin> <module>...     (relative to the repository)
bills() {
  local pin=$1; shift
  local cc=$WB/.internal/toolchain/$pin/npkc d="$A/bills/x" m n ids
  mkdir -p "$d"
  for m in "$@"; do
    n=$(echo "$m" | tr '/.' '__')
    # four levels below the repository, like a file in tests/unit/ is two
    printf 'mod:b_%s;\nuse "../../../../%s".*;\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n' "$n" "$m" > "$d/b_$n.npk"
    ids=$(cd "$d" && "$cc" "b_$n.npk" -o /dev/null 2>&1 | grep -o 'NITPICK-REACH-003.*' | head -1 \
          | sed -n 's/.* identities: \(.*\) -- with.*/\1/p' | tr -d ',' | tr ' ' '\n' | grep -v '^$' | sort | tr '\n' ' ')
    printf '%-30s %2d  %s\n' "$m" "$(echo $ids | wc -w)" "$ids" | sed 's/ *$//'
  done
}

# Does a program's failsafe name EXACTLY what REACH asks -- no arm missing, none
# extra? The same program with its failsafe cut off, compiled four levels deep so
# its `../../src/` imports still resolve, makes NITPICK-REACH-003 list the identities.
#     arms_check <file>...
arms_check() {
  local f src b ids arms
  mkdir -p "$A/arms/x"
  for f in "$@"; do
    src=$f; [ "${f#/}" = "$f" ] && src="$REPO/$f"
    b=$(basename "$f" .npk)
    python3 -B - "$src" "$A/arms/x/zz_$b.npk" "zz_$b" <<'PY'
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

# A copy of the working tree AS IT STANDS -- tracked files and new ones, not the
# ignored -- at $A/ctl/<name>, for a control to change one thing in. Prints nothing.
#     ctl <name>
ctl() {
  local d="$A/ctl/$1"
  rm -rf "${d:?}"; mkdir -p "$d"
  ( cd "$REPO" && git ls-files -co --exclude-standard -z | xargs -0 tar -cf - ) | tar -xf - -C "$d"
}

# Replace exactly one occurrence of OLD with NEW in FILE, or say how many there were
# and change nothing. Prints `sub <file>: x<count>`.
#     sub <file> <old> <new>
sub() {
  python3 -B - "$1" "$2" "$3" <<'PY'
import sys
p, old, new = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(p, encoding="utf-8", newline="").read()
n = s.count(old)
if n == 1:
    open(p, "w", encoding="utf-8", newline="").write(s.replace(old, new))
print(f"sub {p.rsplit('/', 1)[-1]}: x{n}")
PY
}

# One tree check, run over a root: its verdict, its failures' first 150 characters.
#     tc <root> <check_name>
tc() {
  python3 -B - "$1" "$2" <<'PY'
import sys
sys.path.insert(0, sys.argv[1] + "/harness")
import treecheck
r = getattr(treecheck, sys.argv[2])(sys.argv[1])
print(("ok   " if r.ok else "FAIL ") + r.name + f"  {len(r.failures)} failure(s)  over {r.examined}")
for f in r.failures:
    print("     " + f[:150])
PY
}

# The full harness, its log kept, its summary lines printed.
#     harness <label>
harness() {
  free -g | awk '/^Mem:/ {print "available GiB:", $7}'
  ( cd "$REPO" && python3 -B harness/run.py ) > "$A/$1.log" 2>&1
  echo "harness exit $?"
  grep -E 'unit\(s\) passed|^GREEN|^RED|^      (conformance|probe|probe-refused|parse|rejection|unit) +\(' "$A/$1.log"
}

# RX-113's REASON-SWEEP (`0.1.0.md` §7): every live line that cites B-15a rule 2's
# reason -- by id (I) and by the shape of the defect stated as current (P). Records
# are out of scope and stay as written: `meta/roadmap/done/`, `meta/audits/`,
# `meta/DECISIONS.md`'s settled text and the transcripts (W-28). This plan and its
# tools quote every pattern, so they are excluded too. Per file, counts only.
#     reasons
reasons() {
  local ex=( -- . ':!meta/roadmap/0.1/0.1.0.md' ':!meta/roadmap/0.1/0.1.0_tools' ':!meta/roadmap/done'
             ':!meta/audits' ':!meta/DECISIONS.md' ':!*TRANSCRIPT.txt' )
  echo "I: $(git -C "$REPO" grep --untracked -h -I -E '\bO-N13\b|\bDEF-7\b|\bRX-113\b' "${ex[@]}" | wc -l) line(s)"
  git -C "$REPO" grep --untracked -c -I -E '\bO-N13\b|\bDEF-7\b|\bRX-113\b' "${ex[@]}" | sort | sed 's/^/    /'
  local p='downgrad|silently cancel|cancels? the re-?export|declines? (a|any) name already bound|without merging|first import of a name wins|symtab_bind_import|silent-cancellation'
  echo "P: $(git -C "$REPO" grep --untracked -h -I -i -E "$p" "${ex[@]}" | wc -l) line(s)"
  git -C "$REPO" grep --untracked -c -I -i -E "$p" "${ex[@]}" | sort | sed 's/^/    /'
}

# Each path of a step, against HEAD: `new` (absent from HEAD), `changed` (differs
# from HEAD) or `same`. It reads the same whether the steps before were committed
# (the worker) or only staged (a rehearsal), which a status tally's letters do not.
#     tally <path>...
tally() {
  local p
  for p in "$@"; do
    if ! git -C "$REPO" cat-file -e "HEAD:$p" 2>/dev/null; then echo "new      $p"
    elif git -C "$REPO" diff --quiet HEAD -- "$p"; then echo "same     $p"
    else echo "changed  $p"; fi
  done
}

OLD=c3bdae2                                    # the pin before this one, kept for controls

# Step 1's two programs, written into a control copy: a consumer of `src/lib.npk`
# naming only the arms `950bb1d` and `94874ce` have, and a file whose `pub use`
# lines are the only imports of the names it then uses.
#     rx113_programs <control-dir>
rx113_programs() {
  cat > "$1/tests/conformance/zz_old_consumer.npk" <<'NPK'
mod:zz_old_consumer;
use "../../src/lib.npk".*;
func:main = int32(cstring[]:_~argv) {
    exit 0i32;
};
func:failsafe = int32(Error:e) {
    pick (e) {
        (HeapBadRequest) { exit 91i32; },
        (HeapOom)        { exit 92i32; },
        (Unreachable)    { exit 95i32; },
        (WildLeak)       { exit 96i32; },
        (ERegexPattern)  { exit 97i32; },
        (*)              { exit 99i32; }
    }
    exit 9i32;
};
NPK
  sed -n '/^func:failsafe/,$p' "$REPO/tests/unit/vec_get_pod_struct.npk" > "$A/fs11.txt"
  { cat <<'NPK'
mod:zz_pub_binds;
pub use "../../src/core/vec.npk".Vec;
pub use "../../src/core/vec.npk".vec_init;
pub use "../../src/core/vec.npk".vec_push;
pub use "../../src/core/vec.npk".vec_get;
pub use "../../src/core/vec.npk".vec_free;
func:main = int32(cstring[]:_~argv) {
    Vec<int64>:v = raw vec_init::<int64>(1i64);
    drop vec_push(@v, 5i64);
    int64:x = raw vec_get(v, 0i64);
    drop vec_free(@v);
    if (x != 5i64) { exit 10i32; }
    exit 0i32;
};
NPK
    cat "$A/fs11.txt"; } > "$1/tests/unit/zz_pub_binds.npk"
}

# Step 3's two programs: the pattern's owner reassigned while a cursor holds its
# view, and a cursor over a view of a LOCAL, returned.
#     cursor_programs <control-dir>
cursor_programs() {
  sed -n '/^func:failsafe/,$p' "$REPO/tests/unit/vec_get_pod_struct.npk" > "$A/fs11.txt"
  { cat <<'NPK'
mod:zz_owner_written;
use "../../src/syntax/syntax.npk".*;
func:main = int32(cstring[]:_~argv) {
    string:s = string_concat("abbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "c");
    Cursor:c = raw cursor_init(string_bytes(s));
    s = string_concat("xyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy", "z");
    int32:b = raw cursor_bump(@c);
    exit b;
};
NPK
    cat "$A/fs11.txt"; } > "$1/tests/unit/zz_owner_written.npk"
  { cat <<'NPK'
mod:zz_local_returned;
use "../../src/syntax/syntax.npk".*;
func:make = Cursor() never fails {
    string:s = string_concat("ab", "c");
    pass raw cursor_init(string_bytes(s));
};
func:main = int32(cstring[]:_~argv) {
    Cursor:c = raw make();
    int32:b = raw cursor_bump(@c);
    exit b;
};
NPK
    cat "$A/fs11.txt"; } > "$1/tests/unit/zz_local_returned.npk"
}

# The COUNT SWEEP (`0.1.0.md` §7): the statements of state or of a count that steps 1
# to 5 make false and step 6 corrects, one pattern each. Seven lines before step 6,
# none after. Records excluded, as for `reasons`.
#     counts
counts() {
  local ex=( -- . ':!meta/roadmap/0.1/0.1.0.md' ':!meta/roadmap/0.1/0.1.0_tools' ':!meta/roadmap/done'
             ':!meta/audits' ':!meta/DECISIONS.md' ':!*TRANSCRIPT.txt' )
  local p='twenty-one consumer-facing|All twenty-one import|\*\*220 units\*\* \(after the cycle 0\.0 close|opens next\*\* from|No matching happens yet\*\*: `src/syntax/`|nothing matches a pattern yet\. \*\*Cycle 0\.1|planned and rehearsed at `c970483`\*\* \|'
  echo "counts: $(git -C "$REPO" grep --untracked -h -I -E "$p" "${ex[@]}" | wc -l) line(s)"
  git -C "$REPO" grep --untracked -n -I -E "$p" "${ex[@]}" | cut -d: -f1,2 | sort -t: -k1,1 -k2,2n | sed 's/^/    /'
}

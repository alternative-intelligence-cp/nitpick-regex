# meta/roadmap/0.2/0.2.3_tools/facts.sh -- `0.2.3.md` §1: re-derive what this plan rests on at the pin, in scratch copies
# of the tree, never in it. Sourced after `env.sh`, as block 0b, BEFORE step 1:
#
#     . "$REPO/meta/roadmap/0.2/0.2.3_tools/env.sh"; . "$T/facts.sh"
#
# `head` is the working tree as it stands; `new` is it with steps 1 … 4 applied by GNU `patch` to the copy alone (`git
# apply` run inside this checkout would resolve the paths against the checkout), dated as `apply.py` dates them -- the
# code this plan's patches carry. Probes live in `$F/p`, outside both copies. A check is asked of its OWN tree's harness.
# The compiler's tree is read with `git show` alone. The copies are removed at the end.
: "${REPO:?}" "${NPKC:?}" "${NPKRT:?}" "${A:?}" "${T:?}"
F=$A/facts
DAY=$(cat "$A/date" 2>/dev/null || date +%F)
fresh() {   # fresh <name> [<step>...]: the working tree as it stands at $F/<name>, then each step's patch
  local d=$1 n; shift
  mkdir -p "$F/$d"
  ( cd "$REPO" && git ls-files -co --exclude-standard -z | xargs -0 tar -cf - ) | tar -xf - -C "$F/$d"
  for n in "$@"; do
    sed "s/@@DATE023@@/$DAY/g" "$T/step$n.patch" | patch -p1 -s --no-backup-if-mismatch -d "$F/$d" \
      || echo "STOP: step$n does not apply to a copy of the tree"
  done
}
legs() {    # legs <src> <prefix> <name>=<argv words>...: build at both legs, then run once per case, each word an argv
            # entry, and print `<prefix> <name>: <exit> at -O0, <exit> after opt -O2` -- or the refusal's codes
  local src=$1 l=$2 o c a e0 e2; shift 2
  o="$F/bin/$(basename "$src" .npk)"; mkdir -p "$F/bin"
  if ! ( cd "$(dirname "$src")" && "$NPKC" "$(basename "$src")" -o "$o.ll" ) > "$o.err" 2>&1; then
    echo "$l: npkc refused -- $(grep -oE '^NITPICK-[A-Z]+-[0-9]+ [^ ]+' "$o.err" | sed -E 's| ([^ ]*/)?([^/ ]+:[0-9]+:[0-9]+):$| \2|' \
      | tr '\n' ' ' | sed 's/ $//')"; return
  fi
  llc -O0 -filetype=obj -relocation-model=static "$o.ll" -o "$o.o" && ld.lld -static "$o.o" "$NPKRT" -o "$o.x0" \
    && opt -O2 -S "$o.ll" -o "$o.2.ll" && llc -O2 -filetype=obj -relocation-model=static "$o.2.ll" -o "$o.2.o" \
    && ld.lld -static "$o.2.o" "$NPKRT" -o "$o.x2"
  for c in "$@"; do a=${c#*=}
    "$o.x0" $a > /dev/null 2>&1; e0=$?; "$o.x2" $a > /dev/null 2>&1; e2=$?
    echo "$l ${c%%=*}: $e0 at -O0, $e2 after opt -O2"; done
}
count() {   # count <copy's unit> <anchor line> <label>=<expression>...: a scratch copy of the unit per expression, the
            # anchor line preceded by an exit of the expression's low byte, then its high byte, each built and run at
            # both legs -- the counts a unit's floors stand on, read out of the unit itself, as 0.2.2's worker read the fuzz's
  local src=$1 anchor=$2 e lab x part lo hi r0 r2; shift 2
  for e in "$@"; do lab=${e%%=*}; x=${e#*=}
    for part in lo hi; do
      if [ "$part" = lo ]; then w="(($x) & 255i64)"; else w="((($x) >> 8i64) & 255i64)"; fi
      python3 -B - "$src" "$(dirname "$src")/zz_count.npk" "$anchor" "    pass $w =>! int32;" <<'PY'
import re, sys
s = open(sys.argv[1], encoding="utf-8").read()
assert s.count(sys.argv[3]) == 1, "anchor"
s = s.replace(sys.argv[3], sys.argv[4] + "\n" + sys.argv[3])
s = re.sub(r"^mod:[a-z_]+;", "mod:zz_count;", s, count=1, flags=re.M)
open(sys.argv[2], "w", encoding="utf-8").write(s)
PY
      r0=$(legs "$(dirname "$src")/zz_count.npk" "x" "v=" | sed -E 's/.*: ([0-9]+) at -O0, ([0-9]+) after.*/\1 \2/')
      [ "${r0% *}" = "${r0#* }" ] || echo "LEGS DIFFER: $lab $part $r0"
      eval "$part=${r0% *}"
    done
    echo "  $lab $((hi * 256 + lo))"
  done
  rm -f "$(dirname "$src")/zz_count.npk"
}
FAILSAFE='func:failsafe = int32(Error:e) {
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
        (ShiftRange)        { exit 115i32; },
        (*)                 { exit 99i32; }
    }
    exit 9i32;
};'

rm -rf "${F:?}"; mkdir -p "$F/p"
fresh head; fresh new 1 2 3 4

# ---- §1.2 the names this plan gives, against the pin's keyword file, prelude and bare-name builtins; and `on`, reserved
KW=$(git -C "$NPK_TREE" show $PIN:src/frontend/keywords.npk)
PRE=$(git -C "$NPK_TREE" show $PIN:src/prelude/prelude.npk)
BI=$(git -C "$NPK_TREE" show $PIN:src/frontend/builtins.npk)
for n in normal hir_normalise hir_copy_groups Todo TODO_ONE TODO_LIST TODO_LEAVE push_w sort_ranges leave_class leave_list \
         emit dead flat width mid left holds cur same_bytes is_tree ranges_exact same_groups normal_text pattern_normal \
         normed normed_text one_form apart concats deep alternates empties classes put3 long_classes texts pairs rootless \
         seeded bits merged literals CLASSES UNIVERSE MERGED_FLOOR LITERAL_FLOOR GNode Gen roll add adopt popcount gen cp_of \
         put_cp put_hex put_class put_pat put_dump pattern_of noisy_of dump_of normal_of same_text mutate TREES DEPTH \
         PAIRS_FLOOR JOINED_FLOOR NOISE_FLOOR MUTANT_FLOOR oracle_find NO_ORACLE hay HAYS PATTERNS on; do
  echo "§1.2 \`$n\`: $(printf '%s' "$KW" | grep -c "\"$n\"") keyword line(s), $(printf '%s' "$PRE" | grep -cE "^pub [a-z]+:$n\b|^pub fixed [a-z0-9]+:$n\b") prelude declaration(s), $(printf '%s' "$BI" | grep -c "\"$n\"") builtin line(s)"
done

# ---- §1.3 the language the normaliser and its units are written in, asked of the pin
printf 'mod:pa;\n\nfunc:main = int32(cstring[]:_~argv) {\n    int64:on = 1i64;\n    exit on =>! int32;\n};\n\n%s\n' "$FAILSAFE" > "$F/p/pa.npk"
legs "$F/p/pa.npk" "§1.3 a local named \`on\`" "run="
printf 'mod:pb;\n\nfunc:f = int64(int64:x) never fails {\n    pass x;\n};\n\nfunc:main = int32(cstring[]:_~argv) {\n    int64:i = 0i64;\n    while (i < 3i64) decreases 3i64 - (raw f(i)) {\n        i = i + 1i64;\n    }\n    exit 0i32;\n};\n\n%s\n' "$FAILSAFE" > "$F/p/pb.npk"
legs "$F/p/pb.npk" "§1.3 a \`decreases\` measure that calls a function not \`pure\`" "run="
printf 'mod:pc;\n\nfunc:main = int32(cstring[]:argv) {\n    uint32:hi = 4294967295u32;\n    if (argv.len > 1i64) { hi = 1114111u32; }\n    int64:wide = (hi => int64) + 1i64;\n    if (wide != 4294967296i64) { if (wide != 1114112i64) { exit 5i32; } }\n    uint32:next = hi + 1u32;\n    if (next == 0u32) { exit 6i32; }\n    exit 7i32;\n};\n\n%s\n' "$FAILSAFE" > "$F/p/pc.npk"
legs "$F/p/pc.npk" "§1.3 a range's end plus one" "at 2^32 - 1 in \`uint32\` (93), where \`int64\` holds it=" "at U+10FFFF (7)=a"

# ---- §1.4 what each module costs a consumer
echo "§1.4 as it stands:"; reach "$F/head/src/hir/repr.npk" "$F/head/src/hir/hir.npk" | sed 's/^/  /'
echo "§1.4 after step 4:"; reach "$F/new/src/hir/repr.npk" "$F/new/src/hir/normal.npk" "$F/new/src/hir/hir.npk" | sed 's/^/  /'

# ---- §1.5 the tree checks, before and after, each copy asked with its own harness
echo "§1.5 as it stands:"; tchecks "$F/head"
echo "§1.5 after step 4:"; tchecks "$F/new"

# ---- §1.6 the units in the patched copy, both legs
echo "§1.6 after step 4:"
for u in hir_normalise hir_normalise_not_fresh hir_normalise_not_a_tree hir_normalise_gate hir_normalise_oracle hir_build \
         hir_dump hir_unit hir_build_classes hir_build_fold; do
  run4 "$F/new/tests/unit/$u.npk"; done | sed 's/^/  /'

# ---- §1.7 the counts the units' floors stand on, read out of the units in the patched copy
echo "§1.7 hir_normalise's seeded classes:"
count "$F/new/tests/unit/hir_normalise.npk" "    if ((merged < MERGED_FLOOR) || (literals < LITERAL_FLOOR)) { pass 84i32; }" \
  "classes=k" "merged or sorted=merged" "left a Literal=literals"
echo "§1.7 hir_normalise_gate's trees:"
count "$F/new/tests/unit/hir_normalise_gate.npk" "    if (pairs < PAIRS_FLOOR) { pass 13i32; }" \
  "trees=n" "pairs textually different=pairs" "pairs only normalisation joins=joined" "runs of pieces wrapped=g.wraps" \
  "runs of alternatives wrapped=g.altwraps" "a (?:) or an Empty respelt=g.empties" "a literal as a class or an escape=g.litcls" \
  "a class respelt=g.clsnoise" "a quantifier or an anchor respelt=g.quants" "alternatives swapped=mutants[0]" \
  "a byte bit flipped=mutants[1]" "pieces swapped=mutants[2]" "a laziness flipped=mutants[3]"
# and that the build ALONE leaves a structurally equal pair apart, which is why the Gate needs the normaliser
{ printf 'mod:pd;\n\nuse "../new/src/core/core.npk".*;\nuse "../new/src/syntax/syntax.npk".*;\nuse "../new/src/hir/hir.npk".*;\n\n'
  printf 'func:dump_of = int64(string:s, bool:norm) never fails {\n    fixed uint8[]:p = string_bytes(s);\n    Ast:t = raw ast_init(8i64);\n    discard(raw parse_pattern(p, @t));\n'
  printf '    Hir:h = raw hir_init(8i64);\n    discard(raw hir_build(p, t, @h));\n    Hir:n = raw hir_init(8i64);\n    drop hir_normalise(@h, @n);\n    Bytes:b = raw bytes_init(64i64);\n'
  printf '    if (norm) { drop hir_dump(@n, @b); } else { drop hir_dump(@h, @b); }\n    int64:r = raw bytes_len(@b);\n    drop hir_free(@n);\n    drop hir_free(@h);\n    drop ast_free(@t);\n    pass r;\n};\n\n'
  printf 'func:main = int32(cstring[]:argv) {\n    bool:norm = argv.len > 1i64;\n    exit ((raw dump_of("a(?:bc)", norm)) - (raw dump_of("abc", norm))) =>! int32;\n};\n\n%s\n' "$FAILSAFE"; } > "$F/p/pd.npk"
legs "$F/p/pd.npk" "§1.7 \`a(?:bc)\`'s dump less \`abc\`'s, in bytes:" "built (9)=" "normalised (0)=a"

# ---- §1.8 what the patches add: the shapes open or silent at the pin, a plain view, the placeholder -- and the scanner's
#      own positive control, a planted file holding every shape, and a clean one naming each in strings and comments
cat > "$F/p/planted.npk.txt" <<'NPK'
fixed int64:N = comptime(3i64);
macro:m = { pass 1i64; };
float64:f = 1.5;
enum:E = { A = 1i32, B };
enum:G = { C = 2i32; D = 3i32; };
func:gen<T> = T(T:x) never fails { pass x; };
if (r.is_error) { exit 1i32; }
int64:v = r ?! E;
#unreachable();
int64:w = #wild_slice(p, 1i64);
give x;
fall two;
int32:k = q.frac;
Vec<int64>:z = move(y);
uint8[]:bs = string_bytes(s);
exit 3i64;
NPK
cat > "$F/p/clean.npk.txt" <<'NPK'
// comptime macro 1.5 enum:E A = 1i32 func:gen<T> is_error ?! #unreachable #wild_slice give fall frac move( uint8[] exit 3i64
pub fixed int64:X = 1i64;
fixed uint8[]:bs = string_bytes("enum:E = { A = 1i32, B }; give fall frac move(x) exit 3i64");
exit 0i32;
NPK
python3 -B - "$T" "$F/head" "$F/p" <<'PY'
import collections, os, re, sys
T, head, P = sys.argv[1], sys.argv[2], sys.argv[3]
def blank(s):
    s = re.sub(r'"(?:\\.|[^"\\])*"', '""', s)
    return s.split("//", 1)[0]
pats = {"comptime": r"\bcomptime\b", "a macro": r"\bmacro\b|#[a-z_]+\s*\(", "a float literal": r"\b\d+\.\d+(f32|f64)?\b",
        "an enum": r"\benum\s*:", "a generic declaration": r"func:[A-Za-z_]+<", "an explicit variant value": r"(?<![\w:])[A-Z]\w*\s*=\s*-?\d",
        "`is_error`": r"\bis_error\b", "`?|` or `?!`": r"\?\||\?!", "`#unreachable`": r"#unreachable", "`#wild_slice`": r"#wild_slice",
        "`give` or `fall`": r"\b(give|fall)\b", "`frac`": r"\bfrac\b", "`move(`": r"\bmove\s*\(", "a plain `uint8[]`": r"(?<!fixed )\buint8\[\]"}
def exits(code):
    ops = collections.Counter()
    for c in code:
        for m in re.finditer(r"\bexit\s+([^;]+);", c):
            o = m.group(1).strip()
            ops["an `i32` literal" if re.fullmatch(r"\d+i32", o) else "`%s`" % o] += 1
    return ops
for name in ("planted", "clean"):
    code = [blank(l) for l in open(os.path.join(P, name + ".npk.txt"), encoding="utf-8")]
    print("§1.8 the scanner over its %s control: " % name + "; ".join("%s %d" % (k, sum(1 for c in code if re.search(v, c))) for k, v in pats.items()))
    print("§1.8 its %s control's `exit` operands: " % name + ", ".join("%s %d" % (k, v) for k, v in sorted(exits(code).items())))
added, touched = [], set()
for n in range(1, 5):
    path = None
    for line in open(os.path.join(T, "step%d.patch" % n), encoding="utf-8"):
        if line.startswith("+++ b/"):
            path = line[6:].strip(); touched.add(path)
        elif line.startswith("+") and not line.startswith("+++") and path and path.endswith(".npk"):
            added.append(line[1:])
code = [blank(l) for l in added]
print("§1.8 the patches' %d added `.npk` lines, comments and strings blanked:" % len(added))
print("  " + "; ".join("%s %d" % (k, sum(1 for c in code if re.search(v, c))) for k, v in pats.items()))
print("§1.8 their `exit` operands: " + ", ".join("%s %d" % (k, v) for k, v in sorted(exits(code).items())))
held = sorted(p for p in touched if os.path.exists(os.path.join(head, p)) and "@@DATE023@@" in open(os.path.join(head, p), encoding="utf-8").read())
print("§1.8 the %d file(s) the patches touch that hold `@@DATE023@@` as the tree stands: %s" % (len(held), " ".join(held) or "none"))
PY

# ---- §1.9 RX-232's list of what it dated, against every note that cites it, by the commit that wrote the note
echo "§1.9 the notes citing RX-232, by the commit that wrote each:"
git -C "$REPO" grep -n -E "cycle 0\.2\.2 (—|--) RX-232" HEAD -- meta/specs meta/roadmap/0.2/README.md src | sed -E 's/^HEAD://' | while IFS=: read -r f l _; do
  echo "  $(git -C "$REPO" blame -L "$l,$l" --porcelain HEAD -- "$f" | head -1 | cut -c1-7) $f"; done | sort | uniq -c | sed 's/^ */  /'
echo "§1.9 RX-232's own list: $(awk '/^### RX-232 /{on=1} on && /^### RX-233 /{exit} on' "$REPO/meta/DECISIONS.md" | tr '\n' ' ' | grep -oE "H-8, H-16, S-13 and C-14 are dated, and \`limits.npk\`'s[^.]*")"
echo "§1.9 PD-107's row names: $(grep -oE "H-8, H-16, S-13, C-14, \`TESTING.md\`'s fuzz note and \`limits.npk\`'s comment dated" "$REPO/meta/roadmap/0.2/0.2.2.md" | head -1)"

# ---- §1.10 what a run leaves: rx120.sh's own python3, run alone in each copy, and what it leaves in harness/__pycache__/
for c in head new; do
  rm -rf "${F:?}/$c/harness/__pycache__" "${F:?}/$c/.internal"
  ( cd "$F/$c" && bash harness/baseline/rx120.sh > "$F/rx120.$c.log" 2>&1 ); r=$?
  echo "§1.10 $c: rx120.sh line $(grep -nE '^python3 (-B )?- "\$root"' "$F/$c/harness/baseline/rx120.sh" | cut -d: -f1): $(grep -oE '^python3 (-B )?-' "$F/$c/harness/baseline/rx120.sh"); exit $r; left in harness/__pycache__/: $(ls "$F/$c/harness/__pycache__" 2>/dev/null | sed -E 's/cpython-[0-9]+/cpython-N/' | tr '\n' ' ' | sed 's/ $//')"
done

# ---- §1.11 the audits' items for this repository, at the tree: each fix's text present, and EK2's actions
for kv in "RA-1|tests/README.md|is not available to this library" "RA-2|harness/treecheck.py|the documents audit's RA-2" \
          "RA-3|meta/OPEN_QUESTIONS.md|the documents audit's RA-3" "RA-4|nitpick.toml|hir_nodes_read" \
          "RA-5|README.md|its first four parts" "RA-6|CLAUDE.md|thirty ways" "RA-7|meta/specs/HIR.md|the documents audit's RA-7" \
          "RA-8|tests/probe/TRANSCRIPT.txt|NOTE ADDED 2026-10-10 BY CYCLE 0.2.2" "E2-6|meta/roadmap/0.14/README.md|the ecosystem audit's E2-6" \
          "E2-10|meta/roadmap/ROADMAP.md|the ecosystem audit's E2-10"; do
  IFS='|' read -r id f s <<< "$kv"
  echo "§1.11 $id: \`$s\` in $f, $(grep -cF "$s" "$REPO/$f") line(s)"
done
echo "§1.11 EK2: $(grep -cE 'uses: actions/(checkout|cache)@v4' "$REPO/.github/workflows/ci.yml") action line(s) on \`@v4\`; the header's triage note: $(grep -c 'one research request serves both' "$REPO/.github/workflows/ci.yml") line(s)"

rm -rf "${F:?}"

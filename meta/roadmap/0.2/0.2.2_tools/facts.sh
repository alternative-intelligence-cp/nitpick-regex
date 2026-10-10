# meta/roadmap/0.2/0.2.2_tools/facts.sh -- `0.2.2.md` §1: re-derive what this plan rests on at the pin, in scratch copies
# of the tree, never in it. Sourced after `env.sh`, as block 0b, BEFORE step 1:
#
#     . "$REPO/meta/roadmap/0.2/0.2.2_tools/env.sh"; . "$T/facts.sh"
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
    sed "s/@@DATE022@@/$DAY/g" "$T/step$n.patch" | patch -p1 -s --no-backup-if-mismatch -d "$F/$d" \
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

# ---- §1.2 the names this plan gives, against the pin's keyword file and prelude; and `end`, which is reserved
KW=$(git -C "$NPK_TREE" show $PIN:src/frontend/keywords.npk)
PRE=$(git -C "$NPK_TREE" show $PIN:src/prelude/prelude.npk)
for n in hir_build_refusal factor LBRACE prod qend bound refusal_of refused_bytes same_text stopped readme edges factors \
         order extended stops deep by_hand pipeline program INST_BYTES quant gap pattern factor_of ordered run PATTERNS \
         NODES BUILT_FLOOR REFUSED_FLOOR around own most end; do
  echo "§1.2 \`$n\`: $(printf '%s' "$KW" | grep -c "\"$n\"") keyword line(s), $(printf '%s' "$PRE" | grep -cE "^pub [a-z]+:$n\b|^pub fixed [a-z0-9]+:$n\b") prelude declaration(s)"
done

# ---- §1.3 the cycle README's pattern on the way down, asked of the tree's own parser: each question a run, its answer the exit
{ printf 'mod:readme;\n\nuse "../head/src/core/core.npk".*;\nuse "../head/src/syntax/syntax.npk".*;\n\n'
  printf 'func:brace = int64(fixed uint8[]:pat, AstNode:n) never fails {\n    int64:q = n.pos + n.len - 1i64;\n'
  printf '    while (pat[q] != 123u8) decreases q - n.pos { q = q - 1i64; }\n    pass q;\n};\n\n'
  printf 'func:main = int32(cstring[]:argv) {\n    int64:k = argv.len;\n    fixed uint8[]:pat = string_bytes("((a{1000}){1000}){1000}");\n'
  printf '    Ast:t = raw ast_init(8i64);\n    discard(raw parse_pattern(pat, @t));\n'
  printf '    int64[3]:at = [0i64, 0i64, 0i64];\n    int64[3]:f = [0i64, 0i64, 0i64];\n    int64:reps = 0i64;\n    int64:m = t.root;\n    int64:steps = 0i64;\n'
  printf '    while ((m != AST_NONE) && (reps < 3i64)) decreases 16i64 - steps {\n        steps = steps + 1i64;\n        AstNode:x = raw ast_get(t, m);\n'
  printf '        if (x.kind == AstKind.Repeat) { at[reps] = raw brace(pat, x); f[reps] = x.c; reps = reps + 1i64; m = x.a; }\n'
  printf '        else if (x.kind == AstKind.Group) { m = x.a; }\n        else { m = AST_NONE; }\n    }\n'
  printf '    int32:r = 0i32;\n    if (k == 1i64) { r = reps =>! int32; }\n    if ((k >= 2i64) && (k <= 4i64)) { r = at[k - 2i64] =>! int32; }\n'
  printf '    if (k == 5i64) { int64:p = 1i64; int64:i = 0i64; while ((i < 3i64) && (r == 0i32)) decreases 3i64 - i {\n'
  printf '        p = p * f[i]; i = i + 1i64; if (p > NREGEX_REPEAT_PRODUCT) { r = i =>! int32; } } }\n'
  printf '    if (k == 6i64) { if (NREGEX_REPEAT_PRODUCT == NREGEX_PROGRAM_INSTRUCTIONS) { r = 1i32; } }\n'
  printf '    if (k == 7i64) { r = pat.len =>! int32; }\n    drop ast_free(@t);\n    exit r;\n};\n\n%s\n' "$FAILSAFE"; } > "$F/p/readme.npk"
legs "$F/p/readme.npk" "§1.3 \`((a{1000}){1000}){1000}\`," "its Repeats on the way down from the root=" \
  "the first one's \`{\`, the last written=a" "the second one's \`{\`=a a" "the third one's \`{\`, the first written=a a a" \
  "the factor, counted on the way down, at which the product first passes NREGEX_REPEAT_PRODUCT=a a a a" \
  "NREGEX_REPEAT_PRODUCT equal to NREGEX_PROGRAM_INSTRUCTIONS (1)=a a a a a" "its length in bytes=a a a a a a"

# ---- §1.4 under `x`, what stands between an atom and its quantifier
{ printf 'mod:xmode;\n\nuse "../head/src/core/core.npk".*;\nuse "../head/src/syntax/syntax.npk".*;\n\n'
  printf 'func:main = int32(cstring[]:argv) {\n    int64:k = argv.len;\n    string:s = "(?x)(a {1000}){1000}";\n'
  printf '    if (k >= 3i64) { s = "(?x)(a#c\\n{1000}){1000}"; }\n    fixed uint8[]:pat = string_bytes(s);\n'
  printf '    Ast:t = raw ast_init(8i64);\n    discard(raw parse_pattern(pat, @t));\n    int64:r = 0i64;\n    int64:n = raw ast_len(t);\n    int64:i = 0i64;\n'
  printf '    while (i < n) decreases n - i {\n        AstNode:x = raw ast_get(t, i);\n'
  printf '        if ((x.kind == AstKind.Repeat) && (x.pos == 5i64)) {\n            AstNode:a = raw ast_get(t, x.a);\n'
  printf '            if ((k == 1i64) || (k == 3i64)) { r = a.pos + a.len; }\n'
  printf '            else { int64:q = x.pos + x.len - 1i64; while (pat[q] != 123u8) decreases q - x.pos { q = q - 1i64; } r = q; }\n        }\n'
  printf '        i = i + 1i64;\n    }\n    drop ast_free(@t);\n    exit r =>! int32;\n};\n\n%s\n' "$FAILSAFE"; } > "$F/p/xmode.npk"
legs "$F/p/xmode.npk" "§1.4 under \`x\`," "\`(?x)(a {1000}){1000}\`: the inner atom's end=" "\`(?x)(a {1000}){1000}\`: its quantifier's \`{\`=a" \
  "\`(?x)(a#c\\n{1000}){1000}\`: the inner atom's end=a a" "\`(?x)(a#c\\n{1000}){1000}\`: its quantifier's \`{\`=a a a"

# ---- §1.5 the language the product is written in, asked of the pin
printf 'mod:pa;\n\n#[derive(Copy)]\nstruct:Step = {\n    int64:node;\n    uint64:prod;\n};\n\nfunc:main = int32(cstring[]:_~argv) {\n    Step:s = Step{ node: 1i64, prod: 1000u64 };\n    int64:c = 1000i64;\n    uint64:p = s.prod * (c =>! uint64);\n    if (p > (NREGEX =>! uint64)) { exit 7i32; }\n    exit 3i32;\n};\n\nfixed int64:NREGEX = 100000i64;\n\n%s\n' "$FAILSAFE" > "$F/p/pa.npk"
legs "$F/p/pa.npk" "§1.5 a \`uint64\` field in a \`Copy\` struct, 1000 x 1000 past 100000 (7)" "run="
printf 'mod:pb;\n\nfixed int64:B = 100000i64;\n\nfunc:main = int32(cstring[]:_~argv) {\n    uint64:b = B => uint64;\n    if (b > 5u64) { exit 4i32; }\n    exit 3i32;\n};\n\n%s\n' "$FAILSAFE" > "$F/p/pb.npk"
legs "$F/p/pb.npk" "§1.5 \`=>\` from \`int64\` to \`uint64\`" "run="
printf 'mod:pc;\n\nfunc:main = int32(cstring[]:_~argv) {\n    int64:c = 4611686018427387904i64;\n    uint64:p = 100000u64 * (c =>! uint64);\n    if (p > 5u64) { exit 4i32; }\n    exit 3i32;\n};\n\n%s\n' "$FAILSAFE" > "$F/p/pc.npk"
legs "$F/p/pc.npk" "§1.5 a \`uint64\` multiply past 2^64 (93, IntOverflow)" "run="
printf 'mod:pd;\n\nfunc:main = int32(cstring[]:_~argv) {\n    int64:end = 1i64;\n    exit end =>! int32;\n};\n\n%s\n' "$FAILSAFE" > "$F/p/pd.npk"
legs "$F/p/pd.npk" "§1.5 a local named \`end\`" "run="

# ---- §1.6 what each module costs a consumer
echo "§1.6 as it stands:"; reach "$F/head/src/hir/build.npk" "$F/head/src/hir/hir.npk" | sed 's/^/  /'
echo "§1.6 after step 4:"; reach "$F/new/src/hir/build.npk" "$F/new/src/hir/hir.npk" | sed 's/^/  /'

# ---- §1.7 the tree checks, before and after, each copy asked with its own harness
echo "§1.7 as it stands:"; tchecks "$F/head"
echo "§1.7 after step 4:"; tchecks "$F/new"

# ---- §1.8 the units in the patched copy, both legs, a capped one under its cap
echo "§1.8 after step 4:"
for u in hir_build_product hir_build_product_fuzz hir_build_product_capped hir_build_product_capped_control hir_build \
         hir_build_not_a_tree hir_build_misnumbered hir_build_classes hir_build_fold pattern_error_text; do
  run4 "$F/new/tests/unit/$u.npk"; done | sed 's/^/  /'

# ---- §1.9 what the patches add: the shapes open or silent at the pin, a plain view, the placeholder
python3 -B - "$T" "$F/head" <<'PY'
import collections, os, re, sys
T, head = sys.argv[1], sys.argv[2]
added, touched = [], set()
for n in range(1, 5):
    path = None
    for line in open(os.path.join(T, "step%d.patch" % n), encoding="utf-8"):
        if line.startswith("+++ b/"):
            path = line[6:].strip(); touched.add(path)
        elif line.startswith("+") and not line.startswith("+++") and path and path.endswith(".npk"):
            added.append(line[1:])
def blank(s):
    s = re.sub(r'"(?:\\.|[^"\\])*"', '""', s)
    return s.split("//", 1)[0]
code = [blank(l) for l in added]
pats = {"comptime": r"\bcomptime\b", "a macro": r"\bmacro\b|#[a-z_]+\s*\(", "a float literal": r"\b\d+\.\d+(f32|f64)?\b",
        "an enum": r"\benum\s*:", "a generic declaration": r"func:[A-Za-z_]+<", "an explicit variant value": r"^\s*[A-Z]\w*\s*=\s*\d",
        "`is_error`": r"\bis_error\b", "`?|` or `?!`": r"\?\||\?!", "`#unreachable`": r"#unreachable", "`#wild_slice`": r"#wild_slice",
        "`give` or `fall`": r"\b(give|fall)\b", "`frac`": r"\bfrac\b", "`move(`": r"\bmove\s*\(", "a plain `uint8[]`": r"(?<!fixed )\buint8\[\]"}
print("§1.9 the patches' %d added `.npk` lines, comments and strings blanked:" % len(added))
print("  " + "; ".join("%s %d" % (k, sum(1 for c in code if re.search(v, c))) for k, v in pats.items()))
ops = collections.Counter()
for c in code:
    for m in re.finditer(r"\bexit\s+([^;]+);", c):
        o = m.group(1).strip()
        ops["an `i32` literal" if re.fullmatch(r"\d+i32", o) else "`%s`" % o] += 1
print("§1.9 their `exit` operands: " + ", ".join("%s %d" % (k, v) for k, v in sorted(ops.items())))
held = sorted(p for p in touched if os.path.exists(os.path.join(head, p)) and "@@DATE022@@" in open(os.path.join(head, p), encoding="utf-8").read())
print("§1.9 the %d file(s) the patches touch that hold `@@DATE022@@` as the tree stands: %s" % (len(held), " ".join(held) or "none"))
PY

# ---- §1.10 the documents audit's RA-3, at the pin: `fold_expr`'s arms and `fold_string_builtin`'s names
TR=$(git -C "$NPK_TREE" show $PIN:src/frontend/type_resolve.npk)
FE=$(printf '%s\n' "$TR" | awk '/^func:fold_expr = /{on=1} on && /^(pub )?func:/ && !/^func:fold_expr = /{exit} on')
echo "§1.10 \`fold_expr\` at $PIN: $(printf '%s\n' "$FE" | grep -o 'kind == ExprKind\.[A-Za-z]*' | sort -u | wc -l) \`ExprKind\` arms; a member access $(printf '%s\n' "$FE" | grep -c 'kind == ExprKind\.ExprMemberAccessExpr'), an index $(printf '%s\n' "$FE" | grep -ciE 'ExprKind\.[A-Za-z]*Index'), an array literal $(printf '%s\n' "$FE" | grep -ciE 'ExprKind\.[A-Za-z]*Array'), a struct literal $(printf '%s\n' "$FE" | grep -ciE 'ExprKind\.[A-Za-z]*Struct')"
echo "§1.10 \`fold_string_builtin\` at $PIN names: $(printf '%s\n' "$TR" | awk '/^func:fold_string_builtin = /{on=1} on && /^(pub )?func:/ && !/^func:fold_string_builtin = /{exit} on' | grep -oE 'string_eq\(name, "[a-z_]+"\)' | grep -oE '"[a-z_]+"' | tr -d '"' | tr '\n' ' ' | sed 's/ $//')"

# ---- §1.11 the documents audit's RA-4: what each rejection fixture imports from `src/`
echo "§1.11 the rejection fixtures, by what they import:"
for f in "$F/head"/tests/rejection/*.npk; do
  grep -oE '^use "[^"]+"' "$f" | sed -E 's|^use "(\.\./)*||; s|"$||' | sort -u | tr '\n' ' '; echo
done | sed 's/ $//' | sort | uniq -c | sed 's/^ */  /'

# ---- §1.12 the cap the pair runs under, and the two leftovers 0.2.1a's verifier named
( ulimit -v $((64 * 1024)); /bin/true ); echo "§1.12 \`/bin/true\` under 64 MiB: exit $?"
echo "§1.12 \`.internal/rx120\` ignored: $(git -C "$REPO" check-ignore -q .internal/rx120 && echo yes || echo no); \`harness/__pycache__/\` ignored: $(git -C "$REPO" check-ignore -q harness/__pycache__/x.pyc && echo yes || echo no)"
echo "§1.12 rx120.sh removes its work directory at line(s) $(grep -nE '^rm -rf "\$work"$' "$REPO/harness/baseline/rx120.sh" | cut -d: -f1 | tr '\n' ' ' | sed 's/ $//') of $(wc -l < "$REPO/harness/baseline/rx120.sh"); a trap: $(grep -c '\btrap\b' "$REPO/harness/baseline/rx120.sh")"
echo "§1.12 check_dated_measurements prunes: $(grep -oE '^_UNDATED_PRUNE_DIRS = .*' "$REPO/harness/treecheck.py")"

rm -rf "${F:?}"

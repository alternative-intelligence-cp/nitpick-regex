# meta/roadmap/0.2/0.2.1_tools/facts.sh -- `0.2.1.md` §1: re-derive what this plan rests on at the pin, in scratch copies
# of the tree, never in it. Sourced after `env.sh`, as block 0b, BEFORE step 1:
#
#     . "$REPO/meta/roadmap/0.2/0.2.1_tools/env.sh"; . "$T/facts.sh"
#
# `head` is the working tree as it stands; `new` is it with steps 1 … 4 applied by GNU `patch` to the copy alone (`git
# apply` run inside this checkout would resolve the paths against the checkout), dated as `apply.py` dates them -- the
# code this plan's patches carry. Probes live in `$F/p`, outside both copies. A check is asked of its OWN tree's harness.
# The copies are removed at the end.
: "${REPO:?}" "${NPKC:?}" "${NPKRT:?}" "${A:?}" "${T:?}"
F=$A/facts
DAY=$(cat "$A/date" 2>/dev/null || date +%F)
fresh() {   # fresh <name> [<step>...]: the working tree as it stands at $F/<name>, then each step's patch
  local d=$1 n; shift
  mkdir -p "$F/$d"
  ( cd "$REPO" && git ls-files -co --exclude-standard -z | xargs -0 tar -cf - ) | tar -xf - -C "$F/$d"
  for n in "$@"; do
    sed "s/@@DATE021@@/$DAY/g" "$T/step$n.patch" | patch -p1 -s --no-backup-if-mismatch -d "$F/$d" \
      || echo "STOP: step$n does not apply to a copy of the tree"
  done
}
legs() {    # legs <src> <prefix> <name>=<argv words>...: build at both legs, then run once per case, each word an argv
            # entry, and print `<prefix> <name>: <exit> at -O0, <exit> after opt -O2` -- or the refusal's codes
  local src=$1 l=$2 o c a e0 e2; shift 2
  o="$F/bin/$(basename "$src" .npk)"; mkdir -p "$F/bin"
  if ! ( cd "$(dirname "$src")" && "$NPKC" "$(basename "$src")" -o "$o.ll" ) > "$o.err" 2>&1; then
    echo "$l: npkc refused -- $(grep -oE '^NITPICK-[A-Z]+-[0-9]+' "$o.err" | tr '\n' ' ' | sed 's/ $//')"; return
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

# ---- §1.2 the names this plan gives, against the pin's keyword file and prelude, and asked of the compiler
KW=$(git -C "$NPK_TREE" show $PIN:src/frontend/keywords.npk)
PRE=$(git -C "$NPK_TREE" show $PIN:src/prelude/prelude.npk)
for n in build Step hir_build resolve_items fold_ranges leaf list held hnode byte_bit push_range STUCK; do
  echo "§1.2 \`$n\`: $(printf '%s' "$KW" | grep -c "\"$n\"") keyword line(s), $(printf '%s' "$PRE" | grep -cE "^pub [a-z]+:$n\b|^pub fixed [a-z0-9]+:$n\b") prelude declaration(s)"
done
{ printf 'mod:build;\n\n#[derive(Copy)]\nstruct:Step = {\n    int64:node;\n    int64:op;\n    int64:mark;\n};\n\n'
  printf 'func:main = int32(cstring[]:_~argv) {\n    Step:s = Step{ node: 3i64, op: 4i64, mark: 0i64 };\n'
  printf '    exit (s.node + s.op + s.mark) =>! int32;\n};\n\n%s\n' "$FAILSAFE"; } > "$F/p/build.npk"
legs "$F/p/build.npk" "§1.2 \`mod:build;\` declaring \`struct:Step\`, exiting 3 + 4 + 0" "run="

# ---- §1.3 the AST the build reads, asked of the tree's own parser: each question a run, its answer the exit
{ printf 'mod:shape;\n\nuse "../head/src/core/core.npk".*;\nuse "../head/src/syntax/syntax.npk".*;\nuse "../head/src/hir/hir.npk".*;\n\n'
  printf 'func:ord = int32(AstKind:k) never fails {\n    int32:n = 99i32;\n    pick (k) {\n'
  i=0; for k in Empty Literal Dot Concat Alternate Repeat Group Flags Anchor WordBoundary Class ClassRange PerlClass PosixClass UnicodeClass ClassOp; do
    printf '        (AstKind.%s) { n = %di32; }%s\n' "$k" $i "$( [ $k = ClassOp ] || echo ,)"; i=$((i+1)); done
  printf '    }\n    pass n;\n};\n\n'
  printf 'func:tree = Ast(string:p) never fails {\n    Ast:t = raw ast_init(8i64);\n    discard(raw parse_pattern(string_bytes(p), @t));\n    pass t;\n};\n\n'
  printf 'func:main = int32(cstring[]:argv) {\n    int64:k = argv.len;\n    int32:r = 0i32;\n'
  printf '    if (k == 1i64) { Ast:t = raw tree("(?i)"); r = raw ord((raw ast_get(t, t.root)).kind); drop ast_free(@t); }\n'
  printf '    if (k == 2i64) { Ast:t = raw tree("a(?i)"); AstNode:c = raw ast_get(t, t.root); AstNode:f = raw ast_get(t, c.a);\n'
  printf '                     r = (raw ord(c.kind)) * 10i32 + (raw ord((raw ast_get(t, f.next)).kind)); drop ast_free(@t); }\n'
  printf '    if (k == 3i64) { Ast:t = raw tree("(?i)|a"); AstNode:c = raw ast_get(t, t.root);\n'
  printf '                     r = (raw ord(c.kind)) * 10i32 + (raw ord((raw ast_get(t, c.a)).kind)); drop ast_free(@t); }\n'
  printf '    if (k == 4i64) { Ast:t = raw tree("((?i))"); AstNode:c = raw ast_get(t, t.root);\n'
  printf '                     r = (raw ord(c.kind)) * 10i32 + (raw ord((raw ast_get(t, c.a)).kind)); drop ast_free(@t); }\n'
  printf '    if (k == 5i64) { Ast:t = raw tree("(?:a)(b)((c))"); AstNode:c = raw ast_get(t, t.root); AstNode:g0 = raw ast_get(t, c.a);\n'
  printf '                     AstNode:g1 = raw ast_get(t, g0.next); AstNode:g2 = raw ast_get(t, g1.next); AstNode:g3 = raw ast_get(t, g2.a);\n'
  printf '                     r = ((g0.b * 64i64 + g1.b * 16i64 + g2.b * 4i64 + g3.b) =>! int32); drop ast_free(@t); }\n'
  printf '    if (k == 6i64) { uint8[]:pat = string_bytes("x(?<year>a)"); Ast:t = raw tree("x(?<year>a)"); AstNode:c = raw ast_get(t, t.root);\n'
  printf '                     AstNode:g = raw ast_get(t, (raw ast_get(t, c.a)).next);\n'
  printf '                     r = (g.c * 10i64) =>! int32; if (pat[g.pos + 3i64] == 121u8) { r = r + 1i32; } drop ast_free(@t); }\n'
  printf '    if (k == 7i64) { Ast:t = raw tree("a*"); AstNode:n = raw ast_get(t, t.root);\n'
  printf '                     if ((n.c == AST_NONE) && (AST_NONE == HIR_NONE)) { r = 1i32; } drop ast_free(@t); }\n'
  printf '    if (k == 8i64) { Ast:t = raw tree("^$\\\\A\\\\z"); AstNode:c = raw ast_get(t, t.root); int64:m = c.a; int64:i = 0i64;\n'
  printf '                     while (i < 4i64) decreases 4i64 - i { AstNode:x = raw ast_get(t, m); r = r * 4i32 + (x.a =>! int32); m = x.next; i = i + 1i64; }\n'
  printf '                     drop ast_free(@t); }\n'
  printf '    if (k == 9i64) { r = ((HIR_TEXT_START * 64i64 + HIR_TEXT_END * 16i64 + HIR_LINE_START * 4i64 + HIR_LINE_END) =>! int32); }\n'
  printf '    if (k == 10i64) { if (AST_FLAG_I == HIR_FLAG_LAZY) { r = 10i32; } if (AST_FLAG_M == HIR_FLAG_BYTE) { r = r + 1i32; } }\n'
  printf '    if (k == 11i64) { Ast:t = raw tree("a"); r = ((raw ast_get(t, t.root)).flags & AST_FLAG_U) =>! int32; drop ast_free(@t); }\n'
  printf '    if (k == 12i64) { Ast:t = raw tree("(?-u)a"); AstNode:c = raw ast_get(t, t.root); AstNode:l = raw ast_get(t, (raw ast_get(t, c.a)).next);\n'
  printf '                     if ((l.flags & AST_FLAG_BYTE) != 0u32) { r = 10i32; } if ((l.flags & AST_FLAG_U) == 0u32) { r = r + 1i32; } drop ast_free(@t); }\n'
  printf '    if (k == 13i64) { Ast:t = raw tree("(?-u)[a]"); AstNode:c = raw ast_get(t, t.root); AstNode:k2 = raw ast_get(t, (raw ast_get(t, c.a)).next);\n'
  printf '                     AstNode:m = raw ast_get(t, k2.a); if ((k2.flags & AST_FLAG_U) == 0u32) { r = 10i32; } if ((m.flags & AST_FLAG_BYTE) == 0u32) { r = r + 1i32; }\n'
  printf '                     drop ast_free(@t); }\n'
  printf '    exit r;\n};\n\n%s\n' "$FAILSAFE"; } > "$F/p/shape.npk"
legs "$F/p/shape.npk" "§1.3" "\`(?i)\`: the root's kind, Flags 7=" "\`a(?i)\`: a Concat, 3, whose second piece is a Flags node, 7=a" \
  "\`(?i)|a\`: an Alternate, 4, whose first alternative is a Flags node=a a" "\`((?i))\`: a Group, 6, whose body is a Flags node=a a a" \
  "\`(?:a)(b)((c))\`: the groups' numbers, base 4: 0 1 2 and the inner 3 is 27=a a a a" \
  "\`x(?<year>a)\`: the name's length times ten, plus 1 when its first byte is at pos + 3=a a a a a" \
  "\`a*\`: an unbounded maximum is AST_NONE, which is HIR_NONE (1)=a a a a a a" \
  "\`^\$\\A\\z\`: the anchors' values, base 4: 0 1 2 3 is 27=a a a a a a a" \
  "the HIR's anchors HIR_TEXT_START … HIR_LINE_END, base 4 (27 is 0 1 2 3)=a a a a a a a a" \
  "AST_FLAG_I is HIR_FLAG_LAZY's value (10), AST_FLAG_M is HIR_FLAG_BYTE's (1)=a a a a a a a a a" \
  "\`a\`: its flags hold AST_FLAG_U, 16, on by default=a a a a a a a a a a" \
  "\`(?-u)a\`: the literal holds AST_FLAG_BYTE (10) and no AST_FLAG_U (1)=a a a a a a a a a a a" \
  "\`(?-u)[a]\`: the class holds no AST_FLAG_U (10), its member no AST_FLAG_BYTE (1)=a a a a a a a a a a a a"

# ---- §1.4 the pending marker, read by the harness as it stands and as step 1 leaves it
python3 -B - "$F/head" "$F/new" <<'PY'
import importlib, sys
for label, root in (("as it stands", sys.argv[1]), ("after step 1", sys.argv[2])):
    sys.path.insert(0, root + "/harness")
    import expect
    importlib.reload(expect)
    for m in ("0.3.4", "0.3", "cycle-0.3.4", "5fbaf4a"):
        e = expect.read("// expect-exit: 0\n// pending-until: %s exit 1\n" % m)
        print("§1.4 %s, `pending-until: %s exit 1`: %s" % (label, m, "read" if e.ok else "UNREADABLE"))
    sys.path.pop(0)
    del sys.modules["expect"]
PY

# ---- §1.5 the dump as it stands writes a stray bit's node and shows nothing of it
for t in head new; do
  { printf 'mod:bit_%s;\n\nuse "../%s/src/core/core.npk".*;\nuse "../%s/src/hir/hir.npk".*;\n\n' "$t" "$t" "$t"
    printf 'func:main = int32(cstring[]:_~argv) {\n    Hir:h = raw hir_init(4i64);\n'
    printf '    int64:x = raw hir_push(@h, HirNode{ kind: HirKind.Anchor, flags: HIR_FLAG_BYTE, a: HIR_LINE_START, b: 0i64, c: 0i64, next: HIR_NONE });\n'
    printf '    drop hir_set_root(@h, x);\n    Bytes:b = raw bytes_init(16i64);\n    drop hir_dump(@h, @b);\n'
    printf '    uint8[]:want = string_bytes("(anchor line-start)");\n    bool:same = (raw bytes_len(@b)) == want.len;\n    int64:i = 0i64;\n'
    printf '    while (same && (i < want.len)) decreases want.len - i {\n        if ((raw bytes_get(@b, i)) != want[i]) { same = false; }\n        i = i + 1i64;\n    }\n'
    printf '    drop hir_free(@h);\n    if (same) { exit 0i32; }\n    exit 10i32;\n};\n\n%s\n' "$FAILSAFE"; } > "$F/p/bit_$t.npk"
done
legs "$F/p/bit_head.npk" "§1.5 a line-start anchor holding HIR_FLAG_BYTE, dumped" "as it stands (0: \`(anchor line-start)\`, the bit unseen)="
legs "$F/p/bit_new.npk" "§1.5 a line-start anchor holding HIR_FLAG_BYTE, dumped" "after step 2 (94: stopped)="

# ---- §1.6 what each module costs a consumer
echo "§1.6 as it stands:"; reach "$F/head/src/hir/hir.npk" | sed 's/^/  /'
echo "§1.6 after step 4:"; reach "$F/new/src/hir/build.npk" "$F/new/src/hir/hir.npk" | sed 's/^/  /'

# ---- §1.7 the tree checks, before and after, each copy asked with its own harness
echo "§1.7 as it stands:"; tchecks "$F/head"
echo "§1.7 after step 4:"; tchecks "$F/new"

# ---- §1.8 the new units in the patched copy, both legs
echo "§1.8 after step 4:"
for u in hir_dump hir_dump_stray_bit hir_build hir_build_not_a_tree hir_build_misnumbered hir_build_classes hir_build_fold; do
  run4 "$F/new/tests/unit/$u.npk"; done | sed 's/^/  /'

# ---- §1.9 what the patches add: the shapes open and silent at the pin, a `#wild_slice`, a `Result` read; the placeholder
python3 -B - "$T" "$F/head" <<'PY'
import os, re, sys
T, head = sys.argv[1], sys.argv[2]
added, touched = [], set()
for n in range(1, 6):
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
        "an enum": r"\benum:", "a generic declaration": r"func:[a-z_]+<", "an explicit variant value": r"^\s*[A-Z]\w*\s*=\s*\d",
        "`is_error`": r"\bis_error\b", "`?|` or `?!`": r"\?\||\?!", "`#unreachable`": r"#unreachable", "`#wild_slice`": r"#wild_slice"}
print("§1.9 the patches' %d added `.npk` lines, comments and strings blanked:" % len(added))
print("  " + "; ".join("%s %d" % (k, sum(1 for c in code if re.search(v, c))) for k, v in pats.items()))
held = sorted(p for p in touched if os.path.exists(os.path.join(head, p)) and "@@DATE021@@" in open(os.path.join(head, p), encoding="utf-8").read())
print("§1.9 the %d file(s) the patches touch that hold `@@DATE021@@` as the tree stands: %s" % (len(held), " ".join(held) or "none"))
PY

# ---- §1.10 what the two pending units name, read from a Unicode database beside the plan's own: Python's
python3 -B - <<'PY'
import unicodedata as u
print("§1.10 Python's unicodedata %s, a secondary reading (cycle 0.3.0 pins the UCD itself):" % u.unidata_version)
for cp in (0x660, 0x200D, 0xA0, 0x3B1, 0x3A9, 0x212A, 0x17F, 0xE9):
    print("  U+%04X %s, %s" % (cp, u.name(chr(cp)), u.category(chr(cp))))
print("  U+212A folds to %r and U+017F to %r (str.casefold)" % (chr(0x212A).casefold(), chr(0x17F).casefold()))
PY
rm -rf "${F:?}"

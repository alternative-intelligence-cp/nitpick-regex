# meta/roadmap/0.2/0.2.4_tools/facts.sh -- `0.2.4.md` §1: re-derive what this plan rests on at the pin, in scratch copies
# of the tree, never in it. Sourced after `env.sh`, as block 0b, BEFORE step 1:
#
#     . "$REPO/meta/roadmap/0.2/0.2.4_tools/env.sh"; . "$T/facts.sh"
#
# `head` is the working tree as it stands; `new` is it with steps 1 … 3 applied by GNU `patch` to the copy alone (`git
# apply` run inside this checkout would resolve the paths against the checkout), dated as `apply.py` dates them -- the
# code this plan's patches carry; `strike` is `new` with RX-235's two-HIR clause struck in `normal.npk`. Probes live in
# `$F/p`, outside every copy. A check is asked of its OWN tree's harness. The compiler's tree is read with `git show`
# alone. The copies are removed at the end. `../0.2.3_tools/facts.sh`, its sections this plan's.
: "${REPO:?}" "${NPKC:?}" "${NPKRT:?}" "${A:?}" "${T:?}"
F=$A/facts
DAY=$(cat "$A/date" 2>/dev/null || date +%F)
fresh() {   # fresh <name> [<step>...]: the working tree as it stands at $F/<name>, then each step's patch
  local d=$1 n; shift
  mkdir -p "$F/$d"
  ( cd "$REPO" && git ls-files -co --exclude-standard -z | xargs -0 tar -cf - ) | tar -xf - -C "$F/$d"
  for n in "$@"; do
    sed "s/@@DATE024@@/$DAY/g" "$T/step$n.patch" | patch -p1 -s --no-backup-if-mismatch -d "$F/$d" \
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
  local src=$1 anchor=$2 e lab x part lo hi r0 r2 zz; shift 2
  zz=$(dirname "$src")/zz_count.npk
  for e in "$@"; do lab=${e%%=*}; x=${e#*=}
    for part in lo hi; do
      if [ "$part" = lo ]; then w="(($x) & 255i64)"; else w="((($x) >> 8i64) & 255i64)"; fi
      python3 -B - "$src" "$zz" "$anchor" "    pass $w =>! int32;" <<'PY'
import re, sys
s = open(sys.argv[1], encoding="utf-8").read()
assert s.count(sys.argv[3]) == 1, "anchor"
s = s.replace(sys.argv[3], sys.argv[4] + "\n" + sys.argv[3])
s = re.sub(r"^mod:[a-z_]+;", "mod:zz_count;", s, count=1, flags=re.M)
open(sys.argv[2], "w", encoding="utf-8").write(s)
PY
      r0=$(legs "$zz" "x" "v=" | sed -E 's/.*: ([0-9]+) at -O0, ([0-9]+) after.*/\1 \2/')
      [ "${r0% *}" = "${r0#* }" ] || echo "LEGS DIFFER: $lab $part $r0"
      eval "$part=${r0% *}"
    done
    echo "  $lab $((hi * 256 + lo))"
  done
  rm -f "${zz:?}"
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
fresh head; fresh new 1 2 3

# ---- §1.2 every name the patches declare -- ENUMERATED from their added `.npk` lines, never chosen -- against the pin's
#      keyword file, prelude and bare-name builtins. The prelude is read whole: a top-level declaration and a member a
#      trait or an impl declares, which 0.2.3's check did not read (its plan verifier's N2). The enumeration proves itself
#      first on a planted control holding every shape a declaration takes and three that are none, and the three lists on
#      a name each holds: `on`, a keyword; `read`, a builtin's; `Ordering`, the prelude's; and `next`, a trait's member.
git -C "$NPK_TREE" show $PIN:src/frontend/keywords.npk > "$F/p/keywords.txt"
git -C "$NPK_TREE" show $PIN:src/prelude/prelude.npk > "$F/p/prelude.txt"
git -C "$NPK_TREE" show $PIN:src/frontend/builtins.npk > "$F/p/builtins.txt"
cat > "$F/p/names.npk.txt" <<'NPK'
mod:zz_mod;
#[derive(Copy)]
struct:ZzStruct = {
    int64:zz_field;
};
fixed int64:ZZ_CONST = 1i64;
func:zz_func = int64(Hir->:zz_ptr, Vec<HirNode>->:zz_vec, fixed uint8[]:zz_view, int64[4]:zz_arr) never fails {
    Bytes:zz_local = raw bytes_init(1i64);
    drop vec_push(@zz_q, Todo{ node: zz_not_a_field, op: 1i64 });
    Vec<int64>:zz_gen = raw vec_init::<int64>(16i64);
    discard(string_bytes("int64:zz_not_in_a_string"));
    pass 0i64;  // int64:zz_not_in_a_comment
};
func:main = int32(cstring[]:_~zz_argv) {
    exit 0i32;
};
NPK
python3 -B - "$T" "$F/p" <<'PY'
import os, re, sys, textwrap
T, P = sys.argv[1], sys.argv[2]
def blank(s):
    s = re.sub(r'"(?:\\.|[^"\\])*"', '""', s)
    return s.split("//", 1)[0]
DECL = re.compile(r"\b(?:func|struct|enum|mod|trait|impl):([A-Za-z_]\w*)")
TYPED = re.compile(r"(?<![\w:])([A-Za-z_]\w*(?:<[^<>()]*>)?(?:\[\d*\])*(?:->)?):(?:_~)?([A-Za-z_]\w*)")
KEYS = {"func", "struct", "enum", "mod", "trait", "impl", "use", "pub"}
def declared(lines):
    got = set()
    for line in lines:
        c = blank(line)
        got.update(m.group(1) for m in DECL.finditer(c))
        got.update(m.group(2) for m in TYPED.finditer(c) if m.group(1) not in KEYS)
    return got
kw, pre, bi = (open(os.path.join(P, f), encoding="utf-8").read().split("\n") for f in ("keywords.txt", "prelude.txt", "builtins.txt"))
def lists(n):
    top = sum(1 for l in pre if re.match(r"^pub [a-z]+:%s\b|^pub fixed [a-z0-9]+:%s\b" % (n, n), l))
    member = sum(1 for l in pre if not re.match(r"^pub ", l) and re.search(r"\b(?:func|struct|enum|trait):%s\b" % n, l))
    return (sum(1 for l in kw if '"%s"' % n in l), top, member, sum(1 for l in bi if '"%s"' % n in l))
planted = sorted(declared(open(os.path.join(P, "names.npk.txt"), encoding="utf-8")))
print("§1.2 the enumeration over its planted control: %d name(s) -- %s" % (len(planted), " ".join(planted)))
for n in ("on", "read", "Ordering", "next"):
    print("§1.2 the lists over `%s`: %d keyword line(s), %d top-level prelude declaration(s), %d prelude member(s), %d builtin line(s)" % ((n,) + lists(n)))
added = []
for k in range(1, 4):
    path = None
    for line in open(os.path.join(T, "step%d.patch" % k), encoding="utf-8"):
        if line.startswith("+++ b/"):
            path = line[6:].strip()
        elif line.startswith("+") and not line.startswith("+++") and path and path.endswith(".npk"):
            added.append(line[1:])
names = sorted(declared(added))
hits = [(n,) + lists(n) for n in names if any(lists(n))]
print("§1.2 the %d name(s) the patches' added `.npk` lines declare, comments and strings blanked: %d on a keyword line, "
      "%d declared at the prelude's top level, %d a prelude member's, %d on a builtin line" % (len(names),
      sum(1 for h in hits if h[1]), sum(1 for h in hits if h[2]), sum(1 for h in hits if h[3]), sum(1 for h in hits if h[4])))
for h in hits:
    print("  HIT `%s`: %d keyword line(s), %d top-level, %d member(s), %d builtin line(s)" % h)
print(textwrap.fill(" ".join(names), width=118, initial_indent="  ", subsequent_indent="  ", break_on_hyphens=False))
PY

# ---- §1.3 the language the units are written in, and the bits' place, asked of the pin
printf 'mod:pa;\n\nuse "../new/src/core/core.npk".*;\nuse "../new/src/hir/hir.npk".*;\n\nfunc:main = int32(cstring[]:_~argv) {\n    Hir:h = raw hir_init(8i64);\n    int64:i = 0i64;\n    while (i < (raw hir_len(h))) decreases (raw hir_len(h)) - i {\n        i = i + 1i64;\n    }\n    drop hir_free(@h);\n    exit 0i32;\n};\n\n%s\n' "$FAILSAFE" > "$F/p/pa.npk"
legs "$F/p/pa.npk" "§1.3 a \`decreases\` measure that calls \`hir_len\`, which is not \`pure\`" "run="
echo "§1.3 the AST's flag bits, \`ast.npk\`: $(grep -oE 'AST_FLAG_[A-Z]+ = [0-9]+u32' "$F/head/src/syntax/ast.npk" | grep -oE '[0-9]+u32' | tr '\n' ' ' | sed 's/ $//'); the computed bits, \`repr.npk\` after step 3: $(grep -oE 'pub fixed uint32:HIR_(PROPS_COMPUTED|CAN_MATCH_EMPTY|IS_ANCHORED_START|IS_ANCHORED_END|IS_ALTERNATION_LITERAL|PROPS|COMPUTED) = [0-9]+u32' "$F/new/src/hir/repr.npk" | sed -E 's/pub fixed uint32://; s/ = /=/' | tr '\n' ' ' | sed 's/ $//')"
python3 -B - "$F/new/src/hir/repr.npk" <<'PY'
import re, sys
s = open(sys.argv[1], encoding="utf-8").read()
v = dict(re.findall(r"pub fixed uint32:(HIR_\w+) = (\d+)u32", s))
four = ["HIR_CAN_MATCH_EMPTY", "HIR_IS_ANCHORED_START", "HIR_IS_ANCHORED_END", "HIR_IS_ALTERNATION_LITERAL"]
print("§1.3 HIR_PROPS is the four's union: %s; HIR_COMPUTED the four's and HIR_PROPS_COMPUTED's: %s; each one bit, none below 65536: %s"
      % (int(v["HIR_PROPS"]) == sum(int(v[k]) for k in four),
         int(v["HIR_COMPUTED"]) == sum(int(v[k]) for k in four) + int(v["HIR_PROPS_COMPUTED"]),
         all(bin(int(v[k])).count("1") == 1 and int(v[k]) >= 65536 for k in four + ["HIR_PROPS_COMPUTED"])))
PY

# ---- §1.4 what each module costs a consumer
echo "§1.4 as it stands:"; reach "$F/head/src/hir/repr.npk" "$F/head/src/hir/dump.npk" "$F/head/src/hir/hir.npk" | sed 's/^/  /'
echo "§1.4 after step 3:"; reach "$F/new/src/hir/repr.npk" "$F/new/src/hir/dump.npk" "$F/new/src/hir/hir.npk" | sed 's/^/  /'

# ---- §1.5 the tree checks, before and after, each copy asked with its own harness
echo "§1.5 as it stands:"; tchecks "$F/head"
echo "§1.5 after step 3:"; tchecks "$F/new"

# ---- §1.6 the units in the patched copy, both legs; and what each verb of `repr.npk` writes, which of them drop the
#      computed bits or stop on a computed tree, and what the facts read
echo "§1.6 after step 3:"
for u in hir_props hir_props_reference hir_props_no_root hir_props_not_in_tree hir_props_frozen_set hir_props_frozen_root \
         hir_props_shared hir_props_not_a_tree hir_normalise hir_normalise_gate hir_build hir_dump hir_unit; do
  run4 "$F/new/tests/unit/$u.npk"; done | sed 's/^/  /'
python3 -B - "$F/new" <<'PY'
import re, sys
root = sys.argv[1]
src = open(root + "/src/hir/repr.npk", encoding="utf-8").read()
READS = ("bytes_len", "bytes_get")
FIELDS = ("nodes", "ranges", "names", "groups", "root")
funcs = {m.group(1): m.group(2) for m in re.finditer(r"^(?:pub )?func:(\w+) = [^\n]*\{\n(.*?)^\};", src, re.S | re.M)}
print("§1.6 the fields of `Hir` each public verb of `repr.npk` writes -- and which drop the computed bits, and which stop on a computed tree:")
for m in re.finditer(r"^pub func:(\w+) = [^\n]*\{\n(.*?)^\};", src, re.S | re.M):
    name, body = m.group(1), m.group(2)
    # a call of a private helper of this file counts as its body
    seen, todo = set(), [body]
    while todo:
        b = todo.pop()
        for c in re.findall(r"\b(\w+)\(", b):
            if c in funcs and c not in seen and not c.startswith("hir_") and c != name:
                seen.add(c); todo.append(funcs[c])
    whole = body + "".join(funcs[c] for c in seen)
    got = {f for v, f in re.findall(r"\b(\w+)\(@\w+\.(nodes|ranges|names|groups)\b", whole) if v not in READS}
    got |= set(re.findall(r"\b\w+\.(root|nodes|ranges|names|groups)(?:\.\w+)* = ", whole))
    if re.search(r"\bHir\{", whole):
        got |= set(FIELDS)
    drops = "drops them" if "& (~HIR_COMPUTED)" in body else ""
    stops = "stops on a computed tree" if "facts_done(h)" in body and name != "hir_props" else ""
    print("  %s: %s%s" % (name, " ".join(f for f in FIELDS if f in got) or "none",
                          "".join("; " + x for x in (drops, stops) if x)))
facts = funcs["facts_of"] + funcs["list_facts"]
print("§1.6 what the facts read, `facts_of` and `list_facts`: " + " ".join(sorted(set(re.findall(r"\b[a-z]\.(kind|a|b|c|next|flags)\b", facts)))))
print("§1.6 and what they do not: HIR_FLAG_BYTE %d, HIR_FLAG_LAZY %d, hir_range %d, ranges %d"
      % tuple(facts.count(x) for x in ("HIR_FLAG_BYTE", "HIR_FLAG_LAZY", "hir_range", "ranges")))
q = funcs["hir_props"]
print("§1.6 `hir_props` stops: " + " | ".join(" ".join(l.split()) for l in q.split("\n") if "vec_oob" in l))
PY

# ---- §1.7 the Gate's counts, read out of the unit as it stands and after step 2: every draw the one it was, and the seventh
#      kind of noise, counted after step 2 and nowhere before
for c in head new; do
  echo "§1.7 hir_normalise_gate's trees, $c:"
  set -- "trees=n" "pairs textually different=pairs" "pairs only normalisation joins=joined" "runs of pieces wrapped=g.wraps" \
    "runs of alternatives wrapped=g.altwraps" "a (?:) or an Empty respelt=g.empties" "a literal as a class or an escape=g.litcls" \
    "a class respelt=g.clsnoise" "a quantifier or an anchor respelt=g.quants" "alternatives swapped=mutants[0]" \
    "a byte bit flipped=mutants[1]" "pieces swapped=mutants[2]" "a laziness flipped=mutants[3]"
  [ "$c" = new ] && set -- "$@" "a repetition's atom in a needless (?:...)=g.repwraps"
  count "$F/$c/tests/unit/hir_normalise_gate.npk" "    if (pairs < PAIRS_FLOOR) { pass 13i32; }" "$@"
done
echo "§1.7 the gate's floors after step 2: $(grep -oE '^fixed int64:[A-Z_]+_FLOOR = [0-9]+i64' "$F/new/tests/unit/hir_normalise_gate.npk" | sed -E 's/fixed int64://; s/ = /=/' | tr '\n' ' ' | sed 's/ $//')"
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
for n in range(1, 4):
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
held = sorted(p for p in touched if os.path.exists(os.path.join(head, p)) and "@@DATE024@@" in open(os.path.join(head, p), encoding="utf-8").read())
print("§1.8 the %d file(s) the patches touch that hold `@@DATE024@@` as the tree stands: %s" % (len(held), " ".join(held) or "none"))
PY

# ---- §1.9 RX-235's two-HIR clause struck, as 0.2.3's §9 strikes it -- a `Literal` copied from the tree read, and a class of
#      one member left a `Literal`, losing the byte bit below 128 -- in a copy of the patched tree: what this plan's units
#      say under it, and the strike's own control, the normaliser's units it reddens
fresh strike 1 2 3
python3 -B - "$F/strike/src/hir/normal.npk" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
a = """            else {
                r = raw push_w(@w, @dead, HirNode{ kind: n.kind, flags: n.flags, a: n.a, b: n.b, c: n.c, next: HIR_NONE });
            }"""
b = """            else {
                uint32:fl = n.flags;
                if ((n.kind == HirKind.Literal) && (n.a < 128i64)) { fl = fl & (~HIR_FLAG_BYTE); }
                r = raw push_w(@w, @dead, HirNode{ kind: n.kind, flags: fl, a: n.a, b: n.b, c: n.c, next: HIR_NONE });
            }"""
c = """        if ((wr.count == first) && (cur.lo == cur.hi)) {
            pass raw push_w(w, dead, HirNode{ kind: HirKind.Literal, flags: n.flags, a: cur.lo => int64,"""
d = """        if ((wr.count == first) && (cur.lo == cur.hi)) {
            uint32:fl = n.flags;
            if (cur.lo < 128u32) { fl = fl & (~HIR_FLAG_BYTE); }
            pass raw push_w(w, dead, HirNode{ kind: HirKind.Literal, flags: fl, a: cur.lo => int64,"""
assert s.count(a) == 1 and s.count(c) == 1, "strike sites"
s = s.replace(a, b).replace(c, d)
open(p, "w", encoding="utf-8").write(s)
import difflib
diff = [l for x, y in ((a, b), (c, d)) for l in difflib.ndiff(x.split("\n"), y.split("\n")) if l[:1] in "+-"]
print("§1.9 the strike: 2 sites in normal.npk, %d lines added and %d removed" % (sum(1 for l in diff if l[0] == "+"),
      sum(1 for l in diff if l[0] == "-")))
PY
for u in hir_props hir_props_reference hir_props_no_root hir_props_not_in_tree hir_props_frozen_set hir_props_frozen_root \
         hir_props_shared hir_props_not_a_tree hir_normalise hir_normalise_gate; do
  run4 "$F/strike/tests/unit/$u.npk"; done | sed 's/^/  /'

# ---- §1.10 the claims steps 1 and 2 date, at the tree as it stands: each line that makes them, outside the records
for kv in "every kind of noise|every kind of noise|each kind of noise" "every bit its nodes hold|every bit its nodes hold|shows every bit" \
          "the writer shows what the arena holds|shows what the arena holds" \
          "they store what a builder hands them|store what a builder hands" "a bit cycle 0.2.4 adds|bit cycle 0\.2\.4 adds|0\.2\.4 says whether"; do
  IFS='|' read -r lab pat <<< "$kv"
  echo "§1.10 \`$lab\`: $(git -C "$REPO" grep -n -i -E "$pat" HEAD -- . ':!meta/roadmap/done' ':!meta/audits' ':!meta/roadmap/0.2/0.2.[0-4]*' \
    | sed -E 's/^HEAD://; s/^([^:]+):([0-9]+):.*/\1:\2/' | tr '\n' ' ' | sed 's/ $//')"
done

# ---- §1.11 every pointer the patches' added lines write, against the documents as the patches leave them: a rule by its
#      declaration in `meta/specs/`, a decision by its heading, a section by its heading, the compiler's decision at the pin
git -C "$NPK_TREE" show $PIN:meta/specs/DECISIONS.md > "$F/p/compiler_decisions.md"
python3 -B - "$T" "$F/new" "$F/p/compiler_decisions.md" "$F/head" <<'PY'
import glob, os, re, sys
T, new, cdec, head = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
added = []
for k in range(1, 4):
    for line in open(os.path.join(T, "step%d.patch" % k), encoding="utf-8"):
        if line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])
text = "".join(added)
specs = {os.path.basename(p): open(p, encoding="utf-8").read() for p in glob.glob(os.path.join(new, "meta/specs/*.md"))}
spec_all = "".join(specs.values())
dec = open(os.path.join(new, "meta/DECISIONS.md"), encoding="utf-8").read()
cd = open(cdec, encoding="utf-8").read()
rules = sorted(set(re.findall(r"(?<![\w-])([HYSCARPUBV]-\d+[a-z]?)\b", text)))
bad = [r for r in rules if not re.search(r"(?:\*\*Rule |Rule |\*\*)%s\b" % re.escape(r), spec_all)]
rx = sorted(set(re.findall(r"\bRX-\d+\b", text)), key=lambda x: int(x[3:]))
badrx = [r for r in rx if not re.search(r"^### %s " % r, dec, re.M)]
ds = sorted(set(re.findall(r"\bD-\d+\b", text)))
badd = [d for d in ds if not re.search(r"^## %s " % d, cd, re.M)]
secs = sorted(set(re.findall(r"`([A-Z]+\.md)` §(\d+)", text)))
bads = [(f, n) for f, n in secs if f not in specs or not re.search(r"^## %s\. " % n, specs[f], re.M)]
# the rules and decisions the patches themselves add are counted, not named: this plan's file never writes them out
spec_head = "".join(open(p, encoding="utf-8").read() for p in glob.glob(os.path.join(head, "meta/specs/*.md")))
dec_head = open(os.path.join(head, "meta/DECISIONS.md"), encoding="utf-8").read()
old_rules = [r for r in rules if re.search(r"(?:\*\*Rule |Rule |\*\*)%s\b" % re.escape(r), spec_head)]
old_rx = [r for r in rx if re.search(r"^### %s " % r, dec_head, re.M)]
print("§1.11 rules: %d named -- %d declared at this plan's commit, %s, and %d the patches declare; undeclared after them: %s"
      % (len(rules), len(old_rules), " ".join(old_rules), len(rules) - len(old_rules), " ".join(bad) or "none"))
print("§1.11 decisions: %d named -- %d headings at this plan's commit, %s, and %d the patches add; no heading after them: %s"
      % (len(rx), len(old_rx), " ".join(old_rx), len(rx) - len(old_rx), " ".join(badrx) or "none"))
print("§1.11 the compiler's decisions at the pin: %s; no heading: %s" % (" ".join(ds), " ".join(badd) or "none"))
print("§1.11 sections: %s; no heading: %s" % (" ".join("%s §%s" % s for s in secs), " ".join("%s §%s" % s for s in bads) or "none"))
PY
echo "§1.11 D-227 at the pin: $(grep -E '^## D-227 ' "$F/p/compiler_decisions.md" | cut -c1-110)"

# ---- §1.12 what the drafts wrote and replaced (0.2.3's record, "To the planner of 0.2.4": a comment its drafts replaced
#      passed every gate), and what the fix round replaced: each replaced phrase, in the lines the patches add -- none
#      survives. The query's obligation line's "i is reached from h.root" is not among them: the fix round restored it.
python3 -B - "$T" <<'PY'
import os, sys
T = sys.argv[1]
added = []
for k in range(1, 4):
    for line in open(os.path.join(T, "step%d.patch" % k), encoding="utf-8"):
        if line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])
gone = ["the table was written first", "are each red here (the plan", "the shapes the build never makes among them",
        "regex-syntax", "change no node of the", "but the seventh", "still stops the dump", "an arena that is not a tree stops it",
        "each kind of noise applied at least this often",
        # and the fix round's, at the plan verifier's PASS: the reference's and RX-238's account of the mutants
        "one rule of H-17 broken at a time", "Each of H-17's rules broken alone", "twenty-five rows"]
text = "".join(added)
print("§1.12 the drafts' replaced words, in the patches' %d added lines: " % len(added) + "; ".join("%s %d" % (g, text.count(g)) for g in gone))
PY

rm -rf "${F:?}"

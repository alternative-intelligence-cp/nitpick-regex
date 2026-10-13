# meta/roadmap/0.2/0.2.5_tools/facts.sh -- `0.2.5.md` §1: re-derive what this plan rests on at the pin, in scratch copies
# of the tree, never in it. Sourced after `env.sh`, as block 0b, BEFORE step 1:
#
#     . "$REPO/meta/roadmap/0.2/0.2.5_tools/env.sh"; . "$T/facts.sh"
#
# `head` is the working tree as it stands; `new` is it with steps 1 and 2 applied by GNU `patch` to the copy alone (`git
# apply` run inside this checkout would resolve the paths against the checkout), dated as `apply.py` dates them -- the
# code this plan's patches carry; `strike` is `new` with RX-235's two-HIR clause struck in `normal.npk`. Probes live in
# `$F/p`, outside every copy. A check is asked of its OWN tree's harness. The compiler's tree is read with `git show`
# alone. The copies are removed at the end. `../0.2.4_tools/facts.sh`, its sections this plan's.
: "${REPO:?}" "${NPKC:?}" "${NPKRT:?}" "${A:?}" "${T:?}"
F=$A/facts
DAY=$(cat "$A/date" 2>/dev/null || date +%F)
fresh() {   # fresh <name> [<step>...]: the working tree as it stands at $F/<name>, then each step's patch
  local d=$1 n; shift
  mkdir -p "$F/$d"
  ( cd "$REPO" && git ls-files -co --exclude-standard -z | xargs -0 tar -cf - ) | tar -xf - -C "$F/$d"
  for n in "$@"; do
    sed "s/@@DATE025@@/$DAY/g" "$T/step$n.patch" | patch -p1 -s --no-backup-if-mismatch -d "$F/$d" \
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
fresh head; fresh new 1 2

# ---- §1.2 every name the patches declare -- ENUMERATED from their added `.npk` lines, never chosen -- against the pin's
#      keyword file, prelude and bare-name builtins. The prelude is read whole: a top-level declaration and a member a
#      trait or an impl declares (0.2.3's plan verifier's N2). The enumeration proves itself first on a planted control
#      holding every shape a declaration takes and three that are none, and the lists on a name each holds: `on` and
#      `limit`, keywords -- `limit` the name a draft gave a parameter, refused `NITPICK-PARSE-002` (§1.3); `read`, a
#      builtin's; `Ordering`, the prelude's; and `next`, a trait's member.
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
for n in ("on", "limit", "read", "Ordering", "next"):
    print("§1.2 the lists over `%s`: %d keyword line(s), %d top-level prelude declaration(s), %d prelude member(s), %d builtin line(s)" % ((n,) + lists(n)))
added = []
for k in range(1, 3):
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

# ---- §1.3 the language the patches are written in, asked of the pin: `limit` as a parameter's name, which a draft wrote;
#      and `Literal`'s size, measured as the exit code, never derived
printf 'mod:pl;\n\nfunc:f = int64(int64:limit) never fails {\n    pass limit;\n};\n\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n\n%s\n' "$FAILSAFE" > "$F/p/pl.npk"
legs "$F/p/pl.npk" "§1.3 \`limit\` as a parameter's name" "run="
printf 'mod:ps;\n\nuse "../new/src/hir/hir.npk".*;\n\nfunc:main = int32(cstring[]:_~argv) {\n    exit #size_of<Literal>() =>! int32;\n};\n\n%s\n' "$FAILSAFE" > "$F/p/ps.npk"
legs "$F/p/ps.npk" "§1.3 \`#size_of<Literal>()\`, the exit" "run="

# ---- §1.4 what each module costs a consumer
echo "§1.4 as it stands:"; reach "$F/head/src/hir/repr.npk" "$F/head/src/hir/dump.npk" "$F/head/src/hir/hir.npk" | sed 's/^/  /'
echo "§1.4 after step 2:"; reach "$F/new/src/hir/repr.npk" "$F/new/src/hir/dump.npk" "$F/new/src/hir/hir.npk" | sed 's/^/  /'

# ---- §1.5 the tree checks, before and after, each copy asked with its own harness
echo "§1.5 as it stands:"; tchecks "$F/head"
echo "§1.5 after step 2:"; tchecks "$F/new"

# ---- §1.6 the units in the patched copy, both legs; who writes the literals' two fields; what the extraction reads of
#      the facts, and what it asks first
echo "§1.6 after step 2:"
for u in hir_literal hir_literal_reference hir_literal_fuzz hir_literal_no_root hir_literal_not_extracted hir_literal_frozen \
         hir_literal_oracle hir_dump hir_props hir_props_reference hir_normalise hir_normalise_gate hir_build hir_unit; do
  run4 "$F/new/tests/unit/$u.npk"; done | sed 's/^/  /'
python3 -B - "$F/new" <<'PY'
import re, sys
root = sys.argv[1]
src = open(root + "/src/hir/repr.npk", encoding="utf-8").read()
funcs = {m.group(1): m.group(2) for m in re.finditer(r"^(?:pub )?func:(\w+) = [^\n]*\{\n(.*?)^\};", src, re.S | re.M)}
pub = [m.group(1) for m in re.finditer(r"^pub func:(\w+) = ", src, re.M)]
def writes(body):
    got = set(re.findall(r"\b\w+\(@\w+\.(literals|lits)\b", body))
    if re.search(r"\bHir\{", body):
        got |= {"literals", "lits"}
    return got
direct = {n: writes(b) for n, b in funcs.items()}
print("§1.6 the functions of `repr.npk` that write `Hir.literals` or `Hir.lits` themselves: " +
      "; ".join("%s %s" % (n, " ".join(sorted(w))) for n, w in sorted(direct.items()) if w))
def reach(n, seen):
    for c in re.findall(r"\b(\w+)\(", funcs[n]):
        if c in funcs and c not in seen:
            seen.add(c); reach(c, seen)
    return seen
print("§1.6 the public verbs that reach one: " + " ".join(n for n in pub if direct.get(n) or any(direct.get(c) for c in reach(n, set()))))
ext = "".join(funcs[n] for n in ("extract_literals", "first_bytes", "prefix_bytes", "shared_start", "plain_put",
                                 "plain_common", "plain_len", "inner_literal", "add_leads", "add_span", "cp_len", "cp_byte"))
print("§1.6 the facts the extraction reads: " + ", ".join("%s %d" % (b, ext.count(b)) for b in
      ("HIR_CAN_MATCH_EMPTY", "HIR_IS_ALTERNATION_LITERAL", "HIR_IS_ANCHORED_START", "HIR_IS_ANCHORED_END", "HIR_PROPS")))
first = [l.strip() for l in funcs["extract_literals"].split("\n") if l.strip()][0]
print("§1.6 the extraction's first statement: " + first)
print("§1.6 `hir_literals`: " + " | ".join(" ".join(l.split()) for l in funcs["hir_literals"].split("\n") if l.strip()))
PY

# ---- §1.7 the fuzz's counts, read out of the unit after step 2: the strings drawn, and the patterns with each role
echo "§1.7 hir_literal_fuzz, after step 2:"
count "$F/new/tests/unit/hir_literal_fuzz.npk" "    if (g.strings < STRINGS_FLOOR) { pass 17i32; }" \
  "strings drawn and held=g.strings" "patterns with a prefix=g.prefix" "with a whole match=g.whole" \
  "with a first-byte set=g.first" "with anywhere=g.anywhere" "with an inner literal=g.inner"
echo "§1.7 its floors and sizes: $(grep -oE '^fixed int64:[A-Z_]+ = [0-9]+i64' "$F/new/tests/unit/hir_literal_fuzz.npk" | sed -E 's/fixed int64://; s/ = /=/' | tr '\n' ' ' | sed 's/ $//')"

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
for n in range(1, 3):
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
held = sorted(p for p in touched if os.path.exists(os.path.join(head, p)) and "@@DATE025@@" in open(os.path.join(head, p), encoding="utf-8").read())
print("§1.8 the %d file(s) the patches touch that hold `@@DATE025@@` as the tree stands: %s" % (len(held), " ".join(held) or "none"))
bi = sorted(set(re.findall(r'string_eq\(name, "([a-z_]+)"\)', open(os.path.join(P, "builtins.txt"), encoding="utf-8").read())))
named = collections.Counter()
called = collections.Counter()
for c in code:
    for n in bi:
        for m in re.finditer(r"(?<![\w.])%s\b(\s*(?:<[^<>]*>)?\s*\()?" % n, c):
            named[n] += 1
            if m.group(1):
                called[n] += 1
print("§1.8 the pin's %d bare-name builtins the added lines name: %s" % (len(bi), "; ".join("`%s` %d, called %d" % (n, named[n], called[n]) for n in sorted(named)) or "none"))
files = [set(l[6:].strip() for l in open(os.path.join(T, "step%d.patch" % n), encoding="utf-8") if l.startswith("+++ b/")) for n in (1, 2)]
print("§1.8 the files step 1 touches %d, step 2 %d; the files both touch: %s" % (len(files[0]), len(files[1]),
      " ".join(sorted(files[0] & files[1])) or "none"))
PY

# ---- §1.9 RX-235's two-HIR clause struck, as 0.2.3's §9 strikes it -- a `Literal` copied from the tree read, and a class of
#      one member left a `Literal`, losing the byte bit below 128 -- in a copy of the patched tree: what this plan's units
#      say under it, and the strike's own control, the normaliser's units it reddens
fresh strike 1 2
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
for u in hir_literal hir_literal_reference hir_literal_fuzz hir_literal_no_root hir_literal_not_extracted hir_literal_frozen \
         hir_literal_oracle hir_normalise hir_normalise_gate; do
  run4 "$F/strike/tests/unit/$u.npk"; done | sed 's/^/  /'

# ---- §1.10 the claims step 1 dates, at the tree as it stands: each line that makes them, outside the records
for kv in "holds no literals until cycle 0.2.5|holds no .literals. until cycle 0\.2\.5" "Literal is cycle 0.2.5's / will|Literal. is cycle 0\.2\.5|Literal. will at cycle 0\.2\.5" \
          "in total|literal text extracted in total" "writes a HIR as one line of text|writes a HIR as one$|hir_dump. writes a HIR as one" \
          "Appends the tree under|Appends the tree under" "Appends the nodes text describes|Appends the nodes .text. describes" \
          "A node, a range and a group own nothing|A node, a range and a group own nothing" "FRESH IS THREE COUNTS|FRESH IS THREE COUNTS" \
          "writes the tree under the root as one line|writes the tree under the root as one line"; do
  IFS='|' read -r lab pat <<< "$kv"
  echo "§1.10 \`$lab\`: $(git -C "$REPO" grep -n -E "$pat" HEAD -- . ':!meta/roadmap/done' ':!meta/audits' ':!meta/roadmap/0.2/0.2.[0-5]*' ':!meta/DECISIONS.md' \
    | sed -E 's/^HEAD://; s/^([^:]+):([0-9]+):.*/\1:\2/' | tr '\n' ' ' | sed 's/ $//')"
done

# ---- §1.11 every pointer the patches' added lines write, against the documents as the patches leave them: a rule by its
#      declaration in `meta/specs/`, a decision by its heading, a section by its heading, the compiler's decision at the pin
git -C "$NPK_TREE" show $PIN:meta/specs/DECISIONS.md > "$F/p/compiler_decisions.md"
python3 -B - "$T" "$F/new" "$F/p/compiler_decisions.md" "$F/head" <<'PY'
import glob, os, re, sys
T, new, cdec, head = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
added = []
for k in range(1, 3):
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
# and no text of this plan but its patches names a decision the patches add -- 0.2.4's plan verification, its finding 3: its
# facts.sh named one before the PASS -- read for any number past the log's last heading
python3 -B - "$T" "$REPO/meta/roadmap/0.2/0.2.5.md" "$REPO/meta/DECISIONS.md" <<'PY'
import glob, os, re, sys
T, plan, dec = sys.argv[1], sys.argv[2], sys.argv[3]
top = max(int(n) for n in re.findall(r"^### RX-(\d+)", open(dec, encoding="utf-8").read(), re.M))
files = [plan] + sorted(p for p in glob.glob(os.path.join(T, "*")) if not os.path.basename(p).startswith("step"))
named = {}
for p in files:
    for n in re.findall(r"\bRX-(\d+)\b", open(p, encoding="utf-8").read()):
        if int(n) > top:
            named.setdefault(os.path.basename(p), set()).add(n)
print("§1.11 the decisions past RX-%d that a text of this plan but its patches names: %s" % (top,
      "; ".join("%s %s" % (k, " ".join(sorted(v))) for k, v in sorted(named.items())) or "none"))
PY

# ---- §1.12 what the drafts wrote and replaced (0.2.3's record: a comment its drafts replaced passed every gate), each
#      replaced phrase in the lines the patches add -- none survives
python3 -B - "$T" <<'PY'
import os, sys
T = sys.argv[1]
added = []
for k in range(1, 3):
    for line in open(os.path.join(T, "step%d.patch" % k), encoding="utf-8"):
        if line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])
gone = ["int64:limit", "2047i64", "65535i64", "U+07FF and U+FFFF", "(n.b != 1i64) || (n.c != 1i64)",
        "minimum and maximum are 1", "minimum and maximum are both 1", "the prefix's own when it is the prefix",
        "six entries", "asked for no facts", "where it stands", "every term of the query", "drop vec_oob(h.root)",
        "by its place", "through `whole`", "(concat (literal 97) (literal 98))\"), @h)) != HIR_NONE) { exit 1i32; }",
        # and the measured texts' and the fuzz header's first words on what the reference and the fuzz hold
        "of one to four, alternations", "every quantifier's shape", "`b`, `c` and `é`",
        # and plan verification 1's fix: the counts and words it replaced, and its own drafts' (§8)
        "every facet of H-19's words", "seventy rows", "twenty-three rows", "everywhere 13", "20 … 26",
        "a vector's first capacity", "one step to spare", "an edge's form that adds an empty span",
        "mutated once by the plan's operator sweep", "node 6"]
text = "".join(added)
print("§1.12 the drafts' replaced words, in the patches' %d added lines: " % len(added) + "; ".join("%s %d" % (g, text.count(g)) for g in gone))
PY

# ---- §1.13 the mutant table's rows, by the rule each breaks: H-19's facets, H-20's terms, and the pending test's hook
python3 -B - "$T/mutants.tsv" <<'PY'
import collections, sys
rows = [l.split("\t")[1] for l in open(sys.argv[1], encoding="utf-8") if l.strip() and not l.startswith("#")]
def rule(n):
    if n.split("-")[0] in ("enc", "class", "span", "first", "prefix", "whole", "alt", "inner"):
        return "H-19"
    if n.split("-")[0] in ("query", "extract", "count", "free", "dump", "read"):
        return "H-20"
    return "the hook"
c = collections.Counter(rule(n) for n in rows)
print("§1.13 the mutant table: %d rows -- H-19 %d, H-20 %d, the pending test's hook %d; names each once: %s"
      % (len(rows), c["H-19"], c["H-20"], c["the hook"], len(set(rows)) == len(rows)))
PY

rm -rf "${F:?}"

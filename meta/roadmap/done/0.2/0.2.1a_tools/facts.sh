# meta/roadmap/0.2/0.2.1a_tools/facts.sh -- `0.2.1a.md` §1: re-derive what this plan rests on, at both pins, in scratch
# copies of the tree, never in it. Sourced after `env.sh`, as block 0b, BEFORE step 1:
#
#     . "$REPO/meta/roadmap/0.2/0.2.1a_tools/env.sh"; . "$T/facts.sh"
#
# `head` is the working tree as it stands; `s1` is it with step 1 applied and `s2` with steps 1 and 2, each by GNU
# `patch` into the copy alone (`git apply` run inside this checkout would resolve the paths against the checkout), dated
# as `apply.py` dates them. Probes live in `$F/p`, outside every copy; each program is built and run at the pin it is
# asked of, under that pin's LLVM (`leg`). A check is asked of its OWN tree's harness. The unchanged tree's two
# censuses are kept as `$A/head_old.tsv` and `$A/head_new.tsv` for block 1; everything else here is removed at the end.
: "${REPO:?}" "${A:?}" "${T:?}" "${PIN:?}" "${OLD:?}"
F=$A/facts
DAY=$(cat "$A/date" 2>/dev/null || date +%F)
fresh() {   # fresh <name> [<step>...]: the working tree as it stands at $F/<name>, then each step's patch
  local d=$1 n; shift
  mkdir -p "$F/$d"
  ( cd "$REPO" && git ls-files -co --exclude-standard -z | xargs -0 tar -cf - ) | tar -xf - -C "$F/$d"
  for n in "$@"; do
    sed "s/@@DATE021A@@/$DAY/g" "$T/step$n.patch" | patch -p1 -s --no-backup-if-mismatch -d "$F/$d" \
      || echo "STOP: step$n does not apply to a copy of the tree"
  done
}
legs() {    # legs <pin> <src> <label>: build at <pin> under its LLVM, run at -O0 and through `opt -O2`, and print
            # `<label>: <exit> at -O0, <exit> after opt -O2` -- or the refusal's codes
  local pin=$1 src=$2 l=$3 o
  o="$F/bin/$pin.$(basename "$src" .npk)"; mkdir -p "$F/bin"
  ( leg "$pin"
    if ! ( cd "$(dirname "$src")" && "$NPKC" "$(basename "$src")" -o "$o.ll" ) > "$o.err" 2>&1; then
      echo "$l: npkc refused -- $(grep -oE '^NITPICK-[A-Z]+-[0-9]+ [^ ]+' "$o.err" | sed -E 's| ([^ ]*/)?([^/ ]+:[0-9]+:[0-9]+):$| \2|' \
        | tr '\n' ' ' | sed 's/ $//')"; exit 0
    fi
    llc -O0 -filetype=obj -relocation-model=static "$o.ll" -o "$o.o" && ld.lld -static "$o.o" "$NPKRT" -o "$o.x0" \
      && opt -O2 -S "$o.ll" -o "$o.2.ll" && llc -O2 -filetype=obj -relocation-model=static "$o.2.ll" -o "$o.2.o" \
      && ld.lld -static "$o.2.o" "$NPKRT" -o "$o.x2"
    "$o.x0" > /dev/null 2>&1; e0=$?; "$o.x2" > /dev/null 2>&1; e2=$?
    echo "$l: $e0 at -O0, $e2 after opt -O2" )
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
probe() {   # probe <name> <body of main>, and any declarations before it on stdin: a program in $F/p
  { printf 'mod:%s;\n\n' "$1"; cat; printf 'func:main = int32(cstring[]:_~argv) {\n%s\n};\n\n%s\n' "$2" "$FAILSAFE"; } > "$F/p/$1.npk"
}

rm -rf "${F:?}"; mkdir -p "$F/p"
fresh head; fresh s1 1; fresh s2 1 2

# ---- §1.2 the unchanged tree at the new pin, its LLVM rows moved: the manifest alone, then both
cp -r "$F/head" "$F/llvm1"; sed -i 's/^llvm          = "20.1.2"$/llvm          = "20.1.8"/' "$F/llvm1/nitpick.toml"
echo "§1.2 the tree's manifest at 20.1.8, the self-check's at 20.1.2, the self-check at $PIN:"; cases $PIN "$F/llvm1" | sed 's/^/  /'
cp -r "$F/llvm1" "$F/llvm2"; sed -i 's/^llvm          = "20.1.2"$/llvm          = "20.1.8"/' "$F/llvm2/harness/selfcheck.py"
( leg $PIN; cd "$F/llvm2" && python3 -B harness/run.py ) > "$A/llvm2.log" 2>&1
python3 - "$A/llvm2.log" <<'PY'
import collections, re, sys
t = open(sys.argv[1], errors="replace").read()
fails = re.findall(r"^FAIL  ([a-z-]+)/(\S+?): (.*)$", t, re.M)
by = collections.Counter(s for s, p, r in fails)
seven = {p for s, p, r in fails if "NITPICK-TYPE-007" in r}
print("§1.2 both rows at 20.1.8, the full run at the new pin: " + re.search(r"^\d+/\d+ unit\(s\) passed", t, re.M).group(0))
print("  %d failure(s): %s" % (len(fails), ", ".join("%s %d" % kv for kv in sorted(by.items()))))
print("  %d of them NITPICK-TYPE-007, over %d file(s); the rest: %d `PENDING.txt` line(s), %d `RESIDUE.txt` entr(ies)"
      % (sum(1 for s, p, r in fails if "NITPICK-TYPE-007" in r), len(seven),
         by["pending-list"], by["baseline"]))
print("  the self-check: " + re.search(r"\d+ live, \d+ pending, \d+ cases", t).group(0))
PY

# ---- §1.3 landing 103's readers, enumerated: every file as a root at both pins -- the checkout itself, as it stands
echo "§1.3 the unchanged tree, every .npk a root:"
census $OLD "$REPO" head_old | sed 's/^/  /'
census $PIN "$REPO" head_new | sed 's/^/  /'
python3 -B "$T/census.py" sites "$A/head_new.tsv" NITPICK-TYPE-007 | sed 's/^/  /'
echo "§1.3 each file at $OLD against $PIN, NITPICK-TYPE-007 left out:"
python3 -B "$T/census.py" compare "$A/head_old.tsv" "$A/head_new.tsv" NITPICK-TYPE-007 | sed 's/^/  /' | cut -c1-150

# ---- §1.4 the spellings, asked of both compilers
probe p_local '    string:v = "abc";
    fixed uint8[]:bs = string_bytes(v);
    exit (bs.len =>! int32);' < /dev/null
probe p_param '    string:v = "abcd";
    exit ((raw count(string_bytes(v))) =>! int32);' <<'NPK'
func:count = int64(fixed uint8[]:pat) never fails {
    pass pat.len;
};

NPK
probe p_field '    string:v = "abcde";
    Cur:c = raw cur_init(string_bytes(v));
    c.pos = c.pos + 1i64;
    exit ((c.src.len + c.pos) =>! int32);' <<'NPK'
struct:Cur = {
    sealed fixed uint8[]:src;
    sealed int64:pos;
};

func:cur_init = Cur(fixed uint8[]:pat) never fails {
    pass Cur{ src: pat, pos: 0i64 };
};

NPK
probe p_grouped '    string:v = "abc";
    (fixed uint8[]):bs = string_bytes(v);
    bs = string_bytes("abcdef");
    exit (bs.len =>! int32);' < /dev/null
probe p_return '    string:s = string_concat("abcaa", "bXbb");
    fixed uint8[]:v = string_bytes(s);
    fixed uint8[]:sub = raw subview(v, 3i64, 5i64);
    exit (sub.len =>! int32);' <<'NPK'
func:subview = fixed uint8[](fixed uint8[]:src, int64:lo, int64:hi) never fails {
    pass src[lo...hi];
};

NPK
probe p_return_plain '    string:s = string_concat("abcaa", "bXbb");
    fixed uint8[]:v = string_bytes(s);
    uint8[]:sub = raw subview(v, 3i64, 5i64);
    exit (sub.len =>! int32);' <<'NPK'
func:subview = fixed uint8[](fixed uint8[]:src, int64:lo, int64:hi) never fails {
    pass src[lo...hi];
};

NPK
for pr in "p_local:a fixed local of the bridge's view (3)" "p_param:a fixed parameter handed one (4)" \
    "p_field:a sealed fixed field, filled by its constructor (6)" "p_grouped:the grouped plain binding, re-pointed (6)" \
    "p_return:a fixed view returned (2)" "p_return_plain:that return bound into a plain local"; do
  for p in $OLD $PIN; do legs $p "$F/p/${pr%%:*}.npk" "§1.4 ${pr#*:} at $p"; done
done

# ---- §1.5 the re-spelling's extent, and the six slots no read-only view reaches
python3 - "$F/head" "$F/s1" "$F/s2" "$REPO" <<'PY'
import os, re, subprocess, sys
head, s1, s2 = sys.argv[1:4]
fs = subprocess.run(["git", "-C", sys.argv[4], "ls-files", "*.npk"], capture_output=True, text=True).stdout.split()
def code(l):
    return "" if l.lstrip().startswith("//") else l.split("//", 1)[0]
def plain(t, f):
    return [(i + 1, l) for i, l in enumerate(open(os.path.join(t, f), encoding="utf-8").read().split("\n"))
            if re.search(r"(?<!fixed )\buint8\[\]", code(l))]
slots = files = 0
for f in fs:
    a = open(os.path.join(head, f), encoding="utf-8").read().split("\n")
    b = open(os.path.join(s1, f), encoding="utf-8").read().split("\n")
    n = sum(len(re.findall(r"(?<!fixed )\buint8\[\]:", code(x))) - len(re.findall(r"(?<!fixed )\buint8\[\]:", code(y)))
            for x, y in zip(a, b)) if len(a) == len(b) else None
    if n is None:
        n = len(re.findall(r"(?<!fixed )\buint8\[\]:", "\n".join(code(x) for x in a))) - \
            len(re.findall(r"(?<!fixed )\buint8\[\]:", "\n".join(code(y) for y in b)))
    if n:
        slots += n; files += 1
print("§1.5 step 1 re-spells %d slot(s) `fixed uint8[]` in %d file(s)" % (slots, files))
for t, lab in ((head, "as it stands"), (s1, "after step 1"), (s2, "after step 2")):
    left = [(f, n) for f in fs for n, l in plain(t, f)]
    by = {}
    for f, n in left:
        by[f] = by.get(f, 0) + 1
    print("§1.5 code lines holding a plain `uint8[]`, %s: %d%s" % (lab, len(left),
          "" if (len(by) > 3 or not by) else " -- " + ", ".join("%s %d" % kv for kv in sorted(by.items()))))
PY
for h in "tests/unit/cursor_unit.npk:func:walk = int32(fixed uint8[]:pat)" \
         "tests/unit/parse_encoding.npk:func:bad = bool(fixed uint8[]:pat," \
         "tests/unit/parse_encoding.npk:func:good = bool(fixed uint8[]:pat," \
         "tests/unit/regex_escape.npk:func:escapes_bytes = bool(fixed uint8[]:text, fixed uint8[]:want)" \
         "tests/unit/regex_escape.npk:func:ill_formed = bool(fixed uint8[]:text,"; do
  f=${h%%:*}; t=${h#*:}; rm -rf "$F/one"; cp -r "$F/s1" "$F/one"
  python3 - "$F/one/$f" "$t" <<'PY'
import sys
p, t = sys.argv[1], sys.argv[2]
s = open(p, encoding="utf-8").read()
assert s.count(t) == 1, t
open(p, "w", encoding="utf-8").write(s.replace(t, t.replace("fixed uint8[]:", "uint8[]:")))
PY
  echo "§1.5 $(basename "$f")'s \`${t#func:}\` plain again: $(codes $PIN "$F/one/$f" | sed 's/^[^:]* at [0-9a-f]*:* *//')"
done

# ---- §1.6 D-332's count over the unchanged tree, at both pins
echo "§1.6 D-332's count, the unchanged tree:"; python3 -B "$T/sitecount.py" "$REPO" $OLD $PIN | sed 's/^/  /'

# ---- §1.7 B-4e's re-read
echo "§1.7 the files B-4e names, $OLD to $PIN:"
git -C "$NPK_TREE" diff --stat $OLD $PIN -- src/frontend/lexer.npk src/frontend/escapes.npk src/frontend/parse_decl.npk \
  meta/specs/LEXICAL_REFERENCE.md src/frontend/numeric.npk src/frontend/num_width.npk | sed 's/^/ /'
for fn in parse_decl.npk:p_parse_import numeric.npk:num_scan; do for p in $OLD $PIN; do
  echo "§1.7 ${fn#*:} at $p: $(git -C "$NPK_TREE" show $p:src/frontend/${fn%%:*} | awk "/^(pub )?func:${fn#*:} /,/^};/" | sha256sum | cut -c1-16)"
done; done
printf 'mod:p_tail;\n\nfunc:main = int32(cstring[]:_~argv) {\n    flt64:x = 1.5e+r"a";\n    exit 0i32;\n};\n\n%s\n' "$FAILSAFE" > "$F/p/p_tail.npk"
codes $OLD "$F/p/p_tail.npk" | sed 's/^/§1.7 `1.5e+r"a"`: /'; codes $PIN "$F/p/p_tail.npk" | sed 's/^/§1.7 `1.5e+r"a"`: /'
python3 - "$F/p/p_tail.npk" "$REPO/harness" <<'PY'
import sys
sys.path.insert(0, sys.argv[2])
import lexical
t = lexical.read(sys.argv[1])
print("§1.7 `1.5e+r\"a\"` as harness/lexical.py reads it: " + ", ".join("%s %s" % (k, t[s:e]) for k, s, e in lexical.spans(t) if k != "comment"))
PY

# ---- §1.8 rx120 at the new pin, in the checkout's position
echo "§1.8 harness/baseline/rx120.sh at $PIN, as the tree stands:"
( leg $PIN; cd "$REPO" && harness/baseline/rx120.sh ) | grep -E '^(ok|FAIL|SKIPPED|rx120: (pin|control|every))' | sed 's/^/  /' | cut -c1-110

# ---- §1.8 and the two rows of BUILD.md §7's reserved-word table that name `5fbaf4a`, asked again
printf 'mod:arena;\n\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n\n%s\n' "$FAILSAFE" > "$F/p/arena.npk"
probe p_reader '    exit 0i32;' <<'NPK'
struct:Reader = { int64:x; };

NPK
for p in $OLD $PIN; do codes $p "$F/p/arena.npk" "$F/p/p_reader.npk" | sed 's/^/§1.8 BUILD.md §7: /'; done

# ---- §1.9 CI's rows
echo "§1.9 $PIN is $(git -C "$NPK_TREE" rev-parse $PIN); its emission row: $(grep -m1 ' npkc.ll ' "$WB/.internal/toolchain/$PIN/PIN.md" | awk '{print $2, $3}')"
git -C "$NPK_TREE" diff --quiet $OLD $PIN -- bootstrap/harness/quickemit.py && echo "§1.9 bootstrap/harness/quickemit.py: the same at both pins"
git -C "$NPK_TREE" cat-file -e $PIN:npkg/main.npk && echo "§1.9 npkg/main.npk: present at $PIN"

# ---- §1.10 what the patches add
python3 - "$T" "$REPO" <<'PY'
import os, re, subprocess, sys
T, R = sys.argv[1], sys.argv[2]
added, touched = [], set()
for n in (1, 2, 3, 4):
    f = None
    for l in open(os.path.join(T, "step%d.patch" % n), encoding="utf-8"):
        if l.startswith("+++ b/"):
            f = l[6:].strip(); touched.add(f)
        elif l.startswith("+") and not l.startswith("+++") and f and f.endswith(".npk"):
            added.append(l[1:])
def blank(l):
    l = re.sub(r'"([^"\\]|\\.)*"', '""', l)
    return l.split("//", 1)[0]
code = [blank(l) for l in added]
pats = [("comptime", r"\bcomptime\b"), ("a macro", r"\bmacro\b|#\[macro"), ("a float literal", r"\b\d+\.\d"),
        ("an enum", r"\benum:"), ("a generic declaration", r"func:\w+\s*<|struct:\w+\s*<"),
        ("an explicit variant value", r"^\s*\w+\s*=\s*-?\d+\s*,?\s*$"), ("`?|` or `#unreachable`", r"\?\||#unreachable"),
        ("`#wild_slice`", r"#wild_slice")]
print("§1.10 the patches' %d added `.npk` lines, comments and strings blanked:" % len(added))
print("  " + "; ".join("%s %d" % (n, sum(1 for c in code if re.search(p, c))) for n, p in pats))
held = [f for f in sorted(touched) if os.path.exists(os.path.join(R, f)) and "@@DATE021A@@" in open(os.path.join(R, f), encoding="utf-8").read()]
print("§1.10 the %d file(s) the patches touch that hold `@@DATE021A@@` as the tree stands: %s" % (len(touched), ", ".join(held) or "none"))
PY

rm -rf "${F:?}"

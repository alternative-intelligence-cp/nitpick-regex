# 0.2.6_tools/facts.sh -- §1 of `0.2.6.md`, re-derived (block 0b). Source `env.sh` first. Reads the checkout, the
# compiler's tree with `git show` and `git rev-parse` alone, and writes only under `$A`. Prints one section per
# subsection of §1, under its number.
P=$A/facts; rm -rf "${P:?}"; mkdir -p "$P"
echo "§1.1 the tree: HEAD a commit of this plan's: $(git -C "$REPO" log -1 --format=%s | grep -cE '^cycle 0\.2\.6: (the plan|fix round [0-9]+) '); its parent chain holds 084187a: $(git -C "$REPO" merge-base --is-ancestor 084187a HEAD && echo yes)"
echo "§1.1 0.2.5a.md's title: $(head -1 "$REPO/meta/roadmap/0.2/0.2.5a.md" | grep -oE '— DONE \([0-9-]+\)$')"
echo "§1.1 the decision log's last heading and its highest: $(grep -oE '^### RX-[0-9]+' "$REPO/meta/DECISIONS.md" | tail -1 | cut -c5-) $(grep -oE '^### RX-[0-9]+' "$REPO/meta/DECISIONS.md" | cut -c8- | sort -n | tail -1)"
echo "§1.1 the block's labels in the tree, outside this plan and its tools: $(git -C "$REPO" grep -l -E 'PD-18[1-9]|PD-190' -- . ':!meta/roadmap/0.2/0.2.6.md' ':!meta/roadmap/0.2/0.2.6_tools' | wc -l)"
python3 -B - "$REPO" <<'PY'
import os, re, sys
R = sys.argv[1]
sys.path.insert(0, os.path.join(R, "harness"))
import lexical
code = lexical.blank(lexical.read(os.path.join(R, "src/hir/repr.npk")))
kinds = [k.strip() for k in re.search(r"pub\s+enum\s*:\s*HirKind\s*=\s*\{([^}]*)\}", code).group(1).split(";") if k.strip()]
b = lexical.blank(lexical.read(os.path.join(R, "src/hir/build.npk")))
w, r = {}, {}
for u in re.finditer(r"(?<![A-Za-z0-9_.])HirKind\s*\.\s*([A-Za-z_]\w*)", b):
    read = b[:u.start()].rstrip().endswith(("==", "!=")) or b[u.end():].lstrip().startswith(("==", "!="))  # no window
    d = r if read else w
    how = "hnode" if b[:u.start()].rstrip().endswith("hnode(") else "assigned"
    d.setdefault(u.group(1), []).append(how)
print("§1.2 HirKind's kinds: %d -- %s" % (len(kinds), " ".join(kinds)))
print("§1.2 build.npk writes: " + "; ".join("%s %s" % (k, ",".join(sorted(set(w.get(k, ["NONE"]))))) for k in kinds))
print("§1.2 build.npk compares only: %s" % (", ".join(k for k in kinds if k in r and k not in w) or "none"))
for cyc in ("0.5", "0.6"):
    t = open(os.path.join(R, "meta/roadmap", cyc, "README.md"), encoding="utf-8").read().split("\n")
    hits = ["%d: %s" % (n, l.strip()[:70]) for n, l in enumerate(t, 1) if "`check_hir_kinds_total`'s" in l]
    print("§1.2 the %s README's boxes for the check's halves: %s" % (cyc, "; ".join(hits) or "none"))
for d in ("src/compile", "tests/oracle"):
    names = 0
    for root, _, fs in os.walk(os.path.join(R, d)):
        for f in fs:
            if f.endswith(".npk"):
                names += len(re.findall(r"HirKind\s*\.", lexical.blank(lexical.read(os.path.join(root, f)))))
    print("§1.2 %s/ names a HirKind: %d time(s)" % (d, names))
s = open(os.path.join(R, "meta/specs/SAFETY.md"), encoding="utf-8").read()
tab = s[s.index("| Constant | Default | Bounds |"):]
rows = [l for l in tab.split("\n")[2:] if l.startswith("| `NREGEX_")]
print("§1.3 SAFETY.md §5's table: %d row(s); the literal bounds among them: %d" % (len(rows), sum("LITERAL" in l for l in rows)))
import treecheck
print("§1.3 LIMIT_NAMES: %d; 64 in _SMALL: %s" % (len(treecheck.LIMIT_NAMES), 64 in treecheck._SMALL))
rp = lexical.blank(lexical.read(os.path.join(R, "src/hir/repr.npk")))
print("§1.3 repr.npk's code names NREGEX_LITERAL_LIMIT: %d time(s), in a comparison: %d" % (
    len(re.findall(r"\bNREGEX_LITERAL_LIMIT\b", rp)), len(re.findall(r"[<>]=?\s*NREGEX_LITERAL_LIMIT\b", rp))))
treecheck._SMALL.discard(64)
c = treecheck.check_constants_named(R)
print("§1.3 check_constants_named with 64 out of the set: %s, %s" % ("ok" if c.ok else "FAIL", c.examined))
der = []
for f in ("src/hir/repr.npk", "src/unicode/class_range.npk"):
    der += re.findall(r"#\[derive\(([^)]*)\)\]", open(os.path.join(R, f), encoding="utf-8").read())
print("§1.4 the derives in repr.npk and class_range.npk: %d, %s" % (len(der), sorted(set(der))))
hits = 0
for root, _, fs in os.walk(os.path.join(R, "src")):
    for f in fs:
        if f.endswith(".npk"):
            hits += len(re.findall(r"\.eq\(|hir_eq", lexical.blank(lexical.read(os.path.join(root, f)))))
print("§1.4 src/'s code names .eq( or hir_eq: %d time(s)" % hits)
PY
mkdir -p "$P/eq" && sed -e 's/^mod:probe02b_derive_eq;/mod:eqtruth;/' -e 's/^    exit 0i32;$/    if (HirKind.Empty.eq(HirKind.Empty)) { exit 20i32; }\n    exit 0i32;/' "$REPO/tests/probe/probe02b_derive_eq.npk" > "$P/eq/eqtruth.npk"
( leg; cd "$P/eq" && "$NPKC" eqtruth.npk -o eqtruth.ll > out.txt 2>&1; echo "§1.4 a derived .eq() as a condition, at $PIN: npkc exit $?, $(grep -oE 'NITPICK-[A-Z]+-[0-9]+ [^ ]+:[0-9]+:[0-9]+: [^;]*' out.txt | sed -E 's#^(NITPICK-[A-Z]+-[0-9]+) [^ ]*/?eqtruth.npk#\1 eqtruth.npk#')" )
for pin in 7e91730 "$PIN"; do
  git -C "$NPK_TREE" show "$pin:src/frontend/builtins.npk" > "$P/builtins.txt"
  python3 -B - "$P/builtins.txt" "$pin" <<'PY'
import re, sys
t = open(sys.argv[1], encoding="utf-8").read()
heads = [(m.start(), m.group(1)) for m in re.finditer(r"^(?:pub )?func:([a-z_0-9]+)", t, re.M)] + [(len(t), "")]
def names(fn):
    s, e = next((a, b) for (a, f), (b, _) in zip(heads, heads[1:]) if f == fn)
    return sorted(set(re.findall(r'string_eq\(name, "([a-z_]+)"\)', t[s:e])))
alln = sorted(set(re.findall(r'string_eq\(name, "([a-z_]+)"\)', t)))
print("§1.5 at %s: the facts' pattern reads %d names: is_builtin_name %d, is_hash_builtin %d -- %s" % (
    sys.argv[2], len(alln), len(names("is_builtin_name")), len(names("is_hash_builtin")), " ".join(names("is_hash_builtin"))))
PY
done
echo "§1.6 0.2.5a's runs: $(grep -E '^\| (0h|0r|0b|1h|2h|4h) \|' "$REPO/meta/roadmap/0.2/0.2.5a.md" | grep -oE '^\| [0-9a-z]+ |[0-9]+ GiB' | tr '\n' ' ' | sed 's/| //g; s/ $//')"
echo "§1.6 RX-134's run: $(grep -oE 'exit 3\*\*, which is `4 - 1` read out of a field named `end`' "$REPO/meta/DECISIONS.md")"
echo "§1.6 RX-245's words: $(grep -oE '`m\.end` read 3 at both legs' "$REPO/meta/DECISIONS.md")"
python3 -B "$T/handons.py" sweep "$REPO/meta/roadmap/0.2" | sed 's/^/§1.7 /'
python3 -B "$T/handons.py" control "$REPO/meta/roadmap/0.2" | tail -1 | sed 's/^/§1.7 /'
for n in 1 2 3 4 6 7; do
  f=$(grep -E '^diff --git' "$T/step$n.patch" | awk '{print substr($3, 3)}')
  held=$(for x in $f; do [ -f "$REPO/$x" ] && grep -l '@@DATE026@@' "$REPO/$x"; done | wc -l)
  bare=$(grep -E '^\+' "$T/step$n.patch" | grep -cE '2026-10-(1[6-9]|2[0-9])')
  echo "§1.8 step $n: $(echo $f | wc -w) file(s), $(grep -cE '^\+[^+]' "$T/step$n.patch") added line(s), $(grep -c '@@DATE026@@' "$T/step$n.patch") placeholder(s); touched files holding it: $held; a date after 2026-10-15 written bare: $bare"
done
( cd "$REPO" && REPO="$REPO" python3 -B "$T/archive.py" check ) | sed 's/^/§1.9 /'
rm -rf "${P:?}"

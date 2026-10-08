# meta/roadmap/0.2/0.2.0_tools/facts.sh -- `0.2.0.md` §1: re-derive the close's measurements at the pin, in scratch copies
# of the tree, never in it. Sourced after `env.sh`, one Bash call per part -- blocks 0b and 0c, run BEFORE step 1:
#
#     . "$REPO/meta/roadmap/0.2/0.2.0_tools/env.sh"; . "$T/facts.sh" 0b      (then, in its own call, 0c)
#
# `close` is the working tree with the fourteen code fences cycle 0.1's close wrote in this plan's §4 written over it,
# exactly as written there, PD labels and all -- read from `94b3072`'s `0.2.0.md` by `fences.py` -- so §1 is asked of
# the code the close measured. `new` is the working tree with steps 1 … 6 applied by GNU `patch` to the copy alone (`git
# apply` run inside this checkout would resolve the paths against the checkout), the code this plan's patches carry.
# Probes live in `$F/p`, outside both copies, so a full run over a copy sweeps none of them. A check is asked of its
# OWN tree's harness. Each part removes its copies at its end.
: "${REPO:?}" "${NPKC:?}" "${NPKRT:?}" "${A:?}" "${T:?}"
F=$A/facts
DAY=$(cat "$A/date" 2>/dev/null || date +%F)
fresh() {   # fresh <name> [<step>...]: the working tree as it stands at $F/<name>, then each step's patch, dated as
            # `apply.py` dates it
  local d=$1 n; shift
  mkdir -p "$F/$d"
  ( cd "$REPO" && git ls-files -co --exclude-standard -z | xargs -0 tar -cf - ) | tar -xf - -C "$F/$d"
  for n in "$@"; do
    sed "s/@@RUN_DATE@@/$DAY/g" "$T/step$n.patch" | patch -p1 -s --no-backup-if-mismatch -d "$F/$d" \
      || echo "STOP: step$n does not apply to a copy of the tree"
  done
}
closecopy() {   # the working tree, the close's fourteen fences written over it
  fresh close
  git -C "$REPO" show 94b3072:meta/roadmap/0.2/0.2.0.md > "$F/close020.md"
  python3 -B "$T/fences.py" "$F/close020.md" "$F/close" > "$F/fences.out"
  sed 's/^/the close'"'"'s /' "$F/fences.out"
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
UNITS="hir_size hir_unit hir_oob_get hir_oob_set_root hir_dump hir_dump_count hir_dump_stray_next hir_dump_not_a_tree"

case "${1:?facts.sh takes a part: 0b or 0c}" in
0b)
rm -rf "${F:?}"; mkdir -p "$F/p"
closecopy; fresh new 1 2 3 4 5 6

# ---- §1.2 the shape: each size a program's exit, both legs (RX-135), and `Literal` free beside a `Literal` variant
{ printf 'mod:sizes;\n\nuse "../close/src/hir/hir.npk".*;\n\n'
  printf '// H-2'"'"'s drawing, as `HIR.md` §2 declares it.\n#[derive(Copy)]\nstruct:Drawn = {\n'
  printf '    HirKind:kind;\n    int32:a;\n    int32:b;\n    int32:c;\n    uint32:flags;\n};\n\n'
  printf '// A struct named `Literal` beside an enum whose variant is `Literal`, in one module.\n'
  printf '#[derive(Copy)]\nenum:Kind = {\n    Empty;\n    Literal;\n};\n\n'
  printf '#[derive(Copy)]\nstruct:Literal = {\n    int64:off;\n    int64:len;\n};\n\n'
  printf 'func:main = int32(cstring[]:argv) {\n    int64:k = argv.len;\n'
  printf '    if (k == 1i64) { exit (#size_of<HirNode>() =>! int32); }\n'
  printf '    if (k == 2i64) { exit (#size_of<Drawn>() =>! int32); }\n'
  printf '    if (k == 3i64) { exit (#size_of<ClassRange>() =>! int32); }\n'
  printf '    if (k == 4i64) { exit (#size_of<GroupInfo>() =>! int32); }\n'
  printf '    if (k == 5i64) { exit (#size_of<HirKind>() =>! int32); }\n'
  printf '    if (k == 6i64) { exit (#size_of<Hir>() =>! int32); }\n'
  printf '    Kind:v = Kind.Literal;\n    Literal:l = Literal{ off: 3i64, len: 4i64 };\n'
  printf '    if (v != Kind.Literal) { exit 10i32; }\n    if ((l.off + l.len) != 7i64) { exit 11i32; }\n    exit 0i32;\n};\n\n'
  printf '%s\n' "$FAILSAFE"; } > "$F/p/sizes.npk"
legs "$F/p/sizes.npk" "§1.2" "#size_of<HirNode>()=" "#size_of<Drawn>(), H-2's drawing=a" "#size_of<ClassRange>()=a a" \
  "#size_of<GroupInfo>()=a a a" "#size_of<HirKind>()=a a a a" "#size_of<Hir>()=a a a a a" \
  "a struct Literal beside an enum's Literal, each read (0)=a a a a a a"

# ---- §1.3 the names the language takes, and the range view
printf 'mod:arena;\n\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n' > "$F/p/arena.npk"
printf 'mod:reader;\n\nstruct:Reader = { int64:pos; };\n\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n' > "$F/p/reader.npk"
echo "§1.3 $(codes $PIN "$F/p/arena.npk") -- $(cd "$F/p" && "$NPKC" arena.npk -o /dev/null 2>&1 | grep -o 'a keyword cannot be declared as a function, type or module name')"
echo "§1.3 $(codes $PIN "$F/p/reader.npk") -- $(cd "$F/p" && "$NPKC" reader.npk -o /dev/null 2>&1 | grep -oE '`Reader` is declared by the prelude[^;(]*')"
{ printf 'mod:view;\n\nfunc:main = int32(cstring[]:argv) {\n    uint8[]:t = string_bytes("abcdef");\n'
  printf '    int64:lo = argv.len;\n    uint8[]:v = t[lo...lo + 2i64];\n    int32:r = (v.len =>! int32) * 10i32;\n'
  printf '    if (v[0i64] == 98u8) { r = r + 1i32; }\n    exit r;\n};\n\n%s\n' "$FAILSAFE"; } > "$F/p/view.npk"
legs "$F/p/view.npk" "§1.3 t[lo...lo + 2i64] over \"abcdef\", exiting v.len * 10, plus 1 if v[0] is b, at" "lo 1=" "lo 5=a a a a" \
  "lo 7=a a a a a a"

# ---- §1.4 the modules compile, and what each costs a consumer
echo "§1.4 the close's sources as roots: $(codes $PIN "$F/close/src/unicode/class_range.npk" "$F/close/src/unicode/unicode.npk" \
  "$F/close/src/hir/repr.npk" "$F/close/src/hir/dump.npk" "$F/close/src/hir/hir.npk" | grep -c ' compiles$') of 5 compile"
echo "§1.4 before, the working tree:"
reach src/hir/hir.npk src/unicode/unicode.npk src/syntax/syntax.npk | sed 's/^/  /'
echo "§1.4 after, the close's copy:"
reach "$F/close/src/hir/hir.npk" "$F/close/src/hir/repr.npk" "$F/close/src/hir/dump.npk" "$F/close/src/unicode/unicode.npk" \
  "$F/close/src/unicode/class_range.npk" "$F/close/src/syntax/syntax.npk" | sed 's/^/  /'

# ---- §1.5 the tree checks, before and after, each copy asked with its own harness
echo "§1.5 before, the working tree:"; tchecks "$REPO"
echo "§1.5 after, the close's copy:"; tchecks "$F/close"

# ---- §1.6 the units, and the refusal with its control
echo "§1.6 the close's units:"; for u in $UNITS; do run4 "$F/close/tests/unit/$u.npk"; done | sed 's/^/  /'
echo "§1.6 $(codes $PIN "$F/close/tests/rejection/hir_nodes_read.npk")"
mkdir -p "$F/sealed"; cp -r "$F/close/src" "$F/close/tests" "$F/sealed/"
sed -i 's/^    hidden Vec<HirNode>:nodes; /    sealed Vec<HirNode>:nodes; /' "$F/sealed/src/hir/repr.npk"
echo "§1.6 the control, \`sealed\` for \`hidden\` on \`nodes\` ($(grep -c '^    sealed Vec<HirNode>:nodes; ' "$F/sealed/src/hir/repr.npk") line): $(codes $PIN "$F/sealed/tests/rejection/hir_nodes_read.npk")"

# ---- §1.7a the walk's bound: what a `decreases` measure admits, and a node with two parents
{ printf 'mod:dec;\n\nfunc:main = int32(cstring[]:argv) {\n    int64:k = argv.len;\n    int64:steps = 0i64;\n'
  printf '    int64:done = 0i64;\n    while (done < k) decreases 3i64 - steps {\n        steps = steps + 1i64;\n'
  printf '        done = done + 1i64;\n    }\n    exit 0i32;\n};\n\n%s\n' "$FAILSAFE"; } > "$F/p/dec.npk"
legs "$F/p/dec.npk" "§1.7a a loop whose measure is 3 - steps, run for" "four steps=a a a" "five steps=a a a a"

for t in close new; do
  { printf 'mod:share_%s;\n\nuse "../%s/src/core/core.npk".*;\nuse "../%s/src/hir/hir.npk".*;\n\n' "$t" "$t" "$t"
    printf 'func:main = int32(cstring[]:_~argv) {\n    Hir:h = raw hir_init(4i64);\n'
    printf '    int64:x = raw hir_push(@h, HirNode{ kind: HirKind.Literal, flags: 0u32, a: 97i64, b: 0i64, c: 0i64, next: HIR_NONE });\n'
    printf '    int64:r = raw hir_push(@h, HirNode{ kind: HirKind.Repeat, flags: 0u32, a: x, b: 0i64, c: HIR_NONE, next: x });\n'
    printf '    int64:cat = raw hir_push(@h, HirNode{ kind: HirKind.Concat, flags: 0u32, a: r, b: 2i64, c: 0i64, next: HIR_NONE });\n'
    printf '    drop hir_set_root(@h, cat);\n    Bytes:b = raw bytes_init(16i64);\n    drop hir_dump(@h, @b);\n'
    printf '    uint8[]:want = string_bytes("(concat (repeat 0 - (literal 97)) (literal 97))");\n'
    printf '    bool:same = (raw bytes_len(@b)) == want.len;\n    int64:i = 0i64;\n'
    printf '    while (same && (i < want.len)) decreases want.len - i {\n'
    printf '        if ((raw bytes_get(@b, i)) != want[i]) { same = false; }\n        i = i + 1i64;\n    }\n'
    printf '    drop hir_free(@h);\n    if (same) { exit 0i32; }\n    exit 10i32;\n};\n\n%s\n' "$FAILSAFE"; } > "$F/p/share_$t.npk"
  legs "$F/p/share_$t.npk" "§1.7a a leaf with two parents, every node reachable, dumped by the" "$t code (0: written twice)="
done

# ---- §1.10 the three records: what names the README's price paragraph, and which sweep counts its words. The three
# archived sweeps' totals are not printed: their pathspecs read this plan's own file, whose Expects quote them.
python3 -B - "$REPO" <<'PY'
import bisect, re, subprocess, sys
root = sys.argv[1]
hits = []
for f in subprocess.run(["git", "-C", root, "ls-files", "-z"], capture_output=True, text=True).stdout.split("\0"):
    if not f or f.startswith("meta/roadmap/0.2/0.2.0"):
        continue
    try:
        lines = [l.strip() for l in open(root + "/" + f, encoding="utf-8").read().split("\n")]
    except (UnicodeDecodeError, OSError):
        continue
    starts, pos = [], 0
    for l in lines:
        starts.append(pos)
        pos += len(l) + 1
    for m in re.finditer(r"price paragraph", " ".join(lines), re.I):
        hits.append("%s:%d" % (f, bisect.bisect_right(starts, m.start())))
print("§1.10 the README's price paragraph named, across line breaks, in %d place(s), this plan's file and tools aside:" % len(hits))
for h in hits:
    print("  " + h)
dec = open(root + "/meta/DECISIONS.md", encoding="utf-8").read()
rx = dec[dec.index("### RX-218 "):dec.index("### RX-219 ")]
print("§1.10 RX-218's text: %d mention(s) of README, price or paragraph" % len(re.findall(r"readme|price|paragraph", rx, re.I)))
PY
for s in 0.1.6a 0.1.6b 0.1.6; do
  d=$REPO/meta/roadmap/done/0.1/${s}_tools
  python3 -B "$d/sweep.py" "$REPO" "$F/sw_$s.txt" "$d/sweep_patterns.txt" > /dev/null
  echo "§1.10 $s's committed sweep over this tree: $(grep -cE ' README\.md:(5[6-9]|6[0-4]):' "$F/sw_$s.txt") saved line(s) in README.md 56-64"
done
python3 -B "$T/sweep.py" "$REPO" "$F/sw_step1.txt" "$T/sweep_step1.txt" decisions > /dev/null
echo "§1.10 this plan's step-1 sweep over this tree: $(grep -cE ' README\.md:(5[6-9]|6[0-4]):' "$F/sw_step1.txt") of its $(wc -l < "$F/sw_step1.txt") saved line(s) in README.md 56-64"

# ---- §1.11 this plan's code against the close's: the patched copy's files beside the fences, PD labels read as RX
python3 -B - "$F/close" "$F/new" "$F/fences.out" <<'PY'
import difflib, os, sys
close, new = sys.argv[1], sys.argv[2]
rx = {"PD-66": "RX-222", "PD-67": "RX-223", "PD-68": "RX-224", "PD-69": "RX-225"}
paths = open(sys.argv[3], encoding="utf-8").read().split(": ", 1)[1].split()
same = []
for p in sorted(paths):
    a = open(os.path.join(close, p), encoding="utf-8").read()
    for k, v in rx.items():
        a = a.replace(k, v)
    b = open(os.path.join(new, p), encoding="utf-8").read()
    if a == b:
        same.append(os.path.basename(p))
        continue
    d = [l for l in difflib.unified_diff(a.split("\n"), b.split("\n"), lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
    print("§1.11 %s: %d line(s) out, %d in" % (p, sum(l[0] == "-" for l in d), sum(l[0] == "+" for l in d)))
    for l in d:
        print("    " + l[:118])
print("§1.11 the same but for PD labels written as RX numbers: %d of %d -- %s" % (len(same), len(paths), " ".join(same)))
extra = sorted(set(f for f in os.listdir(os.path.join(new, "tests", "unit")) if f.startswith("hir_"))
               - set(f for f in os.listdir(os.path.join(close, "tests", "unit")) if f.startswith("hir_")))
print("§1.11 a unit the close did not write: %s" % (" ".join(extra) or "none"))
PY
rm -rf "${F:?}"
;;
0c)
rm -rf "${F:?}"; mkdir -p "$F"
closecopy
echo "§1.7 the close's thirty-two mutants, over its code:"
python3 -B "$T/mutants.py" "$F/close" 0c 4 | sed 's/^/  /'
echo "§1.8 the full run over the close's copy:"
harness facts_close "$F/close" | sed 's/^/  /'
rm -rf "${F:?}"
;;
esac

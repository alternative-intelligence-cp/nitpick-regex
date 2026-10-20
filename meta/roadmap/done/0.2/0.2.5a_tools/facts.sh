# meta/roadmap/0.2/0.2.5a_tools/facts.sh -- `0.2.5a.md` §1: re-derive what this plan rests on, at both pins, from the
# checkout as it stands and from probes in scratch, never in the tree. Sourced after `env.sh`, as block 0b, BEFORE
# step 1:
#
#     . "$REPO/meta/roadmap/0.2/0.2.5a_tools/env.sh"; . "$T/facts.sh"
#
# The unchanged tree's two censuses are kept as `$A/head_old.tsv` and `$A/head_new.tsv`, and its emissions at the old
# pin in `$A/emit/head_old/`, for blocks 1 and 2; everything else here is removed at the end. Each probe is built and
# run at the pin it is asked of, both legs (`legs`). The compiler's tree is read with `git show`, `git diff`,
# `git rev-parse` and `git ls-tree` alone. `../0.2.1a_tools/facts.sh`'s shape.
: "${REPO:?}" "${A:?}" "${T:?}" "${PIN:?}" "${OLD:?}"
F=$A/facts
legs() {    # legs <pin> <src> <label>: build at <pin>, run at -O0 and through `opt -O2`, and print
            # `<label>: <exit> at -O0, <exit> after opt -O2` -- or the refusal's codes and sites
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
said() {    # said <pin> <file>: the first diagnostic's text, after its code and site
  ( leg "$1"; cd "$(dirname "$2")" && "$NPKC" "$(basename "$2")" -o /dev/null 2>&1 | head -1 \
      | sed -E 's|^(NITPICK-[A-Z]+-[0-9]+) [^ ]+: |\1: |' | cut -c1-120 )
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

# ---- §1.3 landing 113's refusal, enumerated: every file as a root at both pins -- the checkout itself, as it stands
echo "§1.3 the unchanged tree, every .npk a root:"
census $OLD "$REPO" head_old | sed 's/^/  /'
census $PIN "$REPO" head_new | sed 's/^/  /'
python3 -B "$T/census.py" sites "$A/head_new.tsv" NITPICK-PARSE-001 | sed 's/^/  /'
python3 - "$A/head_new.tsv" <<'PY'
import collections, sys
rows = [l.rstrip("\n").split("\t") for l in open(sys.argv[1])]
roots = sorted({f for f, e, c, s in rows if c == "NITPICK-PARSE-001"})
by = collections.Counter(f.rsplit("/", 1)[0] for f in roots)
print("  its roots: " + ", ".join("%s %d" % kv for kv in sorted(by.items())))
print("  in src/: " + ", ".join(f for f in roots if f.startswith("src/")))
PY
echo "§1.3 each file at $OLD against $PIN, NITPICK-PARSE-001 left out:"
python3 -B "$T/census.py" compare "$A/head_old.tsv" "$A/head_new.tsv" NITPICK-PARSE-001 | sed 's/^/  /' | cut -c1-150

# ---- §1.4 a keyword as a field's name, and as a local's, asked of both compilers
probe p_match_end '    Match:m = Match{ start: 1i64, end: 4i64 };
    exit ((m.end - m.start) =>! int32);' <<'NPK'
struct:Match = { int64:start; int64:end; };

NPK
probe p_one_keyword '    K:k = K{ x: 1i64, stack: 3i64 };
    k.stack = k.stack + 4i64;
    exit (k.stack =>! int32);' <<'NPK'
struct:K = { int64:x; int64:stack; };

NPK
probe p_two_keywords '    K:k = K{ x: 1i64, stack: 3i64, end: 40i64 };
    exit (k.end =>! int32);' <<'NPK'
struct:K = { int64:x; int64:stack; int64:end; };

NPK
probe p_use_read '    S:s = S{ x: 1i64 };
    int64:y = s.use;
    exit (y =>! int32);' <<'NPK'
struct:S = { int64:x; };

NPK
probe p_rx134_k '    exit 0i32;' <<'NPK'
pub struct:K = { int64:range; int64:limit; int64:in; };

NPK
probe p_limit_field '    exit 0i32;' <<'NPK'
struct:K = { int64:x; int64:limit; };

NPK
probe p_local_end '    int64:end = 5i64;
    exit (end =>! int32);' < /dev/null
probe p_local_stack '    int64:stack = 5i64;
    exit (stack =>! int32);' < /dev/null
probe p_frames '    K:k = K{ x: 1i64, frames: 3i64 };
    k.frames = k.frames + 4i64;
    exit (k.frames =>! int32);' <<'NPK'
struct:K = { int64:x; int64:frames; };

NPK
for pr in "p_match_end:RX-134's Match, a field named end, read (3)" "p_one_keyword:one keyword field, stack, written and read (7)" \
    "p_two_keywords:two keyword fields in one literal" "p_use_read:a read of .use where S has no such field" \
    "p_rx134_k:RX-134's K, three keyword fields declared, unused (0)" "p_limit_field:a field named limit, declared alone, unused (0)" \
    "p_local_end:a local named end" \
    "p_local_stack:a local named stack" "p_frames:a field named frames, written and read (7)"; do
  for p in $OLD $PIN; do legs $p "$F/p/${pr%%:*}.npk" "§1.4 ${pr#*:} at $p"; done
done
echo "§1.4 the two keyword fields' literal at $OLD -- $(said $OLD "$F/p/p_two_keywords.npk")"
echo "§1.4 the read of .use at $PIN -- $(said $PIN "$F/p/p_use_read.npk")"
echo "§1.4 the field named end at $PIN -- $(said $PIN "$F/p/p_match_end.npk")"

# ---- §1.5 the rename's extent: every line of parse.npk that names the word
python3 - "$REPO/src/syntax/parse.npk" <<'PY'
import re, sys
lines = open(sys.argv[1], encoding="utf-8").read().split("\n")
hits = [(i + 1, l) for i, l in enumerate(lines) if re.search(r"\bstack\b", l)]
code = [n for n, l in hits if not l.lstrip().startswith("//")]
comm = [n for n, l in hits if l.lstrip().startswith("//")]
field = [n for n, l in hits if re.search(r"p\.stack\b|Frame>:stack\b|, stack: ", l)]
print("§1.5 src/syntax/parse.npk: %d line(s) name `stack` -- %d code, at %s; %d comment, at %s"
      % (len(hits), len(code), " ".join(map(str, code)), len(comm), " ".join(map(str, comm))))
print("§1.5 of them, the field by name: %d -- the code lines and the comment at %s"
      % (len(field), " ".join(str(n) for n in field if n in comm)))
PY
echo "§1.5 the live tree's other files that name the field: $(git -C "$REPO" grep -n -I -E 'p\.stack\b|Frame>:stack\b' -- . \
  ':!src/syntax/parse.npk' ':!meta/roadmap/done' ':!meta/roadmap/0.2/0.2.1a_tools' ':!meta/roadmap/0.2/0.2.5a_tools' \
  ':!meta/roadmap/0.2/0.2.5a.md' | cut -d: -f1,2 | tr '\n' ' ' | sed 's/ $//')"

# ---- §1.6 D-332's count over the unchanged tree, at both pins
echo "§1.6 D-332's count, the unchanged tree:"; python3 -B "$T/sitecount.py" "$REPO" $OLD $PIN | sed 's/^/  /'

# ---- the unchanged tree's emissions at the old pin, kept for block 1
echo "§1.7 the unchanged tree's emissions, kept for block 1:"; emits $OLD "$REPO" head_old | sed 's/^/  /'

# ---- §1.8 B-4e's re-read, and the two functions O-G1 cites
echo "§1.8 the files B-4e names, $OLD to $PIN:"
git -C "$NPK_TREE" diff --stat $OLD $PIN -- src/frontend/lexer.npk src/frontend/escapes.npk src/frontend/parse_decl.npk \
  meta/specs/LEXICAL_REFERENCE.md src/frontend/numeric.npk src/frontend/num_width.npk | sed 's/^/ /'
echo "§1.8 lexer.npk's changed lines:"
git -C "$NPK_TREE" diff -U0 $OLD $PIN -- src/frontend/lexer.npk | grep -E '^[-+] ' | sed -E 's/^([-+]) +/  \1 /'
for fn in lexer.npk:lexer_skip_trivia lexer.npk:lexer_next parse_decl.npk:p_parse_import numeric.npk:num_scan \
          num_width.npk:num_width_of escapes.npk:escape_decode escapes.npk:decode_string \
          type_resolve.npk:fold_expr type_resolve.npk:fold_string_builtin; do
  a=$(git -C "$NPK_TREE" show $OLD:src/frontend/${fn%%:*} | awk "/^(pub )?func:${fn#*:} /,/^};/" | sha256sum | cut -c1-16)
  b=$(git -C "$NPK_TREE" show $PIN:src/frontend/${fn%%:*} | awk "/^(pub )?func:${fn#*:} /,/^};/" | sha256sum | cut -c1-16)
  echo "§1.8 ${fn#*:}: $a at $OLD, $b at $PIN -- $([ "$a" = "$b" ] && echo the same || echo MOVED)"
done
echo "§1.8 LEXICAL_REFERENCE.md's added lines sit under: $(git -C "$NPK_TREE" show $PIN:meta/specs/LEXICAL_REFERENCE.md \
  | awk -v at="$(git -C "$NPK_TREE" diff -U0 $OLD $PIN -- meta/specs/LEXICAL_REFERENCE.md | grep -oE '^@@ [^ ]+ \+[0-9]+' | grep -oE '[0-9]+$' | head -1)" \
    'NR <= at && /^## / {h = $0} END {print h}')"

# ---- §1.9 rx120 at the new pin, in the checkout's position, and BUILD.md §7's two dated rows asked again
echo "§1.9 harness/baseline/rx120.sh at $PIN, as the tree stands:"
( leg $PIN; cd "$REPO" && harness/baseline/rx120.sh ) | grep -E '^(ok|FAIL|SKIPPED|rx120: (pin|control|every))' | sed 's/^/  /' | cut -c1-110
printf 'mod:arena;\n\nfunc:main = int32(cstring[]:_~argv) {\n    exit 0i32;\n};\n\n%s\n' "$FAILSAFE" > "$F/p/arena.npk"
probe p_reader '    exit 0i32;' <<'NPK'
struct:Reader = { int64:x; };

NPK
for p in $OLD $PIN; do codes $p "$F/p/arena.npk" "$F/p/p_reader.npk" | sed 's/^/§1.9 BUILD.md §7: /'; done

# ---- §1.10 CI's rows, and the emission it asserts
echo "§1.10 $PIN is $(git -C "$NPK_TREE" rev-parse $PIN); its emission row: $(grep -m1 ' npkc.ll ' "$WB/.internal/toolchain/$PIN/PIN.md" | awk '{print $2, $3}')"
git -C "$NPK_TREE" diff --quiet $OLD $PIN -- bootstrap/ && echo "§1.10 bootstrap/: the same at both pins, quickemit.py and the seed among it"
echo "§1.10 npkg/main.npk at $PIN: $(git -C "$NPK_TREE" ls-tree --name-only $PIN npkg/main.npk)"
echo "§1.10 the seed's null_pointer_is_valid at $PIN: $(git -C "$NPK_TREE" show $PIN:bootstrap/seed/stage1.ll | grep -c null_pointer_is_valid)"
echo "§1.10 the emitter's at $PIN: $(git -C "$NPK_TREE" show $PIN:src/backend/ir/ir_types.npk | grep -c 'split-stack\\" null_pointer_is_valid')"

# ---- §1.11 what the patches add
python3 - "$T" "$REPO" <<'PY'
import os, re, sys
T, R = sys.argv[1], sys.argv[2]
added, removed, touched = [], [], set()
for n in (1, 2, 3, 4):
    f = None
    for l in open(os.path.join(T, "step%d.patch" % n), encoding="utf-8"):
        if l.startswith("+++ b/"):
            f = l[6:].strip(); touched.add(f)
        elif f and f.endswith(".npk") and l[:1] in "+-" and not l.startswith(("+++", "---")):
            (added if l[0] == "+" else removed).append(l[1:].rstrip("\n"))
def code(l):
    return "" if l.lstrip().startswith("//") else l.split("//", 1)[0].rstrip()
ca = [code(l) for l in added if code(l)]
cr = [code(l) for l in removed if code(l)]
same = sorted(x.replace("stack", "frames") for x in cr) == sorted(ca)
print("§1.11 the patches' added `.npk` lines: %d, %d of them code -- each a removed line with `stack` read `frames`: %s"
      % (len(added), len(ca), "yes" if same else "NO"))
held = [f for f in sorted(touched) if os.path.exists(os.path.join(R, f)) and "@@DATE025A@@" in open(os.path.join(R, f), encoding="utf-8").read()]
print("§1.11 the %d file(s) the patches touch that hold `@@DATE025A@@` as the tree stands: %s" % (len(touched), ", ".join(held) or "none"))
PY

rm -rf "${F:?}"

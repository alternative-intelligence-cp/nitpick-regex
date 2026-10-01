# meta/roadmap/0.1/0.1.4_tools/env.sh -- sourced at the top of EVERY command block of
# `0.1.4.md`, because a Bash call keeps no variables and no functions from the call
# before it. Set REPO first, to the dispatch's REPO line:
#
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/0.1/0.1.4_tools/env.sh"
#
# 0.1.3's helpers -- `codes`, `harness`, `ctl`, `run4`, `nrcheck` -- with `mutant` widened to name
# the file it breaks, and `selfcase`: one self-check case alone, on the working tree's harness or
# on one with its literal reader broken. `$NPK_TREE` is read with `git` read commands only. Every
# `rm` names its target through `${VAR:?}`. Nothing prints a path above the repository, so no
# output carries a home directory into a record.
#
# THE WORKBENCH IS `$REPO/..`, as for every plan before this one, unless `PLAN_WB` names
# it -- which only a rehearsal in a clone outside the workbench does (the plan's §9).
#
# TMPDIR IS THE REPOSITORY'S OWN SCRATCH, `$A/tmp`. The workbench's sandbox refuses a plain
# `/tmp` (live since 2026-10-01 12:2x), so every block sends the harness's temporary copies
# inside this repository's gitignored `.internal/`, which RX-195 made safe for B-4's `repro`.
: "${REPO:?set REPO to the REPO line of the dispatch, first}"
REPO=$(realpath "$REPO")
WB=$(realpath "${PLAN_WB:-$REPO/..}")
NPK_TREE=$(realpath "$WB/../nitpick")
PIN=5fbaf4a                                   # the pin this subcycle is planned and rehearsed at
PIN_FULL=5fbaf4a40a2f6b213754cd71b6c69700f8aa2c87
NPKC=$WB/.internal/toolchain/$PIN/npkc
NPKRT=$WB/.internal/toolchain/$PIN/npkrt.o
# `harness/baseline/rx120.sh`'s historical leg looks for `950bb1d` under
# `$REPO/../.internal/toolchain/`; it is named here, so the leg runs wherever the clone is.
NPKC_950BB1D=$WB/.internal/toolchain/950bb1d/npkc
T=$REPO/meta/roadmap/0.1/0.1.4_tools        # these tools
A=$REPO/.internal/n14                         # gitignored scratch
mkdir -p "$A/tmp"
TMPDIR=$A/tmp
export NPKC NPKRT NPKC_950BB1D TMPDIR          # the harness reads them from the ENVIRONMENT

# Compile each file as a root from its own directory and print `<file> at <pin>:` and
# each diagnostic's code and site -- `L:C` in the file itself, `<name>:L:C` in another
# -- or `compiles`.        codes <pin> <file>...     (a relative file is the repository's)
codes() {
  local pin=$1; shift
  local cc=$WB/.internal/toolchain/$pin/npkc f src out b
  for f in "$@"; do
    src=$f; [ "${f#/}" = "$f" ] && src="$REPO/$f"
    b=$(basename "$src")
    out=$(cd "$(dirname "$src")" && "$cc" "$b" -o /dev/null 2>&1)
    if [ -z "$out" ]; then echo "$b at $pin compiles"; continue; fi
    echo "$b at $pin: $(echo "$out" | grep -oE '^NITPICK-[A-Z]+-[0-9]+ [^ ]+:[0-9]+:[0-9]+' \
      | sed -E "s|^(NITPICK-[A-Z]+-[0-9]+) ([^ ]*/)?([^/ ]+):([0-9]+):([0-9]+)$|\1 \3:\4:\5|; s| $b:| |" \
      | tr '\n' ' ' | sed 's/ $//')"
  done
}

# The full harness at the pin, its log kept, its summary printed: the exit, the target, the
# self-check's count, every tree check by name, the repro step, the units and the verdict.
#     harness <label>
harness() {
  free -g | awk '/^Mem:/ {print "available GiB:", $7}'
  ( cd "$REPO" && python3 -B harness/run.py ) > "$A/$1.log" 2>&1
  echo "harness exit $?"
  grep -E '^ok    target|live, [0-9]+ pending|^ok    repro|unit\(s\) passed|^GREEN|^THE SELF-CHECK FAILED' "$A/$1.log" | cut -c1-150
  grep -E '^FAIL  [a-z]' "$A/$1.log" | cut -c1-150
  echo "tree checks: $(grep -oE '^  (ok  |FAIL|note)  check_[a-z_]+' "$A/$1.log" | awk '{print $2}' | tr '\n' ' ')"
}

# A copy of the working tree AS IT STANDS -- tracked and new files, not the ignored --
# at $A/ctl/<name>, for a control to change one thing in. Prints nothing.
#     ctl <name>
ctl() {
  local d="$A/ctl/$1"
  rm -rf "${d:?}"; mkdir -p "$d"
  ( cd "$REPO" && git ls-files -co --exclude-standard -z | xargs -0 tar -cf - ) | tar -xf - -C "$d"
}

# Build a program and run it at -O0 and through `opt -O2`: `npkc`, `llc`, `ld.lld`, the
# binary -- all four, because `npkc` exit 0 is not well-formedness (O-N11).
#     run4 <file>...     (at $PIN)
run4() {
  local f src b o r0 r2
  mkdir -p "$A/run4"
  for f in "$@"; do
    src=$f; [ "${f#/}" = "$f" ] && src="$REPO/$f"
    b=$(basename "$src" .npk); o="$A/run4/$b"
    if ! ( cd "$(dirname "$src")" && "$NPKC" "$(basename "$src")" -o "$o.ll" ) > "$o.npkc" 2>&1; then
      echo "$b: npkc refused -- $(grep -oE '^NITPICK-[A-Z]+-[0-9]+' "$o.npkc" | sort -u | tr '\n' ' ')"; continue
    fi
    llc -O0 -filetype=obj -relocation-model=static "$o.ll" -o "$o.o" && ld.lld -static "$o.o" "$NPKRT" -o "$o"
    "$o" > /dev/null 2>&1; r0=$?
    opt -O2 -S "$o.ll" -o "$o.2.ll" && llc -O2 -filetype=obj -relocation-model=static "$o.2.ll" -o "$o.2.o" \
      && ld.lld -static "$o.2.o" "$NPKRT" -o "$o.2"
    "$o.2" > /dev/null 2>&1; r2=$?
    echo "$b: -O0 $r0, -O2 $r2"
  done
}

# `check_no_recursion` alone over a tree (the working tree by default): its verdict and
# what it examined.        nrcheck [<tree>]
nrcheck() {
  python3 -B - "${1:-$REPO}" <<'PY'
import os, sys
root = sys.argv[1]
sys.path.insert(0, os.path.join(root, "harness"))
import treecheck
r = treecheck.check_no_recursion(root)
print("check_no_recursion:", "ok" if r.ok else "FAIL", "|", r.examined)
for f in r.failures:
    print("   ", f[:160])
PY
}

# One self-check case alone, on the instrument, on the working tree's harness -- or on a
# harness with its literal reader broken, to show the case can fail:
#   head           `check_constants_named` as `HEAD` holds it -- before step 1, the old pattern
#   left-off       the literal left of a comparison is not read
#   no-base        a base suffix is not read, so `10FFFFhexi64` is read as no number
#     selfcase <n> [<mutation>]
selfcase() {
  python3 -B - "$REPO" "$1" "${2:-}" <<'PY'
import os, sys, types, subprocess
root, num, mut = sys.argv[1], int(sys.argv[2]), sys.argv[3]
sys.path.insert(0, os.path.join(root, "harness"))
path = os.path.join(root, "harness", "treecheck.py")
if mut == "head":
    src = subprocess.run(["git", "-C", root, "show", "HEAD:harness/treecheck.py"],
                         capture_output=True, text=True, check=True).stdout
else:
    src = open(path, encoding="utf-8").read()
    old, new = {
        "left-off": ("list(_CMP_RIGHT.finditer(code)) + list(_CMP_LEFT.finditer(code))",
                     "list(_CMP_RIGHT.finditer(code))"),
        "no-base": ("            base, body = b, t[:-len(suffix)]\n            break\n", "            break\n"),
        "": ("", ""),
    }[mut]
    assert src.count(old) == 1 or mut == "", f"{mut}: its old text is not in treecheck.py once"
    src = src.replace(old, new)
m = types.ModuleType("treecheck")
m.__file__ = path
exec(compile(src, path, "exec"), m.__dict__)
sys.modules["treecheck"] = m
import selfcheck
case = [c for c in selfcheck.CASES if c.num == num][0]
o = selfcheck._run_case(case, False)
print(f"case {num}{' against ' + mut if mut else ''}:", "passes" if o.ok else "RED", "|", o.detail[:240])
PY
}

# One rule of the parser broken in a copy of the working tree, and the named units built
# against it at -O0 and run: each must exit as the plan's §1.10 records. The table names each
# mutation by the rule it breaks, and the file it edits; its old text must occur in that file
# exactly once, or the helper says so and runs nothing.
#     mutant <name> <unit>...      (a unit is a file under tests/unit/, without `.npk`)
mutant() {
  local name=$1; shift
  ctl "mut_$name"
  python3 -B - "$A/ctl/mut_$name" "$name" <<'PY' || return 0
import os, sys
root, name = sys.argv[1], sys.argv[2]
P, E = "src/syntax/parse.npk", "src/syntax/pattern_error.npk"
M = {
  # step 2 -- the sentinel: each site back to 0, and the text reading 0 as the end
  "sentinel-end": (P, "        pass raw pattern_error(PatternErrorKind.BadGroupName, start, 0i64, NOT_A_CODEPOINT);",
                      "        pass raw pattern_error(PatternErrorKind.BadGroupName, start, 0i64, 0u32);"),
  "sentinel-name": (P, "        pass raw pattern_error(PatternErrorKind.BadGroupName, start, len, NOT_A_CODEPOINT);",
                       "        pass raw pattern_error(PatternErrorKind.BadGroupName, start, len, 0u32);"),
  "text-reads-zero": (E, "            if (e.detail == NOT_A_CODEPOINT) {\n                drop put(@b, \": the name has no closing",
                         "            if (e.detail == 0u32) {\n                drop put(@b, \": the name has no closing"),
  # step 3 -- the escapes
  "zero-digit-ok": (P, "        if (raw is_digit(raw cursor_peek(@p.c))) {\n            pass raw pattern_error(PatternErrorKind.UnknownEscape, at, 3i64",
                       "        if (false) {\n            pass raw pattern_error(PatternErrorKind.UnknownEscape, at, 3i64"),
  "hex-one-digit": (P, "    while (k < 2i64) decreases 2i64 - k {", "    while (k < 1i64) decreases 1i64 - k {"),
  "hex-no-stop": (P, "            if (v <= CP_MAX) { v = (v * 16i64) + h; }\n            n = n + 1i64;",
                     "            v = (v * 16i64) + h;\n            n = n + 1i64;"),
  "surrogate-ok": (P, "    if ((v >= CP_SURROGATE_LO) && (v <= CP_SURROGATE_HI)) {", "    if (false) {"),
  "past-max-ok": (P, "    if (v > CP_MAX) {\n        pass raw pattern_error(PatternErrorKind.InvalidCodepoint",
                     "    if (false) {\n        pass raw pattern_error(PatternErrorKind.InvalidCodepoint"),
  "letters-literal": (P, "    if (raw is_letter(b)) { pass false; }\n    pass !(raw is_digit(b));",
                         "    pass !(raw is_digit(b));"),
  "anchor-a-is-z": (P, "        int64:k = 2i64;\n        if (d == CH_LOWER_Z) { k = 3i64; }",
                       "        int64:k = 3i64;\n        if (d == CH_LOWER_Z) { k = 3i64; }"),
  "end-detail-zero": (P, "        pass raw pattern_error(kind, at, p.c.pos - at, NOT_A_CODEPOINT);",
                         "        pass raw pattern_error(kind, at, p.c.pos - at, 0u32);"),
  "range-end-no-escape": (P, "        if (!e.named) { pass raw unknown_escape(pat, at); }",
                             "        if (true) { pass raw unknown_escape(pat, at); }"),
  # step 4 -- `\<` and `\>` back to the bytes
  "angle-literal": (P, "    if ((b == CH_LT) || (b == CH_GT)) { pass false; }\n", ""),
  # step 5 -- the flags
  "flags-pending": (P, "                                                     open, p.c.pos - open));\n            drop commit(out, @p.f);",
                       "                                                     open, p.c.pos - open));"),
  "flags-reset-at-bar": (P, "            drop close_alt(out, @p.f, at);\n            p.f.cat_pos = p.c.pos;",
                            "            drop close_alt(out, @p.f, at);\n            p.f.cat_pos = p.c.pos;\n            p.f.flags = AST_FLAG_U;"),
  "group-inner-flags": (P, "    p.f.pending = raw ast_push(out, raw node(AstKind.Group, p.f.flags, body,",
                           "    p.f.pending = raw ast_push(out, raw node(AstKind.Group, inner.flags, body,"),
  "duplicate-ok": (P, "            if (((set | clear) & bit) != 0u32) {", "            if (false) {"),
  "second-minus-ok": (P, "            if (minus) {\n                pass raw pattern_error(PatternErrorKind.UnknownFlag, at, 1i64, CH_MINUS =>! uint32);",
                         "            if (false) {\n                pass raw pattern_error(PatternErrorKind.UnknownFlag, at, 1i64, CH_MINUS =>! uint32);"),
  "empty-flags-ok": (P, "            if (!named) {\n                pass raw pattern_error(PatternErrorKind.UnknownFlag, at, 1i64, b =>! uint32);",
                        "            if (false) {\n                pass raw pattern_error(PatternErrorKind.UnknownFlag, at, 1i64, b =>! uint32);"),
  # step 6 -- `x`
  "x-off": (P, "    pass (p.f.flags & AST_FLAG_X) != 0u32;", "    pass false;"),
  "x-comment-on": (P, "        more = (raw cursor_bump(@p.c)) != CH_LF;", "        discard(raw cursor_bump(@p.c));"),
  "x-class-ok": (P, "        if ((raw extended(p)) && ((raw is_space(b)) || (b == CH_HASH))) {\n            e = raw ambiguous(at, 1i64, b => int64);",
                    "        if (false) {\n            e = raw ambiguous(at, 1i64, b => int64);"),
  "x-wide-ok": (P, "    if ((cp == WS_NEL) || (cp == WS_NBSP) || (cp == WS_OGHAM)) { pass true; }",
                   "    if (cp < 0i64) { pass true; }"),
  "x-range-end-ok": (P, "        if ((raw extended(p)) && ((raw is_space(b)) || (b == CH_HASH) || (raw is_wide_space(hi)))) {",
                        "        if (false) {"),
  # step 7 -- `(?-u)`
  "byte-off": (P, "    if (hex2 || (cp < 128i64)) { pass NIL; }", "    pass NIL;"),
  "byte-hex2-refused": (P, "    if (hex2 || (cp < 128i64)) { pass NIL; }", "    if (cp < 128i64) { pass NIL; }"),
  "byte-flag-off": (P, "    if ((fl & AST_FLAG_U) == 0u32) { fl = fl + AST_FLAG_BYTE; }\n", ""),
  "byte-property-ok": (P, "    if ((d != CH_LOWER_P) && (d != CH_UPPER_P)) { pass NIL; }", "    pass NIL;"),
  "byte-class-ok": (P, "            else { e = raw byte_mode(p, at, n, cp, false); }", "            else { e = NIL; }"),
}
f, old, new = M[name]
p = os.path.join(root, f)
s = open(p, encoding="utf-8").read()
if s.count(old) != 1:
    print(f"{name}: its old text occurs {s.count(old)} times in {os.path.basename(f)} -- nothing run")
    sys.exit(1)
open(p, "w", encoding="utf-8").write(s.replace(old, new))
PY
  local u d="$A/ctl/mut_$name/tests/unit" r
  for u in "$@"; do
    if ! ( cd "$d" && "$NPKC" "$u.npk" -o "$u.ll" ) > "$d/$u.npkc" 2>&1; then
      echo "$name: $u npkc refused -- $(grep -oE '^NITPICK-[A-Z]+-[0-9]+' "$d/$u.npkc" | sort -u | tr '\n' ' ')"; continue
    fi
    ( cd "$d" && llc -O0 -filetype=obj -relocation-model=static "$u.ll" -o "$u.o" && ld.lld -static "$u.o" "$NPKRT" -o "$u" )
    "$d/$u" > /dev/null 2>&1; r=$?
    echo "$name: $u -O0 $r"
  done
  rm -rf "${A:?}/ctl/mut_$name"
}

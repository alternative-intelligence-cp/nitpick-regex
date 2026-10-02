# meta/roadmap/0.1/0.1.5_tools/env.sh -- sourced at the top of EVERY command block of
# `0.1.5.md`, because a Bash call keeps no variables and no functions from the call
# before it. Set REPO first, to the dispatch's REPO line:
#
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/0.1/0.1.5_tools/env.sh"
#
# 0.1.4's helpers -- `codes`, `harness`, `ctl`, `run4`, `nrcheck` and `mutant`, its table this plan's
# -- and `texts`, which prints what `pattern_error_text` says for a pattern. `$NPK_TREE` is read with
# `git` read commands only. Every `rm` names its target through `${VAR:?}`. Nothing prints a path
# above the repository, so no output carries a home directory into a record.
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
T=$REPO/meta/roadmap/0.1/0.1.5_tools        # these tools
A=$REPO/.internal/n15                         # gitignored scratch
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

# One rule of the parser broken in a copy of the working tree, and the named units built
# against it at -O0 and run: each must exit as the plan's §1.12 records. The table names each
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
  # step 2 -- the escapes §8 declines, each by its own kind
  "backref-unknown": (P, "    if ((raw is_digit(d)) || (d == CH_LOWER_K)) {\n        pass raw pattern_error(PatternErrorKind.BackreferenceUnsupported",
                         "    if (false) {\n        pass raw pattern_error(PatternErrorKind.BackreferenceUnsupported"),
  "k-unknown": (P, "    if ((raw is_digit(d)) || (d == CH_LOWER_K)) {", "    if (raw is_digit(d)) {"),
  "anchor-unknown": (P, "    if ((d == CH_UPPER_G) || (d == CH_UPPER_Z)) {\n        pass raw pattern_error(PatternErrorKind.UnsupportedAnchor",
                        "    if (false) {\n        pass raw pattern_error(PatternErrorKind.UnsupportedAnchor"),
  "quote-unknown": (P, "    if ((d == CH_UPPER_Q) || (d == CH_UPPER_E)) {\n        pass raw pattern_error(PatternErrorKind.UnsupportedQuoting",
                       "    if (false) {\n        pass raw pattern_error(PatternErrorKind.UnsupportedQuoting"),
  "e-unknown": (P, "    if ((d == CH_UPPER_Q) || (d == CH_UPPER_E)) {", "    if (d == CH_UPPER_Q) {"),
  "declined-in-class": (P, "        drop class_add(out, cf, n, at, p.c.pos, AFTER_CLASS);\n        pass NIL;\n    }\n    pass raw escape_refused(pat, at);",
                           "        drop class_add(out, cf, n, at, p.c.pos, AFTER_CLASS);\n        pass NIL;\n    }\n"
                           "    PatternError?:dd = raw declined_escape(at, d);\n    if (dd != NIL) { pass dd; }\n    pass raw escape_refused(pat, at);"),
  # step 3 -- `\g`
  "g-unknown": (P, "    if ((raw is_digit(d)) || (d == CH_LOWER_K) || (d == CH_LOWER_G)) {", "    if ((raw is_digit(d)) || (d == CH_LOWER_K)) {"),
  "g-call-as-backref": (P, "        if ((n == CH_LT) || (n == CH_QUOTE)) {", "        if (false) {"),
  # step 4 -- `regex_escape`: a byte it leaves bare, a form it writes, a text it misreads
  "esc-no-dot": (P, "    if ((b == CH_BACKSLASH) || (b == CH_DOT) || (b == CH_PLUS)", "    if ((b == CH_BACKSLASH) || (b == CH_PLUS)"),
  "esc-no-hash": (P, "(b == CH_DOLLAR) || (b == CH_HASH)) { pass true; }", "(b == CH_DOLLAR)) { pass true; }"),
  "esc-no-space": (P, "    if ((b == CH_AMP) || (b == CH_MINUS) || (b == CH_TILDE)) { pass true; }\n    pass raw is_space(b);",
                      "    if ((b == CH_AMP) || (b == CH_MINUS) || (b == CH_TILDE)) { pass true; }\n    pass false;"),
  "esc-no-minus": (P, "    if ((b == CH_AMP) || (b == CH_MINUS) || (b == CH_TILDE)) { pass true; }", "    if ((b == CH_AMP) || (b == CH_TILDE)) { pass true; }"),
  "esc-no-rbracket": (P, "(b == CH_LBRACKET) || (b == CH_RBRACKET)) { pass true; }", "(b == CH_LBRACKET)) { pass true; }"),
  "esc-no-amp": (P, "    if ((b == CH_AMP) || (b == CH_MINUS) || (b == CH_TILDE)) { pass true; }", "    if ((b == CH_MINUS) || (b == CH_TILDE)) { pass true; }"),
  "esc-no-tilde": (P, "    if ((b == CH_AMP) || (b == CH_MINUS) || (b == CH_TILDE)) { pass true; }", "    if ((b == CH_AMP) || (b == CH_MINUS)) { pass true; }"),
  "esc-no-wide": (P, "            if (raw is_wide_space(cp)) {\n                drop bytes_extend_str(@b,", "            if (false) {\n                drop bytes_extend_str(@b,"),
  "esc-decodes-ill-formed": (P, "        else if (((c => int64) >= U8_CONT_LO) && (bad == NIL)) {", "        else if ((c => int64) >= U8_CONT_LO) {"),
  "esc-angle": (P, "    if ((b == CH_AMP) || (b == CH_MINUS) || (b == CH_TILDE)) { pass true; }", "    if ((b == CH_AMP) || (b == CH_MINUS) || (b == CH_TILDE) || (b == CH_LT)) { pass true; }"),
  "esc-padded-hex": (P, "                drop hex(@b, cp, 1i64);", "                drop hex(@b, cp, 4i64);"),
  "esc-extra": (P, "    if ((b == CH_AMP) || (b == CH_MINUS) || (b == CH_TILDE)) { pass true; }", "    if ((b == CH_AMP) || (b == CH_MINUS) || (b == CH_TILDE) || (b == CH_COLON)) { pass true; }"),
  "esc-ill-formed-unescaped": (P, "        if (raw is_escaped(c)) {\n            drop bytes_push(@b, CH_BACKSLASH =>! uint8);",
                                  "        if ((raw is_escaped(c)) && (bad == NIL)) {\n            drop bytes_push(@b, CH_BACKSLASH =>! uint8);"),
  # step 5 -- the sentences: a branch lost, and a word K-1 forbids
  "text-supported": (E, "drop put(@b, \": nregex does not know this property.\");", "drop put(@b, \": nregex does not support this property.\");"),
  "octal-generic": (E, "            else if ((e.detail >= OCTAL_FIRST) && (e.detail <= OCTAL_LAST)) {", "            else if (false) {"),
  "r-generic": (E, "            if (e.detail == 82u32) {\n                drop put(@b, \": `(?R)`", "            if (false) {\n                drop put(@b, \": `(?R)`"),
  "z-reads-g": (E, "            if (e.detail == 90u32) {\n                drop put(@b, \"anchor", "            if (false) {\n                drop put(@b, \"anchor"),
  "e-reads-q": (E, "            if (e.detail == 69u32) {\n                drop put(@b, \"quotation end", "            if (false) {\n                drop put(@b, \"quotation end"),
  "block-unknown": (E, "            if (e.detail == 4u32) {\n                drop put(@b, \"Unicode block", "            if (false) {\n                drop put(@b, \"Unicode block"),
  # step 6 -- a `{` after `\b`
  "wordb-detail-zero": (P, "            if (target.kind == AstKind.WordBoundary) { why = 2u32; }", "            if (false) { why = 2u32; }"),
  "wordb-b-only": (P, "            if (target.kind == AstKind.WordBoundary) { why = 2u32; }", "            if ((target.kind == AstKind.WordBoundary) && (target.a == 0i64)) { why = 2u32; }"),
  "wordb-any-atom": (P, "            if (target.kind == AstKind.WordBoundary) { why = 2u32; }", "            if (true) { why = 2u32; }"),
  "wordb-text-generic": (E, "            else if (e.detail == 2u32) {\n                drop put(@b, \": a `{` after", "            else if (false) {\n                drop put(@b, \": a `{` after"),
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

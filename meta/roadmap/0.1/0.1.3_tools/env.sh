# meta/roadmap/0.1/0.1.3_tools/env.sh -- sourced at the top of EVERY command block of
# `0.1.3.md`, because a Bash call keeps no variables and no functions from the call
# before it. Set REPO first, to the dispatch's REPO line:
#
#     REPO=<the dispatch's REPO>; . "$REPO/meta/roadmap/0.1/0.1.3_tools/env.sh"
#
# 0.1.2's helpers this plan uses -- `codes`, `harness`, `ctl`, `run4`, `nrcheck` -- and this
# subcycle's `mutant`: a unit built against `parse.npk` with one named rule broken, which
# must exit with the case written for that rule. `$NPK_TREE` is read with `git` read
# commands only. Every `rm` names its target through `${VAR:?}`. Nothing prints a path
# above the repository, so no output carries a home directory into a record.
#
# THE WORKBENCH IS `$REPO/..`, as for every plan before this one, unless `PLAN_WB` names
# it -- which only a rehearsal in a clone outside the workbench does (the plan's §9).
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
T=$REPO/meta/roadmap/0.1/0.1.3_tools        # these tools
A=$REPO/.internal/n13                         # gitignored scratch
export NPKC NPKRT NPKC_950BB1D                 # the harness reads them from the ENVIRONMENT
# The harness's scratch is `tempfile`'s, so `TMPDIR` decides where it is; since cycle 0.1.2
# (RX-195) it may sit anywhere. Every block runs with it unset -- `/tmp` -- as 0.1.2's did.
unset TMPDIR
mkdir -p "$A"

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

# One rule of the class parser broken in a copy of the working tree's `parse.npk`, and the
# named units built against it at -O0 and run: each must exit with the case written for that
# rule. The table names each mutation by the rule it breaks; its old text must occur in
# `parse.npk` exactly once, or the helper says so and runs nothing.
#     mutant <name> <unit>...      (a unit is a file under tests/unit/, without `.npk`)
mutant() {
  local name=$1; shift
  ctl "mut_$name"
  python3 -B - "$A/ctl/mut_$name/src/syntax/parse.npk" "$name" <<'PY' || return 0
import sys
p, name = sys.argv[1], sys.argv[2]
M = {
  # class_close: the last operator need not have a member after it
  "close-no-right": ("    if (cf.expr != AST_NONE) {\n        if (cf.count == 0i64) {",
                     "    if (cf.expr != AST_NONE) {\n        if (cf.count == -1i64) {"),
  # class_op: an operator need not have a member before it
  "op-no-left": ("    if (cf.count == 0i64) {\n        pass raw pattern_error(PatternErrorKind.ClassOpMismatch, at, 2i64, b =>! uint32);",
                 "    if (cf.count == -1i64) {\n        pass raw pattern_error(PatternErrorKind.ClassOpMismatch, at, 2i64, b =>! uint32);"),
  # class_start: a first `]` is a member, but never remembered as one
  "no-lead": ("        cf.lead = true;\n", "        cf.lead = false;\n"),
  # class_start: a first `]` is no member -- it closes the class
  "no-lead-member": ("    if (raw cursor_peek(@p.c) == CH_RBRACKET) {\n        int64:at = p.c.pos;",
                     "    if (raw cursor_peek(@p.c) == -7i32) {\n        int64:at = p.c.pos;"),
  # posix_class: any name is a POSIX class
  "posix-any": ("    if (k == AST_NONE) {\n        pass raw pattern_error(PatternErrorKind.UnknownPosixClass, at, p.c.pos - at, 0u32);",
                "    if (k == -5i64) {\n        pass raw pattern_error(PatternErrorKind.UnknownPosixClass, at, p.c.pos - at, 0u32);"),
  # a class before a `-` given the detail of a range ending below its start
  "class-dash-0": ("                e = raw pattern_error(PatternErrorKind.BadClassRange, x.pos, p.c.pos - x.pos, 1u32);",
                   "                e = raw pattern_error(PatternErrorKind.BadClassRange, x.pos, p.c.pos - x.pos, 0u32);"),
  # class_range: an end below its start is accepted
  "range-any": ("    if (hi < lo.a) {", "    if (hi < 0i64) {"),
  # read_property: empty braces accepted
  "prop-empty": ("        if (empty) {", "        if (empty && false) {"),
  # class_fold: the operators folded the other way round, the newest union on the left
  "fold-right": ("cf.expr, u, cf.op, x.pos, cf.uend - x.pos", "u, cf.expr, cf.op, x.pos, cf.uend - x.pos"),
  # class_range: a `-` after a range may start another range
  "range-then-dash": ("    cf.uend = p.c.pos;\n    cf.after = AFTER_START;\n    pass NIL;\n};",
                      "    cf.uend = p.c.pos;\n    cf.after = AFTER_ONE;\n    pass NIL;\n};"),
  # parse_class: a nested `[` counts the groups around it and not the classes
  "class-depth-off": ("            else if ((p.stack.count + p.classes.count + 1i64) >= NREGEX_NEST_DEPTH) {",
                      "            else if ((p.stack.count + 1i64) >= NREGEX_NEST_DEPTH) {"),
  # parse_class: the outermost `[` is not checked against the groups around it
  "class-outer-depth-off": ("    if (p.stack.count >= NREGEX_NEST_DEPTH) {\n        pass raw pattern_error(PatternErrorKind.NestTooDeep, open, 1i64, NREGEX_NEST_DEPTH =>! uint32);\n    }\n    ClassFrame:cf",
                            "    if (p.stack.count >= 99999i64) {\n        pass raw pattern_error(PatternErrorKind.NestTooDeep, open, 1i64, NREGEX_NEST_DEPTH =>! uint32);\n    }\n    ClassFrame:cf"),
  # parse_class: a `-` the pattern ends on, after a class, is a bad range rather than an unclosed class
  "dash-at-end": ("\n                 && ((raw cursor_peek(@p.c)) != CURSOR_END)) {", ") {"),
  # escape: outside a class, every Perl class or property read as `\d`
  "outside-as-d": ("        drop atom_node(out, @p.f, raw escape_class_node(pat, p.f.flags, at, d, p.c.pos));",
                   "        drop atom_node(out, @p.f, raw escape_class_node(pat, p.f.flags, at, CH_LOWER_D, p.c.pos));"),
  # posix_alone: never asked
  "alone-off": ("                PatternError?:alone = raw posix_alone(pat, out, cf, p.c.pos);\n                if (alone != NIL) { pass alone; }\n", ""),
  # posix_alone: a `^` after the first `:` read as part of the name
  "alone-no-caret": ("    if ((pat[name] => int32) == CH_CARET) { name = name + 1i64; }",
                     "    if ((pat[name] => int32) == -9i32) { name = name + 1i64; }"),
  # posix_alone: a negated class's `^` read as its first member
  "alone-no-neg": ("    if (cf.neg != 0u32) { lo = lo + 1i64; }", "    if (cf.neg == 7u32) { lo = lo + 1i64; }"),
  # posix_alone: a class of colons alone refused too
  "alone-colons": ("    bool:other = false;", "    bool:other = true;"),
  # posix_alone: a member not written as itself -- a range, an escape, a class -- counted as one that is
  "alone-written": ("        if (x.len != raw utf8_len(pat[x.pos] => int64)) { pass NIL; }",
                    "        if (x.len < 0i64) { pass NIL; }"),
  # posix_alone: a member written as itself only when it is one byte
  "alone-one-byte": ("        if (x.len != raw utf8_len(pat[x.pos] => int64)) { pass NIL; }",
                     "        if (x.len != 1i64) { pass NIL; }"),
}
old, new = M[name]
s = open(p, encoding="utf-8").read()
if s.count(old) != 1:
    print(f"{name}: its old text occurs {s.count(old)} times in parse.npk -- nothing run")
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

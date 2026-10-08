# meta/roadmap/0.1/0.1.6a_tools/facts.sh -- `0.1.6a.md` §1: re-derive §1 at the pin, in scratch copies of the tree,
# never in it. Sourced after `env.sh`, in one Bash call -- block 0b, run BEFORE step 1:
#
#     . "$REPO/meta/roadmap/0.1/0.1.6a_tools/env.sh"; . "$T/facts.sh"
#
# It copies the working tree four ways under `$A/facts`: `head`, as it stands; `one`, with step 1's patch; `two`,
# with steps 1 and 2; `three`, with steps 1, 2 and 3 -- each patch applied by GNU `patch` to the copy alone, since
# `git apply` run inside this checkout would resolve the paths against the checkout, not the copy. Then it asks
# each copy's parser, through `fields.py`'s probe, what §1 says it answers; and the pinned compiler what §1.7 says
# it admits. The copies are removed at the end.
: "${REPO:?}" "${NPKC:?}" "${NPKRT:?}" "${A:?}" "${T:?}"
F=$A/facts; rm -rf "${F:?}"; mkdir -p "$F"
DAY=$(cat "$A/date" 2>/dev/null || date +%F)
fresh() {   # fresh <name> [<step>...]: the working tree as it stands at $F/<name>, then each step's patch
  local d=$1 n; shift
  mkdir -p "$F/$d"
  ( cd "$REPO" && git ls-files -co --exclude-standard -z | xargs -0 tar -cf - ) | tar -xf - -C "$F/$d"
  for n in "$@"; do
    sed "s/@@DATE@@/$DAY/g" "$T/step$n.patch" | patch -p1 -s --no-backup-if-mismatch -d "$F/$d" \
      || echo "STOP: step$n does not apply to a copy of the tree"
  done
}
fresh head; fresh one 1; fresh two 1 2; fresh three 1 2 3

# ---- §1.2 `regex_escape`'s text straight after a `[` (C1, C2), before step 1 and after it
python3 -B "$T/fields.py" "$F/head" c1 "§1.2 HEAD: "
python3 -B "$T/fields.py" "$F/head" names "§1.2 HEAD: "
python3 -B "$T/fields.py" "$F/one" c1 "§1.2 step 1: "
python3 -B "$T/fields.py" "$F/one" names "§1.2 step 1: "
# ---- §1.3 what it cannot promise, after step 1 (K8)
python3 -B "$T/fields.py" "$F/one" k8 "§1.3 step 1: "
# ---- §1.4 a `{` after `\b` (C3), before step 2 and after it
python3 -B "$T/fields.py" "$F/head" c3+t "§1.4 HEAD: "
python3 -B "$T/fields.py" "$F/two" c3 "§1.4 step 2: "
# ---- §1.5 a head at the bound (K7), before step 3 and after it
python3 -B "$T/fields.py" "$F/head" k7+t "§1.5 HEAD: "
python3 -B "$T/fields.py" "$F/three" k7+t "§1.5 step 3: " | head -2
# ---- §1.6 `\K` and `\g`, in a class and out (C6, K1)
python3 -B "$T/fields.py" "$F/head" c6 "§1.6 HEAD: "
# ---- §1.7 a `Copy` struct with a pointer member, and a bare pointer as `T: Copy` (C7)
mkdir -p "$F/head/tests/c7"
for k in member bare; do
  if [ "$k" = member ]; then ty=P; decl='#[derive(Copy)]
struct:P = { int64:a; int64->:p; };'; else ty='int64->'; decl=''; fi
  { printf 'mod:copy_%s;\n\nuse "../../src/core/core.npk".*;\n\n%s\n\nfunc:main = int32(cstring[]:_~argv) {\n' "$k" "$decl"
    printf '    Vec<%s>:v = raw vec_init::<%s>(4i64);\n    drop vec_free(@v);\n    exit 0i32;\n};\n\n' "$ty" "$ty"
    sed -n '/^func:failsafe/,$p' "$REPO/tests/unit/regex_escape.npk"; } > "$F/head/tests/c7/copy_$k.npk"
  echo "§1.7 $(codes $PIN "$F/head/tests/c7/copy_$k.npk")"
done
# ---- §1.8 the rows the audit read against the parser (K2, K3, K5, K6)
python3 -B "$T/fields.py" "$F/head" rows "§1.8 HEAD: "
rm -rf "${F:?}"

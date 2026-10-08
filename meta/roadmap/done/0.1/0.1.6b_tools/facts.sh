# meta/roadmap/0.1/0.1.6b_tools/facts.sh -- `0.1.6b.md` §1: re-derive §1 at the pin, in scratch copies of the tree,
# never in it. Sourced after `env.sh`, in one Bash call -- block 0b, run BEFORE step 1:
#
#     . "$REPO/meta/roadmap/0.1/0.1.6b_tools/env.sh"; . "$T/facts.sh"
#
# It copies the working tree under `$A/facts`: `head`, as it stands; `one`, `two` and `three`, with steps 1, 1-2 and
# 1-3 applied by GNU `patch` to the copy alone -- `git apply` run inside this checkout would resolve the paths against
# the checkout -- and `lit` and `num`, `head` with a bound planted in `src/core/bytes.npk`, a character literal and its
# decimal. Then it asks the copies' checks, the pinned compiler and the fuzz pass's counting twin what §1 says. A check
# is asked of its OWN tree's harness: a check reads its tree, and run from another tree's harness it reads the wrong
# one's exemptions. The copies are removed at the end.
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
fresh head; fresh one 1; fresh two 1 2; fresh three 1 2 3; fresh lit; fresh num

# ---- §1.2 the four kinds no pattern reaches, and the check that holds them (C4)
for k in EmptyClass RepeatProductTooLarge ClassTooLarge ProgramTooLarge; do
  echo "§1.2 PatternErrorKind.$k in src/, outside pattern_error_text's arm: $(grep -rn "PatternErrorKind\.$k" "$F/head/src" | grep -v 'pattern_error.npk:.*(PatternErrorKind\.'"$k"') {' | wc -l) site(s); in a unit: $(grep -rln "PatternErrorKind\.$k" "$F/head/tests/unit" | wc -l) file(s)"
done
echo "§1.2 the cycle README's 0.1.6 box names: $(grep -o '`EmptyClass`\|`ClassTooLarge`\|`RepeatProductTooLarge`\|`ProgramTooLarge`' <(grep -- '- \[ \] \*\*`check_error_kinds_tested` live' "$F/head/meta/roadmap/0.1/README.md") | sort -u | tr '\n' ' ')"
echo "§1.2 step 1's check over the tree: $(tcheck check_error_kinds_tested "$F/one" "$F/one")"
# ---- §1.3 a character literal at a comparison, and a literal behind a widening (C5)
printf '\npub func:zz_over = bool(int64:n) never fails {\n    pass n > (%s => int64);\n};\n' "'\\u{10000}'" >> "$F/lit/src/core/bytes.npk"
printf '\npub func:zz_over = bool(int64:n) never fails {\n    pass n > 65536i64;\n};\n' >> "$F/num/src/core/bytes.npk"
echo "§1.3 the plant, $(codes $PIN "$F/lit/src/core/bytes.npk")"
echo "§1.3 HEAD's check over the character literal: $(tcheck check_constants_named "$F/lit" "$F/head" | head -1)"
echo "§1.3 HEAD's check over its decimal: $(tcheck check_constants_named "$F/num" "$F/head" | head -1)"
echo "§1.3 step 2's check over the character literal:"; tcheck check_constants_named "$F/lit" "$F/two" | cut -c1-140
mkdir -p "$F/head/tests/c5"
{ printf 'mod:charval;\n\nfunc:main = int32(cstring[]:_~argv) {\n'
  printf '    if ((%s => int64) != 65536i64) { exit 10i32; }\n    exit 0i32;\n};\n' "'\\u{10000}'"
  sed -n '/^func:failsafe/,$p' "$REPO/tests/unit/regex_escape.npk"; } > "$F/head/tests/c5/charval.npk"
echo "§1.3 $(run4 "$F/head/tests/c5/charval.npk")"
echo "§1.3 lexer.npk at $PIN imports: $(git -C "$NPK_TREE" show $PIN:src/frontend/lexer.npk | grep -oE '^use "./(numeric|num_width|escapes)\.npk"' | sed 's/^use //' | tr '\n' ' ')"
echo "§1.3 numeric.npk and num_width.npk changed from c970483 to $PIN: $(git -C "$NPK_TREE" diff --stat c970483 $PIN -- src/frontend/numeric.npk src/frontend/num_width.npk | wc -l) line(s) of diffstat"
echo "§1.3 BUILD.md B-4e names numeric.npk or num_width.npk: $(grep -c 'numeric\.npk\|num_width\.npk' "$F/head/meta/specs/BUILD.md") time(s)"
# ---- §1.4 the fuzz pass, as step 3 writes it: what it accepts, refuses and meets (K6)
sed -e 's/^mod:parse_fuzz;/mod:fuzz_count;/' \
    -e 's/^    if (accepted < ACCEPTED_FLOOR) { pass 16i32; }/    int32:zz = raw say(`accepted \&{accepted} refused \&{refused}`);\n    int64:q = 0i64;\n    while (q < 64i64) decreases 64i64 - q {\n        if (met[q] == 1u8) { zz = raw say(`kind \&{q}`); }\n        q = q + 1i64;\n    }\n    if (accepted < ACCEPTED_FLOOR) { pass 16i32; }/' \
    -e 's/^func:run = int32() never fails {/func:say = int32(string:line) never fails {\n    Result<cstring>:c = to_cstring(string_concat(line, "\\n"));\n    if (c.is_error) { pass 20i32; }\n    cstring:s = move(c.value);\n    Result<int64>:w = sys(1i64, 1i64, s.ptr, s.len);\n    if (w.is_error) { pass 21i32; }\n    pass 0i32;\n};\n\nfunc:run = int32() never fails {/' \
    "$F/three/tests/unit/parse_fuzz.npk" > "$F/three/tests/unit/fuzz_count.npk"
( cd "$F/three/tests/unit" && "$NPKC" fuzz_count.npk -o "$F/fc.ll" ) > "$F/fc.npkc" 2>&1 || echo "§1.4 the counting twin did not compile: $(grep -oE '^NITPICK-[A-Z]+-[0-9]+' "$F/fc.npkc" | head -3 | tr '\n' ' ')"
llc -O0 -filetype=obj -relocation-model=static "$F/fc.ll" -o "$F/fc.o" && ld.lld -static "$F/fc.o" "$NPKRT" -o "$F/fc"
"$F/fc" > "$F/fc.out"; echo "§1.4 the counting twin exits $?: $(grep '^accepted' "$F/fc.out")"
python3 -B - "$F/three" "$F/fc.out" <<'PY'
import re, sys
text = open(sys.argv[1] + "/src/syntax/pattern_error.npk", encoding="utf-8").read()
body = re.sub(r"//[^\n]*", "", re.search(r"pub enum:PatternErrorKind = \{([^}]*)\}", text).group(1))
kinds = [k.strip() for k in body.split(";") if k.strip()]
met = [int(l.split()[1]) for l in open(sys.argv[2]) if l.startswith("kind ")]
print("§1.4 kinds met: %d of %d; not met: %s" % (len(met), len(kinds), ", ".join(k for i, k in enumerate(kinds) if i not in met)))
PY
rm -rf "${F:?}"

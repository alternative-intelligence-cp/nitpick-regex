#!/usr/bin/env bash
#
# rx120.sh -- THE RX-120 EXPIRY, ASSERTED RATHER THAN TRANSCRIBED.
#
# WHY THIS FILE REPLACED A TRANSCRIPT. `RX120.txt` recorded the numbers beside
# the commands that produced them, and the cycle 0.0 audit found that one of
# those commands COULD NOT HAVE PRODUCED THE OUTPUT BESIDE IT: section E called
# `harness.irscan.kernel_call_edges`, a function that exists nowhere in this
# tree, and run verbatim it raises AttributeError and exits 1. The conclusion
# was sound and the evidence for it was fabricated -- in the section being
# propagated to four sibling repositories as current fact. Two smaller faults in
# the same file pointed the same way: a decisive `diff` consumed two `.undef`
# files that no shown command created, and one line showed `npkc -o X` while
# annotating it as a stdout redirect, which are alternatives rather than the
# same thing.
#
# A HAND-COPIED TRANSCRIPT CANNOT BE WRONG IN A WAY ANYTHING NOTICES. This can:
# it CREATES every intermediate it later consumes, and it ASSERTS the three
# numbers instead of printing them, so the next re-pin that moves the prelude
# reddens a run instead of silently invalidating a committed sentence. The
# narrative keeps its value and keeps its place beside this file; it no longer
# stands in for it.
#
# WHAT IT ASSERTS, at the working pin:
#   floor      == 2 undefined symbols  (npk_dalloc, npk_ofd_close)
#   syscaller  == 3
#   difference == exactly {npk_sys6}
# and at the superseded pin `950bb1d`, if that compiler is present:
#   floor == syscaller == 29, difference EMPTY, and npk_sys6 IN THE FLOOR
# which is RX-120 as originally measured, and the control that makes the expiry
# a demonstration rather than an argument between two dated claims.
#
# THE HISTORICAL LEG SKIPS RATHER THAN FAILS WHEN `950bb1d` IS ABSENT, and that
# is deliberate: the old compiler lives in the workbench's gitignored toolchain
# directory and is not on a CI runner. A leg that failed there would make CI red
# for a missing artefact rather than for a moved measurement, and a check that
# is red for the wrong reason gets switched off. It says SKIPPED in capitals so
# that "did not apply" never reads like "passed".
#
# EXIT: 0 all asserted legs held; 1 an assertion failed; 2 the environment is
# not usable (no npkc, no llvm-nm) -- which is `npkc`'s own alphabet, where 2
# means "could not proceed and judged nothing".
#
# USAGE
#     NPKC=... harness/baseline/rx120.sh
#     NPKC_950BB1D=... harness/baseline/rx120.sh     # adds the historical leg
# With neither set, both are looked for under ../.internal/toolchain/<pin>/,
# which is where the workbench keeps them.
set -u

PIN=3d15ac9
OLD_PIN=950bb1d
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/../.." && pwd)"
work="$root/.internal/rx120"
tc="$root/../.internal/toolchain"

npkc="${NPKC:-$tc/$PIN/npkc}"
npkc_old="${NPKC_950BB1D:-$tc/$OLD_PIN/npkc}"

fail=0
note() { printf '%s\n' "$*"; }
bad()  { printf 'FAIL  %s\n' "$*"; fail=1; }

# `$?` IS CAPTURED ON THE LINE AFTER THE COMMAND AND NEVER THROUGH A PIPELINE.
# After a pipeline `$?` is the LAST FILTER's status, and this ecosystem has
# shipped a whole sweep on that bug.
run() {
    "$@" > "$work/.out" 2> "$work/.err"
    rc=$?
    if [ "$rc" -ne 0 ]; then
        bad "exit=$rc from: $*"
        head -5 "$work/.err" >&2
    fi
    return $rc
}

if [ ! -x "$npkc" ]; then
    note "rx120: no npkc at $npkc -- nothing was judged."
    exit 2
fi
if ! command -v llvm-nm > /dev/null 2>&1 || ! command -v llc > /dev/null 2>&1; then
    note "rx120: llc or llvm-nm is not on PATH -- nothing was judged."
    exit 2
fi

rm -rf "$work"
mkdir -p "$work" || exit 2

note "rx120: pin $PIN"
note "rx120: sha256(npkc) = $(sha256sum "$npkc" | cut -d' ' -f1)"

# `npkc -o X` WRITES THE FILE AND LEAVES STDOUT EMPTY. The two forms are
# alternatives; RX120.txt's line 45 showed one and annotated the other, and this
# is the one that is true.
undef_of() {
    # undef_of <src.npk> <name> <npkc>  ->  writes $work/<name>.undef, sorted
    local src="$1" name="$2" cc="$3"
    run "$cc" "$root/$src" -o "$work/$name.ll"       || return 1
    run llc -O0 -filetype=obj -relocation-model=static \
        "$work/$name.ll" -o "$work/$name.o"          || return 1
    llvm-nm --undefined-only "$work/$name.o" > "$work/$name.raw"
    rc=$?
    [ "$rc" -eq 0 ] || { bad "llvm-nm exit=$rc on $name.o"; return 1; }
    awk '{ print $NF }' "$work/$name.raw" | sort > "$work/$name.undef"
    return 0
}

expect_count() {
    # expect_count <name> <want>
    local got
    got=$(wc -l < "$work/$1.undef")
    got=$((got))
    if [ "$got" -ne "$2" ]; then
        bad "$1: $got undefined symbol(s), expected $2"
        cat "$work/$1.undef" >&2
    else
        note "ok    $1: $got undefined symbol(s)"
    fi
}

# ---- A and B: the floor and a syscaller, at the working pin -----------------
undef_of harness/baseline/baseline.npk         floor "$npkc"
undef_of harness/selfcheck/syscall_consumer.npk sys  "$npkc"

if [ -s "$work/floor.undef" ] && [ -s "$work/sys.undef" ]; then
    expect_count floor 2
    expect_count sys   3

    # ---- C: the difference IS the whole claim ------------------------------
    # The expected name is a VARIABLE used by both the test and the message, so
    # the two cannot disagree -- which is the failure mode this whole file
    # exists to answer.
    want_diff=npk_sys6
    diff_out=$(comm -13 "$work/floor.undef" "$work/sys.undef")
    if [ "$diff_out" = "$want_diff" ]; then
        note "ok    syscaller - floor == {$want_diff}"
    else
        bad "syscaller - floor == {$(echo $diff_out)}, expected {$want_diff}"
    fi
    # And nothing the other way: the floor must be a SUBSET, or the two
    # programs differ for a reason this file is not measuring.
    only_floor=$(comm -23 "$work/floor.undef" "$work/sys.undef")
    if [ -n "$only_floor" ]; then
        bad "floor - syscaller == {$(echo $only_floor)}, expected empty"
    else
        note "ok    floor - syscaller == {} (the floor is a subset)"
    fi
    # npk_sys6 MUST NOT be in the floor at this pin. That is the whole mechanism  # check_dated_measurements: exempt
    # -- D-262 stopped emitting an unreferenced prelude item -- and it is the
    # property that would silently come back.
    if grep -qx npk_sys6 "$work/floor.undef"; then
        bad "npk_sys6 IS in the floor at $PIN: the prelude emits it again, RX-120's original finding is back, and B-2's first layer is blind to syscalls once more. The call-edge layer is unaffected (that is B-2a's point) but this assertion and the three above are now measuring the OLD compiler's behaviour."
    else
        note "ok    npk_sys6 is NOT in the floor at $PIN"
    fi
fi

# ---- D: the historical control, at the superseded pin -----------------------
if [ -x "$npkc_old" ]; then
    note "rx120: control pin $OLD_PIN"
    note "rx120: sha256(npkc_$OLD_PIN) = $(sha256sum "$npkc_old" | cut -d' ' -f1)"
    undef_of harness/baseline/baseline.npk          floor_old "$npkc_old"
    undef_of harness/selfcheck/syscall_consumer.npk sys_old   "$npkc_old"
    if [ -s "$work/floor_old.undef" ] && [ -s "$work/sys_old.undef" ]; then
        expect_count floor_old 29
        expect_count sys_old   29
        if cmp -s "$work/floor_old.undef" "$work/sys_old.undef"; then
            note "ok    $OLD_PIN: the two symbol sets are IDENTICAL -- RX-120 as measured"
        else
            bad "$OLD_PIN: the two symbol sets DIFFER; RX-120's original measurement does not reproduce"
        fi
        if grep -qx npk_sys6 "$work/floor_old.undef"; then
            note "ok    $OLD_PIN: npk_sys6 is IN THE FLOOR -- the mechanism"
        else
            bad "$OLD_PIN: npk_sys6 is not in the floor; the expiry's explanation does not hold"
        fi
    fi
else
    note "SKIPPED  the $OLD_PIN control: no compiler at $npkc_old."
    note "         The working-pin assertions above still ran and still hold."
    note "         THIS IS NOT A PASS OF THAT LEG. It is the leg not applying,"
    note "         which reads exactly like a pass unless it says so."
fi

# ---- E: what does NOT expire, and it is checked rather than asserted --------
#
# The symbol layer answers "does this object need a kernel symbol". The
# call-edge layer answers "WHICH FUNCTION CALLS IT", no symbol set has ever been
# able to answer that, and the answer does not depend on what the prelude emits.
# So a future prelude carrying npk_sys6 again blinds the first layer and leaves
# this one exactly as strong. Rule B-2a keeps both.
#
# The check below is that `harness.irscan` still offers the entry points B-2a's
# second layer is built on. RX120.txt named `kernel_call_edges` here, which has
# never existed; these two do, and the run asserts it rather than printing a
# list for a reader to compare by eye.
python3 - "$root" <<'PY'
import sys, importlib.util
root = sys.argv[1]
spec = importlib.util.spec_from_file_location("irscan", root + "/harness/irscan.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
missing = [n for n in ("edges", "scan", "DENIED") if not hasattr(m, n)]
if missing:
    print("FAIL  harness/irscan.py is missing %s -- B-2's second layer is not "
          "there to survive the first one's expiry" % ", ".join(missing))
    sys.exit(1)
print("ok    harness/irscan.py offers edges, scan and DENIED "
      "(B-2a's second layer, which no prelude change can blind)")
PY
rc=$?
[ "$rc" -eq 0 ] || fail=1

if [ "$fail" -ne 0 ]; then
    note ""
    note "rx120: FAILED. A number above moved. That is a PRELUDE change and not"
    note "       a library change -- read harness/baseline/RX120.txt for what the"
    note "       numbers mean, decide whether B-2's first layer still sees a"
    note "       syscall at the new pin, and re-record this file's expectations"
    note "       as a deliberate act reviewed on its own."
    exit 1
fi
note "rx120: every asserted leg held."
exit 0

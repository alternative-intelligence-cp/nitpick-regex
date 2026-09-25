#!/usr/bin/env python3
"""A test's expectations, read from the test file -- `BUILD.md` rule B-5.

MARKER FOR MARKER WITH THE COMPILER'S, AND IN ITS DISPATCH ORDER, because the
day this harness retires into `npkg` (RX-004, O-G3) a parity stage diffs the
two runners' verdicts and a grammar that drifted makes every row a false
difference. The source is `npkg/expect.npk` at 950bb1d, function `expect_read`:

  * a line whose STRIPPED form starts with `//`; the body is the rest, stripped;
  * the body dispatched on its prefix, first match winning;
  * `expect-error-at: L[:C]` moves the LAST `expect-error`;
  * `expect-exit: N` -- LAST ONE WINS, default 0;
  * `stress: N` -- default 1;
  * `argv: TOK ...` -- whitespace split;
  * a number that cannot be read makes the expectations UNREADABLE, with the
    line, and an unreadable test is a FAILING test, never a silently defaulted
    one.

Note two things that grammar implies and a reader will not expect. The marker
is recognised only at the START of the comment body, so `// see `expect-exit: 94``
is prose and not an expectation -- which is what keeps `probe08b`'s and
`probe08c`'s explanatory comments from being read as second expectations. And
the value is the WHOLE rest of the line, so `// expect-exit: 94 -- the
OutOfBounds arm` is UNREADABLE rather than 94: `npkg`'s `text_int` refuses a
trailing word, and a test whose expectation cannot be read is a failing test.

THE TWO PLACES THIS DELIBERATELY DIVERGES, and both are refusals of an
expectation that cannot be met rather than a different judgement of one that
can. FIRST: AN EXIT STATUS IS ONE BYTE. A process that exits 321
reports 65 -- 321 mod 256 -- and nothing in the compiler's reader says so, so
`// expect-exit: 321` there is an expectation that can never be met and never
be explained. Here it is refused, by name, at read time. Nothing in this
ecosystem carries a value above 255 today (swept 2026-09-04), so this refuses
no test that exists; it refuses the one somebody writes next.

Negative values keep `npkg`'s meaning and are not refused: `run_binary` reports
a killed process as `0 - signal`, so `expect-exit: -11` is "killed by SIGSEGV".
Below -64 there is no such signal on Linux, so that is refused too.

THIRD, AND IT IS AN ADDITION RATHER THAN A DIVERGENCE: `mem-cap-mib: N`.
`npkg`'s grammar has no such marker and this one is `nregex`'s own, declared
here so the parity stage that retires this runner has a row for it rather than
a surprise. It exists because `SAFETY.md` §8b (S-22) makes half of this
library's memory obligations INVISIBLE TO `exit 0`: D-151 counts `wild` blocks,
D-188 counts live drivers, and neither sees a managed body, so a container
freed without dropping its owning elements exits 0 while retaining every one of
them. Where the obligation is managed the gate is a MEMORY CAP, and a marker is
how a file asks for one.

`run_binary` applies it as an RLIMIT_AS to the child, and **runs `/bin/true`
under the identical cap first, requiring it to succeed**. That control is not
politeness: a low address-space cap measures the DYNAMIC LOADER rather than the
program, and this ecosystem has already shipped an acceptance item asserting
that a probe "finishes clean in under 768 KiB of address space" when `/bin/true`
does not either -- both flip at the same cap, between 2688 and 2816 KiB. A cap
a trivial program also fails is not a statement about your program, so the
control turns that warning into a mechanism.

FOURTH, ALSO AN ADDITION: `pending-until: <commit> exit <N>`. `npkg` has no
such marker either. It exists for the case cycle 0.0.5 met head-on -- **a test
that is CORRECT and RED, because the defect it asserts against lives in the
pinned compiler and is already fixed in a commit this repository has not pinned
yet.** The three wrong answers available were to weaken the test, to guard
around the compiler defect in library code (which `CLAUDE.md`'s last
non-negotiable rule forbids by name), and to not write the test until the
re-pin -- which is how a defect gets forgotten between the day it is understood
and the day it could be caught.

**A PENDING UNIT IS BUILT AND RUN LIKE ANY OTHER AND ITS ACTUAL EXIT IS
PRINTED** -- on EVERY leg, at -O0 and through `opt -O2`, `stress` times each,
since RX-159 (the fourth cycle-0.0 audit's N-19: it had been observed once, at
-O0 only). It is counted as neither a pass nor a failure, exactly as
`selfcheck.py`'s pending cases are (P-18): *a pending case is not a passing
case*, and a denominator that quietly absorbs one is a denominator that lies.

**THE MARKER EXCUSES THE FAILURE IT NAMES AND NO OTHER** (RX-154, `BUILD.md`
B-5b). It names the exit it is pending on, and a pending unit that gives any
other exit is a FAILURE -- rule B-7's reasoning applied to this marker: a unit
held only to "it failed" passes for the wrong reason. It goes RED, too, the day
it MEETS its expectation, and says to delete the marker. **And it takes a
reviewed line in `harness/baseline/PENDING.txt`**, checked both ways, so the
marker's one comment line cannot, alone, move a red out of a green run's
denominator. *(A `use` in a SIBLING's comment could, through the program
suites' skip, until RX-157 -- the fourth cycle-0.0 audit's BL-7.)*

**WHAT IS STILL KEYED ON THE EXIT ALONE (RX-159), stated so nobody assumes
more:** a code is an identity, not a cause. A unit pending on 92 is excused for
ANY `HeapOom` under its cap, and one pending on a trap's code for any trap of
that identity. Where the defect allows, a pending unit exits with a code of its
own -- one only its own assertion can produce -- rather than a shared trap code.

**THE COMMIT IS A LABEL, AND NOTHING HERE READS IT.** It is checked for the
shape of a commit -- 7 to 40 lowercase hex digits -- and never resolved: this
runner has no compiler checkout to resolve it against, and W-18 and RX-007 keep
the compiler's tree out of it. It tells the human who moves the pin which fix
the unit waits on. UNTIL THE THIRD CYCLE-0.0 AUDIT (BL-6) THIS PARAGRAPH SAID
"the day the pin moves past the named commit, the harness itself says so, in
the run that moves it". Measured false: a marker naming a commit that does not
exist was accepted and behaved identically, because the retirement was keyed on
the exit alone -- which is still true, and is now the whole of the claim.

SECOND: `stress: 0`. Here the divergence is smaller and the reason is
different, and it is worth stating exactly because the first draft of this
comment got it wrong. `npkg` does NOT run the program zero times: `run_binary`
opens with `int64:runs = stress; if (runs < 1i64) { runs = 1i64; }`, so a zero
is SILENTLY CLAMPED to one run -- checked in the source, not assumed, after the
comment here had already claimed a hole that is not there. What is left is
still worth refusing: `stress: 0` is an expectation the runner rewrites rather
than honours, and a marker whose meaning is quietly changed is the thing this
grammar exists to prevent. So it is refused by name here and it is not a defect
there.
"""

import re

EXIT_MAX = 255
SIGNAL_MIN = -64
# A commit's SHAPE, never its existence (RX-154): see the fourth marker above.
_COMMIT = re.compile(r"^[0-9a-f]{7,40}$")


class Expect:
    def __init__(self):
        self.errors = []        # list of dicts: code, line, col  (-1 = any)
        self.notes = []
        self.exit_code = 0
        self.stress = 1
        self.argv = []
        self.mem_cap_mib = 0    # 0 = uncapped. `mem-cap-mib: N` sets it.
        self.pending_until = ""   # a compiler commit, as a LABEL: never resolved (RX-154)
        self.pending_exit = None  # the exit the unit is pending on; any other fails it
        self.pending_line = 0
        self.no_parse_error = False
        self.ok = True
        self.bad_line = 0
        self.bad_why = ""

    def codes(self):
        return sorted({e["code"] for e in self.errors})


def _after_colon(body):
    i = body.find(":")
    if i < 0:
        return ""
    return body[i + 1:].strip()


def _int(s):
    """`npkg`'s `text_int`: optional sign, then digits only, at most 18 of them."""
    t = s.strip()
    if not t:
        return None
    i = 0
    neg = False
    if t[0] == "-":
        neg, i = True, 1
    elif t[0] == "+":
        i = 1
    if i >= len(t) or len(t) - i > 18:
        return None
    if not t[i:].isdigit() or not t[i:].isascii():
        return None
    v = int(t[i:])
    return -v if neg else v


def _at(loc):
    """`L[:C]`; None when a number cannot be read."""
    if ":" in loc:
        ln, cl = loc.split(":", 1)
    else:
        ln, cl = loc, ""
    l = _int(ln)
    if l is None:
        return None
    if not cl.strip():
        return (l, -1)
    c = _int(cl)
    if c is None:
        return None
    return (l, c)


def read(text):
    e = Expect()
    for n, raw in enumerate(text.split("\n"), 1):
        s = raw.strip()
        if not s.startswith("//"):
            continue
        body = s[2:].strip()

        if body.startswith("expect-error-at:"):
            a = _at(_after_colon(body))
            if a is None:
                return _bad(e, n, "an `expect-error-at:` whose number cannot be read")
            if e.errors:
                e.errors[-1]["line"], e.errors[-1]["col"] = a
            continue
        if body.startswith("expect-error:"):
            e.errors.append({"code": _after_colon(body), "line": -1, "col": -1})
            continue
        if body.startswith("expect-note-at:"):
            a = _at(_after_colon(body))
            if a is None:
                return _bad(e, n, "an `expect-note-at:` whose number cannot be read")
            if e.notes:
                e.notes[-1]["line"], e.notes[-1]["col"] = a
            continue
        if body.startswith("expect-note:"):
            e.notes.append({"code": _after_colon(body), "line": -1, "col": -1})
            continue
        if body.startswith("expect-exit:"):
            v = _int(_after_colon(body))
            if v is None:
                return _bad(e, n, "an `expect-exit:` whose number cannot be read")
            if v > EXIT_MAX:
                return _bad(e, n, f"`expect-exit: {v}` -- AN EXIT STATUS IS ONE BYTE. "
                                  f"A process exiting {v} reports {v % 256}, silently, "
                                  "and no run could ever satisfy this. Compose weights "
                                  "that cannot sum past 255, or print the value and "
                                  "assert on stdout")
            if v < SIGNAL_MIN:
                return _bad(e, n, f"`expect-exit: {v}` -- a negative expectation means "
                                  f"`0 - signal`, and there is no signal {-v}")
            e.exit_code = v
            continue
        if body.startswith("stress:"):
            v = _int(_after_colon(body))
            if v is None:
                return _bad(e, n, "a `stress:` whose number cannot be read")
            if v < 1:
                return _bad(e, n, f"`stress: {v}` -- a run count below one is not a run")
            e.stress = v
            continue
        if body.startswith("mem-cap-mib:"):
            v = _int(_after_colon(body))
            if v is None:
                return _bad(e, n, "a `mem-cap-mib:` whose number cannot be read")
            if v < 1:
                return _bad(e, n, f"`mem-cap-mib: {v}` -- a cap below one MiB cannot "
                                  f"load a process at all, so it would measure the "
                                  f"dynamic loader rather than the program")
            e.mem_cap_mib = v
            continue
        if body.startswith("pending-until:"):
            toks = _after_colon(body).split()
            if (len(toks) != 3 or toks[1] != "exit"
                    or not _COMMIT.match(toks[0]) or _int(toks[2]) is None):
                return _bad(e, n, "a `pending-until:` that is not `pending-until: "
                                  "<commit> exit <N>` -- 7 to 40 lowercase hex digits, "
                                  "the word `exit`, and the exit the unit is pending "
                                  "on. The marker EXCUSES A RED, so it must name WHICH "
                                  "red: a marker excusing any exit is the one that "
                                  "absorbed a failure it did not name (RX-154)")
            v = _int(toks[2])
            if v > EXIT_MAX or v < SIGNAL_MIN:
                return _bad(e, n, f"`pending-until: ... exit {v}` -- no process can "
                                  f"exit {v}, so the marker could never match")
            e.pending_until = toks[0]
            e.pending_exit = v
            e.pending_line = n
            continue

        if body.startswith("argv:"):
            e.argv = _after_colon(body).split()
            continue
        if body.startswith("expect-no-parse-error"):
            e.no_parse_error = True
            continue
    # Checked after every line is read, because `expect-exit:` is LAST ONE WINS
    # and may come after the marker.
    if e.pending_until and e.pending_exit == e.exit_code:
        return _bad(e, e.pending_line,
                    f"a `pending-until:` pending on exit {e.pending_exit}, which is "
                    f"the exit the file EXPECTS -- a marker that excuses the "
                    f"passing answer excuses nothing and would hide the pass")
    return e


def _bad(e, line, why):
    e.ok = False
    e.bad_line = line
    e.bad_why = why
    return e


def unreadable_message(name, e):
    return f"{name}: line {e.bad_line}: {e.bad_why}"

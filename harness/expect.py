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

EXIT_MAX = 255
SIGNAL_MIN = -64


class Expect:
    def __init__(self):
        self.errors = []        # list of dicts: code, line, col  (-1 = any)
        self.notes = []
        self.exit_code = 0
        self.stress = 1
        self.argv = []
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
        if body.startswith("argv:"):
            e.argv = _after_colon(body).split()
            continue
        if body.startswith("expect-no-parse-error"):
            e.no_parse_error = True
            continue
    return e


def _bad(e, line, why):
    e.ok = False
    e.bad_line = line
    e.bad_why = why
    return e


def unreadable_message(name, e):
    return f"{name}: line {e.bad_line}: {e.bad_why}"

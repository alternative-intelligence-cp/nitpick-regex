#!/usr/bin/env python3
"""THE HARNESS'S ONE READING OF NITPICK SOURCE -- RX-157.

Every place in this harness that reads `.npk` text as code reads it through this
module: the program suites' "imported by a sibling" skip (`stages.py`), the B-2
scans' "does this program reach `src/`" (`build.reaches_src`), and every tree
check (`treecheck.py`). Until the fourth cycle-0.0 audit there were THREE import
readers and a fourth blanker, and they disagreed: two matched only `use "` and
missed `pub use`, one matched both, and NONE of them skipped a comment or a
string -- so a `/* */` block naming a red unit took it out of a GREEN run's
denominator (`173/173`, exit 0; BL-7), while the compiler, reading the same
file, saw no import at all. And the one blanker handled only `"`, so a `'"'`
character literal earlier on a line hid the rest of that line from every check
built on it (N-18's M12). ONE reading means one place to be wrong and one place
to fix it, which is the argument this repository already made about `vec_oob`.

WHAT IT MIRRORS, READ AT COMPILER `c3bdae2` WITH `git show`, NOT FROM A SUMMARY:
`src/frontend/lexer.npk`, `lexer_skip_trivia` and `lexer_next`, and
`LEXICAL_REFERENCE.md` §2, §6.3 and §6.4.

  * `//` runs to the end of the line.
  * `/* ... */` does NOT NEST: the first `*/` closes it, and an unterminated one
    runs to the end of the file (the lexer's own comment says nesting is a
    decision to preserve, because it would let an unterminated comment swallow
    the file silently).
  * `"..."`: `\\` skips the byte after it; a NEWLINE ends the literal (the
    lexer's "newline in a string literal", which stops there rather than
    swallowing the file).
  * `""` followed by anything but `"` is an EMPTY string; `\"\"\"` opens a BLOCK
    string, which closes at the first `""` not escaped by `\\` and consumes
    three quotes there.
  * `r"..."` is RAW -- no escapes, closed by the next `"` -- when the `r` BEGINS
    A TOKEN, i.e. the byte before it is not `[0-9A-Za-z_]` (otherwise `r` is the
    tail of an identifier or a numeric literal, and the `"` opens a plain one).
  * `'x'`: a `\\` escape (`\\xHH`, `\\u{...}`, or one byte) or ONE code point,
    then `'`. Without the closing quote the lexer resyncs past the next `'` on
    the line, or to the line's end, and so does this.
  * `` `...` ``: a TEMPLATE. Its text is literal and is not trivia -- a `//` in it
    is text -- and `&{` opens an interpolation that is CODE until the `}` that
    closes it at the brace depth it opened at. Templates nest through their
    interpolations.

WHAT IT IS NOT: a lexer. It finds the spans that are not code and nothing else.
`spans()` returns them; `blank()` replaces each with spaces, keeping every
newline, so a check's line and column numbers are the file's own; `imports()`
reads `use` declarations the way the parser does (`p_parse_import`, the same
file): the keyword, then a plain string literal (`StringLit` -- a raw or block
string is not a path), with `pub` before it when it re-exports.

ITS OWN TEST IS SELF-CHECK CASE 18, which feeds it one text holding every form
above and requires exactly the imports the compiler would read.
"""
import re

_IDENT = frozenset("abcdefghijklmnopqrstuvwxyz"
                   "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")

# A `use` KEYWORD in blanked code: not the tail of an identifier, not a field
# (`x.use` -- a reserved word IS accepted as a field name, RX-134), and not the
# head of a longer identifier.
_USE_KW = re.compile(r"(?<![A-Za-z0-9_.])use(?![A-Za-z0-9_])")
# `pub`, then any of the declaration modifiers `p_at_decl_start` accepts
# between it and the keyword, then the end of the text before `use`.
_PUB_BEFORE = re.compile(
    r"(?<![A-Za-z0-9_.])pub(?:\s+(?:inline|noinline|comptime|async|thread))*\s*$")
_MAIN = re.compile(r"(?<![A-Za-z0-9_.])func\s*:\s*main(?![A-Za-z0-9_])\s*=")


def spans(text):
    """Every comment and every literal, as `(kind, start, end)`, end exclusive.

    Kinds: `comment`, `string` (a plain `"..."`, which is the only kind a `use`
    may name), `raw`, `block`, `char`, `template` (a template's text and its
    backticks -- never its interpolations, which are code)."""
    out = []
    n = len(text)
    i = 0
    in_template = False
    interp = []            # the brace depth at each open `&{` -- the lexer's `interp_brace`
    brace = 0
    while i < n:
        if in_template:
            s = i
            while i < n and text[i] != "`" and not (
                    text[i] == "&" and i + 1 < n and text[i + 1] == "{"):
                i += 1
            if i >= n:
                out.append(("template", s, n))
                break
            if text[i] == "`":
                out.append(("template", s, i + 1))
                i += 1
                in_template = False
                continue
            if i > s:
                out.append(("template", s, i))
            i += 2                              # `&{` -- code from here
            in_template = False
            interp.append(brace)
            continue

        c = text[i]
        nx = text[i + 1] if i + 1 < n else ""
        if c == "/" and nx == "/":
            e = text.find("\n", i)
            e = n if e < 0 else e
            out.append(("comment", i, e))
            i = e
            continue
        if c == "/" and nx == "*":
            e = text.find("*/", i + 2)
            e = n if e < 0 else e + 2
            out.append(("comment", i, e))
            i = e
            continue
        if c == "}" and interp and brace == interp[-1]:
            interp.pop()                        # closes an interpolation: text again
            i += 1
            in_template = True
            continue
        if c == "{":
            brace += 1
            i += 1
            continue
        if c == "}":
            brace -= 1
            i += 1
            continue
        if c == "`":
            out.append(("template", i, i + 1))
            i += 1
            in_template = True
            continue
        if c == "r" and nx == '"' and (i == 0 or text[i - 1] not in _IDENT):
            e = text.find('"', i + 2)
            e = n if e < 0 else e + 1
            out.append(("raw", i, e))
            i = e
            continue
        if c == '"':
            if nx == '"':
                if i + 2 < n and text[i + 2] == '"':
                    j = i + 3
                    while j < n:
                        if text[j] == '"' and j + 1 < n and text[j + 1] == '"':
                            break
                        if text[j] == "\\":
                            j += 1
                        j += 1
                    e = min(n, j + 3)
                    out.append(("block", i, e))
                    i = e
                    continue
                out.append(("string", i, i + 2))      # `""`, the empty string
                i += 2
                continue
            j = i + 1
            while j < n:
                if text[j] == "\n":
                    break                             # the lexer stops the literal here
                if text[j] == '"':
                    j += 1
                    break
                if text[j] == "\\":
                    j += 1
                j += 1
            e = min(n, j)
            out.append(("string", i, e))
            i = e
            continue
        if c == "'":
            j = i + 1
            if j < n and text[j] == "\\":
                if j + 1 < n and text[j + 1] == "x":
                    j += 4
                elif j + 2 < n and text[j + 1] == "u" and text[j + 2] == "{":
                    k = text.find("}", j + 3)
                    j = n if k < 0 else k + 1
                else:
                    j += 2
            elif j < n:
                j += 1                                # ONE code point
            if j < n and text[j] == "'":
                e = j + 1
            else:
                e = j                                 # the lexer's resync
                while e < n and text[e] != "\n":
                    if text[e] == "'":
                        e += 1
                        break
                    e += 1
            e = min(n, e)
            out.append(("char", i, e))
            i = e
            continue
        i += 1
    return out


def blank(text, sp=None):
    """The text with every comment and literal replaced by spaces, NEWLINES KEPT,
    so offsets, lines and columns are the file's own. Interpolations stay: they
    are code, and a `/` in one arms `DivByZero` like any other."""
    chars = list(text)
    for _, s, e in (spans(text) if sp is None else sp):
        for k in range(s, e):
            if chars[k] != "\n":
                chars[k] = " "
    return "".join(chars)


def imports(text):
    """Every `use` declaration the compiler would read: `[(line, target, pub)]`.

    `target` is the string literal's text, not decoded -- nothing here writes an
    escape into a path. A `use` inside a comment, a string or a template is not
    code and is not an import, which is the whole of BL-7."""
    sp = spans(text)
    code = blank(text, sp)
    trivia = {s: e for k, s, e in sp if k == "comment"}
    plain = {s: e for k, s, e in sp if k == "string"}
    out = []
    n = len(text)
    for m in _USE_KW.finditer(code):
        j = m.end()
        while j < n:
            if text[j] in " \t\r\n":
                j += 1
            elif j in trivia:
                j = trivia[j]
            else:
                break
        if j not in plain:
            continue                          # a logical path (`use std.x.*;`), or not an import
        target = text[j + 1:plain[j] - 1]
        if not target:
            continue
        pub = _PUB_BEFORE.search(code, 0, m.start()) is not None
        out.append((text.count("\n", 0, m.start()) + 1, target, pub))
    return out


def declares_main(text):
    """Does this file declare `func:main`? Read from code, never from prose."""
    return _MAIN.search(blank(text)) is not None

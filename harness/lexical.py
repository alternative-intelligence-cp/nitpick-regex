#!/usr/bin/env python3
"""THE HARNESS'S ONE READING OF NITPICK SOURCE -- RX-157, AS AMENDED BY RX-165.

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

AND IT WAS NOT THE COMPILER'S, IN TWO MEASURED WAYS -- the fifth cycle-0.0 audit's
BL-9, and RX-165. (a) Every caller read a file in Python's TEXT MODE, which turns a
lone carriage return into a line end before this module saw it; the compiler ends a
`//` comment at byte 10 only and treats byte 13 as whitespace. So after `// note<CR>`
what was still comment to the compiler was code here: a `use` there was a phantom
import, and a `/*` there blanked the rest of the file -- together `209/209` GREEN over
a red unit, and one more CR cleared an owning field in a `src/` `Vec` element. (b)
`imports()` returned a path's TEXT, while the compiler takes the string literal's
DECODED value, so `"..\\x2f..\\x2fsrc/core/zz.npk"` reached `src/` for the compiler and
nowhere for B-2's scans -- a syscall in `src/` behind `213/213` GREEN. Hence `read()`
below, the one way a `.npk` file is opened, and `_decode()`.

WHAT IT MIRRORS, READ AT COMPILER `c3bdae2` WITH `git show`, NOT FROM A SUMMARY
-- AND AGAIN AT `c970483` (cycle 0.0.4e), where `lexer.npk` differs only in the
block-string close below and `escapes.npk` and `p_parse_import` not at all:
`src/frontend/lexer.npk`, `lexer_skip_trivia` and `lexer_next`;
`src/frontend/escapes.npk`, `escape_decode` and `decode_string`; `p_parse_import` in
`src/frontend/parse_decl.npk`; and `LEXICAL_REFERENCE.md` §2, §6.3 and §6.4.

  * THE TEXT IS BYTES. `read()` maps each byte to one character (latin-1), so every
    offset here is the compiler's byte offset, `\\n` (byte 10) is the only line end,
    and nothing translates a CR (the lexer's own header: "The lexer works in BYTES").
    WHITESPACE is exactly the lexer's `is_space`: space, tab, CR and LF.

  * `//` runs to the end of the line.
  * `/* ... */` does NOT NEST: the first `*/` closes it, and an unterminated one
    runs to the end of the file (the lexer's own comment says nesting is a
    decision to preserve, because it would let an unterminated comment swallow
    the file silently).
  * `"..."`: `\\` skips the byte after it; a NEWLINE ends the literal (the
    lexer's "newline in a string literal", which stops there rather than
    swallowing the file).
  * `""` followed by anything but `"` is an EMPTY string; `\"\"\"` opens a BLOCK
    string, which closes at the first `\"\"\"` not escaped by `\\` -- a `""` in its
    body is two body characters -- and consumes those three. That is the lexer
    since the compiler's 1.6.0 step 3e (DEF-98), read at `c970483`, and
    `LEXICAL_REFERENCE.md` §6.3's grammar. THROUGH `c3bdae2` THE LEXER CLOSED AT
    THE FIRST `""` AND CONSUMED THREE BYTES THERE, AND SO DID THIS MODULE (RX-170):
    probe 15 records the verdict, and self-check case 18 holds a block string with
    a `""` in its body and a `use` after its close, and fails against the old close
    (the fifth audit's N-28).
  * `r"..."` is RAW -- no escapes, closed by the next `"` -- when the `r` BEGINS
    A TOKEN, i.e. the byte before it is not `[0-9A-Za-z_]` (otherwise `r` is the
    tail of an identifier or a numeric literal, and the `"` opens a plain one).
  * `'x'`: a `\\` escape (`\\xHH`, `\\u{...}`, or one byte) or ONE code point,
    then `'`. Without the closing quote the lexer resyncs past the next `'` on
    the line, or to the line's end, and so does this. Read as bytes, a code point
    of two to four bytes is that many characters here, and the resync reaches the
    same closing quote the lexer's `utf8_decode` does -- no continuation byte is a
    quote -- so the span is the lexer's for every literal the compiler accepts.
  * `` `...` ``: a TEMPLATE. Its text is literal and is not trivia -- a `//` in it
    is text -- and `&{` opens an interpolation that is CODE until the `}` that
    closes it at the brace depth it opened at. Templates nest through their
    interpolations.

WHAT IT IS NOT: a lexer. It finds the spans that are not code and nothing else.
`spans()` returns them; `blank()` replaces each with spaces, keeping every
newline, so a check's line and column numbers are the file's own; `imports()`
reads `use` declarations the way the parser does (`p_parse_import`): the
keyword, then a plain string literal (`StringLit` -- a raw or block string is
not a path), with `pub` before it when it re-exports -- and the path is the
literal's DECODED value, by `escapes.npk`'s rules, as a filesystem path.

WHAT IT STILL DOES NOT MIRROR, stated rather than implied, and each confined to
files the compiler REFUSES -- which the `parse` sweep, judging every `.npk` in
the tree as a root, turns red whatever this module reads in them: a NUL byte
(the lexer's end-of-text sentinel); an interpolation nested more than eight deep;
`_?`, `_!`, `_~`, `_^` at the start of a template part; `e+r"` after a float; an
invalid escape or UTF-8 sequence; and a path that begins neither `./`, `../`
nor `/`, which the compiler resolves against the dependency roots -- empty at
`c3bdae2` and `c970483`, so `NITPICK-RESOLVE-005` (measured at both) -- while the harness's callers join
it to the importer's directory.

AND IT IS NOT THE ONLY DEFENCE. The program suites' "imported by a sibling" skip
also asks the COMPILER whether a candidate defines `main` (`stages.py`), so a
defect here that invents an import cannot take a program out of the count: the
two defences share no reader (RX-165).

ITS OWN TEST IS SELF-CHECK CASE 18, which writes one text holding every form
above to a FILE, reads it back through `read()`, and requires exactly the
imports and the code the compiler would see at `c970483`. Cases 19, 20 and 21
are BL-9's three routes through the whole runner.
"""
import os
import re

_IDENT = frozenset("abcdefghijklmnopqrstuvwxyz"
                   "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")
# The lexer's `is_space`, exactly: space, tab, carriage return, newline. Python's
# `\s` also matches VT, FF, 0x1C-0x1F, 0x85 and 0xA0, which the lexer calls
# unexpected characters.
_WS = " \t\r\n"


def read(path):
    """A `.npk` file's text AS THE COMPILER READS IT -- RX-165, BL-9 (a).

    BYTES, one character per byte (latin-1): every offset is the compiler's byte
    offset and no line end is translated, so `\\n` is the only one -- where
    Python's text mode (`newline=None`) had made a lone CR a line end and hidden
    code from every check behind it. THE ONE WAY THE HARNESS OPENS A `.npk` FILE:
    the skip, B-2's reach, the expectation markers and every tree check call this.
    Raises `OSError` like `open()`; the callers keep their own handling."""
    with open(path, "rb") as fh:
        return fh.read().decode("latin-1")


def _hex(c):
    """`hex_value` in `escapes.npk`: the digit's value, or -1."""
    if "0" <= c <= "9":
        return ord(c) - 48
    if "a" <= c <= "f":
        return ord(c) - 87
    if "A" <= c <= "F":
        return ord(c) - 55
    return -1


_SIMPLE_ESCAPES = {"n": 10, "r": 13, "t": 9, "\\": 92, '"': 34, "'": 39, "0": 0}


def _escape(s, at):
    """`escape_decode`: `(codepoint, bytes consumed)` for the escape at `s[at]`
    (a backslash), or None where the compiler's is invalid -- `LEX-BAD-ESCAPE`,
    and the file is refused."""
    if at + 1 >= len(s):
        return None
    e = s[at + 1]
    if e in _SIMPLE_ESCAPES:
        return _SIMPLE_ESCAPES[e], 2
    if e == "x":                               # \xHH -- exactly two
        if at + 3 >= len(s):
            return None
        h1, h2 = _hex(s[at + 2]), _hex(s[at + 3])
        if h1 < 0 or h2 < 0:
            return None
        return h1 * 16 + h2, 4
    if e == "u":                               # \u{...}
        if at + 2 >= len(s) or s[at + 2] != "{":
            return None
        i, acc, seen = at + 3, 0, False
        while i < len(s):
            if s[i] == "}":
                if not seen or acc > 0x10FFFF:
                    return None
                return acc, (i - at) + 1
            h = _hex(s[i])
            if h < 0:
                return None
            acc, seen, i = acc * 16 + h, True, i + 1
        return None                            # unterminated
    return None


def _decode(content):
    """`decode_string`: a plain literal's CONTENT (between its quotes, one
    character per source byte) to the BYTES of its value. An escape becomes its
    code point in UTF-8 -- `\\x2f` is `/`, and `\\xC3` is two bytes, U+00C3 --
    and an invalid one is skipped at its backslash, as the compiler does while
    refusing the file."""
    out = bytearray()
    i = 0
    while i < len(content):
        if content[i] == "\\":
            r = _escape(content, i)
            if r is None:
                i += 1
                continue
            out += chr(r[0]).encode("utf-8", "surrogatepass")
            i += r[1]
        else:
            out.append(ord(content[i]))
            i += 1
    return bytes(out)


# A `use` KEYWORD in blanked code: not the tail of an identifier, not a field
# (`x.use` -- a reserved word IS accepted as a field name, RX-134), and not the
# head of a longer identifier.
_USE_KW = re.compile(r"(?<![A-Za-z0-9_.])use(?![A-Za-z0-9_])")
# `pub`, then any of the declaration modifiers `p_parse_decl` accepts between
# it and the keyword, then the end of the text before `use`. Whitespace is the
# lexer's (`_WS`), never Python's `\s`.
_PUB_BEFORE = re.compile(
    r"(?<![A-Za-z0-9_.])pub(?:[ \t\r\n]+(?:inline|noinline|comptime|async|thread))*[ \t\r\n]*$")


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
                    # A BLOCK STRING CLOSES AT `"""` (DEF-98, the compiler's 1.6.0
                    # step 3e; RX-170) -- through `c3bdae2` at the first `""`.
                    j = i + 3
                    while j < n:
                        if (text[j] == '"' and j + 2 < n and text[j + 1] == '"'
                                and text[j + 2] == '"'):
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

    `text` is what `read()` returns. `target` is the string literal's DECODED
    value, as a filesystem path -- `os.fsdecode` of the bytes `_decode` gives,
    which is the path the compiler's `p_parse_import` takes (RX-165). Until the
    fifth cycle-0.0 audit this returned the literal's TEXT, and its docstring said
    "nothing here writes an escape into a path": a statement about the tree
    standing where a check belonged (BL-9 (b)). A `use` inside a comment, a string
    or a template is not code and is not an import, which is the whole of BL-7."""
    sp = spans(text)
    code = blank(text, sp)
    trivia = {s: e for k, s, e in sp if k == "comment"}
    plain = {s: e for k, s, e in sp if k == "string"}
    out = []
    n = len(text)
    for m in _USE_KW.finditer(code):
        j = m.end()
        while j < n:
            if text[j] in _WS:
                j += 1
            elif j in trivia:
                j = trivia[j]
            else:
                break
        if j not in plain:
            continue                          # a logical path (`use std.x.*;`), or not an import
        target = os.fsdecode(_decode(text[j + 1:plain[j] - 1]))
        if not target:
            continue
        pub = _PUB_BEFORE.search(code, 0, m.start()) is not None
        out.append((text.count("\n", 0, m.start()) + 1, target, pub))
    return out

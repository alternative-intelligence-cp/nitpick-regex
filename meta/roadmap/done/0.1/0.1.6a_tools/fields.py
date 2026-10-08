#!/usr/bin/env python3
"""What the parser answers for each of a list of patterns, in a tree -- `0.1.6a.md` §1's re-derivation.

    python3 -B fields.py <tree> <case-list> [<label-prefix>]

Writes one program into `<tree>/tests/`, which parses each case through that tree's `syntax.npk` and prints its
answer; builds it with `$NPKC` at -O0, links it against `$NPKRT`, runs it, and prints each answer with its kind and
its node kinds by name, read from the tree's own `pattern_error.npk` and `ast.npk`. A case is a pattern written as
bytes, or a pattern built in the program as a prefix, `regex_escape(text)` and a suffix -- so the composition is the
library's, not this script's. Removes the program and its build after the run. Prints nothing above the tree."""
import os, re, subprocess, sys

CASES = {
    # §1.2 -- `regex_escape`'s text straight after a `[` (C1, C2); §1.3 -- what it cannot promise (K8)
    "c1": [("esc", "[a[", ":alpha:", "]]"), ("esc", "[\\\\w--[", ":digit:", "]]"), ("esc", "[[", ":^space:", "]]"),
           ("esc", "[", ":a:", "]"), ("esc", "[", ":alpha:", "]"), ("esc", "(?x)[a[", ":word:", "]]")],
    "k8": [("esc", "\\\\0", "1", ""), ("esc", "[", "", "]"), ("long", "", "", "")],
    # §1.4 -- a `{` after `\b` (C3)
    "c3": [("raw", b"\\b{start}"), ("raw", b"\\b{,3}"), ("raw", b"\\b{ 3}"), ("raw", b"\\B{,2}"), ("raw", b"\\b{"),
           ("raw", b"\\b{x3}"), ("raw", b"a{,3}")],
    # §1.5 -- 250 groups, then a head the `(` begins (K7)
    "k7": [("deep", "(?i)", "", ""), ("deep", "(?#c)", "", ""), ("deep", "(?:a)", "", "")],
    # §1.6 -- `\K` and `\g` in a class and out (C6, K1)
    "c6": [("raw", b"\\K"), ("raw", b"[\\K]"), ("raw", b"[\\g]")],
    # §1.8 -- the rows the audit read against the parser (K2, K3, K5, K6)
    "rows": [("raw", b"(?i"), ("raw", b"(?"), ("raw", b"\\u{41}"), ("raw", b"\xc3\x00"), ("raw", b"\xc3"),
             ("raw", b"(?<")],
}

# §1.2's census -- §5.1's fourteen names as `:name:` and `:^name:` straight after a nested class's `[`, and as
# `:name:` straight after the outermost one, each counted by what the parser makes of it
POSIX = ["alpha", "digit", "alnum", "space", "upper", "lower", "punct", "print", "graph", "cntrl", "xdigit",
         "blank", "word", "ascii"]
CASES["names"] = ([("esc", "[[", ":%s:" % n, "]]") for n in POSIX] + [("esc", "[[", ":^%s:" % n, "]]") for n in POSIX]
                  + [("esc", "[", ":%s:" % n, "]") for n in POSIX])
CENSUS = (("`[[` + regex_escape(\":name:\") + `]]`", 0), ("`[[` + regex_escape(\":^name:\") + `]]`", 14),
          ("`[` + regex_escape(\":name:\") + `]`", 28))


def enum(tree, rel, name):
    text = open(os.path.join(tree, rel), encoding="utf-8").read()
    m = re.search(r"pub enum:" + name + r" = \{([^}]*)\}", text)
    body = re.sub(r"//[^\n]*", "", m.group(1))
    return [x.strip() for x in body.split(";") if x.strip()]

def nstr(s):
    return '"' + s.replace("\\\\", "\\\\") + '"'

def program(cases):
    out = ['mod:fields_probe;\n\nuse "../src/core/core.npk".*;\nuse "../src/syntax/syntax.npk".*;\n', """
func:say = int32(string:line) never fails {
    Result<cstring>:c = to_cstring(string_concat(line, "\\n"));
    if (c.is_error) { pass 20i32; }
    cstring:s = move(c.value);
    Result<int64>:w = sys(1i64, 1i64, s.ptr, s.len);
    if (w.is_error) { pass 21i32; }
    pass 0i32;
};

func:show = int32(int64:label, uint8[]:pat) never fails {
    Ast:t = raw ast_init(8i64);
    PatternError?:r = raw parse_pattern(pat, @t);
    int32:z = 0i32;
    if (r == NIL) {
        int64:n = raw ast_len(t);
        z = raw say(`&{label} NIL &{t.root} &{n}`);
        int64:i = 0i64;
        while (i < n) decreases n - i {
            AstNode:x = raw ast_get(t, i);
            int64:k = (x.kind =>! int32) => int64;
            z = raw say(`&{label} node &{i} &{k} &{x.a} &{x.b} &{x.c} &{x.next}`);
            i = i + 1i64;
        }
    } else {
        PatternError:e = r ?? raw pattern_error(PatternErrorKind.PatternTooLong, 0i64, 0i64, 0u32);
        int64:k = (e.kind =>! int32) => int64;
        int64:d = e.detail => int64;
        z = raw say(`&{label} ERR &{k} &{e.offset} &{e.span_len} &{d} &{pat.len}`);
        z = raw say(string_concat(`&{label} TEXT `, raw pattern_error_text(e)));
    }
    drop ast_free(@t);
    pass z;
};

func:built = string(string:pre, string:text, string:post) never fails {
    Bytes:b = raw bytes_init(64i64);
    drop bytes_extend_str(@b, pre);
    drop bytes_extend_str(@b, raw regex_escape(text));
    drop bytes_extend_str(@b, post);
    pass raw bytes_copy_string(@b);
};

func:main = int32(cstring[]:_~argv) {
    int32:z = 0i32;
"""]
    for i, c in enumerate(cases):
        if c[0] == "raw":
            b = c[1]
            arr = ", ".join(f"{x}u8" for x in b)
            out.append(f"    uint8[{len(b)}]:p{i} = [{arr}];\n    z = raw show({i}i64, p{i}[0i64...{len(b)}i64]);\n")
        elif c[0] == "esc":
            out.append(f"    string:s{i} = raw built({nstr(c[1])}, {nstr(c[2])}, {nstr(c[3])});\n"
                       f"    z = raw show({i}i64, string_bytes(s{i}));\n")
        elif c[0] == "long":
            # a text of 65 537 bytes, every one `.`, which `regex_escape` doubles: the pattern passes the bound
            out.append(f"    Bytes:lb{i} = raw bytes_init(65600i64);\n    int64:li{i} = 0i64;\n"
                       f"    while (li{i} < 65537i64) decreases 65537i64 - li{i} {{\n"
                       f"        drop bytes_push(@lb{i}, 46u8);\n        li{i} = li{i} + 1i64;\n    }}\n"
                       f"    string:ls{i} = raw bytes_copy_string(@lb{i});\n"
                       f"    string:s{i} = raw built(\"\", ls{i}, \"\");\n    z = raw show({i}i64, string_bytes(s{i}));\n")
        elif c[0] == "deep":
            out.append(f"    Bytes:db{i} = raw bytes_init(260i64);\n    int64:di{i} = 0i64;\n"
                       f"    while (di{i} < 250i64) decreases 250i64 - di{i} {{\n"
                       f"        drop bytes_extend_str(@db{i}, \"(\");\n        di{i} = di{i} + 1i64;\n    }}\n"
                       f"    drop bytes_extend_str(@db{i}, {nstr(c[1])});\n"
                       f"    string:s{i} = raw bytes_copy_string(@db{i});\n    z = raw show({i}i64, string_bytes(s{i}));\n")
    out.append("""    exit 0i32;
};

func:failsafe = int32(Error:e) {
    pick (e) {
        (HeapBadRequest)    { exit 91i32; },
        (HeapOom)           { exit 92i32; },
        (IntOverflow)       { exit 93i32; },
        (OutOfBounds)       { exit 94i32; },
        (Unreachable)       { exit 95i32; },
        (WildLeak)          { exit 96i32; },
        (StackExhausted)    { exit 106i32; },
        (MachineFault)      { exit 107i32; },
        (DecreasesViolated) { exit 108i32; },
        (LimitViolated)     { exit 109i32; },
        (ShiftRange)        { exit 115i32; },
        (*)                 { exit 99i32; }
    }
    exit 9i32;
};
""")
    return "".join(out)

def shown(c):
    if c[0] == "raw":
        return "".join(chr(x) if 32 <= x < 127 else "\\x%02X" % x for x in c[1])
    if c[0] == "esc":
        return "%s + regex_escape(%r) + %s" % (c[1].replace("\\\\", "\\"), c[2], c[3])
    if c[0] == "long":
        return "regex_escape(65 537 dots)"
    return "250 `(` then %s" % c[1]

def tree_text(nodes, i, kinds, posix):
    k, a, b, c, nx = nodes[i]
    name = kinds[k]
    if name == "ClassRange":
        return "'%s'" % chr(a) if a == b else "'%s'-'%s'" % (chr(a), chr(b))
    if name == "PosixClass":
        return "[:%s:]" % posix[a]
    if name == "PerlClass":
        return "\\" + "dws"[a]
    if name in ("Class", "Concat", "Alternate"):
        kids, j = [], a
        for _ in range(b):
            kids.append(tree_text(nodes, j, kinds, posix))
            j = nodes[j][4]
        return "%s(%s)" % (name, ", ".join(kids))
    if name == "ClassOp":
        return "%s(%s, %s)" % (["&&", "--", "~~"][c], tree_text(nodes, a, kinds, posix), tree_text(nodes, b, kinds, posix))
    if name == "Literal":
        return "'%s'" % chr(a)
    if name == "Flags":
        return "Flags"
    return name

def main(tree, which, prefix=""):
    tree = os.path.realpath(tree)
    texts = which.endswith("+t")
    cases = CASES[which[:-2] if texts else which]
    kinds = enum(tree, "src/syntax/pattern_error.npk", "PatternErrorKind")
    nodek = enum(tree, "src/syntax/ast.npk", "AstKind")
    posix = ["alpha", "digit", "alnum", "space", "upper", "lower", "punct", "print", "graph", "cntrl", "xdigit",
             "blank", "word", "ascii"]
    d = os.path.join(tree, "tests")
    src = os.path.join(d, "fields_probe.npk")
    with open(src, "w", encoding="utf-8") as fh:
        fh.write(program(cases))
    npkc, npkrt = os.environ["NPKC"], os.environ["NPKRT"]
    base = os.path.join(d, "fields_probe")
    try:
        r = subprocess.run([npkc, "fields_probe.npk", "-o", base + ".ll"], cwd=d, capture_output=True, text=True)
        if r.returncode != 0:
            print(prefix + "the probe did not compile: " + " ".join(re.findall(r"NITPICK-[A-Z]+-\d+ \S+", r.stdout + r.stderr)[:4]))
            return
        subprocess.run(["llc", "-O0", "-filetype=obj", "-relocation-model=static", base + ".ll", "-o", base + ".o"], check=True)
        subprocess.run(["ld.lld", "-static", base + ".o", npkrt, "-o", base], check=True)
        run = subprocess.run([base], capture_output=True, text=True)
        rows = {}
        for line in run.stdout.splitlines():
            f = line.split(" ")
            rows.setdefault(int(f[0]), []).append(f[1:])
        if which == "names":
            for label, start in CENSUS:
                tally = {}
                for i in range(start, start + 14):
                    head = rows.get(i, [["none"]])[0]
                    if head[0] == "ERR":
                        what = "refused %s" % kinds[int(head[1])]
                    else:
                        nodes = {int(r_[1]): tuple(int(x) for x in r_[2:7]) for r_ in rows[i][1:]}
                        t = tree_text(nodes, int(head[1]), nodek, posix)
                        what = "parse as the POSIX class" if "[:" in t else "parse as their codepoints"
                    tally[what] = tally.get(what, 0) + 1
                print(prefix + "%s, the fourteen names: %s" % (label, "; ".join("%d %s" % (n, w) for w, n in sorted(tally.items()))))
            return
        for i, c in enumerate(cases):
            got = rows.get(i, [])
            if not got:
                print(prefix + "%s: no answer" % shown(c)); continue
            head = got[0]
            if head[0] == "ERR":
                k, off, span, det, ln = (int(x) for x in head[1:6])
                print(prefix + "%s: %s at %d, length %d, detail %d (a %d-byte pattern)" % (shown(c), kinds[k], off, span, det, ln))
                if texts:
                    t = [" ".join(r_[1:]) for r_ in got if r_[0] == "TEXT"]
                    print(prefix + "  it reads: " + (t[0] if t else "(nothing)"))
            else:
                root = int(head[1])
                nodes = {}
                for r_ in got[1:]:
                    nodes[int(r_[1])] = tuple(int(x) for x in r_[2:7])
                print(prefix + "%s: parses -- %s" % (shown(c), tree_text(nodes, root, nodek, posix)))
        if run.returncode != 0:
            print(prefix + "the probe exited %d" % run.returncode)
    finally:
        for ext in ("", ".ll", ".o", ".npk"):
            try:
                os.remove(base + ext)
            except FileNotFoundError:
                pass

if __name__ == "__main__":
    main(*sys.argv[1:])

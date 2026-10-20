#!/usr/bin/env python3
"""0.2.6 -- F70's census, measured again for regex itself (step 7a, block 7c): the shapes the compiler's landing 128
(D-341, advance notice F70) moves, counted over every tracked `.npk` of a tree with its comments and strings blanked by
the tree's own `harness/lexical.py`, so a shape in a comment or a string counts nothing -- as F70's census read them
(the workbench board's entry for F70). F70's four for regex: `#ptr_add`, `#wild_slice`, `buffer->`, and a `buffer`
indexed like a slice; and its comparison counts beside them: `.ptr[`, `buffer_new` and `string_from_bytes`. A BUFFER
INDEX is a name a `buffer:` declaration declares, anywhere in the tree, written with `[` after it -- an upper bound, since
a name is not a type. The census prints each count beside F70's figure for regex, and says which differ; a difference is
a measurement for `0.3.0.md`'s gate, not a stop.

THE CONTROL plants each shape four times in one scratch file -- once in code, once in a comment, once in a string and
once inside a longer name -- and the census must count each exactly once.

    python3 -B census.py run <tree>
    python3 -B census.py control <tree>
"""
import os, re, shutil, subprocess, sys, tempfile

SHAPES = [("#ptr_add", re.compile(r"#ptr_add\b")),
          ("#wild_slice", re.compile(r"#wild_slice\b")),
          ("buffer->", re.compile(r"\bbuffer\s*->")),
          ("buffer index", None),
          (".ptr[", re.compile(r"\.ptr\s*\[")),
          ("buffer_new", re.compile(r"\bbuffer_new\b")),
          ("string_from_bytes", re.compile(r"\bstring_from_bytes\b"))]
F70 = {"#ptr_add": 1, "#wild_slice": 0, "buffer->": 0, "buffer index": 0, ".ptr[": 4, "buffer_new": 2,
       "string_from_bytes": 1}
DECL = re.compile(r"\bbuffer\s*:\s*([A-Za-z_]\w*)")
PLANT = """mod:planted;

func:p = int64(buffer:bb, buffer->:pb, uint8->:q) never fails {
    discard(#ptr_add<uint8>(q, 1i64));
    discard(#wild_slice<uint8>(q, 1i64));
    discard(bb[0i64]);
    discard(q.ptr[0i64]);
    discard(buffer_new(1i64));
    discard(string_from_bytes(q, 1i64));
    // #ptr_add #wild_slice buffer-> bb[1i64] x.ptr[1i64] buffer_new string_from_bytes
    discard("#ptr_add #wild_slice buffer-> bb[2i64] x.ptr[2i64] buffer_new string_from_bytes");
    discard(#ptr_add2 + #wild_slice2 + mybuffer->x + abb[3i64] + x.ptrs[3i64] + my_buffer_new + string_from_bytes2);
    pass 0i64;
};
"""


def _lexical(tree):
    sys.path.insert(0, os.path.join(os.path.realpath(tree), "harness"))
    import lexical
    return lexical


def count(lexical, paths, base):
    """{shape: {relative path: n}} over `paths`, comments and strings blanked; and the names `buffer:` declares."""
    code = {os.path.relpath(p, base): lexical.blank(lexical.read(p)) for p in paths}
    names = sorted({m.group(1) for t in code.values() for m in DECL.finditer(t)})
    index = re.compile(r"(?<![\w])(%s)\s*\[" % "|".join(map(re.escape, names))) if names else None
    out = {}
    for shape, pat in SHAPES:
        pat = index if shape == "buffer index" else pat
        out[shape] = {p: len(pat.findall(t)) for p, t in code.items()} if pat else {}
        out[shape] = {p: n for p, n in out[shape].items() if n}
    return out, names


def run(tree):
    tree = os.path.realpath(tree)
    rel = subprocess.run(["git", "-C", tree, "ls-files", "-z", "--", "*.npk"], capture_output=True, text=True,
                         check=True).stdout.split("\0")
    paths = [os.path.join(tree, r) for r in rel if r]
    got, names = count(_lexical(tree), paths, tree)
    print(f"census of {len(paths)} tracked .npk file(s), comments and strings blanked:")
    for shape, _ in SHAPES:
        n = sum(got[shape].values())
        where = ", ".join(f"{p} {k}" for p, k in sorted(got[shape].items()))
        if shape == "buffer index":
            where = " ".join(w for w in (where, f"(names a `buffer:` declares: {', '.join(names) or 'none'})") if w)
        print(f"  {shape:18} {n:3}  {where}".rstrip())
    differ = [f"{s} {sum(got[s].values())} where F70 counted {F70[s]}" for s, _ in SHAPES if sum(got[s].values()) != F70[s]]
    print("F70's figures for regex: " + ", ".join(f"{s} {F70[s]}" for s, _ in SHAPES) + " -- "
          + ("each held" if not differ else "differ: " + "; ".join(differ)))
    return 0


def control(tree):
    d = tempfile.mkdtemp(prefix="census-control-")
    try:
        p = os.path.join(d, "planted.npk")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(PLANT)
        got, _ = count(_lexical(tree), [p], d)
        ok = [s for s, _ in SHAPES if got[s] == {"planted.npk": 1}]
        bad = [f"{s} {sum(got[s].values())}" for s, _ in SHAPES if s not in ok]
        print(f"control: {len(ok)} of {len(SHAPES)} shapes counted once, in code, and not in a comment, a string or a "
              f"longer name" + ("" if not bad else " -- MISCOUNTED: " + ", ".join(bad)))
        return 0 if not bad else 1
    finally:
        shutil.rmtree(d)


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("run", "control"):
        print(__doc__)
        sys.exit(2)
    sys.exit((run if sys.argv[1] == "run" else control)(sys.argv[2]))

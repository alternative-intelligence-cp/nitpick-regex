#!/usr/bin/env python3
"""0.2.0 -- block 2's renderer check: what Markdown makes of the decision log, before and after step 2's four blank
lines, read by markdown-it -- the renderer cycle 0.1.6a's verifier found the swallowed paragraphs with.

    python3 -B render.py <repo>

1. EVERY tracked Markdown file, at HEAD and in the working tree: each paragraph inside a blockquote that holds a line
   not beginning `>` -- a lazy continuation (CommonMark §5.1), the shape that swallows a decision's first paragraph
   into the note above it. Their count and places.
2. `meta/DECISIONS.md` rendered whole at HEAD and in the working tree, cut at every `<h2>` and `<h3>`: how many
   sections, how many byte-identical, and which moved -- by their headings' first words.
3. For each section that moved, before and after: how its first blockquote ends, and how the paragraph after the
   blockquote begins.
4. The page's words, every tag stripped and white space folded, before and after: the same or not.
"""
import html
import re
import subprocess
import sys

import markdown_it
from markdown_it import MarkdownIt

MD = MarkdownIt("commonmark")


def lazy(text):
    lines = text.split("\n")
    depth, hits = 0, []
    for t in MD.parse(text):
        if t.type == "blockquote_open":
            depth += 1
        elif t.type == "blockquote_close":
            depth -= 1
        elif t.type == "paragraph_open" and depth > 0 and t.map:
            a, b = t.map
            bad = [i for i in range(a, b) if not lines[i].lstrip().startswith(">")]
            if bad:
                hits.append(bad[0] + 1)
    return hits


def sections(text):
    out = MD.render(text)
    parts = re.split(r"(?=<h[23]>)", out)
    keyed = []
    for p in parts:
        m = re.match(r"<h([23])>(.*?)</h\1>", p, re.S)
        key = "preamble" if not m else re.sub(r"<[^>]+>", "", m.group(2)).split(" — ")[0].strip()
        keyed.append((key, p))
    return keyed


def words(text):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", MD.render(text))).split())


def plain(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", s)).split())


def first(s, n=40):
    s = plain(s)
    return s[:n] + ("…" if len(s) > n else "")


def last(s, n=40):
    s = plain(s)
    return ("…" if len(s) > n else "") + s[-n:]


def main(argv):
    root = argv[1]
    git = lambda *a: subprocess.run(["git", "-C", root, *a], capture_output=True, text=True).stdout
    print("renderer: markdown-it-py %s, its CommonMark preset" % markdown_it.__version__)
    files = [f for f in git("ls-files", "*.md").split("\n") if f]
    for label, read in (("HEAD", lambda f: git("show", "HEAD:" + f)),
                        ("the working tree", lambda f: open(root + "/" + f, encoding="utf-8").read())):
        found = []
        for f in files:
            found += ["%s:%d" % (f, n) for n in lazy(read(f))]
        print("%s: %d paragraph(s) lazily continued into a blockquote, over %d tracked markdown file(s)%s"
              % (label, len(found), len(files), (": " + " ".join(found)) if found else ""))
    before = git("show", "HEAD:meta/DECISIONS.md")
    after = open(root + "/meta/DECISIONS.md", encoding="utf-8").read()
    b, a = sections(before), sections(after)
    if [k for k, _ in b] != [k for k, _ in a]:
        print("STOP: the sections differ in number or order")
        return 1
    moved = [k for (k, x), (_, y) in zip(b, a) if x != y]
    print("meta/DECISIONS.md: %d section(s) at each h2 and h3, %d byte-identical, %d moved: %s"
          % (len(b), len(b) - len(moved), len(moved), " ".join(moved)))
    for (k, x), (_, y) in zip(b, a):
        if x == y:
            continue
        for label, sec in (("before", x), ("after", y)):
            q = re.search(r"<blockquote>(.*?)</blockquote>(.*)", sec, re.S)
            inner = re.findall(r"<p>(.*?)</p>", q.group(1), re.S)
            nxt = re.search(r"<p>(.*?)</p>", q.group(2), re.S)
            print("  %s %s: the blockquote ends \"%s\"; the paragraph after it begins \"%s\""
                  % (k, label, last(inner[-1]), first(nxt.group(1)) if nxt else "(none)"))
    print("the page's words, before and after: %s" % ("the same" if words(before) == words(after) else "DIFFER"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

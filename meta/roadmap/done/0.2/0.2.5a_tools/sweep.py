#!/usr/bin/env python3
"""0.2.5a -- the omission sweep, block 5 (`../0.2.5_tools/sweep.py`, its pathspec this plan's), and its POSITIVE CONTROL.
A comparator proves the run equals the rehearsal and cannot see a hunk the rehearsal never wrote, so this reads the
committed tree for statements of what the steps moved. TWO READINGS of every pattern, because one line-based reading
cannot see a phrase a line break splits, and the joined reading cannot point at a line by itself:

  line    -- `git grep -n -I -i -E` at HEAD, line by line, case-insensitive
  joined  -- each tracked file read whole, each line's leading comment marker (`//`, `#`, `*`, `>`) stripped, the
             lines joined with spaces, and the pattern matched across them, case-insensitive; a hit is reported at
             the line it starts on

    python3 -B sweep.py <repo> <out-file> <pattern-file> [decisions]
    python3 -B sweep.py control <tools-dir> <pattern-file>

The pattern file holds one ERE per line (`#` lines are comments). The pathspec is fixed below: the live tree, history
excluded -- and `meta/DECISIONS.md` with it, unless the fourth argument is `decisions`, since a settled decision is
read with its dated notes, never rewritten. It prints one line per pattern -- `<n> line hits, <m> joined hits, <k>
joined-only` -- and writes every hit to <out-file> as `<pattern#> <reading> <path>:<line>: <text>`, which the worker
READS, every line. Only the counts are compared; the reading is the check.

THE CONTROL (the workbench `PLAYBOOK.md`'s rule that a stale-claim sweep's patterns get a positive control, the step's
own hunks; and its rule that a correction made by annotating a claim leaves the claim's twins invisible to a search for
removed lines). `control` reads every `step<N>.patch` beside it and, for each hunk, the patterns over two texts: the
lines the hunk REMOVES, joined -- the parent side -- and, for every dated note the hunk adds, the claim the note
annotates: the unchanged lines just above it, and the words it quotes, `*"…"*`, which name a claim that stands higher up.
Each prints with the numbers of the patterns that match it, or `NONE`: a hunk the sweep cannot see, which the plan names
by its kind, or the pattern list grows. And THE TWINS (plan verification 1's finding 5): `sweep_twins.txt` beside the
patches holds, for every claim step 1 dates, the claim written in other words, and each prints with the patterns that
see it by its subject, or `NONE` -- a subject no pattern catches without flooding the sweep, which the plan's §5b names
and leaves to the worker's second sweep by subject. Step 2 is the step whose notes date claims here, so the twins
are its claims' -- and step 1's one marker's.
"""
import bisect
import os
import re
import subprocess
import sys

# The plan and its tools are out: they are this subcycle's own text, its patches quote the old text beside the new,
# and its Expects quote these blocks' outputs -- a sweep that read them would read itself. The research digests are
# out as dated external records, as 0.1.6b's were; so are the earlier plans of this cycle, records now.
PATHSPEC = [".", ":!meta/roadmap/done", ":!meta/audits", ":!meta/research", ":!meta/roadmap/0.2/0.2.0.md",
            ":!meta/roadmap/0.2/0.2.0_tools", ":!meta/roadmap/0.2/0.2.1.md", ":!meta/roadmap/0.2/0.2.1_tools",
            ":!meta/roadmap/0.2/0.2.1a.md", ":!meta/roadmap/0.2/0.2.1a_tools", ":!meta/roadmap/0.2/0.2.2.md",
            ":!meta/roadmap/0.2/0.2.2_tools", ":!meta/roadmap/0.2/0.2.3.md", ":!meta/roadmap/0.2/0.2.3_tools",
            ":!meta/roadmap/0.2/0.2.4.md", ":!meta/roadmap/0.2/0.2.4_tools", ":!meta/roadmap/0.2/0.2.5.md",
            ":!meta/roadmap/0.2/0.2.5_tools", ":!meta/roadmap/0.2/0.2.5a.md", ":!meta/roadmap/0.2/0.2.5a_tools",
            ":!meta/scratch", ":!*TRANSCRIPT.txt"]
_MARK = re.compile(r"^\s*(?://+|#+|\*|>)?\s?")
_NOTE = "@@DATE025A@@, cycle 0.2.5a"
_QUOTE = re.compile(r'\*"([^"]+)"\*')


def git(root, *args):
    return subprocess.run(["git", "-C", root, *args], capture_output=True,
                          text=True, errors="replace").stdout


def patterns(patfile):
    return [l.rstrip("\n") for l in open(patfile, encoding="utf-8") if l.strip() and not l.startswith("#")]


def control(tools, patfile):
    pats = [re.compile(p, re.I) for p in patterns(patfile)]

    def hits(text):
        text = " ".join(_MARK.sub("", l) for l in text)
        got = [str(k) for k, rx in enumerate(pats, 1) if rx.search(text)]
        return ",".join(got) if got else "NONE"

    n = 1
    while os.path.exists(os.path.join(tools, "step%d.patch" % n)):
        path, hunk, k = None, None, 0
        lines = open(os.path.join(tools, "step%d.patch" % n), encoding="utf-8").read().split("\n")

        def flush():
            if hunk is None:
                return
            removed = [l[1:] for l in hunk if l.startswith("-")]
            if removed:
                print("step%d %s hunk %d: the old text, %s" % (n, path, k, hits(removed)))
            for i, l in enumerate(hunk):
                # a decision's own date line is no note on a claim: the log is swept by its own list
                if path.endswith("meta/DECISIONS.md"):
                    break
                if l.startswith("+") and _NOTE in l:
                    j, claim = i - 1, []
                    while j >= 0 and hunk[j].startswith(" ") and len(claim) < 3:
                        claim.insert(0, hunk[j][1:])
                        j -= 1
                    # and the words the note quotes, `*"…"*`, which name the claim where it stands higher up
                    m = i
                    while m < len(hunk) and hunk[m].startswith("+") and (m == i or _NOTE not in hunk[m]):
                        m += 1
                    note = " ".join(_MARK.sub("", x[1:]) for x in hunk[i:m])
                    claim += _QUOTE.findall(note)
                    if claim:
                        print("step%d %s hunk %d: the claim a note dates, %s" % (n, path, k, hits(claim)))
                    else:
                        print("step%d %s hunk %d: a note with no claim above it or quoted" % (n, path, k))

        for l in lines:
            if l.startswith("diff --git "):
                flush()
                hunk, k = None, 0
            elif l.startswith("+++ "):
                path = l[6:] if l.startswith("+++ b/") else l[4:]
            elif l.startswith("@@"):
                flush()
                hunk, k = [], k + 1
            elif hunk is not None and l[:1] in (" ", "-", "+"):
                hunk.append(l)
        flush()
        n += 1
    twins = os.path.join(tools, "sweep_twins.txt")
    if os.path.exists(twins):
        for l in open(twins, encoding="utf-8"):
            if l.strip() and not l.startswith("#"):
                site, _claim, twin = l.rstrip("\n").split("\t")
                print("twin %s: %s" % (site, hits([twin])))
    return 0


def main(argv):
    if len(argv) == 4 and argv[1] == "control":
        return control(argv[2], argv[3])
    if len(argv) not in (4, 5) or (len(argv) == 5 and argv[4] != "decisions"):
        print(__doc__)
        return 2
    root, out, patfile = os.path.realpath(argv[1]), argv[2], argv[3]
    spec = PATHSPEC + ([] if len(argv) == 5 else [":!meta/DECISIONS.md"])
    pats = patterns(patfile)
    files = [f for f in git(root, "ls-files", "-z", "--", *spec).split("\0") if f]
    texts = {}
    for f in files:
        raw = open(os.path.join(root, f), "rb").read()
        if b"\0" in raw:
            continue
        texts[f] = raw.decode("utf-8", "replace").split("\n")
    with open(out, "w", encoding="utf-8") as fh:
        for k, pat in enumerate(pats, 1):
            line_hits = set()
            for row in git(root, "grep", "-n", "-I", "-i", "-E", pat, "HEAD", "--", *spec).splitlines():
                path, ln, text = row.split(":", 3)[1:]
                line_hits.add((path, int(ln)))
                fh.write("%d line %s:%s: %s\n" % (k, path, ln, text.strip()[:200]))
            rx = re.compile(pat, re.I)
            joined_hits, only = set(), 0
            for f, lines in sorted(texts.items()):
                clean = [_MARK.sub("", l) for l in lines]
                starts, pos = [], 0
                for l in clean:
                    starts.append(pos)
                    pos += len(l) + 1
                text = " ".join(clean)
                for m in rx.finditer(text):
                    ln = bisect.bisect_right(starts, m.start())
                    if (f, ln) in joined_hits:
                        continue
                    joined_hits.add((f, ln))
                    if (f, ln) not in line_hits:
                        only += 1
                        fh.write("%d joined %s:%d: %s\n" % (k, f, ln, text[m.start():m.end()][:200]))
            print("%d. %s: %d line hits, %d joined hits, %d joined-only"
                  % (k, pat, len(line_hits), len(joined_hits), only))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

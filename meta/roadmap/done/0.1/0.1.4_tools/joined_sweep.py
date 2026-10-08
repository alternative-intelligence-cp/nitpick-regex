#!/usr/bin/env python3
"""Each text file of a pathspec at HEAD, its line breaks -- with the indentation and the comment or quote marker
after each (`//`, `#`, `>`, `*`) -- read as one space; every pattern matched case-insensitively; each match that
crosses a line break printed with sixty characters either side. A per-line sweep cannot see those (0.1.2's record).

    python3 -B joined_sweep.py "$REPO" "<pattern><TAB><pattern>..." <pathspec>...
"""
import re
import subprocess
import sys

repo, pats, spec = sys.argv[1], sys.argv[2].split("\t"), sys.argv[3:]
listed = subprocess.run(["git", "-C", repo, "ls-files", "--", *spec], capture_output=True, text=True).stdout
files = [f for f in listed.split("\n") if f]
JOIN = re.compile(r"[ \t]*\n[ \t]*(?:(?://|#|>|\*)+[ \t]*)?")
opened, hits = 0, []
for f in files:
    raw = subprocess.run(["git", "-C", repo, "show", f"HEAD:{f}"], capture_output=True).stdout
    if b"\0" in raw[:8192]:
        continue
    opened += 1
    text = raw.decode("utf-8", "replace")
    parts, breaks, last = [], [], 0
    for m in JOIN.finditer(text):
        parts.append(text[last:m.start()])
        breaks.append(sum(len(x) for x in parts))      # where a line break stood in the joined text
        parts.append(" ")
        last = m.end()
    parts.append(text[last:])
    joined = "".join(parts)
    for p in pats:
        for m in re.finditer(p, joined, re.I):
            if any(m.start() < k < m.end() for k in breaks):
                hits.append(f"  [{p[:28]}] {f}: ...{joined[max(0, m.start() - 60):m.end() + 60]}...")
print(f"joined-text sweep: {opened} text files at HEAD opened, {len(files)} in the pathspec")
print(f"matches crossing a line break: {len(hits)}")
for h in hits:
    print(h[:260])

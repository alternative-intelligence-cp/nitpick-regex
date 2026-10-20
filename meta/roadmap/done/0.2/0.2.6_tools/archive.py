#!/usr/bin/env python3
"""0.2.6 -- ARCHIVE CYCLE 0.2: `git mv meta/roadmap/0.2 meta/roadmap/done/0.2`, and re-point what navigates to it, by
the line RX-140 drew at cycle 0.0's archive: LIVE NAVIGATION IS CORRECTED, HISTORICAL CLAIMS ARE NOT. `done/0.1/0.1.6_tools/archive.py`, cycle 0.1's, pointed at
cycle 0.2, in its two halves -- and, as `nitpick-time`'s 0.3.4, EACH HALF STAGES EXACTLY WHAT IT WRITES (`git mv` the
move, and `git add` by name every file a half edits), so a commit after it takes no `git add`:

    archive.py check      -- report what each half would do; write nothing
    archive.py move       -- `git mv`, then every markdown LINK the move breaks: one inside the folder that leaves it
                             gains a `../`, and one outside it that enters it is re-pointed -- in every tracked
                             markdown file, the records too, since a link is navigation and its depth no claim
                             (RX-140: "the depth changed and no claim did")
    archive.py mentions   -- every other mention of the folder outside it -- a plain path, in any tracked text file
                             -- re-pointed, but in the records

THE RECORDS are left as written: `meta/DECISIONS.md` (a settled decision's text is never rewritten), the earlier
archives `meta/roadmap/done/0.0/` and `done/0.1/`, the audit reports in `meta/audits/` and the transcripts. INSIDE the folder a plain
path is left: it says where a file was when its note was written. Reads and writes with `newline=""`, so no byte it
was not asked to change moves. Stops if the folder is already gone (`move`), if `done/0.2` exists (`move`), if the
folder is not gone (`mentions`), or if a live mention is left after `mentions`. Run with `REPO` in the environment.
"""
import os, re, subprocess, sys

REPO = os.environ["REPO"]
OLD, NEW = "meta/roadmap/0.2", "meta/roadmap/done/0.2"
RECORDS = re.compile(r"^meta/DECISIONS\.md$|^meta/roadmap/done/0\.[01]/|^meta/audits/nitpick-regex-|TRANSCRIPT\.txt$")
# A mention of the folder: a repository path (`meta/roadmap/0.2/`, and the relative `roadmap/0.2/` the
# specifications, the questions and the research use), a sibling-relative one (`../0.2/`), not preceded by a path
# character.
MENTION = re.compile(r"(?<![A-Za-z0-9_./-])((?:\.\./)*(?:meta/)?roadmap/)0\.2/"
                     r"|(?<![A-Za-z0-9_./-])((?:\.\./)+)0\.2/")
LINK = re.compile(r"\]\(([^)#\s]+)(#[^)]*)?\)")


def read(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return fh.read()


def write(p, t):
    with open(p, "w", encoding="utf-8", newline="") as fh:
        fh.write(t)
    subprocess.run(["git", "-C", REPO, "add", "--", os.path.relpath(p, REPO)], check=True)


def tracked():
    out = subprocess.run(["git", "-C", REPO, "ls-files"], stdout=subprocess.PIPE, text=True).stdout
    return [l for l in out.split("\n") if l]


def text_of(rel):
    try:
        return read(os.path.join(REPO, rel))
    except (UnicodeDecodeError, IsADirectoryError, FileNotFoundError):
        return None


def _repoint(m):
    if m.group(1) is not None:                  # `…roadmap/0.2/`
        return m.group(1) + "done/0.2/"
    return m.group(2) + "done/0.2/"             # `../0.2/`


def outside_links(rel, text):
    """Markdown links in a file outside the folder that resolve into it, re-pointed to where it goes."""
    count = 0
    base = os.path.dirname(rel)

    def sub(m):
        nonlocal count
        t = m.group(1)
        if t.startswith(("http://", "https://", "mailto:", "#", "/")):
            return m.group(0)
        landed = os.path.normpath(os.path.join(base, t))
        if not (landed == OLD or landed.startswith(OLD + "/")):
            return m.group(0)
        count += 1
        target = NEW + landed[len(OLD):]
        new = os.path.relpath(target, base or ".")
        if t.endswith("/") and not new.endswith("/"):
            new += "/"
        # `]` and `(` built apart: a plan quotes this script.
        return "]" + "(" + new + (m.group(2) or "") + ")"
    return LINK.sub(sub, text), count


def inside_links(rel_new, text):
    """`rel_new` is the file's NEW path; a link resolved from its OLD directory that lands outside the folder is
    re-written from the new one."""
    old_dir = os.path.dirname(rel_new.replace(NEW, OLD, 1))
    new_dir = os.path.dirname(rel_new)
    count = 0

    def sub(m):
        nonlocal count
        t = m.group(1)
        if t.startswith(("http://", "https://", "mailto:", "#", "/")):
            return m.group(0)
        landed = os.path.normpath(os.path.join(old_dir, t))
        if landed == OLD or landed.startswith(OLD + "/"):
            return m.group(0)
        count += 1
        new = os.path.relpath(landed, new_dir)
        if t.endswith("/") and not new.endswith("/"):
            new += "/"
        return "]" + "(" + new + (m.group(2) or "") + ")"
    return LINK.sub(sub, text), count


def plain(text):
    """Every mention of the folder that is NOT inside a markdown link's target."""
    spans = [(m.start(1), m.end(1)) for m in LINK.finditer(text)]
    return [m for m in MENTION.finditer(text) if not any(a <= m.start() < b for a, b in spans)]


def main(mode):
    files = tracked()
    inside = [f for f in files if f.startswith(OLD + "/")]
    outside_md = [f for f in files if not f.startswith(OLD + "/") and f.endswith(".md")]
    live = [f for f in files if not f.startswith(OLD + "/") and not RECORDS.search(f)
            and not f.startswith(NEW + "/")]
    if mode in ("check", "move"):
        if not os.path.isdir(os.path.join(REPO, OLD)):
            sys.exit("STOP: %s is not a directory -- already archived?" % OLD)
        if os.path.exists(os.path.join(REPO, NEW)):
            sys.exit("STOP: %s exists" % NEW)
        print("the folder: %d tracked file(s)" % len(inside))
        n_out = f_out = 0
        for rel in outside_md:
            t = text_of(rel)
            if t is None:
                continue
            new, n = outside_links(rel, t)
            if n:
                n_out += n
                f_out += 1
                print("  link     %-56s %3d" % (rel, n))
                if mode == "move":
                    write(os.path.join(REPO, rel), new)
        print("links into the folder from outside it: %d in %d file(s)" % (n_out, f_out))
        if mode == "move":
            r = subprocess.run(["git", "-C", REPO, "mv", OLD, NEW])
            if r.returncode != 0:
                sys.exit("STOP: git mv exited %d" % r.returncode)
        n_in = f_in = 0
        for rel in inside:
            if not rel.endswith(".md"):
                continue
            rel_new = rel.replace(OLD, NEW, 1)
            p = os.path.join(REPO, rel_new if mode == "move" else rel)
            new, n = inside_links(rel_new, read(p))
            if n:
                n_in += n
                f_in += 1
                if mode == "move":
                    write(p, new)
        print("links leaving the folder from inside it: %d in %d file(s)" % (n_in, f_in))
        n_plain = f_plain = 0
        for rel in live:
            t = text_of(rel)
            if t is None:
                continue
            k = len(plain(t))
            if k:
                n_plain += k
                f_plain += 1
        print("plain mentions outside it, left for `mentions`: %d in %d live file(s)" % (n_plain, f_plain))
        recs = sum(len(MENTION.findall(text_of(f) or "")) for f in files
                   if RECORDS.search(f) and not f.startswith(OLD + "/"))
        print("left as written in the records: %d mention(s)" % recs)
        if mode == "move":
            print("moved: %s -> %s" % (OLD, NEW))
        return
    if os.path.exists(os.path.join(REPO, OLD)):
        sys.exit("STOP: %s still exists -- run `move` first" % OLD)
    total = nfiles = 0
    for rel in live:
        t = text_of(rel)
        if t is None:
            continue
        hits = plain(t)
        if not hits:
            continue
        out, last = [], 0
        for m in hits:
            out.append(t[last:m.start()])
            out.append(_repoint(m))
            last = m.end()
        out.append(t[last:])
        write(os.path.join(REPO, rel), "".join(out))
        total += len(hits)
        nfiles += 1
        print("  plain    %-56s %3d" % (rel, len(hits)))
    print("plain mentions re-pointed: %d in %d live file(s)" % (total, nfiles))
    stale = [f for f in tracked() if not f.startswith(NEW + "/") and not RECORDS.search(f)
             and MENTION.search(text_of(f) or "")]
    if stale:
        sys.exit("STOP: a live mention is left in %s" % ", ".join(stale[:5]))


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("check", "move", "mentions"):
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1])

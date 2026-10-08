#!/usr/bin/env python3
"""0.1.0 -- the one engine every edit of this subcycle runs through.

    python3 -B f10_edit.py <rx113|error|cursor|ast|entry|prose> "$REPO"

`0.0.4e_tools/e4e_edit.py`, the engine this repository's last plan rehearsed,
with its defect-id tokens removed (nothing here is numbered by the orchestrator).
The TEXTS live in `f10_<section>.py` beside this file, as data: `NEW` (whole files
this subcycle adds), `EDITS` (a path and its exact (old, new) pairs, applied in
order), and `KEEP_LINES` (files whose line count must not move, because a measured
`expect-error-at` depends on it). They are the review surface: a worker may tighten
a text, never change what it says -- and AMENDS THE TEXT HERE, BEFORE THE SCRIPT
RUNS, never the written file after (the workbench `PLAYBOOK.md` §12: an appending
edit whose written copy was amended by hand is re-applied by a naive re-run).

IDEMPOTENT, ALL-OR-NOTHING, AND IT STOPS ON DRIFT -- and the NEW text is looked for
FIRST, because an appending edit's new text contains its old (`PLAYBOOK.md` §12):
  * `new` present exactly once                  -> ALREADY, skipped
  * `new` absent, and a line only `new` has is present -> STOP: a hand-amended copy
  * `new` absent, `old` present exactly once    -> EDIT
  * anything else                               -> STOP
  * a `NEW` file present with other content     -> STOP
  * a `KEEP_LINES` file whose line count moved  -> STOP
One STOP and NO file is written. A second run reports every edit ALREADY.

ONE TOKEN, substituted before matching: `@@DATE@@` -- today's date when written,
ANY date when matched, so a re-run on a later day recognises its own edit.
Every file is read and written with `newline=""`, so a byte the texts do not name
is never translated.
"""
import datetime
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATE = datetime.date.today().isoformat()
_DATE_RE = r"\d{4}-\d{2}-\d{2}"
SECTIONS = ("rx113", "error", "cursor", "ast", "entry", "prose")


def pattern(new):
    """`new` as a regex matching any date where it says @@DATE@@."""
    return re.escape(new).replace(re.escape("@@DATE@@"), _DATE_RE)


def load(section):
    path = os.path.join(HERE, f"f10_{section}.py")
    spec = importlib.util.spec_from_file_location(f"f10_{section}", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def read(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def main(argv):
    if len(argv) != 3 or argv[1] not in SECTIONS:
        print(__doc__.split("\n\n")[0])
        return 2
    section, root = argv[1], os.path.realpath(argv[2])
    m = load(section)
    edits = dict(getattr(m, "EDITS", {}))
    new_files = getattr(m, "NEW", {})
    keep = set(getattr(m, "KEEP_LINES", ()))

    stops, done, already, written = 0, 0, 0, 0
    out = {}
    for rel, content in new_files.items():
        path = os.path.join(root, rel)
        if os.path.exists(path):
            if re.fullmatch(pattern(content), read(path)):
                already += 1
                print(f"  ALREADY  {rel} (new file)")
            else:
                stops += 1
                print(f"  STOP     {rel}: exists with other content")
            continue
        out[path] = content.replace("@@DATE@@", DATE)
        written += 1
        print(f"  WRITE    {rel}")

    for rel, pairs in edits.items():
        path = os.path.join(root, rel)
        if not os.path.exists(path):
            stops += 1
            print(f"  STOP     {rel}: missing")
            continue
        s = out.get(path) or read(path)
        before_lines = s.count("\n")
        for n, (old, new) in enumerate(pairs, 1):
            pat = pattern(new)
            cn = len(re.findall(pat, s))
            co = s.count(old)
            # A line only the new text has, long enough to be its own: the tell of a
            # hand-amended copy. Whole lines are compared, never prefixes (0.0.4e's
            # rehearsal found a prefix match stopping the engine on its own edit).
            old_lines = old.split("\n")
            only_new = [ln for ln in new.split("\n")
                        if len(ln.strip()) >= 30 and ln not in old_lines and "@@DATE@@" not in ln]
            s_lines = s.split("\n")
            if cn == 1:
                already += 1
                print(f"  ALREADY  {rel} #{n}")
            elif cn == 0 and only_new and only_new[0] in s_lines:
                stops += 1
                print(f"  STOP     {rel} #{n}: a line only the new text has is present, and the "
                      f"new text is not -- a hand-amended copy; amend THIS script's text")
            elif cn == 0 and co == 1:
                s = s.replace(old, new.replace("@@DATE@@", DATE))
                done += 1
                print(f"  EDIT     {rel} #{n}")
            else:
                stops += 1
                print(f"  STOP     {rel} #{n}: old x{co}, new x{cn}")
        if rel in keep and s.count("\n") != before_lines:
            stops += 1
            print(f"  STOP     {rel}: its line count moved {before_lines} -> {s.count(chr(10))}, "
                  f"and a measured position depends on it")
        out[path] = s

    total = len(set(list(edits) + list(new_files)))
    if stops:
        print(f"f10_{section}: {stops} stop(s) -- NOTHING WRITTEN")
        return 1
    for path, s in out.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(s)
    print(f"f10_{section}: {done} edited, {written} written, {already} already, over "
          f"{total} files -- 0 stops")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

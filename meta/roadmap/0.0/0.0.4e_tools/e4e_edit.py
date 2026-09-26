#!/usr/bin/env python3
"""0.0.4e -- the one engine every edit of this subcycle runs through.

    python3 e4e_edit.py <src|tests|harness|docs> "$REPO"

The TEXTS live in `e4e_<section>.py` beside this file, as data: `EDITS` (a path and
its exact (old, new) pairs), `NEW` (whole files this subcycle adds), and
`KEEP_LINES` (files whose line count must not move, because a measured
`expect-error-at` or a rejection fixture's position depends on it), and `HEADERS`
(a moved file's whole header -- every line above `mod:` -- replaced, keyed by the
sha256 of the header it replaces, so a file that drifted is a STOP). They are the
review surface: a worker may tighten a text, never change what it says -- and
AMENDS THE TEXT HERE, BEFORE THE SCRIPT RUNS, never the written file after
(`PLAYBOOK.md` §12: an appending edit whose written copy was amended by hand is
re-applied by a naive re-run).

IDEMPOTENT, ALL-OR-NOTHING, AND IT STOPS ON DRIFT:
  * `new` present exactly once                  -> ALREADY, skipped
  * `new` absent, `old` present exactly once    -> EDIT
  * `new` absent and a line that only `new` has is present -> STOP: the tree holds
    a hand-amended copy of this edit, and applying it again would duplicate it
  * anything else                               -> STOP
  * a `NEW` file present with other content     -> STOP
  * a `KEEP_LINES` file whose line count moved  -> STOP
One STOP and NO file is written. A second run reports every edit ALREADY.

TOKENS, substituted before matching:
  @@DATE@@        today's date when written; ANY date when matched, so a re-run on
                  a later day recognises its own edit
  @@DEFECT@@      how the texts name the compiler defect `0.0.4e.md` §6.1 raises:
                  "the workbench registry's O-N<n>" when `$E4E_DEFECT_ID` holds
                  O-N<n> (written once in step 0 to `.internal/d4e/defect_id`),
                  otherwise "raised by path from `meta/roadmap/0.0/0.0.4e.md` §6.1"
  @@DEFECT_ID@@   O-N<n>, or "the impl-signature defect" when no number was given
Edits listed under `IF_DEFECT_ID` are applied only when a number was given.
"""
import datetime
import hashlib
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATE = datetime.date.today().isoformat()
_DATE_RE = r"\d{4}-\d{2}-\d{2}"


def defect_id(root):
    v = os.environ.get("E4E_DEFECT_ID", "").strip()
    if not v:
        try:
            v = open(os.path.join(root, ".internal", "d4e", "defect_id")).read().strip()
        except OSError:
            v = ""
    if v and not re.fullmatch(r"O-N\d+", v):
        sys.exit(f"e4e: the defect id {v!r} is not O-N<n> -- NOTHING WRITTEN")
    return v


def tokens(root):
    d = defect_id(root)
    if d:
        return d, {"@@DEFECT@@": f"the workbench registry's {d}",
                   "@@DEFECT_ID@@": d}
    return d, {"@@DEFECT@@": "raised by path from `meta/roadmap/0.0/0.0.4e.md` §6.1",
               "@@DEFECT_ID@@": "the impl-signature defect"}


def subst(text, toks):
    for k, v in toks.items():
        text = text.replace(k, v)
    return text


def pattern(new):
    """`new` as a regex matching any date where it says @@DATE@@, and any MEASURED
    position where it says `expect-error-at: 0:0` -- so a re-run after step 4's
    `pin` reads a pinned file as ALREADY, never back to `0:0` (0.0.4d's rule)."""
    return (re.escape(new).replace(re.escape("@@DATE@@"), _DATE_RE)
            .replace(re.escape("// expect-error-at: 0:0"), r"// expect-error-at: \d+:\d+"))


def load(section):
    path = os.path.join(HERE, f"e4e_{section}.py")
    spec = importlib.util.spec_from_file_location(f"e4e_{section}", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main(argv):
    if len(argv) != 3 or argv[1] not in ("src", "tests", "harness", "docs"):
        print(__doc__.split("\n\n")[0])
        return 2
    section, root = argv[1], os.path.realpath(argv[2])
    did, toks = tokens(root)
    m = load(section)
    edits = dict(getattr(m, "EDITS", {}))
    if did:
        for rel, pairs in getattr(m, "IF_DEFECT_ID", {}).items():
            edits.setdefault(rel, [])
            edits[rel] = list(edits[rel]) + list(pairs)
    new_files = getattr(m, "NEW", {})
    keep = set(getattr(m, "KEEP_LINES", ()))

    stops, done, already, written = 0, 0, 0, 0
    out = {}
    for rel, content in new_files.items():
        path = os.path.join(root, rel)
        want = subst(content, toks).replace("@@DATE@@", DATE)
        if os.path.exists(path):
            have = open(path, encoding="utf-8").read()
            if re.fullmatch(pattern(subst(content, toks)), have):
                already += 1
                print(f"  ALREADY  {rel} (new file)")
            else:
                stops += 1
                print(f"  STOP     {rel}: exists with other content")
            continue
        out[path] = want
        written += 1
        print(f"  WRITE    {rel}")

    for rel, (old_sha, header) in getattr(m, "HEADERS", {}).items():
        path = os.path.join(root, rel)
        if not os.path.exists(path):
            stops += 1
            print(f"  STOP     {rel}: missing (a `git mv` not yet made?)")
            continue
        s = open(path, encoding="utf-8").read()
        cut = s.find("\nmod:") + 1 if not s.startswith("mod:") else 0
        if cut <= 0 and not s.startswith("mod:"):
            stops += 1
            print(f"  STOP     {rel}: no `mod:` line")
            continue
        head, body = s[:cut], s[cut:]
        want = subst(header, toks)
        if re.fullmatch(pattern(want), head):
            already += 1
            print(f"  ALREADY  {rel} (header)")
        elif hashlib.sha256(head.encode("utf-8")).hexdigest() == old_sha:
            out[path] = want.replace("@@DATE@@", DATE) + body
            done += 1
            print(f"  EDIT     {rel} (header)")
        else:
            stops += 1
            print(f"  STOP     {rel}: its header is neither the one this script replaces "
                  f"(sha256 {old_sha[:12]}...) nor the new one")

    for rel, pairs in edits.items():
        path = os.path.join(root, rel)
        if not os.path.exists(path):
            stops += 1
            print(f"  STOP     {rel}: missing (a `git mv` not yet made?)")
            continue
        s = out.get(path) or open(path, encoding="utf-8").read()
        before_lines = s.count("\n")
        for n, (old, new) in enumerate(pairs, 1):
            old, new = subst(old, toks), subst(new, toks)
            pat = pattern(new)
            cn = len(re.findall(pat, s))
            co = s.count(old)
            # A line only the new text has, long enough to be its own: the tell of
            # a hand-amended copy (a short `//` would match any comment).
            only_new = [ln for ln in new.split("\n")
                        if len(ln.strip()) >= 30 and ln not in old.split("\n")
                        and "@@DATE@@" not in ln]
            if cn == 1:
                already += 1
                print(f"  ALREADY  {rel} #{n}")
            elif cn == 0 and only_new and only_new[0] in s.split("\n"):
                stops += 1
                print(f"  STOP     {rel} #{n}: a line only the new text has is present, and "
                      f"the new text is not -- a hand-amended copy; amend THIS script's text")
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

    total = len(set(list(edits) + list(new_files) + list(getattr(m, "HEADERS", {}))))
    if stops:
        print(f"e4e_{section}: {stops} stop(s) -- NOTHING WRITTEN")
        return 1
    for path, s in out.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(s)
    print(f"e4e_{section}: {done} edited, {written} written, {already} already, over "
          f"{total} files -- 0 stops{' -- defect id ' + did if did else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

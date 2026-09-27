# Currency — the facts from outside the compiler tree this plan rests on

One row per standard, data release, corpus or reference implementation the plan
names, with the version pinned, the day it was checked, the primary source, and
the decision that pins it (the workbench research skill's §7). A row unchecked
for six months is stale; a cycle whose rows are unchecked is not ready to start.
The Unicode data, the corpora and the reference engines join this table at the
cycles that first depend on them (0.3, 0.5, 0.9).

| Depends on | Pinned | Checked | Source | Decision |
|---|---|---|---|---|
| well-formed UTF-8 — what a pattern must be (`SYNTAX.md` Y-11, Y-28) | RFC 3629 (STD 63, November 2003), §4's ABNF | 2026-09-27 | rfc-editor.org/rfc/rfc3629 — [`utf8-rfc3629.md`](utf8-rfc3629.md) | `roadmap/0.1/0.1.1.md` PD-27 |

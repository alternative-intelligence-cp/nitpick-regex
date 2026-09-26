# `meta/audits/`

**W-22 audit reports, filed by the orchestrator, reproduced here in full.**

An audit is dispatched adversarially: the auditor is told to break the
verifier's PASS rather than to confirm it, it may not write to any repository,
and it reports without fixing. The worker is then re-dispatched with the report
and triages **every** finding — fixed, deferred to a named cycle with a reason,
or refused with its cost stated. Nothing is silently dropped, and the triage
states its denominator beside its verdict, because a triage that does not count
is the defect this repository keeps finding.

**These files are records and are never rewritten.** A report says what was
found when it was filed; what happened next lives in the subcycle's execution
record, not in an edit here.

| Report | Cycle | Verdict | Triage |
|---|---|---|---|
| [`nitpick-regex-0.0-2026-09-06.md`](nitpick-regex-0.0-2026-09-06.md) | 0.0 | **DO NOT ACCEPT** — 2 blocking, 4 adjudications, 9 non-blocking | [`../roadmap/0.0/0.0.5.md`](../roadmap/0.0/0.0.5.md) §8 — 15 findings, 15 lines |
| [`nitpick-regex-0.0-2026-09-06-second.md`](nitpick-regex-0.0-2026-09-06-second.md) | 0.0 | **DO NOT ACCEPT** — 2 blocking, 3 non-blocking | [`../roadmap/0.0/0.0.5.md`](../roadmap/0.0/0.0.5.md) §9 — 6 items, 6 lines |
| [`nitpick-regex-0.0-2026-09-06-third.md`](nitpick-regex-0.0-2026-09-06-third.md) | 0.0 | **DO NOT ACCEPT** — 2 blocking (BL-5, BL-6), 5 non-blocking (N-13 … N-17) | [`../roadmap/0.0/0.0.5.md`](../roadmap/0.0/0.0.5.md) §10 — 7 findings, 7 lines, after 0.0.4b and 0.0.4c (whose [§9](../roadmap/0.0/0.0.4b.md) read it against `c3bdae2` first). *This cell said **pending** until the fourth triage: the third left it stale* |
| [`nitpick-regex-0.0-2026-09-25-fourth.md`](nitpick-regex-0.0-2026-09-25-fourth.md) | 0.0 | **DO NOT ACCEPT** — 2 blocking (BL-7, BL-8), 6 non-blocking (N-18 … N-23) | [`../roadmap/0.0/0.0.5.md`](../roadmap/0.0/0.0.5.md) §11 — 8 findings, 8 lines; N-15 deferred to 0.0.4d by the author's decision |
| [`nitpick-regex-0.0-2026-09-25-fifth.md`](nitpick-regex-0.0-2026-09-25-fifth.md) | 0.0 | **DO NOT ACCEPT** — 1 blocking (BL-9), 6 non-blocking (N-24 … N-29); the loan's refusal excluded, as directed | [`../roadmap/0.0/0.0.5.md`](../roadmap/0.0/0.0.5.md) §12 — 7 findings, 7 lines, at `c3bdae2`; its post-re-pin checklist is the re-pin subcycle's |

**THE SECOND PASS IS THE ARGUMENT FOR THE FIRST ONE'S EXISTENCE, AND FOR A
THIRD.** It was scoped tightly to the delta and to where the first audit did not
press, and it returned two blocking findings — **one introduced by the first
triage's own fix commit**, and one the first audit's own template could not have
reached, because that template looked for a **missing guard** and the defect was
a guard whose **stop did not stop**. Each pass here has found what the previous
pass's shape could not see. That is the case for auditing again rather than the
case for having finished.

**The fifth report was filed here with its triage (2026-09-25)**, verbatim from
the workbench's copy at `bac4b71` (the same sha256). **The fourth report was filed
here with its triage (2026-09-25)**, verbatim
from the workbench's copy at `0c9d4db` (the same sha256), as the first two
were. **The third report was filed here with the plan for cycle 0.0.4b (2026-09-25)**,
verbatim from the workbench's copy at `f1071fb` (the same sha256), because that
plan cites it; the first two came in with their triage commits. Its triage is
`0.0.5.md` §10 (it read "still the close's" until the fourth triage).

**The copy is deliberate.** The orchestrator files audits in the workbench, one
directory up from this repository, and a repository must carry the record it was
judged by: a clone of `nitpick-regex` alone would otherwise cite a file it does
not have, and `check_refs` would be right to refuse the link.

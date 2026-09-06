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

**THE SECOND PASS IS THE ARGUMENT FOR THE FIRST ONE'S EXISTENCE, AND FOR A
THIRD.** It was scoped tightly to the delta and to where the first audit did not
press, and it returned two blocking findings — **one introduced by the first
triage's own fix commit**, and one the first audit's own template could not have
reached, because that template looked for a **missing guard** and the defect was
a guard whose **stop did not stop**. Each pass here has found what the previous
pass's shape could not see. That is the case for auditing again rather than the
case for having finished.

**The copy is deliberate.** The orchestrator files audits in the workbench, one
directory up from this repository, and a repository must carry the record it was
judged by: a clone of `nitpick-regex` alone would otherwise cite a file it does
not have, and `check_refs` would be right to refuse the link.

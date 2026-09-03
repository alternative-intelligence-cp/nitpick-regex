# Cycle 0.14 — The dogfood consumer

> **Where the consumer lives (RX-101):** `grep`, in [`nitpick-posix`](https://github.com/alternative-intelligence-cp/nitpick-posix) — **not** in this repository's
> `examples/`. A consumer is a real program with its own lifetime, and
> `examples/` would make one that outgrows this library move, and one that
> consumes several pick a parent. The import is by relative path until the
> compiler's dependency resolution lands, and the repository's GitHub
> description and topics are set in the same pass that creates it.

**A real program, in `examples/`, written against the library as a consumer.**

## Why a cycle

Because an example written by the person who wrote the API is weak evidence: it
demonstrates the features the author was thinking about. A program with a
purpose finds what is missing, what is awkward, and what is wrong — and it
finds it before a 1.0 that would have to keep it.

## What to build

**A `grep`-shaped tool** (Q-2): read a file or standard input, search it, report
matches with offsets and context, with the usual switches — case-insensitive,
invert, count, files-with-matches, fixed-string, byte-mode. Chosen because it
exercises exactly the parts most likely to be weak:

| Feature | Exercises |
|---|---|
| a large file | the prefilter path, the DFA cache across a long haystack |
| line-by-line versus whole-file | `regex_find_at`'s offset semantics, the empty-match rule |
| a file that is not valid UTF-8 | byte mode, and the Unicode-mode boundary guarantee |
| many files | the `Cache` lifecycle, and whether one cache per file is obvious |
| `-i` and `\p{…}` | the folding orbit and the property tables, on real text |
| replacement (`-r`) | the template path, and the `Bytes` sink |
| a pathological pattern from a config file | RX-003, in the field |

`../ARCHIVE/nitpick-grep` exists as a shape reference for the tool's surface —
not for its implementation, which predates this language.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.14.0 | **The program** — written straight through, recording every friction | a working tool, and a numbered findings list |
| 0.14.1 | **Triage** — each finding a defect, a gap, or an accepted cost | a decision per finding |
| 0.14.2 | **The fixes** — the defects, and the gaps that survive triage | the library changed, the corpus extended |
| 0.14.3 | **Close** | `done/0.14/`, `1.0.0.md` written |

## Checklist

### 0.14.0 — the program
- [ ] written **without changing the library**, so every friction is recorded rather than smoothed over as it appears
- [ ] every awkwardness written down as it is met, numbered, with the line of code that caused it
- [ ] run over: a 1 GB log, a binary file, a UTF-8 file with one bad byte, a directory of ten thousand small files
- [ ] a pattern from an untrusted source — the ReDoS case, which should simply be slow-but-linear or refused at compile time
- [ ] built **and run** by the harness, so a broken example is a red run

### 0.14.1 — triage
- [ ] every finding classified: **defect** (the library is wrong), **gap** (a consumer reasonably needs something absent), or **cost** (the library is right and this is what the design costs)
- [ ] **every `cost` written into the documentation** — an accepted cost nobody warned about is a defect in the documentation
- [ ] every `gap` sized, and either scheduled into 1.0 or recorded as post-1.0
- [ ] O-A1's `Iterator` decision revisited against how the tool actually iterated

### 0.14.2 — the fixes
- [ ] the defects fixed, each with a corpus fixture
- [ ] the scheduled gaps closed
- [ ] the cross-engine run and the linear-time test still green after every change

## Gate

A `grep` a person would actually use, and a triaged findings list with a
decision per entry.

## Watch for

- **The temptation to fix as you write.** The value of this cycle is the
  *record* of what was awkward; a friction smoothed over in the moment is a
  friction the next user meets too.
- **"It needs a feature" is usually "the example needs a helper".** A gap is
  only a gap if it cannot be written in the application in a reasonable number
  of lines.
- **A pathological pattern from a config file is the demo.** Every other regex
  library's `grep` can be hung by one; this one cannot, and that is worth
  measuring and writing down.

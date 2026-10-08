r"""0.1.0 step 1 -- B-15a's rule 2 retired (the plan's PD-15, recorded as RX-171).

Eight live sites stated the rule's reason -- a compiler defect fixed at `94874ce` --
as current: `CLAUDE.md`, `CONTRIBUTING.md` item 7, `BUILD.md` B-15a, three places in
`harness/treecheck.py` (`check_layering`'s docstring, `_check_umbrella`'s docstring
and its failure message), and the headers of `src/core/core.npk` and `src/lib.npk`.
Each is edited here, `_check_umbrella` loses the branch rule 1's already subsumed,
and the decision and RX-113's marker are appended. Applied by
`python3 -B f10_edit.py rx113 "$REPO"`; the engine's docstring says how.
"""

EDITS = {}
TQ = '"' * 3          # a triple quote, which a raw triple-quoted text cannot hold; written @@TQ@@ below

EDITS["meta/specs/BUILD.md"] = [(
r"""**Rule B-15a (RX-113) — how the umbrella re-exports, and the one way it must
not.** Measured in 0.0.1 over a matrix of a type, an `error:` identity and a
function:

1. **Every line in `src/lib.npk` is `pub use`.** A plain `use` re-exports
   nothing, for any kind of symbol.
2. **No file plain-`use`s a path it also `pub use`s.** `symtab_bind_import`
   declines a name already bound and, on the "same declaration reached twice"
   path, returns the prior binding **without merging the new flags** — so a
   plain `use` above a `pub use` of the same path silently downgrades the
   re-export to nothing, at **no diagnostic**, and the failure appears in the
   consumer as *"cannot find X in this scope"*. Provisional workbench
   **O-N13**. `check_layering` gains this check at cycle 0.0.3.
3. **One name per line.**""",
r"""**Rule B-15a (RX-113; its rule 2 retired by RX-171) — how the umbrella
re-exports.** Measured in 0.0.1 over a matrix of a type, an `error:` identity
and a function:

1. **Every line in `src/lib.npk` is `pub use`.** A plain `use` re-exports
   nothing, for any kind of symbol — still so at `c970483`, where a consumer of
   an umbrella whose one line is a plain `use` is refused `NITPICK-RESOLVE-002`
   at its `(ERegexPattern)` arm. `check_layering` fails every plain `use` in
   the umbrella.
2. ~~**No file plain-`use`s a path it also `pub use`s.**~~ **Retired
   @@DATE@@ by RX-171.** Its reason was a compiler defect: `symtab_bind_import`
   declined a name already bound and returned the prior binding without merging
   the new flags, so a plain `use` above a `pub use` of the same path cancelled
   the re-export at no diagnostic — the workbench registry's O-N13, the
   compiler's DEF-7, fixed at `94874ce`. Measured at cycle 0.1.0: at `950bb1d`
   the shape cancels the re-export and the consumer is refused
   `NITPICK-RESOLVE-002`; at `94874ce` and at `c970483` it does not — above the
   `pub use` or below it, a wildcard or the same name, in `src/lib.npk` and in
   `src/core/core.npk` — and a `pub use` binds its name in its own file, so no
   file needs a plain `use` of a path for a name it re-exports. What remained
   of the rule was style.
3. **One name per line.**"""),
]

EDITS["CLAUDE.md"] = [(
r"""- **`src/lib.npk` re-exports with `pub use`, one name per line, and must never
  plain-`use` a path it also `pub use`s** (RX-113). A plain `use` re-exports
  nothing; a plain `use` above a `pub use` of the same path silently cancels the
  re-export, at no diagnostic, and the failure lands in the consumer as "cannot
  find X in this scope".""",
r"""- **`src/lib.npk` re-exports with `pub use`, one name per line** (RX-113). A
  plain `use` re-exports nothing, and the failure lands in the consumer, not in
  `src/lib.npk`. *(Until cycle 0.1.0 this bullet also said a file must never
  plain-`use` a path it also `pub use`s, because a plain `use` above the
  `pub use` silently cancelled the re-export — the compiler's DEF-7, fixed at
  `94874ce`. Measured at `c970483` it no longer does, and that rule is retired:
  RX-171.)*"""),
]

EDITS["CONTRIBUTING.md"] = [(
r"""7. **`src/lib.npk` is `pub use`, one name per line, and never plain-`use`s a
   path it re-exports** (RX-113). A plain `use` re-exports nothing, and a plain
   `use` written above a `pub use` of the same path cancels the re-export
   silently — no diagnostic, and the failure appears in a consumer as "cannot
   find X in this scope". If you add a name to the public surface, add one
   line, and add it to `API.md` §1 in the same commit.""",
r"""7. **`src/lib.npk` is `pub use`, one name per line** (RX-113). A plain `use`
   re-exports nothing, and the failure appears in a consumer, not in
   `src/lib.npk`. If you add a name to the public surface, add one line, and add
   it to `API.md` §1 in the same commit. *(The rule that a file never
   plain-`use`s a path it also `pub use`s is retired — RX-171: the
   cancellation it guarded against was a compiler defect, fixed at `94874ce`.)*"""),
]

EDITS["harness/treecheck.py"] = [(
r"""      B-15a  the umbrella is all `pub use`, and never plain-`use`s a path it
             also `pub use`s -- the silent-cancellation shape RX-113 measured,
             which produces NO DIAGNOSTIC and surfaces in the consumer.
    @@TQ@@""",
r"""      B-15a  the umbrella is all `pub use` (rule 1): a plain `use` re-exports
             nothing, and the failure surfaces in the consumer, not here. Rule 2
             -- no plain `use` of a path also `pub use`d -- is retired (RX-171):
             the cancellation it guarded against was the compiler's DEF-7,
             fixed at `94874ce`.
    @@TQ@@"""), (
r"""def _check_umbrella(root, lib):
    @@TQ@@RULE B-15a, AND IT IS THE ONE WITH NO COMPILER BEHIND IT.

    A plain `use` re-exports nothing, and a plain `use` written above a
    `pub use` OF THE SAME PATH silently downgrades the re-export to nothing at
    NO DIAGNOSTIC -- `symtab_bind_import` declines a name already bound and
    returns the prior binding without merging the new flags (RX-113, workbench
    O-N13). The failure lands in the CONSUMER as "cannot find X in this scope",
    with nothing wrong at the line that caused it. No compiler will report this
    for us; this check is the only thing that does.@@TQ@@
    if not os.path.exists(lib):
        return [f"src/lib.npk is missing -- it is the umbrella and the whole public "
                f"surface (BUILD.md B-15a)"]
    fl = []
    plain, pub = {}, {}
    try:
        text = lexical.read(lib)
    except OSError as e:
        return [f"src/lib.npk: {e}"]
    for ln, target, is_pub in lexical.imports(text):
        if is_pub:
            pub.setdefault(target, []).append(ln)
        else:
            plain.setdefault(target, []).append(ln)
            fl.append(f"src/lib.npk:{ln}: a plain `use` in the umbrella. EVERY LINE "
                      f"HERE IS `pub use` (B-15a rule 1): a plain `use` re-exports "
                      f"nothing, for any kind of symbol, and the failure appears in "
                      f"the consumer rather than here.")
    for target, lns in sorted(plain.items()):
        if target in pub:
            fl.append(f"src/lib.npk: `{target}` is plain-`use`d at line "
                      f"{lns[0]} AND `pub use`d at line {pub[target][0]}. THE PLAIN "
                      f"ONE SILENTLY CANCELS THE RE-EXPORT (B-15a rule 2, RX-113): "
                      f"the first import of a name wins, a later one is declined "
                      f"without merging its flags, and there is NO DIAGNOSTIC. This "
                      f"check is the only thing in the world that reports it.")
    return fl""",
r"""def _check_umbrella(root, lib):
    @@TQ@@RULE B-15a RULE 1: EVERY LINE OF THE UMBRELLA IS `pub use`.

    A plain `use` re-exports nothing, for any kind of symbol, and the failure
    lands in the CONSUMER -- at `c970483` its `(ERegexPattern)` arm is
    NITPICK-RESOLVE-002 -- with nothing wrong at the line that caused it. So a
    plain `use` here fails the run.

    RULE 2 IS RETIRED (RX-171), AND THIS CHECK NO LONGER TESTS IT. It said no
    file plain-`use`s a path it also `pub use`s, because a plain `use` above the
    `pub use` silently cancelled the re-export -- the compiler's DEF-7 (the
    workbench registry's O-N13), fixed at `94874ce`. Measured at `c970483`, the
    shape leaves the re-export intact. Its branch here never fired alone: in the
    one file this check reads, rule 1's branch already fails every plain `use`.@@TQ@@
    if not os.path.exists(lib):
        return [f"src/lib.npk is missing -- it is the umbrella and the whole public "
                f"surface (BUILD.md B-15a)"]
    fl = []
    try:
        text = lexical.read(lib)
    except OSError as e:
        return [f"src/lib.npk: {e}"]
    for ln, target, is_pub in lexical.imports(text):
        if not is_pub:
            fl.append(f"src/lib.npk:{ln}: a plain `use` in the umbrella. EVERY LINE "
                      f"HERE IS `pub use` (B-15a rule 1): a plain `use` re-exports "
                      f"nothing, for any kind of symbol, and the failure appears in "
                      f"the consumer rather than here.")
    return fl"""),
]

EDITS["src/core/core.npk"] = [(
r"""// THE RE-EXPORT RULES ARE RX-113'S AND THEY ARE NOT STYLE. `use` is not
// transitive (`MODULE_REFERENCE.md` §2.3), so every line here is `pub use`, one
// name per line, and this file never plain-`use`s a path it also `pub use`s —
// a plain `use` above a `pub use` of the same path silently downgrades the
// re-export to nothing, AT NO DIAGNOSTIC, and the failure appears in the
// consumer as "cannot find X in this scope".""",
r"""// THE RE-EXPORT RULES ARE RX-113'S AND THEY ARE NOT STYLE. `use` is not
// transitive (`MODULE_REFERENCE.md` §2.3), so every line here is `pub use`, one
// name per line: a plain `use` re-exports nothing, and the failure appears in
// the consumer, not here. *(Until cycle 0.1.0 this said the file must never
// plain-`use` a path it also `pub use`s, because that silently cancelled the
// re-export -- the compiler's DEF-7, fixed at `94874ce`. Measured at `c970483`,
// a plain `use` of `./vec.npk` above or below these lines leaves every
// re-export intact, and RX-171 retires that rule.)*"""),
]

EDITS["src/lib.npk"] = [(
r"""// THREE RULES, EACH PAID FOR BY A MEASUREMENT IN 0.0.1. Break any of them and
// the failure appears in the CONSUMER, as `there is no type named X`, with
// nothing wrong at the line that caused it.
//
//   1. EVERY LINE HERE IS `pub use`. A plain `use` re-exports nothing.
//   2. THIS FILE NEVER PLAIN-`use`s A PATH IT ALSO `pub use`s. The first
//      import of a name wins and a later one is silently declined
//      (`symtab_bind_import`, `src/frontend/symbols.npk`), so a plain `use`
//      written above a `pub use` of the same path downgrades the re-export to
//      nothing AT NO DIAGNOSTIC. Provisional workbench question O-N13.""",
r"""// TWO RULES, EACH PAID FOR BY A MEASUREMENT IN 0.0.1. Break either and the
// failure appears in the CONSUMER, as `there is no type named X`, with nothing
// wrong at the line that caused it.
//
//   1. EVERY LINE HERE IS `pub use`. A plain `use` re-exports nothing.
//   2. RETIRED (RX-171). It said this file never plain-`use`s a path it also
//      `pub use`s, because a plain `use` above the `pub use` silently cancelled
//      the re-export -- the compiler's DEF-7 (workbench O-N13), fixed at
//      `94874ce`. Measured at `c970483`, it does not."""),
]

EDITS["meta/DECISIONS.md"] = [(
r"""### RX-113 — the umbrella re-exports with `pub use`, one name per line, and never plain-`use`s a path it re-exports
**2026-09-03, from building `src/lib.npk` and measuring what a consumer can""",
r"""### RX-113 — the umbrella re-exports with `pub use`, one name per line, and never plain-`use`s a path it re-exports
> **SUPERSEDED IN PART by RX-171 (@@DATE@@)** — its rule 2 and the every-file check its last paragraph asks
> for: a plain `use` above a `pub use` of the same path no longer cancels the re-export (the compiler's DEF-7,
> fixed at `94874ce`). Rules 1 and 3 stand.
**2026-09-03, from building `src/lib.npk` and measuring what a consumer can"""), (
r"""*Alternatives declined:* **keeping the old close** — the module's purpose is to
agree with the compiler, and it no longer would; **following the grammar and not
the lexer** — they agree now, and the day they part the lexer is still what reads
the files; **flipping line 23's expectation alone** — measured above as a case a
never-closing reader passes.
""",
r"""*Alternatives declined:* **keeping the old close** — the module's purpose is to
agree with the compiler, and it no longer would; **following the grammar and not
the lexer** — they agree now, and the day they part the lexer is still what reads
the files; **flipping line 23's expectation alone** — measured above as a case a
never-closing reader passes.

### RX-171 — B-15a's rule 2 is retired: a plain `use` above a `pub use` of the same path no longer cancels the re-export, and nothing else gave the rule a reason

**@@DATE@@, cycle 0.1.0 (the plan's PD-15), at compiler `c970483`.** It supersedes RX-113 in part — its
rule 2, *"the umbrella never plain-`use`s a path it also `pub use`s"*, and its last paragraph's promise of a
check that no file holds both. Rules 1 and 3 stand, and so does everything RX-113 measured.

**Why now.** Cycle 0.0's close found that the rule's one reason was a compiler defect — `symtab_bind_import`
returned a name's prior binding without merging a later `pub use`'s flags: the workbench registry's O-N13, the
compiler's DEF-7 — fixed at `94874ce` and struck as discharged at the fifth audit's triage, while live sites
still stated it as current (`meta/roadmap/done/0.0/0.0.5.md` §13, finding 1). It handed the decision to this
cycle, ahead of the first layer entry the library writes since the rule was made, `src/syntax/syntax.npk`.

**Measured**, each shape a one-line edit to a copy of the tree, each consumer through `npkc`, `llc`, `ld.lld`
and a run at −O0 and through `opt -O2`:

| the copy | at `950bb1d` | at `94874ce` | at `c970483` |
|---|---|---|---|
| unedited | runs 0 | runs 0 | runs 0 |
| `use "./api/api.npk".*;` above `src/lib.npk`'s `pub use` | **refused `NITPICK-RESOLVE-002`** at the consumer's `(ERegexPattern)` arm: the defect | runs 0 | runs 0 |
| `use "./api/api.npk".ERegexPattern;` above it: the same name | **refused `NITPICK-RESOLVE-002`** | runs 0 | runs 0 |
| that `pub use` made a plain `use` | refused `NITPICK-RESOLVE-002` | refused `NITPICK-RESOLVE-002` | refused `NITPICK-RESOLVE-002` |
| `use "./vec.npk".*;` above, and in another copy below, `src/core/core.npk`'s `pub use` lines | | | `vec_get_pod_struct` runs 0 |

The consumer at `950bb1d` and `94874ce` names the arms those compilers have, and at `c970483` the committed
`tests/conformance/import.npk` is the consumer. A file holding only `pub use` lines also uses the names it
re-exports, at `c970483` — a `pub use` binds its name in its own file — so no file needs a plain `use` of a path
for a name it re-exports.

**So rule 2 guarded against nothing, and its check never tested it alone.** `_check_umbrella` reads
`src/lib.npk` only, where rule 1's branch already fails every plain `use`; the check over every file that
RX-113 promised was never built. The branch goes and rule 1's stays. `BUILD.md` B-15a marks rule 2 retired,
and `CLAUDE.md`, `CONTRIBUTING.md` item 7, `harness/treecheck.py` and the headers of `src/core/core.npk` and
`src/lib.npk` stop stating the cancellation as current — eight sites: the seven the close named, and
`check_layering`'s docstring, which said the shape "produces NO DIAGNOSTIC" in the present tense.

*Alternatives declined:* **keeping rule 2 against a regression of DEF-7** — the compiler's own
`tests/accept/reexport/` guards the fix, and this library's consumer programs (`tests/conformance/import.npk`,
`tests/unit/vec_get_pod_struct.npk`) go red if a re-export they use stops working — RX-151 kept B-0 when its
mechanism expired because a second, true reason held it, and here none does; **keeping it as style** — a specification
states facts about the library, and this would state a lint with no failure behind it; **keeping it and
building the every-file check RX-113 promised** — a check needs a failure message, and this one could give no
true reason; **leaving it to the next audit** — the first layer entry written since is this subcycle's, and
cycle 0.0's close placed the decision before it.
"""),
]

EDITS = {path: [(old.replace("@@TQ@@", TQ), new.replace("@@TQ@@", TQ)) for old, new in pairs]
         for path, pairs in EDITS.items()}

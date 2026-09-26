r'''0.0.4e step 5 -- the harness and CI: `lexical.py` closes a block string at
`"""` (DEF-98, PD-14 -> RX-170), self-check case 18's line 23 made to read the two
closes differently in BOTH directions, `rx120.sh` and CI moved to the pin, and the
comments the re-pin makes false. Applied by `python3 e4e_edit.py harness "$REPO"`.

Texts that hold `"""` or a backslash are raw strings in triple single quotes, so each is the
FILE's bytes exactly -- `lexical.py`'s docstring spells a quote `\"`, and
`selfcheck.py`'s case-18 text spells a newline `\n`, as two characters each.
'''

EDITS = {}

# ------------------------------------------------------------------ harness/lexical.py
EDITS["harness/lexical.py"] = [
# (1) what it mirrors, and when it was read
(r'''WHAT IT MIRRORS, READ AT COMPILER `c3bdae2` WITH `git show`, NOT FROM A SUMMARY:
''',
r'''WHAT IT MIRRORS, READ AT COMPILER `c3bdae2` WITH `git show`, NOT FROM A SUMMARY
-- AND AGAIN AT `c970483` (cycle 0.0.4e), where `lexer.npk` differs only in the
block-string close below and `escapes.npk` and `p_parse_import` not at all:
'''),
# (2) the block-string bullet
(r'''  * `""` followed by anything but `"` is an EMPTY string; `\"\"\"` opens a BLOCK
    string, which closes at the first `""` not escaped by `\\` and consumes
    THREE BYTES there, whatever the third is. That is the lexer at `c3bdae2`
    (DEF-98), not `LEXICAL_REFERENCE.md` §6.3's grammar, which closes at `\"\"\"`;
    probe 15 records the refusal, self-check case 18 holds a block string with a
    `""` in its body and requires this reading (the fifth audit's N-28), and the
    re-pin that carries DEF-98's fix changes both.
''',
r'''  * `""` followed by anything but `"` is an EMPTY string; `\"\"\"` opens a BLOCK
    string, which closes at the first `\"\"\"` not escaped by `\\` -- a `""` in its
    body is two body characters -- and consumes those three. That is the lexer
    since the compiler's 1.6.0 step 3e (DEF-98), read at `c970483`, and
    `LEXICAL_REFERENCE.md` §6.3's grammar. THROUGH `c3bdae2` THE LEXER CLOSED AT
    THE FIRST `""` AND CONSUMED THREE BYTES THERE, AND SO DID THIS MODULE (RX-170):
    probe 15 records the verdict, and self-check case 18 holds a block string with
    a `""` in its body and a `use` after its close, and fails against the old close
    (the fifth audit's N-28).
'''),
# (3) the bare path is still unresolved at the new pin
(r'''nor `/`, which the compiler resolves against the dependency roots -- empty at
`c3bdae2`, so `NITPICK-RESOLVE-005` (measured) -- while the harness's callers join
''',
r'''nor `/`, which the compiler resolves against the dependency roots -- empty at
`c3bdae2` and `c970483`, so `NITPICK-RESOLVE-005` (measured at both) -- while the harness's callers join
'''),
# (4) case 18's promise
(r'''imports and the code the compiler would see at `c3bdae2`. Cases 19, 20 and 21
''',
r'''imports and the code the compiler would see at `c970483`. Cases 19, 20 and 21
'''),
# (5) the close itself
(r'''                if i + 2 < n and text[i + 2] == '"':
                    j = i + 3
                    while j < n:
                        if text[j] == '"' and j + 1 < n and text[j + 1] == '"':
                            break
''',
r'''                if i + 2 < n and text[i + 2] == '"':
                    # A BLOCK STRING CLOSES AT `"""` (DEF-98, the compiler's 1.6.0
                    # step 3e; RX-170) -- through `c3bdae2` at the first `""`.
                    j = i + 3
                    while j < n:
                        if (text[j] == '"' and j + 2 < n and text[j + 1] == '"'
                                and text[j + 2] == '"'):
                            break
'''),
]

# ---------------------------------------------------------------- harness/selfcheck.py
EDITS["harness/selfcheck.py"] = [
# (1) the comment above case 18's text
(r'''# Lines 20-22 are escaped paths, whose value is the decoded one (BL-9 (b)); 23 is
# a block string with a `""` in its body, which the lexer at `c3bdae2` closes
# there and consumes three bytes (DEF-98) -- so what follows is CODE, and the
# `use` in it is read; `LEXICAL_REFERENCE.md` §6.3's `"""` close reads none (N-28).
''',
r'''# Lines 20-22 are escaped paths, whose value is the decoded one (BL-9 (b)); 23 is
# a block string with a `""` in its body and a `use` in it, closed at `"""`, and a
# second `use` after the close. The lexer since the compiler's 1.6.0 step 3e
# (DEF-98; read at `c970483`) reads only the second; the lexer through `c3bdae2`
# closed at the first `""`, consuming three bytes, read the FIRST `use` as code,
# and opened a block that runs to the end of the text -- so each close reads the
# other's import and neither reads both (N-28; RX-170). Both readings were
# measured against the two compilers, `meta/roadmap/0.0/0.0.4e.md` §1.6.
'''),
# (2) line 23 itself
(r'''    'string:bs = """a""b use "./in_block_pin.npk".*; """x""!;\n'  # 23 an import AT c3bdae2
''',
r'''    'string:bs = """a""b use "./in_block.npk".*; """; use "./after_block.npk".*;\n'  # 23
'''),
# (3) its expectation
(r'''                (22, "./back\\slash.npk", False), (23, "./in_block_pin.npk", False)]
''',
r'''                (22, "./back\\slash.npk", False), (23, "./after_block.npk", False)]
'''),
# (4) the message
(r'''                               f"compiler's lexer does at c3bdae2")
''',
r'''                               f"compiler's lexer does at c970483")
'''),
]

# -------------------------------------------------------------- harness/treecheck.py
# the S-23a check's docstring and its failure message said `vec_get` MOVES an
# owning element out -- true through `c3bdae2`; since RX-168 it is refused
EDITS["harness/treecheck.py"] = [
('''    `vec_clear` and `vec_free` orphan what they discard. Measured at
    `c3bdae2`, and pinned per verb by the `vec_owning_*` units.
''',
'''    `vec_clear` and `vec_free` orphan what they discard. Measured at
    `c3bdae2`, and pinned per verb by the `vec_owning_*` units.
    *(Since cycle 0.0.4e, compiler `c970483`: `vec_get` takes `T: Pod` and an
    owning `T` is refused at compile time, NITPICK-TYPE-017 (RX-168). The six
    orphaning verbs are as stated, and this check is still the rule for them and
    the belt for `vec_get`, whose bound an impl declaring `move` defeats.)*
'''),
('''                    f"this check clears only what it can see owns nothing (RX-158): at "
                    f"an owning `T`, `vec_get` MOVES the element out of its slot and "
                    f"six verbs orphan what they discard, invisibly to `exit 0`. Keep "
''',
'''                    f"this check clears only what it can see owns nothing (RX-158): at "
                    f"an owning `T` six verbs orphan what they discard, invisibly to "
                    f"`exit 0`, and `vec_get` is refused only by its `Pod` bound (RX-168). Keep "
'''),
]

# ------------------------------------------------------------ harness/baseline/rx120.sh
EDITS["harness/baseline/rx120.sh"] = [
("""PIN=c3bdae2
OLD_PIN=950bb1d
""",
"""PIN=c970483
OLD_PIN=950bb1d
"""),
]

# ------------------------------------------------------------ .github/workflows/ci.yml
EDITS[".github/workflows/ci.yml"] = [
("""  # ../BOARD.md's pinned toolchain, by FULL sha. `c3bdae2` is the short form
  # used in the roadmap and the transcripts.
""",
"""  # ../BOARD.md's pinned toolchain, by FULL sha. `c970483` is the short form
  # used in the roadmap and the transcripts.
"""),
("""  # yet adopted. It is pushed only together with the adoption, so CI runs
  # once, on the adopted tree (`meta/roadmap/0.0/0.0.4b.md` §3).
  NITPICK_COMMIT: c3bdae270d63c93ab6e89825fddeec9425e2c6fd
""",
"""  # yet adopted. It is pushed only together with the adoption, so CI runs
  # once, on the adopted tree (`meta/roadmap/0.0/0.0.4b.md` §3).
  #
  # AND BUMPED @@DATE@@ FROM `c3bdae2` TO `c970483`, the end of the compiler's
  # 1.6.0 chain -- DEF-95 to DEF-106 and DEF-108 -- IN THE ADOPTION'S OWN COMMIT
  # (`meta/roadmap/0.0/0.0.4e.md`), so CI runs once, on the adopted tree. The
  # old tree does not compile at the new pin (`vec.npk`, NITPICK-TYPE-047) and
  # the new tree's refusals do not refuse at the old one, so neither commit
  # could be green alone.
  NITPICK_COMMIT: c9704830ea9c738f523bf6646a355f52679b3aee
"""),
("""      - name: RX-120's floor, syscaller and difference, asserted at `c3bdae2`
""",
"""      - name: RX-120's floor, syscaller and difference, asserted at `c970483`
"""),
]

# ------------------------------------------------------------------ the harness READMEs
EDITS["harness/README.md"] = [
("""ASSERTS floor == 5, syscaller == 6, difference == `{npk_sys6}` (at `c3bdae2`; 2 and 3 at `3d15ac9`)""",
 """ASSERTS floor == 5, syscaller == 6, difference == `{npk_sys6}` (at `c3bdae2` and `c970483`; 2 and 3 at `3d15ac9`)"""),
]
EDITS["harness/baseline/README.md"] = [
("""`rx120.sh` asserts 5 / 6 / `{npk_sys6}` at `c3bdae2`, and its `950bb1d` leg
""",
"""`rx120.sh` asserts 5 / 6 / `{npk_sys6}` at `c3bdae2` and at `c970483` (the
floor unchanged by the compiler's 1.6.0 chain, cycle 0.0.4e), and its `950bb1d` leg
"""),
]

# ------------------------------------------ the harness's three programs: TYPE-083 is in
# our pin now (N-22's sites). LINE COUNTS KEPT.
EDITS["harness/baseline/baseline.npk"] = [
("""    // compiler's 1.6.0 step 3c refuses it NITPICK-TYPE-083 (its DEF-96), landed on
    // the compiler's `main` at `d156c4f` -- no pin of ours carries it yet.
""",
"""    // compiler's 1.6.0 step 3c refuses it NITPICK-TYPE-083 (its DEF-96), landed at
    // `d156c4f` and in our pin since `c970483` (cycle 0.0.4e).
"""),
]
_T083_SC_OLD = """    // DEF-96, landed on its `main` at `d156c4f` -- no pin of ours carries it yet).
"""
_T083_SC_NEW = """    // DEF-96, landed at `d156c4f` and in our pin since `c970483`, cycle 0.0.4e).
"""
EDITS["harness/selfcheck/new_symbol_consumer.npk"] = [(_T083_SC_OLD, _T083_SC_NEW)]
EDITS["harness/selfcheck/syscall_consumer.npk"] = [(_T083_SC_OLD, _T083_SC_NEW)]
KEEP_LINES = ("harness/baseline/baseline.npk",
              "harness/selfcheck/new_symbol_consumer.npk",
              "harness/selfcheck/syscall_consumer.npk")

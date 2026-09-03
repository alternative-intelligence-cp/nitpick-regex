# Cycle 0.3 — Unicode

**`src/unicode/`: generated property, script and case-folding tables, and the
lookups over them.**

## Decisions in

RX-021, RX-022, RX-023. Settled.

**Open questions to settle:** Q-1 / O-U2 (the version to pin — data, not
design; recorded when chosen).

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.3.0 | **The generator** — `tools/gen_unicode.py`, the pinned UCD, the emitted shape | tables that regenerate byte-identically |
| 0.3.1 | **Properties and scripts** — the lookup, UAX #44 loose name matching | every alias in the UCD's own alias files resolves |
| 0.3.2 | **Perl and POSIX classes** — `UNICODE.md` §3's pinned definitions | `\w` is Annex C, not `[A-Za-z0-9_]` |
| 0.3.3 | **Case folding** — the inverse fold map, the orbit closure | `(?i)k` matches `U+212A`; `(?i)s` matches `U+017F` |
| 0.3.4 | **Class resolution** — 0.1's unresolved items to range lists, with the set operations | `[\p{L}&&\p{ASCII}]` is a sorted disjoint range list |
| 0.3.5 | **Close** — the table checks live | `done/0.3/`, `0.4.0.md` written |

## Checklist

### 0.3.0 — the generator
- [ ] Q-1 answered: the UCD version pinned, recorded in `src/unicode/version.npk` and in `meta/DECISIONS.md` beside RX-021
- [ ] reads `DerivedGeneralCategory.txt`, `Scripts.txt`, `ScriptExtensions.txt`, `DerivedCoreProperties.txt`, `PropList.txt`, `CaseFolding.txt`, `PropertyAliases.txt`, `PropertyValueAliases.txt`
- [ ] the UCD files themselves **gitignored**; the generated tables **committed**
- [ ] the emitted shape is `ClassRange { uint32:lo; uint32:hi; }` arrays, sorted and disjoint (U-4)
- [ ] every generated file carries the Unicode version and the generator's name in its header
- [ ] `check_tables_regenerate` live and **seen to fail** against a hand-edited table
- [ ] `check_table_invariants` live: sorted, disjoint, `lo <= hi`, every range within `U+10FFFF`, and **no range overlapping the surrogates** (C-3)

### 0.3.1 — properties and scripts
- [ ] General_Category (long and short), the category groups, Script, Script_Extensions, the standard binary properties
- [ ] UAX #44 loose matching: case, whitespace, `-` and `_` ignored in both name and value (U-6)
- [ ] **the gate**: every alias in `PropertyAliases.txt` and `PropertyValueAliases.txt` resolves to the same set as its canonical name
- [ ] `UnknownUnicodeProperty` with the offset, **never an empty class** (U-7) — an engine that silently matches nothing for a typo turns a mistake into a pattern that never fires
- [ ] **blocks refused**, naming `Script` (U-8, RX-023)

### 0.3.2 — Perl and POSIX classes
- [ ] `\d`, `\w`, `\s` and their complements, per `UNICODE.md` §3's table, in both Unicode and byte mode
- [ ] **`\w` is `[\p{Alphabetic}\p{M}\p{Nd}\p{Pc}\p{Join_Control}]`** (U-10) — a test asserts a Devanagari word and an emoji ZWJ sequence are matched by `\w+` without splitting
- [ ] complements taken **within the relevant universe** — all codepoints in Unicode mode, all 256 bytes in byte mode — with a test showing `\W` differs between the two
- [ ] the fourteen POSIX bracket classes, inside a class only

### 0.3.3 — case folding
- [ ] `CaseFolding.txt`'s `C` and `S` entries only (RX-022)
- [ ] the **inverse** fold map generated — fold target to every codepoint reaching it — because that is the direction the orbit computation needs (U-14)
- [ ] the orbit closure: for each codepoint in a class, add every codepoint folding to the same value
- [ ] **the gate**: `(?i)k` matches `U+212A` KELVIN SIGN and `(?i)s` matches `U+017F` LONG S. Those two assertions are the whole reason folding is a table and not `± 32`
- [ ] a test over the full `CaseFolding.txt` `C`+`S` set: folding each codepoint's singleton class produces its whole orbit
- [ ] full folding's affected codepoints enumerated into `docs/` as the documented limitation (U-12)

### 0.3.4 — class resolution
- [ ] 0.1's unresolved class items resolved to `ClassRange` lists
- [ ] union, intersection (`&&`), difference (`--`), symmetric difference (`~~`) over sorted range lists, with Y-17's precedence
- [ ] negation within the correct universe
- [ ] folding applied **at resolution**, so the engine never folds (U-13)
- [ ] `NREGEX_CLASS_RANGES` enforced; `ClassTooLarge`
- [ ] 0.2's `(?i:…)` hook filled, and its pending test now green

### 0.3.5 — close
- [ ] both table checks live and green
- [ ] the generated table sizes recorded, so a future version bump's diff is visible
- [ ] findings written; `0.4.0.md` written; archived

## Gate

`(?i)k` matches `U+212A` and `(?i)s` matches `U+017F`; every UCD alias
resolves; and `check_tables_regenerate` has been seen to fail.

## Watch for

- **`\w` is the one everybody gets wrong.** `[A-Za-z0-9_]` is the ASCII answer
  and it is not what UTS #18 says. Leaving out `\p{M}` splits Devanagari words;
  leaving out `\p{Join_Control}` splits emoji sequences.
- **`± 32` is not case folding.** Two codepoints outside the Latin range fold
  into ASCII, and a test asserts both.
- **The tables are `fixed` module state**, so they are read-only memory and cost
  nothing at run time. A table built at startup would be a different and worse
  thing.
- **The hot path never reads these tables** (U-4): a class is compiled into the
  program at 0.4/0.6. That is why the range-array representation is fine and
  why a trie would be optimising something that does not run.

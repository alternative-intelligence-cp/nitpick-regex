# Compilation: UTF-8 automata, alphabet compression, the program

HIR to an executable NFA program.

---

## 1. The shape

```
HIR ──► UTF-8 range compilation ──► alphabet compression ──► instruction emission ──► Program
        (codepoint classes to           (256 bytes to N          (a flat POD array)
         byte-range sequences)           equivalence classes)
```

**Rule C-1 (RX-031) — the program is a flat POD array with no owning field.**

```nitpick
pub struct:Inst = {
    InstKind:kind;
    uint32:a;        // kind-specific: goto, class index, capture slot, byte lo
    uint32:b;        // kind-specific: alternate goto, byte hi
};

pub struct:Program = {
    Vec<Inst>:insts;
    Vec<ByteSet>:classes;      // §3 — one per distinct byte class
    Vec<uint8>:byte_classes;   // 256 entries: byte -> equivalence class
    int32:start;
    int32:start_anchored;
    int32:capture_slots;
    uint32:flags;              // is-anchored, is-utf8, matches-empty
};
```

A `Program` is therefore **copyable, comparable, and dumpable** — which is what
makes a compiled program a committed fixture (`TESTING.md` §4) and a compiler
change a visible diff rather than a behaviour nobody can inspect.

---

## 2. UTF-8 range compilation

**Rule C-2 — a codepoint range becomes a set of byte-sequence ranges.** This is
the step that makes `UNICODE.md` U-18's byte decision real, and it is the least
obvious part of the library, so it is specified rather than left to the
implementation.

A codepoint range like `U+0080…U+07FF` is, in UTF-8, exactly the two-byte
sequences `[C2-DF][80-BF]`. A range that spans encoding-length boundaries —
`U+0000…U+10FFFF` — splits at each boundary first. A range that spans a
*prefix* boundary within a length splits again, because `U+0800…U+0FFF` is
`E0[A0-BF][80-BF]` while `U+1000…U+CFFF` is `[E1-EC][80-BF][80-BF]`: the lead
byte constrains the continuation range.

The algorithm is the standard one (`utf8-ranges`): split the codepoint range at
the encoding-length boundaries `0x7F`, `0x7FF`, `0xFFFF`, then recursively
split each piece so that every produced sequence is a product of independent
byte ranges. **It produces at most a handful of sequences per input range**,
and the bound is stated and tested.

**Rule C-3 — the surrogate range `U+D800…U+DFFF` is excluded from every
class**, in Unicode mode, before compilation. It has no UTF-8 encoding; a class
written as `[\u{0}-\u{10FFFF}]` is the two ranges either side of it.

**Rule C-4 — the produced byte automaton is an alternation of concatenations of
byte-range instructions**, sharing suffixes where the compiler can see them.
Suffix sharing is an **optimisation** and is subject to `ENGINES.md` R-3: with
it off, the answer is identical and the program is larger. A cross-check
compiles every corpus pattern both ways and requires the same match results.

**Rule C-5 — this is where a large class becomes a large program.** `\p{L}` is
about 700 codepoint ranges and several thousand byte-range instructions.
`NREGEX_PROGRAM_INSTRUCTIONS` is what bounds it, and `\p{L}{100}` is the
pattern that finds out whether the bound is right. The benchmark suite carries
it.

---

## 3. Alphabet compression

**Rule C-6 — the 256 byte values are partitioned into equivalence classes**,
where two bytes are equivalent when no instruction in the program
distinguishes them. A `byte_classes` table maps a byte to its class, and every
class instruction is over class indices rather than byte values.

**Rule C-7 — this is what makes the lazy DFA affordable.** A DFA transition
table is `states × alphabet`; at 256 symbols a state costs 1 KiB, and at the 8
or 12 classes a typical pattern actually distinguishes it costs 32 to 48 bytes.
For a pattern like `\d+` the alphabet compresses to three classes — digits,
everything else, and the end-of-input pseudo-symbol — which is a 60-fold
reduction in cache pressure.

**Rule C-8 — the partition is computed once, at compile time**, by a single
pass over every byte-range instruction accumulating boundary positions.
`ENGINES.md` §4 is its only consumer, and the Pike VM ignores it entirely.

**Rule C-9 — the identity partition is always valid.** If the computation is
ever wrong in the direction of *too few* classes the DFA is wrong; if it is
wrong in the direction of too many it is merely slower. So the test is not
"does it produce the expected partition" but a property: **for every byte pair
in the same class, every instruction accepts both or neither.** That is
checkable over the whole program in `O(insts × 256)` and it is checked in debug
builds and in the corpus stage.

---

## 4. The instruction set

**Rule C-10 (RX-030) — a closed list.** A tree check asserts every kind is emitted by
the compiler and handled by every engine and by the oracle.

| Kind | Meaning | Operands |
|---|---|---|
| `Match` | a match ends here | pattern id (for multi-pattern, §6) |
| `ByteRange` | consume one byte in `[a, b]`, then go to `goto` | `lo`, `hi`, `goto` |
| `ByteClass` | consume one byte in class `a`, then `goto` | class index, `goto` |
| `Split` | try `a` first, then `b` — zero width | `a`, `b` |
| `Jump` | go to `a` — zero width | `a` |
| `Save` | record the current offset in capture slot `a`, then `goto` | slot, `goto` |
| `Assert` | a zero-width assertion of kind `a` holds | kind, `goto` |
| `Fail` | never matches | — |

`Assert`'s kinds are `StartHaystack`, `EndHaystack`, `StartLine`, `EndLine`,
`WordBoundary`, `NotWordBoundary`.

**Rule C-11 — `Split` is ordered and the order is the semantics.** `a` is
preferred over `b`, and that is how greediness (`SYNTAX.md` Y-5) and
leftmost-first alternation (Y-3) are expressed. An engine that explores `b`
first is not faster, it is wrong.

**Rule C-12 — there is no `Char` instruction and no codepoint instruction.**
Everything is bytes, per `UNICODE.md` U-18. A literal `é` is two `ByteRange`
instructions.

---

## 5. Emission

**Rule C-13 — an explicit stack, never native recursion** (`SAFETY.md` S-19).
Emission walks the HIR, whose depth a pattern controls.

**Rule C-14 — repetition is expanded here**, under `NREGEX_REPEAT_PRODUCT`
which the HIR already checked (`HIR.md` H-8), so emission can expand without
re-deriving the bound. `a{2,4}` becomes `aa(a(a)?)?` in instructions;
`a{2,}` becomes `aa` followed by a `Split` loop.

**Rule C-15 — an unanchored search gets a `.*?` prefix**, compiled as a
`Split` loop over the "any byte" class, and its entry point is `start`. The
anchored entry point `start_anchored` skips it. Both are emitted always,
because the meta-engine chooses between them per search
(`API.md` §3's `find_at` starts anchored when the caller says so).

**Rule C-16 — capture slots are `2 × group_count`**, even and odd for the start
and end of each group, slot 0 and 1 being the whole match. `Save` instructions
are emitted only when captures are wanted: a program compiled for a
boolean `is_match` has none, which is what makes `is_match` eligible for the
one-pass and DFA engines (`ENGINES.md` §4).

---

## 6. Multi-pattern programs

**Rule C-17 — the program format admits several patterns**, each with its own
`Match` instruction carrying a pattern id, sharing one automaton behind one
`Split` fan-out at the start.

Included in the format at 1.0 and **not exposed in the API at 1.0**. The reason
to build the capability in now: retrofitting a pattern id into `Match` later
would change every engine's inner loop and every committed program fixture,
where reserving the field costs four bytes per `Match` instruction and nothing
else. The API for it (`RegexSet`) is cycle 1.1 material.

---

## 7. Determinism

**Rule C-18 — compiling the same pattern twice produces a byte-identical
program.** No hash iteration order, no address-derived value, no clock. This is
what makes a committed program fixture a real test, and it is the same property
the compiler requires of itself (D-078).

**Rule C-19 — the program is dumpable to a stable text form** and back. A
fixture is that text, a reviewer reads a diff of it, and the round trip is
tested. The dumper is `nregex`'s equivalent of an object dumper and it is what
makes a compiler regression a visible three-line diff rather than a mystery.

---

## 8. Open items

- **O-C1 — whether to share instruction suffixes across alternations.** A real
  size win on patterns with many similar branches, a real complication in
  emission. It is an optimisation subject to R-3, so it can be added later with
  the cross-check proving it changed nothing. Recommendation: not at 1.0.
- **O-C2 — reverse programs.** A reverse-compiled program lets a forward DFA
  find a match's end and a reverse DFA find its start, which is how Rust's
  regex avoids the Pike VM for simple captures. It doubles the compiler's
  output and needs its own correctness argument. Deferred to cycle 0.8, where
  the DFA's capture story is decided.

# Cycle 0.4 — UTF-8 automata

**`src/compile/`: codepoint ranges to byte-range sequences, and the alphabet
compressed into equivalence classes.** The step that makes RX-020's byte
decision real.

## Why here

Because it is the least obvious part of the library and everything after it
depends on being right. It is also entirely pure and entirely testable by
properties rather than examples, which is unusual and worth exploiting.

## Decisions in

RX-020. Settled. **No open questions.**

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.4.0 | **Range splitting** — encoding-length and prefix boundaries | `U+0000…U+10FFFF` produces the expected sequence set |
| 0.4.1 | **The byte automaton** — sequences to an alternation of concatenations | a class becomes a byte-level structure the compiler can emit |
| 0.4.2 | **Alphabet compression** — byte equivalence classes | `\d+` compresses to three classes |
| 0.4.3 | **Close** — the two property tests live | `done/0.4/`, `0.5.0.md` written |

## Checklist

### 0.4.0 — range splitting
- [ ] split at the encoding-length boundaries `0x7F`, `0x7FF`, `0xFFFF`
- [ ] recursive prefix splitting so every produced sequence is a **product of independent byte ranges** — `U+0800…U+0FFF` is `E0[A0-BF][80-BF]` while `U+1000…U+CFFF` is `[E1-EC][80-BF][80-BF]`, and getting that wrong admits over-long or out-of-range encodings
- [ ] **the surrogate range `U+D800…U+DFFF` excluded from every class** in Unicode mode (C-3), so `[\u{0}-\u{10FFFF}]` is the two ranges either side
- [ ] a stated and tested bound on sequences produced per input range
- [ ] **the gate**: an exhaustive round-trip — for every codepoint `0…0x10FFFF`, encode it and assert the produced automaton accepts exactly the codepoints in the input range and no others. Run over a set of ranges including every boundary
- [ ] a negative test: no produced sequence accepts an over-long encoding, a lone surrogate encoding, or a five-byte form

### 0.4.1 — the byte automaton
- [ ] sequences to an alternation of concatenations of byte-range instructions
- [ ] suffix sharing **behind a switch** (C-4, RX-041): with it off the answer is identical and the program larger, and the corpus runs both ways
- [ ] `NREGEX_PROGRAM_INSTRUCTIONS` enforced here, since this is where a large class becomes a large program (C-5)
- [ ] `\p{L}` compiled and its instruction count recorded — the number that tells us whether the bound is right

### 0.4.2 — alphabet compression
- [ ] one pass over every byte-range instruction accumulating boundaries
- [ ] a 256-entry `byte_classes` table, and class-indexed instructions
- [ ] **the property test** (C-9): for every byte pair in the same class, every instruction accepts both or neither — checked over the whole program in `O(insts × 256)`, in debug builds and in the corpus stage
- [ ] `\d+` compresses to three classes; `\p{L}+` to a stated small number; both recorded
- [ ] the identity partition always valid, so a bug in the direction of too many classes is slow and not wrong — stated in a comment, because it is what makes this safe to optimise later

### 0.4.3 — close
- [ ] `check_byte_class_partition` live
- [ ] findings written; `0.5.0.md` written; archived

## Gate

The exhaustive codepoint round trip, and the byte-class partition property over
every corpus program.

## Watch for

- **This is the cycle where a subtle bug silently omits a codepoint.** A class
  that accepts 99.99% of what it should looks correct in every hand-written
  test. The exhaustive round trip is the only thing that finds it, which is why
  it is the gate rather than a nice-to-have.
- **Over-long encodings are the security-relevant failure.** An automaton that
  accepts `C0 80` for `U+0000` is the classic UTF-8 validation bypass. The
  negative test is not optional.
- **The prefix-splitting recursion is on a bounded structure** (the codepoint
  range halves), so it is one of the few places native recursion would be
  defensible — and it still uses an explicit stack, because a tree check greps
  for self-calls and an exception would have to be argued.

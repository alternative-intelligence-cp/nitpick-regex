# Safety: the linear-time guarantee, the error budget, and the bounds

The constraints. Read this first. §2 contains the one decision the whole
library is arranged around, and it is the reason several things a reader will
expect from a regex library are absent.

---

## 1. What the language imposes

Each row is a language decision, not ours. The consequence column is what it
costs a library that compiles and executes patterns.

| Language rule | Where | Consequence for `nregex` |
|---|---|---|
| Borrows are second class — they never pass **up** the call stack | D-004, D-070 | **A `Match` cannot be a slice.** It carries byte offsets. §6, `API.md` §2 |
| A struct holding a borrow cannot be returned | D-004 | sub-views are built by struct literal at the call site, never returned from a helper |
| Owning values are move-only | TYPE-046 | **a value stored in an array declares no owning field** — instructions, HIR nodes, thread entries are all POD |
| Plain integer `+ - *` **traps** on overflow | D-210 | program-size and repetition arithmetic widens explicitly and narrows with `=>!` at a proven point |
| Indexing **a type that carries a length** is bounds-checked and traps | D-070 | a slice `T[]` and a fixed array `T[N]` trap; **a `wild T->` block does not** — and `Vec<T>.items` is one, so every index in this library is unchecked unless the library checks it. §5.3, RX-111 |
| `/` and `%` by zero trap | D-007 | no divisor is unproven on its path |
| There are **no closures** | D-018 | replacement is a template string or a bare function value; iteration is a struct with `next`, never a callback. `API.md` §5 |
| `failsafe`'s `pick` must **name** every reachable error | REACH-002 | **every public `error:` is an arm every consuming program owes.** §4 |
| Reachability is **import-scoped** | 1.4.8 | module decomposition is part of the budget |
| `exit 0` with live `wild` allocations traps | D-151 | every `wild` byte is paired on every path; the test programs exit 0 so a leaked **`wild` block** is a trap. **It sees nothing else** — D-151 counts `wild` blocks, D-188 counts live drivers, and neither sees a managed body, so a container freed without dropping its owning elements exits 0. §8b, RX-110 |
| There are no static methods | D-185 | construction is `regex_compile(pattern)`, never `Regex.new(…)` |
| No operator overloading | OP_REFERENCE | `a.eq(b)`, never `==`, on anything that is not a scalar |
| `comptime` cannot index a string | measured, §7 | **a compile-time-validated pattern literal is not currently expressible.** §7, O-G1 |
| `Default` is not derivable | D-123 | there is no default `Regex`; a pattern is always written |

**Read `../../nitpick/meta/specs/` rather than trusting this table.** It is a
summary of documents that are themselves the summary, and the compiler is
moving.

---

## 2. The linear-time guarantee, and what it costs

**Rule S-1 (RX-003) — a search runs in time bounded by `O(m · n)`**, where `m`
is the size of the compiled program and `n` is the length of the haystack in
bytes. There is no input, and no pattern, for which it is worse. The lazy DFA
brings the common case to `O(n)` amortised; the Pike VM is the floor and the
floor is still linear in `n`.

**The failure this exists to prevent.** A backtracking engine explores a search
tree, and for patterns with nested ambiguous quantifiers that tree is
exponential in the length of the input. `(a+)+$` against thirty `a`s and a `!`
takes longer than the age of the universe on every backtracking engine in
production use. It is called **catastrophic backtracking**, or ReDoS when
somebody does it to you deliberately, and it is:

- **triggered by data the attacker controls**, against a pattern that looks
  entirely reasonable;
- **invisible to review** — nothing about `(a+)+` says "this will hang";
- **not fixable by a timeout** in a language where a timeout means abandoning
  a task mid-computation, which Nitpick deliberately has no way to do
  (D-062: there is no cancellation, because there is no way to name a task).

In a language whose whole proposition is that a stop is controlled and chosen,
a library that lets a remote string hang the process is not one that belongs in
it. So the engine is a finite automaton, and the bound is structural.

**Rule S-2 — the price, stated plainly and not softened.**

| Absent | Because |
|---|---|
| **backreferences** (`(a)\1`) | the language they describe is not regular. Matching one is NP-hard in general, and every implementation does it by backtracking |
| **lookahead / lookbehind** (`(?=…)`, `(?<=…)`) | not regular either; intersection and complement of automata can express *some* of it, at a cost in program size that is exponential in the worst case, and the general case needs backtracking |
| **atomic groups** (`(?>…)`) and **possessive quantifiers** (`a*+`) | these are backtracking-*control* constructs. Under an automaton there is no backtracking to control, and pretending to honour them would change which strings match |
| **recursion / subroutine calls** (`(?R)`, `(?1)`) | context-free, not regular |

Each is **refused at compile time, by name, with the byte offset** — never
silently accepted and never quietly reinterpreted. A user who needs one needs a
parser, and `COMPAT.md` §4 says so with a pointer.

**Rule S-3 — a bounded backtracker was considered and is declined.** The
tempting middle path is a second engine behind an opt-in that supports
lookaround with a step budget, failing rather than hanging. It is declined for
1.0, on three grounds:

1. **It makes the guarantee conditional**, and a conditional guarantee is one
   every caller has to read the documentation to understand. "Linear, always"
   is a property; "linear unless you used this feature" is a footnote.
2. **The budget is a wrong answer, not a slow one.** A search that gives up
   returns "no match" or an error for a haystack that *does* match, and which
   one you get depends on the size of the input. That is worse than a refusal
   at compile time.
3. **It doubles the correctness surface** — a second engine that must agree
   with the first everywhere they overlap, tested by the same oracle, for a
   feature set the first cannot express.

Recorded as O-R1 rather than closed: if a consumer arrives with a real need,
the shape it would take is written down there.

---

## 3. What the guarantee buys

**Rule S-4 (RX-061) — matching cannot fail.** Every way a pattern can be wrong is found
when it is compiled. Once a `Regex` exists, a search returns a `Match` or the
absence of one:

```nitpick
Match?:m = regex_find(re, @cache, hay);      // NOT Result<Match?>
```

There is no error channel on the search path at all. This is the library's
cleanest property and several other rules exist to protect it.

**Rule S-5 — matching cannot trap.** No allocation (the `Cache` is
pre-allocated and reused, `ENGINES.md` §5), no division, no arithmetic that can
overflow at haystack scale, and every index through a checked accessor whose
bound is established by construction. The verification obligations in
`VERIFICATION.md` §3 are the machine-checked form of this claim.

**Rule S-6 — matching allocates nothing.** The `Regex` owns its program; the
`Cache` owns every scratch buffer. A search touches neither allocator.

**Rule S-7 — a `Regex` is immutable and shareable.** The mutable state a lazy
DFA needs is in the caller's `Cache`, not in the `Regex`, so a `Regex` may be
borrowed by any number of threads at once with no lock. `ENGINES.md` §5 has the
reasoning; it is the single most consequential API decision after §2.

---

## 4. The error budget

**Rule S-8 (RX-060) — `nregex` declares exactly ONE public `error:` identity.**

```nitpick
pub error:ERegexPattern;    // the pattern could not be compiled
```

**Importing `nregex` costs your program's `failsafe` exactly one arm.** That is
the strongest statement in this document and it falls out of §2 and §4
together: compilation is the only thing that can fail, and a shutdown handler
does not care *which* way a pattern was malformed.

**Rule S-9 — the detail is a value, not an identity.** `regex_compile` returns
`Result<Regex>`; on failure the caller reads a `PatternError`:

```nitpick
pub struct:PatternError = {
    PatternErrorKind:kind;    // §4.1 — the closed list
    int64:offset;             // byte offset into the pattern
    int64:span_len;           // 0 when the position is a point
    uint32:detail;            // kind-specific: the offending codepoint, the bound exceeded
};
```

Thirty ways a pattern can be malformed are thirty `PatternErrorKind` variants
and **one** error identity, because REACH-002 counts identities and not
variants. A caller that wants to report "unclosed group at byte 14" has
everything it needs; a `failsafe` that wants to stop has one arm.

### 4.1 `PatternErrorKind`

A closed enum, exhaustive over everything the parser and the compiler can
refuse. The list is normative and lives in `SYNTAX.md` §9 beside the grammar
that produces each one; it includes the four §2 refusals
(`BackreferenceUnsupported`, `LookaroundUnsupported`,
`AtomicGroupUnsupported`, `RecursionUnsupported`), each of which names the
guarantee in its message rather than saying "unsupported".

**Rule S-10 — a harness check enforces the budget.** The count and names of
public `error:` declarations are diffed against this section on every full run.
A second identity is a **major version** (RX-005), because it is a
compiler-enforced source break in every consumer.

**Rule S-11 — module decomposition keeps the budget honest.** REACH is
import-scoped, and `nregex`'s layering (`BUILD.md` §6) puts `core`, `unicode`
and `hir` below the error: a program importing `nregex/unicode.npk` to ask
whether a codepoint is alphabetic owes **nothing**.

---

## 5. Bounds

**Rule S-12 (RX-062) — every bound is a named constant in `src/core/limits.npk`, and
nowhere else.** A tree check enforces it. Exceeding one at compile time is a
`PatternError`; there is nothing to exceed at match time.

| Constant | Default | Bounds |
|---|---|---|
| `NREGEX_PATTERN_BYTES` | 65536 | the pattern text |
| `NREGEX_NEST_DEPTH` | 250 | group and alternation nesting — the parser's explicit stack (§8) |
| `NREGEX_PROGRAM_INSTRUCTIONS` | 100000 | the compiled program |
| `NREGEX_REPEAT_MAX` | 1000 | a single `{n,m}` bound |
| `NREGEX_REPEAT_PRODUCT` | 100000 | the **product** across nested repetitions — §5.1 |
| `NREGEX_CAPTURE_GROUPS` | 250 | capture groups, named and numbered |
| `NREGEX_CLASS_RANGES` | 20000 | codepoint ranges in one class after folding |
| `NREGEX_DFA_CACHE_BYTES` | 2 MiB | the lazy DFA's state cache, per `Cache` — §5.2 |
| `NREGEX_DFA_MIN_STATES` | 32 | below this the DFA gives up permanently rather than thrashing |

Each is overridable at compile time through a `RegexOptions` value, and each
has a test sitting exactly on it and one exceeding it.

### 5.1 The repetition bomb

**Rule S-13 (RX-015).** `a{1000}` is a thousand instructions. `(a{1000}){1000}` is a
million, and `((a{1000}){1000}){1000}` is a billion — a pattern of thirty
characters that would exhaust memory during *compilation*. This is the
program-size analogue of ReDoS and it is closed the same way: by a bound, not
by a timeout.

`NREGEX_REPEAT_PRODUCT` is checked **as the HIR is built**, multiplying
nesting factors on the way down, so the refusal happens before the memory is
requested rather than after. The multiply is a `uint64` widening with the
narrow refused if it would exceed the bound, per D-210.

### 5.2 The DFA cache

**Rule S-14 (RX-042) — the lazy DFA's cache never grows past its budget and
never fails.** When it is full it is cleared and rebuilt; if clearing happens too
often to be worth it (measured as states-per-byte falling below a threshold),
the meta-engine **abandons the DFA for that search and falls back to the Pike
VM**, which needs no cache and is still linear.

The user never sees this. It changes the time, never the answer, and
`TESTING.md` §5's cross-engine oracle is what proves that.

### 5.3 Indexing, and what D-070 does not cover

**Rule S-23 (RX-111) — a `wild T->` block is indexed without a bounds check, so
every `Vec` access in this library is checked by this library or not at all.**

D-070's guarantee attaches to types that carry a length:

| Type | Carries a length | Out-of-range index |
|---|---|---|
| slice `T[]` | yes — `{ ptr, len }` | **traps**, `OutOfBounds` |
| fixed array `T[N]` | yes — in the type | **traps**, `OutOfBounds` |
| `wild T->` block | **no** — a bare pointer | **reads**, silently |
| `buffer`, through `.ptr` | the *value* carries `.len`; **the index does not use it** | **reads**, silently (RX-118) |

**The `buffer` row is not the exception it looks like** (RX-118). A `buffer`
does carry `.len` and `.cap`, so it reads like a checked type — but there is no
route from a `buffer` to a slice: `buffer_bytes` is on the compiler's
*"deliberately NOT landed"* list (`TYPE_REFERENCE.md` §23), and §23's own
example gives the byte access as `buf.ptr[0i64]`. `.ptr` is a `uint8->`, so
every byte of a `buffer` is reached through row three, and `.len` sits beside
the index doing nothing unless this library compares against it.

Measured as a pair, same offset and same program shape:
`tests/probe/probe08c_slice_index_traps.npk` (a slice, index 999 into four
elements) exits **94**; `tests/probe/probe08b_wild_index_unchecked.npk` (a
`wild int64->` block, the same index) exits **0**, having read 7 992 bytes past
its allocation and returned the result.

**`Vec<T>.items` is a `wild T->`** (RX-006), so `Program.insts`, `Hir.nodes`,
`Program.classes`, the Pike VM's thread lists and the sparse set are all in the
second category. This is not a compiler defect — `wild` is the language's
unchecked primitive and says so in its name. It was an error in this document,
which read a language guarantee onto a type that never carried it.

**What follows, and it is the reason this rule is in the safety document rather
than a style note:**

- **The "one accessor pair" is now load-bearing.** Every read and write of a
  `Vec` goes through `vec_get` / `vec_set`, which check against `count`, and a
  tree check enforces that no `.items[` appears outside `src/core/vec.npk`.
  **`Bytes` owes the identical pair over its `buffer`** (RX-118): `bytes_get` /
  `bytes_set` checking against `len`, and no `.ptr[` outside
  `src/core/bytes.npk`. `Bytes` is `BUILD.md` B-11's byte sink and every
  replacement in this library is composed into one, from bytes a caller
  controls — so it is the second-most exposed accessor here and it was outside
  this rule until the `buffer` row was added.
  Before this rule that pair was tidiness; it is now the only bounds check.
- **An unchecked index is a WRONG ANSWER, not a crash.** That inverts the
  failure mode §1 advertises. A wrong program counter in an engine reads an
  unrelated heap word as an instruction; a wrong sparse-set probe adds a thread
  for a state the automaton is not in and the library returns a match that is
  not there. Both are silent, and both are reachable from bytes the caller does
  not control.
- **Signedness is half the check.** An index derived from an `int32` field can
  be negative, `n < count` accepts it, and a negative index reads backwards off
  the block. Every accessor checks `0 <= i` as well as `i < count`.
- **`TESTING.md`'s fuzzer invariants gain one**: no accessor is ever called
  with an out-of-range index, asserted in the debug build.

---

## 6. Offsets, not slices

**Rule S-15 (RX-050).** A slice is a second-class borrow: it passes down the
call stack and never up (D-004, D-070). A function therefore **cannot return
one**, so:

```nitpick
pub struct:Match = { int64:start; int64:end; };     // byte offsets, half-open
```

The caller slices its own haystack. This is not a workaround — it is better
than the alternative in three ways that are worth stating, because a reader
arriving from Rust will expect `&str` and should know why they are not being
short-changed: a `Match` is a plain 16-byte value that can be stored in a
`Vec`, sent through a channel, and held across an `await`; the haystack's
lifetime is the caller's business and not encoded in a type; and offsets are
what a caller wants anyway when the haystack is a mapped file.

**Rule S-16.** Offsets are **byte** offsets into the haystack, always, and they
always land on a UTF-8 boundary when the pattern was compiled in Unicode mode
(`UNICODE.md` §6). Never codepoint indices and never character counts.

---

## 7. What cannot be done today, and is wanted

**Rule S-17 — a compile-time-validated pattern literal is not currently
expressible, and this was measured rather than assumed.**

The obvious safety win for this library would be `#regex("…")` — a macro or
`comptime` form that parses the pattern **while compiling the program**, so a
malformed pattern is a compile error and `regex_compile` never fails at run
time at all. Nitpick has a real `comptime` interpreter with loops, mutable
locals and `comptime func:` calls (`MACRO_REFERENCE.md` §8), so this looks
available.

It is not. Measured at the compiler's cycle 1.5.0, reading
`src/frontend/resolve_type.npk`:

- `fold_expr` dispatches on integer, bool, char and string literals; `comptime`
  expressions; unary, binary, cast and unchecked-cast expressions; builtins;
  identifiers; calls; the iteration variable; and `raw` unwraps. **There is no
  arm for an index expression, a member access, an array literal or a struct
  literal.**
- `fold_string_builtin` handles exactly four names — `string_concat`,
  `string_equals`, `string_byte_length`, `string_is_empty`.

So a `comptime func:` can concatenate, compare and measure a pattern string,
and cannot **look at a byte of it**. A pattern walker is not expressible, and
therefore neither is compile-time validation.

The gap is small — one more `fold_expr` arm for indexing a string literal, or
`string_slice` in the foldable set — and the payoff is a property no regex
library in any language offers. It is raised as **O-G1** and this section is
the evidence for the request.

*(A related documentation defect found in the same reading:
`MACRO_REFERENCE.md` §8 says "a `const` global folds", and `const` was retired
from the language at 1.4.2c by D-222. The implementation is correct — it checks
`QUAL_FIXED` — so this is stale prose, raised as **O-G2**.)*

---

## 8. Adversarial input

`nregex` is handed patterns and haystacks that somebody else may control, and
both are attack surfaces.

**Rule S-18 — no native recursion anywhere on a path whose depth an input
controls.** The pattern parser uses an **explicit stack** with
`NREGEX_NEST_DEPTH` entries (`SYNTAX.md` §3). A recursive-descent parser on
`((((((…` blows the call stack, and the language has no stack-depth guard —
the failure is a segfault, not a controlled stop, which is precisely what this
ecosystem exists to prevent.

**Rule S-19 — the same rule applies to every HIR and program walk.** Desugaring,
literal extraction and program emission all walk a tree that a pattern
controls the depth of, and all three use an explicit stack.

**Rule S-20 — the haystack is never validated as UTF-8.** It is `uint8[]`.
Matching over invalid UTF-8 is defined (`UNICODE.md` §6) rather than refused,
because a systems library that can only search validated text cannot search a
network buffer.

**Rule S-21 — the fuzzer's invariants are stated** (`TESTING.md` §7): never
traps, always terminates, never allocates during a search, the answer agrees
with the naive oracle, and every engine agrees with every other.

---

## 8b. What the leak gate actually covers

**Rule S-22 (RX-110) — `exit 0` proves that no `wild` block was left live, and
proves nothing else.** The formulation to use, because it is exact:

> **D-151 counts `wild` blocks, D-188 counts live drivers, and neither sees a
> managed body.**

A `string`'s body, a `Vec`'s owning elements and a `dyn`'s cell are *managed*.
Freeing a container's block does **not** drop its elements, and the controlled
exit does not notice: `nitpick-time` measured a `Vec<string>` retaining
**125 MiB over two million elements at exit 0**, and the same program hit
`HeapOom` only when squeezed under a 64 MiB address-space cap.

**What follows for this library, concretely:**

- **`Program`, `Hir` and every engine's thread list are POD** (C-1, H-2,
  `ENGINES.md` R-6), so for those the block *is* the whole obligation and
  `exit 0` covers it exactly. This is not luck — it is TYPE-046 forcing the
  representation, and it is the main practical reason the POD shape is worth
  its awkwardness.
- **The exceptions are the ones to watch**: `Hir.names`, `Vec<GroupInfo>` if a
  group name is ever an owning `string` rather than an offset into `Bytes`, and
  any future `Vec<string>`. Each must drop its elements before its block goes.
- **Where the obligation is managed, the gate is a memory cap, not an exit
  code** (`TESTING.md` §7's invariant list is the place it belongs).
- **A better instrument is coming.** The compiler's `NPK_HEAP_STATS` will make
  retained managed bytes measurable rather than inferable; when it lands, this
  rule's test becomes a `peak_live` assertion and the memory cap becomes a
  backstop.

**Do not write "the suite's programs exit 0, so a missing `free` on any path is
a trap" without saying which allocations that covers.** It was written four
different ways in this repository's own plan and was false of managed bodies in
every one of them.

---

## 9. Open items

- **O-S1 — whether `RegexOptions` should be a `comptime` parameter rather than
  a value.** A `comptime` bound would let the program-size limit be a type-level
  fact and the arrays be fixed. Against: it makes `Regex` generic over its
  options, which infects every signature that takes one. Recommendation: a
  plain value. Decide at cycle 0.10.

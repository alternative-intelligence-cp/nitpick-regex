# Linear-time matching of lookaround assertions — research digest

**As of 2026-10-01.** Question: is there a published algorithm that matches regular expressions with lookahead and
lookbehind assertions (and without backreferences) in time O(m·n), linear in the haystack's length for a fixed
pattern? Does any shipping regex engine implement linear-time lookaround matching? *(Asked by the planner of
`roadmap/0.1/0.1.5.md` for its PD-56, the sentence `LookaroundUnsupported` reads, which said lookaround "cannot be
matched in linear time"; answered by the workbench's researcher agent, ten fetches, and filed by the planner as
returned, its first person made impersonal, but for one bullet that named the agent's local copies of the papers,
which no reader here can open.)*

## Answer

Yes. Two peer-reviewed papers from 2024, both in PACMPL, give non-backtracking lookaround matching in O(m·n):

- **Mamouras and Chattopadhyay (POPL 2024, Article 92).** O(m · n) for all four kinds: positive and negative
  lookahead, positive and negative lookbehind. Nesting is arbitrary and lookbehind length is unbounded. The grammar
  has no capture groups and no backreferences. Lookahead needs right-to-left passes; lookbehind alone can be matched in
  one streaming pass.
- **Barrière and Pit-Claudel (PLDI 2024, Article 201).** O(|r| × |s|) in two variants:
  - Captureless lookbehinds, positive and negative and nested, in any regex language. This one streams and needs no
    extra space.
  - All JavaScript lookarounds, including capture groups inside them, with extra O(ℓ(r) × |s|) space. This variant
    relies on a JavaScript-specific rule ("Capture Reset").

A third paper, RE# (Varatalu, Veanes, Ernits; read as arXiv v1, 2024), is linear in |s|. It only allows lookarounds at
the edges of a match, with lookaround-free bodies, and its state space can grow exponentially in the pattern.

On regularity: Mamouras and Chattopadhyay state, citing Morihata 2012 and Miyazaki and Minamide 2019, that matching with
lookaround can be decided by finite automata. The cost is a doubly exponential DFA, or an exponential NFA, in the worst
case.

On shipping engines: V8's linear engine, which ships in Chrome and Node.js, accepts captureless lookbehinds in its
current source, but not for global or sticky regexps. With the extra flag
`experimental_regexp_engine_capture_group_opt` it also accepts lookaheads and capturing lookbehinds. The engine itself
is reached only through a command-line flag; that comes from the 2024 paper, and today's default was not checked.
.NET's `RegexOptions.NonBacktracking` does not allow lookarounds at all. So the claim "it cannot be matched in linear
time" is false as of 2026-10-01.

## Evidence

- <https://kmamouras.github.io/papers/regex-lookaround-draft-POPL'24.pdf> — retrieved 2026-10-01. This is the authors'
  copy, and it prints "Proc. ACM Program. Lang., Vol. 8, No. POPL, Article 92. Publication date: January 2024", DOI
  10.1145/3632934. The publisher page <https://dl.acm.org/doi/10.1145/3632934> returned HTTP 403.
  - "Additionally, we propose a new algorithm for matching regular expressions with lookaround that has time complexity
    O(m · n), where m is the size of the regular expression and n is the length of the input text."
  - "Our approach is fully general in that we allow the arbitrary nesting of unrestricted lookahead and lookbehind
    assertions."
  - Definition 1's grammar has ε, predicates, +, ·, \*, "(?>r) [positive lookahead] | (?≯r) [negative lookahead] |
    (?<r) [positive lookbehind] | (?≮r) [negative lookbehind]". There are no captures and no backreferences.
  - On PCRE's limit on lookbehind length: "The algorithm we will present later in Section 4 does not have this
    limitation."
  - Notation note: in Fig. 1, (?>r) holds at i when r matches the whole rest of the text [i,|w|]. So PCRE's (?=r) is
    written (?>r Σ\*), as in Example 4.
  - "We note that our algorithm is not streaming in the general case because it performs right-to-left passes over the
    input text to deal with lookahead assertions efficiently. If the regular expression contains no lookahead
    assertions, then the algorithm can deal with lookbehind in a streaming manner (single left-to-right pass over the
    input text)."
  - "While it is known that the membership problem for regular expressions with lookaround can be solved using
    finite-state automata (see, for example, [Morihata 2012] and [Miyazaki and Minamide 2019]), these automata are
    very large due to the succinctness of lookaround. A DFA of doubly exponential size is needed in the worst case (and
    therefore an NFA of exponential size)."
  - On Berglund et al. 2021: "membership can be decided in O(m · n) time with a right-to-left pass over the input
    string that simulates the AFA execution "in reverse". This approach does not handle lookbehind assertions."
  - "Existing automata-based regex engines (grep, RE2, Hyperscan) do not support lookaround at all."
  - Their implementation is a research prototype: "a Rust implementation of our algorithm".
- <https://arxiv.org/abs/2311.17620> and <https://arxiv.org/pdf/2311.17620> — retrieved 2026-10-01. Version 2 (23 Jul
  2024), which prints "Proc. ACM Program. Lang. 8, PLDI, Article 201 (June 2024)", DOI 10.1145/3656431.
  - "We further advance the state-of-the-art in linear regex matching by presenting the first nonbacktracking
    algorithms for matching lookarounds in linear time: one supporting captureless lookbehinds in any regex language,
    and another leveraging a JavaScript property to support unrestricted lookaheads and lookbehinds."
  - The §1 table gives "Captureless Lookbehinds … O(|r| × |s|) §4.4" and "Unrestricted Lookarounds … O(|r| × |s|)†
    §4.3", with "†: with an additional O(|r| × |s|) space complexity".
  - §4.3: "We now present an algorithm to match all JavaScript lookarounds (both lookaheads and lookbehinds, both
    positive and negative) in linear time." It adds: "This algorithm comes with an additional space complexity of
    O(ℓ(r) × |s|) for the oracle where ℓ(r) ≤ |r| is the number of lookarounds in r."
  - §4.4, which the paper calls "a novel separate streaming algorithm": "In particular, all negative lookbehinds are
    supported, as they cannot define capture groups (see Section 3.2). Compared to the previous section, this algorithm
    needs no additional space complexity. It does not use the Capture Reset property and is thus applicable to any
    regex language, not just JavaScript. This algorithm supports nested lookbehinds and capture groups outside of
    lookbehinds."
  - On backreferences: "It is well-known, for example, that backreferences make the matching problem NP-hard [Aho
    1990; Dominus 2000]."
  - On V8: "We implemented several of our algorithms in V8Linear, with some having been merged and released in V8
    already." Footnote 2 lists "Lookbehinds https://chromium-review.googlesource.com/c/v8/v8/+/5093860". V8Linear is
    "available through a command-line flag."
- <https://raw.githubusercontent.com/v8/v8/main/src/regexp/experimental/experimental-compiler.cc> — retrieved
  2026-10-01 from the main branch; no revision hash recorded.
  - In `CanBeHandledVisitor::VisitLookaround`: `if (IsGlobal(flags()) || IsSticky(flags())) { result_ = false;`
  - Then: `// If \`experimental_regexp_engine_capture_group_opt\` is false, reject all // lookaheads or capturing
    lookbehinds.` followed by `if (!v8_flags.experimental_regexp_engine_capture_group_opt && (node->type() ==
    Lookaround::LOOKAHEAD || node->capture_count() > 0)) {`
- <https://learn.microsoft.com/en-us/dotnet/standard/base-types/regular-expression-options> — retrieved 2026-10-01.
  The page was updated 2026-07-08 (docs commit 34593ddd0173186c7930898a919593a8e6fa65b5).
  - "Match using an approach that avoids backtracking and guarantees linear-time processing in the length of the
    input. (Available in .NET 7 and later versions.)"
  - "It also doesn't allow for the following constructs in the pattern:" The list includes "Lookarounds".
- <https://arxiv.org/pdf/2407.20479> — retrieved 2026-10-01. RE#, version 1 (30 Jul 2024); this copy prints no venue.
  - "We develop the theory formally and show that the main matching algorithm has input-linear complexity both in
    theory as well as experimentally."
  - "Theorem 4 (InputLinearity). The complexity of LLMatch(s, R) is linear in |s|."
  - The grammar is "R ::= E | R1&R2 | (?<=E)·R | (?<!E)·R | R·(?=E) | R·(?!E)", where E has no lookarounds. "in RE#
    lookbacks are only allowed to match context before the actual match and lookaheads after it."
  - "the state space can still grow exponentially with respect to the size of the regex in the worst case."

## What would change this

The condition was met: an O(m·n) algorithm has been published and peer-reviewed (POPL 2024, PLDI 2024). Under the
request's own plan, that means three things:

1. The refusal sentence must drop "it cannot be matched in linear time" and give nregex's own reason.
2. K-1's example gets a dated note.
3. S-2's row goes to the author as a finding:
   - "not regular either" is contradicted, because finite automata decide matching with lookaround.
   - "*some* of it" understates the case; all of it can be expressed.
   - "the general case needs backtracking" is contradicted by both 2024 algorithms.
   - The exponential program-size clause holds for translation to plain automata (an exponential NFA or a doubly
     exponential DFA), but not for the oracle-NFA approach.

One thing for the planner to know: if nregex also guarantees a single pass, or memory that does not grow with the
haystack, the general lookahead algorithms do not meet that. They need right-to-left passes, and Barrière's §4.3 needs
O(ℓ(r)×|s|) extra space. Captureless lookbehind does meet it: it streams and needs no extra space. Whether that space
cost is unavoidable was not established. Mamouras's contribution (5) mentions an optimisation "to reduce the memory
footprint to O(m)", and how far it applies was not read.

## Confidence and gaps

- **The algorithm question: high confidence.** Two independent peer-reviewed sources, read in the authors' copies,
  which print the PACMPL reference lines. They were not compared word for word with ACM's versions of record, since
  the ACM page returned 403.
- **Shipping engines: medium confidence.**
  - The fetch of V8's `flag-definitions.h` was cut off before the regexp flags, so whether the linear engine, or
    `experimental_regexp_engine_capture_group_opt`, is on by default today was not checked. "Command-line flag" comes
    from the 2024 paper.
  - Chromium change 5093860 was not opened.
  - RE#'s publication venue, and whether it is released as a package, were not verified.
  - Rust `regex`, RE2, Go, Hyperscan and PCRE2 at their current versions were not surveyed.
- **The classical regularity fact** rests on Mamouras and Chattopadhyay's statement. Morihata 2012 and Miyazaki and
  Minamide 2019 were not opened. For Berglund et al. (J.UCS 2021), the landing page showed metadata only, and the PDF
  redirected to public.pensoft.net, which was not followed because of the budget.
- **Leads not opened:** <https://dl.acm.org/doi/10.1145/3703595.3705884> ("Verified and Efficient Matching of Regular
  Expressions with Lookaround") and <https://arxiv.org/pdf/2603.26139> (2026, on the complexity of JavaScript regex
  matching).
- **Budget:** all 10 fetches used.

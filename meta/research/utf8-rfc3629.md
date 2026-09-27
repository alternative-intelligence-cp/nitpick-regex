# Well-formed UTF-8 — research digest

**As of 2026-09-27.** Question: which byte sequences are well-formed UTF-8, exactly, for a validator that refuses
every other one?

## Answer

RFC 3629 (STD 63, November 2003, obsoleting RFC 2279) defines them in §4's ABNF: one to four bytes, a lead from
`00`–`7F`, `C2`–`DF`, `E0`–`EF` or `F0`–`F4`, with the second byte narrowed after four leads — `E0` takes
`A0`–`BF` (no overlong), `ED` takes `80`–`9F` (no surrogate), `F0` takes `90`–`BF` (no overlong), `F4` takes
`80`–`8F` (nothing above U+10FFFF) — and every other continuation `80`–`BF`. So `80`–`C1` and `F5`–`FF` never
start a character. `parse_check_encoding` (cycle 0.1.1) is this table, case for case.

## Evidence

- https://www.rfc-editor.org/rfc/rfc3629.html — retrieved 2026-09-27 — §4:
  "UTF8-2 = %xC2-DF UTF8-tail / UTF8-3 = %xE0 %xA0-BF UTF8-tail / %xE1-EC 2( UTF8-tail ) / %xED %x80-9F UTF8-tail /
  %xEE-EF 2( UTF8-tail ) / UTF8-4 = %xF0 %x90-BF 2( UTF8-tail ) / %xF1-F3 3( UTF8-tail ) / %xF4 %x80-8F 2(
  UTF8-tail ) / UTF8-tail = %x80-BF"; the header: "STD: 63", "Obsoletes: 2279", "November 2003".

## What would change this

A successor RFC or an erratum narrowing the table would change the validator's ranges. Neither is known; the
table has matched the Unicode Standard's well-formed sequences since RFC 3629 was published.

## Confidence and gaps

High for the table, quoted from the primary. The fetch returned the document, not the RFC Editor's errata or
obsoletion index; that index is re-read at the hardening cycle (1.0), with this row.

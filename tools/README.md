# `tools/` — generators and instruments

`gen_unicode.py` (the property, class and case-folding tables), `fetch_corpora.py`
(the third-party conformance suites, by pinned revision), `fuzz_pattern.py` (the
structured pattern-and-haystack fuzzer). Everything a generator emits is
**committed as source** and checked by regeneration — a hand-edited generated
file is the failure that prevents.

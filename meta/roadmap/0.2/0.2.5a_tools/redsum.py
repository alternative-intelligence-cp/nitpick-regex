#!/usr/bin/env python3
"""0.2.5a -- a RED harness log, its failures classified: block 0r's reading of the unchanged tree at `c9baa9e`.

    python3 -B redsum.py <harness.log>

Prints the run's units line; its failures by suite; how many of them NAME landing 113's one site,
`NITPICK-PARSE-001` at `src/syntax/parse.npk:223:16`, over how many files; the rejection verdicts that report
`NITPICK-PARSE-001` where their file names another code (a parse refusal stands in front of the checker, so the
site is the census's to give, block 0b); the `PENDING.txt` lines no pending unit matched; and every other failure,
whole -- which a reading of the tree at this pin must not have. `../0.2.1a_tools/facts.sh`'s §1.2 reading, as a tool.
"""
import collections
import re
import sys

SITE = "NITPICK-PARSE-001 src/syntax/parse.npk:223:16"


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    t = open(argv[1], errors="replace").read()
    fails = re.findall(r"^FAIL  ([a-z-]+)/(\S+?): (.*)$", t, re.M)
    by = collections.Counter(s for s, p, r in fails)
    site = [(s, p) for s, p, r in fails if SITE in r]
    rej = [(s, p) for s, p, r in fails if SITE not in r and re.search(r"expected NITPICK-[A-Z]+-\d+, got NITPICK-PARSE-001 \|", r)]
    pend = [(s, p, r) for s, p, r in fails if s == "pending-list"]
    other = [(s, p, r) for s, p, r in fails if (s, p) not in site and (s, p) not in rej and s != "pending-list"]
    m = re.search(r"^\d+/\d+ unit\(s\) passed", t, re.M)
    print("the run: %s" % (m.group(0) if m else "no units line"))
    print("%d failure(s): %s" % (len(fails), ", ".join("%s %d" % kv for kv in sorted(by.items()))))
    print("  %d name %s, over %d file(s)" % (len(site), SITE, len({p for s, p in site})))
    print("  %d are rejection verdicts reporting NITPICK-PARSE-001 where the file names another code, over %d file(s): %s"
          % (len(rej), len({p for s, p in rej}), " ".join(sorted({p.rsplit("/", 1)[1] for s, p in rej}))))
    print("  %d are PENDING.txt lines no pending unit matched: %s"
          % (len(pend), " ".join(re.search(r"names `([^`]+)`", r).group(1).rsplit("/", 1)[1] for s, p, r in pend)))
    print("  %d other" % len(other))
    for s, p, r in other:
        print("    %s/%s: %s" % (s, p, r[:150]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

#!/usr/bin/env python3
"""`nitpick.toml`, read the way `npkg` reads it -- P-10.

WHY A READER AND NOT `tomllib`. Python 3.11's `tomllib` would parse this file
and would accept things `npkg`'s reader does not, so a manifest that worked
here could be refused by the tool this harness retires into (RX-004). The
subset is the compiler's: tables, `[[array]]` headers, strings, integers,
booleans and single-line arrays, and nothing else -- `npkg/manifest.npk`'s own
words at 950bb1d.

THE SCHEMA CHECK IS THE POINT. `npkg` refuses a key its schema lacks; so does
this. A key nothing reads is the next stale document (D-204), and a manifest
whose typo'd key is silently ignored is worse than one that fails.
"""
import re


class ManifestError(Exception):
    pass


# Every (table, key) the compiler's schema has, read out of `npkg/manifest.npk`
# `schema_allows` at 950bb1d. `[dependencies]` takes any key by design.
SCHEMA = {
    "project":   {"name", "version", "description", "authors", "target"},
    "build":     {"entry", "output", "opt-level"},
    "toolchain": {"llvm", "llc-flags", "llc-opt-flags", "opt-flags", "lld-flags"},
    "test":      {"name", "stage", "kind", "path", "paths", "recursive"},
    "verify":    {"z3", "z3-version", "z3-sha256", "z3-options"},
}
ANY_KEY = {"dependencies"}

# `npkg`'s stage vocabulary, and the two extensions this library declares as
# its own (`BUILD.md` §3's dagger rows). A stage this harness cannot judge is
# refused by name rather than skipped -- an undeclared stage silently doing
# nothing is the "green while checking nothing" failure the manifest's own
# header was written to prevent.
KNOWN_STAGES = {"parse", "accept", "check", "compile", "program", "runtime",
                "verify", "corpus", "oracle"}
KNOWN_KINDS = {"positive", "negative", "diagnostic"}

_TABLE = re.compile(r'^\[([A-Za-z0-9_.-]+)\]$')
_ARRAY_TABLE = re.compile(r'^\[\[([A-Za-z0-9_.-]+)\]\]$')
_KEYVAL = re.compile(r'^([A-Za-z0-9_-]+)\s*=\s*(.*)$')


def _strip_comment(line):
    """A `#` outside a string starts a comment. The manifest has no `#` inside one."""
    out, in_str = [], False
    for ch in line:
        if ch == '"':
            in_str = not in_str
        if ch == "#" and not in_str:
            break
        out.append(ch)
    return "".join(out).strip()


def _value(raw, where):
    raw = raw.strip()
    if raw.startswith("["):
        if not raw.endswith("]"):
            raise ManifestError(f"{where}: a multi-line array -- the reader takes "
                                "single-line arrays only, as npkg's does")
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [_value(p, where) for p in _split_top(inner)]
    if raw.startswith('"') and raw.endswith('"') and len(raw) >= 2:
        return raw[1:-1]
    if raw in ("true", "false"):
        return raw == "true"
    try:
        return int(raw)
    except ValueError:
        raise ManifestError(f"{where}: {raw!r} is not a string, integer, boolean "
                            "or single-line array")


def _split_top(inner):
    parts, cur, in_str = [], [], False
    for ch in inner:
        if ch == '"':
            in_str = not in_str
        if ch == "," and not in_str:
            parts.append("".join(cur))
            cur = []
            continue
        cur.append(ch)
    if "".join(cur).strip():
        parts.append("".join(cur))
    return [p for p in parts if p.strip()]


class Manifest:
    def __init__(self, tables, tests, path):
        self.tables = tables
        self.tests = tests
        self.path = path

    def get(self, table, key, default=None):
        return self.tables.get(table, {}).get(key, default)

    def need(self, table, key):
        if key not in self.tables.get(table, {}):
            raise ManifestError(f"{self.path}: [{table}] has no `{key}`")
        return self.tables[table][key]


def read(path):
    tables, tests = {}, []
    section, target = None, None
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        text = _strip_comment(line)
        if not text:
            continue
        where = f"{path}:{n}"
        m = _ARRAY_TABLE.match(text)
        if m:
            section = m.group(1)
            if section != "test":
                raise ManifestError(f"{where}: [[{section}]] -- the only array "
                                    "table the schema has is [[test]]")
            target = {}
            tests.append(target)
            continue
        m = _TABLE.match(text)
        if m:
            section = m.group(1)
            if section not in SCHEMA and section not in ANY_KEY:
                raise ManifestError(f"{where}: [{section}] is not a table the "
                                    f"schema has ({', '.join(sorted(set(SCHEMA) | ANY_KEY))})")
            target = tables.setdefault(section, {})
            continue
        m = _KEYVAL.match(text)
        if not m:
            raise ManifestError(f"{where}: {text!r} is neither a table header "
                                "nor `key = value`")
        if target is None:
            raise ManifestError(f"{where}: `{m.group(1)}` before any table header")
        key = m.group(1)
        if section not in ANY_KEY and key not in SCHEMA.get(section, set()):
            allowed = ", ".join(sorted(SCHEMA.get(section, set())))
            raise ManifestError(f"{where}: [{section}] has no key `{key}` in the "
                                f"schema (it has: {allowed}). A key nothing reads "
                                "is the next stale document -- D-204.")
        if key in target:
            raise ManifestError(f"{where}: `{key}` given twice in [{section}]")
        target[key] = _value(m.group(2), where)
    _check_tests(tests, path)
    return Manifest(tables, tests, path)


def _check_tests(tests, path):
    seen = set()
    for i, t in enumerate(tests):
        where = f"{path}: [[test]] #{i + 1}"
        for k in ("name", "stage"):
            if k not in t:
                raise ManifestError(f"{where}: no `{k}`")
        if t["name"] in seen:
            raise ManifestError(f"{where}: `{t['name']}` is declared twice")
        seen.add(t["name"])
        if t["stage"] not in KNOWN_STAGES:
            raise ManifestError(f"{where} ({t['name']}): stage `{t['stage']}` is not "
                                f"one of {', '.join(sorted(KNOWN_STAGES))}")
        if "kind" in t and t["kind"] not in KNOWN_KINDS:
            raise ManifestError(f"{where} ({t['name']}): kind `{t['kind']}` is not "
                                f"one of {', '.join(sorted(KNOWN_KINDS))}")
        if "path" not in t and "paths" not in t:
            raise ManifestError(f"{where} ({t['name']}): neither `path` nor `paths`")
        if "path" in t and "paths" in t:
            raise ManifestError(f"{where} ({t['name']}): both `path` and `paths`")


def paths_of(t):
    """`path` is a directory and never a file; `paths` is a list of them (RX-119)."""
    if "paths" in t:
        return list(t["paths"])
    return [t["path"]]

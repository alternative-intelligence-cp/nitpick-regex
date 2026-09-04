#!/usr/bin/env python3
"""The toolchain is a build input (D-204), so it is asserted and not reported.

The manifest pins a PATCH release, so every check is exact: a patch release may
change instruction selection, and a suite that ran on a different `llc` than
the one the manifest names has measured a different compiler.

ASKS THE TOOLS, NOT `llvm-config` (step 2). `llvm-config` ships in the `-dev`
package, which a machine that can build and link this library does not
otherwise need; asking `llc`, `opt` and `ld.lld` themselves asks the three
binaries that actually run.
"""
import os
import re
import subprocess

_VERSION = re.compile(r"\b(\d+\.\d+\.\d+)\b")


class ToolchainError(Exception):
    pass


def _ask(tool):
    try:
        r = subprocess.run([tool, "--version"], capture_output=True, text=True,
                           timeout=30)
    except FileNotFoundError:
        raise ToolchainError(f"`{tool}` is not on PATH -- it is one of the three "
                             "binaries `nitpick.toml` [toolchain] pins, and "
                             "skipping a check because its tool is missing is how "
                             "a defect ships")
    except subprocess.TimeoutExpired:
        raise ToolchainError(f"`{tool} --version` did not answer in 30 s")
    m = _VERSION.search(r.stdout + r.stderr)
    if not m:
        raise ToolchainError(f"`{tool} --version` printed no version this reader "
                             f"could find: {(r.stdout + r.stderr).strip()[:120]!r}")
    return m.group(1)


def check(llvm_version, out):
    """Every tool at exactly the pinned version. Raises on the first mismatch."""
    for tool in ("llc", "opt", "ld.lld"):
        got = _ask(tool)
        if got != llvm_version:
            raise ToolchainError(
                f"`{tool}` is {got} and nitpick.toml [toolchain] llvm pins "
                f"{llvm_version} exactly. A patch release may change instruction "
                "selection, so this is a refusal and not a warning (D-204).")
        out(f"ok    {tool} {got}")


def compiler(out):
    """`$NPKC` and `$NPKRT`: the pinned pair the board names (W-18)."""
    got = {}
    for var, what in (("NPKC", "the pinned npkc binary"),
                      ("NPKRT", "the pinned npkrt.o runtime object")):
        p = os.environ.get(var, "")
        if not p:
            raise ToolchainError(f"${var} is not set; it must name {what}. The "
                                 "orchestrator supplies it, or set it by hand from "
                                 "`../.internal/toolchain/<commit>/`.")
        if not os.path.isfile(p):
            raise ToolchainError(f"${var} is {p!r}, which is not a file")
        got[var] = os.path.abspath(p)
        out(f"ok    ${var} -> {got[var]}")
    return got["NPKC"], got["NPKRT"]

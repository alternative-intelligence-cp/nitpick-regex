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


_LAYOUT = re.compile(r'^target datalayout = "([^"]*)"$', re.M)


def check_target(triple, datalayout, out):
    """The layout pin is what the pinned `opt` derives from the triple pin.

    The compiler's `check_datalayout_pin` (its harness, since its landing 71: E-8,
    D-322 (5)), ported at cycle 0.1.0b -- RX-176. Every module states a `target
    datalayout`; `opt` keeps a wrong one as written and `llc` accepts one in
    silence, so a stated layout proves nothing about itself. This holds the PIN to
    the toolchain, and `build.module_header` holds every linked emission to the
    pin. Raises on a mismatch, like every other check here (D-204)."""
    try:
        r = subprocess.run(["opt", "-S", "-"], input=f'target triple = "{triple}"\n',
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as e:
        raise ToolchainError(f"`opt -S` over the triple probe failed: {e}")
    m = _LAYOUT.search(r.stdout)
    if r.returncode != 0 or not m:
        raise ToolchainError("`opt -S` over a module stating only the pinned triple "
                             "wrote no `target datalayout` line: "
                             f"{(r.stderr or r.stdout).strip()[:160]!r}")
    if m.group(1) != datalayout:
        raise ToolchainError(
            f"nitpick.toml [toolchain] pins the layout {datalayout!r}, but the pinned "
            f"`opt` derives {m.group(1)!r} from the triple {triple!r} -- the layout "
            "every module states must be the one the toolchain lays the binary out "
            "under (E-8, D-322 (5)).")
    out(f"ok    target {triple}, its layout the one the pinned opt derives")


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

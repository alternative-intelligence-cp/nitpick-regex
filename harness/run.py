#!/usr/bin/env python3
"""nregex's build and test runner -- A STUB. It checks the toolchain and nothing else.

WHAT THIS IS NOT, YET. The real runner is cycle 0.0.2 and 0.0.3: the manifest
reader, the module-graph walk, the build pipeline, the `compile`, `parse`,
`check` and `program` stages, the differential undefined-symbol scan (RX-116),
and the self-check that proves the runner can FAIL. None of that is here.

WHY IT EXISTS NOW. CI is cycle 0.0.1's deliverable and CI needs something to
run. The danger with a placeholder runner is the one `nitpick.toml`'s own header
names: a suite that reports green while checking nothing. So this stub checks
the one thing that is genuinely checkable today and would otherwise go
unchecked until 0.0.2 -- THAT THE TOOLCHAIN IS THE PINNED ONE -- and it says, on
every run and in its exit line, that it checks nothing else.

`npkg` cannot build this library (O-G3), which is why a Python runner exists at
all (RX-004); it retires into `npkg` the day that closes.
"""
import os
import subprocess
import sys

LLVM_VERSION = "20.1.2"          # nitpick.toml [toolchain] llvm -- D-204: the toolchain is a build input
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def fail(msg):
    print(f"FAIL  {msg}")
    return False


def check_llvm():
    """The manifest pins a PATCH release, so the check is exact (D-204)."""
    try:
        out = subprocess.run(["llvm-config", "--version"],
                             capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        return fail(f"llvm-config did not run: {e}")
    if out != LLVM_VERSION:
        return fail(f"LLVM is {out}, and nitpick.toml pins {LLVM_VERSION} exactly. "
                    "A patch release may change instruction selection.")
    print(f"ok    llvm-config --version == {LLVM_VERSION}")
    return True


def check_tool(env_name, what):
    path = os.environ.get(env_name, "")
    if not path:
        return fail(f"${env_name} is not set; it must name {what}")
    if not os.path.isfile(path):
        return fail(f"${env_name} is {path!r}, which is not a file")
    print(f"ok    ${env_name} names an existing {what}")
    return True


def main():
    print("nregex harness -- STUB (cycle 0.0.1). It checks the toolchain and NOTHING ELSE.")
    print(f"      tree: {ROOT}")
    ok = True
    ok &= check_llvm()
    ok &= check_tool("NPKC", "npkc binary")
    ok &= check_tool("NPKRT", "npkrt.o runtime object")
    if not ok:
        print("\nSTUB FAILED. The toolchain is not the pinned one.")
        return 1
    print("\nSTUB PASSED, AND THAT IS A STATEMENT ABOUT THE TOOLCHAIN ALONE.")
    print("No source was compiled, no test was run, and no suite in nitpick.toml")
    print("was read. A green run here is not evidence about this library.")
    print("The runner that judges the suites is cycle 0.0.2 (meta/roadmap/0.0/0.0.2.md).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

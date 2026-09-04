#!/usr/bin/env python3
"""An ELF64 relocatable object's symbol table, read with `struct` -- P-11.

WHY NOT `llvm-nm`. The undefined-symbol scan is a BUILD STEP and law here
(`BUILD.md` B-2, RX-008). Resting law on a fourth tool outside the manifest's
pin, parsed out of text nothing checks, is the weaker of the two designs; the
format is forty lines of `struct`. `llvm-nm` is still what the committed
transcripts show, because a transcript should be re-runnable by hand, and
`selfcheck` diffs this reader against it (cycle 0.0.3).

The reader refuses anything that is not a little-endian ELF64 relocatable for
x86-64 rather than guessing, because a silently mis-parsed symbol table is a
scan that reports clean.
"""
import struct

SHT_SYMTAB = 2
SHN_UNDEF = 0
STB_LOCAL = 0
STT_FILE = 4
STT_SECTION = 3


class ElfError(Exception):
    pass


class Obj:
    def __init__(self, path):
        self.path = path
        with open(path, "rb") as fh:
            self.b = fh.read()
        self._header()
        self._sections()
        self._symbols()

    def _header(self):
        b = self.b
        if len(b) < 64 or b[:4] != b"\x7fELF":
            raise ElfError(f"{self.path}: not an ELF file")
        if b[4] != 2:
            raise ElfError(f"{self.path}: not ELF64 (EI_CLASS={b[4]})")
        if b[5] != 1:
            raise ElfError(f"{self.path}: not little-endian (EI_DATA={b[5]})")
        (self.e_type, self.e_machine) = struct.unpack_from("<HH", b, 16)
        if self.e_type != 1:
            raise ElfError(f"{self.path}: e_type={self.e_type}, not a relocatable "
                           "object (ET_REL=1)")
        if self.e_machine != 62:
            raise ElfError(f"{self.path}: e_machine={self.e_machine}, not x86-64 (62)")
        (self.shoff,) = struct.unpack_from("<Q", b, 40)
        (self.shentsize, self.shnum) = struct.unpack_from("<HH", b, 58)
        if self.shentsize != 64:
            raise ElfError(f"{self.path}: e_shentsize={self.shentsize}, not 64")

    def _sections(self):
        self.sections = []
        for i in range(self.shnum):
            off = self.shoff + i * self.shentsize
            (name, typ, flags, addr, soff, size, link, info,
             align, entsize) = struct.unpack_from("<IIQQQQIIQQ", self.b, off)
            self.sections.append(dict(name=name, type=typ, offset=soff, size=size,
                                      link=link, entsize=entsize))

    def _str(self, strtab_idx, off):
        s = self.sections[strtab_idx]
        base = s["offset"] + off
        end = self.b.index(b"\0", base)
        return self.b[base:end].decode("utf-8", "replace")

    def _symbols(self):
        self.syms = []
        for sec in self.sections:
            if sec["type"] != SHT_SYMTAB:
                continue
            if sec["entsize"] != 24:
                raise ElfError(f"{self.path}: sh_entsize={sec['entsize']} on a "
                               "symtab, not 24")
            n = sec["size"] // 24
            for i in range(n):
                off = sec["offset"] + i * 24
                (nm, info, other, shndx, value, size) = struct.unpack_from(
                    "<IBBHQQ", self.b, off)
                name = self._str(sec["link"], nm) if nm else ""
                self.syms.append(dict(name=name, bind=info >> 4, type=info & 0xF,
                                      shndx=shndx))

    def undefined(self):
        """What `llvm-nm --undefined-only` prints: named, SHN_UNDEF, not local."""
        return sorted({s["name"] for s in self.syms
                       if s["shndx"] == SHN_UNDEF and s["name"]
                       and s["bind"] != STB_LOCAL})

    def defined(self):
        return sorted({s["name"] for s in self.syms
                       if s["shndx"] != SHN_UNDEF and s["name"]
                       and s["type"] not in (STT_FILE, STT_SECTION)})


def undefined(path):
    return Obj(path).undefined()

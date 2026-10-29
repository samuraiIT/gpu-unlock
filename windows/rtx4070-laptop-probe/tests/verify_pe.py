# SPDX-License-Identifier: MIT
"""Build checks; explicit failures remain active under python -O."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_headers(vendor):
    vendor = vendor.resolve()
    entries = json.loads((vendor / 'headers.json').read_text(encoding='utf-8-sig'))['files']
    require(bool(entries), 'Empty header manifest')
    actual = {p.relative_to(vendor).as_posix() for p in (vendor / 'Include').rglob('*.h')}
    require(actual == set(entries), 'Missing or unlisted vendor headers')
    for name, expected in entries.items():
        path = (vendor / name).resolve()
        require(path.is_relative_to(vendor), 'Header path escapes vendor directory')
        require(hashlib.sha256(path.read_bytes()).hexdigest() == expected.lower(),
                'Vendor header hash mismatch: ' + name)
    return len(entries)


def verify_pe(data):
    def value(fmt, offset):
        require(0 <= offset <= len(data) - struct.calcsize(fmt), 'Truncated PE structure')
        return struct.unpack_from(fmt, data, offset)[0]

    def u16(offset):
        return value('<H', offset)

    def u32(offset):
        return value('<I', offset)

    require(data[:2] == b'MZ', 'Missing DOS signature')
    pe = u32(0x3c)
    require(data[pe:pe + 4] == b'PE\0\0' and u16(pe + 4) == 0x8664, 'Not x64 PE')
    opt = pe + 24
    opt_size = u16(pe + 20)
    require(opt_size >= 240 and opt + opt_size <= len(data), 'Invalid optional header')
    require(u16(opt) == 0x20b and u16(opt + 68) == 10, 'Not a PE32+ EFI application')
    require(u32(opt + 108) >= 16, 'Missing PE data directories')
    for index in (1, 9, 14):
        require(u32(opt + 112 + index * 8) == 0 and u32(opt + 116 + index * 8) == 0,
                'Unexpected import/TLS/CLR directory')
    reloc_rva, reloc_size = u32(opt + 152), u32(opt + 156)
    require(reloc_rva != 0 and reloc_size >= 8, 'Missing relocations')
    entry = u32(opt + 16)
    entry_ok = reloc_ok = False
    sections = u16(pe + 6)
    require(0 < sections <= 32, 'Invalid section count')
    for i in range(sections):
        off = opt + opt_size + i * 40
        virtual_size, rva = u32(off + 8), u32(off + 12)
        raw_size, raw = u32(off + 16), u32(off + 20)
        require(raw + raw_size <= len(data), 'Section exceeds file')
        flags = u32(off + 36)
        entry_ok |= bool(flags & 0x20000000 and rva <= entry < rva + min(raw_size, virtual_size))
        reloc_ok |= bool(rva <= reloc_rva and reloc_rva + reloc_size <= rva + raw_size)
    require(entry_ok and reloc_ok, 'Entry point or relocations not backed by a section')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--headers-only', action='store_true')
    args = parser.parse_args()
    count = verify_headers(ROOT / 'vendor/edk2')
    print(f'PASS: {count} pinned vendor headers')
    if args.headers_only:
        return
    verify_pe((ROOT / 'build/RTX4070-PROBE.EFI').read_bytes())
    source = '\n'.join(p.read_text(encoding='utf-8') for p in (ROOT / 'src').glob('*.c'))
    for forbidden in ('->Mem.Read', '->Mem.Write', '->Pci.Write', 'SetVariable(',
                      'DisconnectController(', 'ConnectController(', 'SampleProm(', 'SampleRegisters('):
        require(forbidden not in source, 'Forbidden source access: ' + forbidden)
    require('mobile_mmio_unqualified' in source, 'Missing MMIO exclusion marker')
    capture = json.loads((ROOT / 'build/host-capture.json').read_text(encoding='utf-8'))
    require(capture['gpu_writes'] is False and capture['mmio_reads'] is False
            and capture['unlock_attempted'] is False, 'Mock capture claims GPU access')
    require(capture['unique_expected_identity_observed'] is True, 'Mock target not observed')
    print('PASS: x64 EFI, bounded sections, entry, relocations, no imports/TLS/CLR; mock JSON and source checks')


if __name__ == '__main__':
    main()

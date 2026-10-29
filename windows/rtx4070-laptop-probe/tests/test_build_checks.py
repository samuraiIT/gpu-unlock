# SPDX-License-Identifier: MIT
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
import verify_pe


class BuildChecks(unittest.TestCase):
    def test_manifest_rejects_changed_missing_and_extra_headers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'Include').mkdir()
            header = root / 'Include/a.h'
            header.write_bytes(b'original')
            (root / 'headers.json').write_text(json.dumps({'files': {
                'Include/a.h': hashlib.sha256(b'original').hexdigest()}}))
            self.assertEqual(verify_pe.verify_headers(root), 1)
            header.write_bytes(b'modified')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                verify_pe.verify_headers(root)
            header.unlink()
            with self.assertRaisesRegex(ValueError, 'Missing or unlisted'):
                verify_pe.verify_headers(root)
            header.write_bytes(b'original')
            (root / 'Include/extra.h').write_bytes(b'unlisted')
            with self.assertRaisesRegex(ValueError, 'Missing or unlisted'):
                verify_pe.verify_headers(root)

    def test_real_binary_and_corrupt_pe(self):
        binary = (verify_pe.ROOT / 'build/RTX4070-PROBE.EFI').read_bytes()
        verify_pe.verify_pe(binary)
        for damaged in (b'', binary[:64], b'XX' + binary[2:]):
            with self.assertRaises(ValueError):
                verify_pe.verify_pe(damaged)
        pe = struct.unpack_from('<I', binary, 0x3c)[0]
        for directory in (1, 9, 14):
            damaged = bytearray(binary)
            struct.pack_into('<I', damaged, pe + 24 + 112 + directory * 8, 1)
            with self.assertRaisesRegex(ValueError, 'import/TLS/CLR'):
                verify_pe.verify_pe(damaged)


if __name__ == '__main__':
    unittest.main()

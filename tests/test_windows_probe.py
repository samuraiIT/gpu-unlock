# SPDX-License-Identifier: GPL-2.0-only
import contextlib
import ctypes
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('windows_probe', Path(__file__).parents[1] / 'tools' / 'windows_probe.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

class ProbeTests(unittest.TestCase):
    def test_pci_and_exact_profile(self):
        pci = probe.decode_pci(0x282010de, 0x01571558, 0xa1, 0x2820)
        self.assertTrue(probe.profile_match(pci))
        self.assertEqual(pci['external_device_id_raw'], 0x2820)
        self.assertEqual(pci['pci_revision_id'], 0xa1)
        pci['pci_revision_id'] = 0xa0
        self.assertFalse(probe.profile_match(pci))
        del pci['pci_revision_id']
        self.assertFalse(probe.profile_match(pci))
        pci['pci_revision_id'] = 0xa1
        pci['subsystem_device_id'] = 1
        self.assertFalse(probe.profile_match(pci))
        self.assertFalse(probe.profile_match({}))

    def test_platform_error(self):
        with patch.object(probe.sys, 'platform', 'unsupported'):
            result = probe.probe()
        self.assertEqual(result['errors'][0]['stage'], 'platform')
        self.assertFalse(result['windows_unlock_supported'])
        self.assertFalse(result['hardware_unlock_tested'])

    def test_multi_gpu_json_and_exit_error(self):
        data = {'gpus': [{'errors': []}, {'errors': [{'stage': 'pci', 'status': -1}]}], 'errors': []}
        with patch.object(probe, 'probe', return_value=data), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(probe.main([]), 1)
        self.assertEqual(json.loads(out.getvalue()), data)

    def test_refuses_existing_output_before_probe(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'data.json'
            path.write_text('keep')
            with patch.object(probe, 'probe') as run, self.assertRaises(FileExistsError):
                probe.main(['--output', str(path)])
            run.assert_not_called()
            self.assertEqual(path.read_text(), 'keep')

    def test_nvapi_lifecycle_and_errors(self):
        def run(init=0, enum_status=0, count=1, getter_status=0):
            calls = []
            def fn(key, _args):
                def invoke(*args):
                    calls.append(key)
                    if key == 'initialize':
                        return init
                    if key == 'enum':
                        ctypes.cast(args[1], ctypes.POINTER(probe.U32))[0] = count
                        if count and count <= probe.MAX_GPUS:
                            args[0][0] = 42
                        return enum_status
                    if key == 'name':
                        return getter_status
                    return 0
                return invoke
            with patch.object(probe.sys, 'platform', 'win32'), patch.object(probe, 'load_query', return_value=fn):
                result = probe.probe()
            return result, calls
        result, calls = run(init=-1)
        self.assertEqual(result['errors'][0]['stage'], 'initialize')
        self.assertNotIn('unload', calls)
        for kwargs in ({'enum_status': -1}, {'count': 65}, {'count': 0}):
            result, calls = run(**kwargs)
            self.assertEqual(result['errors'][0]['stage'], 'enum')
            self.assertEqual(calls.count('unload'), 1)
        result, calls = run(getter_status=-3)
        self.assertEqual(result['gpus'][0]['errors'], [{'stage': 'name', 'status': -3}])
        self.assertEqual(calls.count('unload'), 1)

if __name__ == '__main__':
    unittest.main()

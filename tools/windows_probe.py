# SPDX-License-Identifier: GPL-2.0-only
"""Read-only NVAPI inventory; no GPU writes or privileged driver access."""
import argparse
import ctypes
import json
import sys
from pathlib import Path

U32 = ctypes.c_uint32
MAX_GPUS = 64
IDS = {'initialize': 0x0150e828, 'unload': 0xd22bdd7e,
       'enum': 0xe5ac921f, 'name': 0xceee8e9f, 'pci': 0x2ddfb66e,
       'arch': 0xd8265d24, 'vbios': 0xa561fd7d, 'bus': 0x1be0b8e5}

class ArchInfo(ctypes.Structure):
    _fields_ = [('version', U32), ('architecture', U32),
                ('implementation', U32), ('revision', U32)]

def decode_pci(device, subsystem, revision, external):
    return {'internal_device_id_raw': device, 'external_device_id_raw': external,
            'subsystem_id_raw': subsystem, 'pci_revision_id': revision,
            'vendor_id': device & 0xffff, 'device_id': device >> 16,
            'subsystem_vendor_id': subsystem & 0xffff,
            'subsystem_device_id': subsystem >> 16}

def profile_match(pci):
    return all(pci.get(k) == v for k, v in {
        'vendor_id': 0x10de, 'device_id': 0x2820,
        'subsystem_vendor_id': 0x1558, 'subsystem_device_id': 0x0157,
        'pci_revision_id': 0xa1}.items())

def load_query():
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    getdir = kernel.GetSystemDirectoryW
    getdir.argtypes, getdir.restype = [ctypes.POINTER(ctypes.c_wchar), U32], U32
    buffer = ctypes.create_unicode_buffer(32768)
    size = getdir(buffer, len(buffer))
    if not size or size >= len(buffer):
        raise OSError('GetSystemDirectoryW failed')
    dll = ctypes.WinDLL(str(Path(buffer.value) / 'nvapi64.dll'), winmode=0x800)
    query = dll.nvapi_QueryInterface
    query.argtypes, query.restype = [U32], ctypes.c_void_p
    def function(key, args):
        address = query(IDS[key])
        if not address:
            raise RuntimeError('NVAPI interface unavailable: ' + key)
        return ctypes.WINFUNCTYPE(ctypes.c_int, *args)(address)
    return function

def probe():
    result = {'windows_unlock_supported': False, 'hardware_unlock_tested': False,
              'gpus': [], 'errors': []}
    if sys.platform != 'win32' or ctypes.sizeof(ctypes.c_void_p) != 8:
        result['errors'].append({'stage': 'platform', 'message': 'Requires 64-bit Windows'})
        return result
    initialized = False
    try:
        function = load_query()
        initialize, unload = function('initialize', []), function('unload', [])
        status = initialize()
        if status:
            result['errors'].append({'stage': 'initialize', 'status': status})
            return result
        initialized = True
        handle = ctypes.c_void_p
        enum = function('enum', [ctypes.POINTER(handle), ctypes.POINTER(U32)])
        handles, count = (handle * MAX_GPUS)(), U32()
        status = enum(handles, ctypes.byref(count))
        if status:
            result['errors'].append({'stage': 'enum', 'status': status})
            return result
        if count.value > MAX_GPUS:
            result['errors'].append({'stage': 'enum', 'message': 'GPU count exceeds buffer'})
            return result
        if count.value == 0:
            result['errors'].append({'stage': 'enum', 'message': 'No NVIDIA physical GPUs returned'})
            return result
        funcs = {'name': function('name', [handle, ctypes.c_void_p]),
                 'vbios': function('vbios', [handle, ctypes.c_void_p]),
                 'bus': function('bus', [handle, ctypes.POINTER(U32)]),
                 'pci': function('pci', [handle] + [ctypes.POINTER(U32)] * 4),
                 'arch': function('arch', [handle, ctypes.POINTER(ArchInfo)])}
        for i in range(count.value):
            gpu = {'index': i, 'profile_match': False, 'errors': []}
            result['gpus'].append(gpu)
            def record(stage, status):
                if status:
                    gpu['errors'].append({'stage': stage, 'status': status})
                return status == 0
            for field in ('name', 'vbios'):
                value = ctypes.create_string_buffer(64)
                if record(field, funcs[field](handles[i], value)):
                    gpu[field] = value.value.decode('utf-8', errors='replace')
            bus = U32()
            if record('bus', funcs['bus'](handles[i], ctypes.byref(bus))):
                gpu['bus_id'] = bus.value
            values = [U32() for _ in range(4)]
            if record('pci', funcs['pci'](handles[i], *(ctypes.byref(x) for x in values))):
                gpu['pci'] = decode_pci(*(x.value for x in values))
                gpu['profile_match'] = profile_match(gpu['pci'])
            arch = ArchInfo(ctypes.sizeof(ArchInfo) | (2 << 16), 0, 0, 0)
            if record('arch', funcs['arch'](handles[i], ctypes.byref(arch))):
                gpu['architecture'] = {'architecture': arch.architecture,
                    'implementation': arch.implementation, 'revision': arch.revision}
                gpu['expected_ada_implementation_match'] = (arch.architecture == 0x190 and arch.implementation == 6)
    except (OSError, RuntimeError, AttributeError) as exc:
        result['errors'].append({'stage': 'nvapi', 'message': str(exc)})
    finally:
        if initialized:
            status = unload()
            if status:
                result['errors'].append({'stage': 'unload', 'status': status})
    return result

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', help='Create a new JSON file; refuse overwrite')
    args = parser.parse_args(argv)
    stream = None
    try:
        if args.output:
            stream = open(args.output, 'x', encoding='utf-8')
        result = probe()
        text = json.dumps(result, indent=2) + '\n'
        if stream:
            stream.write(text)
        else:
            sys.stdout.write(text)
        return 1 if result['errors'] or any(g['errors'] for g in result['gpus']) else 0
    finally:
        if stream:
            stream.close()

if __name__ == '__main__':
    sys.exit(main())

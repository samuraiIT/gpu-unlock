# Provenance

The diagnostic source and host mocks are adapted from `windows/ad104-msi/diagnostic` in https://github.com/JustAResearcher/gpu-unlock-ada at commit d28c485418c3d9d034cd4bac19200bc33dd3453b, MIT license, retained in LICENSE.txt. `sample.c` and `sample.h` are not included; MMIO and physical PROM access were removed. The target is limited to PCI 10de:2820 subsystem 1558:0157 revision a1.

The EDK II header snapshot is copied unmodified from the same commit's `windows/ad104-msi/vendor/edk2`. `vendor/edk2/headers.json` records hashes, and `vendor/edk2/License.txt` retains licensing. The original source states TianoCore commit c1415771ac592ad8509351c46cd3cda4f38d7d52, via impacifist/Windows-GPU-UNLOCK commit 9352abd27480203ea146f766e7c96957912d148a. No EDK II library binary is linked.

This build has only been compiled and exercised under host mocks. It has not been run in firmware or on GPU hardware.

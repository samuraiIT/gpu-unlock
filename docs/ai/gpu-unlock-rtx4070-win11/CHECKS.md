# Проверки v0.2.0-20261029

| Проверка | Результат | Что подтверждено |
|---|---|---|
| NVAPI на реальной Windows | PASS | 2820, subsystem1558:0157, a1, arch0x190/impl6 |
| Windows probe unit tests | PASS, 5 тестов в Windows и WSL | ID/revision, no-overwrite, API lifecycle/error paths |
| C admission test | PASS | Exact-target parser, opt-in/all отказы, board/revision, no-resume predicate; остальные 65535 ID сохраняют lookup при всех 4 сочетаниях flags |
| Полный Linux module build | PASS | Ubuntu headers6.8.0-146, GCC13.3, KCFLAGS=-Werror; модуль не загружался |
| UEFI MSVC host mocks | PASS | 630 проверок приложения + 179 PE/ownership проверок на имитациях |
| UEFI PE/header validation | PASS | 43 pinned headers, x64 EFI, entry/sections/relocations, отсутствие import/TLS/CLR; mock JSON |
| Негативные build-validator tests | PASS, 2 теста с python -O | Изменённые/пропавшие/лишние headers, повреждённый PE и import/TLS/CLR отклоняются |
| Две последовательные UEFI-сборки | PASS | Побайтово одинаковы в этой среде MSVC; /Brepro |
| Аппаратная загрузка UEFI | NOT RUN | Пока требуется присутствие владельца и USB |
| Разблокировка на Linux или Windows | NOT RUN | Нет доказанного прироста, нет Windows unlock backend |
| Cold A/B/A, workload, sleep/resume | NOT RUN | Производительность и аппаратный откат не квалифицированы |
| Состояние Windows после разработки | PASS в доступном объёме | SHA-256 nvapi64.dll/nvcuda.dll/nvml.dll/nvidia-smi.exe прежние; GPU OK/code0, driver/VBIOS прежние, SecureBoot registry=1 |

SHA-256 диагностической EFI:
`c364a7f64d9ded2125c6da948abf90b831df90b72d759946325a6ad780ebd38b`.
Артефакт `windows/rtx4070-laptop-probe/build/RTX4070-PROBE.EFI` остаётся локальным,
рядом `manifest.json`. Это probe, не unlocker.

Сборка UEFI без установки:

```powershell
./windows/rtx4070-laptop-probe/Build.ps1
python -m unittest discover -s windows/rtx4070-laptop-probe/tests -p 'test_*.py' -v
```

Первоначальная host-компиляция C-теста выявила upstream warnings о частично
инициализированных структурах и неиспользуемой GA100-константе. Host test исключает
только эти два класса; остальные warnings fatal. Kernel module build использует
штатный Kbuild с -Werror. BTF пропущен из-за отсутствия vmlinux; это не ошибка сборки.

Независимое ревью обнаружило два исправленных дефекта: пропущенная ревизия PCI в
Windows predicate и отсутствие сверки фактических EDK2 headers с manifest. Проверки
PE используют явные исключения, поэтому python -O не отключает проверки.

Ограничения: host mocks не исполняют реальную GPU firmware; строковая проверка
опасных вызовов не является формальным доказательством; UEFI protocol pointers
предполагаются корректными. USB file check/create не атомарен и рассчитан на
контролируемую флешку без параллельного писателя. Raw capture содержит потенциальные
идентификаторы, ROM и код firmware-драйверов: хранить локально и не публиковать.

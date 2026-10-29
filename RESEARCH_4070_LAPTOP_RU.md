# RTX 4070 Laptop 10DE:2820 — исследовательская ветка

**Версия работы: v0.2.0-20261029. Рабочая разблокировка Windows пока не реализована.**
Этот форк содержит экспериментальный путь Linux и средства диагностики Windows.
Он не является установщиком ускорения для Windows и не подтверждает прирост скорости.

## Что реализовано

- Для PCI `10de:2820`, subsystem `1558:0157`, revision `a1` добавлен отдельный
  экспериментальный рецепт AD106. Обычный список поддерживаемых GPU его не включает.
- Требуются одновременно `rtx4070_laptop_experimental=1` и точный PCI-адрес в `targets`.
  `targets=all`, другой subsystem и другая ревизия эту карту не допускают.
- Повторная разблокировка этого экспериментального устройства после сна запрещена
  и в вызывающем коде, и перед началом транзакции. Другие карты сохраняют поведение upstream.
- `tools/windows_probe.py` получает идентификаторы, архитектуру и VBIOS через
  официальный NVAPI. Он не меняет настройки GPU, драйвер, EFI, BCD или реестр.
- Собрано `windows/rtx4070-laptop-probe/build/RTX4070-PROBE.EFI`: диагностика PCI/UEFI
  и cached ROM без GPU MMIO, физического PROM, reset или отключения графики.
  Программа ещё не запускалась в UEFI. Capture не является разрешением на запись в GPU.

На целевой машине официальный NVAPI действительно вернул architecture `0x190`,
implementation `6`, revision `0xa1`. Это обосновывает идентификацию AD106, но не
совместимость мобильного FWSEC, DMA, FLR или сохранение эффекта после запуска драйвера.
Рецепт использует имеющуюся транзакцию AD10x upstream; firmware, offsets и payload
не подбирались по догадке и не изменялись.

## Проверки без разблокировки

Из корня репозитория, в 64-битном Python Windows:

```powershell
python tools/windows_probe.py
python -m unittest discover -s tests -p 'test_windows_probe.py' -v
```

`--output <новый-файл.json>` сохраняет результат и отказывается перезаписывать файл.
Поля `windows_unlock_supported` и `hardware_unlock_tested` остаются `false`,
даже если `profile_match=true`.

Тест выбора рецептов на Linux/WSL с обычным C-компилятором:

```sh
sh tests/mobile-admission.sh
```

Сборка модуля без установки, для заранее подготовленных kernel headers:

```sh
make -C kernel/gpu_unlock KDIR=/path/to/kernel-headers KCFLAGS=-Werror
```

WSL использован только как среда сборки. Это не способ запустить pre-driver
разблокировку физического GPU Windows. В этой работе модуль не загружался,
загрузочные параметры не добавлялись и firmware не исполнялась.

## Почему Windows ещё не готов

Оригинальный проект — Linux-модуль. Windows-порт другой настольной платы нельзя
перенести заменой PCI ID: он закрепляет firmware, ROM, графические UEFI-драйверы,
владение протоколами, DMA, восстановление дисплея и переход к Windows Boot Manager.
Для данной платы эти предзагрузочные данные ещё не получены. В работающей Windows
NVAPI не предоставляет снимок UEFI Boot Services перед передачей управления ОС.

Следующий аппаратный этап требует проверенного способа возврата к штатной загрузке,
отдельного USB и участия владельца в выборе загрузочного устройства. Secure Boot
по доступному registry readback включён; прямое чтение UEFI и BitLocker в текущем
неадминистративном процессе недоступно. Recovery keys не читались и не публиковались.
Загрузочная диагностика и изменение Secure Boot в этой работе не выполнялись.

После получения приватного capture нужны отдельный Windows-профиль и его review,
затем cold stock → experiment → stock, проверка восстановления драйвера, корректности
результатов и повторяемых FP16/BF16/TF32 замеров. Лог `unlocked` и успешная сборка
не заменяют эти проверки. Известен [отчёт по другой RTX 4070 Laptop, 2860](https://github.com/JustAResearcher/gpu-unlock-ada/issues/87),
где после инициализации драйвера измеренная скорость осталась штатной.

## Версии, откат и доказательства

Исходная база: `Zagitta/gpu-unlock` commit
`7eb51bccae0a0b7e599e084d971170e9a1e82d0c`.
Ветка: `research/rtx4070-laptop-2820-windows`.
Существующий `main` форка не изменяется.

Документы проекта: [контекст](docs/ai/gpu-unlock-rtx4070-win11/PROJECT_CONTEXT.md),
[проверки](docs/ai/gpu-unlock-rtx4070-win11/CHECKS.md),
[откат](docs/ai/gpu-unlock-rtx4070-win11/ROLLBACK.md).
Сырые аппаратные данные, backup и локальные пути не входят в публикуемый код.

Первичные источники: [Linux upstream](https://github.com/Zagitta/gpu-unlock),
[Ada fork](https://github.com/JustAResearcher/gpu-unlock-ada),
[строго привязанный Windows-порт AD104](https://github.com/JustAResearcher/gpu-unlock-ada/tree/d28c485418c3d9d034cd4bac19200bc33dd3453b/windows/ad104-msi),
[NVAPI](https://github.com/NVIDIA/nvapi).

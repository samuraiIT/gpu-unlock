# Инструменты

Использованы локальный PowerShell, Git, Python stdlib, WSL/GCC и kernel headers
из официального Ubuntu package index, GitHub API и публичные первоисточники.
GitHub credential использован через существующий credential helper внутри процесса;
значение токена не выводилось, не сохранялось в документации и не добавлялось в Git.

Отдельного MCP-коннектора GitHub/UEFI в сессии нет. App/Page context не содержит
открытой страницы. Предзагрузочный аппаратный доступ удалённым tool не предоставлен.

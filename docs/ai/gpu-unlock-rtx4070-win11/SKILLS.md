# Роли и skills

- Главный инженер: архитектура Linux/UEFI, Windows-интеграция, границы аппаратных испытаний.
- GPT-6 Luna Medium: ограниченная сверка публичных матриц совместимости.
- GPT-6.1 Terra Medium: анализ источников, реализация Windows diagnostics и тестов.
- Независимое security/code review: GPT-6 Astra Medium. GPT-6.1 Sol High был выбран
  первым, но runtime вернул capacity error; глобальная модель/авторизация не менялись.

Применены `find-skills` (поиск) и
[`systematic-debugging`](https://github.com/obra/superpowers/blob/main/skills/systematic-debugging/SKILL.md)
(проверка причин и гипотез перед аппаратной модификацией). Поиск Windows GPU skills
не выявил подходящего специализированного установщика для этой платы. Популярность
skill не принималась за доказательство аппаратной совместимости.

Правило выбора моделей прочитано в актуальном MODEL_GUIDE, на который ссылается
предоставленный владельцем combo-refresh README от 27.10.2026. Native Codex оставлен
в своём runtime; OmniRoute config/routes не менялись. Страница provider доступна,
но её статический HTML не доказывает live model catalog. Успешные worker tasks
подтверждают выполнение соответствующих задач, а не сравнительную экономию токенов.

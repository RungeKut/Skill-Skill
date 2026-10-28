---
id: 40-03
title: GitHub без gh — REST API по токену из git credential fill; gh auth login из агентской оболочки висит вечно; JSON с кириллицей — только файлом
tags: [github, gh, rest api, токен, прокси, кодировка]
applies_to: Windows 10, Git for Windows (Git Bash, curl), GitHub CLI 2.x
status: проверено
verified: 2026-09-21 — gh auth login из оболочки агента повис без вывода (SolidWorks-Skill); 2026-10-08 — репозиторий создан через REST API по токену, JSON с кириллицей из командной строки дал 400, из файла прошёл (Pcad-Skill); форк и PR через REST — не проверено
source: перенесено из SolidWorks-Skill и Pcad-Skill (там эксперимент)
---

# GitHub без gh

## gh auth login из агента не запускать

`gh auth login` печатает одноразовый код и ждёт Enter, проверяя наличие
терминала. У оболочки агента stdin пустой: команда висит без вывода
(`printf '\n' | gh auth login` — тоже). Проверить вход без зависания:

```bash
gh auth status
```

«not logged in» — попросить человека один раз выполнить в своём терминале
`gh auth login --hostname github.com --git-protocol https --web`. Повисший
процесс снять: `taskkill //F //IM gh.exe`.

Свежеустановленный `gh` (winget) не виден в уже открытых оболочках: PATH
перечитывается только новыми процессами — искать `gh.exe` в
`%LOCALAPPDATA%\Microsoft\WinGet\Packages\GitHub.cli_*\bin`.

## REST API по токену git

Хватает git с сохранённым доступом к github.com (Диспетчер учётных данных
Windows):

```bash
TOKEN=$(printf 'protocol=https\nhost=github.com\n\n' | git credential fill | sed -n 's/^password=//p')
curl -s -H "Authorization: token $TOKEN" https://api.github.com/user/repos \
     --data-binary @payload.json        # тело — из файла
```

* **JSON с кириллицей — только файлом** (`--data-binary @file`, UTF-8): из
  командной строки Git Bash curl получает испорченные байты —
  `400 Problems parsing JSON`.
* Корпоративный прокси с подменой сертификата в `http.<url>.proxy` даёт
  `SSL certificate problem` / `511`; есть прямой доступ — прокси для
  github.com убрать (это глобальная настройка — по согласию человека).
* Новый репозиторий — закрытым (`"private": true`); открывает владелец.

| Действие | Запрос |
|---|---|
| форк | `POST /repos/{owner}/{repo}/forks` |
| PR | `POST /repos/{owner}/{repo}/pulls`, `head` = `<логин>:<ветка>` |
| открытые PR | `GET /repos/{owner}/{repo}/pulls?state=open` |
| вернуть PR | `POST /repos/{owner}/{repo}/pulls/{N}/reviews`, `"event":"REQUEST_CHANGES"` |

Сливать PR через API или кнопкой не нужно: владелец сливает локально
`git merge --no-ff` (40-02, 30-03); `403` на `PUT …/pulls/{N}/merge` —
вы не владелец, PR оставить ему. Форк, PR и отзыв через REST — по
документации, не проверено.

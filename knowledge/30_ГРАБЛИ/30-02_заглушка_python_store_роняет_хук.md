---
id: 30-02
title: «python» в PATH может быть заглушкой Microsoft Store (код 49) — хук, взявший её, не проверяет коммит; общий хук ищет Python, который реально запускается
tags: [хук, commit-msg, python, windows, git bash, PATH]
applies_to: Windows 10, Git for Windows 2.31, Python 3.13 (установка для пользователя)
status: проверено
verified: 2026-10-28 — в оболочке без каталога Python в PATH хук skill-skill нашёл только заглушки и отклонил коммит с подсказкой; с каталогом Python в PATH — проверил сообщение
source: эксперимент
---

# Заглушка Python из Microsoft Store

## Что происходит

В `%LOCALAPPDATA%\Microsoft\WindowsApps` лежат `python.exe` и `python3.exe`
— заглушки, открывающие Microsoft Store. `command -v python` их находит, а
запуск возвращает код 49 и сообщение «Python was not found». Старый хук
наборов брал первый найденный `python` и делал `exec`: коммит отклонялся с
невнятным текстом, а когда Python не находился совсем — хук выходил с 0 и
сообщение молча не проверялось.

## Почему

Установщик Python «для пользователя» не всегда добавляет себя в PATH, а
заглушки в PATH есть всегда. Git запускает хук с PATH той оболочки, из
которой вызван.

## Как правильно

Хук `skill-skill/hooks/commit-msg` перебирает `python3`, `python`, `py` и
берёт первый, у которого `"$py" -c "import sys"` проходит. Не нашёл —
**отклоняет** коммит с подсказкой добавить настоящий Python в PATH.
Вызывающему: перед `git commit` в PowerShell —

```powershell
$env:Path = "$env:LOCALAPPDATA\Programs\Python\Python313;" + $env:Path
```

(каталог — где стоит Python на этой машине).

## Как неправильно

* `exit 0`, когда Python не найден, — проверка тихо выключается.
* Проверять только `command -v python`: заглушка его проходит.

## Чем подтверждено

2026-10-28: хук запущен с PATH без каталога Python — отказ с подсказкой;
с каталогом — сообщение с трейлером соавтора отклонено, чистое принято.

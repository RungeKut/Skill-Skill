---
id: 30-05
title: PowerShell 5.1 читает .ps1 без BOM как ANSI — кириллица ломает разбор; .ps1 только UTF-8 с BOM, в .bat — только латиница
tags: [powershell, кодировка, bom, bat]
applies_to: Windows PowerShell 5.1, Windows 10
status: проверено
verified: 2026-10-07 — в Pcad-Skill скрипт без BOM упал с ParserError «MissingEndCurlyBrace», с BOM отработал целиком
source: перенесено из Pcad-Skill (там эксперимент); дополнено из Context-Skill
---

# .ps1 с кириллицей — только с BOM

## Что происходит

PowerShell 5.1 читает `.ps1` **без BOM** в кодировке системы (cp1251).
UTF-8 с русскими строками превращается в мусор, разбор падает с невнятным
`MissingEndCurlyBrace` / «неожиданная лексема» — причина в кодировке, а не
в скобках. Вывод `Get-Content` без `-Encoding` у таких файлов — тоже мусор.

Рядом (Context-Skill, не проверено): `Get-… -ErrorAction SilentlyContinue`
на объекте без прав возвращает пустое — «нет доступа» принимается за «нет».

## Как правильно

* `.ps1` сохранять в UTF-8 **с** BOM; редактор пишет без BOM — дописать
  `EF BB BF`:

  ```python
  data = open(path, "rb").read()
  open(path, "wb").write(b"\xef\xbb\xbf" + data)
  ```

* В `.bat` — только латиница: cmd читает в текущей кодовой странице;
  сообщения выводит вызываемый скрипт.
* Существование проверять `Test-Path` или `-ErrorAction Stop` в
  `try/catch`.

## Как неправильно

«Чинить скобки» вместо кодировки; кириллица в `.bat`; вывод «нет» из
пустого результата при SilentlyContinue.

## Чем подтверждено

2026-10-07, Pcad-Skill: скрипт без BOM — ParserError; с BOM — отработал.

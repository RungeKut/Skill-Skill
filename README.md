# Skill-Skill

Мета-скилл: правила ведения скиллов-репозиториев `RungeKut/*-Skill`, общие
проверки, общий хук `commit-msg` и шаблон нового скилла. Обновить правила
и проверки во всех скиллах разом — `git pull` здесь.

```
skill-skill/
├── SKILL.md            точка входа для ИИ
├── knowledge/          00_ПРАВИЛА (закон базы для всех наборов), 30_ГРАБЛИ, 40_СРЕДА
├── hooks/commit-msg    общий хук: стоп-слова и трейлеры соавторов в сообщении
├── tools/
│   ├── check_docs.py   проверка одного скилла (--root, --project)
│   ├── check_msg.py    проверка текста коммита (её вызывает хук)
│   ├── check_all.py    проверка всех соседних скиллов, сводка
│   ├── new_skill.py    новый скилл из шаблона
│   └── stoplist.txt    общий стоп-лист машины — локальный, не под git
└── templates/skill/    шаблон набора; tools/check_docs.py в нём — обёртка
```

## Установка

```bash
cd "<папка скиллов агента>"
git clone https://github.com/RungeKut/Skill-Skill.git skill-skill
git -C skill-skill config core.hooksPath hooks
```

Дальше — автор клона, стоп-лист и наборы рядом: `knowledge/40_СРЕДА/40-01`.
В каждом наборе `git config core.hooksPath ../skill-skill/hooks`.

## Лицензия

MIT.

# -*- coding: utf-8 -*-
"""Новый скилл из templates/skill рядом с skill-skill.

    python tools/new_skill.py <name> <Имя>-Skill [--dest <папка скиллов>]

name — имя папки и поле name в SKILL.md (строчные латинские, цифры, дефис).
Создаёт папку, git init -b main, хук, автора (как у клона skill-skill),
remote origin и пустой локальный стоп-лист; коммит не делает.
"""
import datetime
import io
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_docs import BRANCH, HOOKS_FOR_OTHERS, SKILL_SKILL, git

TEMPLATE = os.path.join(SKILL_SKILL, "templates", "skill")
TEXT = (".md", ".py", ".txt", ".gitignore", ".gitattributes")


def fill(path, values):
    text = io.open(path, encoding="utf-8").read()
    for k, v in values.items():
        text = text.replace("{{%s}}" % k, v)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main(argv):
    dest = os.path.dirname(SKILL_SKILL)
    if "--dest" in argv:
        i = argv.index("--dest")
        dest, argv = argv[i + 1], argv[:i] + argv[i + 2:]
    if len(argv) != 2 or not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", argv[0]):
        print(__doc__)
        return 2
    name, title = argv
    if not title.endswith("-Skill"):
        title += "-Skill"
    target = os.path.join(dest, name)
    if os.path.exists(target):
        print("%s уже есть" % target)
        return 1
    shutil.copytree(TEMPLATE, target)
    values = {"name": name, "title": title,
              "date": datetime.date.today().isoformat()}
    for dp, _dn, fn in os.walk(target):
        for f in fn:
            if f.endswith(TEXT):
                fill(os.path.join(dp, f), values)
    io.open(os.path.join(target, "tools", "stoplist.txt"), "w").close()

    subprocess.check_call(["git", "init", "-q", "-b", BRANCH, target])
    subprocess.check_call(["git", "-C", target, "config", "core.hooksPath",
                           HOOKS_FOR_OTHERS])
    subprocess.check_call(["git", "-C", target, "remote", "add", "origin",
                           "https://github.com/RungeKut/%s.git" % title])
    author = [git(SKILL_SKILL, "config", "--local", "--get", k)
              for k in ("user.name", "user.email")]
    if all(author):
        for k, v in zip(("user.name", "user.email"), author):
            subprocess.check_call(["git", "-C", target, "config", k, v])
    print("Создан %s (%s)." % (target, title))
    if not all(author):
        print("Автор не задан: git config user.name/user.email в клоне.")
    print("Дальше: SKILL.md (description, быстрый старт, правила), "
          "knowledge/40_СРЕДА/40-01, python tools/check_docs.py, коммит.")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))

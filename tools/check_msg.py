# -*- coding: utf-8 -*-
"""Проверка текста коммита: стоп-слова и трейлеры соавторов (40-02).

Файлы набора сверяет check_docs.py, а сообщение коммита — только этот
скрипт; его вызывает общий хук hooks/commit-msg. Вручную:

    python tools/check_msg.py [--root <репозиторий>] <файл с текстом коммита>
"""
import io
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_docs import ATTRIBUTION, load_local, project_words, stop_words


def toplevel():
    try:
        out = subprocess.check_output(["git", "rev-parse", "--show-toplevel"],
                                      stderr=subprocess.DEVNULL)
        return out.decode("utf-8", "replace").strip()
    except Exception:
        return os.getcwd()


def main(argv):
    root = None
    if len(argv) >= 2 and argv[0] == "--root":
        root, argv = argv[1], argv[2:]
    if len(argv) != 1 or not os.path.exists(argv[0]):
        print("check_msg.py: нужен путь к файлу с текстом коммита")
        return 2
    root = os.path.abspath(root or toplevel())
    lines = [l for l in io.open(argv[0], encoding="utf-8", errors="replace")
             .read().splitlines() if not l.lstrip().startswith("#")]
    text = "\n".join(lines)
    low = text.lower()

    words = stop_words(root) | project_words(root, None, load_local(root))
    hits = ["стоп-слово %r" % w for w in sorted(words) if w.lower() in low]
    hits += [what for rx, what in ATTRIBUTION if rx.search(text)]
    if not hits:
        return 0
    print("")
    print("  КОММИТ ОТКЛОНЁН:")
    for h in hits:
        print("    - " + h)
    print("")
    print("  Репозиторий публичный: в сообщении нет рабочих проектов и нет")
    print("  подписей (строки «…-by:», «Generated with», 🤖, noreply ИИ);")
    print("  автор — тот, кто задан для клона. Правило: skill-skill,")
    print("  knowledge/40_СРЕДА/40-02. Перепишите сообщение и повторите.")
    print("")
    return 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))

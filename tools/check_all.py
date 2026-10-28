# -*- coding: utf-8 -*-
"""check_docs по всем скиллам папки скиллов (соседям skill-skill); сводка.

    python tools/check_all.py [-v]

-v печатает отчёт каждого скилла целиком. Скиллом считается папка с
SKILL.md, с .git или со старой папкой skill (непереведённый набор).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_docs import SKILL_SKILL, collect, report


def skills():
    parent = os.path.dirname(SKILL_SKILL)
    for name in sorted(os.listdir(parent)):
        d = os.path.join(parent, name)
        if any(os.path.exists(os.path.join(d, m))
               for m in ("SKILL.md", os.path.join("skill", "SKILL.md"),
                         ".git")):
            yield d


def main(argv):
    verbose = "-v" in argv
    rows, bad = [], 0
    for d in skills():
        try:
            problems, history, info = collect(d)
        except Exception as e:
            problems, history, info = ["проверка упала: %r" % e], [], []
        bad += bool(problems or history)
        rows.append((os.path.basename(d), len(problems), len(history)))
        if verbose:
            report(d, problems, history, info)
            print("")
    width = max(len(r[0]) for r in rows) if rows else 0
    print("%-*s  расхождений  история" % (width, "скилл"))
    for name, p, h in rows:
        print("%-*s  %11d  %7d" % (width, name, p, h))
    print("\nИстория: старые коммиты исправит только перепись истории по "
          "команде владельца.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))

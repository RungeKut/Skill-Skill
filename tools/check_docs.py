# -*- coding: utf-8 -*-
"""Общая проверка скилла-репозитория; что и зачем — knowledge/00_ПРАВИЛА.md.

    python tools/check_docs.py [--root <скилл>] [--project <папка проекта>]

Без --root проверяется текущая папка. Особое для набора — в
<скилл>/tools/kit_local.py, всё необязательно: GENERIC (слова, не считающиеся
приметой проекта), TEXT_EXT, PROJECT_EXT (расширения файлов проекта, чьи имена
становятся стоп-словами), project_words(project_dir) -> set,
extra_checks(root) -> list[str].
"""
import importlib.util
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_SKILL = os.path.dirname(HERE)
WRAPPER = os.path.join(SKILL_SKILL, "templates", "skill", "tools",
                       "check_docs.py")
HOOKS_FOR_OTHERS = "../skill-skill/hooks"
HOOKS_FOR_SELF = "hooks"
BRANCH = "main"

REQUIRED = ("id", "title", "status")
VALID_STATUS = ("проверено", "не проверено", "устарело", "действует")
SKILL_MAX_BYTES = 4096
DESCRIPTION_MAX = 1024
MAX_LINES = 200
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
NAME_MAX = 64
REPO_FILES = (
    (".gitattributes", "переводы строк будут зависеть от core.autocrlf "
                       "машины — взять из шаблона skill-skill"),
    ("LICENSE", "публичный репозиторий без лицензии — пользоваться им "
                "нельзя; взять MIT из шаблона skill-skill"),
)
INDEX_HEADER = "| id | Утверждение | status | Файл |"

TEXT_EXT = (".md", ".py", ".ps1", ".psm1", ".bat", ".cmd", ".sh", ".txt",
            ".cfg", ".ini", ".toml", ".json", ".yml", ".yaml", ".xml",
            ".c", ".h", ".s", ".ld", ".il", ".tcl")
TEXT_NAMES = ("Makefile", "commit-msg")
CODE_EXT = (".py", ".ps1", ".psm1", ".bat", ".cmd", ".sh")
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tif",
             ".tiff", ".ico")
SKIP_DIRS = (".git", "__pycache__", ".venv", "local", "node_modules")
STOPLIST_REL = "tools/stoplist.txt"
GENERIC = set("""board design project schematic test tests main build params
kit skill skills work temp data copy backup new old final model models
workspace system state states event events action actions region machine
part assembly docs index rules agents claude code src source release debug
плата платы плате схема схемы проект проекта модуль блок версия копия
управления питания контроля модель модели автомат автоматы деталь сборка
документы правила агенты состояние индекс""".split())

ATTRIBUTION = (
    (re.compile(r"строка соавторства\s*:", re.I), "трейлер строка соавторства"),
    (re.compile(r"generated with", re.I), "«Generated with»"),
    (re.compile(r"noreply@anthropic\.com", re.I), "адрес noreply ИИ"),
    (re.compile("\U0001F916"), "значок 🤖"),
)
LEGACY_CODE = (
    (re.compile(r"\.claude[/\\]|\.kimi-code", re.I),
     "путь конкретного агента — корень = папка SKILL.md (30-01)"),
    (re.compile(r"(environ|getenv|\$env:)[\w.\[\]\"'( ]{0,40}_HOME\b"
                r"|%\w+_HOME%|\$\{?\w+_HOME\b", re.I),
     "переменная *_HOME — соседей искать в <родитель корня>/<name> (30-01)"),
    (re.compile(r"\b[A-Za-z]:[/\\]([^\s\"'<>|*?]*[/\\])?skills[/\\]", re.I),
     "жёсткий путь к папке скиллов — корень = папка SKILL.md, сосед — "
     "<родитель корня>/<name> (30-01)"),
    (re.compile(r"\bmklink\b", re.I), "junction — клон и есть папка скилла"),
    (re.compile(r"skill[/\\]SKILL\.md"), "skill/SKILL.md — SKILL.md в корне"),
)
OLD_NAME = re.compile(r"\b[A-Za-z]+-Kit\b")
ORIGIN = re.compile(r"github\.com[/:][\w.-]+/[\w.]+-Skill(\.git)?$")


def read(path):
    return io.open(path, encoding="utf-8", errors="replace").read()


def git(root, *args):
    try:
        out = subprocess.check_output(["git", *args], cwd=root,
                                      stderr=subprocess.DEVNULL)
    except Exception:
        return None
    return out.decode("utf-8", "replace").strip()


def is_self(root):
    return os.path.normcase(os.path.realpath(root)) == \
        os.path.normcase(os.path.realpath(SKILL_SKILL))


def front_matter(text):
    """Плоская шапка YAML: {ключ: значение как написано}."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    out = {}
    for line in text[3:end].splitlines():
        m = re.match(r"^([a-zA-Z_]+):\s*(.*)$", line.strip())
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def unquote(v):
    return v[1:-1] if len(v) >= 2 and v[0] == v[-1] == '"' else v


def load_local(root):
    path = os.path.join(root, "tools", "kit_local.py")
    if not os.path.exists(path):
        return None
    name = "kit_local_" + re.sub(r"\W", "_", os.path.basename(root))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def local_attr(local, name, default):
    return getattr(local, name, default) if local else default


def stoplists(root):
    paths = [os.path.join(SKILL_SKILL, STOPLIST_REL),
             os.path.join(root, STOPLIST_REL)]
    out = []
    for p in paths:
        if os.path.exists(p) and os.path.normcase(os.path.realpath(p)) not in \
                [os.path.normcase(os.path.realpath(q)) for q in out]:
            out.append(p)
    return out


def stop_words(root):
    out = {}
    for p in stoplists(root):
        for line in io.open(p, encoding="utf-8-sig").read().splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                out.setdefault(line.lower(), line)
    return set(out.values())


def project_dirs(root, project_dir=None):
    dirs = [project_dir] if project_dir else []
    cfg = git(root, "config", "--get",
              "%s.project" % os.path.basename(root))
    if cfg:
        dirs.append(cfg)
    return [d for d in dirs if os.path.isdir(d)]


def project_words(root, project_dir=None, local=None):
    generic = GENERIC | {w.lower() for w in local_attr(local, "GENERIC", ())}
    exts = tuple(e.upper() for e in local_attr(local, "PROJECT_EXT", ()))
    out = set()
    for d in project_dirs(root, project_dir):
        names = [os.path.basename(os.path.abspath(d))]
        if exts:
            for dp, dn, fn in os.walk(d):
                dn[:] = [x for x in dn if not x.startswith(".")]
                names += [os.path.splitext(f)[0] for f in fn
                          if os.path.splitext(f)[1].upper() in exts]
        for name in names:
            out |= {t for t in re.split(r"[^0-9A-Za-zА-Яа-яЁё]+", name)
                    if len(t) >= 4 and t.lower() not in generic}
        extra = local_attr(local, "project_words", None)
        if extra:
            out |= set(extra(d))
    return out


def repo_files(root, local=None):
    """Файлы, которые может увидеть коммит: под git и не игнорируемые."""
    listed = git(root, "ls-files", "-co", "--exclude-standard", "-z")
    if listed is None:
        rels = []
        for dp, dn, fn in os.walk(root):
            dn[:] = [d for d in dn if d not in SKIP_DIRS]
            rels += [os.path.relpath(os.path.join(dp, f), root) for f in fn]
    else:
        rels = [r for r in listed.split("\0") if r]
    out = []
    for r in sorted(r.replace("\\", "/") for r in rels):
        if r == STOPLIST_REL or r.split("/")[0] in SKIP_DIRS:
            continue
        if os.path.exists(os.path.join(root, r)):
            out.append(r)
    return out


def is_text(rel, local=None):
    ext = TEXT_EXT + tuple(local_attr(local, "TEXT_EXT", ()))
    name = rel.rsplit("/", 1)[-1]
    return name.lower().endswith(tuple(e.lower() for e in ext)) \
        or name in TEXT_NAMES


def is_code(rel):
    return rel.lower().endswith(CODE_EXT) or rel.startswith("hooks/") \
        or rel == "SKILL.md"


def check_skill_md(root):
    out = []
    skill = os.path.join(root, "SKILL.md")
    for rel in ("skill", "tools/setup.ps1", "Install-skill.bat",
                "tools/Install-skill.bat"):
        if os.path.exists(os.path.join(root, rel)):
            out.append("%s остался от установщика — клон и есть папка "
                       "скилла, удалить" % rel)
    if not os.path.exists(skill):
        return out + ["нет SKILL.md в корне — агент не увидит скилл"]
    text = read(skill)
    size = len(text.encode("utf-8"))
    if size > SKILL_MAX_BYTES:
        out.append("SKILL.md %d байт, предел %d — подробности в базу"
                   % (size, SKILL_MAX_BYTES))
    fm = front_matter(text) or {}
    name = os.path.basename(os.path.abspath(root))
    if fm.get("name") != name:
        out.append("SKILL.md: name %r, а папка %r — клон кладётся в папку "
                   "<name>" % (fm.get("name"), name))
    if not (len(name) <= NAME_MAX and NAME_RE.match(name)):
        out.append("name %r: нужно 1–%d знаков, строчная латиница, цифры и "
                   "дефис между ними — иначе часть агентов (opencode) скилл "
                   "не загрузит" % (name, NAME_MAX))
    raw = fm.get("description", "")
    desc = unquote(raw)
    if not desc:
        out.append("SKILL.md: нет description")
    else:
        if raw == desc:
            out.append("SKILL.md: description без кавычек — с «: » часть "
                       "загрузчиков молча не видит скилл")
        if len(desc) > DESCRIPTION_MAX:
            out.append("SKILL.md: description %d знаков, предел %d (30-06)"
                       % (len(desc), DESCRIPTION_MAX))
    if not is_self(root) and "skill-skill" not in text:
        out.append("SKILL.md: нет строки «общие правила — соседний скилл "
                   "skill-skill»")
    out += ["нет %s: %s" % (rel, why) for rel, why in REPO_FILES
            if not os.path.exists(os.path.join(root, rel))]
    return out


def check_knowledge(root):
    out, ids = [], {}
    kn = os.path.join(root, "knowledge")
    index = os.path.join(kn, "INDEX.md")
    if not os.path.isdir(kn):
        return ["нет папки knowledge/"], ids
    files = []
    for dp, _dn, fn in os.walk(kn):
        files += [os.path.join(dp, f) for f in fn
                  if f.endswith(".md") and f != "INDEX.md"]
    files.sort()

    def rel(p):
        return os.path.relpath(p, kn).replace("\\", "/")

    for path in files:
        r, text = rel(path), read(path)
        fm = front_matter(text)
        if fm is None:
            out.append("%s: нет шапки YAML" % r)
            continue
        fm = {k: unquote(v) for k, v in fm.items()}
        out += ["%s: в шапке нет поля %s" % (r, f)
                for f in REQUIRED if f not in fm]
        status = fm.get("status", "")
        if status and status not in VALID_STATUS:
            out.append("%s: неизвестный status %r (допустимы: %s)"
                       % (r, status, ", ".join(VALID_STATUS)))
        if status == "проверено" and not fm.get("verified"):
            out.append("%s: «проверено» без verified — запись не имеет силы"
                       % r)
        if status == "проверено" and not fm.get("applies_to"):
            out.append("%s: «проверено» без applies_to" % r)
        if len(text.splitlines()) > MAX_LINES:
            out.append("%s: больше %d строк — одна тема на файл"
                       % (r, MAX_LINES))
        fid = fm.get("id", "")
        if fid:
            if fid in ids:
                out.append("%s: id %s уже занят файлом %s" % (r, fid, ids[fid]))
            else:
                ids[fid] = r
            base = os.path.basename(path)
            if not base.startswith(fid + "_") and base != "00_ПРАВИЛА.md":
                out.append("%s: id %s не совпадает с именем файла" % (r, fid))

    link_re = re.compile(r"\]\(([^)#\s]+\.md)(?:#[^)]*)?\)")
    if not os.path.exists(index):
        out.append("нет knowledge/INDEX.md")
    else:
        text = read(index)
        out += check_index_header(text)
        linked = {l.replace("\\", "/") for l in link_re.findall(text)}
        out += ["%s: файла нет в INDEX.md" % rel(p)
                for p in files if rel(p) not in linked]
        existing = {rel(p) for p in files}
        out += ["INDEX.md ссылается на несуществующий %s" % l
                for l in sorted(linked)
                if l not in existing and not l.startswith("..")
                and not l.startswith("http")]
        width = None
        for n, line in enumerate(text.splitlines(), 1):
            if not line.startswith("|"):
                width = None
                continue
            cells = line.count("|")
            if width is None:
                width = cells
            elif cells != width:
                out.append("INDEX.md, строка %d: %d ячеек вместо %d — таблица "
                           "испорчена" % (n, cells - 1, width - 1))
    for path in files:
        for link in link_re.findall(read(path)):
            if link.startswith("http"):
                continue
            target = os.path.normpath(os.path.join(os.path.dirname(path), link))
            if not os.path.exists(target):
                out.append("%s: битая ссылка -> %s" % (rel(path), link))
    return out, ids


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def check_index_header(text):
    """Первая таблица INDEX.md — id | утверждение | status | файл.

    Ссылка на файл может стоять в ячейке id вместо столбца «Файл», статус —
    называться «Статус»; лишние столбцы (когда читать) допустимы.
    """
    rows = [l for l in text.splitlines() if l.startswith("|")]
    if not rows:
        return ["INDEX.md: нет таблицы записей — нужна %s (00)" % INDEX_HEADER]
    head = [c.lower() for c in cells(rows[0])]
    first = cells(rows[2])[0] if len(rows) > 2 else ""
    ok = len(head) >= 3 and head[0] == "id" and head[1] == "утверждение" \
        and ({"status", "статус"} & set(head)) \
        and ("файл" in head or "](" in first)
    if ok:
        return []
    return ["INDEX.md: заголовок таблицы %r — нужен %s (00)"
            % (rows[0].strip(), INDEX_HEADER)]


def check_texts(root, files, words, local):
    out = []
    lowered = sorted({w.lower() for w in words})
    for r in files:
        if not is_text(r, local):
            continue
        text = read(os.path.join(root, r))
        low = text.lower()
        out += ["%s: стоп-слово %r — приметы рабочего проекта в набор не "
                "попадают (40-02)" % (r, w) for w in lowered if w in low]
        if r != "CHANGELOG.md":
            for m in sorted(set(OLD_NAME.findall(text))):
                out.append("%s: старое имя %s — теперь %s-Skill"
                           % (r, m, m[:-4]))
        if is_code(r) and os.path.abspath(os.path.join(root, r)) != \
                os.path.abspath(__file__):
            for rx, why in LEGACY_CODE:
                if rx.search(text):
                    out.append("%s: %s" % (r, why))
    return out


def check_local_files(root):
    out = []
    if not os.path.exists(os.path.join(SKILL_SKILL, STOPLIST_REL)):
        out.append("нет общего стоп-листа skill-skill/tools/stoplist.txt — "
                   "проверять не по чему; завести локально (40-01)")
    if git(root, "ls-files", "--", STOPLIST_REL):
        out.append("tools/stoplist.txt под git — при push приметы проектов "
                   "уйдут наружу: git rm --cached tools/stoplist.txt")
    if git(root, "ls-files", "--", "local"):
        out.append("каталог local/ под git — он только локальный")
    for r in (git(root, "ls-files", "-z") or "").split("\0"):
        if r.lower().endswith(IMAGE_EXT) and not r.startswith("examples/"):
            out.append("%s: изображение под git вне examples/ — снимки "
                       "рабочих окон не коммитятся (40-02)" % r)
    if not is_self(root):
        wrapper = os.path.join(root, "tools", "check_docs.py")
        same = os.path.exists(wrapper) and os.path.exists(WRAPPER) and \
            read(wrapper).replace("\r\n", "\n") == \
            read(WRAPPER).replace("\r\n", "\n")
        if not same:
            out.append("tools/check_docs.py не совпадает с обёрткой "
                       "skill-skill/templates/skill/tools/check_docs.py — "
                       "скопировать её")
        for rel in ("tools/check_msg.py", "tools/hooks"):
            if os.path.exists(os.path.join(root, rel)):
                out.append("%s: остаток своего хука — хук общий, "
                           "в skill-skill/hooks; удалить" % rel)
    return out


def check_git(root, words):
    out = []
    if git(root, "rev-parse", "--git-dir") is None:
        return ["не git-репозиторий"]
    want = HOOKS_FOR_SELF if is_self(root) else HOOKS_FOR_OTHERS
    got = (git(root, "config", "--get", "core.hooksPath") or "")
    if got.replace("\\", "/").rstrip("/") != want:
        out.append("core.hooksPath = %r, нужно %r — без хука текст коммита "
                   "никто не проверяет: git config core.hooksPath %s"
                   % (got, want, want))
    elif not os.path.exists(os.path.join(root, want, "commit-msg")):
        out.append("хук %s/commit-msg не найден — нужен соседний скилл "
                   "skill-skill (40-01)" % want)
    name = git(root, "config", "--local", "--get", "user.name")
    email = git(root, "config", "--local", "--get", "user.email")
    if not (name and email):
        out.append("для клона не задан автор — git возьмёт глобальные (на "
                   "рабочей машине рабочие) имя и адрес: git config "
                   "user.name/user.email без --global; не задан — не "
                   "коммитить, спросить человека")
    elif bad_identity(name, email, words):
        out.append("автор клона %s <%s>: адрес .local или стоп-слово — нужен "
                   "публичный" % (name, email))
    branch = git(root, "symbolic-ref", "--short", "HEAD")
    if branch != BRANCH:
        out.append("ветка %r, нужна %r: git branch -m %s %s"
                   % (branch, BRANCH, branch, BRANCH))
    origin = git(root, "remote", "get-url", "origin") or ""
    if not ORIGIN.search(origin):
        out.append("remote origin %r — нужно https://github.com/RungeKut/"
                   "<Имя>-Skill.git" % origin)
    return out


def bad_identity(name, email, words):
    low = ("%s %s" % (name, email)).lower()
    return email.lower().endswith(".local") or \
        any(w.lower() in low for w in words)


def check_history(root, words):
    log = git(root, "log", "--all",
              "--format=%h%x1f%an%x1f%ae%x1f%cn%x1f%ce%x1f%B%x1e")
    if not log:
        return []
    found = {}
    for rec in log.split("\x1e"):
        parts = rec.strip("\n").split("\x1f")
        if len(parts) < 6:
            continue
        h, an, ae, cn, ce, msg = parts
        for rx, what in ATTRIBUTION:
            if rx.search(msg):
                found.setdefault(what, []).append(h)
        if bad_identity(an, ae, words) or bad_identity(cn, ce, words):
            found.setdefault("автор/коммитер с адресом .local или "
                             "стоп-словом", []).append(h)
        low = msg.lower()
        if any(w.lower() in low for w in words):
            found.setdefault("стоп-слово в сообщении", []).append(h)
    out = ["%s — %d: %s" % (what, len(hs), ", ".join(hs))
           for what, hs in sorted(found.items())]
    return out + history_content(root, words)


def mask(word):
    """Слово в отчёте — первая буква и длина: отчёт читают и пересылают."""
    return "%s…(%d)" % (word[:1], len(word))


def added_text(root):
    """{(коммит, файл): имя файла и добавленные строки} по всей истории.

    Любое содержимое, когда-либо лежавшее в репозитории, добавлено каким-то
    коммитом, поэтому строк «+» из git log -p хватает. Изменения, внесённые
    только разрешением конфликта при слиянии, не видны.
    """
    log = git(root, "-c", "core.quotepath=off", "log", "--all", "-p",
              "--no-color", "--no-ext-diff", "--no-renames",
              "--format=%x1e%h")
    out = {}
    for rec in (log or "").split("\x1e"):
        lines = rec.split("\n")
        h, path, chunks, header = lines[0].strip(), None, [], True
        for line in lines[1:]:
            if line.startswith("diff --git "):
                if path:
                    out[(h, path)] = "\n".join(chunks).lower()
                path, chunks, header = None, [], True
            elif header and line.startswith("+++ "):
                target = line[4:]
                path = target[2:] if target.startswith("b/") else None
                chunks = [path or ""]
            elif line.startswith("@@"):
                header = False
            elif not header and line.startswith("+"):
                chunks.append(line[1:])
        if path:
            out[(h, path)] = "\n".join(chunks).lower()
    return out


def history_content(root, words, shown=8):
    hits = {}
    lowered = {w.lower() for w in words}
    for (h, path), text in added_text(root).items():
        for w in lowered:
            if w in text:
                hits.setdefault(w, []).append("%s %s" % (h, path))
    out = []
    for w in sorted(hits):
        places = sorted(hits[w])
        more = len(places) - shown
        out.append("стоп-слово %s в содержимом — %d: %s%s" % (
            mask(w), len(places), ", ".join(places[:shown]),
            ", …ещё %d" % more if more > 0 else ""))
    return out


def unpushed(root):
    branch = git(root, "symbolic-ref", "--short", "HEAD") or "?"
    n = git(root, "rev-list", "--count", "@{u}..HEAD")
    if n is None and git(root, "rev-parse", "--verify", "--quiet",
                         "refs/remotes/origin/%s" % branch):
        n = git(root, "rev-list", "--count", "origin/%s..HEAD" % branch)
    if n is None:
        return "ветка %s; удалённой ветки %s нет (репозиторий не создан или " \
               "не отправлен)" % (branch, branch)
    return "ветка %s; неотправленных коммитов: %s" % (branch, n)


def collect(root, project_dir=None):
    """(расхождения, история, сведения) для скилла в root."""
    root = os.path.abspath(root)
    local = load_local(root)
    words = stop_words(root)
    project = project_words(root, project_dir, local)
    files = repo_files(root, local)
    problems = check_skill_md(root)
    kn, ids = check_knowledge(root)
    problems += kn
    problems += check_texts(root, files, words | project, local)
    problems += check_local_files(root)
    problems += check_git(root, words)
    extra = local_attr(local, "extra_checks", None)
    if extra:
        problems += list(extra(root))
    history = check_history(root, words | project)
    info = ["стоп-слов: %d (%s)" % (len(words | project), ", ".join(
                os.path.relpath(p, os.path.dirname(SKILL_SKILL))
                for p in stoplists(root)) or "стоп-листов нет"),
            "текстовых файлов проверено: %d"
            % sum(1 for f in files if is_text(f, local)),
            unpushed(root),
            "занятые id: %s" % ", ".join(sorted(ids))]
    if project:
        info.insert(0, "приметы проекта: %s" % ", ".join(sorted(project)))
    return problems, history, info


HISTORY_NOTE = ("старые коммиты исправит только перепись истории — по "
                "команде владельца; до неё эти строки ожидаемы, новые "
                "коммиты должны быть чистыми")


def report(root, problems, history, info):
    print("Скилл: %s" % root)
    for line in info:
        print("  " + line)
    if problems:
        print("РАСХОЖДЕНИЯ (%d):" % len(problems))
        for p in problems:
            print("  - " + p)
    else:
        print("Расхождений нет.")
    if history:
        print("ИСТОРИЯ (%d) — %s:" % (len(history), HISTORY_NOTE))
        for p in history:
            print("  - " + p)


def parse_args(argv):
    opts = {"--root": os.getcwd(), "--project": None}
    i = 0
    while i < len(argv):
        if argv[i] in opts and i + 1 < len(argv):
            opts[argv[i]] = argv[i + 1]
            i += 2
        else:
            raise SystemExit("неизвестный аргумент %r; запуск: check_docs.py "
                             "[--root <скилл>] [--project <папка>]" % argv[i])
    return opts["--root"], opts["--project"]


def main(argv):
    root, project = parse_args(argv)
    root = os.path.abspath(root)
    problems, history, info = collect(root, project)
    report(root, problems, history, info)
    return 1 if problems or history else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))

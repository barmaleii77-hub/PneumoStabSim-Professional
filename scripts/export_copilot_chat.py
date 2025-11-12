#!/usr/bin/env python3

import argparse
import datetime as dt
import glob
import json
import os
import re
import sqlite3
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

ConversationBlock = tuple[str, dt.datetime | None, list[dict[str, Any]], float]

# ---------- утилиты ----------

def human_ts(ts: dt.datetime | None, fallback_epoch: float | None = None) -> str:
    if ts:
        try: return ts.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        except Exception: return ts.strftime("%Y-%m-%d %H:%M:%S")
    if fallback_epoch is not None:
        return dt.datetime.fromtimestamp(fallback_epoch).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    return ""

def parse_iso(ts: Any) -> dt.datetime | None:
    if isinstance(ts, (int, float)):
        # эвристика: миллисекунды?
        return dt.datetime.fromtimestamp(ts/1000.0) if ts > 10_000_000_000 else dt.datetime.fromtimestamp(float(ts))
    if isinstance(ts, str):
        try: return dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception: return None
    return None

def fence(text: str) -> str:
    return str(text).replace("```", "``\u200b`")

def sanitize_role(role: str) -> str:
    rl = (role or "").lower()
    if "user" in rl: return "User"
    if any(k in rl for k in ("assistant","copilot","ai","bot")): return "Copilot"
    return role.capitalize() or "Unknown"

def write_msgs(md, title, source_path, conv_ts, msgs, fallback_epoch=None):
    md.write(f"---\n\n")
    md.write(f"### {title}\n\n")
    if source_path: md.write(f"**Источник:** `{source_path}`  \n")
    if conv_ts or fallback_epoch: md.write(f"**Время:** {human_ts(conv_ts, fallback_epoch)}\n\n")
    if not msgs:
        md.write("_Сообщения не найдены._\n\n")
        return
    for m in msgs:
        role = sanitize_role(m.get("role",""))
        content = str(m.get("content","")).strip()
        ts = m.get("timestamp")
        when = f" _({human_ts(ts)})_" if isinstance(ts, dt.datetime) else ""
        md.write(f"**{role}:**{when}\n\n")
        if "\n" in content or len(content) > 120:
            md.write(f"```\n{fence(content)}\n```\n\n")
        else:
            md.write(content + "\n\n")

# ---------- парсеры ----------

def load_json_safe(p: Path) -> dict[str, Any] | None:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

def extract_from_vscode_chatSessions(root: Path) -> list[ConversationBlock]:
    """
    VS Code: %APPDATA%/Code/User/workspaceStorage/<id>/chatSessions/*.json
    """
    out = []
    for ws in (root / "User" / "workspaceStorage").glob("*"):
        chat_dir = ws / "chatSessions"
        if not chat_dir.exists(): continue
        for jf in chat_dir.glob("*.json"):
            data = load_json_safe(jf)
            if not data: continue
            title = data.get("title") or f"VS Code chat (workspace {ws.name})"
            msgs = []
            ts_all = []
            for it in data.get("messages", []):
                role = it.get("role") or it.get("speaker") or it.get("author") or "unknown"
                content = it.get("content") or it.get("text") or it.get("body") or ""
                t = parse_iso(it.get("createdAt") or it.get("timestamp") or it.get("at"))
                if isinstance(content, dict):
                    content = content.get("text") or content.get("value") or json.dumps(content, ensure_ascii=False)
                msgs.append({"role": role, "content": content, "timestamp": t})
                if t: ts_all.append(t)
            conv_ts = max(ts_all) if ts_all else None
            out.append((f"{jf}", conv_ts, msgs, jf.stat().st_mtime))
    return out

def extract_from_vscode_state_db(db_path: Path) -> list[ConversationBlock]:
    """
    VS Code: %APPDATA%/Code/User/workspaceStorage/<id>/state.vscdb -> keys:
      - 'interactive.sessions' (array)
      - 'memento/interactive-session' (object or array)
    Будем искать любые ключи, где встречаются 'interactive' или 'copilot'.
    """
    out = []
    try:
        con = sqlite3.connect(str(db_path))
        cur = con.cursor()
        # schema у state.vscdb может отличаться; в новых версиях таблица называется 'ItemTable'
        # c колонками 'key', 'value'. Попробуем обе схемы.
        tables = []
        try:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cur.fetchall()]
        except Exception:
            pass
        candidate_tables = [t for t in tables if t.lower() in ("itemtable","items","state")]
        if not candidate_tables:
            candidate_tables = tables  # fallback: попробуем всё

        for t in candidate_tables:
            try:
                cur.execute(f"SELECT key, value FROM {t}")
            except Exception:
                continue
            rows = cur.fetchall()
            for k, v in rows:
                key = str(k or "")
                if not any(s in key.lower() for s in ("interactive", "copilot", "session")):
                    continue
                try:
                    js = json.loads(v)
                except Exception:
                    continue
                # Нормализуем в список сообщений
                collected = []
                ts_all = []
                if isinstance(js, list):
                    iterable = js
                elif isinstance(js, dict):
                    # возможные поля: messages, items, entries
                    iterable = js.get("messages") or js.get("items") or js.get("entries") or []
                    if not isinstance(iterable, list):
                        iterable = []
                else:
                    iterable = []

                for m in iterable:
                    role = (m.get("role") or m.get("speaker") or m.get("author") or "unknown") if isinstance(m, dict) else "unknown"
                    content = (m.get("content") or m.get("text") or m.get("body") or "") if isinstance(m, dict) else str(m)
                    ts = None
                    if isinstance(m, dict):
                        ts = parse_iso(m.get("createdAt") or m.get("timestamp") or m.get("at"))
                    collected.append({"role": role, "content": content, "timestamp": ts})
                    if ts: ts_all.append(ts)
                conv_ts = max(ts_all) if ts_all else None
                if collected:
                    out.append((f"{db_path}::{key}", conv_ts, collected, db_path.stat().st_mtime))
        con.close()
    except Exception:
        pass
    return out

def extract_vscode_all() -> list[ConversationBlock]:
    out = []
    # корни VS Code (Windows/macOS/Linux)
    roots: list[Path] = []
    home = Path.home()
    appdata = os.environ.get("APPDATA")
    if appdata:
        roots += [Path(appdata)/"Code", Path(appdata)/"Code - Insiders", Path(appdata)/"VSCodium"]
    # macOS:
    roots += [
        home/"Library"/"Application Support"/"Code",
        home/"Library"/"Application Support"/"Code - Insiders",
        home/"Library"/"Application Support"/"VSCodium",
    ]
    # Linux:
    roots += [
        home/".config"/"Code",
        home/".config"/"Code - Insiders",
        home/".config"/"VSCodium",
    ]
    seen = set()
    for r in roots:
        if not r.exists(): continue
        key = str(r)
        if key in seen: continue
        seen.add(key)
        # chatSessions JSON
        out += extract_from_vscode_chatSessions(r)
        # state.vscdb (SQLite)
        ws_root = r / "User" / "workspaceStorage"
        for ws in ws_root.glob("*"):
            db = ws / "state.vscdb"
            if db.exists():
                out += extract_from_vscode_state_db(db)
    return out

def extract_visualstudio_logs() -> list[ConversationBlock]:
    """
    Visual Studio: логи Copilot Chat в %LOCALAPPDATA%\\Temp\\**\\*VSGitHubCopilot*.chat*.log
    """
    out = []
    lad = os.environ.get("LOCALAPPDATA")
    if not lad: return out
    patterns = [
        str(Path(lad)/"Temp"/"**"/"*VSGitHubCopilot*.chat*.log"),
        str(Path(lad)/"Temp"/"*VSGitHubCopilot*.chat*.log"),
    ]
    matched = []
    for pat in patterns:
        matched += glob.glob(pat, recursive=True)
    for fp in sorted(set(matched)):
        p = Path(fp)
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        # логи построчные, сделаем из них "сообщения" (простой парсер)
        msgs = []
        ts_guess = None
        for line in text.splitlines():
            if not line.strip(): continue
            # Попробуем выдернуть метку времени формата [YYYY-MM-DD HH:MM:SS]
            ts = None
            if line.startswith("[") and "]" in line[:30]:
                hdr = line[1:line.index("]")]
                try:
                    ts = dt.datetime.fromisoformat(hdr)
                except Exception:
                    ts = None
                content = line[line.index("]")+1:].strip()
            else:
                content = line.strip()
            msgs.append({"role": "Copilot", "content": content, "timestamp": ts})
            if ts and not ts_guess: ts_guess = ts
        out.append((fp, ts_guess, msgs, p.stat().st_mtime))
    return out

# ---------- фильтрация и основной экспорт ----------


def _compile_patterns(patterns: Iterable[str] | None, *, case_sensitive: bool) -> list[re.Pattern[str]]:
    compiled: list[re.Pattern[str]] = []
    if not patterns:
        return compiled

    flags = 0 if case_sensitive else re.IGNORECASE
    for pattern in patterns:
        if not pattern:
            continue
        try:
            compiled.append(re.compile(pattern, flags))
        except re.error as exc:  # pragma: no cover - validated in caller
            raise ValueError(f"Некорректное регулярное выражение: {pattern!r} ({exc})") from exc
    return compiled


def filter_conversation_blocks(
    blocks: Iterable[ConversationBlock],
    substrings: Iterable[str] | None = None,
    regex_patterns: Iterable[str] | None = None,
    *,
    case_sensitive: bool = False,
    keep_empty: bool = False,
) -> list[ConversationBlock]:
    """Filter Copilot chat blocks by message content.

    ``substrings`` performs containment checks while ``regex_patterns`` applies
    regular expression matching. When both are provided a message passes if it
    satisfies **any** filter. Blocks without matching messages are discarded
    unless ``keep_empty`` is enabled. A defensive copy of every kept message is
    returned so callers may mutate the result without touching the source
    collection.
    """

    has_substrings = False
    normalized_substrings: list[str] = []
    if substrings:
        for item in substrings:
            if not item:
                continue
            has_substrings = True
            normalized_substrings.append(item if case_sensitive else item.lower())

    compiled_patterns = _compile_patterns(regex_patterns, case_sensitive=case_sensitive)
    apply_filters = bool(has_substrings or compiled_patterns)

    filtered: list[ConversationBlock] = []
    for src, ts, messages, mtime in blocks:
        if not apply_filters:
            filtered.append((src, ts, [dict(msg) for msg in messages], mtime))
            continue

        kept_messages: list[dict[str, Any]] = []
        for message in messages:
            content = str(message.get("content", ""))
            haystack = content if case_sensitive else content.lower()

            matched = False
            if has_substrings and any(sub in haystack for sub in normalized_substrings):
                matched = True
            if not matched and compiled_patterns:
                for pattern in compiled_patterns:
                    if pattern.search(content):
                        matched = True
                        break

            if matched:
                kept_messages.append(dict(message))

        if kept_messages or keep_empty:
            filtered.append((src, ts, kept_messages, mtime))

    return filtered


def main():
    ap = argparse.ArgumentParser(description="Export GitHub Copilot Chat history (VS Code + Visual Studio) to Markdown.")
    ap.add_argument("--out", "-o", type=str, default="copilot_chat_history.md", help="Выходной .md")
    ap.add_argument("--since", type=str, default=None, help="Фильтр по дате YYYY-MM-DD")
    ap.add_argument(
        "--contains",
        "-c",
        action="append",
        default=None,
        help="Оставить только сообщения, содержащие подстроку (можно указать несколько раз)",
    )
    ap.add_argument(
        "--regex",
        "-r",
        action="append",
        default=None,
        help="Оставить сообщения, совпадающие с регулярным выражением",
    )
    ap.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Не понижать регистр фильтров",
    )
    ap.add_argument(
        "--keep-empty",
        action="store_true",
        help="Сохранять блоки даже без совпадающих сообщений",
    )
    args = ap.parse_args()

    since_dt: dt.datetime | None = None
    if args.since:
        try:
            since_dt = dt.datetime.fromisoformat(args.since)
        except Exception:
            print("Неверный формат --since. Используйте YYYY-MM-DD.")
            sys.exit(2)

    collected: list[ConversationBlock] = []
    collected += extract_vscode_all()
    collected += extract_visualstudio_logs()

    if since_dt:
        collected = [c for c in collected if dt.datetime.fromtimestamp(c[3]) >= since_dt]

    try:
        collected = filter_conversation_blocks(
            collected,
            substrings=args.contains,
            regex_patterns=args.regex,
            case_sensitive=args.case_sensitive,
            keep_empty=args.keep_empty,
        )
    except ValueError as exc:
        print(f"Ошибка фильтрации: {exc}")
        sys.exit(2)

    if not collected:
        print(
            "История чатов не найдена в VS Code workspaceStorage или в логах Visual Studio.\n"
            "Подсказки:\n"
            "  • Для VS Code — чаты лежат в User/workspaceStorage (state.vscdb / chatSessions/*.json)\n"
            "  • Для Visual Studio — попробуй ещё раз после новой беседы (логи создаются при сессии).\n"
            "  • Проверь параметры фильтрации (--contains/--regex), они могли исключить все сообщения."
        )
        sys.exit(1)

    collected.sort(key=lambda x: (x[1] or dt.datetime.fromtimestamp(x[3])))

    out_path = Path(args.out).resolve()
    with out_path.open("w", encoding="utf-8") as md:
        md.write("# Copilot Chat — экспорт\n\n")
        md.write(f"_Сгенерировано: {dt.datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}_\n\n")

        # Группируем блоки по типу источника для наглядности
        # VS Code JSON/DB
        md.write("## Из VS Code / VSCodium (workspaceStorage)\n\n")
        any_vscode = False
        for src, ts, msgs, mtime in collected:
            if "workspaceStorage" in src or src.endswith(".vscdb"):
                any_vscode = True
                title = "Чат (VS Code)"
                write_msgs(md, title, src, ts, msgs, mtime)
        if not any_vscode:
            md.write("_Не найдено._\n\n")

        # Visual Studio logs
        md.write("## Из Visual Studio (логи Copilot Chat)\n\n")
        any_vs = False
        for src, ts, msgs, mtime in collected:
            if src.lower().endswith(".log"):
                any_vs = True
                title = "Сеанс (Visual Studio)"
                write_msgs(md, title, src, ts, msgs, mtime)
        if not any_vs:
            md.write("_Не найдено._\n\n")

    print(f"Готово: {out_path} (найдено блоков: {len(collected)})")

if __name__ == "__main__":
    main()

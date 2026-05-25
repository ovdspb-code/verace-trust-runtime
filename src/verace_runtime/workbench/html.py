"""Tiny HTML helpers for the browser workbench."""

from __future__ import annotations

from html import escape


STYLE = """
body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:0;background:#f6f7f9;color:#15171a}
main{max-width:1040px;margin:0 auto;padding:24px}
header{background:#111827;color:white;padding:18px 24px}
nav a{color:#dbeafe;margin-right:16px;text-decoration:none}
section,.card{background:white;border:1px solid #dde2ea;border-radius:8px;margin:16px 0;padding:18px}
h1,h2{margin:0 0 12px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}
.hero{background:#f8fafc;border-color:#cbd5e1}.status{display:inline-block;border-radius:999px;padding:6px 10px;font-weight:700}
.ok{color:#047857}.fail{color:#b91c1c}.status.ok{background:#dcfce7}.status.fail{background:#fee2e2}
.notice{background:#ecfdf5;border-color:#a7f3d0}.error{background:#fef2f2;border-color:#fecaca}.actions a{margin-right:8px}
label{display:block;margin:10px 0 4px;font-weight:600}input,textarea,select{width:100%;box-sizing:border-box;padding:9px;border:1px solid #cbd5e1;border-radius:6px}
button,.button{display:inline-block;margin-top:12px;padding:9px 13px;border:0;border-radius:6px;background:#1d4ed8;color:white;text-decoration:none;cursor:pointer}
ul{padding-left:20px}.muted{color:#64748b}.meta{color:#475569;font-size:.94rem}.review-card form{margin-top:12px}
pre{white-space:pre-wrap;background:#0f172a;color:#e2e8f0;border-radius:8px;padding:16px;overflow:auto}
"""


def page(title: str, body: str, notice: str | None = None, error: str | None = None) -> str:
    messages = ""
    if notice:
        messages += f"<section class='notice'><strong>Подтверждено receipt-записью</strong><p>{escape(notice)}</p></section>"
    if error:
        messages += f"<section class='error'><strong>Ошибка</strong><p>{escape(error)}</p></section>"
    return f"""<!doctype html>
<html lang="ru">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title><style>{STYLE}</style></head>
<body><header><h1>Verace</h1><nav>
<a href="/vera">Вера</a><a href="/">Обзор</a><a href="/plan">План</a><a href="/documents">Документы</a>
<a href="/capture">Входящие</a>
<a href="/tasks/new">Задача</a><a href="/decisions/new">Решение</a>
<a href="/reviews">Проверки</a><a href="/reviews/new">На проверку</a><a href="/doctor">Диагностика</a>
</nav></header><main>{messages}{body}</main></body></html>"""


def esc(value: object) -> str:
    return escape("" if value is None else str(value))


def items(rows: list[str], empty: str = "Пока нет записей.") -> str:
    if not rows:
        return f"<p class='muted'>{escape(empty)}</p>"
    return "<ul>" + "".join(f"<li>{row}</li>" for row in rows) + "</ul>"

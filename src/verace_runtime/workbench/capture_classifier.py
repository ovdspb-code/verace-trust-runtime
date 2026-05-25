"""Deterministic classifier for pasted working text."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CaptureSuggestionCandidate:
    kind: str
    title: str
    body: str
    reason: str
    source_span: str | None = None


def classify_capture(raw_text: str, source_type: str = "other") -> list[CaptureSuggestionCandidate]:
    text = raw_text.strip()
    if not text:
        return [_ignore("Empty capture text")]
    lowered = text.lower()
    suggestions: list[CaptureSuggestionCandidate] = []
    if _has_any(text, ("TASK FOR CODEX", "Goal:", "Acceptance criteria:")):
        suggestions.append(_codex_task(text, source_type))
    if _has_any(text, ("FOUNDER DECISION:", "РЕШЕНИЕ:", "Решение:")):
        suggestions.append(_decision(text))
    if _looks_like_codex_report(text):
        suggestions.append(_review_report(text))
        next_work = _line_with(lowered, ("next intended work", "next work", "следующий шаг"))
        if next_work:
            suggestions.append(_task("Продолжить следующий шаг из отчета", next_work, "Codex report names next work"))
    if _has_any(lowered, ("blocker", "риск", "risk", "опасность", "fail", "сломалось", "не работает")):
        suggestions.append(_risk(text))
    if _has_any(lowered, ("нужно", "надо", "сделать", "подготовить", "implement", "fix", "add", "create")):
        suggestions.append(_task(_task_title(text), _clip(text), "Task-like wording found"))
    return _dedupe(suggestions) or [_ignore("No actionable signal found by deterministic classifier")]


def _decision(text: str) -> CaptureSuggestionCandidate:
    line = _line_with(text, ("FOUNDER DECISION:", "РЕШЕНИЕ:", "Решение:")) or _first_line(text)
    body = line.split(":", 1)[1].strip() if ":" in line else _clip(text)
    return CaptureSuggestionCandidate("decision", _title(body, "Зафиксировать решение"), body, "Explicit decision marker found", line)


def _review_report(text: str) -> CaptureSuggestionCandidate:
    return CaptureSuggestionCandidate(
        "review",
        "Review Codex report",
        "Проверить отчет Codex и подтвердить, что результаты полезны и receipt-backed.",
        "Codex report markers found",
        _first_line(text),
    )


def _risk(text: str) -> CaptureSuggestionCandidate:
    line = _line_with(text.lower(), ("blocker", "риск", "risk", "опасность", "fail", "сломалось", "не работает")) or _first_line(text)
    return CaptureSuggestionCandidate("risk_review", "Проверить риск из захвата", _clip(text), "Risk/blocker wording found", line)


def _task(title: str, body: str, reason: str) -> CaptureSuggestionCandidate:
    return CaptureSuggestionCandidate("task", _title(title, "Создать задачу"), body, reason, _first_line(body))


def _codex_task(text: str, source_type: str) -> CaptureSuggestionCandidate:
    return CaptureSuggestionCandidate("codex_task", "Codex task из захвата", _clip(text), f"Structured Codex prompt markers found in {source_type}", _first_line(text))


def _ignore(reason: str) -> CaptureSuggestionCandidate:
    return CaptureSuggestionCandidate("ignore", "Игнорировать захват", "Нет надежного сигнала для задачи, решения или проверки.", reason)


def _looks_like_codex_report(text: str) -> bool:
    return _has_any(text, ("Готово", "Commit:", "PR:", "Checks", "pytest", "Final git status"))


def _has_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _line_with(text: str, needles: tuple[str, ...]) -> str | None:
    for line in text.splitlines():
        if any(needle in line for needle in needles):
            return line.strip()
    return None


def _task_title(text: str) -> str:
    line = _line_with(text.lower(), ("нужно", "надо", "сделать", "подготовить", "implement", "fix", "add", "create"))
    return line or _first_line(text)


def _first_line(text: str) -> str:
    return next((line.strip() for line in text.splitlines() if line.strip()), "")


def _clip(text: str, limit: int = 600) -> str:
    compact = " ".join(text.split())
    return compact[:limit]


def _title(text: str, fallback: str) -> str:
    compact = " ".join(text.split())
    if not compact:
        return fallback
    return compact[:90]


def _dedupe(items: list[CaptureSuggestionCandidate]) -> list[CaptureSuggestionCandidate]:
    seen: set[tuple[str, str]] = set()
    out: list[CaptureSuggestionCandidate] = []
    for item in items:
        key = (item.kind, item.title)
        if key not in seen:
            out.append(item)
            seen.add(key)
    return out

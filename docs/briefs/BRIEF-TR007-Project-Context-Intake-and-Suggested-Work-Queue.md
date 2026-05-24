# BRIEF-TR007: Project Context Intake and Suggested Work Queue

Status: Implemented in PR draft scope

## Goal

Make Browser Founder Workbench useful without manual empty-form entry by adding deterministic project context intake from repository documentation and a suggested work queue.

## Context

FOUNDER-TRIAL-002 showed that the Browser Founder Workbench can support real sessions, but it starts empty unless Oleg manually reconstructs project state. The next product step is for the workbench to read local project documentation and propose useful next actions.

## Product Effect

Oleg opens the browser workbench and sees:

- what project he is in;
- where the project stands;
- what documents exist;
- what the next proposed work is;
- which risks or reviews need attention;
- proposed task, decision, review, and Codex-task cards that he can edit and accept.

## Scope

Implement deterministic local markdown intake for:

- `README.md`;
- `docs/ops/PROJECT_STATE.md`;
- `docs/ops/WORKLOG.md`;
- `docs/ops/DECISIONS.md`;
- `docs/ops/RISK_REGISTER.md`;
- `docs/ops/SESSION_PROTOCOL.md`;
- `docs/adr/*.md`;
- `docs/briefs/*.md`;
- `docs/plans/*.md`.

Add browser pages:

- `/plan`;
- `/documents`;
- prefilled suggestion accept forms;
- deterministic Codex task text rendering.

## Non-goals

- No ADR.
- No LLM/provider integration.
- No Telegram/channel integration.
- No external APIs or GitHub API.
- No arbitrary natural-language understanding.
- No npm, React, Vite, external CSS, or CDN.
- No runtime core semantic changes.

## Acceptance Criteria

- Browser workbench no longer starts as an empty manual notebook.
- `/plan` shows current project state and next intended work from docs.
- `/documents` shows the documentation map.
- Suggested work cards are generated from local docs.
- Oleg can edit and accept suggestions as task, review, or decision.
- Codex task prompt can be generated from a suggestion.
- Read-only intake pages do not mutate ledger.
- State-changing accept actions create receipt-backed confirmations.

# BRIEF-TR008: Conversation Capture Inbox

**Status:** Implemented in progress  
**Date:** 2026-05-24  
**Mode:** Product loop first

## Goal

Add a Conversation Capture Inbox to the Browser Founder Workbench.

Oleg can paste a fragment from ChatGPT, Codex, Claude, Telegram, or local notes. The Workbench stores the capture locally, classifies it deterministically, and proposes editable suggestions:

- task;
- decision;
- review;
- risk review;
- Codex task;
- ignore.

## Product Boundary

The Workbench is not a manual notebook. It should bridge Oleg's real working text into Verace Runtime suggestions, then wait for human approval before ledger mutation.

## Deterministic Classification

This brief does not add LLM synthesis.

Classification uses simple local rules:

- explicit decision markers create decision suggestions;
- Codex report markers create review and next-work suggestions;
- blocker/risk wording creates risk-review suggestions;
- task-like wording creates task suggestions;
- structured Codex prompt markers create Codex-task suggestions;
- text with no actionable signal creates an ignore suggestion.

Suggestions are candidates, not truth.

## Receipt Boundary

Recording a capture creates a receipt-backed capture item.

Accepting a suggestion as task, decision, or review reuses existing runtime creation paths and produces receipt-backed ledger records. Dismiss and Codex prompt preview are not ledger-success claims.

## Non-Goals

- No LLM/provider integration.
- No Telegram/channel integration.
- No external API calls.
- No GitHub API integration.
- No voice input.
- No automatic chat scraping.
- No browser extension.
- No npm, React, Vite, external CSS, or CDN.
- No runtime DB/log/secret/private files committed.

## Residual Risk

The deterministic classifier is intentionally shallow. Future LLM-assisted capture and channel ingestion must preserve the thin-wrapper / hard-facts boundary: suggestions may be synthesized, but ledger mutation still requires explicit founder approval and receipts.

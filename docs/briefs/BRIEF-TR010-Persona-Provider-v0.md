# BRIEF-TR010: Persona Provider v0

Status: Proposed v1.0  
Date: 2026-05-26

## Goal

Connect `/vera` to a real model provider so Vera becomes a usable conversational founder entry, while preserving Verace runtime fact boundaries.

## Product Decision

Fallback-only Vera is not founder UX. A founder trial is valid only when `/vera` uses a real provider to compose useful responses.

The first provider is the OpenAI Responses API. The provider is replaceable and environment-gated:

- `VERACE_PERSONA_PROVIDER=openai`
- `OPENAI_API_KEY`
- `VERACE_PERSONA_MODEL`

## Boundary

- LLM owns voice, synthesis, explanation, and proposed next actions.
- Runtime owns facts, permissions, approvals, receipts, claims, and ledger state.
- Human approval is required before task, decision, or review mutation.
- Vera may not claim that she recorded, created, checked, sent, merged, or completed anything unless the runtime has a receipt-backed result.

## Scope

- Add an OpenAI Responses API persona provider adapter.
- Build provider prompts from user message, verified project context, ledger summary, and deterministic candidate hints.
- Ask the provider for a human Russian answer plus `proposed_actions`.
- Keep `store=false` explicit.
- Disable tool/function calling in v0.
- Keep tests on fake/local providers only.

## Non-goals

- No Telegram, channel integration, autonomous tools, external action execution, generic agent framework, npm, React, or Vite.
- No model-owned durable state.
- No ledger mutation before explicit confirmation.
- No Workbench expansion.

## Acceptance

- `/vera` clearly reports unavailable state when no provider is configured and does not pretend to be Vera.
- With a configured provider, Vera can answer a natural question using project/runtime context.
- Provider proposed actions do not mutate the ledger.
- Explicit confirmation creates receipt-backed task, decision, or review entries through existing runtime paths.
- Final "recorded/created" language is shown only after receipt-backed runtime results.
- Tests do not make external API calls.

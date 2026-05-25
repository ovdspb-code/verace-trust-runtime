# BRIEF-TR009: Persona Front Door

Status: Proposed v1.0  
Date: 2026-05-25

## Goal

Make the primary founder entry point a live persona front door instead of a dispatcher cockpit.

## Product Decision

Verace follows the Front-of-House Model:

```text
Persona is the interface.
Runtime is the truth.
Workbench is the audit cockpit.
```

Oleg should enter through a conversational assistant that explains, proposes, and clarifies. The runtime remains the accounting and trust layer for mandates, policy, actions, receipts, claims, ledger state, evidence, and review/audit.

## Scope

- Add `/vera` as the first browser Persona Front Door.
- Keep Workbench available as backstage/audit/doctor/review surface.
- Keep Capture Inbox available as an ingestion primitive, not the main founder workflow.
- Use deterministic capture hints as backstage signal.
- Require explicit founder confirmation before ledger mutation.
- Reuse existing receipt-backed task, decision, and review paths.

## Non-goals

- No new ADR.
- No Telegram, channel, LLM provider, external API, npm, React, or Vite integration.
- No generic multi-agent framework.
- No workflow builder.
- No runtime truth in the model.
- No system-action success claims without receipt-backed runtime results.

## UX Rule

The founder should not perform manual runtime taxonomy work. Internal kinds may exist in code, but the visible front door should speak naturally:

- record as a useful task;
- fix a decision;
- put a concern on review;
- ask for clarification.

It should not present task/review/decision/capture cards as the primary mental model.

## Voice Boundary

The persona voice should remain alive and conversational. Runtime controls constrain operational facts only. A persona may say "I think", "I suggest", or "this looks important"; it may not say "I recorded", "I created", "I checked", "I sent", or "I merged" unless a receipt-backed result exists.

## Acceptance

- `/vera` exists.
- Natural text produces a human-facing draft response.
- Ledger state does not change without explicit confirmation.
- Confirmed task/decision/review actions create receipt-backed entries.
- Workbench, Capture Inbox, Plan, Documents, and Doctor remain available as backstage surfaces.

# Decisions

Durable operating decisions for Verace - Trust Runtime.

| ID | Decision | Source |
| --- | --- | --- |
| D-TR-001 | Verace remains the umbrella platform. | ADR-TR002 |
| D-TR-002 | Existing TruthOps becomes Verace Truth. | ADR-TR002 |
| D-TR-003 | Founder Assistant is the first canary, not the architecture. | ADR-TR002 / PLAN-TR001 / ADR-TR003 |
| D-TR-004 | No receipt, no success claim. | ADR-TR002 |
| D-TR-005 | State is not in the model. | ADR-TR002 |
| D-TR-006 | ADR-TR004 Runtime Ledger Minimal Contract accepted; Runtime Ledger is operational source of truth. | ADR-TR004 |
| D-TR-007 | ADR-TR005 Receipt and Approval Policy accepted; consequential external action requires mandate or approval, and success claims require receipts. | ADR-TR005 |
| D-TR-008 | ADR-TR006 Runtime Schema and Migration Policy accepted; runtime schemas are versioned contracts and unknown schema states must fail closed. | ADR-TR006 |
| D-TR-009 | Bugfixes and hardening changes are accepted only when the failure class is closed, not when the demonstrated case is green. Every fix must define the class axis, invariant, parametric tests, fail-closed behavior for unknown variants, and residual risk. | FAILURE_CLASS_CLOSURE / Porthos memo 2026-05-24 |
| D-TR-010 | Human-facing factual statements about the system's own actions must be rendered from ledger/receipt fields or validated against receipts; otherwise the runtime must fail closed, repair, clarify, or downgrade the statement. | FAILURE_CLASS_CLOSURE / ADR-TR002 |
| D-TR-011 | ADR-TR007 Human-Facing System-Action Claim Rendering accepted; future channel/LLM-facing system-action statements must be rendered from or validated against receipt-backed runtime state. | ADR-TR007 |
| D-TR-012 | Verace primary founder UX follows the Front-of-House Model: live persona as entry point, runtime as trust controller, Workbench as backstage/audit cockpit, and Capture Inbox as ingestion capability rather than primary founder workflow. | Founder decision / TR009 |
| D-TR-013 | Persona Provider v0 uses an env-gated, replaceable OpenAI Responses API adapter; `store=false` is explicit, tools are disabled, and no founder trial is valid while `/vera` is fallback-only. | Founder decision / BRIEF-TR010 |

## Decision Discipline

Codex may implement inside an accepted brief. Codex may not ratify strategy, approve architecture, or expand scope beyond the brief.

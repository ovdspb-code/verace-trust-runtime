# PLAN-TR001: Verace Work Plan — From Founder Assistant to Trust Runtime

**Status:** Accepted v1.0  
**Date:** 2026-05-23  
**Ratified:** 2026-05-23 by Oleg Dolgikh  
**Owner:** Oleg Dolgikh  
**Project:** Verace — Trust Runtime  
**Scope:** Strategic work plan, phase gates, sequencing doctrine  
**Governing ADR:** ADR-TR002: Verace as Trust Runtime for AI Work  

---

## 1. Decision

We start with a working prototype of Oleg’s personal assistant.

This is not a retreat from the larger Verace vision. It is the seed implementation of it.

The first product surface is personal because it gives us:

- a real principal;
- real mandates;
- real documents;
- real follow-ups;
- real approvals;
- real memory pressure;
- real failure visibility;
- real daily use.

The strategic product remains broader:

> **Verace makes AI work verifiable.**

The first proof of that product is a founder-grade assistant that helps Oleg run the Verace project itself with durable tasks, decisions, documents, receipts, approvals, and review loops.

The product grows in this order:

```text
Founder Assistant
  → Founder Operating System
  → Verace Runtime
  → Verace Truth Integration
  → Team / Office Trust Runtime
  → External Agent / Tool Gateway
  → Platform for Verifiable AI Work
```

---

## 2. Planning Principle

This plan is phase-gated, not date-gated.

A phase is complete only when its trust contract is proven in use. Calendar targets may guide execution, but they do not override readiness.

The governing chain is:

```text
mandate → policy → action → receipt → claim → ledger → review/audit
```

The first assistant must therefore be useful immediately, but it must not become a toy wrapper around a model. Every capability added to the assistant must either:

1. improve Oleg’s real work loop; or
2. strengthen the reusable Verace Runtime; or
3. generate evidence for the future platform.

Anything else is product noise.

---

## 3. Non-Negotiable Constraints

1. **No receipt, no success claim.**  
   The assistant may not claim that an external action, document delivery, upload, send, or state change happened unless the runtime has a receipt.

2. **State is not in the model.**  
   Tasks, decisions, approvals, reminders, documents, delivery state, and mandates live in the runtime ledger.

3. **The personal assistant is a canary, not the architecture.**  
   Porthos / Vera / Telegram / chat UI are interfaces. Verace is the trust substrate.

4. **Founder work is the first benchmark.**  
   The system must help Oleg run Verace better before it claims general product value.

5. **Core first, intelligence second.**  
   Stable ledger, task state, outbox, receipts, approvals, backup, and recovery come before advanced agent behavior.

6. **No OpenClaw / Hermes clone.**  
   We do not build a generic agent framework, marketplace, workflow builder, or orchestration theater.

7. **TruthOps is preserved.**  
   Existing Verace Truth work becomes the knowledge-verification line and later plugs into the runtime through explicit boundaries.

---

## 4. Phase Overview

| Phase | Name | Product meaning | Trust gate |
|---|---|---|---|
| 0 | Operating Base | Prepare project discipline and repo/ADR control | Codex can execute bounded tasks without ambiguity |
| 1 | Founder Assistant Seed | Oleg gets a useful daily assistant | Tasks, reminders, notes, and answers survive restart |
| 2 | Receipts & Approvals | Assistant becomes trustworthy for work artifacts | No completion claim without evidence |
| 3 | Founder Operating System | Assistant helps run Verace itself | ADRs, decisions, tasks, reviews, and Codex work become ledgered |
| 4 | Verace Runtime Extraction | Reusable runtime separates from assistant UX | Core concepts are portable beyond Oleg’s assistant |
| 5 | Verace Truth Integration | Knowledge claims enter the trust loop | Important project/company claims can be checked and routed |
| 6 | Multi-Contour Work | Extend from Oleg to office/team/project contours | No cross-contour leakage; approvals are enforceable |
| 7 | Gateway Readiness | Tools, agents, credentials, payments become future ports | External action remains mandate- and receipt-bound |
| 8 | Platform Wedge | Convert internal runtime into marketable product | Clear first buyer/use-case, not generic platform vapor |

---

## 5. Phase 0 — Operating Base

### Goal

Create the working discipline for the project before building more code.

### Scope

- ADR index.
- Work plan register.
- Decision register.
- Codex task format.
- Repo-state protocol.
- Evidence folder convention.
- Minimal naming rules for Verace Runtime, Porthos, Vera, and Verace Truth.

### Output

A project spine that prevents architectural drift:

```text
ADR → task → implementation → test evidence → receipt → decision/update
```

### Acceptance Criteria

- Every Codex task has goal, context, non-goals, files, constraints, tests, acceptance criteria, rollback, and done definition.
- No task says “improve architecture” without a bounded deliverable.
- Project state can be reconstructed from files, not memory.
- The current strategic ADRs are indexed and referenced.

---

## 6. Phase 1 — Founder Assistant Seed

### Goal

Build the first useful personal assistant for Oleg as a daily working surface.

This assistant should initially be modest but reliable. It should help Oleg manage Verace, not perform theatrical autonomy.

### Core Use Cases

- capture tasks and follow-ups;
- summarize current open work;
- remember project decisions;
- prepare drafts for ADRs, Codex tasks, memos, investor notes, and product text;
- track “waiting for” items;
- remind about unresolved decisions;
- keep separate contours for personal, Verace, office/family, finance/legal;
- produce a daily or session-level project brief.

### Exclusions

- no autonomous money movement;
- no legal commitments;
- no external sending without approval;
- no hidden background work;
- no multi-agent orchestration;
- no general plugin system.

### Output

A small working assistant surface with durable state.

The first assistant may be Telegram-first or another fast channel, but the channel must not become the state engine.

### Acceptance Criteria

- Oleg can ask “что открыто по Verace?” and receive a ledger-grounded status.
- Follow-up messages attach to the correct task or produce clarification.
- The assistant can distinguish project note, task, decision, draft, and approval request.
- Restart does not lose active work.
- Every inbound message ends as answer, ack, clarify, status, approval request, review route, or explicit failure.
- No raw internal machinery leaks into normal chat.

---

## 7. Phase 2 — Receipts & Approvals

### Goal

Move from “helpful assistant” to “trustworthy assistant.”

### Scope

Add the first hard trust primitives:

- receipts for created files;
- receipts for uploads;
- receipts for sent/drafted messages where available;
- explicit approval gates;
- failure receipts;
- visible task state;
- simple policy rules for risky actions.

### Output

The assistant can safely handle real work artifacts.

Examples:

- “подготовь ADR для Codex” → draft file receipt;
- “сохрани в проект” → storage receipt;
- “отправь” → approval request first;
- “готово?” → status based on ledger, not model memory.

### Acceptance Criteria

- The system cannot claim file creation, delivery, or external sending without a receipt.
- Failed tools produce explicit failure, not a fake completion.
- Human approval is required before external send, legal commitment, payment, or sensitive-data disclosure.
- Receipts are visible enough for Oleg to audit without becoming UX noise.

---

## 8. Phase 3 — Founder Operating System

### Goal

Turn the assistant into the operating system for building Verace.

This is the first compounding loop: the tool helps build itself and records how it was built.

### Scope

- ADR lifecycle support;
- Codex task generation and tracking;
- architecture decision ledger;
- review backlog;
- open risk register;
- weekly/project review;
- “what changed since last session” brief;
- document pack generation;
- founder-ground-truth capture;
- evidence packs for completed work.

### Output

Oleg can manage Verace through the assistant with a reliable project memory and work ledger.

### Acceptance Criteria

- Each strategic decision can be traced to an ADR, memo, task, or founder instruction.
- Codex work can be tracked from assignment to evidence.
- Review items are not silently buried.
- The assistant can produce a current Verace project brief from ledgered facts.
- “Что мы решили и почему?” is answerable without hallucinated history.

---

## 9. Phase 4 — Verace Runtime Extraction

### Goal

Separate reusable runtime from the personal assistant product layer.

### Scope

Extract the stable core concepts:

- Contour;
- Mandate;
- Claim;
- Receipt;
- Approval;
- Ledger;
- Codex / evidence snapshot;
- Disposition;
- Policy;
- Provider adapter;
- Channel adapter.

### Output

A lightweight Verace Runtime that can support Porthos, Vera, future assistant surfaces, and later enterprise use cases.

### Acceptance Criteria

- The runtime does not depend on Oleg-specific data, Telegram-specific assumptions, or one provider.
- The assistant product layer owns persona and workflows.
- The runtime owns state, evidence, permissions, receipts, and policy.
- A second interface or contour can be added without rewriting the core.

---

## 10. Phase 5 — Verace Truth Integration

### Goal

Connect the existing Verace TruthOps lineage to the new runtime without importing the old backend as a monolith.

### Scope

- define TruthCheck boundary;
- route knowledge-sensitive claims to review/check;
- use Verace Truth concepts for project knowledge and later enterprise corpora;
- preserve TruthKey / TruthRecord / TruthSnapshot direction;
- bring authority-frame thinking into mandate/action context.

### Output

The assistant and runtime can distinguish:

- user instruction;
- project fact;
- knowledge claim;
- unresolved uncertainty;
- founder-ground-truth decision;
- verified evidence.

### Acceptance Criteria

- Knowledge-sensitive claims can be flagged as verified, needs review, outdated, conflicting, or insufficiently evidenced.
- Verace Truth remains a product line, not a hard dependency of the lightweight assistant runtime.
- The system does not block basic office work when the Truth pipeline is unavailable.
- Founder-approved truths are not overwritten by LLM verdicts.

---

## 11. Phase 6 — Multi-Contour Work

### Goal

Move from one founder assistant to a trusted work environment across people, roles, and contexts.

### Scope

- Oleg private contour;
- Verace project contour;
- office/team contour;
- finance/legal contour;
- partner/client contour later;
- role-specific visibility;
- cross-contour approval rules;
- contour-local memory.

### Output

Verace becomes useful beyond one chat without losing trust boundaries.

### Acceptance Criteria

- Tasks and memories do not bleed across contours.
- The same person can have different permissions in different contours.
- External sharing requires policy and approval.
- A team member can use an interface without seeing founder-private state.
- Review/audit can reconstruct what happened in each contour.

---

## 12. Phase 7 — Gateway Readiness

### Goal

Prepare Verace for the world of external tools, agents, credentials, and payments without committing to any protocol as the core.

### Scope

- Tool boundary;
- Agent boundary;
- Credential boundary;
- Payment boundary;
- external receipt normalization;
- external agent trust profile;
- inbound/outbound mandate checks.

### Output

Verace can become the trust gateway between a principal and external AI-mediated action.

### Acceptance Criteria

- External tools and agents enter through explicit boundaries.
- Every external action is tied to mandate, policy, receipt, and ledger state.
- Payment/legal/sensitive actions remain approval-gated.
- Protocol integrations remain adapters, not architecture.

---

## 13. Phase 8 — Platform Wedge

### Goal

Convert the internal runtime into an external product wedge.

### Strategic Options

The first market wedge should be chosen from proven internal usage, not imagined platform breadth.

Likely candidates:

1. **Founder / principal operating runtime**  
   For entrepreneurs, investors, family offices, and small executive teams.

2. **Verifiable AI work for regulated teams**  
   For legal, finance, compliance, procurement, and due diligence workflows.

3. **Verace Truth + Mandate for enterprise AI**  
   Knowledge verification plus controlled agent action.

4. **Due diligence / transaction cockpit**  
   Project- and document-heavy work where claims, approvals, and evidence matter immediately.

### Output

A narrow commercial product that carries the full Verace DNA without claiming to be a universal platform.

### Acceptance Criteria

- The buyer has a concrete painful workflow.
- The product can be explained without saying “AI assistant.”
- Receipts, claims, mandates, approvals, and ledger are visible product value, not backend trivia.
- The wedge compounds into the broader trust runtime.

---

## 14. Parallel Track: Verace Truth

Verace Truth must continue as a living product line, but it should not block the personal assistant/runtime seed.

### Maintain

- existing TRM/ADR discipline;
- Truth Codex direction;
- conflict detection work that is already validated;
- due diligence / compliance wedge thinking;
- founder-ground-truth review discipline.

### Do Not Do Yet

- deep backend merge;
- schema unification by force;
- enterprise-grade containment claims for the new runtime;
- Truth pipeline dependency in the assistant hot path.

### Integration Rule

Verace Truth enters the new runtime through contracts and ports first. Shared concepts precede shared infrastructure.

---

## 15. Phase Gate Metrics

The project should be measured by trust and usefulness, not by agentic theatrics.

### Founder Usefulness

- reduced forgotten tasks;
- faster project recall;
- cleaner Codex task flow;
- fewer repeated explanations;
- reliable status on open work.

### Runtime Trust

- zero false completion claims in tested flows;
- restart recovery proven;
- receipt coverage for artifact workflows;
- approval gates enforced;
- no cross-contour leakage in tests.

### Product Learning

- repeated workflows identified;
- manual review points identified;
- externalizable buyer pain identified;
- reusable contracts stabilized.

### Engineering Discipline

- bounded ADRs;
- tests before claims;
- no repo-state assertions without evidence;
- no hidden provider lock-in;
- no speculative framework expansion.

---

## 16. Risks and Controls

| Risk | Control |
|---|---|
| Personal assistant becomes a side quest | Treat it as the first runtime canary; every feature must map to Verace concepts. |
| Assistant UX dictates architecture | Keep interface layer separate from runtime. |
| Runtime becomes too heavy too early | Start with boring primitives and prove them in daily use. |
| Verace Truth roadmap gets abandoned | Preserve it as a parallel product line and later integrate through TruthCheck boundary. |
| False completion erodes trust | Make receipt-required claims a hard invariant. |
| Cross-contour leakage | Use contours as durable trust boundaries from early phases. |
| Codex overbuilds | Feed Codex small, testable tasks only. |
| Platform story becomes vague | Keep first wedge narrow and grounded in real workflows. |

---

## 17. First Implementation Doctrine

The first implementation must optimize for reliability, not sophistication.

Preferred first build shape:

```text
personal assistant surface
        ↓
runtime ledger
        ↓
mandates / tasks / messages / approvals / receipts
        ↓
provider adapter
        ↓
validated envelope
        ↓
outbox / user-visible response
```

The assistant may sound human. The runtime must behave like accounting.

---

## 18. Immediate Program Backlog

These are the first program-level documents/tasks after this plan.

1. **ADR-TR003: Founder Assistant as First Runtime Canary**  
   Define why the personal assistant is the first implementation surface and what it must not become.

2. **ADR-TR004: Runtime Ledger Minimal Contract**  
   Define the first durable state contract: contours, mandates, tasks, messages, receipts, approvals, claims, outbox.

3. **ADR-TR005: Receipt and Approval Policy**  
   Define which actions require receipt, approval, review, or hard block.

4. **Implementation Brief 001: Porthos Seed / Founder Assistant MVP**  
   Bounded Codex task for the first working prototype.

5. **Implementation Brief 002: Project Operating Memory**  
   Decision register, task register, ADR index, and daily brief support.

---

## 19. Ratification Criteria

This plan is accepted when Oleg confirms:

1. The first implementation surface is Oleg’s personal assistant.
2. The assistant is a runtime canary, not the final product category.
3. Verace remains the platform strategy.
4. The phase order is accepted: assistant → operating system → runtime extraction → Truth integration → multi-contour → gateway → platform wedge.
5. No phase may violate “No receipt, no success claim.”
6. Detailed technical decisions must be handled by lower-level ADRs and implementation briefs.

Once accepted, changes to this plan should require a founder-level planning update, not routine implementation drift.

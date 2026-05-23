# ADR-TR003: Founder Assistant as First Runtime Canary

**Status:** Proposed v1.0  
**Date:** 2026-05-23  
**Owner:** Oleg Dolgikh  
**Project:** Verace — Trust Runtime  
**Scope:** First implementation surface, product boundary, canary doctrine  
**Governing ADR:** ADR-TR002: Verace as Trust Runtime for AI Work  
**Governing Plan:** PLAN-TR001: Verace Work Plan — From Founder Assistant to Trust Runtime  

---

## 1. Decision

The first implementation surface of Verace Runtime will be Oleg’s personal founder assistant.

This assistant is the first runtime canary: a live, daily-use proving ground for mandate-bound, evidence-backed AI-mediated work.

It is not the final product category. It is not a Telegram bot strategy. It is not a generic assistant platform. It is the smallest real environment where Verace can prove its core promise:

> **Verace makes AI work verifiable.**

The assistant exists to make Oleg’s real work on Verace more systematic while generating the first reusable runtime primitives for the broader platform.

---

## 2. Why This Starts Here

A founder assistant is the right seed because it gives the runtime real pressure immediately:

- a real principal;
- real mandates;
- real decisions;
- real documents;
- real follow-ups;
- real approvals;
- real memory pressure;
- real ambiguity;
- real failure visibility;
- real daily use.

A synthetic demo would optimize for appearance. A founder assistant optimizes for survival.

The assistant must help run the Verace project itself: ADRs, Codex tasks, decisions, risks, worklogs, research, drafts, evidence, and review loops.

This creates the first compounding loop:

```text
Verace helps build Verace.
```

---

## 3. Product Boundary

The assistant is a product surface.

The runtime is the strategic asset.

The assistant may own:

- tone;
- persona;
- channel-specific UX;
- founder workflow shortcuts;
- project-specific commands;
- drafting style;
- daily/session briefing format.

The runtime must own:

- identity;
- contours;
- mandates;
- task state;
- messages;
- approvals;
- receipts;
- claims;
- ledger;
- outbox;
- policy decisions;
- review/audit state.

A channel may carry the conversation. It must not own truth, state, or authority.

---

## 4. Core Doctrine

The assistant must follow the same governing chain as Verace Runtime:

```text
mandate → policy → action → receipt → claim → ledger → review/audit
```

In the founder-assistant phase, this means:

1. Oleg gives an instruction.
2. The system records or derives the relevant mandate.
3. Policy determines whether the work can proceed, needs clarification, needs approval, or must be blocked.
4. Actions are performed only inside the permitted boundary.
5. Each consequential action produces a receipt or an explicit failure.
6. The assistant may claim completion only from ledgered evidence.
7. Uncertainty becomes review, clarification, approval request, or explicit failure.

The assistant may sound human. The runtime must behave like accounting.

---

## 5. First Useful Work Loop

The first assistant should be useful before it is sophisticated.

The initial work loop is:

```text
capture → classify → ledger → status → draft/action → receipt → review
```

The assistant should help with:

- capturing tasks and follow-ups;
- maintaining project status;
- remembering decisions;
- drafting ADRs, implementation briefs, memos, investor notes, and product language;
- tracking waiting-for items;
- surfacing unresolved decisions;
- keeping a risk register alive;
- preparing session/project briefs;
- tying Codex work to tasks, evidence, and review outcomes.

The benchmark is not whether the assistant appears impressive. The benchmark is whether Oleg can run Verace with less repeated explanation, fewer lost threads, clearer decisions, and better evidence.

---

## 6. Non-Negotiable Invariants

1. **No receipt, no success claim.**  
   The assistant cannot claim that a file was created, saved, uploaded, sent, delivered, or externally changed unless the runtime has a receipt.

2. **State is not in the model.**  
   Tasks, decisions, mandates, reminders, approvals, documents, delivery state, and review state live in the ledger.

3. **Every inbound message ends somewhere.**  
   Each message must become an answer, acknowledgement, clarification, status, approval request, review route, or explicit failure.

4. **Founder work is the first benchmark.**  
   The assistant must help Oleg run Verace better before it claims broader product value.

5. **Personal does not mean private architecture.**  
   Oleg-specific data, tone, and workflows belong in the assistant layer, not in the reusable runtime core.

6. **Interfaces are not the core.**  
   Telegram, web, email, local CLI, ChatGPT, and future channels are replaceable surfaces.

7. **Risky actions require approval.**  
   External sending, legal commitments, payments, sensitive data disclosure, irreversible operations, and customer-visible obligations require explicit approval unless a later mandate/policy ADR grants a narrower exception.

8. **No orchestration theater.**  
   Do not build a multi-agent framework, workflow marketplace, generic plugin system, or OpenClaw/Hermes clone.

---

## 7. Initial Contours

The assistant should treat contours as durable trust boundaries from the beginning, even if the first implementation represents them simply.

The first conceptual contours are:

- **Oleg Private** — personal founder context;
- **Verace Project** — ADRs, Codex tasks, product strategy, repository state, worklog, risks;
- **Office / Family** — later, only when needed;
- **Finance / Legal** — later, approval-heavy by default;
- **External / Investor / Partner** — later, explicit-send and visibility controls required.

The first implementation may start with only Oleg Private and Verace Project, but it must not assume that one chat equals one durable trust boundary forever.

---

## 8. Relationship to Verace Truth

The founder assistant must not import the existing Verace TruthOps backend as a hard dependency.

Verace Truth remains a first-class product line and will later connect through explicit contracts and ports.

During the founder-assistant phase, Verace Truth concepts should influence the runtime:

- claims are not automatically true;
- founder-approved truth overrides LLM disagreement;
- unresolved uncertainty routes to review;
- evidence and snapshots matter;
- signed or reproducible artifacts are more valuable than generated text.

But the assistant must remain useful even before the Truth pipeline is integrated.

---

## 9. What This ADR Does Not Decide

This ADR does not decide:

- final channel choice;
- repository/package layout;
- database schema;
- provider selection;
- prompt design;
- UI design;
- deployment topology;
- integration with old Verace backend;
- MCP/A2A/AP2/VC integration;
- payment or legal execution capability.

Those belong to lower-level ADRs and implementation briefs.

---

## 10. Strategic Consequences

1. The first build must optimize for reliability, not theatrical autonomy.
2. The assistant must be useful in daily founder work quickly.
3. Every assistant feature must map to a reusable Verace concept or a real founder workflow.
4. The runtime must be extracted from the assistant once the core work loop is proven.
5. The assistant is allowed to be personal; the runtime is not allowed to be parochial.
6. Codex tasks must remain small, bounded, and evidence-producing.
7. A feature that cannot produce status, evidence, or a clear failure path is not ready for this phase.

---

## 11. Success Criteria

ADR-TR003 is successful when the next implementation brief can be written without ambiguity.

The implementation brief must be able to define:

- the first assistant surface;
- the first contours;
- the first ledger-backed work objects;
- the first commands or interaction patterns;
- the first receipt types;
- the first approval gates;
- the first restart/recovery checks;
- the first “what is open?” project-status answer;
- the first no-false-completion tests.

The assistant seed is successful when Oleg can ask:

```text
что открыто по Verace?
что мы решили?
что ждёт Codex?
что требует моего решения?
что было сделано и чем это подтверждено?
```

—and receive ledger-grounded answers rather than model memory theater.

---

## 12. Non-Goals

This ADR does not approve building:

- a generic personal assistant;
- a Telegram-only bot;
- an agent framework;
- a plugin marketplace;
- autonomous money movement;
- autonomous legal commitments;
- external sending without approval;
- hidden background work;
- provider-specific architecture;
- a mechanical merge with the existing Verace TruthOps backend.

---

## 13. Next Documents

After this ADR is accepted, the next documents are:

1. **ADR-TR004: Runtime Ledger Minimal Contract**  
   Defines the first durable state contract.

2. **ADR-TR005: Receipt and Approval Policy**  
   Defines which actions require receipt, approval, review, or hard block.

3. **BRIEF-TR001: Founder Assistant MVP**  
   First bounded implementation brief for Codex.

Implementation work should not begin from this ADR alone. It begins from BRIEF-TR001 after ADR-TR004 and ADR-TR005 define the minimal runtime and trust gates, unless Oleg explicitly approves a narrower spike.

---

## 14. Ratification Criteria

This ADR is accepted when Oleg confirms:

1. The first implementation surface is Oleg’s personal founder assistant.
2. The assistant is the first runtime canary, not the final product category.
3. The assistant must help run Verace itself.
4. The runtime owns state, evidence, approvals, receipts, and policy.
5. The assistant layer owns persona, channel UX, and founder-specific workflow.
6. No completion claim is allowed without receipt.
7. No implementation work begins without a bounded brief and acceptance criteria.

Once accepted, this ADR should be changed only by founder-level architecture decision, not by routine implementation drift.

---

## 15. References

- ADR-TR002: Verace as Trust Runtime for AI Work.
- PLAN-TR001: Verace Work Plan — From Founder Assistant to Trust Runtime.
- ADR-ASSISTANT-CORE-001: Thin Provider-Independent Assistant Runtime.
- Verace Technical Reference Manual v6.3.

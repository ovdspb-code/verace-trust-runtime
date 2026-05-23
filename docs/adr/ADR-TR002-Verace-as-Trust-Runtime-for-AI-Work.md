# ADR-TR002: Verace as Trust Runtime for AI Work

**Status:** Accepted v1.0
**Date:** 2026-05-23
**Ratified:** 2026-05-23 by Oleg Dolgikh
**Owner:** Oleg Dolgikh
**Authors:** Codex draft, final architecture review by Chief Architect
**Project:** Verace — Trust Runtime
**Scope:** Platform strategy, product hierarchy, strategic invariants
**Related:** ADR-TR001 / Assistant Core foundation, Verace TruthOps ADRs, Verace TRM v6.3

---

## 1. Decision

Verace remains the platform and company umbrella.

The existing TruthOps work becomes the first product line:

> **Verace Truth** — determines what knowledge is safe for people, AI systems, and agents to use.

The new Assistant / Mandate Core direction becomes part of the broader runtime:

> **Verace Mandate / Verace Runtime** — turns human delegation into governed, evidence-backed AI-mediated work.

The shared kernel is not chat, RAG, workflow orchestration, multi-agent coordination, or provider routing.

The shared kernel is:

* claims;
* mandates;
* contours;
* policy;
* approvals;
* receipts;
* ledger;
* Codex / evidence snapshots;
* dispositions.

Strategic category:

> **Trust Runtime for AI Work**

Strategic formula:

> **Verace makes AI work verifiable.**

Architectural formulation:

> **Verace is the trust runtime between human intent, AI agents, knowledge, tools, and proof.**

---

## 2. Why This Decision Exists

Verace began with a knowledge problem:

> Can AI safely trust this knowledge?

The next phase exposes the adjacent action problem:

> Can a human safely trust this AI-mediated work?

These are the same class of problem at different layers.

When AI only answers, contradictory or stale knowledge produces bad output. When AI acts, the same uncertainty becomes operational, legal, financial, reputational, or security risk.

Therefore Verace must not remain only a conflict detector or RAG hygiene layer. Those remain valuable, but they are the first wedge of a larger platform: a runtime that governs what AI knows, what AI is allowed to do, what it actually did, and what evidence proves it.

This ADR does not approve a production migration. It defines the strategic umbrella and the non-negotiable invariants under which later technical ADRs must operate.

---

## 3. Product Hierarchy

Adopt the following hierarchy:

```text
Verace Platform
  ├── Verace Truth
  │   └── knowledge claims, conflicts, Truth Score, Truth Codex
  │
  ├── Verace Mandate
  │   └── human delegation, contours, policy, approvals, authority boundaries
  │
  ├── Verace Ledger / Verace Codex
  │   └── claims, receipts, actions, decisions, evidence snapshots
  │
  ├── Verace Gateway
  │   └── future tool, agent, payment, credential, and protocol boundaries
  │
  └── Interfaces
      └── Porthos, Vera, chat, web, email, API, and future agent surfaces
```

`Porthos` is the first living deployment and canary. It is not the architecture.

`Vera` may become the operator and review interface. It is not the platform.

`Verace Truth` is not legacy. It remains the first commercial wedge and one of the core product lines.

`Verace Runtime` is the trust substrate beneath all of them.

---

## 4. Core Doctrine

The central operational chain is:

```text
mandate → policy → action → receipt → claim → ledger → review/audit
```

The LLM is a replaceable cognitive engine. It may draft, classify, infer, summarize, plan, and explain.

The LLM does not own:

* truth;
* identity;
* permissions;
* approvals;
* task state;
* delivery truth;
* action completion;
* durable memory;
* audit state.

Operational truth comes from explicit mandates, policy decisions, durable ledger state, human approvals, tool receipts, and signed or reproducible evidence.

---

## 5. Non-Negotiable Invariants

1. **No receipt, no success claim.**
   If the system cannot produce evidence of completion, it cannot claim completion.

2. **State is not in the model.**
   Tasks, deadlines, approvals, permissions, delivery state, and identity live in the runtime ledger, not in prompts or chat history.

3. **No LLM verdict overrides authorized human ground truth.**
   LLM disagreement creates diagnostic backlog, not truth replacement.

4. **Uncertain means review.**
   Unresolved uncertainty routes to review, approval, clarification, or explicit failure. It does not become confident output.

5. **Approval gates protect irreversible or risky action.**
   Money, legal commitments, external sending, sensitive data, irreversible operations, and customer-visible obligations require human approval unless an explicit mandate says otherwise.

6. **Core first, intelligence second.**
   Ledger, state machine, receipts, approvals, outbox, recovery, and tests precede agentic sophistication.

7. **Provider independence is mandatory.**
   Models and providers are adapters. The strategic asset is model-independent mandate, policy, ledger, receipt, and Codex state.

8. **Lightweight, boring, durable.**
   Prefer small durable primitives over orchestration theater. Introduce heavy infrastructure only when the operational need is proven.

9. **Interfaces are not the core.**
   Telegram, web, email, ChatGPT apps, APIs, and external agents are channels. The trust boundary is the contour and the ledger.

10. **Every inbound message ends somewhere.**
    Each message produces an answer, acknowledgement, clarification, status, review route, approval request, or explicit failure. Silent swallowing is a production bug.

---

## 6. Strategic Vocabulary

These are strategic concepts, not final database tables.

**Contour**
A bounded zone of trust, visibility, policy, tools, and memory. A chat is a transport surface. A contour is the durable trust boundary.

**Mandate**
A formalized human delegation: who delegated, to whom, in which contour, for what purpose, with which permissions, limits, evidence requirements, and expiry conditions.

**Claim**
An assertion about knowledge, work, state, intent, or action. Claims are not automatically true. They require disposition and, when relevant, evidence.

**Policy**
The rule layer that decides whether an action is allowed, blocked, reviewable, or requires approval.

**Approval**
A human authorization for a risky or consequential action. Approval is not the same as review: review resolves uncertainty; approval grants permission.

**Receipt**
Evidence that a tool, channel, provider, or external system produced a verifiable result.

**Ledger**
The durable record of messages, mandates, tasks, policy decisions, approvals, actions, receipts, failures, claims, and review outcomes.

**Codex**
The signed or reproducible evidence layer that makes selected knowledge, decisions, mandates, and actions durable, inspectable, and auditable.

**Disposition**
The decision state assigned to a claim, conflict, mandate, or action: for example allowed, blocked, needs approval, needs review, verified, failed, expired, superseded, or suppressed.

---

## 7. Relationship to Existing Verace TruthOps

Existing Verace TruthOps work carries forward as a first-class product line.

The following principles are inherited directly:

* claim-first thinking;
* Assertion Register vs governed truth separation;
* human-approved truth records;
* TruthKey / TruthRecord / TruthSnapshot direction;
* Truth Codex as signed artifact, not mere output;
* authority-frame thinking;
* disposition routing;
* review-only as a safe state;
* cross-platform neutrality;
* narrow public surfaces;
* deterministic pipeline discipline;
* no automatic overwrite of human ground truth.

What changes is the scope.

Old Verace TruthOps governs whether knowledge is safe to use.

New Verace Runtime also governs whether delegated AI work is authorized, executed, evidenced, and auditable.

---

## 8. Strategic Consequences

1. **Verace must not be positioned as merely an assistant.**
   Assistants are interfaces. Verace is the trust substrate.

2. **Verace Truth must not be discarded.**
   It remains the concrete enterprise wedge and the knowledge-verification arm of the platform.

3. **The runtime must stay independent from any one model, channel, or protocol.**
   Claude, OpenAI, Gemini, Kimi, local models, future providers, Telegram, email, web, MCP-like tools, A2A-like agents, AP2-like payment rails, and verifiable credentials are all adapters or future ports, not the center.

4. **The lightweight runtime must not mechanically import the existing TruthOps backend.**
   Shared contracts come first. Deep integration comes only through explicit boundaries.

5. **Every future product line must attach to the same kernel.**
   If a product cannot be expressed through mandates, claims, policy, receipts, ledger, and Codex, it is probably outside Verace or needs a separate ADR.

6. **This ADR is intentionally implementation-light.**
   Schema names, repository shape, providers, protocols, deployment topology, and storage engines are lower-level decisions. Changing them does not require changing this ADR unless an invariant is broken.

---

## 9. Non-Goals

This ADR does not approve building:

* a generic multi-agent framework;
* an OpenClaw / Hermes / LangGraph clone;
* a Telegram-only assistant product;
* a visual workflow builder;
* a prompt, plugin, or agent marketplace;
* a vendor-specific AI router as the core product;
* payment execution as an immediate capability;
* a mechanical merger of existing Verace backend code into the new runtime;
* enterprise governance theater without receipts and auditability.

---

## 10. Strategic Moat

The defensible asset is not a model, prompt, UI, connector, or single algorithm.

The defensible asset is the accumulated trust state:

* cross-platform neutrality;
* verified operational graph;
* history of claims, mandates, approvals, receipts, and dispositions;
* customer-specific ground truth;
* policy and contour configuration;
* signed Codex artifacts;
* review and audit trail;
* low portability of operational accountability.

Over time, Verace should become the layer that knows what was delegated, what was allowed, what was known, what was done, what was proven, and what still needs human judgment.

---

## 11. Risk Posture

| Risk                      | Strategic mitigation                                                              |
| ------------------------- | --------------------------------------------------------------------------------- |
| Scope explosion           | Keep the first wedge narrow: Verace Truth + lightweight runtime + Porthos canary. |
| Brand dilution            | Verace is the trust substrate; Porthos and Vera are interfaces.                   |
| Overweight architecture   | Shared contracts and ports before backend integration.                            |
| False completion claims   | Enforce “No receipt, no success claim.”                                           |
| Model/provider drift      | Keep state, policy, identity, and approvals outside the model.                    |
| Cross-contour leakage     | Treat contours as durable trust boundaries.                                       |
| Protocol cargo cult       | Future protocols shape boundaries but do not define the MVP.                      |
| TruthOps roadmap conflict | Verace Truth remains a product line, not obsolete history.                        |

---

## 12. Ratification Criteria

This ADR is accepted when Oleg confirms that:

1. Verace remains the umbrella platform and brand.
2. The top-level category is **Trust Runtime for AI Work**.
3. The strategic formula is **Verace makes AI work verifiable**.
4. Existing TruthOps work becomes **Verace Truth**.
5. Assistant / Mandate Core work becomes part of **Verace Runtime / Verace Mandate**.
6. `mandate → policy → action → receipt → claim → ledger → review/audit` is the governing architectural chain.
7. “No receipt, no success claim” is binding.
8. Lower-level implementation ADRs must comply with this ADR rather than re-litigate the umbrella strategy.

Once accepted, this ADR should be changed only by a founder-level strategy ADR, not by routine implementation deltas.

---

## 13. References

* ADR-TR001 / Assistant Core foundation draft.
* ADR-022: Warrant-Based Codex Model.
* ADR-031: Authority Frame and Finding Disposition.
* ADR-033: Black Box Unit Pattern.
* ADR-034: API Trust Boundary Pattern.
* ADR-036: FactKey Architecture.
* Verace Technical Reference Manual v6.3.
* Verace investor/product materials defining TruthOps, cross-platform neutrality, and Truth Codex.

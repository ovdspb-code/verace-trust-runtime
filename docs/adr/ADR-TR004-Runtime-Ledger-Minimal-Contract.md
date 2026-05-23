# ADR-TR004: Runtime Ledger Minimal Contract

**Status:** Accepted v1.0  
**Date:** 2026-05-23  
**Ratified:** 2026-05-23 by Oleg Dolgikh  
**Owner:** Oleg Dolgikh  
**Project:** Verace — Trust Runtime  
**Scope:** Durable runtime state contract, ledger boundaries, minimum operational truth model  
**Governing ADRs:** ADR-TR002, ADR-TR003  
**Governing Plan:** PLAN-TR001  

---

## 1. Decision

Verace Runtime will use a durable **Runtime Ledger** as the operational source of truth for AI-mediated work.

The ledger is not a chat transcript, not model memory, not a workflow engine, and not a product UI. It is the minimum durable record that allows Verace to answer:

- who delegated;
- in which contour;
- under what mandate;
- what task was opened;
- what messages and artifacts belong to it;
- what policy or approval applied;
- what action was attempted;
- what receipt proves the result;
- what claim may safely be made;
- what remains unresolved, blocked, failed, or reviewable.

The first implementation may use a simple local database. The strategic contract is storage-independent: any future implementation must preserve the same trust semantics even if the database, deployment model, provider, channel, or UI changes.

The minimal chain remains:

```text
mandate → policy → action → receipt → claim → ledger → review/audit
```

---

## 2. Why This ADR Exists

ADR-TR002 defines Verace as the trust runtime between human intent, AI agents, knowledge, tools, and proof.

ADR-TR003 defines Oleg’s founder assistant as the first runtime canary.

This ADR defines the first durable state contract beneath that assistant.

Without a ledger, the assistant is only a conversation. With a ledger, it becomes the first operational surface of Verace Runtime.

The purpose of this ADR is to prevent three failure modes:

1. **Model-held state** — tasks, approvals, and delivery truth living only in prompt/session history.
2. **False completion** — AI claiming that something was done without evidence.
3. **Context bleed** — messages, tasks, memory, and permissions leaking across contours.

---

## 3. Ledger Doctrine

The Runtime Ledger owns operational truth.

The LLM may propose, classify, summarize, draft, and explain. It may not become the source of durable state.

The ledger must make the following statements reconstructable without relying on model memory:

```text
This principal delegated this mandate in this contour.
This task belongs to that mandate.
This message or artifact belongs to that task or contour.
This action was allowed, blocked, approved, failed, or completed.
This receipt proves, or fails to prove, the action.
This claim is therefore verified, unverified, blocked, failed, or needs review.
```

The ledger should behave more like accounting than conversation.

---

## 4. Minimal Ledger Objects

These are strategic object contracts, not final table names.

### 4.1 Principal / Person

A human or system actor known to the runtime.

At minimum, the ledger must distinguish:

- Oleg as principal/founder;
- other humans who may appear in future contours;
- the assistant/runtime identity;
- external systems or tools that produce receipts.

### 4.2 Contour

A bounded zone of trust, visibility, permissions, tools, and memory.

Examples:

- Oleg private;
- Verace project;
- family/office;
- finance/legal;
- investor;
- client/pilot.

A channel is not a contour. A Telegram chat, email thread, web session, or API call is a transport surface. The contour is the durable trust boundary.

### 4.3 Mandate

A human delegation with authority boundaries.

A mandate records what the runtime is allowed to do, for whom, in which contour, with what limits, and with what evidence requirements.

A mandate may be explicit or implicit:

- **explicit mandate:** a clear instruction to do work;
- **implicit low-risk mandate:** local note-taking, summarization, draft preparation, or task capture inside the active contour;
- **not a mandate:** external sending, payment, legal commitment, irreversible action, or sensitive-data disclosure without approval.

### 4.4 Task

An operational unit of work created under a mandate or low-risk interaction.

A task is not the same as a mandate. A mandate grants authority; a task tracks work.

A task must be reconstructable after restart and must not depend on chat history alone.

### 4.5 Message

A durable record of inbound and outbound communication.

Messages are input evidence and delivery history. They are not sufficient operational state by themselves.

### 4.6 Event

An append-first record of a meaningful state transition.

Examples:

- task created;
- task classified;
- follow-up attached;
- mandate created;
- approval requested;
- approval granted or denied;
- action attempted;
- receipt recorded;
- claim verified;
- task completed;
- task failed;
- review requested.

Events are how the ledger explains how state changed.

### 4.7 Approval

A human authorization for risky or consequential action.

Approval is not the same as review. Review resolves uncertainty. Approval grants permission.

Approvals must be explicit, durable, scoped, and tied to the relevant mandate, task, action, or claim.

### 4.8 Receipt

Evidence that a tool, channel, or external system produced a result.

Receipts may prove success or failure. A failure receipt is still useful evidence.

Receipt examples:

- file created with path and checksum;
- document updated with version/hash;
- message drafted with draft id;
- message sent with provider/channel id;
- calendar event created with event id;
- tool failed with structured error;
- approval recorded with actor and timestamp.

### 4.9 Claim

An assertion about knowledge, state, work, or action.

A claim may be produced by a user, model, tool, connector, runtime component, or external agent. It is not automatically true.

Action claims that imply completion require receipts.

### 4.10 Outbox Item

A planned user-visible or external delivery.

The outbox exists to avoid silent swallowing and duplicate delivery. It tracks what should be sent, what was sent, what failed, and what is awaiting approval.

### 4.11 Attachment / Artifact

A file, document, image, dataset, or generated artifact known to the runtime.

Artifacts must be linked to their source, contour, task, and receipts where relevant.

### 4.12 Scheduled Wakeup

A durable reminder or future work trigger.

The scheduler may be simple. The wakeup record must survive restart.

### 4.13 Evidence Snapshot / Codex Candidate

A durable bundle of selected claims, receipts, approvals, and decisions that may later become part of Verace Codex.

Not every ledger entry is a Codex artifact. The ledger is operational memory; the Codex is the curated/auditable evidence layer.

---

## 5. Minimum Relationship Contract

The first ledger must support these relationships:

```text
person → contour membership
contour → mandate
mandate → task
task → messages
task → events
task → approvals
task → receipts
task → claims
task → outbox items
claim → required receipt when applicable
claim → receipt when verified
approval → mandate/task/action scope
receipt → action/tool/channel/provider result
artifact → task/receipt/source
scheduled wakeup → task/mandate/contour
```

The implementation may optimize or denormalize this structure, but it must not erase these relationships semantically.

---

## 6. State and Disposition Contract

The ledger must avoid vague single-status buckets.

At minimum, it must distinguish:

### 6.1 Task state

```text
open
in_progress
waiting_for_user
waiting_for_approval
waiting_for_external
blocked
completed
failed
cancelled
superseded
```

### 6.2 Mandate state

```text
active
paused
fulfilled
revoked
expired
superseded
closed
```

### 6.3 Claim disposition

```text
proposed
requires_receipt
verified
rejected
needs_review
blocked
failed
suppressed
superseded
```

### 6.4 Action disposition

```text
allowed
blocked
needs_approval
needs_review
attempted
succeeded
failed
expired
superseded
```

### 6.5 Outbox state

```text
pending
waiting_approval
delivered
failed
cancelled
suppressed
```

Exact enum names may change in implementation ADRs, but the distinctions must survive.

---

## 7. Non-Negotiable Ledger Invariants

1. **No receipt, no success claim.**  
   A completed external action, file delivery, upload, send, or irreversible state change may not be claimed without a receipt.

2. **State is not in the model.**  
   The model may read selected state. It does not own state.

3. **Every inbound message ends somewhere.**  
   The ledger must record whether the message produced an answer, acknowledgement, clarification, task, approval request, review route, status, outbox item, or explicit failure.

4. **Contours are durable trust boundaries.**  
   Messages, tasks, artifacts, approvals, and memory must be bound to contours.

5. **Append-first history.**  
   Important state transitions must leave an event trail. Current state may be materialized, but history cannot disappear silently.

6. **Idempotent ingress.**  
   Duplicate channel updates must not create duplicate tasks, actions, receipts, or sends.

7. **Idempotent delivery.**  
   Retrying outbox delivery must not create duplicate external effects without an explicit duplicate-safe receipt model.

8. **Approval is scoped.**  
   An approval must specify what it authorizes. A broad approval cannot be silently reused for unrelated actions.

9. **Failure is first-class.**  
   Tool failure, provider failure, validation failure, policy block, and user denial must be recorded explicitly.

10. **Diagnostics are not user UX.**  
    The ledger may store technical metadata, but normal user-facing messages must not expose internal machinery unless requested by the principal.

---

## 8. What The Ledger Does Not Decide

The ledger does not decide:

- final product UX;
- assistant persona;
- LLM provider choice;
- prompt strategy;
- external protocol choice;
- TruthOps pipeline implementation;
- payment execution;
- enterprise deployment topology;
- final database engine.

Those are separate ADRs or implementation briefs.

The ledger only defines the operational truth boundary that those layers must respect.

---

## 9. First Implementation Posture

The first implementation should be boring.

Acceptable first posture:

```text
local durable store
single-writer discipline
append-first events
simple materialized current state
explicit outbox
basic receipt registry
restart recovery test
no hidden autonomous background work
```

The first implementation should optimize for correctness and inspectability, not scale theater.

Scaling, distributed workflow orchestration, protocol gateways, enterprise audit exports, and full Codex signing are later concerns.

---

## 10. Relationship to Verace Truth

Verace Truth remains the knowledge-verification product line.

The Runtime Ledger should not import the existing Verace Truth backend as a hard dependency.

The connection is conceptual and eventually contractual:

```text
ledger claim → TruthCheck boundary → assessment/disposition → ledger event/claim update
```

The ledger must be able to store knowledge-sensitive claims and their disposition, but it must not require the full Truth pipeline for basic assistant operation.

---

## 11. Relationship to Verace Codex

The Runtime Ledger and Verace Codex are related but not identical.

```text
Runtime Ledger = operational memory of work
Verace Codex  = curated/auditable evidence layer
```

A ledger may contain noisy, transient, failed, or low-value operational entries.

A Codex artifact should contain selected, structured, signed or reproducible evidence that is worth preserving for audit, trust, review, or external proof.

The first runtime should make future Codex extraction possible, but it does not need full Codex signing in MVP.

---

## 12. Acceptance Criteria For This ADR

This ADR is accepted when Oleg confirms that:

1. Runtime Ledger is the operational source of truth for the first assistant.
2. The ledger contract covers at least contours, mandates, tasks, messages, events, approvals, receipts, claims, artifacts, outbox, and scheduled wakeups.
3. The ledger is storage-independent at strategy level.
4. The first implementation may be simple and local if it preserves the contract.
5. Chat history and LLM memory are explicitly not state.
6. Every external success claim requires a receipt.
7. Contour isolation is a hard boundary from the first runtime implementation.
8. Detailed schema, migrations, package layout, and tests are delegated to implementation briefs or lower-level ADRs.

---

## 13. Consequences

### Positive

- Founder Assistant can become a real runtime canary instead of a chatbot.
- Restart recovery becomes testable.
- Codex work can be tracked through tasks, events, receipts, and claims.
- Future multi-contour work has a clean boundary.
- Verace Truth integration has a place to attach without monolithic coupling.
- “No receipt, no success claim” becomes enforceable in code, not just a slogan.

### Negative / Cost

- Even the first assistant needs more structure than a simple chat wrapper.
- Some UX shortcuts must be rejected if they bypass the ledger.
- Codex tasks must produce operational receipts, not just prose reports.
- Early velocity may look slower than a naive bot, but failure modes become visible.

### Risk Controls

- Keep first implementation minimal.
- Do not implement full enterprise schema.
- Do not import old Verace backend.
- Do not add external protocols yet.
- Keep every implementation brief bounded and testable.

---

## 14. Non-Goals

This ADR does not approve:

- production database schema;
- ORM choice;
- migration framework;
- provider adapter implementation;
- Telegram integration;
- Verace Truth backend integration;
- full Codex signing;
- distributed workflow orchestration;
- multi-agent framework;
- payment/legal execution;
- external customer deployment.

---

## 15. Next ADR

The next ADR should be:

```text
ADR-TR005: Receipt and Approval Policy
```

It should define which action classes require receipt, approval, review, block, or explicit failure.

After ADR-TR005, the project can produce the first bounded implementation brief:

```text
BRIEF-TR001: Founder Assistant MVP — Ledger Seed
```

---

## 16. References

- ADR-TR002: Verace as Trust Runtime for AI Work.
- ADR-TR003: Founder Assistant as First Runtime Canary.
- PLAN-TR001: Verace Work Plan — From Founder Assistant to Trust Runtime.
- ADR-ASSISTANT-CORE-001: Thin Provider-Independent Assistant Runtime.
- Verace TRM v6.3, especially claim/disposition discipline and current-state caveats.

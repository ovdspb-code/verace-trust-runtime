# ADR-TR005: Receipt and Approval Policy

**Status:** Proposed v1.0  
**Date:** 2026-05-23  
**Owner:** Oleg Dolgikh  
**Project:** Verace — Trust Runtime  
**Scope:** Policy doctrine for receipts, approvals, review, blocks, and safe claims  
**Governing ADRs:** ADR-TR002, ADR-TR003, ADR-TR004  
**Governing Plan:** PLAN-TR001  

---

## 1. Decision

Verace Runtime will enforce a minimal **Receipt and Approval Policy** before the first Founder Assistant implementation begins.

The policy determines whether a proposed action is:

```text
allowed
allowed_with_receipt
needs_approval
needs_review
blocked
```

and whether the system may later make a claim about the result.

The policy is not a final authorization engine, not a compliance framework, and not a workflow language. It is the first trust contract that prevents the assistant from turning helpful intent into unsafe action.

The governing rule remains:

```text
No receipt, no success claim.
```

A second rule is added:

```text
No mandate or approval, no consequential external action.
```

The runtime may draft, prepare, classify, summarize, and record low-risk work inside the active contour. It may not send, publish, pay, commit externally, disclose sensitive data, create obligations, or make irreversible changes unless policy and approval allow it and a receipt records the result.

---

## 2. Why This ADR Exists

ADR-TR004 defines the Runtime Ledger as the operational source of truth.

A ledger without policy can record what happened, but it does not prevent unsafe work.

This ADR defines the first policy boundary beneath the Founder Assistant:

```text
mandate → policy → action → receipt → claim → ledger → review/audit
```

The policy must prevent five early failure modes:

1. **False completion** — claiming work was done without evidence.
2. **Unsafe external action** — sending, sharing, publishing, or committing without approval.
3. **Permission drift** — treating a narrow instruction as broad authority.
4. **Review/approval confusion** — using human review of uncertainty as permission to act.
5. **Silent failure** — hiding blocks, denials, tool failures, or ambiguous state behind fluent text.

---

## 3. Core Doctrine

### 3.1 Approval is not review

**Approval** grants permission for a risky or consequential action.

**Review** resolves uncertainty about meaning, scope, identity, sensitivity, or truth.

A reviewed claim is not automatically approved for action. An approved action is not automatically a verified truth claim.

### 3.2 Receipts prove attempts and results

A receipt may prove success or failure.

A failure receipt is still valuable because it prevents the model from inventing completion.

The runtime must distinguish:

```text
action requested
action allowed
action approved
action attempted
action succeeded
action failed
action blocked
action needs review
```

### 3.3 Externality raises the risk level

Any action that changes state outside the active private runtime contour is higher risk.

External actions include sending, publishing, uploading to shared locations, changing calendars, opening pull requests, pushing commits, sending email, creating tickets, calling third-party APIs, or exposing data to another person or system.

### 3.4 Consequence overrides convenience

If an action is legally, financially, reputationally, security, privacy, or customer consequential, it requires approval or is blocked, even if the user wording sounds casual.

### 3.5 Uncertainty fails safe

If the runtime cannot determine the contour, mandate, recipient, data sensitivity, action target, or required evidence, the action must route to review, clarification, approval, or block.

It must not proceed by optimistic inference.

---

## 4. Policy Inputs

Before action execution, the runtime should evaluate at least these inputs:

- active contour;
- principal / actor;
- mandate or task;
- requested action;
- target system or recipient;
- data/artifact sensitivity;
- reversibility;
- externality;
- money/legal/customer impact;
- existing approval, if any;
- required receipt class;
- claim the assistant intends to make after execution.

The first implementation may use simple deterministic rules. The strategic contract is that policy is evaluated outside the model and recorded in the ledger.

---

## 5. Action Classes

These are strategic action classes, not final enum names.

| Class | Examples | Default policy |
|---|---|---|
| **Internal conversation** | answer, clarify, status, explanation | Allowed; ledger event required |
| **Task / note capture** | create task, attach follow-up, record decision candidate | Allowed inside active contour; ledger event required |
| **Drafting** | draft ADR, memo, email text, Codex brief | Allowed; artifact receipt required if saved as file |
| **Local/private artifact creation** | create local markdown/doc, generate summary pack | Allowed with receipt |
| **Read-only retrieval** | read project docs, query ledger, inspect repo files | Allowed if contour permits; receipt/event for consequential reads |
| **Tool execution without external effect** | format file, compute checksum, run local test | Allowed with receipt |
| **Repo mutation** | edit tracked file, commit, branch, push, PR | Requires accepted brief or explicit approval; receipt required |
| **External share/send/publish** | email send, message send, public upload, shared Drive link | Requires approval and receipt |
| **Calendar or commitment creation** | create meeting, accept invitation, promise delivery | Requires approval and receipt |
| **Sensitive data disclosure** | personal, financial, legal, credentials, private docs | Requires approval; may be blocked depending on target |
| **Money movement** | payment, refund, invoice payment, purchase | Blocked in MVP; future ADR required |
| **Legal commitment** | contract acceptance, legal notice, binding representation | Blocked in MVP; future ADR required |
| **Destructive/irreversible action** | delete data, revoke access, overwrite source of record | Blocked in MVP unless a later ADR defines safe handling |
| **External autonomous agent delegation** | asking another agent/system to act externally | Blocked in MVP; future Gateway ADR required |

---

## 6. Receipt Requirements

Every receipt must answer, at minimum:

```text
what action was attempted
who/what performed it
under which contour / mandate / task
when it happened
what target it affected
what result occurred
what evidence proves the result
whether the receipt proves success, failure, or partial completion
```

### 6.1 Minimum receipt classes

The first runtime should support these receipt classes conceptually:

- `ledger.event` — internal state change recorded;
- `artifact.created` — file or artifact created with path/reference and digest where possible;
- `artifact.updated` — artifact changed with version/digest where possible;
- `tool.succeeded` — local or remote tool succeeded;
- `tool.failed` — tool failed with structured error;
- `message.drafted` — outbound message draft created;
- `message.sent` — outbound message sent with channel/provider id;
- `repo.changed` — repository file changed;
- `repo.committed` — commit hash recorded;
- `repo.pushed` — remote/branch push recorded;
- `approval.granted` — scoped human approval recorded;
- `approval.denied` — human denial recorded;
- `policy.blocked` — policy blocked action;
- `review.requested` — uncertainty routed to review;
- `claim.verified` — claim tied to sufficient evidence;
- `claim.rejected` — claim rejected or unsupported.

Exact names may change. The distinctions must survive.

### 6.2 Receipt quality

A weak receipt may prove that an attempt happened but not that the intended outcome succeeded.

Examples:

- a tool call log may prove attempt, not delivery;
- a local file path may prove local creation, not external upload;
- a draft id may prove draft creation, not sending;
- a git commit hash may prove local commit, not push;
- a push receipt may prove branch update, not review or merge;
- a screenshot may support human review, but should not replace structured receipt when an API receipt exists.

The runtime must not promote weak receipts into stronger claims.

---

## 7. Approval Requirements

Approval must be explicit, scoped, durable, and tied to the relevant mandate, task, action, artifact, or claim.

At minimum, an approval record must answer:

```text
who approved
what exact action was approved
which target/recipient/system was approved
which data/artifact was approved
which contour and mandate apply
when approval was granted
whether approval expires
which constraints apply
```

### 7.1 Approval required

Approval is required for:

- external sending or sharing;
- public publishing;
- push or pull-request activity that changes public repository state;
- disclosure of sensitive data;
- calendar creation or modification that affects another person;
- customer/partner/investor-visible statements;
- legal, financial, or commercial commitments;
- action that may create obligation, reliance, or reputational consequence;
- any action whose contour, recipient, or authority is uncertain but potentially consequential.

### 7.2 Approval cannot be silently reused

A prior approval cannot be reused for a materially different action.

Changing any of the following requires new approval or review:

- recipient;
- external system;
- artifact content;
- scope;
- amount/value;
- legal/commercial implication;
- public/private visibility;
- contour.

### 7.3 Standing mandates

A future runtime may support standing mandates for repeated low-risk actions.

For MVP, standing mandates must not cover:

- money movement;
- legal commitments;
- external sending of sensitive data;
- destructive operations;
- autonomous external agent delegation;
- public releases.

---

## 8. Review Requirements

Review is required when the runtime cannot safely determine:

- whether a message is a new task or follow-up;
- which contour applies;
- whether the user has authority;
- whether the data is sensitive;
- whether a claim is verified or conflicting;
- whether a receipt proves the intended result;
- whether an action is reversible;
- whether a source is current or superseded;
- whether an instruction conflicts with an existing mandate, policy, or founder ground truth.

Review may produce one of several outcomes:

```text
clarify with user
request approval
block action
record uncertainty
mark claim needs_review
proceed with narrowed action
```

Review is a safe state, not a failure.

---

## 9. Claim Policy

The assistant may not make a claim stronger than the evidence allows.

### 9.1 Claims that require receipts

The following claims require receipts:

- “created a file”;
- “updated the document”;
- “uploaded”;
- “sent”;
- “scheduled”;
- “committed”;
- “pushed”;
- “tests passed”;
- “working tree is clean”;
- “external system accepted it”;
- “approval was granted”;
- “task completed” when completion depends on a tool/action;
- “issue fixed” when fix depends on code/test evidence.

### 9.2 Claims allowed without external receipts

The assistant may make conversational or draft-limited claims without external receipts when the claim is clearly bounded:

- “I can draft this.”
- “Here is a draft.”
- “I understand the instruction as…”
- “I need clarification.”
- “I do not have evidence that this was sent.”
- “Based on the current ledger…” if the ledger state is read and cited internally.

### 9.3 Negative evidence must be explicit

If there is no receipt, the assistant should say so plainly.

Correct:

```text
Draft prepared. I do not have a send receipt, so I cannot claim it was sent.
```

Incorrect:

```text
Done.
```

---

## 10. MVP Policy for Founder Assistant

The first Founder Assistant may:

- answer questions;
- capture tasks;
- attach follow-ups;
- record decision candidates;
- draft ADRs, briefs, memos, and messages;
- summarize project state from ledger/repo evidence;
- create local/private artifacts with receipts;
- prepare approval requests;
- report status, blockers, and failures.

The first Founder Assistant must not autonomously:

- send external messages;
- publish public content;
- push to GitHub;
- create or merge PRs;
- make payments;
- accept legal terms;
- disclose sensitive data;
- delete or overwrite source-of-record artifacts;
- delegate external action to another agent;
- claim delivery without a receipt.

Repo and GitHub actions are allowed only through an explicit Codex brief or direct founder instruction that states the allowed files, branch/push behavior, checks, and done definition.

---

## 11. Relationship to Codex Work

Codex execution must follow the same policy doctrine.

A Codex report is a claim set. Claims in that report need receipts.

Examples:

| Codex claim | Required receipt |
|---|---|
| “file changed” | file path + diff/status |
| “tests passed” | command and output |
| “working tree clean” | `git status` output |
| “committed” | commit hash |
| “pushed” | push output / remote ref |
| “no code files changed” | diff/name-status or file scan evidence |
| “ADR body unchanged” | diff evidence or scoped status |

Codex may propose implementation plans. Codex may not ratify strategy, expand scope, or treat its own confidence as evidence.

---

## 12. Policy Failure Handling

Policy failures must be visible enough to be useful.

The runtime should distinguish:

```text
blocked_by_policy
needs_approval
needs_review
approval_denied
tool_failed
receipt_insufficient
claim_unsupported
contour_unclear
mandate_missing
```

User-facing language may be simple, but the ledger state must preserve the actual reason.

A policy block is not an error. It is a trust-preserving outcome.

---

## 13. What This ADR Does Not Decide

This ADR does not define:

- final policy DSL;
- final database schema;
- authorization UI;
- enterprise RBAC model;
- signature model;
- secret management implementation;
- payment execution protocol;
- legal workflow engine;
- external agent gateway;
- complete data classification taxonomy;
- provider-specific tool APIs.

Those require lower-level ADRs or implementation briefs.

---

## 14. Consequences

### Positive

- The first assistant can be useful without becoming unsafe.
- Completion claims become evidence-bound.
- Review and approval stop being conflated.
- Codex work becomes more auditable.
- External action can be added later without rethinking the trust model.

### Cost

- Some apparently simple actions require explicit approval or receipt.
- Early UX may be less magical than a naive assistant.
- Implementation must include policy checks before many tool calls.
- Reports must be evidence-aware, not merely fluent.

### Risk controls

- Keep MVP policy deterministic and small.
- Default-deny external effects.
- Treat uncertainty as review.
- Treat failure receipts as first-class.
- Require lower-level ADRs before money, legal, destructive, or external-agent actions.

---

## 15. Acceptance Criteria For This ADR

This ADR is accepted when Oleg confirms that:

1. Receipt and Approval Policy is required before Founder Assistant implementation.
2. External, consequential, sensitive, financial, legal, destructive, or public actions require approval or are blocked in MVP.
3. Receipts may prove success or failure, and both must be ledgered.
4. Approval and review are separate concepts.
5. The assistant may not claim external completion without sufficient receipt.
6. The first Founder Assistant is limited to low-risk internal work, drafting, task capture, ledgered artifacts, status, and approval requests.
7. Repo/GitHub mutations require explicit brief or direct founder approval.
8. Detailed policy schema, DSL, and implementation mechanics are delegated to implementation briefs or lower-level ADRs.

---

## 16. Next Document

After this ADR is accepted, the project may proceed to the first implementation brief:

```text
BRIEF-TR001: Founder Assistant MVP — Ledger Seed
```

That brief should implement the smallest working slice of the Founder Assistant without adding unsafe external action.

---

## 17. References

- ADR-TR002: Verace as Trust Runtime for AI Work.
- ADR-TR003: Founder Assistant as First Runtime Canary.
- ADR-TR004: Runtime Ledger Minimal Contract.
- PLAN-TR001: Verace Work Plan — From Founder Assistant to Trust Runtime.
- SESSION_PROTOCOL: Brief → Preflight → Implementation plan → Approval → Execution → Checks → Report → Review.

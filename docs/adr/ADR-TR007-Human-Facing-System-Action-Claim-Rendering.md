# ADR-TR007: Human-Facing System-Action Claim Rendering

**Status:** Accepted v1.0  
**Ratified:** 2026-05-24 by Oleg Dolgikh  
**Date:** 2026-05-24  
**Owner:** Oleg Dolgikh  
**Project:** Verace — Trust Runtime  
**Scope:** User-visible statements about Verace Runtime actions, receipt-derived prose, channel/LLM response boundary  
**Governing ADRs:** ADR-TR002, ADR-TR004, ADR-TR005, ADR-TR006  
**Related governance:** FAILURE_CLASS_CLOSURE, Session Protocol, Porthos patch-vs-class-closure memo  

---

## 1. Decision

Verace Runtime must not allow free-form model prose to make factual claims about the system's own actions.

Any human-facing factual statement about a Verace-controlled action must be either:

1. rendered from ledger / receipt / claim / task / artifact fields; or
2. validated as entailed by those fields; or
3. downgraded, repaired, clarified, or failed closed.

This applies to statements such as:

```text
created
generated
rendered
attached
uploaded
sent
scheduled
extracted
checked
pushed
merged
delivered
```

The LLM may draft tone, style, explanation, and non-operational prose.  
The LLM may not invent operational facts.

Strategic invariant:

```text
No receipt-rendered prose, no system-action statement.
```

This extends, but does not replace:

```text
No receipt, no success claim.
No class closure, no fix accepted.
```

---

## 2. Why This Decision Exists

The Porthos patch-vs-class-closure memo exposed a specific failure class: a system can possess a valid receipt while its human-facing prose states an operational fact that does not follow from that receipt.

Example class:

```text
Delivered artifact = DOCX
Human-facing prose = "PDF prepared"
```

This is not the same as a missing receipt. It is a mismatch between evidence-backed state and user-visible action prose.

The current Verace Runtime already governs ledger, tasks, decisions, reviews, schema, doctor checks, receipts, claims, and review lifecycle. Before adding channel or LLM response layers, the runtime needs a strict rendering boundary for system-action statements.

The core chain remains:

```text
mandate → policy → action → receipt → claim → ledger → review/audit
```

ADR-TR007 adds the final user-facing step:

```text
ledger / receipt / claim → allowed visible claim → receipt-rendered prose
```

---

## 3. Core Doctrine

A system-action statement is a factual statement to a human about an action the system performed, attempted, blocked, scheduled, checked, generated, delivered, or failed.

Such statements must be grounded in runtime state.

Allowed:

```text
Task TR-000001 was recorded.
Receipt: RCPT-...
```

Allowed if receipt fields support it:

```text
DOCX prepared: letter.docx.
```

Not allowed:

```text
PDF prepared.
```

when the underlying receipt or artifact metadata says `docx`.

Not allowed:

```text
File sent.
```

when the runtime only has a draft receipt.

Not allowed:

```text
Tests passed.
```

when no test command receipt exists.

---

## 4. Required Rendering Boundary

Future assistant / channel / LLM response code must include a rendering boundary. The exact implementation name is lower-level detail, but the conceptual boundary is:

```text
ResponseClaimRenderer
```

or equivalent.

Inputs should include, as relevant:

```text
receipts
claims
tasks
review items
decisions
artifacts
delivery state
policy results
doctor/schema state
```

Outputs must be constrained to:

```text
visible statements that follow from runtime state
```

The renderer may produce templates, structured text, or validated prose. The implementation may be deterministic at first.

---

## 5. Allowed Claim Classes

The runtime may expose these classes only when backed by corresponding state.

| Human-facing class | Required backing |
|---|---|
| task recorded | task row + task creation receipt / claim |
| decision recorded | decision row + decision receipt / claim |
| review created | review item + creation event + receipt + claim |
| review resolved/dismissed | review status + lifecycle event + receipt + claim |
| schema healthy | doctor/schema state |
| file/artifact created | artifact receipt with format/name/path/checksum as applicable |
| external send completed | external-send receipt |
| GitHub pushed/merged | git/GitHub receipt |
| tests passed | command/check receipt |
| blocked action | policy decision + blocked receipt / claim |

If required backing is absent, the statement must not be emitted as fact.

---

## 6. Failure Behavior

If a proposed response contains a system-action statement that is not supported by runtime state, the runtime must do one of:

1. repair the statement from receipt fields;
2. downgrade to a non-completion statement;
3. ask for clarification;
4. route to review;
5. emit explicit failure.

Examples:

```text
Cannot claim file was sent: only a draft receipt exists.
```

```text
Prepared DOCX, not PDF: receipt RCPT-... shows format=docx.
```

```text
Action blocked by policy: external.send requires approval.
```

Silent correction by model-only paraphrase is not sufficient.

---

## 7. Relationship to Existing Invariants

### ADR-TR002

ADR-TR002 defines Verace as the trust runtime between human intent, AI agents, knowledge, tools, and proof. It states that LLMs do not own truth, permissions, task state, delivery truth, action completion, durable memory, or audit state.

ADR-TR007 applies the same rule to user-visible system-action prose.

### ADR-TR005

ADR-TR005 defines receipt and approval policy.

ADR-TR007 constrains how receipt-backed state may be stated to users.

### FAILURE_CLASS_CLOSURE

Failure-Class Closure governance requires fixes to close the class, not only the demonstrated case.

ADR-TR007 closes a known class:

```text
human-facing system-action prose diverges from receipt-backed state
```

---

## 8. Non-Goals

This ADR does not approve:

- Telegram integration;
- LLM provider integration;
- response generation architecture in full;
- arbitrary natural-language truth validation;
- validation of all world claims;
- Verace Truth integration;
- external sending;
- artifact pipeline implementation;
- approval execution;
- GitHub automation by runtime.

This ADR governs the boundary that future response/channel work must satisfy.

---

## 9. Implementation Direction

The first implementation should be small and deterministic.

Recommended future brief:

```text
BRIEF-TR005: Response Claim Renderer
```

It should:

- add a deterministic renderer for current runtime entities;
- render task/decision/review/session/doctor status from ledger state;
- reject or repair unsupported system-action statements;
- include parameterized tests over action type and receipt state;
- keep LLM out of the rendering path initially.

Minimum test axis:

```text
task recorded / missing receipt
decision recorded / missing claim
review created / missing lifecycle event
review resolved / missing resolution claim
schema healthy / unsafe schema
artifact format pdf/docx/txt/unknown
external send draft/sent/unknown
```

Unknown or malformed action state must fail closed.

---

## 10. Acceptance Criteria

This ADR is accepted when Oleg confirms:

1. Human-facing factual statements about Verace-controlled actions must be rendered from, or validated against, ledger/receipt/claim state.
2. LLMs may not invent operational facts in user-facing prose.
3. Unsupported system-action claims must fail closed, repair, clarify, downgrade, or route to review.
4. Future channel/LLM response work must implement this boundary before user-facing autonomy.
5. The next implementation brief should add a deterministic Response Claim Renderer or equivalent.

Once accepted, implementation briefs for channel, LLM, artifact delivery, GitHub actions, or external sending must comply with this ADR.

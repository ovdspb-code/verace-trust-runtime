# Risk Register

| Risk | Status | Mitigation |
| --- | --- | --- |
| Scope explosion | Open | Keep Phase 0 focused on operating base only; require briefs for implementation. |
| Overfitting to personal assistant | Open | Treat Founder Assistant as first canary, not final product category. |
| No git / weak operating memory | Mitigated in TR-001 | Git initialized; project state, decisions, worklog, and session protocol created. |
| False success claims | Open | Enforce "No receipt, no success claim" in briefs, reports, and runtime design. |
| Old Verace backend over-import | Open | Use shared contracts and explicit ports before any backend integration. |
| Protocol cargo cult | Open | Future protocols may shape boundaries but must not define MVP scope. |
| Architect lacks direct local filesystem access | Mitigated in TR-GH-001 | GitHub canonical repository plus commit/PR review flow. |
| Secrets leakage | Open | Keep `.env`, databases, credentials, and generated runtime state out of git; future secret scanning not configured yet. |
| Runtime DB accidentally committed | Open | `.runtime/`, `.runtime-test/`, and SQLite files are gitignored; implementation sessions must inspect git status before commit. |
| MVP mistaken for full assistant | Open | BRIEF-TR001 explicitly excludes Telegram, LLM providers, external actions, and autonomous tools. |
| File-size creep | Open | OD rule: no code file over 300 lines; target 100-200 lines. CI does not enforce this yet; implementation sessions must check line counts before commit. |
| Ledger invariant regression | Open | Doctor now checks schema, PRAGMAs, integrity, foreign keys, seed state, and receipt coverage; pytest covers broken receipt cases. |
| Project brief overclaiming | Open | Project brief is read-only and only reports ledger state already present in local DB; tests assert full status counts do not change. |
| No runtime schema migration runner | Mitigated in PR #3 | ADR-TR006 is accepted; BRIEF-TR003 added schema metadata, fail-closed inspection, schema-status, and a minimal migration runner. |
| Backup/restore policy absent | Open | ADR-TR006 governs schema safety, but backup/restore product policy remains out of scope until a future brief or ADR. |
| Review queue mistaken for approval system | Open | BRIEF-TR004 review items are human-inspection work only; approval grants and approval execution remain explicit non-goals. |
| Patch accepted as fix | Open | Every bugfix/review-fix must include Failure-Class Closure: class axis, invariant, parametric tests, fail-closed unknowns, receipt/claim boundary, and residual risk. A single green demonstrated case is not acceptance. |
| Receipt/prose mismatch for current runtime entities | Mitigated in PR #5 | BRIEF-TR005 added a deterministic Response Claim Renderer for task, decision, review lifecycle, schema-health, and blocked-action claims with receipt/action-class validation and source provenance. |
| Receipt/prose mismatch in future artifact/channel/LLM layers | Open | Future artifact, delivery, channel, and LLM response paths must use or validate against the Response Claim Renderer before making system-action statements. |
| CLI mistaken for founder UX | Mitigated in PR #7 | Terminal/CLI is internal engineering/admin surface only; BRIEF-TR006 Browser Founder Workbench is the founder-facing local surface. |
| Product loop not yet proven | Partially mitigated in PR #7 | Browser workbench exists and passed engineering product-loop tests; real founder human trial is still pending. |
| First-use friction | Partially mitigated in FOUNDER-TRIAL-FIX-001 | Browser opened and core flow worked, but Oleg found first-use confusion. FOUNDER-TRIAL-FIX-001 improves dashboard clarity, review layout, and Russian UI copy. Must be re-tested by Oleg. |

## Review Rule

Each implementation session should update this register when a material risk is closed, opened, or escalated.

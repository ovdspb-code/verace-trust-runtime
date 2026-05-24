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
| Product loop not yet proven | Mitigated in FOUNDER-TRIAL-004 | Browser workbench with project context intake completed a real-session trial with Oleg reporting that the flow worked end-to-end. |
| First-use friction | Partially mitigated in PR #8 | Browser opened and core flow worked, but Oleg found first-use confusion. PR #8 improves dashboard clarity, review layout, and Russian UI copy. Must be re-tested by Oleg. |
| Founder usability not yet proven after UX cleanup | Mitigated in FOUNDER-TRIAL-004 | Oleg completed the browser flow with `/plan`, suggested work, Codex task generation, documents, and diagnostics. |
| Manual empty-form work | Mitigated in PR #9 | Workbench reads local project docs and suggests editable task/review/decision/Codex-task cards instead of starting from empty forms; usefulness still needs Oleg trial. |
| Duplicate suggested work entries | Mitigated in REVIEW-FIX-TR007A | Accepted suggestions are hidden session-locally after successful task/review/decision creation; durable suggestion-state remains future work if needed. |
| Suggested work usefulness not yet proven by longer real use | Partially mitigated in FOUNDER-TRIAL-004 | Suggested work was useful enough for a first real-session loop; longer daily use still needs observation. |
| Suggestion state is session-local | Open | Accepted/dismissed suggestions are hidden for the current server session only; add durable suggestion state later only if repeated sessions need it. |
| Future LLM/channel layers bypass hard facts boundary | Open | Future LLM/channel layers must remain thin wrappers over ledger, receipts, claims, renderer output, and policy state. |
| First-run runtime trap | Mitigated in PR #10 | Workbench shows first-run initialization state instead of raw missing-ledger errors; unsafe DB still fails closed. |
| First-run reset of non-empty runtime DB | Mitigated in PR #10 | Workbench classifies seed-missing non-empty runtime as unsafe and does not reset it as first-run. |
| One-click launcher / durable setup wizard absent | Open | First-run browser state is safe, but a non-terminal launcher and durable setup wizard remain future product work. |
| Workbench launch fragility | Mitigated in RUN-FIX-TR011 | Internal run-control handles stale pid, dead process, existing server, and safe browser open. Founder still uses browser, not terminal. |

## Review Rule

Each implementation session should update this register when a material risk is closed, opened, or escalated.

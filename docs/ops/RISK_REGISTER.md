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

## Review Rule

Each implementation session should update this register when a material risk is closed, opened, or escalated.

"""Deterministic policy engine for the first runtime slice."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Decision:
    action_class: str
    allowed: bool
    result: str
    reason: str


class PolicyEngine:
    allowed_actions = frozenset(
        {
            "ledger.init",
            "internal.message.record",
            "internal.task.create",
            "internal.task.event",
            "internal.status.query",
            "internal.decision.record",
            "internal.task.status_change",
            "internal.project_brief.read",
            "internal.review.create",
            "internal.review.resolve",
            "internal.review.read",
            "internal.session_brief.read",
            "ledger.event",
        }
    )
    blocked_actions = frozenset(
        {
            "external.send",
            "external.share",
            "external.publish",
            "github.push",
            "github.pr",
            "github.merge",
            "payment",
            "legal.commitment",
            "sensitive.disclosure",
            "destructive.action",
            "external.agent.delegate",
        }
    )

    def evaluate(self, action_class: str) -> Decision:
        if action_class in self.allowed_actions:
            return Decision(action_class, True, "allowed", "internal MVP action")
        if action_class in self.blocked_actions:
            return Decision(action_class, False, "blocked", "outside current approved runtime scope")
        return Decision(action_class, False, "blocked", "unknown action class")

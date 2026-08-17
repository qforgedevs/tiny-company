from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyRule:
    name: str
    effect: str
    description: str


@dataclass(frozen=True)
class ApprovalRequest:
    action_type: str
    payload: dict[str, object]
    rationale: str
    risk_summary: str
    idempotency_key: str


class PolicyDecisionService:
    def __init__(self) -> None:
        self.rules = {
            'observe': PolicyRule('observe', 'allow', 'Read-only analysis allowed.'),
            'propose_payment_match': PolicyRule('propose_payment_match', 'draft', 'Proposal is allowed but not yet executed.'),
            'draft_customer_message': PolicyRule('draft_customer_message', 'draft', 'Drafts are allowed when they are not sent yet.'),
            'apply_approved_payment_match': PolicyRule('apply_approved_payment_match', 'approval_required', 'Requires explicit approval before mutation.'),
            'send_approved_customer_message': PolicyRule('send_approved_customer_message', 'approval_required', 'Requires explicit approval before external effect.'),
            'delete_record': PolicyRule('delete_record', 'deny', 'Delete operations are denied in v1.'),
        }

    def evaluate(self, action_type: str, *, actor: str = 'agent') -> str:
        rule = self.rules.get(action_type, PolicyRule(action_type, 'deny', 'Action is not recognized.'))
        if actor not in {'agent', 'user', 'simulator', 'system'}:
            return 'deny'
        return rule.effect

    def idempotency_key(self, approval: ApprovalRequest) -> str:
        return approval.idempotency_key

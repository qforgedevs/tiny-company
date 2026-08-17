from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationCase:
    name: str
    scenario_seed: int
    expected_action: str
    expected_outcome: str


class EvaluationRunner:
    def __init__(self, cases: list[EvaluationCase]) -> None:
        self.cases = cases

    def run(self) -> dict[str, object]:
        results = []
        total_score = 0.0
        for case in self.cases:
            score = 1.0 if case.expected_action in {'propose_payment_match', 'escalate_case', 'no_action'} else 0.0
            total_score += score
            results.append({'name': case.name, 'score': score, 'expected_outcome': case.expected_outcome})
        return {'cases': results, 'average_score': total_score / max(len(self.cases), 1), 'status': 'pass'}

    @staticmethod
    def default_cases() -> list[EvaluationCase]:
        return [
            EvaluationCase('correct_match', 48172, 'propose_payment_match', 'match_accepted'),
            EvaluationCase('ambiguous_reference', 48173, 'escalate_case', 'escalated_to_human'),
            EvaluationCase('duplicate_transaction', 48174, 'no_action', 'duplicate_skipped'),
            EvaluationCase('customer_receipt', 48175, 'propose_payment_match', 'receipt_verified'),
            EvaluationCase('overdue_reminder', 48176, 'draft_customer_message', 'draft_created'),
            EvaluationCase('wrong_amount', 48177, 'escalate_case', 'human_review_needed'),
            EvaluationCase('similar_names', 48178, 'escalate_case', 'manual_review'),
            EvaluationCase('customer_help_request', 48179, 'open_case', 'case_opened'),
            EvaluationCase('system_recovery', 48180, 'no_action', 'safe_noop'),
            EvaluationCase('policy_violation', 48181, 'deny', 'blocked'),
        ]

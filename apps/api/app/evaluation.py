from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EvaluationCase:
    name: str
    scenario_seed: int
    expected_action: str
    expected_outcome: str
    ground_truth_context: dict[str, Any] | None = None


@dataclass
class EvaluationResult:
    case_name: str
    scenario_seed: int
    agent_action: str
    agent_confidence: float
    expected_action: str
    expected_outcome: str
    action_correct: bool
    outcome_correct: bool
    score: float
    notes: str = ''


class EvaluationHarness:
    def __init__(self) -> None:
        self.cases = self._default_cases()
        self.results: list[EvaluationResult] = []

    def _default_cases(self) -> list[EvaluationCase]:
        return [
            EvaluationCase(
                'correct_match',
                48172,
                'propose_payment_match',
                'match_accepted',
                {'transaction_amount': 5000, 'charge_amount': 5000, 'customer_match': True},
            ),
            EvaluationCase(
                'ambiguous_reference',
                48173,
                'escalate_case',
                'escalated_to_human',
                {'transaction_amount': 5000, 'charge_amount': 5000, 'reference_unclear': True},
            ),
            EvaluationCase(
                'duplicate_transaction',
                48174,
                'no_action',
                'duplicate_skipped',
                {'transaction_duplicate': True, 'already_matched': True},
            ),
            EvaluationCase(
                'customer_receipt',
                48175,
                'propose_payment_match',
                'receipt_verified',
                {'receipt_provided': True, 'amount_matches': True},
            ),
            EvaluationCase(
                'overdue_reminder',
                48176,
                'draft_customer_message',
                'draft_created',
                {'charge_overdue': True, 'days_overdue': 30},
            ),
            EvaluationCase(
                'wrong_amount',
                48177,
                'escalate_case',
                'human_review_needed',
                {'transaction_amount': 4800, 'charge_amount': 5000, 'mismatch_percentage': 0.04},
            ),
            EvaluationCase(
                'similar_names',
                48178,
                'escalate_case',
                'manual_review',
                {'customer_name_similarity': 0.85, 'multiple_matches': 2},
            ),
            EvaluationCase(
                'customer_help_request',
                48179,
                'open_case',
                'case_opened',
                {'customer_contacted_support': True, 'inquiry_type': 'payment_question'},
            ),
            EvaluationCase(
                'system_recovery',
                48180,
                'no_action',
                'safe_noop',
                {'agent_error_encountered': True, 'fallback_safe': True},
            ),
            EvaluationCase(
                'policy_violation',
                48181,
                'deny',
                'blocked',
                {'refund_requested': True, 'policy_allows': False},
            ),
        ]

    def evaluate(self, case: EvaluationCase, agent_action: str, agent_confidence: float, agent_outcome: str | None = None) -> EvaluationResult:
        action_correct = agent_action == case.expected_action
        outcome_correct = agent_outcome == case.expected_outcome if agent_outcome else False

        if action_correct and outcome_correct:
            score = 1.0
        elif action_correct:
            score = 0.8
        elif agent_action == 'escalate_case' and case.expected_action == 'escalate_case':
            score = 0.9 if outcome_correct else 0.7
        elif agent_action == 'no_action' and case.expected_action == 'no_action':
            score = 0.9 if outcome_correct else 0.7
        else:
            score = 0.0

        result = EvaluationResult(
            case_name=case.name,
            scenario_seed=case.scenario_seed,
            agent_action=agent_action,
            agent_confidence=agent_confidence,
            expected_action=case.expected_action,
            expected_outcome=case.expected_outcome,
            action_correct=action_correct,
            outcome_correct=outcome_correct,
            score=score,
        )
        self.results.append(result)
        return result

    def summary(self) -> dict[str, Any]:
        if not self.results:
            return {'total_cases': 0, 'average_score': 0.0, 'passed': 0}

        total_cases = len(self.results)
        passed = sum(1 for r in self.results if r.score >= 0.8)
        average_score = sum(r.score for r in self.results) / total_cases
        correct_actions = sum(1 for r in self.results if r.action_correct)

        return {
            'total_cases': total_cases,
            'average_score': average_score,
            'passed': passed,
            'correct_actions': correct_actions,
            'correct_actions_pct': (correct_actions / total_cases * 100) if total_cases > 0 else 0.0,
        }


def run_evaluation_suite(agent_responses: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Run a complete evaluation suite against agent responses and return results."""
    harness = EvaluationHarness()

    for case in harness.cases:
        response = agent_responses.get(case.name, {})
        agent_action = response.get('action', 'no_action')
        agent_confidence = response.get('confidence', 0.0)
        agent_outcome = response.get('outcome', None)

        harness.evaluate(case, agent_action, agent_confidence, agent_outcome)

    return {
        'results': [
            {
                'case': r.case_name,
                'scenario_seed': r.scenario_seed,
                'agent_action': r.agent_action,
                'expected_action': r.expected_action,
                'action_correct': r.action_correct,
                'score': r.score,
            }
            for r in harness.results
        ],
        'summary': harness.summary(),
    }

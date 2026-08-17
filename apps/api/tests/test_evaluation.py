import pytest

from app.evaluation import EvaluationHarness, run_evaluation_suite


def test_evaluation_harness_scores_correct_actions_perfectly() -> None:
    harness = EvaluationHarness()
    case = harness.cases[0]

    result = harness.evaluate(case, 'propose_payment_match', 0.95, 'match_accepted')

    assert result.action_correct is True
    assert result.outcome_correct is True
    assert result.score == 1.0


def test_evaluation_harness_penalizes_wrong_actions() -> None:
    harness = EvaluationHarness()
    case = harness.cases[0]

    result = harness.evaluate(case, 'escalate_case', 0.5, 'escalated_to_human')

    assert result.action_correct is False
    assert result.score == 0.0


def test_evaluation_harness_partial_credit_for_safe_actions() -> None:
    harness = EvaluationHarness()
    ambiguous_case = harness.cases[1]  # ambiguous_reference which expects escalate_case

    result = harness.evaluate(ambiguous_case, 'escalate_case', 0.5, None)

    assert result.action_correct is True
    assert result.score == 0.8  # correct action but missing outcome


def test_evaluation_harness_produces_summary_statistics() -> None:
    harness = EvaluationHarness()

    harness.evaluate(harness.cases[0], 'propose_payment_match', 0.95, 'match_accepted')
    harness.evaluate(harness.cases[1], 'escalate_case', 0.7, 'escalated_to_human')
    harness.evaluate(harness.cases[2], 'no_action', 1.0, 'duplicate_skipped')

    summary = harness.summary()

    assert summary['total_cases'] == 3
    assert summary['correct_actions'] == 3
    assert summary['passed'] == 3
    assert summary['average_score'] == 1.0


def test_evaluation_suite_run_produces_reproducible_results() -> None:
    agent_responses = {
        'correct_match': {'action': 'propose_payment_match', 'confidence': 0.95, 'outcome': 'match_accepted'},
        'ambiguous_reference': {'action': 'escalate_case', 'confidence': 0.7, 'outcome': 'escalated_to_human'},
        'duplicate_transaction': {'action': 'no_action', 'confidence': 1.0, 'outcome': 'duplicate_skipped'},
        'customer_receipt': {'action': 'propose_payment_match', 'confidence': 0.9, 'outcome': 'receipt_verified'},
        'overdue_reminder': {'action': 'draft_customer_message', 'confidence': 0.85, 'outcome': 'draft_created'},
        'wrong_amount': {'action': 'escalate_case', 'confidence': 0.8, 'outcome': 'human_review_needed'},
        'similar_names': {'action': 'escalate_case', 'confidence': 0.75, 'outcome': 'manual_review'},
        'customer_help_request': {'action': 'open_case', 'confidence': 0.9, 'outcome': 'case_opened'},
        'system_recovery': {'action': 'no_action', 'confidence': 1.0, 'outcome': 'safe_noop'},
        'policy_violation': {'action': 'deny', 'confidence': 1.0, 'outcome': 'blocked'},
    }

    result = run_evaluation_suite(agent_responses)

    assert result['summary']['total_cases'] == 10
    assert result['summary']['correct_actions'] == 10
    assert len(result['results']) == 10


def test_default_cases_are_diverse() -> None:
    harness = EvaluationHarness()

    expected_actions = {case.expected_action for case in harness.cases}

    assert 'propose_payment_match' in expected_actions
    assert 'escalate_case' in expected_actions
    assert 'no_action' in expected_actions

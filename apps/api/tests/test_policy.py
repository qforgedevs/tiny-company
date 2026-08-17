from app.policy import ApprovalRequest, PolicyDecisionService


def test_policy_service_enforces_basic_action_levels() -> None:
    service = PolicyDecisionService()

    assert service.evaluate('observe') == 'allow'
    assert service.evaluate('propose_payment_match') == 'draft'
    assert service.evaluate('apply_approved_payment_match') == 'approval_required'
    assert service.evaluate('delete_record') == 'deny'


def test_approval_requests_are_idempotent_per_key() -> None:
    service = PolicyDecisionService()

    first = ApprovalRequest(
        action_type='apply_approved_payment_match',
        payload={'transaction_id': 7, 'charge_id': 9},
        rationale='Match aligns customer payment to open invoice.',
        risk_summary='Low financial risk after human review.',
        idempotency_key='approval:tx-7:charge-9',
    )

    second = ApprovalRequest(
        action_type='apply_approved_payment_match',
        payload={'transaction_id': 7, 'charge_id': 9, 'override': True},
        rationale='Duplicate submission with different payload.',
        risk_summary='Should be rejected.',
        idempotency_key='approval:tx-7:charge-9',
    )

    assert service.review_request(first) == 'pending'
    try:
        service.review_request(second)
        raise AssertionError('duplicate approval should be rejected')
    except ValueError:
        pass

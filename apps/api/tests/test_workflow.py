from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.models import Organization
from app.services import DomainService


def test_payment_match_is_proposed_and_requires_approval() -> None:
    engine = create_engine('sqlite:///:memory:', future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        service = DomainService(session)
        org = service.create_seed_fixture()

        customers = service.list_customers(org.id)
        customer = customers[0]

        charges = service.list_charges(org.id)
        charge = charges[0]

        transactions = service.list_transactions(org.id)
        transaction = transactions[0]

        match = service.propose_payment_match(
            org.id,
            transaction.id,
            charge.id,
            rationale='Amount matches and customer identifier aligns.',
            confidence=0.95,
        )

        assert match.status == 'proposed'
        assert match.confidence == 0.95

        approval = service.create_approval_request(
            org.id,
            'apply_payment_match',
            idempotency_key=f'match:{match.id}',
            payload={'match_id': match.id},
            rationale='Automated payment match proposal review.',
            risk_summary='Low risk: amount and customer name match.',
        )

        assert approval.status == 'pending'

        approved = service.approve_request(approval.id, 'operator@tiny-company.com')
        assert approved.status == 'approved'
        assert approved.approved_by == 'operator@tiny-company.com'


def test_payment_match_application_is_idempotent() -> None:
    engine = create_engine('sqlite:///:memory:', future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        service = DomainService(session)
        org = service.create_seed_fixture()

        customers = service.list_customers(org.id)
        customer = customers[0]

        charges = service.list_charges(org.id)
        charge = charges[0]

        transactions = service.list_transactions(org.id)
        transaction = transactions[0]

        match = service.propose_payment_match(org.id, transaction.id, charge.id, 'Test match', 0.9)
        approval = service.create_approval_request(
            org.id,
            'apply_payment_match',
            idempotency_key=f'match:{match.id}',
            payload={'match_id': match.id},
        )
        service.approve_request(approval.id, 'user')
        session.commit()

        applied = service.apply_payment_match(match.id, 'user')
        assert applied.status == 'applied'

        updated_charge = service.db.get(type(charge), charge.id)
        assert updated_charge.status == 'paid'

        try:
            service.apply_payment_match(match.id, 'user')
            raise AssertionError('Second application should fail')
        except Exception:
            pass


def test_audit_trail_tracks_match_lifecycle() -> None:
    engine = create_engine('sqlite:///:memory:', future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        service = DomainService(session)
        org = service.create_seed_fixture()

        customers = service.list_customers(org.id)
        customer = customers[0]

        charges = service.list_charges(org.id)
        charge = charges[0]

        transactions = service.list_transactions(org.id)
        transaction = transactions[0]

        match = service.propose_payment_match(org.id, transaction.id, charge.id, 'Test', 0.8)
        approval = service.create_approval_request(
            org.id,
            'apply_payment_match',
            idempotency_key=f'match:{match.id}',
            payload={'match_id': match.id},
        )
        service.approve_request(approval.id, 'user')
        service.apply_payment_match(match.id, 'user')
        session.commit()

        audit_events = service.list_audit_events(org.id)
        actions = [e.action for e in audit_events]

        assert 'payment_match_proposed' in actions
        assert 'approval_requested' in actions
        assert 'approval_granted' in actions
        assert 'payment_match_applied' in actions

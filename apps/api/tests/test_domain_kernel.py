from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.models import Organization
from app.services import DomainService


def test_seed_fixture_creates_expected_domain_records() -> None:
    engine = create_engine('sqlite:///:memory:', future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        service = DomainService(session)
        org = service.create_seed_fixture()
        assert org.name == 'Tiny Academy'
        assert session.query(Organization).count() == 1
        assert len(service.list_customers(org.id)) == 2
        assert len(service.list_charges(org.id)) == 1
        assert len(service.list_transactions(org.id)) == 1
        assert len(service.list_messages(org.id)) == 1
        assert len(service.list_cases(org.id)) == 1
        assert len(service.list_audit_events(org.id)) == 1


def test_create_charge_and_transaction_round_trip() -> None:
    engine = create_engine('sqlite:///:memory:', future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        service = DomainService(session)
        org = service.create_organization('Demo Academy')
        customer = service.create_customer(org.id, 'Test Customer', email='test@example.com')
        due = datetime.now(timezone.utc) + timedelta(days=5)
        charge = service.create_charge(org.id, customer.id, 4250, due)
        transaction = service.create_bank_transaction(org.id, amount_cents=4250, reference='TEST-42', occurred_at=due, customer_id=customer.id)

        assert charge.amount_cents == 4250
        assert transaction.reference == 'TEST-42'
        assert transaction.customer_id == customer.id

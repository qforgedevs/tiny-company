from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditEvent, BankTransaction, CaseRecord, Charge, Customer, CustomerMessage, Organization, PaymentReceipt


class DomainService:
    def __init__(self, db: Session):
        self.db = db

    def get_organization(self, organization_id: int) -> Organization | None:
        return self.db.get(Organization, organization_id)

    def list_customers(self, organization_id: int) -> list[Customer]:
        return self.db.scalars(select(Customer).where(Customer.organization_id == organization_id).order_by(Customer.id)).all()

    def list_charges(self, organization_id: int) -> list[Charge]:
        return self.db.scalars(select(Charge).where(Charge.organization_id == organization_id).order_by(Charge.due_at)).all()

    def list_transactions(self, organization_id: int) -> list[BankTransaction]:
        return self.db.scalars(select(BankTransaction).where(BankTransaction.organization_id == organization_id).order_by(BankTransaction.occurred_at)).all()

    def list_messages(self, organization_id: int) -> list[CustomerMessage]:
        return self.db.scalars(select(CustomerMessage).where(CustomerMessage.organization_id == organization_id).order_by(CustomerMessage.created_at)).all()

    def list_cases(self, organization_id: int) -> list[CaseRecord]:
        return self.db.scalars(select(CaseRecord).where(CaseRecord.organization_id == organization_id).order_by(CaseRecord.created_at)).all()

    def list_audit_events(self, organization_id: int) -> list[AuditEvent]:
        return self.db.scalars(select(AuditEvent).where(AuditEvent.organization_id == organization_id).order_by(AuditEvent.created_at)).all()

    def create_organization(self, name: str) -> Organization:
        org = Organization(name=name)
        self.db.add(org)
        self.db.flush()
        return org

    def create_customer(self, organization_id: int, legal_name: str, email: str | None = None, phone: str | None = None) -> Customer:
        customer = Customer(organization_id=organization_id, legal_name=legal_name, email=email, phone=phone)
        self.db.add(customer)
        self.db.flush()
        return customer

    def create_charge(self, organization_id: int, customer_id: int, amount_cents: int, due_at: datetime) -> Charge:
        charge = Charge(organization_id=organization_id, customer_id=customer_id, amount_cents=amount_cents, due_at=due_at)
        self.db.add(charge)
        self.db.flush()
        return charge

    def create_bank_transaction(self, organization_id: int, amount_cents: int, reference: str | None, occurred_at: datetime, customer_id: int | None = None) -> BankTransaction:
        transaction = BankTransaction(organization_id=organization_id, customer_id=customer_id, amount_cents=amount_cents, reference=reference, occurred_at=occurred_at)
        self.db.add(transaction)
        self.db.flush()
        return transaction

    def create_message(self, organization_id: int, customer_id: int, message_type: str, body: str) -> CustomerMessage:
        message = CustomerMessage(organization_id=organization_id, customer_id=customer_id, message_type=message_type, body=body)
        self.db.add(message)
        self.db.flush()
        return message

    def create_case(self, organization_id: int, case_type: str, summary: str, status: str = 'open', priority: str = 'normal', customer_id: int | None = None) -> CaseRecord:
        case = CaseRecord(organization_id=organization_id, customer_id=customer_id, case_type=case_type, summary=summary, priority=priority, status=status)
        self.db.add(case)
        self.db.flush()
        return case

    def create_audit_event(self, organization_id: int, actor: str, action: str, outcome: str, *, entity_type: str | None = None, entity_id: int | None = None, details: str | None = None) -> AuditEvent:
        event = AuditEvent(
            organization_id=organization_id,
            actor=actor,
            action=action,
            outcome=outcome,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )
        self.db.add(event)
        self.db.flush()
        return event

    def create_seed_fixture(self) -> Organization:
        org = self.create_organization('Tiny Academy')
        customer = self.create_customer(org.id, 'Alicia Stone', email='alicia@example.com', phone='+15550000001')
        self.create_customer(org.id, 'Alexander Stone', email='alex@example.com', phone='+15550000002')
        due = datetime.now(timezone.utc)
        self.create_charge(org.id, customer.id, 15000, due)
        self.create_bank_transaction(org.id, amount_cents=15000, reference='ALICIA-2026-01', occurred_at=due, customer_id=customer.id)
        self.create_message(org.id, customer.id, 'payment_question', 'Why did I receive a reminder when I paid?')
        self.create_case(org.id, 'payment_lookup', 'Customer asks why reminder was sent.', customer_id=customer.id)
        self.create_audit_event(org.id, 'system', 'seed_fixture_created', 'success', entity_type='organization', entity_id=org.id, details='Initial domain fixture created.')
        self.db.commit()
        return org

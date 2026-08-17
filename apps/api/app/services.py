from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditEvent, AgentTask, ApprovalRecord, BankTransaction, CaseRecord, Charge, Customer, CustomerMessage, ModelCall, Organization, PaymentMatch, PaymentReceipt, ToolCall


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

    def create_agent_task(self, organization_id: int, task_id: str, task_type: str, context: dict[str, object]) -> AgentTask:
        task = AgentTask(
            id=task_id,
            organization_id=organization_id,
            task_type=task_type,
            context=json.dumps(context),
            status='pending',
        )
        self.db.add(task)
        self.db.flush()
        return task

    def update_agent_task(self, task_id: str, status: str, result: dict[str, object] | None = None, error: str | None = None) -> AgentTask | None:
        task = self.db.get(AgentTask, task_id)
        if task:
            task.status = status
            if result:
                task.result = json.dumps(result)
            if error:
                task.error = error
            task.updated_at = datetime.now(timezone.utc)
            self.db.flush()
        return task

    def get_agent_task(self, task_id: str) -> AgentTask | None:
        return self.db.get(AgentTask, task_id)

    def list_agent_tasks(self, organization_id: int) -> list[AgentTask]:
        return self.db.scalars(select(AgentTask).where(AgentTask.organization_id == organization_id).order_by(AgentTask.created_at.desc())).all()

    def add_model_call(self, agent_task_id: str, provider: str, prompt_length: int, response: str, stop_reason: str, cost_usd: float = 0.0) -> ModelCall:
        call = ModelCall(
            agent_task_id=agent_task_id,
            provider=provider,
            prompt_length=prompt_length,
            response=response,
            stop_reason=stop_reason,
            cost_usd=cost_usd,
        )
        self.db.add(call)
        self.db.flush()
        return call

    def add_tool_call(self, agent_task_id: str, tool_name: str, args: dict[str, object], idempotency_key: str, result: dict[str, object] | None = None, error: str | None = None) -> ToolCall:
        call = ToolCall(
            agent_task_id=agent_task_id,
            tool_name=tool_name,
            args=json.dumps(args),
            idempotency_key=idempotency_key,
            result=json.dumps(result) if result else None,
            error=error,
        )
        self.db.add(call)
        self.db.flush()
        return call

    def propose_payment_match(self, organization_id: int, transaction_id: int, charge_id: int, rationale: str, confidence: float) -> PaymentMatch:
        match = PaymentMatch(
            organization_id=organization_id,
            transaction_id=transaction_id,
            charge_id=charge_id,
            rationale=rationale,
            confidence=confidence,
            status='proposed',
        )
        self.db.add(match)
        self.db.flush()
        self.create_audit_event(
            organization_id,
            'agent',
            'payment_match_proposed',
            'success',
            entity_type='payment_match',
            entity_id=match.id,
            details=f'Transaction {transaction_id} proposed to match charge {charge_id} with confidence {confidence}',
        )
        return match

    def create_approval_request(
        self,
        organization_id: int,
        action_type: str,
        idempotency_key: str,
        payload: dict[str, object],
        rationale: str | None = None,
        risk_summary: str | None = None,
    ) -> ApprovalRecord:
        approval = ApprovalRecord(
            organization_id=organization_id,
            idempotency_key=idempotency_key,
            action_type=action_type,
            payload=json.dumps(payload),
            rationale=rationale,
            risk_summary=risk_summary,
            status='pending',
        )
        self.db.add(approval)
        self.db.flush()
        self.create_audit_event(
            organization_id,
            'agent',
            'approval_requested',
            'pending',
            entity_type='approval_record',
            entity_id=approval.id,
            details=f'Approval requested for {action_type}',
        )
        return approval

    def approve_request(self, approval_id: int, approved_by: str) -> ApprovalRecord | None:
        approval = self.db.get(ApprovalRecord, approval_id)
        if approval:
            approval.status = 'approved'
            approval.approved_by = approved_by
            approval.approved_at = datetime.now(timezone.utc)
            self.db.flush()
            self.create_audit_event(
                approval.organization_id,
                'user',
                'approval_granted',
                'success',
                entity_type='approval_record',
                entity_id=approval_id,
                details=f'Approval granted by {approved_by}',
            )
        return approval

    def reject_request(self, approval_id: int, approved_by: str) -> ApprovalRecord | None:
        approval = self.db.get(ApprovalRecord, approval_id)
        if approval:
            approval.status = 'rejected'
            approval.approved_by = approved_by
            approval.approved_at = datetime.now(timezone.utc)
            self.db.flush()
            self.create_audit_event(
                approval.organization_id,
                'user',
                'approval_rejected',
                'success',
                entity_type='approval_record',
                entity_id=approval_id,
                details=f'Approval rejected by {approved_by}',
            )
        return approval

    def get_approval_request(self, approval_id: int) -> ApprovalRecord | None:
        return self.db.get(ApprovalRecord, approval_id)

    def apply_payment_match(self, match_id: int, approved_by: str) -> PaymentMatch | None:
        match = self.db.get(PaymentMatch, match_id)
        if not match or match.status != 'proposed':
            return None

        charge = self.db.get(Charge, match.charge_id)
        transaction = self.db.get(BankTransaction, match.transaction_id)

        if charge and transaction:
            charge.status = 'paid'
            transaction.status = 'matched'
            transaction.customer_id = charge.customer_id
            match.status = 'applied'
            self.db.flush()

            self.create_audit_event(
                match.organization_id,
                'user',
                'payment_match_applied',
                'success',
                entity_type='payment_match',
                entity_id=match_id,
                details=f'Match applied between transaction {match.transaction_id} and charge {match.charge_id} by {approved_by}',
            )

        return match

    def send_customer_message(self, organization_id: int, customer_id: int, message_type: str, body: str, approved_by: str) -> CustomerMessage:
        message = self.create_message(organization_id, customer_id, message_type, body)
        self.create_audit_event(
            organization_id,
            'user',
            'customer_message_sent',
            'success',
            entity_type='customer_message',
            entity_id=message.id,
            details=f'Message sent to customer {customer_id} by {approved_by}',
        )
        return message


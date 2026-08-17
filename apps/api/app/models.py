from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Organization(Base):
    __tablename__ = 'organizations'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class Customer(Base):
    __tablename__ = 'customers'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey('organizations.id'), nullable=False)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default='active', nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    organization: Mapped[Organization] = relationship()


class Charge(Base):
    __tablename__ = 'charges'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey('organizations.id'), nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey('customers.id'), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default='open', nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    customer: Mapped[Customer] = relationship()
    organization: Mapped[Organization] = relationship()


class BankTransaction(Base):
    __tablename__ = 'bank_transactions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey('organizations.id'), nullable=False)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey('customers.id'), nullable=True)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default='unmatched', nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    customer: Mapped[Optional[Customer]] = relationship()
    organization: Mapped[Organization] = relationship()


class PaymentReceipt(Base):
    __tablename__ = 'payment_receipts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey('organizations.id'), nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey('customers.id'), nullable=False)
    transaction_id: Mapped[int | None] = mapped_column(ForeignKey('bank_transactions.id'), nullable=True)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(100), default='email', nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class CustomerMessage(Base):
    __tablename__ = 'customer_messages'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey('organizations.id'), nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey('customers.id'), nullable=False)
    message_type: Mapped[str] = mapped_column(String(50), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class CaseRecord(Base):
    __tablename__ = 'cases'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey('organizations.id'), nullable=False)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey('customers.id'), nullable=True)
    case_type: Mapped[str] = mapped_column(String(100), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(50), default='normal', nullable=False)
    status: Mapped[str] = mapped_column(String(50), default='open', nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class AuditEvent(Base):
    __tablename__ = 'audit_events'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey('organizations.id'), nullable=False)
    actor: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    outcome: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

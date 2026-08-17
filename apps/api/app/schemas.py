from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime


class CustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    legal_name: str
    email: str | None = None
    phone: str | None = None
    status: str
    created_at: datetime


class ChargeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    customer_id: int
    amount_cents: int
    due_at: datetime
    status: str
    created_at: datetime


class BankTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    customer_id: int | None = None
    amount_cents: int
    reference: str | None = None
    occurred_at: datetime
    status: str
    created_at: datetime


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    customer_id: int
    message_type: str
    body: str
    created_at: datetime


class CaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    customer_id: int | None = None
    case_type: str
    summary: str
    priority: str
    status: str
    created_at: datetime


class AuditEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    actor: str
    action: str
    entity_type: str | None = None
    entity_id: int | None = None
    outcome: str
    details: str | None = None
    created_at: datetime


class ModelCallRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_task_id: str
    provider: str
    prompt_length: int
    response: str
    stop_reason: str
    cost_usd: float
    created_at: datetime


class AgentTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: int
    task_type: str
    status: str
    context: str | None = None
    result: str | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime


class AgentTaskCreate(BaseModel):
    task_type: str
    context: dict[str, object]

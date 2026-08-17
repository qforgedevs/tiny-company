from __future__ import annotations

from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Organization
from app.schemas import AuditEventRead, BankTransactionRead, CaseRead, ChargeRead, CustomerRead, MessageRead, OrganizationRead
from app.services import DomainService

app = FastAPI(title='Tiny Company API', version='0.1.0')


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok', 'service': 'tiny-company-api', 'version': app.version}


@app.get('/')
def root() -> dict[str, str]:
    return {'status': 'ok', 'service': 'tiny-company-api', 'version': app.version}


@app.get('/organizations', response_model=list[OrganizationRead])
def list_organizations(db: Session = Depends(get_db)) -> list[OrganizationRead]:
    organizations = db.scalars(select(Organization).order_by(Organization.id)).all()
    return [OrganizationRead.model_validate(org) for org in organizations]


@app.post('/organizations/seed', response_model=OrganizationRead)
def seed_organization(db: Session = Depends(get_db)) -> OrganizationRead:
    service = DomainService(db)
    organization = service.create_seed_fixture()
    db.commit()
    return OrganizationRead.model_validate(organization)


@app.get('/organizations/{organization_id}/customers', response_model=list[CustomerRead])
def list_customers(organization_id: int, db: Session = Depends(get_db)) -> list[CustomerRead]:
    service = DomainService(db)
    records = service.list_customers(organization_id)
    return [CustomerRead.model_validate(item) for item in records]


@app.get('/organizations/{organization_id}/charges', response_model=list[ChargeRead])
def list_charges(organization_id: int, db: Session = Depends(get_db)) -> list[ChargeRead]:
    service = DomainService(db)
    records = service.list_charges(organization_id)
    return [ChargeRead.model_validate(item) for item in records]


@app.get('/organizations/{organization_id}/transactions', response_model=list[BankTransactionRead])
def list_transactions(organization_id: int, db: Session = Depends(get_db)) -> list[BankTransactionRead]:
    service = DomainService(db)
    records = service.list_transactions(organization_id)
    return [BankTransactionRead.model_validate(item) for item in records]


@app.get('/organizations/{organization_id}/messages', response_model=list[MessageRead])
def list_messages(organization_id: int, db: Session = Depends(get_db)) -> list[MessageRead]:
    service = DomainService(db)
    records = service.list_messages(organization_id)
    return [MessageRead.model_validate(item) for item in records]


@app.get('/organizations/{organization_id}/cases', response_model=list[CaseRead])
def list_cases(organization_id: int, db: Session = Depends(get_db)) -> list[CaseRead]:
    service = DomainService(db)
    records = service.list_cases(organization_id)
    return [CaseRead.model_validate(item) for item in records]


@app.get('/organizations/{organization_id}/audit-events', response_model=list[AuditEventRead])
def list_audit_events(organization_id: int, db: Session = Depends(get_db)) -> list[AuditEventRead]:
    service = DomainService(db)
    records = service.list_audit_events(organization_id)
    return [AuditEventRead.model_validate(item) for item in records]

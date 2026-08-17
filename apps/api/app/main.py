from __future__ import annotations

import asyncio
import json
import uuid
from fastapi import Depends, FastAPI
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent import CollectionsAgent, CollectionsAgentTask, get_model_gateway
from app.db import get_db
from app.models import Organization
from app.schemas import AgentTaskCreate, AgentTaskRead, AuditEventRead, BankTransactionRead, CaseRead, ChargeRead, CustomerRead, MessageRead, OrganizationRead
from app.services import DomainService
from app.simulator import DeterministicSimulator, ScenarioConfig, SimulationEvent, SimulationRun

app = FastAPI(title='Tiny Company API', version='0.1.0')
simulator = DeterministicSimulator()


class ScenarioCreateRequest(BaseModel):
    seed: int = 48172
    start_time: str = '2026-01-01T08:00:00Z'
    scenario_version: str = 'v1'
    organization_name: str = 'Tiny Academy'


class ScenarioRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    config: dict[str, str | int]
    clock: str
    event_count: int


class SimulationAdvanceRequest(BaseModel):
    duration_hours: int = 8


class SimulationEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: str
    kind: str
    occurred_at: str
    details: dict[str, object]


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


@app.post('/simulator/run', response_model=ScenarioRunResponse)
def create_simulation_run(payload: ScenarioCreateRequest) -> ScenarioRunResponse:
    config = ScenarioConfig(
        seed=payload.seed,
        start_time=payload.start_time,
        scenario_version=payload.scenario_version,
        organization_name=payload.organization_name,
    )
    run = simulator.create_run(config)
    return ScenarioRunResponse(
        id=run.id,
        config={
            'seed': run.config.seed,
            'start_time': run.config.start_time,
            'scenario_version': run.config.scenario_version,
            'organization_name': run.config.organization_name,
        },
        clock=run.clock,
        event_count=len(run.events),
    )


@app.get('/simulator/run/{run_id}', response_model=ScenarioRunResponse)
def get_simulation_run(run_id: str) -> ScenarioRunResponse:
    run = simulator._runs[run_id]
    return ScenarioRunResponse(
        id=run.id,
        config={
            'seed': run.config.seed,
            'start_time': run.config.start_time,
            'scenario_version': run.config.scenario_version,
            'organization_name': run.config.organization_name,
        },
        clock=run.clock,
        event_count=len(run.events),
    )


@app.post('/simulator/run/{run_id}/advance', response_model=list[SimulationEventResponse])
def advance_simulation_run(run_id: str, payload: SimulationAdvanceRequest) -> list[SimulationEventResponse]:
    events = simulator.advance(run_id, duration_hours=payload.duration_hours)
    return [SimulationEventResponse.model_validate(event) for event in events]


@app.post('/simulator/run/{run_id}/reset', response_model=ScenarioRunResponse)
def reset_simulation_run(run_id: str) -> ScenarioRunResponse:
    run = simulator.reset(run_id)
    return ScenarioRunResponse(
        id=run.id,
        config={
            'seed': run.config.seed,
            'start_time': run.config.start_time,
            'scenario_version': run.config.scenario_version,
            'organization_name': run.config.organization_name,
        },
        clock=run.clock,
        event_count=len(run.events),
    )


@app.get('/simulator/run/{run_id}/replay', response_model=list[SimulationEventResponse])
def replay_simulation_run(run_id: str) -> list[SimulationEventResponse]:
    events = simulator.replay(run_id)
    return [SimulationEventResponse.model_validate(event) for event in events]


class AgentTaskRequest(BaseModel):
    task_type: str
    context: dict[str, object]


@app.post('/organizations/{organization_id}/agent-tasks', response_model=AgentTaskRead)
def create_agent_task(
    organization_id: int,
    payload: AgentTaskRequest,
    db: Session = Depends(get_db),
) -> AgentTaskRead:
    service = DomainService(db)
    task_id = str(uuid.uuid4())
    task = service.create_agent_task(organization_id, task_id, payload.task_type, payload.context)
    db.commit()
    return AgentTaskRead.model_validate(task)


@app.get('/organizations/{organization_id}/agent-tasks', response_model=list[AgentTaskRead])
def list_agent_tasks(
    organization_id: int,
    db: Session = Depends(get_db),
) -> list[AgentTaskRead]:
    service = DomainService(db)
    tasks = service.list_agent_tasks(organization_id)
    return [AgentTaskRead.model_validate(task) for task in tasks]


@app.post('/organizations/{organization_id}/agent-tasks/{task_id}/run', response_model=AgentTaskRead)
def run_agent_task(
    organization_id: int,
    task_id: str,
    db: Session = Depends(get_db),
) -> AgentTaskRead:
    service = DomainService(db)
    task_record = service.get_agent_task(task_id)
    if not task_record:
        raise ValueError(f'Task {task_id} not found')

    context = json.loads(task_record.context)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    async def execute_task() -> None:
        agent = CollectionsAgent(gateway=get_model_gateway())
        task_obj = CollectionsAgentTask(
            id=task_id,
            task_type=task_record.task_type,
            context=context,
        )
        result = await agent.run_task(task_obj)

        for model_call in result.model_calls:
            service.add_model_call(
                task_id,
                model_call['provider'],
                model_call['prompt_length'],
                model_call['response'],
                model_call['stop_reason'],
                model_call['cost_usd'],
            )

        for tool_call in result.tool_calls:
            service.add_tool_call(
                task_id,
                tool_call.name,
                tool_call.args,
                tool_call.idempotency_key,
            )

        service.update_agent_task(task_id, result.status, result.result, result.error)
        db.commit()

    if loop:
        loop.run_until_complete(execute_task())
    else:
        asyncio.run(execute_task())

    updated_task = service.get_agent_task(task_id)
    return AgentTaskRead.model_validate(updated_task)


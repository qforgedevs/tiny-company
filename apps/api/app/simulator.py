from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import random
from typing import Any


@dataclass(frozen=True)
class ScenarioConfig:
    seed: int = 48172
    start_time: str = '2026-01-01T08:00:00Z'
    scenario_version: str = 'v1'
    organization_name: str = 'Tiny Academy'


@dataclass
class SimulationEvent:
    event_id: str
    kind: str
    occurred_at: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulationRun:
    id: str
    config: ScenarioConfig
    clock: str
    events: list[SimulationEvent] = field(default_factory=list)
    schedule: list[SimulationEvent] = field(default_factory=list)


class DeterministicSimulator:
    def __init__(self) -> None:
        self._runs: dict[str, SimulationRun] = {}

    def create_run(self, config: ScenarioConfig | None = None) -> SimulationRun:
        scenario = config or ScenarioConfig()
        run_id = f"run-{scenario.seed}-{scenario.start_time}-{scenario.scenario_version}"
        run = SimulationRun(id=run_id, config=scenario, clock=scenario.start_time)
        self._runs[run.id] = run
        return run

    def _generate_events(self, run: SimulationRun, duration_hours: int) -> list[SimulationEvent]:
        rng = random.Random(run.config.seed)
        base_time = datetime.fromisoformat(run.clock.replace('Z', '+00:00'))
        events: list[SimulationEvent] = []
        step_count = max(1, duration_hours // 2)

        for index in range(step_count):
            delta = timedelta(hours=index * 2)
            at_time = base_time + delta
            kind = ['monthly_charge_due', 'bank_transaction_arrived', 'customer_receipt_uploaded', 'customer_message_received'][index % 4]
            event = SimulationEvent(
                event_id=f"evt-{run.id}-{index}",
                kind=kind,
                occurred_at=at_time.isoformat().replace('+00:00', 'Z'),
                details={
                    'seed': run.config.seed,
                    'customer_id': int(rng.randint(1, 5)),
                    'amount_cents': int(rng.randint(12000, 20000)),
                    'label': f'{kind}-{index}',
                },
            )
            events.append(event)

        return events

    def advance(self, run_id: str, duration_hours: int = 8) -> list[SimulationEvent]:
        run = self._runs[run_id]
        events = self._generate_events(run, duration_hours)
        run.events.extend(events)
        run.schedule.extend(events)
        run.clock = (datetime.fromisoformat(run.clock.replace('Z', '+00:00')) + timedelta(hours=duration_hours)).isoformat().replace('+00:00', 'Z')
        return events

    def reset(self, run_id: str) -> SimulationRun:
        run = self._runs[run_id]
        run.clock = run.config.start_time
        run.events.clear()
        run.schedule.clear()
        return run

    def replay(self, run_id: str) -> list[SimulationEvent]:
        run = self._runs[run_id]
        return [event for event in run.schedule]

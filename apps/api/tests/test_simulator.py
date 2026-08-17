from app.simulator import DeterministicSimulator, ScenarioConfig


def test_same_seed_yields_same_event_schedule() -> None:
    simulator_a = DeterministicSimulator()
    simulator_b = DeterministicSimulator()

    run_a = simulator_a.create_run(ScenarioConfig(seed=48172, start_time='2026-01-01T08:00:00Z'))
    run_b = simulator_b.create_run(ScenarioConfig(seed=48172, start_time='2026-01-01T08:00:00Z'))

    events_a = simulator_a.advance(run_a.id, duration_hours=8)
    events_b = simulator_b.advance(run_b.id, duration_hours=8)

    assert [event.kind for event in events_a] == [event.kind for event in events_b]
    assert [event.details for event in events_a] == [event.details for event in events_b]
    assert run_a.clock == run_b.clock


def test_reset_clears_schedule_and_replays_empty_state() -> None:
    simulator = DeterministicSimulator()
    run = simulator.create_run(ScenarioConfig(seed=99, start_time='2026-01-01T08:00:00Z'))
    simulator.advance(run.id, duration_hours=8)

    simulator.reset(run.id)

    assert run.clock == '2026-01-01T08:00:00Z'
    assert run.events == []
    assert run.schedule == []
    assert simulator.replay(run.id) == []


def test_advance_tracks_clock_and_event_ids() -> None:
    simulator = DeterministicSimulator()
    run = simulator.create_run(ScenarioConfig(seed=321, start_time='2026-01-01T08:00:00Z'))

    events = simulator.advance(run.id, duration_hours=4)

    assert len(events) >= 1
    assert run.clock == '2026-01-01T12:00:00Z'
    assert all(event.event_id.startswith('evt-') for event in events)

'use client';

import { useMemo, useState } from 'react';
import { advanceRun, createScenarioRun, getRun, resetRun, type ScenarioRun, type SimulationEvent } from './lib/api';

const defaultScenario = {
  seed: 48172,
  start_time: '2026-01-01T08:00:00Z',
  scenario_version: 'v1',
  organization_name: 'Tiny Academy',
};

export function OperationsDashboard() {
  const [scenario, setScenario] = useState(defaultScenario);
  const [run, setRun] = useState<ScenarioRun | null>(null);
  const [events, setEvents] = useState<SimulationEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sections = useMemo(
    () => ['scenario', 'inbox', 'customers', 'charges', 'transactions', 'cases', 'audit'],
    []
  );

  async function handleCreateRun() {
    setLoading(true);
    setError(null);

    try {
      const created = await createScenarioRun(scenario);
      setRun(created);
      const nextEvents = await advanceRun(created.id, 4);
      setEvents(nextEvents);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create scenario');
    } finally {
      setLoading(false);
    }
  }

  async function handleAdvance() {
    if (!run) return;
    setLoading(true);
    try {
      const nextEvents = await advanceRun(run.id, 4);
      setEvents(nextEvents);
      const refreshed = await getRun(run.id);
      setRun(refreshed);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not advance the run');
    } finally {
      setLoading(false);
    }
  }

  async function handleReset() {
    if (!run) return;
    setLoading(true);
    try {
      const resetRunState = await resetRun(run.id);
      setRun(resetRunState);
      setEvents([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not reset the run');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ padding: 32, fontFamily: 'sans-serif' }}>
      <h1>Tiny Company</h1>
      <p>Operations dashboard</p>

      <section aria-label="scenario" style={{ marginBottom: 24 }}>
        <h2>Scenario</h2>
        <label>
          Seed
          <input
            type="number"
            value={scenario.seed}
            onChange={(event) => setScenario({ ...scenario, seed: Number(event.target.value) })}
          />
        </label>
        <button onClick={handleCreateRun} disabled={loading}>
          {loading ? 'Working...' : 'Create scenario'}
        </button>
        {run ? (
          <div>
            <p>Run ID: {run.id}</p>
            <p>Clock: {run.clock}</p>
            <button onClick={handleAdvance}>Advance time</button>
            <button onClick={handleReset}>Reset</button>
          </div>
        ) : null}
      </section>

      {error ? <p role="alert">{error}</p> : null}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16 }}>
        {sections.map((section) => (
          <div key={section} style={{ border: '1px solid #ccc', padding: 12, borderRadius: 8 }}>
            <strong>{section}</strong>
          </div>
        ))}
      </div>

      <section aria-label="inbox" style={{ marginTop: 24 }}>
        <h2>Inbox</h2>
        {events.length === 0 ? <p>No events yet.</p> : (
          <ul>
            {events.map((event) => (
              <li key={event.event_id}>
                {event.kind} — {event.occurred_at}
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}

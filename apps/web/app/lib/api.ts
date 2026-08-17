const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export type ScenarioConfigInput = {
  seed: number;
  start_time: string;
  scenario_version?: string;
  organization_name?: string;
};

export type ScenarioRun = {
  id: string;
  config: {
    seed: number;
    start_time: string;
    scenario_version: string;
    organization_name: string;
  };
  clock: string;
  event_count: number;
};

export type SimulationEvent = {
  event_id: string;
  kind: string;
  occurred_at: string;
  details: Record<string, unknown>;
};

export async function createScenarioRun(payload: ScenarioConfigInput): Promise<ScenarioRun> {
  const response = await fetch(`${API_BASE_URL}/simulator/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Failed to create scenario: ${response.status}`);
  }

  return response.json();
}

export async function advanceRun(runId: string, durationHours: number): Promise<SimulationEvent[]> {
  const response = await fetch(`${API_BASE_URL}/simulator/run/${runId}/advance`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ duration_hours: durationHours }),
  });

  if (!response.ok) {
    throw new Error(`Failed to advance run: ${response.status}`);
  }

  return response.json();
}

export async function resetRun(runId: string): Promise<ScenarioRun> {
  const response = await fetch(`${API_BASE_URL}/simulator/run/${runId}/reset`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error(`Failed to reset run: ${response.status}`);
  }

  return response.json();
}

export async function getRun(runId: string): Promise<ScenarioRun> {
  const response = await fetch(`${API_BASE_URL}/simulator/run/${runId}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch run: ${response.status}`);
  }

  return response.json();
}

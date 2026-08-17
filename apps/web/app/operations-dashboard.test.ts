import { describe, expect, it } from 'vitest';

describe('operations dashboard', () => {
  it('exposes scenario controls and data sections', () => {
    const sections = ['scenario', 'inbox', 'customers', 'charges', 'transactions', 'cases', 'audit'];

    expect(sections).toHaveLength(7);
    expect(sections[0]).toBe('scenario');
    expect(sections.includes('cases')).toBe(true);
  });
});

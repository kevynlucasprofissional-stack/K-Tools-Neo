import { describe, it, expect } from 'vitest';
import { isValidKToolsConnection } from './validation';
import { type Node } from '@xyflow/react';

describe('isValidKToolsConnection', () => {
  const nodes: Node[] = [
    {
      id: 'node-1',
      position: { x: 0, y: 0 },
      data: {
        outputs: [{ id: 'out1', type: 'file' }, { id: 'out2', type: 'audio' }],
      },
    },
    {
      id: 'node-2',
      position: { x: 0, y: 0 },
      data: {
        inputs: [{ id: 'in1', type: 'file' }, { id: 'in2', type: 'audio' }, { id: 'in3', type: 'video' }],
      },
    },
  ];

  it('allows exact type match', () => {
    expect(
      isValidKToolsConnection({ source: 'node-1', target: 'node-2', sourceHandle: 'out1', targetHandle: 'in1' }, nodes)
    ).toBe(true);
    expect(
      isValidKToolsConnection({ source: 'node-1', target: 'node-2', sourceHandle: 'out2', targetHandle: 'in2' }, nodes)
    ).toBe(true);
  });

  it('allows subtype casting to file', () => {
    // audio can be connected to file
    expect(
      isValidKToolsConnection({ source: 'node-1', target: 'node-2', sourceHandle: 'out2', targetHandle: 'in1' }, nodes)
    ).toBe(true);
  });

  it('rejects incompatible types', () => {
    // file cannot be connected to audio
    expect(
      isValidKToolsConnection({ source: 'node-1', target: 'node-2', sourceHandle: 'out1', targetHandle: 'in2' }, nodes)
    ).toBe(false);
  });
});

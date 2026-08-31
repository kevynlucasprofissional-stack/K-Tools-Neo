import { type Node, type Edge } from '@xyflow/react';

export const initialNodes: Node[] = [
  {
    id: 'node-1',
    type: 'ktool',
    position: { x: 250, y: 100 },
    data: {
      label: 'Read File',
      category: 'Data',
      inputs: [],
      outputs: [{ id: 'out1', type: 'file', label: 'File Data' }],
      config: { filePath: '/tmp/test.txt' },
      runState: 'IDLE' // IDLE, RUNNING, SUCCESS, ERROR, CACHED
    },
  },
  {
    id: 'node-2',
    type: 'ktool',
    position: { x: 500, y: 100 },
    data: {
      label: 'Extract Audio',
      category: 'Audio',
      inputs: [{ id: 'in1', type: 'file', label: 'Video File' }],
      outputs: [{ id: 'out1', type: 'audio', label: 'Audio Stream' }],
      config: { format: 'mp3' },
      runState: 'IDLE'
    },
  },
  {
    id: 'node-3',
    type: 'missing',
    position: { x: 750, y: 200 },
    data: {
      originalType: 'community.video.unknown-node',
      label: 'Missing Node Placeholder',
      config: { magic_value: 42 },
      inputs: [{ id: 'in1', type: 'audio', label: 'Audio' }],
      outputs: [{ id: 'out1', type: 'video', label: 'Video' }]
    },
  },
];

export const initialEdges: Edge[] = [
  { id: 'e1-2', source: 'node-1', target: 'node-2', sourceHandle: 'out1', targetHandle: 'in1' },
];

export const nodeCatalog = [
    {
        type: 'ktool',
        label: 'Read File',
        category: 'System',
        defaultData: {
            label: 'Read File',
            inputs: [],
            outputs: [{ id: 'out1', type: 'file', label: 'File' }],
            config: { path: '' }
        }
    },
    {
        type: 'ktool',
        label: 'Text Concat',
        category: 'Text',
        defaultData: {
            label: 'Text Concat',
            inputs: [{ id: 'in1', type: 'text', label: 'Text 1' }, { id: 'in2', type: 'text', label: 'Text 2' }],
            outputs: [{ id: 'out1', type: 'text', label: 'Result' }],
            config: { separator: ' ' }
        }
    },
    {
        type: 'ktool',
        label: 'Extract Audio',
        category: 'Media',
        defaultData: {
            label: 'Extract Audio',
            inputs: [{ id: 'in1', type: 'file', label: 'Video/File' }],
            outputs: [{ id: 'out1', type: 'audio', label: 'Audio' }],
            config: { format: 'wav' }
        }
    }
]

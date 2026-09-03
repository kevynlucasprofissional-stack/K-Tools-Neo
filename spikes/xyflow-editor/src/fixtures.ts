import { type Node, type Edge } from '@xyflow/react';
import catalogData from './catalog.json';

export const nodeCatalog = catalogData;

export const initialNodes: Node[] = [
  {
    id: 'node-1',
    type: 'ktool',
    position: { x: 80, y: 140 },
    data: {
      type_id: 'folder.literal',
      label: 'Pasta',
      category: 'Files',
      inputs: [],
      outputs: [{ id: 'folder', type: 'folder', label: 'pasta' }],
      config: { path: 'C:/Midias' },
      runState: 'IDLE',
    },
  },
  {
    id: 'node-2',
    type: 'ktool',
    position: { x: 380, y: 120 },
    data: {
      type_id: 'folder.scan_files',
      label: 'Scan Folder Files',
      category: 'Files',
      inputs: [{ id: 'folder', type: 'folder', label: 'folder' }],
      outputs: [
        { id: 'files', type: 'files', label: 'files' },
        { id: 'report', type: 'json', label: 'report' },
      ],
      config: { recursive: true, extensions: 'mp4,mkv,avi' },
      runState: 'IDLE',
    },
  },
  {
    id: 'node-3',
    type: 'ktool',
    position: { x: 720, y: 120 },
    data: {
      type_id: 'media.extract_audio',
      label: 'Extract Audio',
      category: 'Media',
      inputs: [{ id: 'file', type: 'file', label: 'file' }],
      outputs: [{ id: 'audio', type: 'file', label: 'audio' }],
      config: { format: 'wav', sample_rate: 44100 },
      runState: 'IDLE',
    },
  },
  {
    id: 'node-4',
    type: 'ktool',
    position: { x: 1040, y: 120 },
    data: {
      type_id: 'media.convert_lossless_alac',
      label: 'Convert to Lossless ALAC',
      category: 'Media',
      inputs: [{ id: 'file', type: 'file', label: 'file' }],
      outputs: [{ id: 'output_file', type: 'file', label: 'output_file' }],
      config: { keep_source: true },
      runState: 'IDLE',
    },
  },
];

export const initialEdges: Edge[] = [
  {
    id: 'e1-2',
    source: 'node-1',
    target: 'node-2',
    sourceHandle: 'folder',
    targetHandle: 'folder',
    animated: true,
    style: { stroke: '#eab308', strokeWidth: 2 },
  },
  {
    id: 'e2-3',
    source: 'node-2',
    target: 'node-3',
    sourceHandle: 'files',
    targetHandle: 'file',
    animated: true,
    style: { stroke: '#38bdf8', strokeWidth: 2 },
  },
  {
    id: 'e3-4',
    source: 'node-3',
    target: 'node-4',
    sourceHandle: 'audio',
    targetHandle: 'file',
    animated: true,
    style: { stroke: '#38bdf8', strokeWidth: 2 },
  },
];

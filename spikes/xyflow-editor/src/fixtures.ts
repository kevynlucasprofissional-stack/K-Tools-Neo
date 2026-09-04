import { type Node, type Edge } from '@xyflow/react';
import catalogData from './catalog.json';
import { WORKFLOW_PRESETS } from './presets';

export const nodeCatalog = catalogData;

// Default initial workflow is the flagship YouTube/Videos to Drive workflow
export const initialNodes: Node[] = WORKFLOW_PRESETS[0].nodes;
export const initialEdges: Edge[] = WORKFLOW_PRESETS[0].edges;

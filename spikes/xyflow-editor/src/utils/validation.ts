import { type Connection, type Node, type Edge } from '@xyflow/react';

// Strict typing validation
export function isValidKToolsConnection(connection: Connection | Edge, nodes: Node[]) {
  const sourceNode = nodes.find((n) => n.id === connection.source);
  const targetNode = nodes.find((n) => n.id === connection.target);

  if (!sourceNode || !targetNode) return false;

  const sourceOutput = (sourceNode.data?.outputs as any[])?.find((o: any) => o.id === connection.sourceHandle);
  const targetInput = (targetNode.data?.inputs as any[])?.find((i: any) => i.id === connection.targetHandle);

  if (!sourceOutput || !targetInput) return false;

  // Simple rule: exact type match, or 'file' can accept 'audio'/'video' (as an example of subtype casting)
  if (sourceOutput.type === targetInput.type) {
      return true;
  }
  
  if (targetInput.type === 'file' && ['audio', 'video', 'text'].includes(sourceOutput.type)) {
      return true;
  }

  console.warn(`Invalid connection: Cannot connect ${sourceOutput.type} to ${targetInput.type}`);
  return false;
}

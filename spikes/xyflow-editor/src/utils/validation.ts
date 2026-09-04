import { type Connection, type Node, type Edge } from '@xyflow/react';

// Strict typing validation
export function isValidKToolsConnection(connection: Connection | Edge, nodes: Node[]) {
  const sourceNode = nodes.find((n) => n.id === connection.source);
  const targetNode = nodes.find((n) => n.id === connection.target);

  if (!sourceNode || !targetNode) return false;
  if (connection.source === connection.target) return false;

  const sourceOutput = (sourceNode.data?.outputs as any[])?.find((o: any) => o.id === connection.sourceHandle);
  const targetInput = (targetNode.data?.inputs as any[])?.find((i: any) => i.id === connection.targetHandle);

  if (!sourceOutput || !targetInput) return false;

  const srcType = (sourceOutput.type || 'any').toLowerCase();
  const tgtType = (targetInput.type || 'any').toLowerCase();

  // If either port is 'any', allow connection
  if (srcType === 'any' || tgtType === 'any') {
    return true;
  }

  // Exact match
  if (srcType === tgtType) {
    return true;
  }

  // File collection equivalence (files <-> file_set)
  if (
    (srcType === 'files' || srcType === 'file_set') &&
    (tgtType === 'files' || tgtType === 'file_set')
  ) {
    return true;
  }

  // Media subtype casting to 'file'
  if (tgtType === 'file' && ['audio', 'video', 'image', 'pdf', 'text', 'files', 'file_set'].includes(srcType)) {
    return true;
  }

  // Connecting single file into file collection receiver
  if ((tgtType === 'files' || tgtType === 'file_set') && ['file', 'audio', 'video', 'image', 'pdf', 'text'].includes(srcType)) {
    return true;
  }

  console.warn(`Conexão incompatível: Não é possível ligar ${sourceOutput.label || srcType} em ${targetInput.label || tgtType}`);
  return false;
}

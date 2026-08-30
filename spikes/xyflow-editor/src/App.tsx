import { useState, useCallback } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
  Node,
  Edge,
  NodeChange,
  EdgeChange,
  Connection,
  ReactFlowProvider,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { KToolNode, MissingNode } from './components/nodes';
import { Inspector } from './components/Inspector';
import { Palette } from './components/Palette';

// Fixture Data
import { initialNodes, initialEdges } from './fixtures';
import { isValidKToolsConnection } from './utils/validation';

import './App.css';

const nodeTypes = {
  ktool: KToolNode,
  missing: MissingNode,
};

function FlowEditor() {
  const [nodes, setNodes] = useState<Node[]>(initialNodes);
  const [edges, setEdges] = useState<Edge[]>(initialEdges);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => {
      setNodes((nds) => applyNodeChanges(changes, nds));
      const selectionChange = changes.find((c) => c.type === 'select');
      if (selectionChange && selectionChange.type === 'select') {
        const node = nodes.find((n) => n.id === selectionChange.id);
        if (selectionChange.selected && node) {
          setSelectedNode(node);
        } else if (!selectionChange.selected && selectedNode?.id === selectionChange.id) {
          setSelectedNode(null);
        }
      }
    },
    [nodes, selectedNode]
  );

  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );

  const onConnect = useCallback(
    (connection: Connection) => {
      if (isValidKToolsConnection(connection, nodes)) {
        setEdges((eds) => addEdge({ ...connection, markerEnd: { type: MarkerType.ArrowClosed } }, eds));
      }
    },
    [nodes]
  );

  const onNodeUpdate = useCallback((nodeId: string, data: any) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === nodeId) {
          return { ...node, data: { ...node.data, ...data } };
        }
        return node;
      })
    );
    if (selectedNode && selectedNode.id === nodeId) {
       setSelectedNode((prev) => prev ? { ...prev, data: { ...prev.data, ...data } } : null);
    }
  }, [selectedNode]);

  const onAddNode = useCallback((type: string, nodeData: any) => {
    const newNode: Node = {
      id: `node-${Date.now()}`,
      type: type,
      position: { x: Math.random() * 200 + 100, y: Math.random() * 200 + 100 },
      data: nodeData,
    };
    setNodes((nds) => [...nds, newNode]);
  }, []);

  const simulateRun = () => {
    // Simple state machine for simulation
    const runStates = ['RUNNING', 'SUCCESS', 'ERROR'];
    
    setNodes((nds) => nds.map((n, i) => {
        if(n.type === 'missing') return { ...n, data: { ...n.data, runState: 'ERROR' }};
        return { ...n, data: { ...n.data, runState: 'RUNNING' } };
    }));

    setTimeout(() => {
        setNodes((nds) => nds.map((n, i) => {
            if(n.type === 'missing') return n;
            return { ...n, data: { ...n.data, runState: i % 3 === 0 ? 'ERROR' : 'SUCCESS' } };
        }));
    }, 2000);
  };

  const clearRunState = () => {
      setNodes((nds) => nds.map(n => ({ ...n, data: { ...n.data, runState: 'IDLE' } })));
  }

  return (
    <div className="editor-layout">
      <div className="sidebar">
        <Palette onAddNode={onAddNode} />
      </div>
      <div className="canvas-container">
        <div className="toolbar">
            <button onClick={simulateRun}>Simulate Run</button>
            <button onClick={clearRunState}>Clear State</button>
        </div>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          isValidConnection={(conn) => isValidKToolsConnection(conn, nodes)}
          fitView
          keyboardEnabled={true}
        >
          <Background />
          <Controls />
        </ReactFlow>
      </div>
      <div className="inspector-panel">
        <Inspector selectedNode={selectedNode} onNodeUpdate={onNodeUpdate} />
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ReactFlowProvider>
      <FlowEditor />
    </ReactFlowProvider>
  );
}

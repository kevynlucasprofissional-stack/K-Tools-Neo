import { useState, useCallback } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  MiniMap,
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
  ReactFlowProvider,
  MarkerType,
  type Node,
  type Edge,
  type NodeChange,
  type EdgeChange,
  type Connection,
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
  const [isRunning, setIsRunning] = useState<boolean>(false);

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
    (connection: Connection | Edge) => {
      if (isValidKToolsConnection(connection, nodes)) {
        setEdges((eds) =>
          addEdge(
            {
              ...connection,
              animated: true,
              style: { stroke: '#38bdf8', strokeWidth: 2 },
              markerEnd: { type: MarkerType.ArrowClosed, color: '#38bdf8' },
            } as Edge | Connection,
            eds
          )
        );
      }
    },
    [nodes]
  );

  const onNodeUpdate = useCallback(
    (nodeId: string, data: any) => {
      setNodes((nds) =>
        nds.map((node) => {
          if (node.id === nodeId) {
            return { ...node, data: { ...node.data, ...data } };
          }
          return node;
        })
      );
      if (selectedNode && selectedNode.id === nodeId) {
        setSelectedNode((prev) => (prev ? { ...prev, data: { ...prev.data, ...data } } : null));
      }
    },
    [selectedNode]
  );

  const onAddNode = useCallback((type: string, nodeData: any) => {
    const newNode: Node = {
      id: `node-${Date.now()}`,
      type: type,
      position: { x: Math.random() * 250 + 200, y: Math.random() * 250 + 150 },
      data: {
        ...nodeData,
        runState: 'IDLE',
      },
    };
    setNodes((nds) => [...nds, newNode]);
  }, []);

  const simulateRun = () => {
    setIsRunning(true);
    // Transiciona todos os nos para RUNNING
    setNodes((nds) =>
      nds.map((n) => {
        if (n.type === 'missing') return { ...n, data: { ...n.data, runState: 'ERROR' } };
        return { ...n, data: { ...n.data, runState: 'RUNNING' } };
      })
    );

    setTimeout(() => {
      setNodes((nds) =>
        nds.map((n, i) => {
          if (n.type === 'missing') return n;
          return {
            ...n,
            data: {
              ...n.data,
              runState: i % 4 === 0 ? 'CACHED' : 'SUCCESS',
            },
          };
        })
      );
      setIsRunning(false);
    }, 1500);
  };

  const clearRunState = () => {
    setIsRunning(false);
    setNodes((nds) => nds.map((n) => ({ ...n, data: { ...n.data, runState: 'IDLE' } })));
  };

  const exportWorkflowJson = () => {
    const payload = {
      version: '1.0.0',
      nodes: nodes.map((n) => ({
        id: n.id,
        type: n.type,
        type_id: n.data.type_id || n.data.label,
        position: n.position,
        config: n.data.config || {},
      })),
      edges: edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle,
        targetHandle: e.targetHandle,
      })),
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ktools-workflow-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="app-container">
      {/* Top Navbar */}
      <header className="top-navbar">
        <div className="brand-section">
          <div className="brand-logo">
            <span style={{ fontSize: '18px', filter: 'drop-shadow(0 0 6px #38bdf8)' }}>⚡</span>
            <span>K-Tools Neo</span>
          </div>
          <span className="brand-badge">Workflow Studio</span>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '11px',
              color: '#10b981',
              background: 'rgba(16, 185, 129, 0.12)',
              padding: '3px 9px',
              borderRadius: '12px',
              border: '1px solid rgba(16, 185, 129, 0.25)',
              marginLeft: '12px',
            }}
          >
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10b981' }} />
            <span>34 Nós Registrados (M0-M5 Ativos)</span>
          </div>
        </div>

        <div className="navbar-actions">
          <button
            className="btn btn-primary"
            onClick={simulateRun}
            disabled={isRunning}
            style={{ opacity: isRunning ? 0.7 : 1 }}
          >
            <span>{isRunning ? '⏳' : '▶'}</span>
            <span>{isRunning ? 'Executando...' : 'Executar Workflow'}</span>
          </button>
          <button className="btn btn-secondary" onClick={clearRunState}>
            <span>🔄</span>
            <span>Limpar Estado</span>
          </button>
          <button className="btn btn-secondary" onClick={exportWorkflowJson}>
            <span>📥</span>
            <span>Exportar JSON</span>
          </button>
        </div>
      </header>

      {/* Editor Layout: Palette + Canvas + Inspector */}
      <div className="editor-layout">
        {/* Left: Palette */}
        <aside className="sidebar">
          <Palette onAddNode={onAddNode} />
        </aside>

        {/* Center: ReactFlow Canvas */}
        <main className="canvas-container">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            isValidConnection={(conn) => isValidKToolsConnection(conn, nodes)}
            fitView
          >
            <Background color="#1e293b" gap={20} size={1.2} />
            <Controls />
            <MiniMap
              nodeColor={(n) => {
                if (n.data?.runState === 'RUNNING') return '#f59e0b';
                if (n.data?.runState === 'SUCCESS') return '#10b981';
                if (n.data?.runState === 'ERROR') return '#ef4444';
                if (n.data?.runState === 'CACHED') return '#06b6d4';
                return '#38bdf8';
              }}
              maskColor="rgba(9, 13, 22, 0.75)"
            />
          </ReactFlow>
        </main>

        {/* Right: Inspector */}
        <aside className="inspector-panel">
          <Inspector
            key={selectedNode?.id || 'empty'}
            selectedNode={selectedNode}
            onNodeUpdate={onNodeUpdate}
          />
        </aside>
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

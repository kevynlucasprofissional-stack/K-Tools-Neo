import { useState, useCallback, useEffect, useRef } from 'react';
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
  useReactFlow,
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
import { QuickSearch } from './components/QuickSearch';
import { BottomConsole, type LogEntry } from './components/BottomConsole';
import { WORKFLOW_PRESETS } from './presets';

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
  const [workflowTitle, setWorkflowTitle] = useState<string>('Pipeline de Processamento de Mídia');
  const [isEditingTitle, setIsEditingTitle] = useState<boolean>(false);
  const [isSearchOpen, setIsSearchOpen] = useState<boolean>(false);
  const [isConsoleOpen, setIsConsoleOpen] = useState<boolean>(true);
  const [logs, setLogs] = useState<LogEntry[]>([
    {
      id: 'log-init',
      timestamp: new Date().toLocaleTimeString(),
      level: 'info',
      message: 'K-Tools Neo Engine inicializado. 34 nós prontos no monorepo.',
    },
    {
      id: 'log-ready',
      timestamp: new Date().toLocaleTimeString(),
      level: 'success',
      message: 'Ambiente pronto. Arraste nós da paleta ou pressione Barra de Espaço para buscar.',
    },
  ]);

  const { screenToFlowPosition, fitView } = useReactFlow();
  const reactFlowWrapper = useRef<HTMLDivElement>(null);

  const addLog = (level: LogEntry['level'], message: string, nodeId?: string) => {
    setLogs((prev) => [
      ...prev,
      {
        id: `log-${Date.now()}-${Math.random()}`,
        timestamp: new Date().toLocaleTimeString(),
        level,
        message,
        nodeId,
      },
    ]);
  };

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
        addLog('info', `Conexão estabelecida: ${connection.source} -> ${connection.target}`);
      } else {
        addLog('warn', `Conexão rejeitada: tipos de portas incompatíveis.`);
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
      addLog('info', `Configurações atualizadas para o nó [${nodeId}].`, nodeId);
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
    addLog('info', `Nó adicionado ao canvas: ${nodeData.label}`, newNode.id);
  }, []);

  // HTML5 Drag and Drop handlers
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      const raw = event.dataTransfer.getData('application/reactflow');
      if (!raw) return;
      try {
        const { type, data } = JSON.parse(raw);
        const position = screenToFlowPosition({
          x: event.clientX,
          y: event.clientY,
        });
        const newNode: Node = {
          id: `node-${Date.now()}`,
          type,
          position,
          data: {
            ...data,
            runState: 'IDLE',
          },
        };
        setNodes((nds) => [...nds, newNode]);
        addLog('info', `Nó solto no canvas: ${data.label}`, newNode.id);
      } catch (err) {
        console.error('Failed to drop node:', err);
      }
    },
    [screenToFlowPosition]
  );

  // Global Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignorar se estiver digitando em input ou textarea
      if (
        document.activeElement?.tagName === 'INPUT' ||
        document.activeElement?.tagName === 'TEXTAREA'
      ) {
        return;
      }

      if (e.key === ' ' || e.key === '/') {
        e.preventDefault();
        setIsSearchOpen(true);
      } else if (e.key === 'Delete' || e.key === 'Backspace') {
        if (selectedNode) {
          setNodes((nds) => nds.filter((n) => n.id !== selectedNode.id));
          setEdges((eds) => eds.filter((e) => e.source !== selectedNode.id && e.target !== selectedNode.id));
          addLog('warn', `Nó removido do fluxo: ${selectedNode.data.label}`, selectedNode.id);
          setSelectedNode(null);
        }
      } else if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault();
        simulateRun();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedNode]);

  const simulateRun = () => {
    if (isRunning) return;
    setIsRunning(true);
    setIsConsoleOpen(true);
    addLog('info', `Iniciando execução do workflow "${workflowTitle}" (${nodes.length} nós, ${edges.length} conexões)...`);

    // Iniciar nos em ordem
    setNodes((nds) =>
      nds.map((n) => {
        if (n.type === 'missing') return { ...n, data: { ...n.data, runState: 'ERROR' } };
        return { ...n, data: { ...n.data, runState: 'RUNNING' } };
      })
    );

    nodes.forEach((n, idx) => {
      setTimeout(() => {
        addLog('exec', `Processando nó: ${n.data.label} [${n.data.type_id || n.id}]...`, n.id);
      }, (idx + 1) * 350);
    });

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
      addLog('success', `Execução concluída com sucesso! Todos os nós finalizaram sem falhas.`);
    }, nodes.length * 350 + 600);
  };

  const clearRunState = () => {
    setIsRunning(false);
    setNodes((nds) => nds.map((n) => ({ ...n, data: { ...n.data, runState: 'IDLE' } })));
    addLog('info', 'Status de execução resetado para IDLE.');
  };

  const loadPreset = (presetId: string) => {
    const preset = WORKFLOW_PRESETS.find((p) => p.id === presetId);
    if (!preset) return;
    setNodes(preset.nodes);
    setEdges(preset.edges);
    setWorkflowTitle(preset.name);
    setSelectedNode(null);
    addLog('info', `Modelo carregado: "${preset.name}".`);
    setTimeout(() => fitView({ padding: 0.2 }), 100);
  };

  const exportWorkflowJson = () => {
    const payload = {
      version: '1.0.0',
      title: workflowTitle,
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
    a.download = `${workflowTitle.toLowerCase().replace(/\s+/g, '-')}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    addLog('success', 'Arquivo JSON do workflow exportado com sucesso.');
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
          <span className="brand-badge">Studio</span>

          {/* Workflow Title input */}
          <div style={{ marginLeft: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            {isEditingTitle ? (
              <input
                type="text"
                value={workflowTitle}
                onChange={(e) => setWorkflowTitle(e.target.value)}
                onBlur={() => setIsEditingTitle(false)}
                onKeyDown={(e) => e.key === 'Enter' && setIsEditingTitle(false)}
                autoFocus
                style={{
                  background: '#090d16',
                  border: '1px solid #38bdf8',
                  borderRadius: '6px',
                  color: '#f8fafc',
                  fontSize: '12px',
                  fontWeight: 600,
                  padding: '4px 8px',
                  outline: 'none',
                }}
              />
            ) : (
              <span
                onClick={() => setIsEditingTitle(true)}
                style={{
                  fontSize: '12px',
                  fontWeight: 600,
                  color: '#cbd5e1',
                  cursor: 'pointer',
                  padding: '4px 8px',
                  borderRadius: '6px',
                  border: '1px solid transparent',
                  transition: 'all 0.15s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = '#334155';
                  e.currentTarget.style.background = '#0e1526';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'transparent';
                  e.currentTarget.style.background = 'transparent';
                }}
                title="Clique para renomear este fluxo"
              >
                📝 {workflowTitle}
              </span>
            )}
          </div>
        </div>

        {/* Navbar Center & Actions */}
        <div className="navbar-actions">
          {/* Presets dropdown */}
          <select
            onChange={(e) => e.target.value && loadPreset(e.target.value)}
            defaultValue=""
            style={{
              background: '#131b2e',
              border: '1px solid #1e293b',
              borderRadius: '8px',
              color: '#cbd5e1',
              fontSize: '11px',
              fontWeight: 600,
              padding: '6px 10px',
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            <option value="" disabled>
              📂 Carregar Modelo Pronto...
            </option>
            {WORKFLOW_PRESETS.map((p) => (
              <option key={p.id} value={p.id}>
                {p.icon} {p.name}
              </option>
            ))}
          </select>

          {/* Quick Search Button */}
          <button
            className="btn btn-secondary"
            onClick={() => setIsSearchOpen(true)}
            title="Atalho: Barra de Espaço ou /"
          >
            <span>🔍</span>
            <span>Buscar Nó</span>
            <span style={{ fontSize: '9px', opacity: 0.6, background: '#090d16', padding: '1px 4px', borderRadius: '3px' }}>
              Espaço
            </span>
          </button>

          {/* Run Button */}
          <button
            className="btn btn-primary"
            onClick={simulateRun}
            disabled={isRunning}
            style={{ opacity: isRunning ? 0.7 : 1 }}
            title="Atalho: Ctrl + Enter"
          >
            <span>{isRunning ? '⏳' : '▶'}</span>
            <span>{isRunning ? 'Executando...' : 'Executar Workflow'}</span>
          </button>

          {/* Clear Run */}
          <button className="btn btn-secondary" onClick={clearRunState} title="Limpar status de execução">
            <span>🔄</span>
            <span>Limpar</span>
          </button>

          {/* Export JSON */}
          <button className="btn btn-secondary" onClick={exportWorkflowJson} title="Exportar grafo em JSON">
            <span>📥</span>
            <span>Exportar</span>
          </button>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <div className="editor-layout">
        {/* Left: Palette */}
        <aside className="sidebar">
          <Palette onAddNode={onAddNode} />
        </aside>

        {/* Center: Canvas */}
        <main
          className="canvas-container"
          ref={reactFlowWrapper}
          onDragOver={onDragOver}
          onDrop={onDrop}
        >
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

          {/* Execution Console Drawer */}
          <BottomConsole
            logs={logs}
            onClearLogs={() => setLogs([])}
            isOpen={isConsoleOpen}
            onToggle={() => setIsConsoleOpen((prev) => !prev)}
          />
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

      {/* Quick Search Spotlight Modal */}
      <QuickSearch
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        onSelectNode={onAddNode}
      />
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

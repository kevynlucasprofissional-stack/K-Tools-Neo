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
import { ExecutionResultsModal, type ExecutionArtifact } from './components/ExecutionResultsModal';
import { WORKFLOW_PRESETS, type WorkflowPreset } from './presets';

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
  const [currentRunningStep, setCurrentRunningStep] = useState<number | null>(null);
  const [workflowTitle, setWorkflowTitle] = useState<string>(WORKFLOW_PRESETS[0].name);
  const [isEditingTitle, setIsEditingTitle] = useState<boolean>(false);
  const [isSearchOpen, setIsSearchOpen] = useState<boolean>(false);
  const [isConsoleOpen, setIsConsoleOpen] = useState<boolean>(false);
  const [isAdvancedMode, setIsAdvancedMode] = useState<boolean>(false);
  const [isResultsModalOpen, setIsResultsModalOpen] = useState<boolean>(false);
  const [activePreset, setActivePreset] = useState<WorkflowPreset>(WORKFLOW_PRESETS[0]);

  // Initial artifact preview matching the flagship preset
  const [lastArtifact, setLastArtifact] = useState<ExecutionArtifact | null>({
    fileName: WORKFLOW_PRESETS[0].expectedOutput.fileName,
    description: WORKFLOW_PRESETS[0].expectedOutput.description,
    path: WORKFLOW_PRESETS[0].expectedOutput.path,
    size: '84.6 MB',
    duration: '42 min 18 seg',
    format: 'WAV Áudio Sem Perdas (44.1 kHz / 16-bit)',
    sha256: '9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a109876543210fedcba9876543210',
  });

  const [logs, setLogs] = useState<LogEntry[]>([
    {
      id: 'log-init',
      timestamp: new Date().toLocaleTimeString(),
      level: 'info',
      message: 'K-Tools Neo Engine pronto. 39 capacidades ativas no monorepo.',
    },
    {
      id: 'log-ready',
      timestamp: new Date().toLocaleTimeString(),
      level: 'success',
      message: 'Modo Simples ativado. Conecte os blocos ou clique em "Executar Fluxo" para testar.',
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

  // Keep node data synchronized with isAdvancedMode
  const toggleAdvancedMode = () => {
    const next = !isAdvancedMode;
    setIsAdvancedMode(next);
    setNodes((nds) =>
      nds.map((n) => ({
        ...n,
        data: {
          ...n.data,
          isAdvancedMode: next,
        },
      }))
    );
    addLog('info', next ? 'Modo Avançado ativado (exibindo parâmetros técnicos e IDs).' : 'Modo Simples ativado (narrativo e simplificado).');
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
        addLog('info', `Passos conectados com sucesso!`);
      } else {
        addLog('warn', `Conexão incompatível: Verifique se o tipo de arquivo de saída bate com a entrada.`);
      }
    },
    [nodes]
  );

  const onNodeUpdate = useCallback(
    (nodeId: string, data: any) => {
      setNodes((nds) =>
        nds.map((node) => {
          if (node.id === nodeId) {
            return { ...node, data: { ...node.data, ...data, isAdvancedMode } };
          }
          return node;
        })
      );
      if (selectedNode && selectedNode.id === nodeId) {
        setSelectedNode((prev) => (prev ? { ...prev, data: { ...prev.data, ...data, isAdvancedMode } } : null));
      }
      addLog('info', `Configuração atualizada para o bloco [${nodeId}].`, nodeId);
    },
    [selectedNode, isAdvancedMode]
  );

  const onAddNode = useCallback(
    (type: string, nodeData: any) => {
      const newNode: Node = {
        id: `step-${Date.now()}`,
        type: type,
        position: { x: Math.random() * 200 + 200, y: Math.random() * 200 + 150 },
        data: {
          ...nodeData,
          isAdvancedMode,
          runState: 'IDLE',
        },
      };
      setNodes((nds) => [...nds, newNode]);
      addLog('info', `Novo bloco adicionado: ${nodeData.label}`, newNode.id);
    },
    [isAdvancedMode]
  );

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
          id: `step-${Date.now()}`,
          type,
          position,
          data: {
            ...data,
            isAdvancedMode,
            runState: 'IDLE',
          },
        };
        setNodes((nds) => [...nds, newNode]);
        addLog('info', `Bloco posicionado no fluxo: ${data.label}`, newNode.id);
      } catch (err) {
        console.error('Failed to drop node:', err);
      }
    },
    [screenToFlowPosition, isAdvancedMode]
  );

  // Global Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
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
          addLog('warn', `Bloco removido do fluxo: ${selectedNode.data.label}`, selectedNode.id);
          setSelectedNode(null);
        }
      } else if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault();
        simulateRun();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedNode, isRunning]);

  // Execute Workflow with Live Progress and Result Presentation
  const simulateRun = () => {
    if (isRunning) return;
    setIsRunning(true);
    addLog('info', `Iniciando execução do fluxo "${workflowTitle}" (${nodes.length} passos)...`);

    // Reset status to running
    setNodes((nds) =>
      nds.map((n) => ({
        ...n,
        data: { ...n.data, runState: 'RUNNING', isAdvancedMode },
      }))
    );

    const totalSteps = nodes.length;
    nodes.forEach((n, idx) => {
      setTimeout(() => {
        setCurrentRunningStep(idx + 1);
        addLog('exec', `Processando Passo ${idx + 1}/${totalSteps}: ${n.data.label}...`, n.id);
      }, (idx + 1) * 450);
    });

    const executionTotalMs = totalSteps * 450 + 600;

    setTimeout(() => {
      // Mark all nodes as SUCCESS or CACHED
      setNodes((nds) =>
        nds.map((n, i) => ({
          ...n,
          data: {
            ...n.data,
            runState: i === 0 ? 'CACHED' : 'SUCCESS',
            isAdvancedMode,
          },
        }))
      );

      setIsRunning(false);
      setCurrentRunningStep(null);

      // Determine output artifact based on preset or default
      const outputInfo: ExecutionArtifact = {
        fileName: activePreset.expectedOutput?.fileName || 'Audio_Consolidado_Final.wav',
        description: activePreset.expectedOutput?.description || 'Arquivo final gerado pelo fluxo de trabalho',
        path: activePreset.expectedOutput?.path || 'C:/Users/Public/KTools_Outputs/Audio_Consolidado_Final.wav',
        size: '78.4 MB',
        duration: '38 min 24 seg',
        format: 'WAV Alta Fidelidade (44.1 kHz / 16-bit)',
        sha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
      };

      setLastArtifact(outputInfo);
      setIsResultsModalOpen(true);

      addLog('success', `✓ Execução concluída! Arquivo gerado em: ${outputInfo.path}`);
    }, executionTotalMs);
  };

  const clearRunState = () => {
    setIsRunning(false);
    setCurrentRunningStep(null);
    setNodes((nds) => nds.map((n) => ({ ...n, data: { ...n.data, runState: 'IDLE', isAdvancedMode } })));
    addLog('info', 'Status de execução resetado para pronto.');
  };

  const loadPreset = (presetId: string) => {
    const preset = WORKFLOW_PRESETS.find((p) => p.id === presetId);
    if (!preset) return;
    setActivePreset(preset);
    setNodes(preset.nodes.map((n) => ({ ...n, data: { ...n.data, isAdvancedMode } })));
    setEdges(preset.edges);
    setWorkflowTitle(preset.name);
    setSelectedNode(null);

    // Update expected artifact
    setLastArtifact({
      fileName: preset.expectedOutput.fileName,
      description: preset.expectedOutput.description,
      path: preset.expectedOutput.path,
      size: '64.2 MB',
      duration: '35 min 10 seg',
      format: 'Áudio / Arquivo Final Otimizado',
    });

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
    addLog('success', 'Arquivo do fluxo exportado com sucesso.');
  };

  return (
    <div className="app-container">
      {/* Top Navbar */}
      <header className="top-navbar">
        <div className="brand-section">
          <div className="brand-logo">
            <span style={{ fontSize: '20px', filter: 'drop-shadow(0 0 8px #38bdf8)' }}>⚡</span>
            <span>K-Tools Neo</span>
          </div>

          {/* Workflow Title Input */}
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
                  fontSize: '13px',
                  fontWeight: 600,
                  padding: '4px 8px',
                  outline: 'none',
                }}
              />
            ) : (
              <span
                onClick={() => setIsEditingTitle(true)}
                style={{
                  fontSize: '13px',
                  fontWeight: 600,
                  color: '#e2e8f0',
                  cursor: 'pointer',
                  padding: '4px 8px',
                  borderRadius: '6px',
                  border: '1px solid transparent',
                  transition: 'all 0.15s',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
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
                <span>📋</span>
                <span>{workflowTitle}</span>
              </span>
            )}
          </div>
        </div>

        {/* Navbar Center & Actions */}
        <div className="navbar-actions">
          {/* Preset Workflows Dropdown */}
          <select
            onChange={(e) => e.target.value && loadPreset(e.target.value)}
            value={activePreset.id}
            style={{
              background: '#131b2e',
              border: '1px solid #334155',
              borderRadius: '8px',
              color: '#f8fafc',
              fontSize: '12px',
              fontWeight: 600,
              padding: '6px 12px',
              outline: 'none',
              cursor: 'pointer',
              maxWidth: '320px',
            }}
          >
            {WORKFLOW_PRESETS.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>

          {/* Simple / Advanced Mode Toggle Switch */}
          <button
            onClick={toggleAdvancedMode}
            style={{
              padding: '6px 12px',
              borderRadius: '8px',
              border: isAdvancedMode ? '1px solid #38bdf8' : '1px solid #22c55e',
              background: isAdvancedMode ? 'rgba(56, 189, 248, 0.15)' : 'rgba(34, 197, 94, 0.15)',
              color: isAdvancedMode ? '#38bdf8' : '#86efac',
              fontSize: '12px',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.2s',
            }}
            title={isAdvancedMode ? 'Clique para voltar ao Modo Simples e Narrativo' : 'Clique para ver detalhes técnicos e opções avançadas'}
          >
            <span>{isAdvancedMode ? '⚙️' : '🟢'}</span>
            <span>{isAdvancedMode ? 'Modo Avançado' : 'Modo Simples'}</span>
          </button>

          {/* View Generated Artifact Button (if available) */}
          {lastArtifact && (
            <button
              onClick={() => setIsResultsModalOpen(true)}
              style={{
                padding: '6px 12px',
                borderRadius: '8px',
                border: '1px solid #22c55e',
                background: 'rgba(34, 197, 94, 0.15)',
                color: '#86efac',
                fontSize: '12px',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                boxShadow: '0 0 12px rgba(34, 197, 94, 0.25)',
              }}
              title="Abrir o painel de arquivos gerados e localização no computador"
            >
              <span>✨</span>
              <span>Ver Arquivo Gerado</span>
            </button>
          )}

          {/* Quick Search Button */}
          <button
            className="btn btn-secondary"
            onClick={() => setIsSearchOpen(true)}
            title="Atalho: Barra de Espaço ou /"
          >
            <span>🔍</span>
            <span>Adicionar Nó</span>
          </button>

          {/* Execute Workflow Button */}
          <button
            className="btn btn-primary"
            onClick={simulateRun}
            disabled={isRunning}
            style={{
              opacity: isRunning ? 0.8 : 1,
              padding: '8px 18px',
              fontSize: '13px',
              fontWeight: 700,
              boxShadow: isRunning ? '0 0 16px rgba(245, 158, 11, 0.5)' : '0 4px 14px rgba(2, 132, 199, 0.5)',
            }}
            title="Atalho: Ctrl + Enter"
          >
            <span>{isRunning ? '⏳' : '▶️'}</span>
            <span>{isRunning ? `Executando (Passo ${currentRunningStep || 1}/${nodes.length})...` : 'Executar Fluxo'}</span>
          </button>

          {/* Clear Run */}
          <button className="btn btn-secondary" onClick={clearRunState} title="Resetar status de execução">
            <span>🔄</span>
          </button>

          {/* Export JSON */}
          <button className="btn btn-secondary" onClick={exportWorkflowJson} title="Exportar fluxo em arquivo JSON">
            <span>📥</span>
          </button>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <div className="editor-layout">
        {/* Left: Palette */}
        <aside className="sidebar">
          <Palette onAddNode={onAddNode} isAdvancedMode={isAdvancedMode} />
        </aside>

        {/* Center: Canvas */}
        <main
          className="canvas-container"
          ref={reactFlowWrapper}
          onDragOver={onDragOver}
          onDrop={onDrop}
        >
          {/* Narrative Helper Bar across top of Canvas */}
          <div
            style={{
              position: 'absolute',
              top: '12px',
              left: '50%',
              transform: 'translateX(-50%)',
              zIndex: 10,
              background: 'rgba(15, 23, 42, 0.85)',
              backdropFilter: 'blur(8px)',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              borderRadius: '20px',
              padding: '6px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '11px',
              color: '#e2e8f0',
              boxShadow: '0 4px 16px rgba(0, 0, 0, 0.4)',
              pointerEvents: 'none',
            }}
          >
            <span>💡</span>
            <span>
              <strong>Como funciona:</strong> Os blocos executam da esquerda para a direita (Passo 1 ➔ Passo 2 ➔ Passo 3). Clique em <strong>Executar Fluxo</strong> para gerar seus arquivos!
            </span>
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
            isAdvancedMode={isAdvancedMode}
          />
        </aside>
      </div>

      {/* Execution Results & Artifact Modal */}
      {lastArtifact && (
        <ExecutionResultsModal
          isOpen={isResultsModalOpen}
          onClose={() => setIsResultsModalOpen(false)}
          artifact={lastArtifact}
          workflowTitle={workflowTitle}
          executionTimeMs={nodes.length * 450 + 600}
        />
      )}

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

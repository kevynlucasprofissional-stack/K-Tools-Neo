import { useState } from 'react';

export interface ExecutionArtifact {
  fileName: string;
  description: string;
  path: string;
  size: string;
  duration?: string;
  format: string;
  sha256?: string;
}

export function ExecutionResultsModal({
  isOpen,
  onClose,
  artifact,
  workflowTitle,
  executionTimeMs,
}: {
  isOpen: boolean;
  onClose: () => void;
  artifact: ExecutionArtifact;
  workflowTitle: string;
  executionTimeMs: number;
}) {
  const [copied, setCopied] = useState(false);
  const [simulatedAction, setSimulatedAction] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleCopyPath = () => {
    navigator.clipboard?.writeText(artifact.path);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleOpenFolder = () => {
    setSimulatedAction('Solicitação de abertura de pasta enviada ao Windows Explorer.');
    setTimeout(() => setSimulatedAction(null), 3000);
  };

  const handleOpenFile = () => {
    setSimulatedAction('Abrindo arquivo com o player/aplicativo padrão do Windows...');
    setTimeout(() => setSimulatedAction(null), 3000);
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(6px)',
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
        fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '560px',
          background: '#0d1527',
          border: '1px solid #22c55e',
          borderRadius: '16px',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.8), 0 0 30px rgba(34, 197, 94, 0.2)',
          color: '#f8fafc',
          overflow: 'hidden',
          animation: 'fadeIn 0.2s ease-out',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div
          style={{
            padding: '16px 20px',
            background: 'linear-gradient(90deg, #14532d 0%, #064e3b 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid rgba(34, 197, 94, 0.3)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '22px' }}>✨</span>
            <div>
              <h2 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: '#f0fdf4' }}>
                Processamento Concluído com Sucesso!
              </h2>
              <p style={{ margin: '2px 0 0', fontSize: '12px', color: '#bbf7d0' }}>
                {workflowTitle}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#86efac',
              fontSize: '20px',
              cursor: 'pointer',
              padding: '4px',
            }}
          >
            ✕
          </button>
        </div>

        {/* Modal Content */}
        <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Main Artifact Card */}
          <div
            style={{
              background: '#131e36',
              border: '1px solid #1e293b',
              borderRadius: '12px',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
              <div
                style={{
                  width: '44px',
                  height: '44px',
                  borderRadius: '10px',
                  background: '#0284c7',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '22px',
                  flexShrink: 0,
                  boxShadow: '0 4px 12px rgba(2, 132, 199, 0.4)',
                }}
              >
                🎵
              </div>

              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: '15px', fontWeight: 700, color: '#f8fafc', wordBreak: 'break-all' }}>
                  {artifact.fileName}
                </div>
                <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>
                  {artifact.description}
                </div>
              </div>
            </div>

            {/* Path Box */}
            <div
              style={{
                background: '#090d16',
                border: '1px solid #1e293b',
                borderRadius: '8px',
                padding: '10px 12px',
                display: 'flex',
                flexDirection: 'column',
                gap: '4px',
              }}
            >
              <span style={{ fontSize: '10px', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase' }}>
                Onde o arquivo está salvo:
              </span>
              <div
                style={{
                  fontSize: '12px',
                  fontFamily: 'Consolas, monospace',
                  color: '#e2e8f0',
                  wordBreak: 'break-all',
                }}
              >
                {artifact.path}
              </div>
            </div>

            {/* Stats badges */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ background: '#1e293b', padding: '4px 10px', borderRadius: '6px', fontSize: '11px', color: '#cbd5e1' }}>
                📦 Tamanho: <strong>{artifact.size}</strong>
              </div>
              {artifact.duration && (
                <div style={{ background: '#1e293b', padding: '4px 10px', borderRadius: '6px', fontSize: '11px', color: '#cbd5e1' }}>
                  ⏱️ Duração: <strong>{artifact.duration}</strong>
                </div>
              )}
              <div style={{ background: '#1e293b', padding: '4px 10px', borderRadius: '6px', fontSize: '11px', color: '#cbd5e1' }}>
                💎 Formato: <strong>{artifact.format}</strong>
              </div>
              <div style={{ background: '#14532d', padding: '4px 10px', borderRadius: '6px', fontSize: '11px', color: '#86efac' }}>
                ⚡ Execução: <strong>{(executionTimeMs / 1000).toFixed(1)}s</strong>
              </div>
            </div>
          </div>

          {/* Feedback banner if an action was clicked */}
          {simulatedAction && (
            <div
              style={{
                background: 'rgba(56, 189, 248, 0.15)',
                border: '1px solid #38bdf8',
                borderRadius: '8px',
                padding: '8px 12px',
                fontSize: '12px',
                color: '#38bdf8',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span>ℹ️</span>
              <span>{simulatedAction}</span>
            </div>
          )}

          {/* Direct Action Buttons */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <button
              onClick={handleOpenFolder}
              style={{
                padding: '12px',
                background: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '10px',
                color: '#f8fafc',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = '#334155')}
              onMouseLeave={(e) => (e.currentTarget.style.background = '#1e293b')}
            >
              <span>📂</span>
              <span>Abrir Pasta no Explorer</span>
            </button>

            <button
              onClick={handleOpenFile}
              style={{
                padding: '12px',
                background: '#0284c7',
                border: 'none',
                borderRadius: '10px',
                color: '#ffffff',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                transition: 'all 0.2s',
                boxShadow: '0 4px 12px rgba(2, 132, 199, 0.4)',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = '#0369a1')}
              onMouseLeave={(e) => (e.currentTarget.style.background = '#0284c7')}
            >
              <span>▶️</span>
              <span>Reproduzir / Abrir Arquivo</span>
            </button>
          </div>

          <button
            onClick={handleCopyPath}
            style={{
              padding: '10px',
              background: copied ? '#14532d' : '#0e1526',
              border: copied ? '1px solid #22c55e' : '1px solid #1e293b',
              borderRadius: '8px',
              color: copied ? '#86efac' : '#94a3b8',
              fontSize: '12px',
              fontWeight: 500,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              transition: 'all 0.2s',
            }}
          >
            <span>{copied ? '✓' : '📋'}</span>
            <span>{copied ? 'Caminho Completo Copiado para o seu Ctrl+V!' : 'Copiar Caminho do Arquivo'}</span>
          </button>
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '12px 20px',
            background: '#090d16',
            borderTop: '1px solid #1e293b',
            display: 'flex',
            justifyContent: 'flex-end',
          }}
        >
          <button
            onClick={onClose}
            style={{
              padding: '8px 18px',
              background: '#334155',
              border: 'none',
              borderRadius: '8px',
              color: '#f8fafc',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Fechar Janela
          </button>
        </div>
      </div>
    </div>
  );
}

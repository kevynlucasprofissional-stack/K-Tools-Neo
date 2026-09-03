import { useRef, useEffect } from 'react';

export interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'exec' | 'success' | 'warn' | 'error' | 'cached';
  message: string;
  nodeId?: string;
}

export function BottomConsole({
  logs,
  onClearLogs,
  isOpen,
  onToggle,
}: {
  logs: LogEntry[];
  onClearLogs: () => void;
  isOpen: boolean;
  onToggle: () => void;
}) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, isOpen]);

  const LEVEL_STYLES: Record<string, { color: string; badge: string; bg: string }> = {
    info: { color: '#38bdf8', badge: 'INFO', bg: 'rgba(56, 189, 248, 0.15)' },
    exec: { color: '#f59e0b', badge: 'EXEC', bg: 'rgba(245, 158, 11, 0.15)' },
    success: { color: '#10b981', badge: 'DONE', bg: 'rgba(16, 185, 129, 0.15)' },
    warn: { color: '#fb923c', badge: 'WARN', bg: 'rgba(251, 146, 60, 0.15)' },
    error: { color: '#ef4444', badge: 'FAIL', bg: 'rgba(239, 68, 68, 0.15)' },
    cached: { color: '#06b6d4', badge: 'CACHE', bg: 'rgba(6, 182, 212, 0.15)' },
  };

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 30,
        backgroundColor: '#0a0e1a',
        borderTop: '1px solid #1e293b',
        boxShadow: '0 -4px 20px rgba(0, 0, 0, 0.5)',
        display: 'flex',
        flexDirection: 'column',
        height: isOpen ? '220px' : '36px',
        transition: 'height 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
        fontFamily: 'Consolas, Monaco, monospace',
      }}
    >
      {/* Console Header / Bar */}
      <div
        style={{
          height: '36px',
          padding: '0 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: '#0d1424',
          borderBottom: isOpen ? '1px solid #1e293b' : 'none',
          cursor: 'pointer',
          userSelect: 'none',
        }}
        onClick={onToggle}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '13px', color: '#38bdf8' }}>⌨️</span>
          <span style={{ fontSize: '12px', fontWeight: 600, color: '#f8fafc', letterSpacing: '0.3px' }}>
            Console de Execução & RunJournal
          </span>
          <span
            style={{
              fontSize: '10px',
              padding: '1px 6px',
              borderRadius: '8px',
              background: '#1e293b',
              color: '#94a3b8',
            }}
          >
            {logs.length} eventos
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }} onClick={(e) => e.stopPropagation()}>
          {isOpen && (
            <button
              onClick={onClearLogs}
              style={{
                background: 'transparent',
                border: '1px solid #1e293b',
                borderRadius: '4px',
                padding: '2px 8px',
                fontSize: '11px',
                color: '#94a3b8',
                cursor: 'pointer',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = '#f8fafc')}
              onMouseLeave={(e) => (e.currentTarget.style.color = '#94a3b8')}
            >
              Limpar
            </button>
          )}
          <button
            onClick={onToggle}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              fontSize: '14px',
              cursor: 'pointer',
            }}
          >
            {isOpen ? '▼' : '▲'}
          </button>
        </div>
      </div>

      {/* Logs Viewport */}
      {isOpen && (
        <div
          ref={scrollRef}
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '10px 16px',
            fontSize: '11px',
            display: 'flex',
            flexDirection: 'column',
            gap: '4px',
            lineHeight: '1.5',
          }}
        >
          {logs.length === 0 ? (
            <div style={{ color: '#64748b', fontStyle: 'italic', padding: '8px 0' }}>
              Nenhum evento registrado ainda. Clique em "Executar Workflow" para iniciar a execução.
            </div>
          ) : (
            logs.map((l) => {
              const style = LEVEL_STYLES[l.level] || LEVEL_STYLES.info;
              return (
                <div key={l.id} style={{ display: 'flex', alignItems: 'baseline', gap: '10px' }}>
                  <span style={{ color: '#475569', fontSize: '10px' }}>{l.timestamp}</span>
                  <span
                    style={{
                      fontSize: '9px',
                      fontWeight: 700,
                      padding: '1px 5px',
                      borderRadius: '3px',
                      background: style.bg,
                      color: style.color,
                    }}
                  >
                    {style.badge}
                  </span>
                  <span style={{ color: '#e2e8f0', flex: 1 }}>{l.message}</span>
                  {l.nodeId && (
                    <span style={{ color: '#64748b', fontSize: '10px', opacity: 0.8 }}>
                      [{l.nodeId}]
                    </span>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}

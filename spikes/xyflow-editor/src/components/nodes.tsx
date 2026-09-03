import { Handle, Position } from '@xyflow/react';

const CATEGORY_COLORS: Record<string, { border: string; bg: string; text: string; badge: string }> = {
  Media: { border: '#ec4899', bg: 'rgba(236, 72, 153, 0.15)', text: '#f472b6', badge: '#831843' },
  Text: { border: '#10b981', bg: 'rgba(16, 185, 129, 0.15)', text: '#34d399', badge: '#064e3b' },
  PDF: { border: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)', text: '#f87171', badge: '#7f1d1d' },
  JSON: { border: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)', text: '#fbbf24', badge: '#78350f' },
  Filesystem: { border: '#3b82f6', bg: 'rgba(59, 130, 246, 0.15)', text: '#60a5fa', badge: '#1e3a8a' },
  Images: { border: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.15)', text: '#a78bfa', badge: '#4c1d95' },
  Documents: { border: '#06b6d4', bg: 'rgba(6, 182, 212, 0.15)', text: '#22d3ee', badge: '#164e63' },
  Core: { border: '#64748b', bg: 'rgba(100, 116, 139, 0.15)', text: '#94a3b8', badge: '#1e293b' },
  Files: { border: '#6366f1', bg: 'rgba(99, 102, 241, 0.15)', text: '#818cf8', badge: '#312e81' },
};

const PORT_COLORS: Record<string, string> = {
  file: '#38bdf8',
  files: '#38bdf8',
  folder: '#eab308',
  audio: '#c084fc',
  video: '#fb923c',
  image: '#f472b6',
  text: '#34d399',
  json: '#fbbf24',
  pdf: '#f87171',
  number: '#818cf8',
  any: '#94a3b8',
};

export function KToolNode({ data, selected }: { data: any; selected?: boolean }) {
  const category = data.category || 'Core';
  const theme = CATEGORY_COLORS[category] || CATEGORY_COLORS.Core;
  const runState = data.runState || 'IDLE';

  let stateColor = '#64748b';
  let stateLabel = 'Pronto';
  if (runState === 'RUNNING') {
    stateColor = '#f59e0b';
    stateLabel = 'Executando...';
  } else if (runState === 'SUCCESS') {
    stateColor = '#10b981';
    stateLabel = 'Concluído';
  } else if (runState === 'ERROR') {
    stateColor = '#ef4444';
    stateLabel = 'Erro';
  } else if (runState === 'CACHED') {
    stateColor = '#06b6d4';
    stateLabel = 'Cached';
  }

  return (
    <div
      className={`ktool-node ${selected ? 'selected' : ''}`}
      data-state={runState}
      style={{
        background: '#131b2e',
        borderRadius: '12px',
        border: `2px solid ${selected ? '#38bdf8' : runState === 'IDLE' ? '#1e293b' : stateColor}`,
        boxShadow: selected
          ? '0 0 0 3px rgba(56, 189, 248, 0.35), 0 8px 24px rgba(0,0,0,0.5)'
          : runState === 'RUNNING'
          ? '0 0 16px rgba(245, 158, 11, 0.3), 0 4px 12px rgba(0,0,0,0.4)'
          : '0 4px 16px rgba(0,0,0,0.4)',
        minWidth: '220px',
        maxWidth: '300px',
        color: '#f8fafc',
        fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
        overflow: 'hidden',
        transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
      }}
    >
      {/* Node Header */}
      <div
        className="node-header"
        style={{
          padding: '10px 14px',
          background: 'linear-gradient(180deg, #1e293b 0%, #152033 100%)',
          borderBottom: '1px solid #1e293b',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '8px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
          <div
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: theme.border,
              boxShadow: `0 0 8px ${theme.border}`,
              flexShrink: 0,
            }}
          />
          <strong
            style={{
              fontSize: '13px',
              fontWeight: 600,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              color: '#f8fafc',
            }}
          >
            {data.label}
          </strong>
        </div>

        <span
          style={{
            fontSize: '9px',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            padding: '2px 7px',
            borderRadius: '10px',
            background: theme.bg,
            color: theme.text,
            border: `1px solid ${theme.border}44`,
            flexShrink: 0,
          }}
        >
          {category}
        </span>
      </div>

      {/* Node Type ID pill (monospace) */}
      {data.type_id && (
        <div
          style={{
            padding: '3px 14px',
            fontSize: '10px',
            fontFamily: 'Consolas, monospace',
            color: '#64748b',
            background: '#0e1526',
            borderBottom: '1px solid #1e293b',
          }}
        >
          {data.type_id}
        </div>
      )}

      {/* Animated running progress line */}
      {runState === 'RUNNING' && (
        <div style={{ height: '3px', width: '100%', background: '#1e293b', overflow: 'hidden', position: 'relative' }}>
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              bottom: 0,
              width: '50%',
              background: 'linear-gradient(90deg, #f59e0b, #fbbf24)',
              boxShadow: '0 0 10px #f59e0b',
              animation: 'pulseBar 1s infinite alternate ease-in-out',
            }}
          />
        </div>
      )}

      {/* Node Body (Ports) */}
      <div
        className="node-body"
        style={{
          padding: '12px 14px',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
        }}
      >
        {/* Inputs */}
        {data.inputs && data.inputs.length > 0 && (
          <div className="inputs" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {data.inputs.map((input: any) => {
              const pColor = PORT_COLORS[input.type] || PORT_COLORS.any;
              return (
                <div
                  key={input.id}
                  style={{
                    position: 'relative',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'flex-start',
                  }}
                >
                  <Handle
                    type="target"
                    position={Position.Left}
                    id={input.id}
                    style={{
                      left: '-18px',
                      width: '10px',
                      height: '10px',
                      borderRadius: '50%',
                      background: pColor,
                      border: '2px solid #131b2e',
                      boxShadow: `0 0 6px ${pColor}`,
                    }}
                    isValidConnection={() => true}
                  />
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontSize: '11px', color: '#cbd5e1', fontWeight: 500 }}>
                      {input.label}
                    </span>
                    <span
                      style={{
                        fontSize: '9px',
                        color: pColor,
                        opacity: 0.85,
                        fontFamily: 'monospace',
                      }}
                    >
                      :{input.type}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Outputs */}
        {data.outputs && data.outputs.length > 0 && (
          <div
            className="outputs"
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
              marginTop: data.inputs?.length ? '6px' : '0',
            }}
          >
            {data.outputs.map((output: any) => {
              const pColor = PORT_COLORS[output.type] || PORT_COLORS.any;
              return (
                <div
                  key={output.id}
                  style={{
                    position: 'relative',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'flex-end',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span
                      style={{
                        fontSize: '9px',
                        color: pColor,
                        opacity: 0.85,
                        fontFamily: 'monospace',
                      }}
                    >
                      :{output.type}
                    </span>
                    <span style={{ fontSize: '11px', color: '#cbd5e1', fontWeight: 500 }}>
                      {output.label}
                    </span>
                  </div>
                  <Handle
                    type="source"
                    position={Position.Right}
                    id={output.id}
                    style={{
                      right: '-18px',
                      width: '10px',
                      height: '10px',
                      borderRadius: '50%',
                      background: pColor,
                      border: '2px solid #131b2e',
                      boxShadow: `0 0 6px ${pColor}`,
                    }}
                    isValidConnection={() => true}
                  />
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Node Footer Status */}
      <div
        style={{
          padding: '6px 14px',
          background: '#0a0f1d',
          borderTop: '1px solid #1a2337',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '10px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div
            style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              background: stateColor,
              boxShadow: runState === 'RUNNING' ? `0 0 8px ${stateColor}` : 'none',
            }}
          />
          <span style={{ color: stateColor, fontWeight: 500 }}>{stateLabel}</span>
        </div>

        {data.config && Object.keys(data.config).length > 0 && (
          <span style={{ color: '#64748b', fontSize: '9px' }}>
            ⚙️ {Object.keys(data.config).length} cfg
          </span>
        )}
      </div>
    </div>
  );
}

export function MissingNode({ data, selected }: { data: any; selected?: boolean }) {
  return (
    <div
      className="missing-node"
      style={{
        background: '#1a0d13',
        border: `2px dashed ${selected ? '#f43f5e' : '#e11d48'}`,
        borderRadius: '12px',
        minWidth: '200px',
        padding: '14px',
        color: '#fb7185',
        boxShadow: '0 4px 16px rgba(225, 29, 72, 0.2)',
        fontFamily: 'Inter, system-ui, sans-serif',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '16px' }}>⚠️</span>
        <div>
          <div style={{ fontWeight: 700, fontSize: '12px', textTransform: 'uppercase' }}>
            Nó Ausente / Desconhecido
          </div>
          <div style={{ fontSize: '10px', color: '#fda4af', fontFamily: 'monospace', marginTop: '2px' }}>
            {data.originalType || 'unknown.type'}
          </div>
        </div>
      </div>

      <div className="node-body" style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {data.inputs?.map((input: any) => (
          <div key={input.id} style={{ position: 'relative' }}>
            <Handle type="target" position={Position.Left} id={input.id} style={{ left: '-18px' }} />
            <span style={{ fontSize: '10px', color: '#fda4af' }}>{input.label}</span>
          </div>
        ))}
        {data.outputs?.map((output: any) => (
          <div key={output.id} style={{ position: 'relative', textAlign: 'right' }}>
            <span style={{ fontSize: '10px', color: '#fda4af' }}>{output.label}</span>
            <Handle type="source" position={Position.Right} id={output.id} style={{ right: '-18px' }} />
          </div>
        ))}
      </div>
    </div>
  );
}

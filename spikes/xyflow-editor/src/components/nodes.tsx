import { Handle, Position } from '@xyflow/react';

const CATEGORY_COLORS: Record<string, { border: string; bg: string; text: string; badge: string }> = {
  Mídia: { border: '#ec4899', bg: 'rgba(236, 72, 153, 0.15)', text: '#f472b6', badge: '#831843' },
  'Mídia & Nuvem': { border: '#ec4899', bg: 'rgba(236, 72, 153, 0.15)', text: '#f472b6', badge: '#831843' },
  'Áudio & Voz': { border: '#c084fc', bg: 'rgba(192, 132, 252, 0.15)', text: '#c084fc', badge: '#581c87' },
  Arquivos: { border: '#3b82f6', bg: 'rgba(59, 130, 246, 0.15)', text: '#60a5fa', badge: '#1e3a8a' },
  Texto: { border: '#10b981', bg: 'rgba(16, 185, 129, 0.15)', text: '#34d399', badge: '#064e3b' },
  'Texto & Produtividade': { border: '#10b981', bg: 'rgba(16, 185, 129, 0.15)', text: '#34d399', badge: '#064e3b' },
  PDF: { border: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)', text: '#f87171', badge: '#7f1d1d' },
  'PDF & Documentos': { border: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)', text: '#f87171', badge: '#7f1d1d' },
  Imagens: { border: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.15)', text: '#a78bfa', badge: '#4c1d95' },
  Sistema: { border: '#6366f1', bg: 'rgba(99, 102, 241, 0.15)', text: '#818cf8', badge: '#312e81' },
  'Sistema & Auditoria': { border: '#6366f1', bg: 'rgba(99, 102, 241, 0.15)', text: '#818cf8', badge: '#312e81' },
  Core: { border: '#64748b', bg: 'rgba(100, 116, 139, 0.15)', text: '#94a3b8', badge: '#1e293b' },
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
  boolean: '#10b981',
  any: '#94a3b8',
};

export function KToolNode({ data, selected }: { data: any; selected?: boolean }) {
  const category = data.category || 'Core';
  const theme = CATEGORY_COLORS[category] || CATEGORY_COLORS.Core;
  const runState = data.runState || 'IDLE';
  const isAdvancedMode = data.isAdvancedMode || false;
  const stepNumber = data.stepNumber;

  let stateColor = '#64748b';
  let stateLabel = 'Aguardando';
  if (runState === 'RUNNING') {
    stateColor = '#f59e0b';
    stateLabel = 'Processando...';
  } else if (runState === 'SUCCESS') {
    stateColor = '#10b981';
    stateLabel = '✓ Concluído';
  } else if (runState === 'ERROR') {
    stateColor = '#ef4444';
    stateLabel = 'Falhou';
  } else if (runState === 'CACHED') {
    stateColor = '#06b6d4';
    stateLabel = '✓ Reutilizado (Cache)';
  }

  // Find key config preview
  let previewConfig = '';
  if (data.config) {
    if (data.config.path) previewConfig = `📂 ${data.config.path}`;
    else if (data.config.paths) previewConfig = `📄 ${data.config.paths}`;
    else if (data.config.output_name) previewConfig = `💾 Salvar: ${data.config.output_name}`;
    else if (data.config.format) previewConfig = `🎵 Formato: ${data.config.format.toUpperCase()}`;
    else if (data.config.message) previewConfig = `💬 "${data.config.message.slice(0, 28)}..."`;
  }

  return (
    <div
      className={`ktool-node ${selected ? 'selected' : ''}`}
      data-state={runState}
      style={{
        background: '#131b2e',
        borderRadius: '14px',
        border: `2px solid ${selected ? '#38bdf8' : runState === 'IDLE' ? '#1e293b' : stateColor}`,
        boxShadow: selected
          ? '0 0 0 3px rgba(56, 189, 248, 0.35), 0 10px 28px rgba(0,0,0,0.6)'
          : runState === 'RUNNING'
          ? '0 0 20px rgba(245, 158, 11, 0.35), 0 4px 14px rgba(0,0,0,0.5)'
          : '0 4px 16px rgba(0,0,0,0.4)',
        minWidth: '240px',
        maxWidth: '320px',
        color: '#f8fafc',
        fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
        overflow: 'hidden',
        transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
      }}
    >
      {/* Narrative Step Ribbon (if defined) */}
      {stepNumber && (
        <div
          style={{
            background: 'linear-gradient(90deg, #1e3a8a, #0284c7)',
            color: '#e0f2fe',
            fontSize: '10px',
            fontWeight: 800,
            textTransform: 'uppercase',
            letterSpacing: '1px',
            padding: '3px 12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <span>PASSO {stepNumber}</span>
          <span style={{ fontSize: '9px', opacity: 0.85 }}>{stateLabel}</span>
        </div>
      )}

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

      {/* Description / Subtitle */}
      {data.description && !isAdvancedMode && (
        <div
          style={{
            padding: '6px 14px',
            fontSize: '11px',
            color: '#94a3b8',
            lineHeight: '1.4',
            background: '#0e1526',
            borderBottom: '1px solid #1e293b',
          }}
        >
          {data.description}
        </div>
      )}

      {/* Node Type ID pill (shown in Advanced Mode) */}
      {isAdvancedMode && data.type_id && (
        <div
          style={{
            padding: '3px 14px',
            fontSize: '10px',
            fontFamily: 'Consolas, monospace',
            color: '#64748b',
            background: '#0a0f1d',
            borderBottom: '1px solid #1e293b',
          }}
        >
          ID: {data.type_id}
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
          gap: '10px',
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
                  title={`Conexão de Entrada: ${input.label || input.id}`}
                >
                  <Handle
                    type="target"
                    position={Position.Left}
                    id={input.id}
                    style={{
                      left: '-19px',
                      width: '12px',
                      height: '12px',
                      borderRadius: '50%',
                      background: pColor,
                      border: '2px solid #0f172a',
                      boxShadow: `0 0 8px ${pColor}`,
                    }}
                    isValidConnection={() => true}
                  />
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontSize: '11px', color: '#cbd5e1', fontWeight: 500 }}>
                      {input.label}
                    </span>
                    {isAdvancedMode && (
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
                    )}
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
              marginTop: data.inputs?.length ? '4px' : '0',
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
                  title={`Conexão de Saída: ${output.label || output.id}`}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontSize: '11px', color: '#cbd5e1', fontWeight: 500 }}>
                      {output.label}
                    </span>
                    {isAdvancedMode && (
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
                    )}
                  </div>
                  <Handle
                    type="source"
                    position={Position.Right}
                    id={output.id}
                    style={{
                      right: '-19px',
                      width: '12px',
                      height: '12px',
                      borderRadius: '50%',
                      background: pColor,
                      border: '2px solid #0f172a',
                      boxShadow: `0 0 8px ${pColor}`,
                    }}
                    isValidConnection={() => true}
                  />
                </div>
              );
            })}
          </div>
        )}

        {/* Key config preview badge */}
        {previewConfig && (
          <div
            style={{
              background: '#090d16',
              borderRadius: '6px',
              padding: '4px 8px',
              fontSize: '10px',
              color: '#94a3b8',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              border: '1px solid #1e293b',
            }}
            title={previewConfig}
          >
            {previewConfig}
          </div>
        )}

        {/* Finished / Success Artifact Alert Badge */}
        {(runState === 'SUCCESS' || runState === 'CACHED') && (
          <div
            style={{
              marginTop: '4px',
              padding: '4px 8px',
              borderRadius: '6px',
              background: 'rgba(16, 185, 129, 0.12)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              color: '#34d399',
              fontSize: '10px',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span>✓ Executado com Sucesso</span>
            <span style={{ fontSize: '9px', opacity: 0.85 }}>Ver Resultado</span>
          </div>
        )}
      </div>
    </div>
  );
}

export function MissingNode({ data }: { data: any }) {
  return (
    <div
      className="missing-node"
      style={{
        background: '#181216',
        borderRadius: '12px',
        border: '2px dashed #f43f5e',
        minWidth: '220px',
        color: '#f8fafc',
        fontFamily: 'Inter, system-ui, sans-serif',
        overflow: 'hidden',
        boxShadow: '0 4px 16px rgba(244, 63, 94, 0.2)',
      }}
    >
      <div
        style={{
          padding: '8px 12px',
          background: 'rgba(244, 63, 94, 0.2)',
          borderBottom: '1px solid rgba(244, 63, 94, 0.3)',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          color: '#fda4af',
          fontSize: '12px',
          fontWeight: 600,
        }}
      >
        <span>⚠️</span>
        <span>Extensão Não Encontrada</span>
      </div>
      <div style={{ padding: '12px', fontSize: '11px', color: '#94a3b8', lineHeight: '1.4' }}>
        <div>
          O tipo de nó <code style={{ color: '#f43f5e', background: '#27171d', padding: '1px 4px', borderRadius: '4px' }}>{data.type_id || 'desconhecido'}</code> não está instalado neste ambiente.
        </div>
        <div style={{ marginTop: '6px', fontSize: '10px', color: '#64748b' }}>
          O nó e suas conexões foram preservados no arquivo do fluxo.
        </div>
      </div>
    </div>
  );
}

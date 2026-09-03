import { type Node } from '@xyflow/react';
import { useState, useEffect } from 'react';

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

export function Inspector({
  selectedNode,
  onNodeUpdate,
}: {
  selectedNode: Node | null;
  onNodeUpdate: (id: string, data: any) => void;
}) {
  const [configValues, setConfigValues] = useState<any>({});

  useEffect(() => {
    if (selectedNode) {
      setConfigValues(selectedNode.data?.config || {});
    }
  }, [selectedNode?.id]);

  if (!selectedNode) {
    return (
      <div
        className="inspector-empty"
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          color: '#64748b',
          textAlign: 'center',
          padding: '24px',
          gap: '12px',
        }}
      >
        <div
          style={{
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            background: '#1e293b',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '20px',
          }}
        >
          🔍
        </div>
        <div>
          <div style={{ fontWeight: 600, color: '#cbd5e1', fontSize: '13px' }}>
            Nenhum nó selecionado
          </div>
          <div style={{ fontSize: '11px', marginTop: '4px', color: '#64748b' }}>
            Clique em qualquer nó no fluxo para inspecionar e editar configurações
          </div>
        </div>
      </div>
    );
  }

  const data = (selectedNode.data || {}) as Record<string, any>;
  const type = selectedNode.type;

  const handleConfigChange = (key: string, value: string) => {
    const newConfig = { ...configValues, [key]: value };
    setConfigValues(newConfig);
    onNodeUpdate(selectedNode.id, { config: newConfig });
  };

  return (
    <div
      className="inspector"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        fontFamily: 'Inter, system-ui, sans-serif',
        color: '#f8fafc',
      }}
    >
      {/* Header */}
      <div style={{ borderBottom: '1px solid #1e293b', paddingBottom: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 600, color: '#f8fafc' }}>
            {data.label || 'Propriedades do Nó'}
          </h3>
          <span
            style={{
              fontSize: '10px',
              padding: '2px 8px',
              borderRadius: '12px',
              background: '#1e293b',
              color: '#94a3b8',
              fontWeight: 600,
            }}
          >
            {data.category || 'Geral'}
          </span>
        </div>
        {data.type_id && (
          <div
            style={{
              fontSize: '11px',
              fontFamily: 'monospace',
              color: '#38bdf8',
              marginTop: '4px',
            }}
          >
            {data.type_id}
          </div>
        )}
      </div>

      {/* Metadata Card */}
      <div
        style={{
          background: '#0e1526',
          borderRadius: '8px',
          padding: '10px 12px',
          border: '1px solid #1e293b',
          fontSize: '11px',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: '#64748b' }}>ID do Nó:</span>
          <span style={{ fontFamily: 'monospace', color: '#cbd5e1' }}>{selectedNode.id}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: '#64748b' }}>Status de Execução:</span>
          <span
            style={{
              fontWeight: 600,
              color:
                data.runState === 'SUCCESS'
                  ? '#10b981'
                  : data.runState === 'RUNNING'
                  ? '#f59e0b'
                  : data.runState === 'ERROR'
                  ? '#ef4444'
                  : '#94a3b8',
            }}
          >
            {data.runState || 'IDLE'}
          </span>
        </div>
      </div>

      {/* Missing Node Warning */}
      {type === 'missing' && (
        <div
          style={{
            background: 'rgba(225, 29, 72, 0.15)',
            padding: '10px',
            borderRadius: '8px',
            border: '1px solid #e11d48',
            color: '#fb7185',
            fontSize: '11px',
          }}
        >
          <strong>⚠️ Nó Ausente no Ambiente</strong>
          <p style={{ margin: '4px 0 0 0', opacity: 0.9 }}>
            Tipo original: <code style={{ color: '#fda4af' }}>{String(data.originalType)}</code>
          </p>
        </div>
      )}

      {/* Configuration Section */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div style={{ fontSize: '12px', fontWeight: 600, color: '#cbd5e1' }}>Configurações</div>
        {data.config && Object.keys(data.config as any).length > 0 ? (
          Object.keys(data.config).map((key) => (
            <div key={key} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <label style={{ fontSize: '11px', color: '#94a3b8' }}>{key}</label>
              <input
                type="text"
                value={configValues[key] ?? ''}
                onChange={(e) => handleConfigChange(key, e.target.value)}
                style={{
                  width: '100%',
                  padding: '7px 10px',
                  background: '#0e1526',
                  border: '1px solid #1e293b',
                  borderRadius: '6px',
                  color: '#f8fafc',
                  fontSize: '12px',
                  boxSizing: 'border-box',
                  outline: 'none',
                  transition: 'border-color 0.2s',
                }}
                onFocus={(e) => (e.target.style.borderColor = '#38bdf8')}
                onBlur={(e) => (e.target.style.borderColor = '#1e293b')}
              />
            </div>
          ))
        ) : (
          <div
            style={{
              padding: '12px',
              background: '#0e1526',
              borderRadius: '6px',
              border: '1px dashed #1e293b',
              color: '#64748b',
              fontSize: '11px',
              textAlign: 'center',
            }}
          >
            Este nó opera com portas automáticas ou padrões de contrato.
          </div>
        )}
      </div>

      {/* Ports Overview */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div style={{ fontSize: '12px', fontWeight: 600, color: '#cbd5e1' }}>Portas Contratadas</div>
        {/* Input ports */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <div style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase' }}>
            Entradas ({data.inputs?.length || 0})
          </div>
          {data.inputs && data.inputs.length > 0 ? (
            data.inputs.map((inp: any) => (
              <div
                key={inp.id}
                style={{
                  padding: '5px 8px',
                  background: '#0e1526',
                  borderRadius: '4px',
                  border: '1px solid #1e293b',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <span style={{ fontSize: '11px', color: '#cbd5e1' }}>{inp.label}</span>
                <span
                  style={{
                    fontSize: '9px',
                    fontWeight: 600,
                    color: PORT_COLORS[inp.type] || '#94a3b8',
                    fontFamily: 'monospace',
                  }}
                >
                  {inp.type}
                </span>
              </div>
            ))
          ) : (
            <span style={{ fontSize: '11px', color: '#64748b' }}>Nenhuma entrada necessária</span>
          )}
        </div>

        {/* Output ports */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '6px' }}>
          <div style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase' }}>
            Saídas ({data.outputs?.length || 0})
          </div>
          {data.outputs && data.outputs.length > 0 ? (
            data.outputs.map((out: any) => (
              <div
                key={out.id}
                style={{
                  padding: '5px 8px',
                  background: '#0e1526',
                  borderRadius: '4px',
                  border: '1px solid #1e293b',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <span style={{ fontSize: '11px', color: '#cbd5e1' }}>{out.label}</span>
                <span
                  style={{
                    fontSize: '9px',
                    fontWeight: 600,
                    color: PORT_COLORS[out.type] || '#94a3b8',
                    fontFamily: 'monospace',
                  }}
                >
                  {out.type}
                </span>
              </div>
            ))
          ) : (
            <span style={{ fontSize: '11px', color: '#64748b' }}>Nenhuma saída produzida</span>
          )}
        </div>
      </div>
    </div>
  );
}

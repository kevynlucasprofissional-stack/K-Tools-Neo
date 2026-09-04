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
  boolean: '#10b981',
  any: '#94a3b8',
};

export function Inspector({
  selectedNode,
  onNodeUpdate,
  isAdvancedMode,
}: {
  selectedNode: Node | null;
  onNodeUpdate: (id: string, data: any) => void;
  isAdvancedMode: boolean;
}) {
  const [configValues, setConfigValues] = useState<any>({});
  const [showAdvancedAccordion, setShowAdvancedAccordion] = useState(false);

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
            width: '52px',
            height: '52px',
            borderRadius: '14px',
            background: '#131e36',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '24px',
            border: '1px solid #1e293b',
          }}
        >
          👆
        </div>
        <div>
          <div style={{ fontWeight: 600, color: '#e2e8f0', fontSize: '14px' }}>
            Nenhum bloco selecionado
          </div>
          <div style={{ fontSize: '12px', marginTop: '6px', color: '#64748b', lineHeight: '1.4' }}>
            Clique em qualquer bloco do fluxo para ver o que ele faz e configurar de forma simples.
          </div>
        </div>
      </div>
    );
  }

  const data = (selectedNode.data || {}) as Record<string, any>;
  const stepNumber = data.stepNumber;
  const config = configValues || {};

  const handleConfigChange = (key: string, value: any) => {
    const newConfig = { ...configValues, [key]: value };
    setConfigValues(newConfig);
    onNodeUpdate(selectedNode.id, { config: newConfig });
  };

  // Divide config keys into essential and advanced
  const allKeys = Object.keys(config);
  const essentialKeys = (data.essentialFields as string[]) || allKeys.slice(0, 1);
  const advancedKeys = (data.advancedFields as string[]) || allKeys.filter((k) => !essentialKeys.includes(k));

  // Friendly labels for config keys
  const FIELD_LABELS: Record<string, { label: string; helper: string; placeholder: string }> = {
    path: {
      label: '📁 Pasta no Computador',
      helper: 'Indique a pasta onde os arquivos estão guardados.',
      placeholder: 'C:/Users/SeuNome/Videos',
    },
    paths: {
      label: '📄 Arquivo(s) Selecionado(s)',
      helper: 'Nome ou caminho dos arquivos para processamento.',
      placeholder: 'exemplo_video.mp4',
    },
    output_name: {
      label: '💾 Nome do Arquivo Final',
      helper: 'Como você deseja nomear o arquivo resultante.',
      placeholder: 'Audio_Consolidado_Final.wav',
    },
    extensions: {
      label: '🔍 Extensões Permitidas',
      helper: 'Tipos de arquivos que devem ser procurados (separados por vírgula).',
      placeholder: 'mp4, mkv, webm',
    },
    format: {
      label: '🎵 Formato de Áudio',
      helper: 'WAV para máxima qualidade ou MP3 para tamanho reduzido.',
      placeholder: 'wav',
    },
    output_dir: {
      label: '📂 Pasta para Salvar Relatório',
      helper: 'Onde o relatório de auditoria será gerado.',
      placeholder: 'C:/Relatorios_KTools',
    },
    message: {
      label: '💬 Mensagem da Notificação',
      helper: 'Texto que aparecerá na barra de notificações do Windows ao concluir.',
      placeholder: 'Processamento concluído com sucesso!',
    },
    intensity: {
      label: '🎚️ Intensidade do De-Esser',
      helper: 'Quanto maior o valor, mais suave ficará a voz (padrão recomendado: 0.5).',
      placeholder: '0.5',
    },
    parts_count: {
      label: '✂️ Quantidade de Partes',
      helper: 'Em quantas partes equilibradas o documento será repartido.',
      placeholder: '2',
    },
    sample_rate: {
      label: 'Taxa de Amostragem (Hz)',
      helper: 'Qualidade técnica do sinal acústico (44100Hz = Padrão CD).',
      placeholder: '44100',
    },
    normalize: {
      label: 'Normalização Automática de Volume',
      helper: 'Equaliza o volume das diferentes faixas para ficarem com a mesma altura.',
      placeholder: 'true',
    },
    recursive: {
      label: 'Varrer Subpastas',
      helper: 'Se ativado, procura também arquivos dentro de pastas internas.',
      placeholder: 'true',
    },
    denoise: {
      label: 'Redução de Ruído de Fundo',
      helper: 'Aplica filtro espectral para limpar chiados de gravação.',
      placeholder: 'true',
    },
    keep_source: {
      label: 'Manter Arquivos Originais',
      helper: 'Não remove os arquivos de entrada após a conversão.',
      placeholder: 'true',
    },
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
        {stepNumber && (
          <div
            style={{
              display: 'inline-block',
              background: '#0284c7',
              color: '#ffffff',
              fontSize: '10px',
              fontWeight: 800,
              padding: '2px 8px',
              borderRadius: '6px',
              marginBottom: '6px',
              letterSpacing: '0.5px',
            }}
          >
            PASSO {stepNumber}
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 700, color: '#f8fafc' }}>
            {data.label || 'Configurações'}
          </h3>
          <span
            style={{
              fontSize: '10px',
              padding: '2px 8px',
              borderRadius: '10px',
              background: '#1e293b',
              color: '#94a3b8',
              fontWeight: 600,
            }}
          >
            {data.category || 'Geral'}
          </span>
        </div>

        {data.description && (
          <p style={{ margin: '6px 0 0', fontSize: '12px', color: '#94a3b8', lineHeight: '1.4' }}>
            {data.description}
          </p>
        )}

        {isAdvancedMode && data.type_id && (
          <div
            style={{
              fontSize: '11px',
              fontFamily: 'monospace',
              color: '#38bdf8',
              marginTop: '6px',
              background: '#090d16',
              padding: '4px 8px',
              borderRadius: '6px',
            }}
          >
            ID Canônico: {data.type_id}
          </div>
        )}
      </div>

      {/* ESSENTIAL CONFIGS (Decisões Importantes e Simples) */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <div style={{ fontSize: '12px', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          Configurações Principais
        </div>

        {allKeys.length === 0 ? (
          <div style={{ fontSize: '12px', color: '#64748b', fontStyle: 'italic', background: '#090d16', padding: '10px', borderRadius: '8px' }}>
            Este bloco funciona de forma 100% automática. Nenhuma configuração manual é necessária!
          </div>
        ) : (
          allKeys.map((key) => {
            const isAdvanced = advancedKeys.includes(key);
            if (isAdvanced && !showAdvancedAccordion && !isAdvancedMode) {
              return null; // Omitir no modo simples até abrir o acordeão
            }

            const info = FIELD_LABELS[key] || {
              label: key,
              helper: `Valor para ${key}`,
              placeholder: String(config[key] ?? ''),
            };

            const val = config[key];
            const isBool = typeof val === 'boolean';

            return (
              <div
                key={key}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                  background: '#0e1526',
                  padding: '10px 12px',
                  borderRadius: '10px',
                  border: '1px solid #1e293b',
                }}
              >
                <label style={{ fontSize: '12px', fontWeight: 600, color: '#f1f5f9' }}>
                  {info.label}
                </label>
                <span style={{ fontSize: '11px', color: '#64748b', lineHeight: '1.3' }}>
                  {info.helper}
                </span>

                {isBool ? (
                  <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                    <button
                      type="button"
                      onClick={() => handleConfigChange(key, true)}
                      style={{
                        padding: '5px 12px',
                        fontSize: '11px',
                        borderRadius: '6px',
                        border: val ? '1px solid #22c55e' : '1px solid #1e293b',
                        background: val ? '#14532d' : '#090d16',
                        color: val ? '#86efac' : '#94a3b8',
                        cursor: 'pointer',
                        fontWeight: 600,
                      }}
                    >
                      Sim (Ativado)
                    </button>
                    <button
                      type="button"
                      onClick={() => handleConfigChange(key, false)}
                      style={{
                        padding: '5px 12px',
                        fontSize: '11px',
                        borderRadius: '6px',
                        border: !val ? '1px solid #ef4444' : '1px solid #1e293b',
                        background: !val ? '#7f1d1d' : '#090d16',
                        color: !val ? '#fca5a5' : '#94a3b8',
                        cursor: 'pointer',
                        fontWeight: 600,
                      }}
                    >
                      Não (Desativado)
                    </button>
                  </div>
                ) : (
                  <input
                    type="text"
                    value={val !== undefined ? String(val) : ''}
                    placeholder={info.placeholder}
                    onChange={(e) => handleConfigChange(key, e.target.value)}
                    style={{
                      width: '100%',
                      padding: '8px 10px',
                      background: '#090d16',
                      border: '1px solid #334155',
                      borderRadius: '6px',
                      color: '#f8fafc',
                      fontSize: '12px',
                      boxSizing: 'border-box',
                      marginTop: '4px',
                      outline: 'none',
                    }}
                    onFocus={(e) => (e.target.style.borderColor = '#38bdf8')}
                    onBlur={(e) => (e.target.style.borderColor = '#334155')}
                  />
                )}
              </div>
            );
          })
        )}
      </div>

      {/* ADVANCED OPTIONS TOGGLE (Se existirem opções técnicas) */}
      {advancedKeys.length > 0 && !isAdvancedMode && (
        <div style={{ marginTop: '4px' }}>
          <button
            type="button"
            onClick={() => setShowAdvancedAccordion(!showAdvancedAccordion)}
            style={{
              width: '100%',
              padding: '8px 12px',
              background: '#090d16',
              border: '1px dashed #334155',
              borderRadius: '8px',
              color: '#94a3b8',
              fontSize: '11px',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span>⚙️ Opções Técnicas Avançadas ({advancedKeys.length})</span>
            <span>{showAdvancedAccordion ? '▲ Recolher' : '▼ Expandir'}</span>
          </button>
          {!showAdvancedAccordion && (
            <div style={{ fontSize: '10px', color: '#64748b', marginTop: '4px', textAlign: 'center' }}>
              Valores recomendados de estúdio já estão configurados por padrão.
            </div>
          )}
        </div>
      )}

      {/* CONNECTIONS SUMMARY (Entradas e Saídas do Bloco) */}
      <div style={{ borderTop: '1px solid #1e293b', paddingTop: '12px' }}>
        <div style={{ fontSize: '12px', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase', marginBottom: '8px', letterSpacing: '0.5px' }}>
          O que este bloco conecta:
        </div>

        {/* Inputs */}
        <div style={{ marginBottom: '8px' }}>
          <span style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 600 }}>
            📥 Recebe do nó anterior:
          </span>
          {(!data.inputs || data.inputs.length === 0) ? (
            <div style={{ fontSize: '11px', color: '#64748b', fontStyle: 'italic', marginTop: '2px' }}>
              Nenhum (É o ponto de partida do fluxo).
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '4px' }}>
              {data.inputs.map((inp: any) => {
                const pColor = PORT_COLORS[inp.type] || PORT_COLORS.any;
                return (
                  <div
                    key={inp.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      background: '#090d16',
                      padding: '4px 8px',
                      borderRadius: '6px',
                    }}
                  >
                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: pColor }} />
                    <span style={{ fontSize: '11px', color: '#cbd5e1' }}>{inp.label || inp.id}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Outputs */}
        <div>
          <span style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 600 }}>
            📤 Entrega para o próximo nó:
          </span>
          {(!data.outputs || data.outputs.length === 0) ? (
            <div style={{ fontSize: '11px', color: '#64748b', fontStyle: 'italic', marginTop: '2px' }}>
              Nenhum (É o destino final do fluxo).
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '4px' }}>
              {data.outputs.map((out: any) => {
                const pColor = PORT_COLORS[out.type] || PORT_COLORS.any;
                return (
                  <div
                    key={out.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      background: '#090d16',
                      padding: '4px 8px',
                      borderRadius: '6px',
                    }}
                  >
                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: pColor }} />
                    <span style={{ fontSize: '11px', color: '#cbd5e1' }}>{out.label || out.id}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

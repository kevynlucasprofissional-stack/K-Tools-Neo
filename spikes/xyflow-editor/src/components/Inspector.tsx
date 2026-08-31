import { type Node } from '@xyflow/react';
import { useState } from 'react';

export function Inspector({ selectedNode, onNodeUpdate }: { selectedNode: Node | null, onNodeUpdate: (id: string, data: any) => void }) {
  const initialConfig = selectedNode?.data?.config || {};
  const [configValues, setConfigValues] = useState<any>(initialConfig);

  if (!selectedNode) {
    return <div className="inspector-empty">Select a node to inspect</div>;
  }

  const { data, type } = selectedNode;

  const handleConfigChange = (key: string, value: string) => {
    const newConfig = { ...configValues, [key]: value };
    setConfigValues(newConfig);
    onNodeUpdate(selectedNode.id, { config: newConfig });
  };

  return (
    <div className="inspector">
      <h3>Inspector</h3>
      <div style={{ marginBottom: '16px' }}>
        <strong>ID:</strong> <span style={{ fontSize: '12px' }}>{selectedNode.id}</span><br />
        <strong>Type:</strong> <span style={{ fontSize: '12px' }}>{type}</span>
      </div>

      {type === 'missing' && (
        <div style={{ background: '#fff3f3', padding: '8px', border: '1px solid #dc3545', color: '#dc3545', marginBottom: '16px' }}>
          <strong>Missing Node</strong>
          <p style={{ margin: '4px 0', fontSize: '12px' }}>
            Original Type: {String(data.originalType)}
          </p>
        </div>
      )}

      {!!data.config && Object.keys(data.config as any).length > 0 && (
        <div className="config-section">
          <h4>Configuration</h4>
          {Object.keys(data.config).map((key) => (
            <div key={key} style={{ marginBottom: '8px' }}>
              <label style={{ display: 'block', fontSize: '12px', marginBottom: '4px' }}>{key}</label>
              <input
                type="text"
                value={configValues[key] || ''}
                onChange={(e) => handleConfigChange(key, e.target.value)}
                style={{ width: '100%', padding: '4px', boxSizing: 'border-box' }}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

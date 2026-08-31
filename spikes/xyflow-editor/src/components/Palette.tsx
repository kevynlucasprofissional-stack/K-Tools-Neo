import { nodeCatalog } from '../fixtures';

export function Palette({ onAddNode }: { onAddNode: (type: string, data: any) => void }) {
  return (
    <div className="palette">
      <h3>Nodes</h3>
      <div className="node-list">
        {nodeCatalog.map((item) => (
          <div
            key={item.label}
            className="palette-item"
            style={{
              padding: '8px',
              margin: '8px 0',
              background: 'white',
              border: '1px solid #ccc',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
            onClick={() => onAddNode(item.type, item.defaultData)}
          >
            <strong>{item.label}</strong>
            <div style={{ fontSize: '10px', color: '#666' }}>{item.category}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

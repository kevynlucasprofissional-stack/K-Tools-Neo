import { useState, useMemo } from 'react';
import { nodeCatalog } from '../fixtures';

export function Palette({ onAddNode }: { onAddNode: (type: string, data: any) => void }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  const categories = useMemo(() => {
    const cats = new Set(nodeCatalog.map((n) => n.category));
    return ['All', ...Array.from(cats).sort()];
  }, []);

  const filteredNodes = useMemo(() => {
    return nodeCatalog.filter((item) => {
      const matchesSearch =
        item.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (item.type_id && item.type_id.toLowerCase().includes(searchTerm.toLowerCase()));
      const matchesCategory = selectedCategory === 'All' || item.category === selectedCategory;
      return matchesSearch && matchesCategory;
    });
  }, [searchTerm, selectedCategory]);

  return (
    <div className="palette" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ paddingBottom: '8px' }}>
        <h3 style={{ margin: '0 0 8px 0' }}>Node Packs ({filteredNodes.length})</h3>
        <input
          type="text"
          placeholder="Buscar nós..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={{
            width: '100%',
            padding: '6px 8px',
            border: '1px solid #ccc',
            borderRadius: '4px',
            boxSizing: 'border-box',
            fontSize: '12px',
          }}
        />
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '4px',
            marginTop: '8px',
            maxHeight: '60px',
            overflowY: 'auto',
          }}
        >
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              style={{
                fontSize: '10px',
                padding: '2px 6px',
                borderRadius: '12px',
                border: '1px solid',
                borderColor: selectedCategory === cat ? '#007bff' : '#ccc',
                background: selectedCategory === cat ? '#007bff' : '#f0f0f0',
                color: selectedCategory === cat ? '#fff' : '#333',
                cursor: 'pointer',
              }}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      <div className="node-list" style={{ flex: 1, overflowY: 'auto', paddingRight: '4px' }}>
        {filteredNodes.map((item) => (
          <div
            key={item.type_id || item.label}
            className="palette-item"
            style={{
              padding: '8px 10px',
              margin: '6px 0',
              background: 'white',
              border: '1px solid #ddd',
              borderRadius: '6px',
              cursor: 'pointer',
              transition: 'box-shadow 0.15s, border-color 0.15s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = '#007bff';
              e.currentTarget.style.boxShadow = '0 2px 5px rgba(0,123,255,0.15)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = '#ddd';
              e.currentTarget.style.boxShadow = 'none';
            }}
            onClick={() => onAddNode(item.type, item.defaultData)}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <strong style={{ fontSize: '12px' }}>{item.label}</strong>
              <span
                style={{
                  fontSize: '9px',
                  padding: '1px 5px',
                  background: '#e9ecef',
                  borderRadius: '3px',
                  color: '#495057',
                }}
              >
                {item.category}
              </span>
            </div>
            {item.type_id && (
              <div style={{ fontSize: '10px', color: '#888', marginTop: '2px', fontFamily: 'monospace' }}>
                {item.type_id}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

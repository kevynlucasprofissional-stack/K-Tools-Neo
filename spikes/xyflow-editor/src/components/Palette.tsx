import { useState, useMemo } from 'react';
import { nodeCatalog } from '../fixtures';

const CATEGORY_COLORS: Record<string, { border: string; bg: string; text: string }> = {
  Media: { border: '#ec4899', bg: 'rgba(236, 72, 153, 0.15)', text: '#f472b6' },
  Text: { border: '#10b981', bg: 'rgba(16, 185, 129, 0.15)', text: '#34d399' },
  PDF: { border: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)', text: '#f87171' },
  JSON: { border: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)', text: '#fbbf24' },
  Filesystem: { border: '#3b82f6', bg: 'rgba(59, 130, 246, 0.15)', text: '#60a5fa' },
  Images: { border: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.15)', text: '#a78bfa' },
  Documents: { border: '#06b6d4', bg: 'rgba(6, 182, 212, 0.15)', text: '#22d3ee' },
  Core: { border: '#64748b', bg: 'rgba(100, 116, 139, 0.15)', text: '#94a3b8' },
  Files: { border: '#6366f1', bg: 'rgba(99, 102, 241, 0.15)', text: '#818cf8' },
};

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
    <div
      className="palette"
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        fontFamily: 'Inter, system-ui, sans-serif',
        color: '#f8fafc',
      }}
    >
      <div style={{ paddingBottom: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <h3 style={{ margin: 0, fontSize: '14px', fontWeight: 600, color: '#f8fafc' }}>
            Biblioteca de Nós
          </h3>
          <span
            style={{
              fontSize: '10px',
              padding: '2px 8px',
              borderRadius: '10px',
              background: '#1e293b',
              color: '#38bdf8',
              fontWeight: 700,
            }}
          >
            {filteredNodes.length} nós
          </span>
        </div>

        {/* Search input */}
        <div style={{ position: 'relative', marginTop: '6px' }}>
          <input
            type="text"
            placeholder="Buscar nó por nome ou tipo..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px',
              background: '#0e1526',
              border: '1px solid #1e293b',
              borderRadius: '8px',
              color: '#f8fafc',
              fontSize: '12px',
              boxSizing: 'border-box',
              outline: 'none',
              transition: 'all 0.2s',
            }}
            onFocus={(e) => (e.target.style.borderColor = '#38bdf8')}
            onBlur={(e) => (e.target.style.borderColor = '#1e293b')}
          />
        </div>

        {/* Category Pills */}
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '4px',
            marginTop: '8px',
            maxHeight: '65px',
            overflowY: 'auto',
          }}
        >
          {categories.map((cat) => {
            const isSelected = selectedCategory === cat;
            const theme = CATEGORY_COLORS[cat];
            return (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                style={{
                  fontSize: '10px',
                  fontWeight: 600,
                  padding: '3px 8px',
                  borderRadius: '12px',
                  border: isSelected ? '1px solid #38bdf8' : '1px solid #1e293b',
                  background: isSelected ? '#1e3a5f' : '#0e1526',
                  color: isSelected ? '#38bdf8' : theme ? theme.text : '#94a3b8',
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                {cat}
              </button>
            );
          })}
        </div>
      </div>

      {/* Node Cards List */}
      <div
        className="node-list"
        style={{
          flex: 1,
          overflowY: 'auto',
          paddingRight: '4px',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
        }}
      >
        {filteredNodes.map((item) => {
          const theme = CATEGORY_COLORS[item.category] || CATEGORY_COLORS.Core;
          return (
            <div
              key={item.type_id || item.label}
              className="palette-item"
              style={{
                padding: '10px 12px',
                background: '#131b2e',
                border: '1px solid #1e293b',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.15s cubic-bezier(0.4, 0, 0.2, 1)',
                display: 'flex',
                flexDirection: 'column',
                gap: '3px',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = '#38bdf8';
                e.currentTarget.style.background = '#18223a';
                e.currentTarget.style.transform = 'translateY(-1px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = '#1e293b';
                e.currentTarget.style.background = '#131b2e';
                e.currentTarget.style.transform = 'none';
              }}
              onClick={() => onAddNode(item.type, item.defaultData)}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <strong style={{ fontSize: '12px', color: '#f8fafc' }}>{item.label}</strong>
                <span
                  style={{
                    fontSize: '9px',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    padding: '2px 6px',
                    borderRadius: '8px',
                    background: theme.bg,
                    color: theme.text,
                    border: `1px solid ${theme.border}33`,
                  }}
                >
                  {item.category}
                </span>
              </div>
              {item.type_id && (
                <div style={{ fontSize: '10px', color: '#64748b', fontFamily: 'monospace' }}>
                  {item.type_id}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

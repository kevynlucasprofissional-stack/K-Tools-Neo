import { useState, useMemo } from 'react';
import { nodeCatalog } from '../fixtures';

const CATEGORY_COLORS: Record<string, { border: string; bg: string; text: string }> = {
  Mídia: { border: '#ec4899', bg: 'rgba(236, 72, 153, 0.15)', text: '#f472b6' },
  Arquivos: { border: '#3b82f6', bg: 'rgba(59, 130, 246, 0.15)', text: '#60a5fa' },
  Texto: { border: '#10b981', bg: 'rgba(16, 185, 129, 0.15)', text: '#34d399' },
  PDF: { border: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)', text: '#f87171' },
  Imagens: { border: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.15)', text: '#a78bfa' },
  Sistema: { border: '#6366f1', bg: 'rgba(99, 102, 241, 0.15)', text: '#818cf8' },
  Core: { border: '#64748b', bg: 'rgba(100, 116, 139, 0.15)', text: '#94a3b8' },
};

export function Palette({
  onAddNode,
  isAdvancedMode,
}: {
  onAddNode: (type: string, data: any) => void;
  isAdvancedMode: boolean;
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('Todos');

  const categories = useMemo(() => {
    const cats = new Set(nodeCatalog.map((n) => n.category || 'Geral'));
    return ['Todos', ...Array.from(cats).sort()];
  }, []);

  const filteredNodes = useMemo(() => {
    return nodeCatalog.filter((item) => {
      const label = item.label || '';
      const desc = item.description || '';
      const category = item.category || '';
      const typeId = item.type_id || '';

      const term = searchTerm.toLowerCase();
      const matchesSearch =
        label.toLowerCase().includes(term) ||
        desc.toLowerCase().includes(term) ||
        category.toLowerCase().includes(term) ||
        typeId.toLowerCase().includes(term);

      const matchesCategory = selectedCategory === 'Todos' || category === selectedCategory;
      return matchesSearch && matchesCategory;
    });
  }, [searchTerm, selectedCategory]);

  const onDragStart = (event: React.DragEvent, nodeItem: any) => {
    event.dataTransfer.setData(
      'application/reactflow',
      JSON.stringify({
        type: nodeItem.type,
        data: {
          ...nodeItem.defaultData,
          label: nodeItem.label,
          category: nodeItem.category,
          description: nodeItem.description,
          icon: nodeItem.icon,
        },
      })
    );
    event.dataTransfer.effectAllowed = 'move';
  };

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
          <div>
            <h3 style={{ margin: 0, fontSize: '14px', fontWeight: 700, color: '#f8fafc' }}>
              Biblioteca de Ações
            </h3>
            <span style={{ fontSize: '11px', color: '#64748b' }}>
              Arraste para o fluxo para usar
            </span>
          </div>
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
            {filteredNodes.length} blocos
          </span>
        </div>

        {/* Search input */}
        <div style={{ position: 'relative', marginTop: '6px' }}>
          <input
            type="text"
            placeholder="O que você deseja fazer? (ex: extrair som, juntar vídeos)..."
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
          gap: '8px',
        }}
      >
        {filteredNodes.map((item) => {
          const theme = CATEGORY_COLORS[item.category] || CATEGORY_COLORS.Core;
          return (
            <div
              key={item.type_id || item.label}
              className="palette-card"
              draggable
              onDragStart={(e) => onDragStart(e, item)}
              onClick={() =>
                onAddNode(item.type, {
                  ...item.defaultData,
                  label: item.label,
                  category: item.category,
                  description: item.description,
                })
              }
              style={{
                padding: '10px 12px',
                background: '#0e1526',
                border: '1px solid #1e293b',
                borderRadius: '10px',
                cursor: 'grab',
                transition: 'all 0.15s ease',
                display: 'flex',
                flexDirection: 'column',
                gap: '4px',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = theme.border;
                e.currentTarget.style.background = '#131e36';
                e.currentTarget.style.transform = 'translateY(-1px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = '#1e293b';
                e.currentTarget.style.background = '#0e1526';
                e.currentTarget.style.transform = 'none';
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', fontWeight: 600, color: '#f8fafc' }}>
                  {item.label}
                </span>
                <span
                  style={{
                    fontSize: '9px',
                    fontWeight: 700,
                    padding: '1px 6px',
                    borderRadius: '8px',
                    background: theme.bg,
                    color: theme.text,
                    border: `1px solid ${theme.border}33`,
                  }}
                >
                  {item.category}
                </span>
              </div>

              {item.description && (
                <div style={{ fontSize: '11px', color: '#94a3b8', lineHeight: '1.3' }}>
                  {item.description}
                </div>
              )}

              {isAdvancedMode && item.type_id && (
                <div style={{ fontSize: '9px', fontFamily: 'monospace', color: '#64748b' }}>
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

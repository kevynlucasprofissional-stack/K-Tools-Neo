import { useState, useEffect, useRef } from 'react';
import { nodeCatalog } from '../fixtures';

export function QuickSearch({
  isOpen,
  onClose,
  onSelectNode,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSelectNode: (type: string, data: any) => void;
}) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const filtered = nodeCatalog.filter((item) => {
    const q = query.toLowerCase();
    return (
      item.label.toLowerCase().includes(q) ||
      item.category.toLowerCase().includes(q) ||
      (item.type_id && item.type_id.toLowerCase().includes(q))
    );
  });

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % Math.max(1, filtered.length));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + filtered.length) % Math.max(1, filtered.length));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filtered[selectedIndex]) {
        onSelectNode(filtered[selectedIndex].type, filtered[selectedIndex].defaultData);
        onClose();
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(5, 8, 15, 0.75)',
        backdropFilter: 'blur(4px)',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        paddingTop: '120px',
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '560px',
          maxWidth: '90vw',
          backgroundColor: '#0e1526',
          borderRadius: '14px',
          border: '1px solid #334155',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.7), 0 0 30px rgba(56, 189, 248, 0.15)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          animation: 'fadeIn 0.15s ease-out',
        }}
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
      >
        {/* Search Input Bar */}
        <div
          style={{
            padding: '14px 18px',
            borderBottom: '1px solid #1e293b',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
          }}
        >
          <span style={{ fontSize: '18px', color: '#38bdf8' }}>🔍</span>
          <input
            ref={inputRef}
            type="text"
            placeholder="Digite para buscar nós... (↑ ↓ para navegar, Enter para inserir)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              color: '#f8fafc',
              fontSize: '14px',
              outline: 'none',
              fontFamily: 'inherit',
            }}
          />
          <span
            style={{
              fontSize: '10px',
              padding: '2px 6px',
              background: '#1e293b',
              borderRadius: '4px',
              color: '#94a3b8',
            }}
          >
            ESC para fechar
          </span>
        </div>

        {/* Results List */}
        <div style={{ maxHeight: '360px', overflowY: 'auto', padding: '8px' }}>
          {filtered.length === 0 ? (
            <div style={{ padding: '24px', textAlign: 'center', color: '#64748b', fontSize: '13px' }}>
              Nenhum nó encontrado para "{query}".
            </div>
          ) : (
            filtered.map((item, idx) => {
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={item.type_id || item.label}
                  style={{
                    padding: '10px 14px',
                    borderRadius: '8px',
                    background: isSelected ? '#1e293b' : 'transparent',
                    border: isSelected ? '1px solid #38bdf8' : '1px solid transparent',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    transition: 'all 0.1s',
                  }}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  onClick={() => {
                    onSelectNode(item.type, item.defaultData);
                    onClose();
                  }}
                >
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <strong style={{ fontSize: '13px', color: isSelected ? '#38bdf8' : '#f8fafc' }}>
                        {item.label}
                      </strong>
                      <span
                        style={{
                          fontSize: '9px',
                          padding: '1px 6px',
                          borderRadius: '8px',
                          background: '#131b2e',
                          color: '#94a3b8',
                        }}
                      >
                        {item.category}
                      </span>
                    </div>
                    {item.type_id && (
                      <span style={{ fontSize: '11px', color: '#64748b', fontFamily: 'monospace' }}>
                        {item.type_id}
                      </span>
                    )}
                  </div>

                  {isSelected && (
                    <span style={{ fontSize: '11px', color: '#38bdf8', fontWeight: 600 }}>
                      Inserir ↵
                    </span>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}

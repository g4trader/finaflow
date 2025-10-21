import { useState, useEffect } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';

interface CollapsibleRowProps {
  id: string;
  title: string;
  level: 'group' | 'subgroup' | 'account';
  children?: React.ReactNode;
  value?: number | string;
  className?: string;
  defaultExpanded?: boolean;
  storageKey?: string;
}

export default function CollapsibleRow({
  id,
  title,
  level,
  children,
  value,
  className = '',
  defaultExpanded = true,
  storageKey = 'cash-flow-expanded'
}: CollapsibleRowProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  // Carregar estado do localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(storageKey);
      if (stored) {
        try {
          const expandedState = JSON.parse(stored);
          if (expandedState[id] !== undefined) {
            setIsExpanded(expandedState[id]);
          }
        } catch (e) {
          console.error('Erro ao carregar estado:', e);
        }
      }
    }
  }, [id, storageKey]);

  // Salvar estado no localStorage
  const toggleExpanded = () => {
    const newState = !isExpanded;
    setIsExpanded(newState);

    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(storageKey);
      const expandedState = stored ? JSON.parse(stored) : {};
      expandedState[id] = newState;
      localStorage.setItem(storageKey, JSON.stringify(expandedState));
    }
  };

  // Estilos baseados no nível
  const getLevelStyles = () => {
    switch (level) {
      case 'group':
        return {
          row: 'bg-blue-50 font-bold text-gray-900 border-b-2 border-blue-200',
          indent: 'pl-2',
          icon: 'text-blue-600'
        };
      case 'subgroup':
        return {
          row: 'bg-gray-50 font-semibold text-gray-800 border-b border-gray-200',
          indent: 'pl-8',
          icon: 'text-gray-600'
        };
      case 'account':
        return {
          row: 'bg-white text-gray-700',
          indent: 'pl-16',
          icon: 'text-gray-400'
        };
    }
  };

  const styles = getLevelStyles();
  const hasChildren = children !== null && children !== undefined;

  return (
    <>
      <tr className={`${styles.row} hover:bg-opacity-80 transition-colors ${className}`}>
        <td className={`py-3 ${styles.indent}`}>
          <div className="flex items-center gap-2">
            {hasChildren && (
              <button
                onClick={toggleExpanded}
                className={`${styles.icon} hover:bg-gray-200 rounded p-1 transition-colors`}
                aria-label={isExpanded ? 'Retrair' : 'Expandir'}
              >
                {isExpanded ? (
                  <ChevronDown className="w-4 h-4" />
                ) : (
                  <ChevronRight className="w-4 h-4" />
                )}
              </button>
            )}
            {!hasChildren && <span className="w-6" />}
            <span className={level === 'account' ? 'text-sm' : ''}>{title}</span>
          </div>
        </td>
        <td className="py-3 text-right pr-4">
          {value !== undefined && value}
        </td>
      </tr>
      {hasChildren && isExpanded && children}
    </>
  );
}


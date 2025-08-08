import React from 'react';
import { motion } from 'framer-motion';

interface TableProps {
  children: React.ReactNode;
  className?: string;
}

interface TableHeaderProps {
  children: React.ReactNode;
  className?: string;
}

interface TableBodyProps {
  children: React.ReactNode;
  className?: string;
}

interface TableRowProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

interface TableCellProps {
  children: React.ReactNode;
  className?: string;
  header?: boolean;
}

const Table: React.FC<TableProps> & {
  Header: React.FC<TableHeaderProps>;
  Body: React.FC<TableBodyProps>;
  Row: React.FC<TableRowProps>;
  Cell: React.FC<TableCellProps>;
} = ({ children, className = '' }) => {
  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
      <div className="overflow-x-auto">
        <table className={`min-w-full divide-y divide-gray-200 ${className}`}>
          {children}
        </table>
      </div>
    </div>
  );
};

const TableHeader: React.FC<TableHeaderProps> = ({ children, className = '' }) => (
  <thead className={`bg-gray-50 ${className}`}>
    {children}
  </thead>
);

const TableBody: React.FC<TableBodyProps> = ({ children, className = '' }) => (
  <tbody className={`divide-y divide-gray-200 bg-white ${className}`}>
    {children}
  </tbody>
);

const TableRow: React.FC<TableRowProps> = ({ children, className = '', onClick }) => (
  <motion.tr
    className={`${onClick ? 'cursor-pointer hover:bg-gray-50' : ''} ${className}`}
    onClick={onClick}
    whileHover={onClick ? { backgroundColor: '#f9fafb' } : {}}
    transition={{ duration: 0.2 }}
  >
    {children}
  </motion.tr>
);

const TableCell: React.FC<TableCellProps> = ({ children, className = '', header = false }) => {
  const Tag = header ? 'th' : 'td';
  const baseClasses = header
    ? 'px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'
    : 'px-6 py-4 whitespace-nowrap text-sm text-gray-900';

  return (
    <Tag className={`${baseClasses} ${className}`}>
      {children}
    </Tag>
  );
};

Table.Header = TableHeader;
Table.Body = TableBody;
Table.Row = TableRow;
Table.Cell = TableCell;

export default Table;


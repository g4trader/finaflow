import React from 'react';

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
  hover?: boolean;
}

interface TableCellProps {
  children: React.ReactNode;
  className?: string;
  header?: boolean;
  align?: 'left' | 'center' | 'right';
}

const Table: React.FC<TableProps> & {
  Header: React.FC<TableHeaderProps>;
  Body: React.FC<TableBodyProps>;
  Row: React.FC<TableRowProps>;
  Cell: React.FC<TableCellProps>;
} = ({ children, className = '' }) => {
  return (
    <div className="overflow-x-auto">
      <table className={`min-w-full divide-y divide-gray-200 ${className}`}>
        {children}
      </table>
    </div>
  );
};

const TableHeader: React.FC<TableHeaderProps> = ({ children, className = '' }) => (
  <thead className={`bg-gray-50 ${className}`}>
    {children}
  </thead>
);

const TableBody: React.FC<TableBodyProps> = ({ children, className = '' }) => (
  <tbody className={`bg-white divide-y divide-gray-200 ${className}`}>
    {children}
  </tbody>
);

const TableRow: React.FC<TableRowProps> = ({ 
  children, 
  className = '', 
  hover = true 
}) => (
  <tr className={`
    ${hover ? 'hover:bg-gray-50 transition-colors duration-200' : ''} 
    ${className}
  `}>
    {children}
  </tr>
);

const TableCell: React.FC<TableCellProps> = ({ 
  children, 
  className = '', 
  header = false,
  align = 'left'
}) => {
  const alignClasses = {
    left: 'text-left',
    center: 'text-center',
    right: 'text-right',
  };

  const baseClasses = `px-6 py-4 whitespace-nowrap ${alignClasses[align]}`;
  
  if (header) {
    return (
      <th className={`
        ${baseClasses} 
        text-xs font-medium text-gray-500 uppercase tracking-wider 
        ${className}
      `}>
        {children}
      </th>
    );
  }

  return (
    <td className={`
      ${baseClasses} 
      text-sm text-gray-900 
      ${className}
    `}>
      {children}
    </td>
  );
};

Table.Header = TableHeader;
Table.Body = TableBody;
Table.Row = TableRow;
Table.Cell = TableCell;

export default Table;
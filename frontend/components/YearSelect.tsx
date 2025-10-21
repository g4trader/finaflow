import React from 'react';
import { ChevronDown } from 'lucide-react';

interface YearSelectProps {
  year: number;
  onYearChange: (year: number) => void;
  disabled?: boolean;
}

const YearSelect: React.FC<YearSelectProps> = ({ 
  year, 
  onYearChange, 
  disabled = false 
}) => {
  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 11 }, (_, i) => currentYear - 5 + i);

  return (
    <div className="relative">
      <select
        value={year}
        onChange={(e) => onYearChange(parseInt(e.target.value, 10))}
        disabled={disabled}
        className="appearance-none bg-white border border-gray-300 rounded-md px-4 py-2 pr-8 text-sm font-medium text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        aria-label="Selecionar ano"
      >
        {years.map((y) => (
          <option key={y} value={y}>
            {y}
          </option>
        ))}
      </select>
      <ChevronDown className="absolute right-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
    </div>
  );
};

export default YearSelect;

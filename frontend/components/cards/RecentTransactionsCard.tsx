import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Calendar, DollarSign } from 'lucide-react';
import Link from 'next/link';
import type { TransactionsResponse } from '../../types/dashboard';

interface RecentTransactionsCardProps {
  data: TransactionsResponse;
  year: number;
  isLoading?: boolean;
}

const RecentTransactionsCard: React.FC<RecentTransactionsCardProps> = ({ 
  data, 
  year, 
  isLoading = false 
}) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'revenue':
        return <DollarSign className="w-4 h-4 text-green-600" />;
      case 'expense':
        return <DollarSign className="w-4 h-4 text-red-600" />;
      case 'cost':
        return <DollarSign className="w-4 h-4 text-orange-600" />;
      default:
        return <DollarSign className="w-4 h-4 text-gray-600" />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'revenue':
        return 'text-green-600 bg-green-50';
      case 'expense':
        return 'text-red-600 bg-red-50';
      case 'cost':
        return 'text-orange-600 bg-orange-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'revenue':
        return 'Receita';
      case 'expense':
        return 'Despesa';
      case 'cost':
        return 'Custo';
      default:
        return 'Outro';
    }
  };

  if (isLoading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
      >
        <div className="animate-pulse">
          <div className="flex items-center justify-between mb-6">
            <div className="h-6 bg-gray-200 rounded w-40"></div>
            <div className="h-4 bg-gray-200 rounded w-16"></div>
          </div>
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gray-200 rounded"></div>
                  <div className="space-y-1">
                    <div className="h-4 bg-gray-200 rounded w-32"></div>
                    <div className="h-3 bg-gray-200 rounded w-20"></div>
                  </div>
                </div>
                <div className="h-4 bg-gray-200 rounded w-16"></div>
              </div>
            ))}
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
    >
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          Transações Recentes
        </h3>
        <Link 
          href={`/transactions?year=${year}`}
          className="text-sm text-blue-600 hover:text-blue-800 font-medium flex items-center"
        >
          Ver todas
          <ArrowRight className="w-4 h-4 ml-1" />
        </Link>
      </div>

      {!data.items || data.items.length === 0 ? (
        <div className="text-center py-8">
          <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 text-sm">
            Nenhuma transação encontrada para {year}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {(data.items || []).map((transaction, index) => (
            <motion.div
              key={transaction.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors duration-150"
            >
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-full ${getTypeColor(transaction.type)}`}>
                  {getTypeIcon(transaction.type)}
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {transaction.description}
                  </p>
                  <div className="flex items-center space-x-2 text-xs text-gray-500">
                    <span>{formatDate(transaction.date)}</span>
                    <span>•</span>
                    <span>{transaction.account}</span>
                    <span>•</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTypeColor(transaction.type)}`}>
                      {getTypeLabel(transaction.type)}
                    </span>
                  </div>
                </div>
              </div>
              <div className="text-right">
                <p className={`text-sm font-medium ${
                  transaction.type === 'revenue' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {transaction.type === 'revenue' ? '+' : '-'}{formatCurrency(transaction.amount)}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  );
};

export default RecentTransactionsCard;

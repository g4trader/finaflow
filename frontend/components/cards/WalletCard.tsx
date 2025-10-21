import React from 'react';
import { motion } from 'framer-motion';
import { Wallet, Building2, TrendingUp } from 'lucide-react';
import type { WalletResponse } from '../../types/dashboard';

interface WalletCardProps {
  data: WalletResponse;
  isLoading?: boolean;
}

const WalletCard: React.FC<WalletCardProps> = ({ data, isLoading = false }) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  if (isLoading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg shadow-lg border border-purple-700 p-6 text-white animate-pulse"
      >
        <div className="flex items-center justify-between mb-4">
          <div className="space-y-2">
            <div className="h-6 bg-white bg-opacity-20 rounded w-32"></div>
            <div className="h-8 bg-white bg-opacity-20 rounded w-24"></div>
          </div>
          <div className="w-8 h-8 bg-white bg-opacity-20 rounded"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white bg-opacity-20 rounded-lg p-4">
              <div className="space-y-2">
                <div className="h-4 bg-white bg-opacity-20 rounded w-20"></div>
                <div className="h-6 bg-white bg-opacity-20 rounded w-16"></div>
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
      className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg shadow-lg border border-purple-700 p-6 text-white"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">💰 Saldo Disponível</h3>
        <span className="text-3xl font-bold">{formatCurrency(data.totalAvailable)}</span>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Contas Bancárias */}
        <div className="bg-white bg-opacity-20 rounded-lg p-4">
          <div className="flex items-center mb-2">
            <Building2 className="w-4 h-4 mr-2" />
            <p className="text-purple-100 text-sm font-medium">Contas Bancárias</p>
          </div>
          <p className="text-2xl font-bold mb-2">
            {formatCurrency((data.bankAccounts || []).reduce((sum, account) => sum + account.amount, 0))}
          </p>
          {data.bankAccounts && data.bankAccounts.length > 0 && (
            <div className="space-y-1">
              {(data.bankAccounts || []).slice(0, 3).map((account, idx) => (
                <div key={idx} className="text-xs text-purple-100 flex justify-between">
                  <span className="truncate mr-2">{account.label}</span>
                  <span className="font-medium">{formatCurrency(account.amount)}</span>
                </div>
              ))}
              {data.bankAccounts && data.bankAccounts.length > 3 && (
                <div className="text-xs text-purple-100">
                  +{data.bankAccounts.length - 3} mais
                </div>
              )}
            </div>
          )}
        </div>

        {/* Caixa / Dinheiro */}
        <div className="bg-white bg-opacity-20 rounded-lg p-4">
          <div className="flex items-center mb-2">
            <Wallet className="w-4 h-4 mr-2" />
            <p className="text-purple-100 text-sm font-medium">Caixa / Dinheiro</p>
          </div>
          <p className="text-2xl font-bold mb-2">
            {formatCurrency((data.cash || []).reduce((sum, cash) => sum + cash.amount, 0))}
          </p>
          {data.cash && data.cash.length > 0 && (
            <div className="space-y-1">
              {(data.cash || []).slice(0, 3).map((cash, idx) => (
                <div key={idx} className="text-xs text-purple-100 flex justify-between">
                  <span className="truncate mr-2">{cash.label}</span>
                  <span className="font-medium">{formatCurrency(cash.amount)}</span>
                </div>
              ))}
              {data.cash && data.cash.length > 3 && (
                <div className="text-xs text-purple-100">
                  +{data.cash.length - 3} mais
                </div>
              )}
            </div>
          )}
        </div>

        {/* Investimentos */}
        <div className="bg-white bg-opacity-20 rounded-lg p-4">
          <div className="flex items-center mb-2">
            <TrendingUp className="w-4 h-4 mr-2" />
            <p className="text-purple-100 text-sm font-medium">Investimentos</p>
          </div>
          <p className="text-2xl font-bold mb-2">
            {formatCurrency((data.investments || []).reduce((sum, investment) => sum + investment.amount, 0))}
          </p>
          {data.investments && data.investments.length > 0 && (
            <div className="space-y-1">
              {(data.investments || []).slice(0, 3).map((investment, idx) => (
                <div key={idx} className="text-xs text-purple-100 flex justify-between">
                  <span className="truncate mr-2">{investment.label}</span>
                  <span className="font-medium">{formatCurrency(investment.amount)}</span>
                </div>
              ))}
              {data.investments && data.investments.length > 3 && (
                <div className="text-xs text-purple-100">
                  +{data.investments.length - 3} mais
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default WalletCard;

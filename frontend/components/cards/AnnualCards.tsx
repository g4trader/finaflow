import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, DollarSign, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import type { AnnualSummaryResponse } from '../../types/dashboard';

interface AnnualCardsProps {
  data: AnnualSummaryResponse;
  isLoading?: boolean;
}

const AnnualCards: React.FC<AnnualCardsProps> = ({ data, isLoading = false }) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const getTrendIcon = (current: number, previous?: number) => {
    if (!previous || previous === 0) return null;
    const trend = current > previous ? 'up' : 'down';
    return trend === 'up' ? (
      <ArrowUpRight className="w-4 h-4 text-green-600 mr-1" />
    ) : (
      <ArrowDownRight className="w-4 h-4 text-red-600 mr-1" />
    );
  };

  const getTrendColor = (current: number, previous?: number) => {
    if (!previous || previous === 0) return 'text-gray-600';
    return current > previous ? 'text-green-600' : 'text-red-600';
  };

  const getTrendText = (current: number, previous?: number) => {
    if (!previous || previous === 0) return 'Total do Ano';
    const percentage = ((current - previous) / previous * 100).toFixed(1);
    const direction = current > previous ? '+' : '';
    return `${direction}${percentage}% vs ano anterior`;
  };

  const cards = [
    {
      title: 'Receita Total',
      value: data.totals.revenue,
      icon: <TrendingUp className="w-6 h-6 text-green-600" />,
      trend: data.ytdComparison?.currentYTD,
      previousTrend: data.ytdComparison?.lastYearYTD,
      color: 'text-green-600'
    },
    {
      title: 'Despesas Totais',
      value: data.totals.expense,
      icon: <TrendingDown className="w-6 h-6 text-red-600" />,
      trend: data.ytdComparison?.currentYTD,
      previousTrend: data.ytdComparison?.lastYearYTD,
      color: 'text-red-600'
    },
    {
      title: 'Custos Totais',
      value: data.totals.cost,
      icon: <DollarSign className="w-6 h-6 text-orange-600" />,
      trend: data.ytdComparison?.currentYTD,
      previousTrend: data.ytdComparison?.lastYearYTD,
      color: 'text-orange-600'
    }
  ];

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 animate-pulse">
            <div className="flex items-center justify-between">
              <div className="space-y-2">
                <div className="h-4 bg-gray-200 rounded w-24"></div>
                <div className="h-8 bg-gray-200 rounded w-32"></div>
              </div>
              <div className="w-6 h-6 bg-gray-200 rounded"></div>
            </div>
            <div className="mt-4">
              <div className="h-4 bg-gray-200 rounded w-28"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {cards.map((card, index) => (
        <motion.div
          key={card.title}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
          className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">{card.title}</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(card.value)}
              </p>
            </div>
            {card.icon}
          </div>
          <div className="mt-4 flex items-center text-sm">
            {getTrendIcon(card.trend, card.previousTrend)}
            <span className={getTrendColor(card.trend, card.previousTrend)}>
              {getTrendText(card.trend, card.previousTrend)}
            </span>
          </div>
        </motion.div>
      ))}
    </div>
  );
};

export default AnnualCards;

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import Layout from '../components/layout/Layout';
import { useAuth } from '../context/AuthContext';
import { getApi } from '../utils/api-client';
import { TrendingUp, TrendingDown, Calendar } from 'lucide-react';

interface CashFlowData {
  categoria: string;
  nivel: number; // 0: Grupo principal, 1: Subgrupo, 2: Conta
  meses: {
    [mes: string]: {
      previsto: number;
      realizado: number;
      ah: number; // Análise Horizontal (% realizado/previsto)
      av: number; // Análise Vertical (% do total)
    }
  };
}

const CashFlow: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [cashFlowData, setCashFlowData] = useState<CashFlowData[]>([]);
  const [selectedMonth, setSelectedMonth] = useState<string | null>(null);
  
  const meses = [
    'JANEIRO', 'FEVEREIRO', 'MARÇO', 'ABRIL', 'MAIO', 'JUNHO',
    'JULHO', 'AGOSTO', 'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO'
  ];

  useEffect(() => {
    if (user?.business_unit_id) {
      loadCashFlowData();
    }
  }, [user, selectedYear]);

  const loadCashFlowData = async () => {
    setLoading(true);
    try {
      // Buscar fluxo de caixa calculado pelo backend
      const api = await getApi();
      const response = await api.get(`/api/v1/cash-flow/previsto-realizado?year=${selectedYear}`);
      
      if (response.data.success) {
        setCashFlowData(response.data.data || []);
      } else {
        console.error('Erro ao carregar fluxo de caixa:', response.data.message);
      }
    } catch (error) {
      console.error('Erro ao carregar fluxo de caixa:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value.toFixed(0)}%`;
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Fluxo de Caixa</h1>
            <p className="text-gray-600 mt-1">
              Análise Previsto x Realizado - {selectedYear}
            </p>
          </div>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2">
              <Calendar size={20} className="text-gray-600" />
              <select
                value={selectedYear}
                onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                {[2024, 2025, 2026].map(year => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </select>
            </label>
          </div>
        </div>

        {/* Filtro de Mês */}
        <div className="bg-white rounded-lg shadow-md p-4">
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedMonth(null)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedMonth === null
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Todos os Meses
            </button>
            {meses.map(mes => (
              <button
                key={mes}
                onClick={() => setSelectedMonth(mes)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  selectedMonth === mes
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {mes.substring(0, 3)}
              </button>
            ))}
          </div>
        </div>

        {/* Tabela de Fluxo de Caixa */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase sticky left-0 bg-gray-50 z-10">
                    Categoria
                  </th>
                  {(selectedMonth ? [selectedMonth] : meses).map(mes => (
                    <React.Fragment key={mes}>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase border-l-2 border-gray-300" colSpan={4}>
                        {mes}
                      </th>
                    </React.Fragment>
                  ))}
                </tr>
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 sticky left-0 bg-gray-50 z-10"></th>
                  {(selectedMonth ? [selectedMonth] : meses).map(mes => (
                    <React.Fragment key={mes}>
                      <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 bg-blue-50 border-l-2 border-gray-300">Previsto</th>
                      <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 bg-green-50">Realizado</th>
                      <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 bg-yellow-50">AH%</th>
                      <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 bg-purple-50">AV%</th>
                    </React.Fragment>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr>
                    <td colSpan={1 + (selectedMonth ? 4 : meses.length * 4)} className="px-6 py-12 text-center text-gray-500">
                      Carregando...
                    </td>
                  </tr>
                ) : cashFlowData.length === 0 ? (
                  <tr>
                    <td colSpan={1 + (selectedMonth ? 4 : meses.length * 4)} className="px-6 py-12 text-center text-gray-500">
                      Nenhum dado encontrado
                    </td>
                  </tr>
                ) : (
                  cashFlowData.map((row, idx) => (
                    <tr key={idx} className={`hover:bg-gray-50 ${row.nivel === 0 ? 'font-semibold bg-gray-50' : ''}`}>
                      <td className={`px-6 py-3 text-sm text-gray-900 sticky left-0 bg-white ${row.nivel === 0 ? 'font-bold' : ''}`}>
                        <span style={{ marginLeft: `${row.nivel * 20}px` }}>
                          {row.categoria}
                        </span>
                      </td>
                      {(selectedMonth ? [selectedMonth] : meses).map(mes => {
                        const mesData = row.meses[mes];
                        return (
                          <React.Fragment key={mes}>
                            <td className="px-3 py-3 text-sm text-right text-gray-700 border-l-2 border-gray-300 bg-blue-50">
                              {formatCurrency(mesData.previsto)}
                            </td>
                            <td className="px-3 py-3 text-sm text-right text-gray-900 font-medium bg-green-50">
                              {formatCurrency(mesData.realizado)}
                            </td>
                            <td className={`px-3 py-3 text-sm text-right font-semibold bg-yellow-50 ${
                              mesData.ah >= 100 ? 'text-green-600' : 
                              mesData.ah >= 80 ? 'text-yellow-600' : 'text-red-600'
                            }`}>
                              <div className="flex items-center justify-end gap-1">
                                {mesData.ah >= 100 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                                {formatPercent(mesData.ah)}
                              </div>
                            </td>
                            <td className="px-3 py-3 text-sm text-right text-gray-600 bg-purple-50">
                              {formatPercent(mesData.av)}
                            </td>
                          </React.Fragment>
                        );
                      })}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Legenda */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Legenda</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="flex items-center gap-2">
              <div className="w-12 h-8 bg-blue-50 border border-blue-200 rounded"></div>
              <div>
                <div className="text-sm font-medium">Previsto</div>
                <div className="text-xs text-gray-500">Valores previstos</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-12 h-8 bg-green-50 border border-green-200 rounded"></div>
              <div>
                <div className="text-sm font-medium">Realizado</div>
                <div className="text-xs text-gray-500">Valores realizados</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-12 h-8 bg-yellow-50 border border-yellow-200 rounded"></div>
              <div>
                <div className="text-sm font-medium">AH%</div>
                <div className="text-xs text-gray-500">Análise Horizontal</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-12 h-8 bg-purple-50 border border-purple-200 rounded"></div>
              <div>
                <div className="text-sm font-medium">AV%</div>
                <div className="text-xs text-gray-500">Análise Vertical</div>
              </div>
            </div>
          </div>
          
          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-sm text-gray-600">
              <strong>AH (Análise Horizontal)</strong>: Percentual de realização em relação ao previsto. 
              <span className="text-green-600 font-medium">≥100%</span> = Meta atingida, 
              <span className="text-yellow-600 font-medium">80-99%</span> = Atenção, 
              <span className="text-red-600 font-medium">&lt;80%</span> = Abaixo da meta
            </p>
            <p className="text-sm text-gray-600 mt-2">
              <strong>AV (Análise Vertical)</strong>: Percentual em relação ao total de receitas do mês
            </p>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default CashFlow;


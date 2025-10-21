import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import Layout from '../components/layout/Layout';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { Calendar, ChevronLeft, ChevronRight } from 'lucide-react';

interface DailyCashFlow {
  categoria: string;
  nivel: number;
  dias: { [dia: number]: number }; // dia -> valor
}

const DailyCashFlow: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [cashFlowData, setCashFlowData] = useState<DailyCashFlow[]>([]);
  
  const meses = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
  ];

  useEffect(() => {
    if (user?.business_unit_id) {
      loadDailyCashFlow();
    }
  }, [user, selectedDate]);

  const loadDailyCashFlow = async () => {
    setLoading(true);
    try {
      const year = selectedDate.getFullYear();
      const month = selectedDate.getMonth() + 1;
      
      const response = await api.get(`/api/v1/cash-flow/daily?year=${year}&month=${month}`);
      
      if (response.data.success) {
        setCashFlowData(response.data.data || []);
      } else {
        console.error('Erro ao carregar fluxo de caixa diário:', response.data.message);
      }
    } catch (error) {
      console.error('Erro ao carregar fluxo de caixa diário:', error);
    } finally {
      setLoading(false);
    }
  };

  const getDaysInMonth = (date: Date): number => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  const previousMonth = () => {
    const newDate = new Date(selectedDate);
    newDate.setMonth(newDate.getMonth() - 1);
    setSelectedDate(newDate);
  };

  const nextMonth = () => {
    const newDate = new Date(selectedDate);
    newDate.setMonth(newDate.getMonth() + 1);
    setSelectedDate(newDate);
  };

  const formatCurrency = (value: number) => {
    if (value === 0) return '-';
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 2
    }).format(value);
  };

  const daysInMonth = getDaysInMonth(selectedDate);
  const monthName = meses[selectedDate.getMonth()];
  const year = selectedDate.getFullYear();

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Fluxo de Caixa Diário</h1>
            <p className="text-gray-600 mt-1">
              Movimentação diária de {monthName}/{year}
            </p>
          </div>
          
          {/* Navegação de Mês */}
          <div className="flex items-center gap-4">
            <button
              onClick={previousMonth}
              className="p-2 border border-gray-300 rounded-lg hover:bg-gray-100"
            >
              <ChevronLeft size={20} />
            </button>
            
            <div className="flex items-center gap-2">
              <Calendar size={20} className="text-gray-600" />
              <input
                type="month"
                value={`${year}-${String(selectedDate.getMonth() + 1).padStart(2, '0')}`}
                onChange={(e) => {
                  const [y, m] = e.target.value.split('-');
                  setSelectedDate(new Date(parseInt(y), parseInt(m) - 1, 1));
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <button
              onClick={nextMonth}
              className="p-2 border border-gray-300 rounded-lg hover:bg-gray-100"
            >
              <ChevronRight size={20} />
            </button>
          </div>
        </div>

        {/* Tabela */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase sticky left-0 bg-gray-50 z-10 min-w-[200px]">
                    Categoria
                  </th>
                  {[...Array(daysInMonth)].map((_, i) => (
                    <th key={i + 1} className="px-4 py-3 text-center text-xs font-medium text-gray-500 border-l border-gray-200 min-w-[100px]">
                      {i + 1}
                    </th>
                  ))}
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase border-l-2 border-gray-400 bg-blue-50 sticky right-0 z-10 min-w-[120px]">
                    Total
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr>
                    <td colSpan={daysInMonth + 2} className="px-6 py-12 text-center text-gray-500">
                      Carregando...
                    </td>
                  </tr>
                ) : cashFlowData.length === 0 ? (
                  <tr>
                    <td colSpan={daysInMonth + 2} className="px-6 py-12 text-center text-gray-500">
                      Nenhum dado encontrado
                    </td>
                  </tr>
                ) : (
                  cashFlowData.map((row, idx) => {
                    const totalLinha = Object.values(row.dias).reduce((sum, val) => sum + val, 0);
                    const tipo = row.tipo || 'conta';
                    
                    // Determinar estilo baseado no tipo
                    let rowClass = 'hover:bg-gray-50';
                    let cellClass = 'bg-white';
                    
                    if (tipo === 'calculado') {
                      rowClass = 'bg-yellow-50 font-bold border-t border-b border-yellow-200';
                      cellClass = 'bg-yellow-50 font-bold';
                    } else if (tipo === 'saldo') {
                      rowClass = 'bg-green-50 font-bold border-t-2 border-green-400';
                      cellClass = 'bg-green-50 font-bold';
                    } else if (row.categoria === 'TOTAL' || row.categoria.includes('TOTAL')) {
                      rowClass = 'bg-blue-50 font-bold border-t-2 border-blue-400';
                      cellClass = 'bg-blue-50 font-bold';
                    } else if (tipo === 'grupo' || row.nivel === 0) {
                      rowClass = 'bg-gray-100 font-semibold';
                      cellClass = 'bg-gray-100 font-semibold';
                    } else if (tipo === 'subgrupo' || row.nivel === 1) {
                      rowClass = 'bg-gray-50 font-medium';
                      cellClass = 'bg-gray-50 font-medium';
                    }
                    
                    return (
                      <tr key={idx} className={rowClass}>
                        <td className={`px-6 py-3 text-sm sticky left-0 z-10 ${cellClass}`}>
                          <span style={{ marginLeft: `${row.nivel * 20}px` }}>
                            {row.categoria}
                          </span>
                        </td>
                        {[...Array(daysInMonth)].map((_, i) => {
                          const dia = i + 1;
                          const valor = row.dias[dia] || 0;
                          return (
                            <td 
                              key={dia} 
                              className={`px-2 py-3 text-sm text-right border-l border-gray-200 ${
                                valor > 0 ? 'text-gray-900 font-medium' : 'text-gray-300'
                              }`}
                            >
                              {valor !== 0 ? formatCurrency(valor) : '-'}
                            </td>
                          );
                        })}
                        <td className={`px-6 py-3 text-sm text-right font-bold border-l-2 border-gray-400 sticky right-0 z-10 ${cellClass}`}>
                          {formatCurrency(totalLinha)}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Resumo */}
        {cashFlowData.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {(() => {
              const totalRow = cashFlowData.find(r => r.categoria === 'TOTAL');
              if (!totalRow) return null;
              
              const totalMes = Object.values(totalRow.dias).reduce((sum, val) => sum + val, 0);
              const mediaDiaria = totalMes / daysInMonth;
              const diasComMovimentacao = Object.values(totalRow.dias).filter(v => v > 0).length;
              
              return (
                <>
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <div className="text-sm text-gray-600">Total do Mês</div>
                    <div className="text-2xl font-bold text-gray-900 mt-1">
                      {formatCurrency(totalMes)}
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <div className="text-sm text-gray-600">Média Diária</div>
                    <div className="text-2xl font-bold text-gray-900 mt-1">
                      {formatCurrency(mediaDiaria)}
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg shadow-md p-6">
                    <div className="text-sm text-gray-600">Dias com Movimentação</div>
                    <div className="text-2xl font-bold text-gray-900 mt-1">
                      {diasComMovimentacao} de {daysInMonth}
                    </div>
                  </div>
                </>
              );
            })()}
          </div>
        )}

        {/* Legenda */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Legenda e Estrutura</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Tipos de Linha */}
            <div>
              <h4 className="font-medium text-gray-700 mb-3">Tipos de Linha</h4>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-6 bg-gray-100 border rounded"></div>
                  <span><strong>Grupos</strong> (Receita, Custos, Despesas)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-6 bg-gray-50 border rounded"></div>
                  <span className="ml-4"><strong>Subgrupos</strong> (ex: Despesas Admin)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-6 bg-white border rounded"></div>
                  <span className="ml-8">Contas (ex: Água, Salário)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-6 bg-yellow-50 border border-yellow-200 rounded"></div>
                  <span><strong>Calculados</strong> (Receita Líquida, Lucro)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-6 bg-green-50 border border-green-400 rounded"></div>
                  <span><strong>Saldos</strong> (Início/Fim do mês)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-6 bg-blue-50 border border-blue-400 rounded"></div>
                  <span><strong>TOTAL</strong> (Totalizador geral)</span>
                </div>
              </div>
            </div>
            
            {/* Como Usar */}
            <div>
              <h4 className="font-medium text-gray-700 mb-3">Como Usar</h4>
              <div className="space-y-2 text-sm text-gray-600">
                <p>• Navegue entre meses usando as setas ou seletor</p>
                <p>• Cada coluna = um dia do mês</p>
                <p>• Valores calculados dos <strong>Lançamentos Financeiros</strong></p>
                <p>• <strong>Atualização automática</strong> ao criar novos lançamentos</p>
                <p>• Coluna <strong>Total</strong> = soma de todos os dias</p>
                <p>• Linhas <strong>calculadas</strong> mostram indicadores (Lucro, Receita Líquida)</p>
                <p>• Seção <strong>Saldos</strong> mostra evolução do caixa</p>
              </div>
            </div>
          </div>
          
          <div className="mt-4 pt-4 border-t border-gray-200">
            <h4 className="font-medium text-gray-700 mb-2">Indicadores Calculados</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-gray-600">
              <p>• <strong>Receita Líquida</strong> = Receita - Deduções</p>
              <p>• <strong>Lucro Bruto</strong> = Receita Líquida - Custos</p>
              <p>• <strong>Desembolso Total</strong> = Custos + Despesas + Investimentos</p>
              <p>• <strong>Lucro Operacional</strong> = Lucro Bruto - Despesas - Investimentos</p>
              <p>• <strong>Fluxo (Variação)</strong> = Receitas - Saídas</p>
              <p>• <strong>Fim do mês</strong> = Início + Variação acumulada</p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default DailyCashFlow;


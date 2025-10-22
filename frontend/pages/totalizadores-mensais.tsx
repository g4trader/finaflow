import React, { useState, useEffect } from 'react';
import { Calendar, TrendingUp, TrendingDown, DollarSign, BarChart3 } from 'lucide-react';
import api from '../services/api';

interface TotalizadorMensal {
  mes: number;
  entradas: number;
  saidas: number;
  saldo_final: number;
  quantidade_lancamentos: number;
}

interface TotalizadoresResponse {
  success: boolean;
  ano: number;
  totalizadores: TotalizadorMensal[];
}

const meses = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
];

export default function TotalizadoresMensais() {
  const [totalizadores, setTotalizadores] = useState<TotalizadorMensal[]>([]);
  const [loading, setLoading] = useState(true);
  const [ano, setAno] = useState(new Date().getFullYear());
  const [tipo, setTipo] = useState<'contas-bancarias' | 'caixa' | 'investimentos'>('contas-bancarias');

  useEffect(() => {
    fetchTotalizadores();
  }, [ano, tipo]);

  const fetchTotalizadores = async () => {
    try {
      setLoading(true);
      const endpoint = `/api/v1/${tipo}/totalizadores-mensais?ano=${ano}`;
      const response = await api.get(endpoint);
      
      if (response.data.success) {
        setTotalizadores(response.data.totalizadores);
      }
    } catch (error) {
      console.error('Erro ao carregar totalizadores:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatarMoeda = (valor: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(valor);
  };

  const calcularTotaisAnuais = () => {
    const totais = totalizadores.reduce((acc, mes) => {
      acc.entradas += mes.entradas;
      acc.saidas += mes.saidas;
      acc.lancamentos += mes.quantidade_lancamentos;
      return acc;
    }, { entradas: 0, saidas: 0, lancamentos: 0 });
    
    const saldoFinal = totalizadores[totalizadores.length - 1]?.saldo_final || 0;
    return { ...totais, saldoFinal };
  };

  const totaisAnuais = calcularTotaisAnuais();

  const getTipoLabel = () => {
    switch (tipo) {
      case 'contas-bancarias':
        return 'Contas Bancárias';
      case 'caixa':
        return 'Caixa';
      case 'investimentos':
        return 'Investimentos';
      default:
        return 'Contas Bancárias';
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="space-y-4">
            {[...Array(12)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Totalizadores Mensais</h1>
        <p className="text-gray-600">Visualize os totais mensais de {getTipoLabel().toLowerCase()}</p>
      </div>

      {/* Filtros */}
      <div className="bg-white p-4 rounded-lg shadow mb-6">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-gray-500" />
            <label className="text-sm font-medium text-gray-700">Ano:</label>
          </div>
          
          <select
            value={ano}
            onChange={(e) => setAno(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {[2023, 2024, 2025, 2026].map(year => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>
          
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-gray-500" />
            <label className="text-sm font-medium text-gray-700">Tipo:</label>
          </div>
          
          <select
            value={tipo}
            onChange={(e) => setTipo(e.target.value as any)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="contas-bancarias">Contas Bancárias</option>
            <option value="caixa">Caixa</option>
            <option value="investimentos">Investimentos</option>
          </select>
        </div>
      </div>

      {/* Totais Anuais */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Entradas</p>
              <p className="text-lg font-semibold text-green-600">
                {formatarMoeda(totaisAnuais.entradas)}
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-green-500" />
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Saídas</p>
              <p className="text-lg font-semibold text-red-600">
                {formatarMoeda(totaisAnuais.saidas)}
              </p>
            </div>
            <TrendingDown className="w-8 h-8 text-red-500" />
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Saldo Final</p>
              <p className={`text-lg font-semibold ${totaisAnuais.saldoFinal >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatarMoeda(totaisAnuais.saldoFinal)}
              </p>
            </div>
            <DollarSign className="w-8 h-8 text-blue-500" />
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Lançamentos</p>
              <p className="text-lg font-semibold text-gray-900">
                {totaisAnuais.lancamentos.toLocaleString()}
              </p>
            </div>
            <BarChart3 className="w-8 h-8 text-purple-500" />
          </div>
        </div>
      </div>

      {/* Tabela Mensal */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Totalizadores Mensais - {ano}
          </h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Mês
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Entradas
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Saídas
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Saldo Final
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Lançamentos
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {totalizadores.map((mes) => (
                <tr key={mes.mes} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                        <span className="text-sm font-medium text-blue-600">{mes.mes}</span>
                      </div>
                      <span className="text-sm font-medium text-gray-900">
                        {meses[mes.mes - 1]}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm font-medium text-green-600">
                      {formatarMoeda(mes.entradas)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm font-medium text-red-600">
                      {formatarMoeda(mes.saidas)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`text-sm font-medium ${mes.saldo_final >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatarMoeda(mes.saldo_final)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-gray-900">
                      {mes.quantidade_lancamentos.toLocaleString()}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

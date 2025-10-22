import React, { useState, useEffect } from 'react';
import { Calendar, Download, Filter, TrendingUp, TrendingDown, DollarSign } from 'lucide-react';
import api from '../services/api';

interface Lancamento {
  id: string;
  conta: string;
  descricao: string;
  valor: number;
  tipo: string;
  liquidacao: string;
}

interface DiaExtrato {
  data: string;
  entradas: number;
  saidas: number;
  saldo_dia: number;
  lancamentos: Lancamento[];
}

interface ExtratoResponse {
  success: boolean;
  periodo: {
    inicio: string;
    fim: string;
  };
  extrato: DiaExtrato[];
}

export default function ExtratoContasBancarias() {
  const [extrato, setExtrato] = useState<DiaExtrato[]>([]);
  const [loading, setLoading] = useState(true);
  const [dataInicio, setDataInicio] = useState('');
  const [dataFim, setDataFim] = useState('');
  const [periodo, setPeriodo] = useState<{inicio: string, fim: string} | null>(null);

  useEffect(() => {
    // Definir período padrão (últimos 30 dias)
    const hoje = new Date();
    const trintaDiasAtras = new Date(hoje.getTime() - 30 * 24 * 60 * 60 * 1000);
    
    const inicio = trintaDiasAtras.toISOString().split('T')[0];
    const fim = hoje.toISOString().split('T')[0];
    
    setDataInicio(inicio);
    setDataFim(fim);
    
    fetchExtrato(inicio, fim);
  }, []);

  const fetchExtrato = async (inicio: string, fim: string) => {
    try {
      setLoading(true);
      const response = await api.get(`/api/v1/contas-bancarias/extrato-diario?data_inicio=${inicio}&data_fim=${fim}`);
      
      if (response.data.success) {
        setExtrato(response.data.extrato);
        setPeriodo(response.data.periodo);
      }
    } catch (error) {
      console.error('Erro ao carregar extrato:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFiltrar = () => {
    if (dataInicio && dataFim) {
      fetchExtrato(dataInicio, dataFim);
    }
  };

  const formatarMoeda = (valor: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(valor);
  };

  const formatarData = (data: string) => {
    return new Date(data).toLocaleDateString('pt-BR');
  };

  const getTipoColor = (tipo: string) => {
    switch (tipo) {
      case 'RECEITA':
        return 'text-green-600 bg-green-50';
      case 'DESPESA':
        return 'text-red-600 bg-red-50';
      case 'CUSTO':
        return 'text-orange-600 bg-orange-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getTipoIcon = (tipo: string) => {
    switch (tipo) {
      case 'RECEITA':
        return <TrendingUp className="w-4 h-4" />;
      case 'DESPESA':
      case 'CUSTO':
        return <TrendingDown className="w-4 h-4" />;
      default:
        return <DollarSign className="w-4 h-4" />;
    }
  };

  const calcularTotais = () => {
    const totais = extrato.reduce((acc, dia) => {
      acc.entradas += dia.entradas;
      acc.saidas += dia.saidas;
      acc.saldoFinal = dia.saldo_dia;
      return acc;
    }, { entradas: 0, saidas: 0, saldoFinal: 0 });
    
    return totais;
  };

  const totais = calcularTotais();

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Extrato Diário - Contas Bancárias</h1>
        <p className="text-gray-600">Visualize o movimento diário das suas contas bancárias</p>
      </div>

      {/* Filtros */}
      <div className="bg-white p-4 rounded-lg shadow mb-6">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-gray-500" />
            <label className="text-sm font-medium text-gray-700">Período:</label>
          </div>
          
          <input
            type="date"
            value={dataInicio}
            onChange={(e) => setDataInicio(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          
          <span className="text-gray-500">até</span>
          
          <input
            type="date"
            value={dataFim}
            onChange={(e) => setDataFim(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          
          <button
            onClick={handleFiltrar}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            <Filter className="w-4 h-4" />
            Filtrar
          </button>
        </div>
      </div>

      {/* Totais */}
      {periodo && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Período</p>
                <p className="text-lg font-semibold text-gray-900">
                  {formatarData(periodo.inicio)} - {formatarData(periodo.fim)}
                </p>
              </div>
              <Calendar className="w-8 h-8 text-blue-500" />
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Entradas</p>
                <p className="text-lg font-semibold text-green-600">
                  {formatarMoeda(totais.entradas)}
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
                  {formatarMoeda(totais.saidas)}
                </p>
              </div>
              <TrendingDown className="w-8 h-8 text-red-500" />
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Saldo Final</p>
                <p className={`text-lg font-semibold ${totais.saldoFinal >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatarMoeda(totais.saldoFinal)}
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-blue-500" />
            </div>
          </div>
        </div>
      )}

      {/* Extrato */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Extrato Detalhado</h2>
        </div>
        
        {extrato.length === 0 ? (
          <div className="p-8 text-center">
            <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">Nenhum lançamento encontrado para o período selecionado</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {extrato.map((dia, index) => (
              <div key={index} className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                      <Calendar className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{formatarData(dia.data)}</h3>
                      <p className="text-sm text-gray-500">{dia.lancamentos.length} lançamento(s)</p>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className="flex items-center gap-4">
                      <div className="text-center">
                        <p className="text-sm text-gray-500">Entradas</p>
                        <p className="font-semibold text-green-600">{formatarMoeda(dia.entradas)}</p>
                      </div>
                      <div className="text-center">
                        <p className="text-sm text-gray-500">Saídas</p>
                        <p className="font-semibold text-red-600">{formatarMoeda(dia.saidas)}</p>
                      </div>
                      <div className="text-center">
                        <p className="text-sm text-gray-500">Saldo</p>
                        <p className={`font-semibold ${dia.saldo_dia >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {formatarMoeda(dia.saldo_dia)}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Lançamentos do dia */}
                <div className="ml-13 space-y-2">
                  {dia.lancamentos.map((lancamento) => (
                    <div key={lancamento.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-full ${getTipoColor(lancamento.tipo)}`}>
                          {getTipoIcon(lancamento.tipo)}
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{lancamento.conta}</p>
                          <p className="text-sm text-gray-500">{lancamento.descricao}</p>
                        </div>
                      </div>
                      
                      <div className="text-right">
                        <p className={`font-semibold ${lancamento.tipo === 'RECEITA' ? 'text-green-600' : 'text-red-600'}`}>
                          {lancamento.tipo === 'RECEITA' ? '+' : '-'}{formatarMoeda(lancamento.valor)}
                        </p>
                        <p className="text-sm text-gray-500">{lancamento.tipo}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { Calendar, ArrowLeft, TrendingUp, TrendingDown, DollarSign, Building2, Wallet, TrendingUp as TrendingUpIcon } from 'lucide-react';
import Layout from '../components/layout/Layout';
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

interface ExtratoInvestimento {
  data: string;
  tipo: string;
  descricao: string;
  valor_aplicado: number;
  valor_atual: number;
  rentabilidade: number;
  observacoes: string;
}

interface ContaInfo {
  id: string;
  banco?: string;
  agencia?: string;
  conta?: string;
  nome?: string;
  descricao?: string;
  tipo?: string;
  instituicao?: string;
  saldo_atual?: number;
  valor_aplicado?: number;
  valor_atual?: number;
  data_aplicacao?: string;
}

interface ExtratoResponse {
  success: boolean;
  conta?: ContaInfo;
  caixa?: ContaInfo;
  investimento?: ContaInfo;
  periodo: {
    inicio: string;
    fim: string;
  };
  meta?: {
    saldo_inicial?: number;
    saldo_final?: number;
    media_diaria?: number;
  };
  extrato: DiaExtrato[] | ExtratoInvestimento[];
}

export default function ExtratoConta() {
  const router = useRouter();
  const { tipo, id } = router.query;
  
  const [extrato, setExtrato] = useState<DiaExtrato[] | ExtratoInvestimento[]>([]);
  const [contaInfo, setContaInfo] = useState<ContaInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [dataInicio, setDataInicio] = useState('');
  const [dataFim, setDataFim] = useState('');
  const [periodo, setPeriodo] = useState<{inicio: string, fim: string} | null>(null);
  const [meta, setMeta] = useState<{saldo_inicial?: number; saldo_final?: number; media_diaria?: number} | null>(null);

  useEffect(() => {
    if (id && tipo) {
      // Definir período padrão (últimos 30 dias)
      const hoje = new Date();
      const trintaDiasAtras = new Date(hoje.getTime() - 30 * 24 * 60 * 60 * 1000);
      
      const inicio = trintaDiasAtras.toISOString().split('T')[0];
      const fim = hoje.toISOString().split('T')[0];
      
      setDataInicio(inicio);
      setDataFim(fim);
      
      fetchExtrato(id as string, tipo as string, inicio, fim);
    }
  }, [id, tipo]);

  const fetchExtrato = async (contaId: string, tipoConta: string, inicio: string, fim: string) => {
    try {
      setLoading(true);
      const endpoint = `/api/v1/${tipoConta}/${contaId}/extrato?data_inicio=${inicio}&data_fim=${fim}`;
      const response = await api.get(endpoint);
      
      if (response.data.success) {
        setExtrato(response.data.extrato);
        setPeriodo(response.data.periodo);
        setMeta(response.data.meta || null);
        
        // Definir informações da conta baseado no tipo
        if (response.data.conta) {
          setContaInfo(response.data.conta);
        } else if (response.data.caixa) {
          setContaInfo(response.data.caixa);
        } else if (response.data.investimento) {
          setContaInfo(response.data.investimento);
        }
      }
    } catch (error) {
      console.error('Erro ao carregar extrato:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFiltrar = () => {
    if (dataInicio && dataFim && id && tipo) {
      fetchExtrato(id as string, tipo as string, dataInicio, dataFim);
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

  const getTipoIcone = () => {
    switch (tipo) {
      case 'contas-bancarias':
        return <Building2 className="w-6 h-6" />;
      case 'caixa':
        return <Wallet className="w-6 h-6" />;
      case 'investimentos':
        return <TrendingUpIcon className="w-6 h-6" />;
      default:
        return <DollarSign className="w-6 h-6" />;
    }
  };

  const getTipoLabel = () => {
    switch (tipo) {
      case 'contas-bancarias':
        return 'Conta Bancária';
      case 'caixa':
        return 'Caixa';
      case 'investimentos':
        return 'Investimento';
      default:
        return 'Conta';
    }
  };

  const calcularTotais = () => {
    if (tipo === 'investimentos') {
      // Para investimentos, não temos entradas/saídas diárias
      return { entradas: 0, saidas: 0, saldoFinal: contaInfo?.valor_atual || 0 };
    }
    
    const totais = (extrato as DiaExtrato[]).reduce((acc, dia) => {
      acc.entradas += dia.entradas;
      acc.saidas += dia.saidas;
      acc.saldoFinal = dia.saldo_dia;
      return acc;
    }, { entradas: 0, saidas: 0, saldoFinal: 0 });
    
    return totais;
  };

  const totais = calcularTotais();
  const saldoInicial = meta?.saldo_inicial ?? (
    extrato.length > 0 && tipo !== 'investimentos'
      ? (extrato[0] as DiaExtrato).saldo_dia - (extrato[0] as DiaExtrato).entradas + (extrato[0] as DiaExtrato).saidas
      : 0
  );
  const saldoFinal = meta?.saldo_final ?? totais.saldoFinal;

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
    <Layout>
      <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-4 mb-4">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            Voltar
          </button>
        </div>
        
        <div className="flex items-center gap-3 mb-2">
          {getTipoIcone()}
          <h1 className="text-2xl font-bold text-gray-900">
            Extrato - {getTipoLabel()}
          </h1>
        </div>
        
        {contaInfo && (
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                {tipo === 'contas-bancarias' && (
                  <>
                    <p className="text-lg font-semibold text-gray-900">
                      {contaInfo.banco} - Ag. {contaInfo.agencia} - Conta {contaInfo.conta}
                    </p>
                    <p className="text-sm text-gray-600">Conta Bancária</p>
                  </>
                )}
                {tipo === 'caixa' && (
                  <>
                    <p className="text-lg font-semibold text-gray-900">{contaInfo.nome}</p>
                    <p className="text-sm text-gray-600">{contaInfo.descricao}</p>
                  </>
                )}
                {tipo === 'investimentos' && (
                  <>
                    <p className="text-lg font-semibold text-gray-900">
                      {contaInfo.tipo} - {contaInfo.instituicao}
                    </p>
                    <p className="text-sm text-gray-600">
                      Aplicado em: {contaInfo.data_aplicacao}
                    </p>
                  </>
                )}
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-600">Saldo Atual</p>
                <p className="text-xl font-bold text-blue-600">
                  {formatarMoeda(contaInfo.saldo_atual || contaInfo.valor_atual || 0)}
                </p>
              </div>
            </div>
          </div>
        )}
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
            <Calendar className="w-4 h-4" />
            Filtrar
          </button>
        </div>
      </div>

      {/* Totais */}
      {periodo && (
        <div className={`grid grid-cols-1 ${tipo !== 'investimentos' ? 'md:grid-cols-5' : 'md:grid-cols-2'} gap-4 mb-6`}>
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
          
          {tipo !== 'investimentos' && (
            <>
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
                    <p className="text-sm text-gray-600">Saldo Inicial</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {formatarMoeda(saldoInicial)}
                    </p>
                  </div>
                  <DollarSign className="w-8 h-8 text-gray-500" />
                </div>
              </div>

              <div className="bg-white p-4 rounded-lg shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Saldo Final</p>
                    <p className={`text-lg font-semibold ${saldoFinal >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatarMoeda(saldoFinal)}
                    </p>
                  </div>
                  <DollarSign className="w-8 h-8 text-blue-500" />
                </div>
              </div>
            </>
          )}

          {tipo === 'investimentos' && (
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Valor Atual</p>
                  <p className="text-lg font-semibold text-blue-600">
                    {formatarMoeda(totais.saldoFinal)}
                  </p>
                </div>
                <DollarSign className="w-8 h-8 text-blue-500" />
              </div>
            </div>
          )}
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
            {extrato.map((item, index) => (
              <div key={index} className="p-4">
                {tipo === 'investimentos' ? (
                  // Layout específico para investimentos
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                        <TrendingUpIcon className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">{(item as ExtratoInvestimento).descricao}</h3>
                        <p className="text-sm text-gray-500">{(item as ExtratoInvestimento).data}</p>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <div className="flex items-center gap-6">
                        <div className="text-center">
                          <p className="text-sm text-gray-500">Valor Aplicado</p>
                          <p className="font-semibold text-gray-900">{formatarMoeda((item as ExtratoInvestimento).valor_aplicado)}</p>
                        </div>
                        <div className="text-center">
                          <p className="text-sm text-gray-500">Valor Atual</p>
                          <p className="font-semibold text-green-600">{formatarMoeda((item as ExtratoInvestimento).valor_atual)}</p>
                        </div>
                        <div className="text-center">
                          <p className="text-sm text-gray-500">Rentabilidade</p>
                          <p className={`font-semibold ${(item as ExtratoInvestimento).rentabilidade >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {formatarMoeda((item as ExtratoInvestimento).rentabilidade)}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  // Layout para contas bancárias e caixa
                  <>
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                          <Calendar className="w-5 h-5 text-blue-600" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-gray-900">{formatarData((item as DiaExtrato).data)}</h3>
                          <p className="text-sm text-gray-500">{(item as DiaExtrato).lancamentos.length} lançamento(s)</p>
                        </div>
                      </div>
                      
                      <div className="text-right">
                        <div className="flex items-center gap-4">
                          <div className="text-center">
                            <p className="text-sm text-gray-500">Entradas</p>
                            <p className="font-semibold text-green-600">{formatarMoeda((item as DiaExtrato).entradas)}</p>
                          </div>
                          <div className="text-center">
                            <p className="text-sm text-gray-500">Saídas</p>
                            <p className="font-semibold text-red-600">{formatarMoeda((item as DiaExtrato).saidas)}</p>
                          </div>
                          <div className="text-center">
                            <p className="text-sm text-gray-500">Saldo</p>
                            <p className={`font-semibold ${(item as DiaExtrato).saldo_dia >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {formatarMoeda((item as DiaExtrato).saldo_dia)}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Lançamentos do dia */}
                    <div className="ml-13 space-y-2">
                      {(item as DiaExtrato).lancamentos.map((lancamento) => (
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
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      </div>
    </Layout>
  );
}

import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../context/AuthContext';
import Layout from '../components/layout/Layout';
import { getApi } from '../utils/api-client';
import { TrendingUp, Plus, DollarSign, Calendar, Percent, FileText } from 'lucide-react';

interface Investimento {
  id: string;
  tipo: string;
  instituicao: string;
  descricao: string;
  valor_aplicado: number;
  valor_atual: number;
  data_aplicacao: string;
  data_vencimento: string;
  taxa_rendimento: number;
  created_at: string;
}

interface Resumo {
  quantidade: number;
  total_aplicado: number;
  total_atual: number;
  rentabilidade_percentual: number;
}

export default function Investimentos() {
  const { user } = useAuth();
  const router = useRouter();
  const [investimentos, setInvestimentos] = useState<Investimento[]>([]);
  const [resumo, setResumo] = useState<Resumo | null>(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  
  const [formData, setFormData] = useState({
    tipo: 'renda_fixa',
    instituicao: '',
    descricao: '',
    valor_aplicado: 0,
    valor_atual: 0,
    data_aplicacao: new Date().toISOString().split('T')[0],
    data_vencimento: '',
    taxa_rendimento: 0
  });

  useEffect(() => {
    fetchInvestimentos();
    fetchResumo();
  }, []);

  const fetchInvestimentos = async () => {
    try {
      setLoading(true);
      const api = await getApi();
      const response = await api.get('/api/v1/investimentos');
      if (response.data.success) {
        setInvestimentos(response.data.investimentos);
      }
    } catch (error) {
      console.error('Erro ao carregar investimentos:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchResumo = async () => {
    try {
      const api = await getApi();
      const response = await api.get('/api/v1/investimentos/resumo');
      if (response.data.success) {
        setResumo(response.data.resumo);
      }
    } catch (error) {
      console.error('Erro ao carregar resumo:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const api = await getApi();
      await api.post('/api/v1/investimentos', formData);
      
      setShowModal(false);
      setFormData({
        tipo: 'renda_fixa',
        instituicao: '',
        descricao: '',
        valor_aplicado: 0,
        valor_atual: 0,
        data_aplicacao: new Date().toISOString().split('T')[0],
        data_vencimento: '',
        taxa_rendimento: 0
      });
      fetchInvestimentos();
      fetchResumo();
    } catch (error) {
      console.error('Erro ao salvar investimento:', error);
      alert('Erro ao salvar investimento');
    }
  };

  const handleVerExtrato = (id: string) => {
    router.push(`/extrato-conta?tipo=investimentos&id=${id}`);
  };

  const getTipoLabel = (tipo: string) => {
    const tipos: Record<string, string> = {
      renda_fixa: 'Renda Fixa',
      renda_variavel: 'Renda Variável',
      fundo: 'Fundo de Investimento',
      cdb: 'CDB',
      lci: 'LCI',
      lca: 'LCA',
      tesouro_direto: 'Tesouro Direto',
      poupanca: 'Poupança',
      outro: 'Outro'
    };
    return tipos[tipo] || tipo;
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  const calcularRentabilidade = (aplicado: number, atual: number) => {
    if (aplicado === 0) return 0;
    return ((atual - aplicado) / aplicado) * 100;
  };

  return (
    <Layout>
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <TrendingUp className="w-6 h-6" />
              Investimentos
            </h1>
            <p className="text-gray-600 mt-1">Gerencie seus investimentos e aplicações</p>
          </div>
          <button
            onClick={() => {
              setFormData({
                tipo: 'renda_fixa',
                instituicao: '',
                descricao: '',
                valor_aplicado: 0,
                valor_atual: 0,
                data_aplicacao: new Date().toISOString().split('T')[0],
                data_vencimento: '',
                taxa_rendimento: 0
              });
              setShowModal(true);
            }}
            className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Novo Investimento
          </button>
        </div>

        {/* Cards de Resumo */}
        {resumo && (
          <div className="grid gap-4 md:grid-cols-4 mb-6">
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <p className="text-sm text-gray-600 mb-1">Total Aplicado</p>
              <p className="text-2xl font-bold text-gray-900">{formatCurrency(resumo.total_aplicado)}</p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <p className="text-sm text-gray-600 mb-1">Valor Atual</p>
              <p className="text-2xl font-bold text-purple-600">{formatCurrency(resumo.total_atual)}</p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <p className="text-sm text-gray-600 mb-1">Rendimento</p>
              <p className="text-2xl font-bold text-green-600">
                {formatCurrency(resumo.total_atual - resumo.total_aplicado)}
              </p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <p className="text-sm text-gray-600 mb-1">Rentabilidade</p>
              <p className="text-2xl font-bold text-green-600">
                {resumo.rentabilidade_percentual.toFixed(2)}%
              </p>
            </div>
          </div>
        )}

        {/* Lista de Investimentos */}
        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Carregando investimentos...</p>
          </div>
        ) : investimentos.length === 0 ? (
          <div className="bg-white rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
            <TrendingUp className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Nenhum investimento cadastrado
            </h3>
            <p className="text-gray-600 mb-4">
              Comece adicionando seu primeiro investimento
            </p>
            <button
              onClick={() => setShowModal(true)}
              className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700"
            >
              Adicionar Investimento
            </button>
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Investimento
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tipo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Valor Aplicado
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Valor Atual
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Rendimento
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Vencimento
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Ações
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {investimentos.map((inv) => {
                    const rentabilidade = calcularRentabilidade(inv.valor_aplicado, inv.valor_atual);
                    const ganho = inv.valor_atual - inv.valor_aplicado;
                    
                    return (
                      <tr key={inv.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="font-medium text-gray-900">{inv.instituicao}</div>
                            {inv.descricao && (
                              <div className="text-sm text-gray-500">{inv.descricao}</div>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="px-2 py-1 text-xs font-medium rounded-full bg-purple-100 text-purple-800">
                            {getTipoLabel(inv.tipo)}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatCurrency(inv.valor_aplicado)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-purple-600">
                          {formatCurrency(inv.valor_atual)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className={`text-sm font-medium ${ganho >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {formatCurrency(ganho)}
                            <div className="text-xs">({rentabilidade.toFixed(2)}%)</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(inv.data_vencimento)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <button
                            onClick={() => handleVerExtrato(inv.id)}
                            className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                            title="Ver Extrato"
                          >
                            <FileText className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Modal */}
        {showModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
            <div className="bg-white rounded-lg p-6 w-full max-w-2xl m-4">
              <h2 className="text-xl font-bold mb-4">Novo Investimento</h2>
              
              <form onSubmit={handleSubmit}>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tipo *
                    </label>
                    <select
                      required
                      value={formData.tipo}
                      onChange={(e) => setFormData({ ...formData, tipo: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    >
                      <option value="renda_fixa">Renda Fixa</option>
                      <option value="renda_variavel">Renda Variável</option>
                      <option value="fundo">Fundo de Investimento</option>
                      <option value="cdb">CDB</option>
                      <option value="lci">LCI</option>
                      <option value="lca">LCA</option>
                      <option value="tesouro_direto">Tesouro Direto</option>
                      <option value="poupanca">Poupança</option>
                      <option value="outro">Outro</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Instituição *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.instituicao}
                      onChange={(e) => setFormData({ ...formData, instituicao: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="Ex: Banco do Brasil, XP Investimentos"
                    />
                  </div>

                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Descrição
                    </label>
                    <textarea
                      value={formData.descricao}
                      onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      rows={2}
                      placeholder="Descrição opcional"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Valor Aplicado *
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      required
                      value={formData.valor_aplicado}
                      onChange={(e) => {
                        const valor = parseFloat(e.target.value) || 0;
                        setFormData({ 
                          ...formData, 
                          valor_aplicado: valor,
                          valor_atual: formData.valor_atual === 0 ? valor : formData.valor_atual
                        });
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="0.00"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Valor Atual
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={formData.valor_atual}
                      onChange={(e) => setFormData({ ...formData, valor_atual: parseFloat(e.target.value) || 0 })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="0.00"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Data de Aplicação *
                    </label>
                    <input
                      type="date"
                      required
                      value={formData.data_aplicacao}
                      onChange={(e) => setFormData({ ...formData, data_aplicacao: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Data de Vencimento
                    </label>
                    <input
                      type="date"
                      value={formData.data_vencimento}
                      onChange={(e) => setFormData({ ...formData, data_vencimento: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                  </div>

                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Taxa de Rendimento (% a.a.)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={formData.taxa_rendimento}
                      onChange={(e) => setFormData({ ...formData, taxa_rendimento: parseFloat(e.target.value) || 0 })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="Ex: 12.5 para 12,5% a.a."
                    />
                  </div>
                </div>

                <div className="flex gap-3 mt-6">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                  >
                    Criar
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}


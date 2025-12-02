import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Plus, Edit, Trash2, Search, Filter, Calendar,
  DollarSign, FileText, Building, Users, ArrowUpDown
} from 'lucide-react';
import Layout from '../components/layout/Layout';
import { useAuth } from '../context/AuthContext';
import { getApi } from '../utils/api-client';

interface PlanoContas {
  grupos: Array<{ id: string; code: string; name: string; }>;
  subgrupos: Array<{ id: string; code: string; name: string; group_id: string; }>;
  contas: Array<{ id: string; code: string; name: string; subgroup_id: string; }>;
}

interface LancamentoDiario {
  id: string;
  data_movimentacao: string;
  valor: number;
  liquidacao?: string;
  observacoes?: string;
  conta_id: string;
  conta_nome: string;
  conta_codigo: string;
  subgrupo_id: string;
  subgrupo_nome: string;
  subgrupo_codigo: string;
  grupo_id: string;
  grupo_nome: string;
  grupo_codigo: string;
  transaction_type: string;
  status: string;
  created_at: string;
}

const LancamentosDiarios: React.FC = () => {
  const { user } = useAuth();
  const [lancamentos, setLancamentos] = useState<LancamentoDiario[]>([]);
  const [planoContas, setPlanoContas] = useState<PlanoContas | null>(null);
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingLancamento, setEditingLancamento] = useState<LancamentoDiario | null>(null);
  const [formData, setFormData] = useState({
    data_movimentacao: '',
    valor: '',
    liquidacao: '',
    observacoes: '',
    grupo_id: '',
    subgrupo_id: '',
    conta_id: ''
  });

  useEffect(() => {
    if (user?.business_unit_id) {
      loadPlanoContas();
      loadLancamentos();
    }
  }, [user]);

  const loadPlanoContas = async () => {
    try {
      const api = await getApi();
      const response = await api.get('/api/v1/lancamentos-diarios/plano-contas');
      setPlanoContas(response.data);
    } catch (error) {
      console.error('Erro ao carregar plano de contas:', error);
    }
  };

  const loadLancamentos = async () => {
    setLoading(true);
    try {
      const api = await getApi();
      const response = await api.get('/api/v1/lancamentos-diarios');
      setLancamentos(response.data.lancamentos || []);
    } catch (error) {
      console.error('Erro ao carregar lançamentos:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const payload = {
        ...formData,
        valor: parseFloat(formData.valor),
        liquidacao: formData.liquidacao || null
      };

      const api = await getApi();
      if (editingLancamento) {
        await api.put(`/api/v1/lancamentos-diarios/${editingLancamento.id}`, payload);
      } else {
        await api.post('/api/v1/lancamentos-diarios', payload);
      }

      await loadLancamentos();
      setShowCreateModal(false);
      setEditingLancamento(null);
      resetForm();
    } catch (error) {
      console.error('Erro ao salvar lançamento:', error);
    }
  };

  const handleEdit = (lancamento: LancamentoDiario) => {
    setFormData({
      data_movimentacao: lancamento.data_movimentacao.split('T')[0],
      valor: lancamento.valor.toString(),
      liquidacao: lancamento.liquidacao ? lancamento.liquidacao.split('T')[0] : '',
      observacoes: lancamento.observacoes || '',
      grupo_id: lancamento.grupo_id,
      subgrupo_id: lancamento.subgrupo_id,
      conta_id: lancamento.conta_id
    });
    setEditingLancamento(lancamento);
    setShowCreateModal(true);
  };

  const handleDelete = async (id: string) => {
    if (confirm('Tem certeza que deseja excluir este lançamento?')) {
      try {
        const api = await getApi();
        await api.delete(`/api/v1/lancamentos-diarios/${id}`);
        await loadLancamentos();
      } catch (error) {
        console.error('Erro ao excluir lançamento:', error);
      }
    }
  };

  const resetForm = () => {
    setFormData({
      data_movimentacao: '',
      valor: '',
      liquidacao: '',
      observacoes: '',
      grupo_id: '',
      subgrupo_id: '',
      conta_id: ''
    });
  };

  const handleGroupChange = (groupId: string) => {
    setFormData(prev => ({
      ...prev,
      grupo_id: groupId,
      subgrupo_id: '',
      conta_id: ''
    }));
  };

  const handleSubgroupChange = (subgroupId: string) => {
    setFormData(prev => ({
      ...prev,
      subgrupo_id: subgroupId,
      conta_id: ''
    }));
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  const getSubgruposByGroup = (groupId: string) => {
    return planoContas?.subgrupos.filter(s => s.group_id === groupId) || [];
  };

  const getContasBySubgroup = (subgroupId: string) => {
    return planoContas?.contas.filter(c => c.subgroup_id === subgroupId) || [];
  };

  return (
    <Layout>
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Lançamentos Diários</h1>
            <p className="text-gray-600">Gerencie os lançamentos financeiros diários</p>
          </div>
          <button
            onClick={() => {
              resetForm();
              setEditingLancamento(null);
              setShowCreateModal(true);
            }}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <Plus size={20} />
            Novo Lançamento
          </button>
        </div>

        {/* Filtros */}
        <div className="bg-white p-4 rounded-lg shadow mb-6">
          <div className="flex gap-4 items-center">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Buscar lançamentos..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <button className="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 flex items-center gap-2">
              <Filter size={16} />
              Filtros
            </button>
          </div>
        </div>

        {/* Lista de Lançamentos */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Data Movimentação
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Grupo
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Subgrupo
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Conta
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Valor
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tipo
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Observações
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Ações
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr>
                    <td colSpan={8} className="px-6 py-4 text-center text-gray-500">
                      Carregando...
                    </td>
                  </tr>
                ) : lancamentos.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-6 py-4 text-center text-gray-500">
                      Nenhum lançamento encontrado
                    </td>
                  </tr>
                ) : (
                  lancamentos.map((lancamento) => (
                    <tr key={lancamento.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatDate(lancamento.data_movimentacao)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div>
                          <div className="font-medium">{lancamento.grupo_codigo}</div>
                          <div className="text-gray-500">{lancamento.grupo_nome}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div>
                          <div className="font-medium">{lancamento.subgrupo_codigo}</div>
                          <div className="text-gray-500">{lancamento.subgrupo_nome}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div>
                          <div className="font-medium">{lancamento.conta_codigo}</div>
                          <div className="text-gray-500">{lancamento.conta_nome}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <span className={`font-medium ${
                          lancamento.transaction_type === 'RECEITA' ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {formatCurrency(lancamento.valor)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          lancamento.transaction_type === 'RECEITA'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {lancamento.transaction_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                        {lancamento.observacoes || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleEdit(lancamento)}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            <Edit size={16} />
                          </button>
                          <button
                            onClick={() => handleDelete(lancamento.id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Modal de Criação/Edição */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto"
            >
              <h2 className="text-xl font-bold mb-4">
                {editingLancamento ? 'Editar Lançamento' : 'Novo Lançamento'}
              </h2>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Data Movimentação *
                    </label>
                    <input
                      type="date"
                      required
                      value={formData.data_movimentacao}
                      onChange={(e) => setFormData(prev => ({ ...prev, data_movimentacao: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Valor *
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      required
                      value={formData.valor}
                      onChange={(e) => setFormData(prev => ({ ...prev, valor: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Grupo *
                  </label>
                  <select
                    required
                    value={formData.grupo_id}
                    onChange={(e) => handleGroupChange(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Selecione um grupo</option>
                    {planoContas?.grupos.map(grupo => (
                      <option key={grupo.id} value={grupo.id}>
                        {grupo.code} - {grupo.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Subgrupo *
                  </label>
                  <select
                    required
                    value={formData.subgrupo_id}
                    onChange={(e) => handleSubgroupChange(e.target.value)}
                    disabled={!formData.grupo_id}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                  >
                    <option value="">Selecione um subgrupo</option>
                    {getSubgruposByGroup(formData.grupo_id).map(subgrupo => (
                      <option key={subgrupo.id} value={subgrupo.id}>
                        {subgrupo.code} - {subgrupo.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Conta *
                  </label>
                  <select
                    required
                    value={formData.conta_id}
                    onChange={(e) => setFormData(prev => ({ ...prev, conta_id: e.target.value }))}
                    disabled={!formData.subgrupo_id}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                  >
                    <option value="">Selecione uma conta</option>
                    {getContasBySubgroup(formData.subgrupo_id).map(conta => (
                      <option key={conta.id} value={conta.id}>
                        {conta.code} - {conta.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Liquidação
                  </label>
                  <input
                    type="date"
                    value={formData.liquidacao}
                    onChange={(e) => setFormData(prev => ({ ...prev, liquidacao: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Observações
                  </label>
                  <textarea
                    value={formData.observacoes}
                    onChange={(e) => setFormData(prev => ({ ...prev, observacoes: e.target.value }))}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    {editingLancamento ? 'Atualizar' : 'Criar'}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default LancamentosDiarios;

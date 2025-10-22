import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Plus, Edit, Trash2, Search, Calendar, ChevronLeft, ChevronRight,
  Filter, X
} from 'lucide-react';
import Layout from '../components/layout/Layout';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

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

// Funções auxiliares para períodos
const getDateRange = (period: string): { start: string; end: string } => {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  
  switch (period) {
    case 'hoje':
      return {
        start: today.toISOString().split('T')[0],
        end: today.toISOString().split('T')[0]
      };
    case 'ontem':
      const yesterday = new Date(today);
      yesterday.setDate(yesterday.getDate() - 1);
      return {
        start: yesterday.toISOString().split('T')[0],
        end: yesterday.toISOString().split('T')[0]
      };
    case 'esta-semana':
      const firstDay = new Date(today);
      firstDay.setDate(today.getDate() - today.getDay());
      return {
        start: firstDay.toISOString().split('T')[0],
        end: today.toISOString().split('T')[0]
      };
    case 'semana-passada':
      const lastWeekEnd = new Date(today);
      lastWeekEnd.setDate(today.getDate() - today.getDay() - 1);
      const lastWeekStart = new Date(lastWeekEnd);
      lastWeekStart.setDate(lastWeekEnd.getDate() - 6);
      return {
        start: lastWeekStart.toISOString().split('T')[0],
        end: lastWeekEnd.toISOString().split('T')[0]
      };
    case 'este-mes':
      const firstDayMonth = new Date(now.getFullYear(), now.getMonth(), 1);
      return {
        start: firstDayMonth.toISOString().split('T')[0],
        end: today.toISOString().split('T')[0]
      };
    case 'mes-passado':
      const firstDayLastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
      const lastDayLastMonth = new Date(now.getFullYear(), now.getMonth(), 0);
      return {
        start: firstDayLastMonth.toISOString().split('T')[0],
        end: lastDayLastMonth.toISOString().split('T')[0]
      };
    case 'este-ano':
      const firstDayYear = new Date(now.getFullYear(), 0, 1);
      return {
        start: firstDayYear.toISOString().split('T')[0],
        end: today.toISOString().split('T')[0]
      };
    case 'ano-passado':
      const firstDayLastYear = new Date(now.getFullYear() - 1, 0, 1);
      const lastDayLastYear = new Date(now.getFullYear() - 1, 11, 31);
      return {
        start: firstDayLastYear.toISOString().split('T')[0],
        end: lastDayLastYear.toISOString().split('T')[0]
      };
    default:
      return { start: '', end: '' };
  }
};

const Transactions: React.FC = () => {
  const { user } = useAuth();
  const [lancamentos, setLancamentos] = useState<LancamentoDiario[]>([]);
  const [planoContas, setPlanoContas] = useState<PlanoContas | null>(null);
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingLancamento, setEditingLancamento] = useState<LancamentoDiario | null>(null);
  
  // Filtros
  const [searchTerm, setSearchTerm] = useState('');
  const [dateStart, setDateStart] = useState('');
  const [dateEnd, setDateEnd] = useState('');
  const [selectedGrupo, setSelectedGrupo] = useState('');
  const [selectedSubgrupo, setSelectedSubgrupo] = useState('');
  const [selectedConta, setSelectedConta] = useState('');
  
  // Paginação
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;
  
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
      const response = await api.get('/api/v1/lancamentos-diarios/plano-contas');
      setPlanoContas(response.data);
    } catch (error) {
      console.error('Erro ao carregar plano de contas:', error);
    }
  };

  const loadLancamentos = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/v1/lancamentos-diarios');
      setLancamentos(response.data?.lancamentos || []);
    } catch (error) {
      console.error('Erro ao carregar lançamentos:', error);
      setLancamentos([]); // Garantir que sempre seja um array
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

      if (editingLancamento) {
        await api.put(`/api/v1/lancamentos-diarios/${editingLancamento.id}`, payload);
      } else {
        await api.post('/api/v1/lancamentos-diarios', payload);
      }

      await loadLancamentos();
      resetForm();
      setShowCreateModal(false);
      setEditingLancamento(null);
    } catch (error) {
      console.error('Erro ao salvar lançamento:', error);
      alert('Erro ao salvar lançamento');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Tem certeza que deseja excluir este lançamento?')) return;
    
    try {
      await api.delete(`/api/v1/lancamentos-diarios/${id}`);
      await loadLancamentos();
    } catch (error) {
      console.error('Erro ao excluir lançamento:', error);
      alert('Erro ao excluir lançamento');
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

  const handleEdit = (lancamento: LancamentoDiario) => {
    setEditingLancamento(lancamento);
    setFormData({
      data_movimentacao: lancamento.data_movimentacao.split('T')[0],
      valor: lancamento.valor.toString(),
      liquidacao: lancamento.liquidacao ? lancamento.liquidacao.split('T')[0] : '',
      observacoes: lancamento.observacoes || '',
      grupo_id: lancamento.grupo_id,
      subgrupo_id: lancamento.subgrupo_id,
      conta_id: lancamento.conta_id
    });
    setShowCreateModal(true);
  };

  const applyPeriodFilter = (period: string) => {
    if (period === 'todos') {
      setDateStart('');
      setDateEnd('');
      setCurrentPage(1);
      return;
    }
    
    const range = getDateRange(period);
    setDateStart(range.start);
    setDateEnd(range.end);
    setCurrentPage(1);
  };

  const clearFilters = () => {
    setSearchTerm('');
    setDateStart('');
    setDateEnd('');
    setSelectedGrupo('');
    setSelectedSubgrupo('');
    setSelectedConta('');
    setCurrentPage(1);
  };

  // Filtrar lançamentos
  const filteredLancamentos = (lancamentos || []).filter(lanc => {
    // Filtro de busca
    if (searchTerm && !lanc.observacoes?.toLowerCase().includes(searchTerm.toLowerCase()) &&
        !lanc.conta_nome.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false;
    }
    
    // Filtro de data
    if (dateStart && lanc.data_movimentacao.split('T')[0] < dateStart) return false;
    if (dateEnd && lanc.data_movimentacao.split('T')[0] > dateEnd) return false;
    
    // Filtro de grupo
    if (selectedGrupo && lanc.grupo_id !== selectedGrupo) return false;
    
    // Filtro de subgrupo
    if (selectedSubgrupo && lanc.subgrupo_id !== selectedSubgrupo) return false;
    
    // Filtro de conta
    if (selectedConta && lanc.conta_id !== selectedConta) return false;
    
    return true;
  });

  // Paginação
  const totalPages = Math.ceil(filteredLancamentos.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentLancamentos = filteredLancamentos.slice(startIndex, endIndex);

  // Filtrar subgrupos baseado no grupo selecionado
  const filteredSubgrupos = planoContas?.subgrupos.filter(
    sub => !selectedGrupo || sub.group_id === selectedGrupo
  ) || [];

  // Filtrar contas baseado no subgrupo selecionado
  const filteredContas = planoContas?.contas.filter(
    conta => !selectedSubgrupo || conta.subgroup_id === selectedSubgrupo
  ) || [];

  return (
    <Layout>
      <div className="space-y-6">
          {/* Header */}
        <div className="flex justify-between items-center">
              <div>
            <h1 className="text-3xl font-bold text-gray-900">Lançamentos Financeiros</h1>
                <p className="text-gray-600 mt-1">
              {filteredLancamentos.length} lançamento(s) encontrado(s)
                </p>
              </div>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => {
              resetForm();
              setEditingLancamento(null);
              setShowCreateModal(true);
            }}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <Plus size={20} />
            Novo Lançamento
          </motion.button>
        </div>

        {/* Filtros */}
        <div className="bg-white rounded-lg shadow-md p-6 space-y-4">
          {/* Filtros de Período */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Período
            </label>
            <div className="flex flex-wrap gap-2">
              {[
                { label: 'Todos', value: 'todos' },
                { label: 'Hoje', value: 'hoje' },
                { label: 'Ontem', value: 'ontem' },
                { label: 'Esta Semana', value: 'esta-semana' },
                { label: 'Semana Passada', value: 'semana-passada' },
                { label: 'Este Mês', value: 'este-mes' },
                { label: 'Mês Passado', value: 'mes-passado' },
                { label: 'Este Ano', value: 'este-ano' },
                { label: 'Ano Passado', value: 'ano-passado' }
              ].map(period => (
                <button
                  key={period.value}
                  onClick={() => applyPeriodFilter(period.value)}
                  className={`px-4 py-2 rounded-lg transition-colors text-sm font-medium ${
                    period.value === 'todos'
                      ? 'bg-blue-600 hover:bg-blue-700 text-white'
                      : 'bg-gray-100 hover:bg-blue-100 text-gray-700 hover:text-blue-700'
                  }`}
                >
                  {period.label}
                </button>
              ))}
            </div>
          </div>

          {/* Filtros Customizados */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {/* Data Início */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Data Início
              </label>
              <input
                type="date"
                value={dateStart}
                onChange={(e) => setDateStart(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Data Fim */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Data Fim
              </label>
              <input
                type="date"
                value={dateEnd}
                onChange={(e) => setDateEnd(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Grupo */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Grupo
              </label>
              <select
                value={selectedGrupo}
                onChange={(e) => {
                  setSelectedGrupo(e.target.value);
                  setSelectedSubgrupo('');
                  setSelectedConta('');
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Todos os grupos</option>
                {planoContas?.grupos.map(grupo => (
                  <option key={grupo.id} value={grupo.id}>
                    {grupo.code} - {grupo.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Subgrupo */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Subgrupo
              </label>
              <select
                value={selectedSubgrupo}
                onChange={(e) => {
                  setSelectedSubgrupo(e.target.value);
                  setSelectedConta('');
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                disabled={!selectedGrupo}
              >
                <option value="">Todos os subgrupos</option>
                {filteredSubgrupos.map(sub => (
                  <option key={sub.id} value={sub.id}>
                    {sub.code} - {sub.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Conta */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Conta
              </label>
              <select
                value={selectedConta}
                onChange={(e) => setSelectedConta(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                disabled={!selectedSubgrupo}
              >
                <option value="">Todas as contas</option>
                {filteredContas.map(conta => (
                  <option key={conta.id} value={conta.id}>
                    {conta.code} - {conta.name}
                  </option>
                ))}
              </select>
            </div>
              </div>
              
          {/* Busca e Limpar */}
          <div className="flex gap-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Buscar por observações ou conta..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              onClick={clearFilters}
              className="px-6 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg flex items-center gap-2"
            >
              <X size={18} />
              Limpar Filtros
            </button>
                </div>
                </div>

        {/* Tabela */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Data
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
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Ações
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr>
                    <td colSpan={8} className="px-6 py-12 text-center text-gray-500">
                      Carregando...
                    </td>
                  </tr>
                ) : currentLancamentos.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-6 py-12 text-center text-gray-500">
                      Nenhum lançamento encontrado
                          </td>
                  </tr>
                ) : (
                  currentLancamentos.map((lanc) => (
                    <tr key={lanc.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(lanc.data_movimentacao).toLocaleDateString('pt-BR')}
                          </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        <div className="font-medium">{lanc.grupo_codigo}</div>
                        <div className="text-gray-500 text-xs">{lanc.grupo_nome}</div>
                          </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        <div className="font-medium">{lanc.subgrupo_codigo}</div>
                        <div className="text-gray-500 text-xs">{lanc.subgrupo_nome}</div>
                          </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        <div className="font-medium">{lanc.conta_codigo}</div>
                        <div className="text-gray-500 text-xs">{lanc.conta_nome}</div>
                          </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                        R$ {lanc.valor.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          lanc.transaction_type === 'RECEITA' 
                            ? 'bg-green-100 text-green-800' 
                            : lanc.transaction_type === 'CUSTO'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {lanc.transaction_type}
                            </span>
                          </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {lanc.observacoes || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                              <button
                          onClick={() => handleEdit(lanc)}
                          className="text-blue-600 hover:text-blue-900 mr-4"
                              >
                          <Edit size={18} />
                              </button>
                              <button
                          onClick={() => handleDelete(lanc.id)}
                                className="text-red-600 hover:text-red-900"
                              >
                          <Trash2 size={18} />
                              </button>
                          </td>
                        </tr>
                  ))
                )}
                    </tbody>
                  </table>
                </div>

          {/* Paginação */}
          {totalPages > 1 && (
            <div className="bg-gray-50 px-6 py-4 flex items-center justify-between border-t border-gray-200">
              <div className="flex-1 flex justify-between sm:hidden">
                <button
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  Anterior
                </button>
                    <button
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                    >
                  Próxima
                    </button>
                  </div>
              <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm text-gray-700">
                    Mostrando <span className="font-medium">{startIndex + 1}</span> até{' '}
                    <span className="font-medium">{Math.min(endIndex, filteredLancamentos.length)}</span> de{' '}
                    <span className="font-medium">{filteredLancamentos.length}</span> resultados
                      </p>
                    </div>
                <div>
                  <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                    <button
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                      className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                    >
                      <ChevronLeft size={20} />
                    </button>
                    {[...Array(totalPages)].map((_, i) => (
                      <button
                        key={i}
                        onClick={() => setCurrentPage(i + 1)}
                        className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                          currentPage === i + 1
                            ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                            : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                        }`}
                      >
                        {i + 1}
                      </button>
                    ))}
                    <button
                      onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                      className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                    >
                      <ChevronRight size={20} />
                    </button>
                  </nav>
                </div>
              </div>
            </div>
          )}
                  </div>
                  
        {/* Modal de Criação/Edição */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
            >
              <div className="p-6">
                <h2 className="text-2xl font-bold mb-4">
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
                        value={formData.data_movimentacao}
                        onChange={(e) => setFormData({...formData, data_movimentacao: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Valor *
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        value={formData.valor}
                        onChange={(e) => setFormData({...formData, valor: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Grupo *
                    </label>
                    <select
                      value={formData.grupo_id}
                      onChange={(e) => setFormData({...formData, grupo_id: e.target.value, subgrupo_id: '', conta_id: ''})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      required
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
                      value={formData.subgrupo_id}
                      onChange={(e) => setFormData({...formData, subgrupo_id: e.target.value, conta_id: ''})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      required
                      disabled={!formData.grupo_id}
                    >
                      <option value="">Selecione um subgrupo</option>
                      {planoContas?.subgrupos
                        .filter(sub => sub.group_id === formData.grupo_id)
                        .map(sub => (
                          <option key={sub.id} value={sub.id}>
                            {sub.code} - {sub.name}
                          </option>
                        ))}
                    </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                      Conta *
                      </label>
                      <select
                      value={formData.conta_id}
                      onChange={(e) => setFormData({...formData, conta_id: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      required
                      disabled={!formData.subgrupo_id}
                    >
                      <option value="">Selecione uma conta</option>
                      {planoContas?.contas
                        .filter(conta => conta.subgroup_id === formData.subgrupo_id)
                        .map(conta => (
                          <option key={conta.id} value={conta.id}>
                            {conta.code} - {conta.name}
                          </option>
                        ))}
                      </select>
                    </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Data Liquidação
                    </label>
                    <input
                      type="date"
                      value={formData.liquidacao}
                      onChange={(e) => setFormData({...formData, liquidacao: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Observações
                      </label>
                      <textarea
                      value={formData.observacoes}
                      onChange={(e) => setFormData({...formData, observacoes: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      rows={3}
                    />
                  </div>

                  <div className="flex gap-4 pt-4">
                    <button
                      type="button"
                      onClick={() => {
                        setShowCreateModal(false);
                        setEditingLancamento(null);
                        resetForm();
                      }}
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                    >
                      Cancelar
                    </button>
                    <button
                      type="submit"
                      className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      {editingLancamento ? 'Atualizar' : 'Criar'} Lançamento
                    </button>
                  </div>
                </form>
              </div>
            </motion.div>
            </div>
          )}
      </div>
    </Layout>
  );
};

export default Transactions;

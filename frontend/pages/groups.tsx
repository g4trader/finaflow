import React, { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import { 
  Plus, 
  Edit, 
  Trash2, 
  Search, 
  Filter,
  Eye,
  MoreHorizontal
} from 'lucide-react';
import Button from '../components/ui/Button';
import { 
  getChartAccountGroups, 
  createGroup, 
  updateGroup, 
  deleteGroup 
} from '../services/api';
import { useAuth } from '../context/AuthContext';

interface Group {
  id: string;
  name: string;
  code: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

const Groups: React.FC = () => {
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterActive, setFilterActive] = useState<boolean | null>(null);
  
  // Modal states
  const [showModal, setShowModal] = useState(false);
  const [editingGroup, setEditingGroup] = useState<Group | null>(null);
  const [modalTitle, setModalTitle] = useState('');
  
  // Form states
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    description: '',
    is_active: true
  });
  
  const { token } = useAuth();

  useEffect(() => {
    if (token) {
      loadGroups();
    }
  }, [token]);

  const loadGroups = async () => {
    try {
      setLoading(true);
      const data = await getChartAccountGroups();
      setGroups(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar grupos');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      if (editingGroup) {
        await updateGroup(editingGroup.id, formData);
      } else {
        await createGroup(formData);
      }
      
      setShowModal(false);
      resetForm();
      loadGroups();
    } catch (err: any) {
      setError(err.message || 'Erro ao salvar grupo');
    }
  };

  const handleEdit = (group: Group) => {
    setEditingGroup(group);
    setFormData({
      name: group.name,
      code: group.code,
      description: group.description || '',
      is_active: group.is_active
    });
    setModalTitle('Editar Grupo');
    setShowModal(true);
  };

  const handleDelete = async (groupId: string) => {
    if (confirm('Tem certeza que deseja excluir este grupo?')) {
      try {
        await deleteGroup(groupId);
        loadGroups();
      } catch (err: any) {
        setError(err.message || 'Erro ao excluir grupo');
      }
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      code: '',
      description: '',
      is_active: true
    });
    setEditingGroup(null);
    setModalTitle('');
  };

  const openCreateModal = () => {
    resetForm();
    setModalTitle('Novo Grupo');
    setShowModal(true);
  };

  const filteredGroups = groups.filter(group => {
    const matchesSearch = group.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         group.code.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterActive === null || group.is_active === filterActive;
    return matchesSearch && matchesFilter;
  });

  if (!token) {
    return (
      <Layout title="Grupos">
        <div className="text-center py-8">
          <p className="text-gray-600">Usuário não autenticado</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Grupos">
      <div className="p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Grupos do Plano de Contas</h1>
            <p className="text-gray-600">Gerencie os grupos para organizar suas contas contábeis</p>
          </div>
          <Button onClick={openCreateModal} className="flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Novo Grupo
          </Button>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-sm border p-4 mb-6">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex-1 min-w-64">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Buscar grupos..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <select
                value={filterActive === null ? '' : filterActive.toString()}
                onChange={(e) => setFilterActive(e.target.value === '' ? null : e.target.value === 'true')}
                className="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Todos</option>
                <option value="true">Ativos</option>
                <option value="false">Inativos</option>
              </select>
            </div>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Groups Table */}
        <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
          {loading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-600">Carregando grupos...</p>
            </div>
          ) : filteredGroups.length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-gray-500">Nenhum grupo encontrado</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Código
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Nome
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Descrição
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Criado em
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Ações
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredGroups.map((group) => (
                    <tr key={group.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {group.code}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {group.name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {group.description || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          group.is_active 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {group.is_active ? 'Ativo' : 'Inativo'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(group.created_at).toLocaleDateString('pt-BR')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleEdit(group)}
                            className="flex items-center gap-1"
                          >
                            <Edit className="w-3 h-3" />
                            Editar
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDelete(group.id)}
                            className="flex items-center gap-1 text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="w-3 h-3" />
                            Excluir
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h2 className="text-xl font-bold mb-4">{modalTitle}</h2>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Código *
                </label>
                <input
                  type="text"
                  required
                  value={formData.code}
                  onChange={(e) => setFormData({...formData, code: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Ex: 1"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Ex: Ativo"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Descrição
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Descrição opcional do grupo"
                  rows={3}
                />
              </div>
              
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="is_active" className="ml-2 block text-sm text-gray-900">
                  Grupo ativo
                </label>
              </div>
              
              <div className="flex gap-3 pt-4">
                <Button type="submit" className="flex-1">
                  {editingGroup ? 'Atualizar' : 'Criar'}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowModal(false)}
                  className="flex-1"
                >
                  Cancelar
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </Layout>
  );
};

export default Groups;

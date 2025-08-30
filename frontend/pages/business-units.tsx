import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { getBusinessUnits, createBusinessUnit, updateBusinessUnit, deleteBusinessUnit, getTenants } from '../services/api';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Modal from '../components/ui/Modal';
import ProtectedRoute from '../components/ProtectedRoute';

interface BusinessUnit {
  id: string;
  tenant_id: string;
  name: string;
  code: string;
  status: string;
  created_at: string;
  updated_at: string;
}

interface Tenant {
  id: string;
  name: string;
  domain: string;
  status: string;
}

interface BusinessUnitFormData {
  tenant_id: string;
  name: string;
  code: string;
  status: string;
}

const BusinessUnitsContent: React.FC = () => {
  const { token } = useAuth();
  const [businessUnits, setBusinessUnits] = useState<BusinessUnit[]>([]);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingBU, setEditingBU] = useState<BusinessUnit | null>(null);
  const [formData, setFormData] = useState<BusinessUnitFormData>({
    tenant_id: '',
    name: '',
    code: '',
    status: 'active'
  });
  const [loading, setLoading] = useState(true);

  const fetchBusinessUnits = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getBusinessUnits(token ?? undefined);
      setBusinessUnits(data);
    } catch (error) {
      console.error('Erro ao carregar BUs:', error);
    } finally {
      setLoading(false);
    }
  }, [token]);

  const fetchTenants = useCallback(async () => {
    try {
      const data = await getTenants(token ?? undefined);
      setTenants(data);
    } catch (error) {
      console.error('Erro ao carregar empresas:', error);
    }
  }, [token]);

  useEffect(() => {
    fetchBusinessUnits();
    fetchTenants();
  }, [fetchBusinessUnits, fetchTenants]);

  const handleInputChange = useCallback((field: keyof BusinessUnitFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  }, []);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingBU) {
        await updateBusinessUnit(editingBU.id, formData, token ?? undefined);
      } else {
        await createBusinessUnit(formData, token ?? undefined);
      }
      await fetchBusinessUnits();
      setIsModalOpen(false);
      setEditingBU(null);
      setFormData({ tenant_id: '', name: '', code: '', status: 'active' });
    } catch (error) {
      console.error('Erro ao salvar BU:', error);
    }
  }, [editingBU, formData, token, fetchBusinessUnits]);

  const handleEdit = useCallback((bu: BusinessUnit) => {
    setEditingBU(bu);
    setFormData({
      tenant_id: bu.tenant_id,
      name: bu.name,
      code: bu.code,
      status: bu.status
    });
    setIsModalOpen(true);
  }, []);

  const handleDelete = useCallback(async (id: string) => {
    if (window.confirm('Tem certeza que deseja excluir esta BU?')) {
      try {
        await deleteBusinessUnit(id, token ?? undefined);
        await fetchBusinessUnits();
      } catch (error) {
        console.error('Erro ao excluir BU:', error);
      }
    }
  }, [token, fetchBusinessUnits]);

  const openCreateModal = useCallback(() => {
    setEditingBU(null);
    setFormData({ tenant_id: '', name: '', code: '', status: 'active' });
    setIsModalOpen(true);
  }, []);

  const closeModal = useCallback(() => {
    setIsModalOpen(false);
    setEditingBU(null);
    setFormData({ tenant_id: '', name: '', code: '', status: 'active' });
  }, []);

  const getTenantName = useCallback((tenantId: string) => {
    const tenant = tenants.find(t => t.id === tenantId);
    return tenant ? tenant.name : 'N/A';
  }, [tenants]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Carregando BUs...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Business Units</h1>
        <Button onClick={openCreateModal} className="bg-blue-600 hover:bg-blue-700">
          Nova BU
        </Button>
      </div>

      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Nome
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Código
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Empresa
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Criado em
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {businessUnits.map((bu) => (
                <tr key={bu.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {bu.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {bu.code}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {getTenantName(bu.tenant_id)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      bu.status === 'active' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {bu.status === 'active' ? 'Ativo' : 'Inativo'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(bu.created_at).toLocaleDateString('pt-BR')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => handleEdit(bu)}
                      className="text-indigo-600 hover:text-indigo-900 mr-4"
                    >
                      Editar
                    </button>
                    <button
                      onClick={() => handleDelete(bu.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Excluir
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <Modal 
        isOpen={isModalOpen} 
        onClose={closeModal}
        title={editingBU ? 'Editar BU' : 'Nova BU'}
      >
        <div className="bg-white p-6 rounded-lg max-w-md w-full">
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Empresa
              </label>
              <select
                value={formData.tenant_id}
                onChange={(e) => handleInputChange('tenant_id', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                <option value="">Selecione uma empresa</option>
                {tenants.map((tenant) => (
                  <option key={tenant.id} value={tenant.id}>
                    {tenant.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Nome da BU
              </label>
              <Input
                type="text"
                placeholder="Digite o nome da BU"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                required
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Código
              </label>
              <Input
                type="text"
                placeholder="Digite o código da BU"
                value={formData.code}
                onChange={(e) => handleInputChange('code', e.target.value)}
                required
              />
            </div>
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Status
              </label>
              <select
                value={formData.status}
                onChange={(e) => handleInputChange('status', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="active">Ativo</option>
                <option value="inactive">Inativo</option>
              </select>
            </div>
            <div className="flex justify-end space-x-3">
              <Button
                type="button"
                onClick={closeModal}
                className="bg-gray-300 hover:bg-gray-400 text-gray-800"
              >
                Cancelar
              </Button>
              <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
                {editingBU ? 'Atualizar' : 'Criar'}
              </Button>
            </div>
          </form>
        </div>
      </Modal>
    </div>
  );
};

export default function BusinessUnits() {
  return (
    <ProtectedRoute>
      <BusinessUnitsContent />
    </ProtectedRoute>
  );
}

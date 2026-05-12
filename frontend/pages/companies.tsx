import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { getTenants, createTenant, updateTenant, deleteTenant } from '../services/api';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Modal from '../components/ui/Modal';
import Layout from '../components/layout/Layout';
import ProtectedRoute from '../components/ProtectedRoute';

// Página de gerenciamento de empresas (tenants)

interface Company {
  id: string;
  name: string;
  domain: string;
  status: string;
  created_at: string;
  updated_at: string;
}

interface CompanyFormData {
  name: string;
  domain: string;
  status: string;
}

const CompaniesContent: React.FC = () => {
  const { token, user, logout } = useAuth();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCompany, setEditingCompany] = useState<Company | null>(null);
  const [formData, setFormData] = useState<CompanyFormData>({
    name: '',
    domain: '',
    status: 'active'
  });
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');

  const fetchCompanies = useCallback(async () => {
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setErrorMessage('');
      const data = await getTenants(token ?? undefined);
      setCompanies(data);
    } catch (error: any) {
      console.error('Erro ao carregar empresas:', error);
      if (error?.response?.status === 401) {
        setErrorMessage('Sua sessão expirou. Faça login novamente.');
        logout();
        return;
      }
      setErrorMessage(error?.response?.data?.detail || 'Erro ao carregar empresas');
    } finally {
      setLoading(false);
    }
  }, [token, logout]);

  useEffect(() => {
    fetchCompanies();
  }, [fetchCompanies]);

  const handleInputChange = useCallback((field: keyof CompanyFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  }, []);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setErrorMessage('');
      if (editingCompany) {
        await updateTenant(editingCompany.id, formData, token ?? undefined);
      } else {
        await createTenant(formData, token ?? undefined);
      }
      await fetchCompanies();
      setIsModalOpen(false);
      setEditingCompany(null);
      setFormData({ name: '', domain: '', status: 'active' });
    } catch (error: any) {
      console.error('Erro ao salvar empresa:', error);
      setErrorMessage(error?.response?.data?.detail || 'Erro ao salvar empresa');
    }
  }, [editingCompany, formData, token, fetchCompanies]);

  const handleEdit = useCallback((company: Company) => {
    setEditingCompany(company);
    setFormData({
      name: company.name,
      domain: company.domain,
      status: company.status
    });
    setIsModalOpen(true);
  }, []);

  const isProtectedCompany = useCallback((company: Company) => {
    return company.domain === 'finaflow.local' || company.id === user?.tenant_id;
  }, [user?.tenant_id]);

  const handleDelete = useCallback(async (company: Company) => {
    if (isProtectedCompany(company)) {
      setErrorMessage(
        company.domain === 'finaflow.local'
          ? 'A empresa global FinaFlow não pode ser excluída.'
          : 'Não é possível excluir a empresa atualmente selecionada na sua sessão.'
      );
      return;
    }

    if (window.confirm('Tem certeza que deseja excluir esta empresa?')) {
      try {
        setErrorMessage('');
        await deleteTenant(company.id, token ?? undefined);
        await fetchCompanies();
      } catch (error: any) {
        console.error('Erro ao excluir empresa:', error);
        setErrorMessage(error?.response?.data?.detail || 'Erro ao excluir empresa');
      }
    }
  }, [token, fetchCompanies, isProtectedCompany]);

  const openCreateModal = useCallback(() => {
    setEditingCompany(null);
    setFormData({ name: '', domain: '', status: 'active' });
    setIsModalOpen(true);
  }, []);

  const closeModal = useCallback(() => {
    setIsModalOpen(false);
    setEditingCompany(null);
    setFormData({ name: '', domain: '', status: 'active' });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Carregando empresas...</div>
      </div>
    );
  }

  return (
    <Layout title="Empresas">
      <div className="flex justify-between items-center mb-6">
        <Button onClick={openCreateModal} className="bg-blue-600 hover:bg-blue-700">
          Nova Empresa
        </Button>
      </div>

      {errorMessage && (
        <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {errorMessage}
        </div>
      )}

      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Nome
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Domínio
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
              {companies.map((company) => (
                <tr key={company.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {company.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {company.domain}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      company.status === 'active' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {company.status === 'active' ? 'Ativo' : 'Inativo'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(company.created_at).toLocaleDateString('pt-BR')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => handleEdit(company)}
                      className="text-indigo-600 hover:text-indigo-900 mr-4"
                    >
                      Editar
                    </button>
                    <button
                      onClick={() => handleDelete(company)}
                      disabled={isProtectedCompany(company)}
                      className={
                        isProtectedCompany(company)
                          ? 'cursor-not-allowed text-gray-400'
                          : 'text-red-600 hover:text-red-900'
                      }
                      title={
                        isProtectedCompany(company)
                          ? 'Esta empresa não pode ser excluída'
                          : 'Excluir empresa'
                      }
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
        title={editingCompany ? 'Editar Empresa' : 'Nova Empresa'}
      >
        <div className="bg-white p-6 rounded-lg max-w-md w-full">
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Nome da Empresa
              </label>
              <Input
                type="text"
                placeholder="Digite o nome da empresa"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                required
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Domínio
              </label>
              <Input
                type="text"
                placeholder="exemplo.com"
                value={formData.domain}
                onChange={(e) => handleInputChange('domain', e.target.value)}
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
                {editingCompany ? 'Atualizar' : 'Criar'}
              </Button>
            </div>
          </form>
        </div>
      </Modal>
    </Layout>
  );
};

export default function Companies() {
  return (
    <ProtectedRoute>
      <CompaniesContent />
    </ProtectedRoute>
  );
}

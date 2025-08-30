import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  getUserTenantPermissions, 
  createUserTenantPermission, 
  updateUserTenantPermission, 
  deleteUserTenantPermission,
  getUserBusinessUnitPermissions,
  createUserBusinessUnitPermission,
  updateUserBusinessUnitPermission,
  deleteUserBusinessUnitPermission,
  getUsers,
  getTenants,
  getBusinessUnits
} from '../services/api';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Modal from '../components/ui/Modal';
import Layout from '../components/layout/Layout';
import ProtectedRoute from '../components/ProtectedRoute';
import { Users, Building2, GitBranch, Shield, ShieldCheck, ShieldX, Edit, Trash2, Plus } from 'lucide-react';

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
}

interface Tenant {
  id: string;
  name: string;
  domain: string;
}

interface BusinessUnit {
  id: string;
  name: string;
  code: string;
  tenant_id: string;
}

interface TenantPermission {
  id: string;
  user_id: string;
  tenant_id: string;
  tenant_name: string;
  can_read: boolean;
  can_write: boolean;
  can_delete: boolean;
  can_manage_users: boolean;
  created_at: string;
  updated_at: string;
}

interface BusinessUnitPermission {
  id: string;
  user_id: string;
  business_unit_id: string;
  business_unit_name: string;
  tenant_name: string;
  can_read: boolean;
  can_write: boolean;
  can_delete: boolean;
  can_manage_users: boolean;
  created_at: string;
  updated_at: string;
}

const UserPermissionsContent: React.FC = () => {
  const { token } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [businessUnits, setBusinessUnits] = useState<BusinessUnit[]>([]);
  const [selectedUser, setSelectedUser] = useState<string>('');
  const [tenantPermissions, setTenantPermissions] = useState<TenantPermission[]>([]);
  const [businessUnitPermissions, setBusinessUnitPermissions] = useState<BusinessUnitPermission[]>([]);
  
  // Estados para modais
  const [isTenantModalOpen, setIsTenantModalOpen] = useState(false);
  const [isBusinessUnitModalOpen, setIsBusinessUnitModalOpen] = useState(false);
  const [editingTenantPermission, setEditingTenantPermission] = useState<TenantPermission | null>(null);
  const [editingBusinessUnitPermission, setEditingBusinessUnitPermission] = useState<BusinessUnitPermission | null>(null);
  
  // Estados para formulários
  const [tenantFormData, setTenantFormData] = useState({
    user_id: '',
    tenant_id: '',
    can_read: true,
    can_write: false,
    can_delete: false,
    can_manage_users: false
  });
  
  const [businessUnitFormData, setBusinessUnitFormData] = useState({
    user_id: '',
    business_unit_id: '',
    can_read: true,
    can_write: false,
    can_delete: false,
    can_manage_users: false
  });

  // Carregar dados iniciais
  useEffect(() => {
    fetchUsers();
    fetchTenants();
    fetchBusinessUnits();
  }, []);

  // Carregar permissões quando usuário for selecionado
  useEffect(() => {
    if (selectedUser) {
      fetchTenantPermissions();
      fetchBusinessUnitPermissions();
    }
  }, [selectedUser]);

  const fetchUsers = async () => {
    try {
      const data = await getUsers(token ?? undefined);
      setUsers(data);
    } catch (error) {
      console.error('Erro ao carregar usuários:', error);
    }
  };

  const fetchTenants = async () => {
    try {
      const data = await getTenants(token ?? undefined);
      setTenants(data);
    } catch (error) {
      console.error('Erro ao carregar empresas:', error);
    }
  };

  const fetchBusinessUnits = async () => {
    try {
      const data = await getBusinessUnits(token ?? undefined);
      setBusinessUnits(data);
    } catch (error) {
      console.error('Erro ao carregar BUs:', error);
    }
  };

  const fetchTenantPermissions = async () => {
    try {
      const data = await getUserTenantPermissions(selectedUser, token ?? undefined);
      setTenantPermissions(data);
    } catch (error) {
      console.error('Erro ao carregar permissões de empresa:', error);
    }
  };

  const fetchBusinessUnitPermissions = async () => {
    try {
      const data = await getUserBusinessUnitPermissions(selectedUser, token ?? undefined);
      setBusinessUnitPermissions(data);
    } catch (error) {
      console.error('Erro ao carregar permissões de BU:', error);
    }
  };

  // Handlers para permissões de empresa
  const openTenantModal = (permission?: TenantPermission) => {
    if (permission) {
      setEditingTenantPermission(permission);
      setTenantFormData({
        user_id: permission.user_id,
        tenant_id: permission.tenant_id,
        can_read: permission.can_read,
        can_write: permission.can_write,
        can_delete: permission.can_delete,
        can_manage_users: permission.can_manage_users
      });
    } else {
      setEditingTenantPermission(null);
      setTenantFormData({
        user_id: selectedUser,
        tenant_id: '',
        can_read: true,
        can_write: false,
        can_delete: false,
        can_manage_users: false
      });
    }
    setIsTenantModalOpen(true);
  };

  const closeTenantModal = () => {
    setIsTenantModalOpen(false);
    setEditingTenantPermission(null);
  };

  const handleTenantSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingTenantPermission) {
        await updateUserTenantPermission(editingTenantPermission.id, tenantFormData, token ?? undefined);
      } else {
        await createUserTenantPermission(tenantFormData, token ?? undefined);
      }
      closeTenantModal();
      fetchTenantPermissions();
    } catch (error) {
      console.error('Erro ao salvar permissão de empresa:', error);
    }
  };

  const handleDeleteTenantPermission = async (permissionId: string) => {
    if (window.confirm('Tem certeza que deseja remover esta permissão?')) {
      try {
        await deleteUserTenantPermission(permissionId, token ?? undefined);
        fetchTenantPermissions();
      } catch (error) {
        console.error('Erro ao remover permissão de empresa:', error);
      }
    }
  };

  // Handlers para permissões de BU
  const openBusinessUnitModal = (permission?: BusinessUnitPermission) => {
    if (permission) {
      setEditingBusinessUnitPermission(permission);
      setBusinessUnitFormData({
        user_id: permission.user_id,
        business_unit_id: permission.business_unit_id,
        can_read: permission.can_read,
        can_write: permission.can_write,
        can_delete: permission.can_delete,
        can_manage_users: permission.can_manage_users
      });
    } else {
      setEditingBusinessUnitPermission(null);
      setBusinessUnitFormData({
        user_id: selectedUser,
        business_unit_id: '',
        can_read: true,
        can_write: false,
        can_delete: false,
        can_manage_users: false
      });
    }
    setIsBusinessUnitModalOpen(true);
  };

  const closeBusinessUnitModal = () => {
    setIsBusinessUnitModalOpen(false);
    setEditingBusinessUnitPermission(null);
  };

  const handleBusinessUnitSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingBusinessUnitPermission) {
        await updateUserBusinessUnitPermission(editingBusinessUnitPermission.id, businessUnitFormData, token ?? undefined);
      } else {
        await createUserBusinessUnitPermission(businessUnitFormData, token ?? undefined);
      }
      closeBusinessUnitModal();
      fetchBusinessUnitPermissions();
    } catch (error) {
      console.error('Erro ao salvar permissão de BU:', error);
    }
  };

  const handleDeleteBusinessUnitPermission = async (permissionId: string) => {
    if (window.confirm('Tem certeza que deseja remover esta permissão?')) {
      try {
        await deleteUserBusinessUnitPermission(permissionId, token ?? undefined);
        fetchBusinessUnitPermissions();
      } catch (error) {
        console.error('Erro ao remover permissão de BU:', error);
      }
    }
  };

  const getPermissionIcon = (hasPermission: boolean) => {
    return hasPermission ? (
      <ShieldCheck className="w-4 h-4 text-green-600" />
    ) : (
      <ShieldX className="w-4 h-4 text-red-600" />
    );
  };

  return (
    <Layout title="Permissões de Usuário">
      <div className="space-y-6">
        {/* Seletor de usuário */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <Users className="w-5 h-5 mr-2" />
            Selecionar Usuário
          </h2>
          <select
            value={selectedUser}
            onChange={(e) => setSelectedUser(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Selecione um usuário</option>
            {users.map((user) => (
              <option key={user.id} value={user.id}>
                {user.name} ({user.email}) - {user.role}
              </option>
            ))}
          </select>
        </div>

        {selectedUser && (
          <>
            {/* Permissões de Empresa */}
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold flex items-center">
                  <Building2 className="w-5 h-5 mr-2" />
                  Permissões de Empresa
                </h2>
                <Button onClick={() => openTenantModal()} className="bg-blue-600 hover:bg-blue-700">
                  <Plus className="w-4 h-4 mr-2" />
                  Nova Permissão
                </Button>
              </div>
              
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Empresa</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ler</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Escrever</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Excluir</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Gerenciar Usuários</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ações</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {tenantPermissions.map((permission) => (
                      <tr key={permission.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {permission.tenant_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {getPermissionIcon(permission.can_read)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {getPermissionIcon(permission.can_write)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {getPermissionIcon(permission.can_delete)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {getPermissionIcon(permission.can_manage_users)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button
                            onClick={() => openTenantModal(permission)}
                            className="text-indigo-600 hover:text-indigo-900 mr-4"
                          >
                            <Edit className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteTenantPermission(permission.id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Permissões de Business Unit */}
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold flex items-center">
                  <GitBranch className="w-5 h-5 mr-2" />
                  Permissões de Business Unit
                </h2>
                <Button onClick={() => openBusinessUnitModal()} className="bg-blue-600 hover:bg-blue-700">
                  <Plus className="w-4 h-4 mr-2" />
                  Nova Permissão
                </Button>
              </div>
              
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">BU</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Empresa</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ler</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Escrever</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Excluir</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Gerenciar Usuários</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ações</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {businessUnitPermissions.map((permission) => (
                      <tr key={permission.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {permission.business_unit_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {permission.tenant_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {getPermissionIcon(permission.can_read)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {getPermissionIcon(permission.can_write)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {getPermissionIcon(permission.can_delete)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {getPermissionIcon(permission.can_manage_users)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button
                            onClick={() => openBusinessUnitModal(permission)}
                            className="text-indigo-600 hover:text-indigo-900 mr-4"
                          >
                            <Edit className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteBusinessUnitPermission(permission.id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Modal para permissões de empresa */}
      <Modal
        isOpen={isTenantModalOpen}
        onClose={closeTenantModal}
        title={editingTenantPermission ? 'Editar Permissão de Empresa' : 'Nova Permissão de Empresa'}
      >
        <form onSubmit={handleTenantSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Empresa
            </label>
            <select
              value={tenantFormData.tenant_id}
              onChange={(e) => setTenantFormData({...tenantFormData, tenant_id: e.target.value})}
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
          
          <div className="grid grid-cols-2 gap-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={tenantFormData.can_read}
                onChange={(e) => setTenantFormData({...tenantFormData, can_read: e.target.checked})}
                className="mr-2"
              />
              <span className="text-sm">Ler</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={tenantFormData.can_write}
                onChange={(e) => setTenantFormData({...tenantFormData, can_write: e.target.checked})}
                className="mr-2"
              />
              <span className="text-sm">Escrever</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={tenantFormData.can_delete}
                onChange={(e) => setTenantFormData({...tenantFormData, can_delete: e.target.checked})}
                className="mr-2"
              />
              <span className="text-sm">Excluir</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={tenantFormData.can_manage_users}
                onChange={(e) => setTenantFormData({...tenantFormData, can_manage_users: e.target.checked})}
                className="mr-2"
              />
              <span className="text-sm">Gerenciar Usuários</span>
            </label>
          </div>
          
          <div className="flex justify-end space-x-3">
            <Button type="button" onClick={closeTenantModal} className="bg-gray-300 hover:bg-gray-400">
              Cancelar
            </Button>
            <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
              {editingTenantPermission ? 'Atualizar' : 'Criar'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal para permissões de BU */}
      <Modal
        isOpen={isBusinessUnitModalOpen}
        onClose={closeBusinessUnitModal}
        title={editingBusinessUnitPermission ? 'Editar Permissão de BU' : 'Nova Permissão de BU'}
      >
        <form onSubmit={handleBusinessUnitSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Business Unit
            </label>
            <select
              value={businessUnitFormData.business_unit_id}
              onChange={(e) => setBusinessUnitFormData({...businessUnitFormData, business_unit_id: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              <option value="">Selecione uma BU</option>
              {businessUnits.map((bu) => (
                <option key={bu.id} value={bu.id}>
                  {bu.name} ({bu.code})
                </option>
              ))}
            </select>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={businessUnitFormData.can_read}
                onChange={(e) => setBusinessUnitFormData({...businessUnitFormData, can_read: e.target.checked})}
                className="mr-2"
              />
              <span className="text-sm">Ler</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={businessUnitFormData.can_write}
                onChange={(e) => setBusinessUnitFormData({...businessUnitFormData, can_write: e.target.checked})}
                className="mr-2"
              />
              <span className="text-sm">Escrever</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={businessUnitFormData.can_delete}
                onChange={(e) => setBusinessUnitFormData({...businessUnitFormData, can_delete: e.target.checked})}
                className="mr-2"
              />
              <span className="text-sm">Excluir</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={businessUnitFormData.can_manage_users}
                onChange={(e) => setBusinessUnitFormData({...businessUnitFormData, can_manage_users: e.target.checked})}
                className="mr-2"
              />
              <span className="text-sm">Gerenciar Usuários</span>
            </label>
          </div>
          
          <div className="flex justify-end space-x-3">
            <Button type="button" onClick={closeBusinessUnitModal} className="bg-gray-300 hover:bg-gray-400">
              Cancelar
            </Button>
            <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
              {editingBusinessUnitPermission ? 'Atualizar' : 'Criar'}
            </Button>
          </div>
        </form>
      </Modal>
    </Layout>
  );
};

export default function UserPermissions() {
  return (
    <ProtectedRoute>
      <UserPermissionsContent />
    </ProtectedRoute>
  );
}

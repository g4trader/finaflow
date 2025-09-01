'use client';
import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { motion } from 'framer-motion';
import Layout from '../components/layout/Layout';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import { Shield, Users, Building2, GitBranch, Check, X, Plus, Settings } from 'lucide-react';
import { getUsers, getTenants, getBusinessUnits, getUserPermissions, updateUserPermissions, getPermissions } from '../services/api';

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  status: string;
}

interface Tenant {
  id: string;
  name: string;
}

interface BusinessUnit {
  id: string;
  name: string;
  code: string;
  tenant_id: string;
}

interface Permission {
  id: string;
  name: string;
  code: string;
  description: string;
  category: string;
}

interface UserPermission {
  id: string;
  user_id: string;
  business_unit_id: string;
  permission_id: string;
  is_granted: boolean;
}

export default function UserPermissions() {
  const [users, setUsers] = useState<User[]>([]);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [businessUnits, setBusinessUnits] = useState<BusinessUnit[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [selectedTenant, setSelectedTenant] = useState<string>('');
  const [selectedBusinessUnit, setSelectedBusinessUnit] = useState<string>('');
  const [userPermissions, setUserPermissions] = useState<UserPermission[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [usersData, tenantsData, permissionsData] = await Promise.all([
        getUsers(),
        getTenants(),
        getPermissions()
      ]);
      
      setUsers(usersData);
      setTenants(tenantsData);
      setPermissions(permissionsData);
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
      setError('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  const loadBusinessUnits = async (tenantId: string) => {
    try {
      const businessUnitsData = await getBusinessUnits(tenantId);
      setBusinessUnits(businessUnitsData);
    } catch (error) {
      console.error('Erro ao carregar BUs:', error);
    }
  };

  const loadUserPermissions = async (userId: string, businessUnitId: string) => {
    try {
      const permissionsData = await getUserPermissions(userId, businessUnitId);
      setUserPermissions(permissionsData);
    } catch (error) {
      console.error('Erro ao carregar permissões:', error);
    }
  };

  const handleTenantChange = (tenantId: string) => {
    setSelectedTenant(tenantId);
    setSelectedBusinessUnit('');
    setBusinessUnits([]);
    if (tenantId) {
      loadBusinessUnits(tenantId);
    }
  };

  const handleBusinessUnitChange = (businessUnitId: string) => {
    setSelectedBusinessUnit(businessUnitId);
    if (selectedUser && businessUnitId) {
      loadUserPermissions(selectedUser.id, businessUnitId);
    }
  };

  const handlePermissionToggle = (permissionId: string) => {
    setUserPermissions(prev => 
      prev.map(perm => 
        perm.permission_id === permissionId 
          ? { ...perm, is_granted: !perm.is_granted }
          : perm
      )
    );
  };

  const handleSavePermissions = async () => {
    if (!selectedUser || !selectedBusinessUnit) {
      setError('Selecione um usuário e uma unidade de negócio');
      return;
    }

    try {
      setSaving(true);
      await updateUserPermissions(selectedUser.id, selectedBusinessUnit, userPermissions);
      setError('');
      // Recarregar permissões
      await loadUserPermissions(selectedUser.id, selectedBusinessUnit);
    } catch (error) {
      console.error('Erro ao salvar permissões:', error);
      setError('Erro ao salvar permissões');
    } finally {
      setSaving(false);
    }
  };

  const groupedPermissions = permissions.reduce((acc, permission) => {
    if (!acc[permission.category]) {
      acc[permission.category] = [];
    }
    acc[permission.category].push(permission);
    return acc;
  }, {} as Record<string, Permission[]>);

  if (loading) {
    return (
      <Layout title="Permissões de Usuário">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Permissões de Usuário">
      <Head>
        <title>Permissões de Usuário - FinaFlow</title>
      </Head>

      <div className="space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between"
        >
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Permissões de Usuário</h1>
            <p className="text-gray-600">Gerencie as permissões de acesso dos usuários</p>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Shield className="w-5 h-5" />
            <span>Controle de Acesso</span>
          </div>
        </motion.div>

        {/* Seleção de Usuário */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card>
            <Card.Body className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Selecionar Usuário</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {users.map(user => (
                  <div
                    key={user.id}
                    onClick={() => setSelectedUser(user)}
                    className={`p-4 border rounded-lg cursor-pointer transition-all ${
                      selectedUser?.id === user.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                        <span className="text-white font-medium">
                          {user.name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{user.name}</p>
                        <p className="text-sm text-gray-600">{user.email}</p>
                        <span className={`inline-block px-2 py-1 text-xs rounded-full ${
                          user.role === 'super_admin' ? 'bg-red-100 text-red-800' :
                          user.role === 'admin' ? 'bg-orange-100 text-orange-800' :
                          'bg-green-100 text-green-800'
                        }`}>
                          {user.role}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card.Body>
          </Card>
        </motion.div>

        {/* Configuração de Permissões */}
        {selectedUser && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card>
              <Card.Body className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Configurar Permissões para {selectedUser.name}
                </h3>

                {/* Seleção de Empresa e BU */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Empresa
                    </label>
                    <select
                      value={selectedTenant}
                      onChange={(e) => handleTenantChange(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Selecione uma empresa</option>
                      {tenants.map(tenant => (
                        <option key={tenant.id} value={tenant.id}>
                          {tenant.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Unidade de Negócio
                    </label>
                    <select
                      value={selectedBusinessUnit}
                      onChange={(e) => handleBusinessUnitChange(e.target.value)}
                      disabled={!selectedTenant}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                    >
                      <option value="">Selecione uma unidade</option>
                      {businessUnits.map(bu => (
                        <option key={bu.id} value={bu.id}>
                          {bu.name} ({bu.code})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Lista de Permissões */}
                {selectedBusinessUnit && (
                  <div className="space-y-6">
                    <div className="flex items-center justify-between">
                      <h4 className="text-md font-medium text-gray-900">Permissões Disponíveis</h4>
                      <Button
                        onClick={handleSavePermissions}
                        disabled={saving}
                        className="flex items-center gap-2"
                      >
                        {saving ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        ) : (
                          <Check className="w-4 h-4" />
                        )}
                        Salvar Permissões
                      </Button>
                    </div>

                    {error && (
                      <div className="bg-red-50 border border-red-200 rounded-md p-4">
                        <p className="text-red-800">{error}</p>
                      </div>
                    )}

                    <div className="space-y-4">
                      {Object.entries(groupedPermissions).map(([category, categoryPermissions]) => (
                        <div key={category} className="border border-gray-200 rounded-lg p-4">
                          <h5 className="font-medium text-gray-900 mb-3 capitalize">
                            {category.replace('_', ' ')}
                          </h5>
                          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                            {categoryPermissions.map(permission => {
                              const userPermission = userPermissions.find(
                                up => up.permission_id === permission.id
                              );
                              const isGranted = userPermission?.is_granted ?? false;

                              return (
                                <div
                                  key={permission.id}
                                  className="flex items-center justify-between p-3 border border-gray-200 rounded-md"
                                >
                                  <div className="flex-1">
                                    <p className="font-medium text-sm text-gray-900">
                                      {permission.name}
                                    </p>
                                    <p className="text-xs text-gray-600">
                                      {permission.description}
                                    </p>
                                  </div>
                                  <button
                                    onClick={() => handlePermissionToggle(permission.id)}
                                    className={`ml-3 p-1 rounded-full transition-colors ${
                                      isGranted
                                        ? 'bg-green-100 text-green-600 hover:bg-green-200'
                                        : 'bg-gray-100 text-gray-400 hover:bg-gray-200'
                                    }`}
                                  >
                                    {isGranted ? (
                                      <Check className="w-4 h-4" />
                                    ) : (
                                      <X className="w-4 h-4" />
                                    )}
                                  </button>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </Card.Body>
            </Card>
          </motion.div>
        )}
      </div>
    </Layout>
  );
}

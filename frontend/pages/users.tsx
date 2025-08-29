import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Plus,
  Search,
  Filter,
  MoreHorizontal,
  Edit,
  Trash2,
  Mail,
  Phone,
  Calendar,
  Shield,
  ShieldCheck,
} from 'lucide-react';
import Layout from '../components/layout/Layout';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Card from '../components/ui/Card';
import Table from '../components/ui/Table';
import Modal from '../components/ui/Modal';
import ProtectedRoute from '../components/ProtectedRoute';

interface User {
  id: string;
  name: string;
  email: string;
  phone: string;
  role: 'admin' | 'user' | 'manager';
  status: 'active' | 'inactive';
  createdAt: string;
  lastLogin: string;
}

function UsersContent() {
  const [users, setUsers] = useState<User[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRole, setSelectedRole] = useState('all');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Mock data
  useEffect(() => {
    const mockUsers: User[] = [
      {
        id: '1',
        name: 'João Silva',
        email: 'joao@empresa.com',
        phone: '(11) 99999-9999',
        role: 'admin',
        status: 'active',
        createdAt: '2024-01-15',
        lastLogin: '2024-08-07',
      },
      {
        id: '2',
        name: 'Maria Santos',
        email: 'maria@empresa.com',
        phone: '(11) 88888-8888',
        role: 'manager',
        status: 'active',
        createdAt: '2024-02-20',
        lastLogin: '2024-08-06',
      },
      {
        id: '3',
        name: 'Pedro Costa',
        email: 'pedro@empresa.com',
        phone: '(11) 77777-7777',
        role: 'user',
        status: 'inactive',
        createdAt: '2024-03-10',
        lastLogin: '2024-07-30',
      },
    ];

    setTimeout(() => {
      setUsers(mockUsers);
      setLoading(false);
    }, 1000);
  }, []);

  const filteredUsers = users.filter((user) => {
    const matchesSearch = user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRole = selectedRole === 'all' || user.role === selectedRole;
    return matchesSearch && matchesRole;
  });

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'admin':
        return <ShieldCheck className="w-4 h-4 text-red-600" />;
      case 'manager':
        return <Shield className="w-4 h-4 text-blue-600" />;
      default:
        return <Shield className="w-4 h-4 text-gray-600" />;
    }
  };

  const getRoleBadge = (role: string) => {
    const colors = {
      admin: 'bg-red-100 text-red-800',
      manager: 'bg-blue-100 text-blue-800',
      user: 'bg-gray-100 text-gray-800',
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[role as keyof typeof colors]}`}>
        {getRoleIcon(role)}
        <span className="ml-1 capitalize">{role}</span>
      </span>
    );
  };

  const getStatusBadge = (status: string) => {
    const colors = {
      active: 'bg-green-100 text-green-800',
      inactive: 'bg-gray-100 text-gray-800',
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[status as keyof typeof colors]}`}>
        <div className={`w-1.5 h-1.5 rounded-full mr-1.5 ${status === 'active' ? 'bg-green-400' : 'bg-gray-400'}`} />
        {status === 'active' ? 'Ativo' : 'Inativo'}
      </span>
    );
  };

  const UserForm = () => (
    <form className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Nome completo"
          placeholder="Digite o nome"
          defaultValue={editingUser?.name}
          fullWidth
        />
        <Input
          label="Email"
          type="email"
          placeholder="email@exemplo.com"
          defaultValue={editingUser?.email}
          icon={<Mail className="w-4 h-4" />}
          fullWidth
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Telefone"
          placeholder="(11) 99999-9999"
          defaultValue={editingUser?.phone}
          icon={<Phone className="w-4 h-4" />}
          fullWidth
        />
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Função
          </label>
          <select
            className="input w-full"
            defaultValue={editingUser?.role || 'user'}
          >
            <option value="user">Usuário</option>
            <option value="manager">Gerente</option>
            <option value="admin">Administrador</option>
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Status
        </label>
        <select
          className="input w-full"
          defaultValue={editingUser?.status || 'active'}
        >
          <option value="active">Ativo</option>
          <option value="inactive">Inativo</option>
        </select>
      </div>

      <div className="flex justify-end space-x-3 pt-4">
        <Button
          variant="secondary"
          onClick={() => setIsModalOpen(false)}
        >
          Cancelar
        </Button>
        <Button variant="primary">
          {editingUser ? 'Atualizar' : 'Criar'} Usuário
        </Button>
      </div>
    </form>
  );

  return (
    <Layout title="Usuários">
      <div className="space-y-6">
        {/* Header Actions */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex-1 max-w-lg">
            <Input
              placeholder="Buscar usuários..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              icon={<Search className="w-4 h-4" />}
              fullWidth
            />
          </div>

          <div className="flex items-center space-x-3">
            <select
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
              className="input"
            >
              <option value="all">Todas as funções</option>
              <option value="admin">Administrador</option>
              <option value="manager">Gerente</option>
              <option value="user">Usuário</option>
            </select>

            <Button
              variant="secondary"
              icon={<Filter className="w-4 h-4" />}
            >
              Filtros
            </Button>

            <Button
              variant="primary"
              icon={<Plus className="w-4 h-4" />}
              onClick={() => {
                setEditingUser(null);
                setIsModalOpen(true);
              }}
            >
              Novo Usuário
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card hover>
            <Card.Body className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                    <Shield className="w-5 h-5 text-blue-600" />
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Total de Usuários</p>
                  <p className="text-2xl font-semibold text-gray-900">{users.length}</p>
                </div>
              </div>
            </Card.Body>
          </Card>

          <Card hover>
            <Card.Body className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                    <ShieldCheck className="w-5 h-5 text-green-600" />
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Usuários Ativos</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {users.filter(u => u.status === 'active').length}
                  </p>
                </div>
              </div>
            </Card.Body>
          </Card>

          <Card hover>
            <Card.Body className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                    <Shield className="w-5 h-5 text-purple-600" />
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Administradores</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {users.filter(u => u.role === 'admin').length}
                  </p>
                </div>
              </div>
            </Card.Body>
          </Card>

          <Card hover>
            <Card.Body className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center">
                    <Calendar className="w-5 h-5 text-orange-600" />
                  </div>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Novos este mês</p>
                  <p className="text-2xl font-semibold text-gray-900">2</p>
                </div>
              </div>
            </Card.Body>
          </Card>
        </div>

        {/* Users Table */}
        <Card>
          <Card.Body className="p-0">
            {loading ? (
              <div className="p-8 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-2 text-gray-500">Carregando usuários...</p>
              </div>
            ) : (
              <Table>
                <Table.Header>
                  <Table.Row>
                    <Table.Cell header>Usuário</Table.Cell>
                    <Table.Cell header>Contato</Table.Cell>
                    <Table.Cell header>Função</Table.Cell>
                    <Table.Cell header>Status</Table.Cell>
                    <Table.Cell header>Último Login</Table.Cell>
                    <Table.Cell header>Ações</Table.Cell>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {filteredUsers.map((user) => (
                    <Table.Row key={user.id}>
                      <Table.Cell>
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10">
                            <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                              <span className="text-sm font-medium text-gray-700">
                                {user.name.split(' ').map(n => n[0]).join('')}
                              </span>
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">
                              {user.name}
                            </div>
                            <div className="text-sm text-gray-500">
                              ID: {user.id}
                            </div>
                          </div>
                        </div>
                      </Table.Cell>
                      <Table.Cell>
                        <div className="text-sm text-gray-900">{user.email}</div>
                        <div className="text-sm text-gray-500">{user.phone}</div>
                      </Table.Cell>
                      <Table.Cell>
                        {getRoleBadge(user.role)}
                      </Table.Cell>
                      <Table.Cell>
                        {getStatusBadge(user.status)}
                      </Table.Cell>
                      <Table.Cell>
                        <div className="text-sm text-gray-900">
                          {new Date(user.lastLogin).toLocaleDateString('pt-BR')}
                        </div>
                      </Table.Cell>
                      <Table.Cell>
                        <div className="flex items-center space-x-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            icon={<Edit className="w-4 h-4" />}
                            onClick={() => {
                              setEditingUser(user);
                              setIsModalOpen(true);
                            }}
                          />
                          <Button
                            variant="ghost"
                            size="sm"
                            icon={<Trash2 className="w-4 h-4" />}
                            className="text-red-600 hover:text-red-700"
                          />
                          <Button
                            variant="ghost"
                            size="sm"
                            icon={<MoreHorizontal className="w-4 h-4" />}
                          />
                        </div>
                      </Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table>
            )}
          </Card.Body>
        </Card>
      </div>

      {/* User Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingUser ? 'Editar Usuário' : 'Novo Usuário'}
        size="lg"
      >
        <UserForm />
      </Modal>
    </Layout>
  );
}

export default function Users() {
  return (
    <ProtectedRoute>
      <UsersContent />
    </ProtectedRoute>
  );
}

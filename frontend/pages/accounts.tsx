import React, { useEffect, useState, useContext } from 'react';
import { Plus, Edit, Trash2, Search, Wallet, Filter, Download, Upload } from 'lucide-react';
import Layout from '../components/layout/Layout';
import Card from '../components/ui/Card';
import Table from '../components/ui/Table';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import ProtectedRoute from '../components/ProtectedRoute';
import {
  getAccounts,
  createAccount,
  updateAccount,
  deleteAccount,
  getSubgroups,
} from '../services/api';
import { AuthContext } from '../context/AuthContext';

interface Account {
  id: string;
  subgroup_id: string;
  name: string;
  balance: number;
  tenant_id: string;
  created_at?: string;
  updated_at?: string;
}

interface Subgroup {
  id: string;
  name: string;
}

function AccountsContent() {
  const { token, tenantId } = useContext(AuthContext);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [subgroups, setSubgroups] = useState<Subgroup[]>([]);
  const [search, setSearch] = useState('');
  const [selectedSubgroup, setSelectedSubgroup] = useState('all');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editing, setEditing] = useState<Account | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    subgroup_id: '',
    name: '',
    balance: '',
  });

  const fetchData = async () => {
    try {
      setLoading(true);
      const [acs, sgs] = await Promise.all([
        getAccounts(token ?? undefined),
        getSubgroups(token ?? undefined),
      ]);
      setAccounts(acs || []);
      setSubgroups(sgs || []);
    } catch (err) {
      console.error('Erro ao buscar contas', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const openNew = () => {
    setEditing(null);
    setFormData({ subgroup_id: '', name: '', balance: '' });
    setIsModalOpen(true);
  };

  const openEdit = (a: Account) => {
    setEditing(a);
    setFormData({
      subgroup_id: a.subgroup_id,
      name: a.name,
      balance: String(a.balance),
    });
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      alert('Por favor, informe o nome da conta');
      return;
    }

    if (!formData.subgroup_id) {
      alert('Por favor, selecione um subgrupo');
      return;
    }

    const balance = parseFloat(formData.balance);
    if (isNaN(balance)) {
      alert('Por favor, informe um valor válido para o saldo');
      return;
    }

    try {
      setSubmitting(true);
      const payload = {
        subgroup_id: formData.subgroup_id,
        name: formData.name.trim(),
        balance: balance,
        tenant_id: tenantId,
      };
      
      if (editing) {
        await updateAccount(editing.id, payload);
      } else {
        await createAccount(payload, token ?? undefined);
      }
      
      await fetchData();
      setIsModalOpen(false);
    } catch (err) {
      console.error('Erro ao salvar conta', err);
      alert('Erro ao salvar conta. Tente novamente.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Tem certeza que deseja excluir esta conta?')) {
      return;
    }

    try {
      await deleteAccount(id);
      await fetchData();
    } catch (err) {
      console.error('Erro ao excluir conta', err);
      alert('Erro ao excluir conta. Tente novamente.');
    }
  };

  // Filtrar contas
  const filteredAccounts = accounts.filter(account => {
    const matchesSearch = account.name.toLowerCase().includes(search.toLowerCase());
    const matchesSubgroup = selectedSubgroup === 'all' || account.subgroup_id === selectedSubgroup;
    return matchesSearch && matchesSubgroup;
  });

  // Calcular totais
  const totalBalance = filteredAccounts.reduce((sum, account) => sum + (account.balance || 0), 0);
  const totalAccounts = filteredAccounts.length;

  // Obter nome do subgrupo
  const getSubgroupName = (subgroup_id: string) => {
    const subgroup = subgroups.find(sg => sg.id === subgroup_id);
    return subgroup?.name || 'Subgrupo não encontrado';
  };

  if (loading) {
    return (
      <Layout title="Contas">
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-medium text-gray-900">Gerenciar Contas</h2>
              <p className="text-sm text-gray-500">Controle suas contas bancárias</p>
            </div>
            <div className="h-10 bg-gray-200 rounded animate-pulse w-32"></div>
          </div>
          
          <Card>
            <Card.Body className="p-0">
              <div className="animate-pulse">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="p-6 border-b border-gray-200 last:border-b-0">
                    <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
                    <div className="h-4 bg-gray-200 rounded w-1/3"></div>
                  </div>
                ))}
              </div>
            </Card.Body>
          </Card>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Contas">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-lg font-medium text-gray-900">Gerenciar Contas</h2>
            <p className="text-sm text-gray-500">Controle suas contas bancárias</p>
          </div>
          <div className="flex items-center space-x-3">
            <Button
              variant="secondary"
              icon={<Download className="w-4 h-4" />}
            >
              Exportar
            </Button>
            <Button
              variant="secondary"
              icon={<Upload className="w-4 h-4" />}
            >
              Importar
            </Button>
            <Button
              icon={<Plus className="w-4 h-4" />}
              onClick={openNew}
            >
              Nova Conta
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <Card.Body className="p-6">
              <div className="flex items-center">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <Wallet className="w-6 h-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Total de Contas</p>
                  <p className="text-2xl font-bold text-gray-900">{totalAccounts}</p>
                </div>
              </div>
            </Card.Body>
          </Card>
          
          <Card>
            <Card.Body className="p-6">
              <div className="flex items-center">
                <div className="p-3 bg-green-100 rounded-lg">
                  <Wallet className="w-6 h-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500">Saldo Total</p>
                  <p className="text-2xl font-bold text-gray-900">
                    R$ {totalBalance.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                  </p>
                </div>
              </div>
            </Card.Body>
          </Card>
        </div>

        {/* Filters */}
        <Card>
          <Card.Body className="p-6">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Buscar Conta
                </label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <Input
                    type="text"
                    placeholder="Digite o nome da conta..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              
              <div className="sm:w-64">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Filtrar por Subgrupo
                </label>
                <select
                  value={selectedSubgroup}
                  onChange={(e) => setSelectedSubgroup(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="all">Todos os Subgrupos</option>
                  {subgroups.map(subgroup => (
                    <option key={subgroup.id} value={subgroup.id}>
                      {subgroup.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </Card.Body>
        </Card>

        {/* Accounts Table */}
        <Card>
          <Card.Body className="p-0">
            {filteredAccounts.length > 0 ? (
              <Table>
                <Table.Header>
                  <Table.Row>
                    <Table.Cell header>Nome da Conta</Table.Cell>
                    <Table.Cell header>Subgrupo</Table.Cell>
                    <Table.Cell header>Saldo</Table.Cell>
                    <Table.Cell header>Data de Criação</Table.Cell>
                    <Table.Cell header>Ações</Table.Cell>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {filteredAccounts.map((account) => (
                    <Table.Row key={account.id}>
                      <Table.Cell>
                        <div>
                          <p className="font-medium text-gray-900">{account.name}</p>
                          <p className="text-sm text-gray-500">ID: {account.id}</p>
                        </div>
                      </Table.Cell>
                      <Table.Cell>
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {getSubgroupName(account.subgroup_id)}
                        </span>
                      </Table.Cell>
                      <Table.Cell>
                        <span className={`font-medium ${
                          account.balance >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          R$ {account.balance.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                        </span>
                      </Table.Cell>
                      <Table.Cell>
                        {account.created_at ? (
                          new Date(account.created_at).toLocaleDateString('pt-BR')
                        ) : (
                          'N/A'
                        )}
                      </Table.Cell>
                      <Table.Cell>
                        <div className="flex space-x-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            icon={<Edit className="w-4 h-4" />}
                            onClick={() => openEdit(account)}
                          />
                          <Button
                            variant="ghost"
                            size="sm"
                            icon={<Trash2 className="w-4 h-4" />}
                            onClick={() => handleDelete(account.id)}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          />
                        </div>
                      </Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table>
            ) : (
              <div className="flex items-center justify-center h-64 text-gray-500">
                <div className="text-center">
                  <Wallet className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p className="text-lg font-medium">Nenhuma conta encontrada</p>
                  <p className="text-sm">Crie sua primeira conta para começar</p>
                  <Button
                    icon={<Plus className="w-4 h-4" />}
                    onClick={openNew}
                    className="mt-4"
                  >
                    Criar Conta
                  </Button>
                </div>
              </div>
            )}
          </Card.Body>
        </Card>

        {/* Modal */}
        <Modal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          title={editing ? 'Editar Conta' : 'Nova Conta'}
        >
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Nome da Conta *
              </label>
              <Input
                type="text"
                placeholder="Ex: Conta Corrente Banco do Brasil"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Subgrupo *
              </label>
              <select
                value={formData.subgroup_id}
                onChange={(e) => setFormData({ ...formData, subgroup_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              >
                <option value="">Selecione um subgrupo</option>
                {subgroups.map(subgroup => (
                  <option key={subgroup.id} value={subgroup.id}>
                    {subgroup.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Saldo Inicial *
              </label>
              <Input
                type="number"
                step="0.01"
                placeholder="0,00"
                value={formData.balance}
                onChange={(e) => setFormData({ ...formData, balance: e.target.value })}
                required
              />
            </div>

            <div className="flex justify-end space-x-3 pt-4">
              <Button
                type="button"
                variant="secondary"
                onClick={() => setIsModalOpen(false)}
                disabled={submitting}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={submitting}
              >
                {submitting ? 'Salvando...' : editing ? 'Atualizar' : 'Criar'}
              </Button>
            </div>
          </form>
        </Modal>
      </div>
    </Layout>
  );
}

export default function Accounts() {
  return (
    <ProtectedRoute>
      <AccountsContent />
    </ProtectedRoute>
  );
}

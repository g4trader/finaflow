import React, { useEffect, useState, useContext } from 'react';
import { Plus, Edit, Trash2, Search } from 'lucide-react';
import Layout from '../components/layout/Layout';
import Card from '../components/ui/Card';
import Table from '../components/ui/Table';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import {
  getForecasts,
  createForecast,
  updateForecast,
  deleteForecast,
  getAccounts,
} from '../services/api';
import { AuthContext } from '../context/AuthContext';

interface Forecast {
  id: string;
  account_id: string;
  amount: number;
  description?: string;
  tenant_id: string;
  created_at: string;
}

interface Account {
  id: string;
  name: string;
}

function ForecastContent() {
  const { token, tenantId } = useContext(AuthContext);
  const [forecasts, setForecasts] = useState<Forecast[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [search, setSearch] = useState('');
  const [selectedAccount, setSelectedAccount] = useState('all');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editing, setEditing] = useState<Forecast | null>(null);
  const [formData, setFormData] = useState({
    account_id: '',
    amount: '',
    description: '',
  });

  const fetchData = async () => {
    try {
      const [fcs, acs] = await Promise.all([
        getForecasts(token ?? undefined),
        getAccounts(token ?? undefined),
      ]);
      setForecasts(fcs);
      setAccounts(acs);
    } catch (err) {
      console.error('Erro ao buscar previsões', err);
    }
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const openNew = () => {
    setEditing(null);
    setFormData({ account_id: '', amount: '', description: '' });
    setIsModalOpen(true);
  };

  const openEdit = (f: Forecast) => {
    setEditing(f);
    setFormData({
      account_id: f.account_id,
      amount: String(f.amount),
      description: f.description || '',
    });
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      account_id: formData.account_id,
      amount: parseFloat(formData.amount),
      description: formData.description,
      tenant_id: tenantId,
    };
    try {
      if (editing) {
        await updateForecast(editing.id, payload, token ?? undefined);
      } else {
        await createForecast(payload, token ?? undefined);
      }
      await fetchData();
      setIsModalOpen(false);
    } catch (err) {
      console.error('Erro ao salvar previsão', err);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteForecast(id, token ?? undefined);
      await fetchData();
    } catch (err) {
      console.error('Erro ao excluir previsão', err);
    }
  };

  const filtered = forecasts.filter((f) => {
    const matchesSearch = (f.description || '')
      .toLowerCase()
      .includes(search.toLowerCase());
    const matchesAccount =
      selectedAccount === 'all' || f.account_id === selectedAccount;
    return matchesSearch && matchesAccount;
  });

  return (
    <Layout title="Forecast">
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex-1 max-w-xs">
            <Input
              placeholder="Buscar previsões..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              icon={<Search className="w-4 h-4" />}
              fullWidth
            />
          </div>
          <div className="flex items-center space-x-3">
            <select
              value={selectedAccount}
              onChange={(e) => setSelectedAccount(e.target.value)}
              className="input"
            >
              <option value="all">Todas as contas</option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
            <Button icon={<Plus className="w-4 h-4" />} onClick={openNew}>
              Nova Previsão
            </Button>
          </div>
        </div>

        <Card>
          <Card.Body className="p-0">
            <Table>
              <Table.Header>
                <Table.Row>
                  <Table.Cell header>Conta</Table.Cell>
                  <Table.Cell header>Valor</Table.Cell>
                  <Table.Cell header>Descrição</Table.Cell>
                  <Table.Cell header>Data</Table.Cell>
                  <Table.Cell header>Ações</Table.Cell>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {filtered.map((f) => (
                  <Table.Row key={f.id}>
                    <Table.Cell>{accounts.find((a) => a.id === f.account_id)?.name}</Table.Cell>
                    <Table.Cell>R$ {Number(f.amount).toFixed(2)}</Table.Cell>
                    <Table.Cell>{f.description}</Table.Cell>
                    <Table.Cell>
                      {new Date(f.created_at).toLocaleDateString('pt-BR')}
                    </Table.Cell>
                    <Table.Cell>
                      <div className="flex space-x-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={<Edit className="w-4 h-4" />}
                          onClick={() => openEdit(f)}
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-red-600 hover:text-red-700"
                          icon={<Trash2 className="w-4 h-4" />}
                          onClick={() => handleDelete(f.id)}
                        />
                      </div>
                    </Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table>
          </Card.Body>
        </Card>
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editing ? 'Editar Previsão' : 'Nova Previsão'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Conta
            </label>
            <select
              className="input w-full"
              value={formData.account_id}
              onChange={(e) =>
                setFormData({ ...formData, account_id: e.target.value })
              }
            >
              <option value="">Selecione uma conta</option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
          </div>
          <Input
            label="Valor"
            type="number"
            step="0.01"
            value={formData.amount}
            onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
            fullWidth
          />
          <Input
            label="Descrição"
            value={formData.description}
            onChange={(e) =>
              setFormData({ ...formData, description: e.target.value })
            }
            fullWidth
          />
          <div className="flex justify-end space-x-2">
            <Button
              variant="secondary"
              type="button"
              onClick={() => setIsModalOpen(false)}
            >
              Cancelar
            </Button>
            <Button type="submit" variant="primary">
              {editing ? 'Atualizar' : 'Criar'}
            </Button>
          </div>
        </form>
      </Modal>
    </Layout>
  );
}

export default function Forecast() {
  return (
    <ProtectedRoute>
      <ForecastContent />
    </ProtectedRoute>
  );
}

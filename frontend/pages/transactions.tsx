import React, { useEffect, useState, useContext } from 'react';
import { Plus, Edit, Trash2 } from 'lucide-react';
import Layout from '../components/layout/Layout';
import Card from '../components/ui/Card';
import Table from '../components/ui/Table';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import ProtectedRoute from '../components/ProtectedRoute';
import {
  getTransactions,
  createTransaction,
  updateTransaction,
  deleteTransaction,
} from '../services/api';
import { AuthContext } from '../context/AuthContext';

interface Transaction {
  id: string;
  account_id: string;
  amount: number;
  description?: string;
  created_at: string;
}

function TransactionsContent() {
  const { token } = useContext(AuthContext);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editing, setEditing] = useState<Transaction | null>(null);
  const [formData, setFormData] = useState({
    account_id: '',
    amount: '',
    description: '',
  });

  const fetchTransactions = async () => {
    try {
      const data = await getTransactions(token ?? undefined);
      setTransactions(data);
    } catch (error) {
      console.error('Erro ao buscar transações', error);
    }
  };

  useEffect(() => {
    fetchTransactions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const openNewModal = () => {
    setEditing(null);
    setFormData({ account_id: '', amount: '', description: '' });
    setIsModalOpen(true);
  };

  const openEditModal = (t: Transaction) => {
    setEditing(t);
    setFormData({
      account_id: t.account_id,
      amount: String(t.amount),
      description: t.description || '',
    });
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      account_id: formData.account_id,
      amount: parseFloat(formData.amount),
      description: formData.description,
    };
    try {
      if (editing) {
        await updateTransaction(editing.id, payload, token ?? undefined);
      } else {
        await createTransaction(payload, token ?? undefined);
      }
      await fetchTransactions();
      setIsModalOpen(false);
    } catch (error) {
      console.error('Erro ao salvar transação', error);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteTransaction(id, token ?? undefined);
      await fetchTransactions();
    } catch (error) {
      console.error('Erro ao excluir transação', error);
    }
  };

  return (
    <Layout title="Transações">
      <div className="space-y-6">
        <div className="flex justify-end">
          <Button icon={<Plus className="w-4 h-4" />} onClick={openNewModal}>
            Nova Transação
          </Button>
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
                {transactions.map((t) => (
                  <Table.Row key={t.id}>
                    <Table.Cell>{t.account_id}</Table.Cell>
                    <Table.Cell>R$ {Number(t.amount).toFixed(2)}</Table.Cell>
                    <Table.Cell>{t.description}</Table.Cell>
                    <Table.Cell>
                      {new Date(t.created_at).toLocaleDateString('pt-BR')}
                    </Table.Cell>
                    <Table.Cell>
                      <div className="flex space-x-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={<Edit className="w-4 h-4" />}
                          onClick={() => openEditModal(t)}
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={<Trash2 className="w-4 h-4" />}
                          onClick={() => handleDelete(t.id)}
                        />
                      </div>
                    </Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table>
          </Card.Body>
        </Card>

        <Modal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          title={editing ? 'Editar Transação' : 'Nova Transação'}
        >
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="ID da Conta"
              value={formData.account_id}
              onChange={(e) => setFormData({ ...formData, account_id: e.target.value })}
              fullWidth
            />
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
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
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
      </div>
    </Layout>
  );
}

export default function Transactions() {
  return (
    <ProtectedRoute>
      <TransactionsContent />
    </ProtectedRoute>
  );
}


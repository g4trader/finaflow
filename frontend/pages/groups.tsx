import React, { useEffect, useState, useContext } from 'react';
import { Plus, Edit, Trash2, Search } from 'lucide-react';
import Layout from '../components/layout/Layout';
import Card from '../components/ui/Card';
import Table from '../components/ui/Table';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import {
  getGroups,
  createGroup,
  updateGroup,
  deleteGroup,
} from '../services/api';
import { AuthContext } from '../context/AuthContext';

interface Group {
  id: string;
  name: string;
  description?: string;
  tenant_id: string;
}

export default function Groups() {
  const { token, tenantId } = useContext(AuthContext);
  const [groups, setGroups] = useState<Group[]>([]);
  const [search, setSearch] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editing, setEditing] = useState<Group | null>(null);
  const [formData, setFormData] = useState({ name: '', description: '' });

  const fetchGroups = async () => {
    try {
      const data = await getGroups(token ?? undefined);
      setGroups(data);
    } catch (err) {
      console.error('Erro ao buscar grupos', err);
    }
  };

  useEffect(() => {
    fetchGroups();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const openNew = () => {
    setEditing(null);
    setFormData({ name: '', description: '' });
    setIsModalOpen(true);
  };

  const openEdit = (g: Group) => {
    setEditing(g);
    setFormData({ name: g.name, description: g.description || '' });
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = { ...formData, tenant_id: tenantId };
    try {
      if (editing) {
        await updateGroup(editing.id, payload, token ?? undefined);
      } else {
        await createGroup(payload, token ?? undefined);
      }
      await fetchGroups();
      setIsModalOpen(false);
    } catch (err) {
      console.error('Erro ao salvar grupo', err);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteGroup(id, token ?? undefined);
      await fetchGroups();
    } catch (err) {
      console.error('Erro ao excluir grupo', err);
    }
  };

  const filtered = groups.filter((g) =>
    g.name.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <Layout title="Groups">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="max-w-xs w-full">
            <Input
              placeholder="Buscar grupos..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              icon={<Search className="w-4 h-4" />}
              fullWidth
            />
          </div>
          <Button icon={<Plus className="w-4 h-4" />} onClick={openNew}>
            Novo Grupo
          </Button>
        </div>

        <Card>
          <Card.Body className="p-0">
            <Table>
              <Table.Header>
                <Table.Row>
                  <Table.Cell header>Nome</Table.Cell>
                  <Table.Cell header>Descrição</Table.Cell>
                  <Table.Cell header>Ações</Table.Cell>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {filtered.map((g) => (
                  <Table.Row key={g.id}>
                    <Table.Cell>{g.name}</Table.Cell>
                    <Table.Cell>{g.description}</Table.Cell>
                    <Table.Cell>
                      <div className="flex space-x-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={<Edit className="w-4 h-4" />}
                          onClick={() => openEdit(g)}
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-red-600 hover:text-red-700"
                          icon={<Trash2 className="w-4 h-4" />}
                          onClick={() => handleDelete(g.id)}
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
        title={editing ? 'Editar Grupo' : 'Novo Grupo'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Nome"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
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

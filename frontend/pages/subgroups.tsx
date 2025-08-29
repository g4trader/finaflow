import React, { useEffect, useState, useContext } from 'react';
import { Plus, Edit, Trash2, Search } from 'lucide-react';
import Layout from '../components/layout/Layout';
import Card from '../components/ui/Card';
import Table from '../components/ui/Table';
import Modal from '../components/ui/Modal';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import {
  getSubgroups,
  createSubgroup,
  updateSubgroup,
  deleteSubgroup,
  getGroups,
} from '../services/api';
import { AuthContext } from '../context/AuthContext';
import ProtectedRoute from '../components/ProtectedRoute';

interface Subgroup {
  id: string;
  group_id: string;
  name: string;
  description?: string;
  tenant_id: string;
}

interface Group {
  id: string;
  name: string;
}

function SubgroupsContent() {
  const { token, tenantId } = useContext(AuthContext);
  const [subgroups, setSubgroups] = useState<Subgroup[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [search, setSearch] = useState('');
  const [selectedGroup, setSelectedGroup] = useState('all');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editing, setEditing] = useState<Subgroup | null>(null);
  const [formData, setFormData] = useState({
    group_id: '',
    name: '',
    description: '',
  });

  const fetchData = async () => {
    try {
      const [sgs, gs] = await Promise.all([
        getSubgroups(token ?? undefined),
        getGroups(token ?? undefined),
      ]);
      setSubgroups(sgs);
      setGroups(gs);
    } catch (err) {
      console.error('Erro ao buscar subgrupos', err);
    }
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const openNew = () => {
    setEditing(null);
    setFormData({ group_id: '', name: '', description: '' });
    setIsModalOpen(true);
  };

  const openEdit = (s: Subgroup) => {
    setEditing(s);
    setFormData({
      group_id: s.group_id,
      name: s.name,
      description: s.description || '',
    });
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = { ...formData, tenant_id: tenantId };
    try {
      if (editing) {
        await updateSubgroup(editing.id, payload, token ?? undefined);
      } else {
        await createSubgroup(payload, token ?? undefined);
      }
      await fetchData();
      setIsModalOpen(false);
    } catch (err) {
      console.error('Erro ao salvar subgrupo', err);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteSubgroup(id, token ?? undefined);
      await fetchData();
    } catch (err) {
      console.error('Erro ao excluir subgrupo', err);
    }
  };

  const filtered = subgroups.filter((s) => {
    const matchesSearch = s.name
      .toLowerCase()
      .includes(search.toLowerCase());
    const matchesGroup =
      selectedGroup === 'all' || s.group_id === selectedGroup;
    return matchesSearch && matchesGroup;
  });

  return (
    <Layout title="Subgroups">
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex-1 max-w-xs">
            <Input
              placeholder="Buscar subgrupos..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              icon={<Search className="w-4 h-4" />}
              fullWidth
            />
          </div>
          <div className="flex items-center space-x-3">
            <select
              value={selectedGroup}
              onChange={(e) => setSelectedGroup(e.target.value)}
              className="input"
            >
              <option value="all">Todos os grupos</option>
              {groups.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.name}
                </option>
              ))}
            </select>
            <Button icon={<Plus className="w-4 h-4" />} onClick={openNew}>
              Novo Subgrupo
            </Button>
          </div>
        </div>

        <Card>
          <Card.Body className="p-0">
            <Table>
              <Table.Header>
                <Table.Row>
                  <Table.Cell header>Nome</Table.Cell>
                  <Table.Cell header>Grupo</Table.Cell>
                  <Table.Cell header>Descrição</Table.Cell>
                  <Table.Cell header>Ações</Table.Cell>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {filtered.map((s) => (
                  <Table.Row key={s.id}>
                    <Table.Cell>{s.name}</Table.Cell>
                    <Table.Cell>{groups.find((g) => g.id === s.group_id)?.name}</Table.Cell>
                    <Table.Cell>{s.description}</Table.Cell>
                    <Table.Cell>
                      <div className="flex space-x-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={<Edit className="w-4 h-4" />}
                          onClick={() => openEdit(s)}
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-red-600 hover:text-red-700"
                          icon={<Trash2 className="w-4 h-4" />}
                          onClick={() => handleDelete(s.id)}
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
        title={editing ? 'Editar Subgrupo' : 'Novo Subgrupo'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Grupo
            </label>
            <select
              className="input w-full"
              value={formData.group_id}
              onChange={(e) => setFormData({ ...formData, group_id: e.target.value })}
            >
              <option value="">Selecione um grupo</option>
              {groups.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.name}
                </option>
              ))}
            </select>
          </div>
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

export default function Subgroups() {
  return (
    <ProtectedRoute>
      <SubgroupsContent />
    </ProtectedRoute>
  );
}

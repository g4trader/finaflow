import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import Layout from '../components/layout/Layout';
import api from '../services/api';
import { Wallet, Plus, Edit2, Trash2, DollarSign } from 'lucide-react';

interface Caixa {
  id: string;
  nome: string;
  descricao: string;
  saldo_inicial: number;
  saldo_atual: number;
  created_at: string;
}

export default function CaixaPage() {
  const { user } = useAuth();
  const [caixas, setCaixas] = useState<Caixa[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingCaixa, setEditingCaixa] = useState<Caixa | null>(null);
  
  const [formData, setFormData] = useState({
    nome: '',
    descricao: '',
    saldo_inicial: 0
  });

  useEffect(() => {
    fetchCaixas();
  }, []);

  const fetchCaixas = async () => {
    try {
      setLoading(true);
      const response = await api.get('/caixa');
      if (response.data.success) {
        setCaixas(response.data.caixas);
      }
    } catch (error) {
      console.error('Erro ao carregar caixas:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      if (editingCaixa) {
        await api.put(`/caixa/${editingCaixa.id}`, formData);
      } else {
        await api.post('/caixa', formData);
      }
      
      setShowModal(false);
      setEditingCaixa(null);
      setFormData({
        nome: '',
        descricao: '',
        saldo_inicial: 0
      });
      fetchCaixas();
    } catch (error) {
      console.error('Erro ao salvar caixa:', error);
      alert('Erro ao salvar caixa');
    }
  };

  const handleEdit = (caixa: Caixa) => {
    setEditingCaixa(caixa);
    setFormData({
      nome: caixa.nome,
      descricao: caixa.descricao || '',
      saldo_inicial: caixa.saldo_inicial
    });
    setShowModal(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Deseja realmente remover este caixa?')) return;
    
    try {
      await api.delete(`/caixa/${id}`);
      fetchCaixas();
    } catch (error) {
      console.error('Erro ao remover caixa:', error);
      alert('Erro ao remover caixa');
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const totalSaldo = caixas.reduce((acc, caixa) => acc + caixa.saldo_atual, 0);

  return (
    <Layout>
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Wallet className="w-6 h-6" />
              Caixa / Dinheiro
            </h1>
            <p className="text-gray-600 mt-1">Gerencie seus caixas e dinheiro físico</p>
          </div>
          <button
            onClick={() => {
              setEditingCaixa(null);
              setFormData({
                nome: '',
                descricao: '',
                saldo_inicial: 0
              });
              setShowModal(true);
            }}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Novo Caixa
          </button>
        </div>

        {/* Card de Saldo Total */}
        <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-6 mb-6 text-white">
          <div className="flex items-center gap-3">
            <DollarSign className="w-8 h-8" />
            <div>
              <p className="text-green-100 text-sm">Total em Caixa / Dinheiro</p>
              <p className="text-3xl font-bold">{formatCurrency(totalSaldo)}</p>
            </div>
          </div>
        </div>

        {/* Lista de Caixas */}
        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Carregando caixas...</p>
          </div>
        ) : caixas.length === 0 ? (
          <div className="bg-white rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
            <Wallet className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Nenhum caixa cadastrado
            </h3>
            <p className="text-gray-600 mb-4">
              Comece adicionando seu primeiro caixa
            </p>
            <button
              onClick={() => setShowModal(true)}
              className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700"
            >
              Adicionar Caixa
            </button>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {caixas.map((caixa) => (
              <div key={caixa.id} className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-lg transition-shadow">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="font-semibold text-lg text-gray-900">{caixa.nome}</h3>
                    {caixa.descricao && (
                      <p className="text-sm text-gray-500 mt-1">{caixa.descricao}</p>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleEdit(caixa)}
                      className="p-2 text-green-600 hover:bg-green-50 rounded"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(caixa.id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                
                <div className="border-t pt-3 mt-3">
                  <p className="text-sm text-gray-600">Saldo Atual</p>
                  <p className="text-2xl font-bold text-green-600">
                    {formatCurrency(caixa.saldo_atual)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Modal */}
        {showModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
              <h2 className="text-xl font-bold mb-4">
                {editingCaixa ? 'Editar Caixa' : 'Novo Caixa'}
              </h2>
              
              <form onSubmit={handleSubmit}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Nome *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.nome}
                      onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                      placeholder="Ex: Caixa Principal, Caixa Filial"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Descrição
                    </label>
                    <textarea
                      value={formData.descricao}
                      onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                      rows={3}
                      placeholder="Descrição opcional"
                    />
                  </div>

                  {!editingCaixa && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Saldo Inicial
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        value={formData.saldo_inicial}
                        onChange={(e) => setFormData({ ...formData, saldo_inicial: parseFloat(e.target.value) || 0 })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                        placeholder="0.00"
                      />
                    </div>
                  )}
                </div>

                <div className="flex gap-3 mt-6">
                  <button
                    type="button"
                    onClick={() => {
                      setShowModal(false);
                      setEditingCaixa(null);
                    }}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  >
                    {editingCaixa ? 'Atualizar' : 'Criar'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}


import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import Layout from '../components/layout/Layout';
import api from '../services/api';
import { Building2, Plus, Edit2, Trash2, DollarSign } from 'lucide-react';

interface ContaBancaria {
  id: string;
  banco: string;
  agencia: string;
  numero_conta: string;
  tipo: string;
  saldo_inicial: number;
  saldo_atual: number;
  created_at: string;
}

export default function ContasBancarias() {
  const { user } = useAuth();
  const [contas, setContas] = useState<ContaBancaria[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingConta, setEditingConta] = useState<ContaBancaria | null>(null);
  
  const [formData, setFormData] = useState({
    banco: '',
    agencia: '',
    numero_conta: '',
    tipo: 'corrente',
    saldo_inicial: 0
  });

  useEffect(() => {
    fetchContas();
  }, []);

  const fetchContas = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/v1/contas-bancarias');
      if (response.data.success) {
        setContas(response.data.contas);
      }
    } catch (error) {
      console.error('Erro ao carregar contas:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      if (editingConta) {
        await api.put(`/api/v1/contas-bancarias/${editingConta.id}`, formData);
      } else {
        await api.post('/api/v1/contas-bancarias', formData);
      }
      
      setShowModal(false);
      setEditingConta(null);
      setFormData({
        banco: '',
        agencia: '',
        numero_conta: '',
        tipo: 'corrente',
        saldo_inicial: 0
      });
      fetchContas();
    } catch (error) {
      console.error('Erro ao salvar conta:', error);
      alert('Erro ao salvar conta bancária');
    }
  };

  const handleEdit = (conta: ContaBancaria) => {
    setEditingConta(conta);
    setFormData({
      banco: conta.banco,
      agencia: conta.agencia || '',
      numero_conta: conta.numero_conta || '',
      tipo: conta.tipo,
      saldo_inicial: conta.saldo_inicial
    });
    setShowModal(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Deseja realmente remover esta conta?')) return;
    
    try {
      await api.delete(`/api/v1/contas-bancarias/${id}`);
      fetchContas();
    } catch (error) {
      console.error('Erro ao remover conta:', error);
      alert('Erro ao remover conta bancária');
    }
  };

  const getTipoLabel = (tipo: string) => {
    const tipos: Record<string, string> = {
      corrente: 'Corrente',
      poupanca: 'Poupança',
      investimento: 'Investimento',
      outro: 'Outro'
    };
    return tipos[tipo] || tipo;
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const totalSaldo = contas.reduce((acc, conta) => acc + conta.saldo_atual, 0);

  return (
    <Layout>
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Building2 className="w-6 h-6" />
              Contas Bancárias
            </h1>
            <p className="text-gray-600 mt-1">Gerencie suas contas bancárias</p>
          </div>
          <button
            onClick={() => {
              setEditingConta(null);
              setFormData({
                banco: '',
                agencia: '',
                numero_conta: '',
                tipo: 'corrente',
                saldo_inicial: 0
              });
              setShowModal(true);
            }}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Nova Conta
          </button>
        </div>

        {/* Card de Saldo Total */}
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-6 mb-6 text-white">
          <div className="flex items-center gap-3">
            <DollarSign className="w-8 h-8" />
            <div>
              <p className="text-blue-100 text-sm">Saldo Total em Contas</p>
              <p className="text-3xl font-bold">{formatCurrency(totalSaldo)}</p>
            </div>
          </div>
        </div>

        {/* Lista de Contas */}
        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Carregando contas...</p>
          </div>
        ) : contas.length === 0 ? (
          <div className="bg-white rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
            <Building2 className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Nenhuma conta bancária cadastrada
            </h3>
            <p className="text-gray-600 mb-4">
              Comece adicionando sua primeira conta bancária
            </p>
            <button
              onClick={() => setShowModal(true)}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
            >
              Adicionar Conta
            </button>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {contas.map((conta) => (
              <div key={conta.id} className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-lg transition-shadow">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="font-semibold text-lg text-gray-900">{conta.banco}</h3>
                    <span className="text-sm text-gray-500">{getTipoLabel(conta.tipo)}</span>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleEdit(conta)}
                      className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(conta.id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                
                {conta.agencia && (
                  <p className="text-sm text-gray-600 mb-1">
                    Agência: <span className="font-medium">{conta.agencia}</span>
                  </p>
                )}
                {conta.numero_conta && (
                  <p className="text-sm text-gray-600 mb-3">
                    Conta: <span className="font-medium">{conta.numero_conta}</span>
                  </p>
                )}
                
                <div className="border-t pt-3 mt-3">
                  <p className="text-sm text-gray-600">Saldo Atual</p>
                  <p className="text-2xl font-bold text-green-600">
                    {formatCurrency(conta.saldo_atual)}
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
                {editingConta ? 'Editar Conta' : 'Nova Conta Bancária'}
              </h2>
              
              <form onSubmit={handleSubmit}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Banco *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.banco}
                      onChange={(e) => setFormData({ ...formData, banco: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Ex: Banco do Brasil, CEF, SICOOB"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Agência
                      </label>
                      <input
                        type="text"
                        value={formData.agencia}
                        onChange={(e) => setFormData({ ...formData, agencia: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="0001"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Número da Conta
                      </label>
                      <input
                        type="text"
                        value={formData.numero_conta}
                        onChange={(e) => setFormData({ ...formData, numero_conta: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="12345-6"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tipo *
                    </label>
                    <select
                      required
                      value={formData.tipo}
                      onChange={(e) => setFormData({ ...formData, tipo: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="corrente">Corrente</option>
                      <option value="poupanca">Poupança</option>
                      <option value="investimento">Investimento</option>
                      <option value="outro">Outro</option>
                    </select>
                  </div>

                  {!editingConta && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Saldo Inicial
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        value={formData.saldo_inicial}
                        onChange={(e) => setFormData({ ...formData, saldo_inicial: parseFloat(e.target.value) || 0 })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                      setEditingConta(null);
                    }}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    {editingConta ? 'Atualizar' : 'Criar'}
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


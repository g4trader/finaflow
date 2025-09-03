import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import Layout from '../components/layout/Layout';
import { 
  Upload, 
  FileText, 
  Plus, 
  Edit, 
  Trash2, 
  Calendar,
  DollarSign,
  ArrowUpRight,
  ArrowDownRight,
  X,
  Receipt
} from 'lucide-react';

interface FinancialTransaction {
  id: string;
  reference: string;
  description: string;
  amount: number;
  transaction_date: string;
  transaction_type: string;
  status: string;
  chart_account_id: string;
  chart_account_name: string;
  chart_account_code: string;
  business_unit_id: string;
  business_unit_name: string;
  created_by: string;
  approved_by?: string;
  is_active: boolean;
  notes?: string;
  created_at: string;
  updated_at: string;
  approved_at?: string;
}

interface ChartAccount {
  id: string;
  name: string;
  code: string;
  subgroup_id: string;
}

const Transactions: React.FC = () => {
  const { user } = useAuth();
  const [transactions, setTransactions] = useState<FinancialTransaction[]>([]);
  const [chartAccounts, setChartAccounts] = useState<ChartAccount[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingTransaction, setEditingTransaction] = useState<FinancialTransaction | null>(null);
  const [formData, setFormData] = useState({
    chart_account_id: '',
    transaction_date: '',
    amount: '',
    description: '',
    transaction_type: 'receita',
    notes: ''
  });

  useEffect(() => {
    if (user?.business_unit_id) {
      loadTransactions(user.business_unit_id);
      loadChartAccounts(user.business_unit_id);
    }
  }, [user]);

  const loadTransactions = async (buId: string) => {
    setLoading(true);
    try {
      const response = await api.get(`/api/v1/financial/transactions?business_unit_id=${buId}`);
      setTransactions(response.data);
    } catch (error) {
      console.error('Erro ao carregar transações:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadChartAccounts = async (buId: string) => {
    try {
      const response = await api.get(`/api/v1/chart-accounts/hierarchy?business_unit_id=${buId}`);
      const accounts = response.data.accounts || [];
      setChartAccounts(accounts);
    } catch (error) {
      console.error('Erro ao carregar contas:', error);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type === 'text/csv') {
      setSelectedFile(file);
    } else {
      alert('Por favor, selecione um arquivo CSV válido.');
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !user?.business_unit_id) return;

    setUploading(true);
    setUploadProgress(0);

    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 90) {
          clearInterval(interval);
          return 90;
        }
        return prev + 10;
      });
    }, 100);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('business_unit_id', user.business_unit_id);

    try {
      const response = await api.post('/api/v1/financial/transactions/import-csv', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(progress);
          }
        },
      });

      setUploadProgress(100);
      setUploadResult(response.data);
      if (response.data.summary.processed > 0) {
        loadTransactions(user.business_unit_id);
      }
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Erro ao importar arquivo');
    } finally {
      setUploading(false);
      setUploadProgress(0);
      setTimeout(() => {
        setShowUploadModal(false);
        setSelectedFile(null);
        setUploadResult(null);
      }, 2000);
    }
  };

  const handleCreateTransaction = async () => {
    if (!user?.business_unit_id || !formData.chart_account_id || !formData.transaction_date || !formData.amount) {
      alert('Por favor, preencha todos os campos obrigatórios.');
      return;
    }

    try {
      await api.post('/api/v1/financial/transactions', {
        ...formData,
        business_unit_id: user.business_unit_id,
        amount: parseFloat(formData.amount)
      });

      setShowCreateModal(false);
      setFormData({
        chart_account_id: '',
        transaction_date: '',
        amount: '',
        description: '',
        transaction_type: 'receita',
        notes: ''
      });
      loadTransactions(user.business_unit_id);
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Erro ao criar transação');
    }
  };

  const handleUpdateTransaction = async () => {
    if (!editingTransaction || !formData.chart_account_id || !formData.transaction_date || !formData.amount) {
      return;
    }

    try {
      await api.post(`/api/v1/financial/transactions/${editingTransaction.id}`, {
        ...formData,
        amount: parseFloat(formData.amount)
      });

      setShowCreateModal(false);
      setEditingTransaction(null);
      setFormData({
        chart_account_id: '',
        transaction_date: '',
        amount: '',
        description: '',
        transaction_type: 'receita',
        notes: ''
      });
      loadTransactions(user.business_unit_id);
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Erro ao atualizar transação');
    }
  };

  const handleDeleteTransaction = async (id: string) => {
    if (!confirm('Tem certeza que deseja excluir esta transação?')) return;

    try {
      await api.delete(`/api/v1/financial/transactions/${id}`);
      loadTransactions(user.business_unit_id);
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Erro ao excluir transação');
    }
  };

  const handleEditTransaction = (transaction: FinancialTransaction) => {
    setEditingTransaction(transaction);
    setFormData({
      chart_account_id: transaction.chart_account_id,
      transaction_date: transaction.transaction_date.split(' ')[0],
      amount: transaction.amount.toString(),
      description: transaction.description,
      transaction_type: transaction.transaction_type,
      notes: transaction.notes || ''
    });
    setShowCreateModal(true);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(amount);
  };

  const getTransactionTypeIcon = (type: string) => {
    return type === 'receita' ? (
      <ArrowUpRight className="w-4 h-4 text-green-600" />
    ) : (
      <ArrowDownRight className="w-4 h-4 text-red-600" />
    );
  };

  const getTransactionTypeColor = (type: string) => {
    return type === 'receita' ? 'text-green-600' : 'text-red-600';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'aprovada':
        return 'text-green-600';
      case 'pendente':
        return 'text-yellow-600';
      case 'rejeitada':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <Layout>
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Transações Financeiras</h1>
                <p className="text-gray-600 mt-1">
                  Gerencie as transações financeiras da sua unidade de negócio
                </p>
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={() => setShowUploadModal(true)}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  Importar CSV
                </button>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Nova Transação
                </button>
              </div>
            </div>
          </div>

          {/* Transactions List */}
          {user?.business_unit_id && (
            <div className="bg-white rounded-lg shadow-sm">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">
                  Transações ({transactions.length})
                </h3>
              </div>
              
              {loading ? (
                <div className="p-6 text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">Carregando transações...</p>
                </div>
              ) : transactions.length === 0 ? (
                <div className="p-6 text-center">
                  <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">Nenhuma transação encontrada</p>
                  <p className="text-gray-500 text-sm mt-1">
                    Comece criando uma nova transação ou importando um arquivo CSV
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Referência
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Conta
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Descrição
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Data
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Valor
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Tipo
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Ações
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {transactions.map((transaction) => (
                        <tr key={transaction.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">
                              {transaction.reference}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div>
                              <div className="text-sm font-medium text-gray-900">
                                {transaction.chart_account_name}
                              </div>
                              <div className="text-sm text-gray-500">
                                {transaction.chart_account_code}
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <div className="text-sm text-gray-900 max-w-xs truncate">
                              {transaction.description}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatDate(transaction.transaction_date)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className={`text-sm font-medium ${getTransactionTypeColor(transaction.transaction_type)}`}>
                              {formatCurrency(transaction.amount)}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              {getTransactionTypeIcon(transaction.transaction_type)}
                              <span className={`ml-1 text-sm font-medium ${getTransactionTypeColor(transaction.transaction_type)}`}>
                                {transaction.transaction_type === 'receita' ? 'Receita' : 'Despesa'}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(transaction.status)}`}>
                              {transaction.status.charAt(0).toUpperCase() + transaction.status.slice(1)}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <div className="flex space-x-2">
                              <button
                                onClick={() => handleEditTransaction(transaction)}
                                className="text-blue-600 hover:text-blue-900"
                              >
                                <Edit className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleDeleteTransaction(transaction.id)}
                                className="text-red-600 hover:text-red-900"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Upload Modal */}
          {showUploadModal && (
            <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
              <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
                <div className="mt-3">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium text-gray-900">Importar Transações CSV</h3>
                    <button
                      onClick={() => setShowUploadModal(false)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <X className="w-6 h-6" />
                    </button>
                  </div>
                  
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Selecionar Arquivo CSV
                    </label>
                    <input
                      type="file"
                      accept=".csv"
                      onChange={handleFileSelect}
                      className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                    />
                  </div>

                  {selectedFile && (
                    <div className="mb-4 p-3 bg-blue-50 rounded-md">
                      <p className="text-sm text-blue-800">
                        Arquivo selecionado: {selectedFile.name}
                      </p>
                    </div>
                  )}

                  {uploading && (
                    <div className="mb-4">
                      <div className="w-full bg-gray-200 rounded-full h-2.5">
                        <div
                          className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                          style={{ width: `${uploadProgress}%` }}
                        ></div>
                      </div>
                      <p className="text-sm text-gray-600 mt-2">
                        Importando... {uploadProgress}%
                      </p>
                    </div>
                  )}

                  {uploadResult && (
                    <div className="mb-4 p-3 bg-green-50 rounded-md">
                      <div className="text-sm text-green-800">
                        {uploadResult.message}
                      </div>
                      <div className="text-sm text-green-700 mt-1">
                        Processadas: {uploadResult.summary.processed} | 
                        Erros: {uploadResult.summary.errors}
                      </div>
                    </div>
                  )}

                  <div className="flex justify-end space-x-3">
                    <button
                      onClick={() => setShowUploadModal(false)}
                      className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
                    >
                      Cancelar
                    </button>
                    <button
                      onClick={handleUpload}
                      disabled={!selectedFile || uploading}
                      className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 rounded-md"
                    >
                      {uploading ? 'Importando...' : 'Importar'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Create/Edit Modal */}
          {showCreateModal && (
            <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
              <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
                <div className="mt-3">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium text-gray-900">
                      {editingTransaction ? 'Editar Transação' : 'Nova Transação'}
                    </h3>
                    <button
                      onClick={() => {
                        setShowCreateModal(false);
                        setEditingTransaction(null);
                        setFormData({
                          chart_account_id: '',
                          transaction_date: '',
                          amount: '',
                          description: '',
                          transaction_type: 'receita',
                          notes: ''
                        });
                      }}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <X className="w-6 h-6" />
                    </button>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Conta Contábil *
                      </label>
                      <select
                        value={formData.chart_account_id}
                        onChange={(e) => setFormData({...formData, chart_account_id: e.target.value})}
                        className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="">Selecione uma conta</option>
                        {chartAccounts.map((account) => (
                          <option key={account.id} value={account.id}>
                            {account.code} - {account.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="label className="block text-sm font-medium text-gray-700 mb-1">
                        Data *
                      </label>
                      <input
                        type="date"
                        value={formData.transaction_date}
                        onChange={(e) => setFormData({...formData, transaction_date: e.target.value})}
                        className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Valor *
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        value={formData.amount}
                        onChange={(e) => setFormData({...formData, amount: e.target.value})}
                        className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        placeholder="0.00"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Descrição *
                      </label>
                      <textarea
                        value={formData.description}
                        onChange={(e) => setFormData({...formData, description: e.target.value})}
                        rows={3}
                        className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        placeholder="Descrição da transação..."
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Tipo
                      </label>
                      <select
                        value={formData.transaction_type}
                        onChange={(e) => setFormData({...formData, transaction_type: e.target.value})}
                        className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="receita">Receita</option>
                        <option value="despesa">Despesa</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Observações
                      </label>
                      <textarea
                        value={formData.notes}
                        onChange={(e) => setFormData({...formData, notes: e.target.value})}
                        rows={2}
                        className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        placeholder="Observações adicionais..."
                      />
                    </div>
                  </div>

                  <div className="flex justify-end space-x-3 mt-6">
                    <button
                      onClick={() => {
                        setShowCreateModal(false);
                        setEditingTransaction(null);
                        setFormData({
                          chart_account_id: '',
                          transaction_date: '',
                          amount: '',
                          description: '',
                          transaction_type: 'receita',
                          notes: ''
                        });
                      }}
                      className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
                    >
                      Cancelar
                    </button>
                    <button
                      onClick={editingTransaction ? handleUpdateTransaction : handleCreateTransaction}
                      className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md"
                    >
                      {editingTransaction ? 'Atualizar' : 'Criar'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
};

export default Transactions;

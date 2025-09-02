import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { 
  Upload, 
  FileText, 
  Plus, 
  Edit, 
  Trash2, 
  Download, 
  Calendar,
  DollarSign,
  Building,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  X
} from 'lucide-react';

interface FinancialForecast {
  id: string;
  business_unit_id: string;
  business_unit_name: string;
  chart_account_id: string;
  chart_account_name: string;
  chart_account_code: string;
  forecast_date: string;
  amount: number;
  description?: string;
  forecast_type: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface BusinessUnit {
  id: string;
  name: string;
  tenant_id: string;
}

interface ChartAccount {
  id: string;
  name: string;
  code: string;
  subgroup_id: string;
}

const FinancialForecasts: React.FC = () => {
  const { user } = useAuth();
  const [forecasts, setForecasts] = useState<FinancialForecast[]>([]);
  const [businessUnits, setBusinessUnits] = useState<BusinessUnit[]>([]);
  const [chartAccounts, setChartAccounts] = useState<ChartAccount[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingForecast, setEditingForecast] = useState<FinancialForecast | null>(null);
  const [formData, setFormData] = useState({
    chart_account_id: '',
    forecast_date: '',
    amount: '',
    description: '',
    forecast_type: 'monthly'
  });

  useEffect(() => {
    if (user?.business_unit_id) {
      loadForecasts(user.business_unit_id);
      loadChartAccounts(user.business_unit_id);
    }
  }, [user]);



  const loadBusinessUnits = async () => {
    try {
      const response = await api.get('/api/v1/auth/user-business-units');
      setBusinessUnits(response.data);
    } catch (error) {
      console.error('Erro ao carregar BUs:', error);
    }
  };

  const loadForecasts = async (buId: string) => {
    setLoading(true);
    try {
      const response = await api.get(`/financial/forecasts?business_unit_id=${buId}`);
      setForecasts(response.data);
    } catch (error) {
      console.error('Erro ao carregar previsões:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadChartAccounts = async (buId: string) => {
    try {
      const response = await api.get(`/chart-accounts/hierarchy?business_unit_id=${buId}`);
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
    setUploadResult(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('business_unit_id', user.business_unit_id);

    try {
      const response = await api.post('/financial/forecasts/import-csv', formData, {
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

      setUploadResult(response.data);
      if (response.data.summary.processed > 0) {
        loadForecasts(user.business_unit_id);
      }
    } catch (error: any) {
      setUploadResult({
        error: true,
        message: error.response?.data?.detail || 'Erro ao fazer upload do arquivo'
      });
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleCreateForecast = async () => {
    if (!selectedBusinessUnit || !formData.chart_account_id || !formData.forecast_date || !formData.amount) {
      alert('Por favor, preencha todos os campos obrigatórios.');
      return;
    }

    try {
      await api.post('/financial/forecasts', {
        ...formData,
        business_unit_id: selectedBusinessUnit,
        amount: parseFloat(formData.amount)
      });

      setShowCreateModal(false);
      setFormData({
        chart_account_id: '',
        forecast_date: '',
        amount: '',
        description: '',
        forecast_type: 'monthly'
      });
      loadForecasts(selectedBusinessUnit);
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Erro ao criar previsão');
    }
  };

  const handleUpdateForecast = async () => {
    if (!editingForecast) return;

    try {
      await api.put(`/financial/forecasts/${editingForecast.id}`, {
        ...formData,
        amount: parseFloat(formData.amount)
      });

      setEditingForecast(null);
      setFormData({
        chart_account_id: '',
        forecast_date: '',
        amount: '',
        description: '',
        forecast_type: 'monthly'
      });
      loadForecasts(selectedBusinessUnit);
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Erro ao atualizar previsão');
    }
  };

  const handleDeleteForecast = async (id: string) => {
    if (!confirm('Tem certeza que deseja excluir esta previsão?')) return;

    try {
      await api.delete(`/financial/forecasts/${id}`);
      loadForecasts(selectedBusinessUnit);
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Erro ao excluir previsão');
    }
  };

  const handleEdit = (forecast: FinancialForecast) => {
    setEditingForecast(forecast);
    setFormData({
      chart_account_id: forecast.chart_account_id,
      forecast_date: forecast.forecast_date,
      amount: forecast.amount.toString(),
      description: forecast.description || '',
      forecast_type: forecast.forecast_type
    });
    setShowCreateModal(true);
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Previsões Financeiras</h1>
              <p className="text-gray-600 mt-1">
                Gerencie as previsões financeiras da sua unidade de negócio
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
                Nova Previsão
              </button>
            </div>
          </div>
        </div>

        {/* Business Unit Selector */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Unidade de Negócio
          </label>
          <select
            value={selectedBusinessUnit}
            onChange={(e) => {
              setSelectedBusinessUnit(e.target.value);
              if (e.target.value) {
                loadForecasts(e.target.value);
                loadChartAccounts(e.target.value);
              }
            }}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Selecione uma BU</option>
            {businessUnits.map((bu) => (
              <option key={bu.id} value={bu.id}>
                {bu.name}
              </option>
            ))}
          </select>
        </div>

        {/* Forecasts List */}
        {selectedBusinessUnit && (
          <div className="bg-white rounded-lg shadow-sm">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">
                Previsões ({forecasts.length})
              </h3>
            </div>
            
            {loading ? (
              <div className="p-6 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-2 text-gray-600">Carregando previsões...</p>
              </div>
            ) : forecasts.length === 0 ? (
              <div className="p-6 text-center">
                <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">Nenhuma previsão encontrada</p>
                <p className="text-gray-500 text-sm mt-1">
                  Comece criando uma nova previsão ou importando um arquivo CSV
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Conta
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
                    {forecasts.map((forecast) => (
                      <tr key={forecast.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {forecast.chart_account_name}
                            </div>
                            <div className="text-sm text-gray-500">
                              {forecast.chart_account_code}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatDate(forecast.forecast_date)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">
                          {formatCurrency(forecast.amount)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {forecast.forecast_type}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            forecast.is_active 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {forecast.is_active ? 'Ativa' : 'Inativa'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <div className="flex space-x-2">
                            <button
                              onClick={() => handleEdit(forecast)}
                              className="text-blue-600 hover:text-blue-900"
                            >
                              <Edit className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDeleteForecast(forecast.id)}
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
                  <h3 className="text-lg font-medium text-gray-900">Importar Previsões CSV</h3>
                  <button
                    onClick={() => setShowUploadModal(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
                
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Selecionar arquivo CSV
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
                    <div className="flex items-center">
                      <FileText className="w-4 h-4 text-blue-600 mr-2" />
                      <span className="text-sm text-blue-800">{selectedFile.name}</span>
                    </div>
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
                    <p className="text-sm text-gray-600 mt-1">
                      Enviando arquivo... {uploadProgress}%
                    </p>
                  </div>
                )}

                {uploadResult && (
                  <div className={`mb-4 p-3 rounded-md ${
                    uploadResult.error 
                      ? 'bg-red-50 text-red-800' 
                      : 'bg-green-50 text-green-800'
                  }`}>
                    <div className="flex items-center">
                      {uploadResult.error ? (
                        <AlertCircle className="w-4 h-4 mr-2" />
                      ) : (
                        <CheckCircle className="w-4 h-4 mr-2" />
                      )}
                      <span className="text-sm">{uploadResult.message}</span>
                    </div>
                    {!uploadResult.error && uploadResult.summary && (
                      <div className="mt-2 text-sm">
                        <p>Processadas: {uploadResult.summary.processed}</p>
                        <p>Erros: {uploadResult.summary.errors}</p>
                        <p>Total: {uploadResult.summary.total_rows}</p>
                      </div>
                    )}
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
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-md"
                  >
                    {uploading ? 'Enviando...' : 'Importar'}
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
                    {editingForecast ? 'Editar Previsão' : 'Nova Previsão'}
                  </h3>
                  <button
                    onClick={() => {
                      setShowCreateModal(false);
                      setEditingForecast(null);
                      setFormData({
                        chart_account_id: '',
                        forecast_date: '',
                        amount: '',
                        description: '',
                        forecast_type: 'monthly'
                      });
                    }}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Conta *
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
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Data *
                    </label>
                    <input
                      type="date"
                      value={formData.forecast_date}
                      onChange={(e) => setFormData({...formData, forecast_date: e.target.value})}
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
                      Descrição
                    </label>
                    <textarea
                      value={formData.description}
                      onChange={(e) => setFormData({...formData, description: e.target.value})}
                      rows={3}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Descrição da previsão..."
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tipo
                    </label>
                    <select
                      value={formData.forecast_type}
                      onChange={(e) => setFormData({...formData, forecast_type: e.target.value})}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="monthly">Mensal</option>
                      <option value="quarterly">Trimestral</option>
                      <option value="yearly">Anual</option>
                    </select>
                  </div>
                </div>

                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    onClick={() => {
                      setShowCreateModal(false);
                      setEditingForecast(null);
                      setFormData({
                        chart_account_id: '',
                        forecast_date: '',
                        amount: '',
                        description: '',
                        forecast_type: 'monthly'
                      });
                    }}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={editingForecast ? handleUpdateForecast : handleCreateForecast}
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md"
                  >
                    {editingForecast ? 'Atualizar' : 'Criar'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FinancialForecasts;

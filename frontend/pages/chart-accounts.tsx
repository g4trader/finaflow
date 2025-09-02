import React, { useState, useEffect } from 'react';
import { 
  PlusIcon, 
  Upload, 
  ChevronDown, 
  ChevronRight,
  Eye,
  Pencil,
  Trash2
} from 'lucide-react';
import { 
  getChartAccountsHierarchy, 
  importChartAccounts 
} from '../services/api';

interface ChartAccountGroup {
  id: string;
  code: string;
  name: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface ChartAccountSubgroup {
  id: string;
  code: string;
  name: string;
  description?: string;
  group_id: string;
  group_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface ChartAccount {
  id: string;
  code: string;
  name: string;
  description?: string;
  subgroup_id: string;
  subgroup_name: string;
  group_id: string;
  group_name: string;
  account_type: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface ChartAccountsHierarchy {
  groups: ChartAccountGroup[];
  subgroups: ChartAccountSubgroup[];
  accounts: ChartAccount[];
}

const ChartAccountsPage: React.FC = () => {
  const [hierarchy, setHierarchy] = useState<ChartAccountsHierarchy | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [expandedSubgroups, setExpandedSubgroups] = useState<Set<string>>(new Set());
  const [showImportModal, setShowImportModal] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<any>(null);

  useEffect(() => {
    loadChartAccounts();
  }, []);

  const loadChartAccounts = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getChartAccountsHierarchy();
      setHierarchy(data);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar plano de contas');
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async () => {
    if (!importFile) return;

    try {
      setImporting(true);
      setError(null);
      const result = await importChartAccounts(importFile);
      setImportResult(result);
      
      if (result.success) {
        // Recarregar dados após importação
        await loadChartAccounts();
        setShowImportModal(false);
        setImportFile(null);
      }
    } catch (err: any) {
      setError(err.message || 'Erro ao importar arquivo');
    } finally {
      setImporting(false);
    }
  };

  const toggleGroup = (groupId: string) => {
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(groupId)) {
      newExpanded.delete(groupId);
    } else {
      newExpanded.add(groupId);
    }
    setExpandedGroups(newExpanded);
  };

  const toggleSubgroup = (subgroupId: string) => {
    const newExpanded = new Set(expandedSubgroups);
    if (newExpanded.has(subgroupId)) {
      newExpanded.delete(subgroupId);
    } else {
      newExpanded.add(subgroupId);
    }
    setExpandedSubgroups(newExpanded);
  };

  const getSubgroupsForGroup = (groupId: string) => {
    return hierarchy?.subgroups.filter(sg => sg.group_id === groupId) || [];
  };

  const getAccountsForSubgroup = (subgroupId: string) => {
    return hierarchy?.accounts.filter(acc => acc.subgroup_id === subgroupId) || [];
  };

  const getAccountTypeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'receita':
        return 'bg-green-100 text-green-800';
      case 'custo':
        return 'bg-red-100 text-red-800';
      case 'despesa':
        return 'bg-orange-100 text-orange-800';
      case 'investimento':
        return 'bg-blue-100 text-blue-800';
      case 'movimentação':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Carregando plano de contas...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-4">❌ Erro</div>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={loadChartAccounts}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Tentar Novamente
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Plano de Contas</h1>
              <p className="text-gray-600">Gerencie a estrutura contábil da empresa</p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => setShowImportModal(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2"
              >
                <Upload className="h-5 w-5" />
                <span>Importar CSV</span>
              </button>
              <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center space-x-2">
                <PlusIcon className="h-5 w-5" />
                <span>Nova Conta</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-2xl font-bold text-blue-600">{hierarchy?.groups.length || 0}</div>
            <div className="text-gray-600">Grupos</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-2xl font-bold text-green-600">{hierarchy?.subgroups.length || 0}</div>
            <div className="text-gray-600">Subgrupos</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-2xl font-bold text-purple-600">{hierarchy?.accounts.length || 0}</div>
            <div className="text-gray-600">Contas</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-2xl font-bold text-orange-600">
              {hierarchy?.groups.filter(g => g.is_active).length || 0}
            </div>
            <div className="text-gray-600">Ativos</div>
          </div>
        </div>

        {/* Chart of Accounts Tree */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Estrutura Hierárquica</h2>
          </div>
          <div className="p-6">
            {hierarchy?.groups.map((group) => (
              <div key={group.id} className="mb-4">
                {/* Group Header */}
                <div 
                  className="flex items-center p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100"
                  onClick={() => toggleGroup(group.id)}
                >
                  {expandedGroups.has(group.id) ? (
                    <ChevronDown className="h-5 w-5 text-gray-500 mr-3" />
                  ) : (
                    <ChevronRight className="h-5 w-5 text-gray-500 mr-3" />
                  )}
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <span className="font-medium text-gray-900">{group.name}</span>
                      <span className="text-sm text-gray-500">({group.code})</span>
                      {!group.is_active && (
                        <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded">Inativo</span>
                      )}
                    </div>
                    {group.description && (
                      <p className="text-sm text-gray-600 mt-1">{group.description}</p>
                    )}
                  </div>
                </div>

                {/* Subgroups */}
                {expandedGroups.has(group.id) && (
                  <div className="ml-8 mt-2 space-y-2">
                    {getSubgroupsForGroup(group.id).map((subgroup) => (
                      <div key={subgroup.id}>
                        {/* Subgroup Header */}
                        <div 
                          className="flex items-center p-3 bg-blue-50 rounded-lg cursor-pointer hover:bg-blue-100"
                          onClick={() => toggleSubgroup(subgroup.id)}
                        >
                          {expandedSubgroups.has(subgroup.id) ? (
                            <ChevronDown className="h-5 w-5 text-blue-500 mr-3" />
                          ) : (
                                                          <ChevronRight className="h-5 w-5 text-blue-500 mr-3" />
                          )}
                          <div className="flex-1">
                            <div className="flex items-center space-x-3">
                              <span className="font-medium text-blue-900">{subgroup.name}</span>
                              <span className="text-sm text-blue-600">({subgroup.code})</span>
                              {!subgroup.is_active && (
                                <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded">Inativo</span>
                              )}
                            </div>
                            {subgroup.description && (
                              <p className="text-sm text-blue-700 mt-1">{subgroup.description}</p>
                            )}
                          </div>
                        </div>

                        {/* Accounts */}
                        {expandedSubgroups.has(subgroup.id) && (
                          <div className="ml-8 mt-2 space-y-2">
                            {getAccountsForSubgroup(subgroup.id).map((account) => (
                              <div key={account.id} className="flex items-center p-3 bg-white border border-gray-200 rounded-lg">
                                <div className="flex-1">
                                  <div className="flex items-center space-x-3">
                                    <span className="font-medium text-gray-900">{account.name}</span>
                                    <span className="text-sm text-gray-500">({account.code})</span>
                                    <span className={`px-2 py-1 text-xs rounded ${getAccountTypeColor(account.account_type)}`}>
                                      {account.account_type}
                                    </span>
                                    {!account.is_active && (
                                      <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded">Inativo</span>
                                    )}
                                  </div>
                                  {account.description && (
                                    <p className="text-sm text-gray-600 mt-1">{account.description}</p>
                                  )}
                                </div>
                                <div className="flex space-x-2">
                                                                  <button className="p-1 text-gray-400 hover:text-blue-600">
                                  <Eye className="h-4 w-4" />
                                </button>
                                <button className="p-1 text-gray-400 hover:text-green-600">
                                  <Pencil className="h-4 w-4" />
                                </button>
                                <button className="p-1 text-gray-400 hover:text-red-600">
                                  <Trash2 className="h-4 w-4" />
                                </button>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Importar Plano de Contas</h3>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Arquivo CSV
                </label>
                <input
                  type="file"
                  accept=".csv"
                  onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                  className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
              </div>

              {importResult && (
                <div className={`p-3 rounded mb-4 ${
                  importResult.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {importResult.message}
                  {importResult.summary && (
                    <div className="mt-2 text-sm">
                      <p>Grupos criados: {importResult.summary.groups_created}</p>
                      <p>Subgrupos criados: {importResult.summary.subgroups_created}</p>
                      <p>Contas criadas: {importResult.summary.accounts_created}</p>
                    </div>
                  )}
                </div>
              )}

              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => {
                    setShowImportModal(false);
                    setImportFile(null);
                    setImportResult(null);
                  }}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleImport}
                  disabled={!importFile || importing}
                  className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {importing ? 'Importando...' : 'Importar'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChartAccountsPage;

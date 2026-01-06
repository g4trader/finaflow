import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../../context/AuthContext';
import Layout from '../../components/layout/Layout';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import { CheckCircle, XCircle, AlertTriangle, TrendingUp, TrendingDown } from 'lucide-react';
import { getReconciliation } from '../../services/api';

interface ReconciliationData {
  tenant_id: string;
  business_unit_id: string;
  reconciliation_date: string;
  status: string;
  totals?: {
    revenue: { excel: number; system: number; diff: number };
    expense: { excel: number; system: number; diff: number };
    cost: { excel: number; system: number; diff: number };
    balance: { excel: number; system: number; diff: number };
  };
  monthly?: Array<{
    month: number;
    revenue?: { excel: number; system: number; diff: number };
    expense?: { excel: number; system: number; diff: number };
    cost?: { excel: number; system: number; diff: number };
    balance?: { excel: number; system: number; diff: number };
  }>;
  errors?: string[];
}

const ReconciliationPage: React.FC = () => {
  const { user, token } = useAuth();
  const router = useRouter();
  const { tenant_id, business_unit_id } = router.query;
  
  const [reconciliation, setReconciliation] = useState<ReconciliationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  useEffect(() => {
    if (tenant_id && business_unit_id) {
      loadReconciliation();
    }
  }, [tenant_id, business_unit_id]);
  
  const loadReconciliation = async () => {
    if (!tenant_id || !business_unit_id) return;
    
    setLoading(true);
    setError('');
    
    try {
      const data = await getReconciliation(String(tenant_id), String(business_unit_id), token || undefined);
      setReconciliation(data);
    } catch (err: any) {
      setError(err.message || 'Erro ao carregar conciliação');
    } finally {
      setLoading(false);
    }
  };
  
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };
  
  const getDiffColor = (diff: number) => {
    if (Math.abs(diff) < 0.01) return 'text-green-600';
    if (diff > 0) return 'text-red-600';
    return 'text-orange-600';
  };
  
  const getDiffIcon = (diff: number) => {
    if (Math.abs(diff) < 0.01) return <CheckCircle className="w-5 h-5 text-green-600" />;
    if (diff > 0) return <TrendingUp className="w-5 h-5 text-red-600" />;
    return <TrendingDown className="w-5 h-5 text-orange-600" />;
  };
  
  const monthNames = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
  
  if (user?.role !== 'super_admin') {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto py-8">
          <Card>
            <Card.Body>
              <div className="text-center py-12">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">Acesso Negado</h2>
                <p className="text-gray-600 mb-6">Apenas super administradores podem acessar esta página.</p>
                <Button onClick={() => router.push('/dashboard')}>Voltar ao Dashboard</Button>
              </div>
            </Card.Body>
          </Card>
        </div>
      </Layout>
    );
  }
  
  return (
    <Layout title="Conciliação de Dados">
      <div className="max-w-7xl mx-auto py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">📊 Conciliação de Dados</h1>
          <p className="text-gray-600">Comparação entre planilha e sistema</p>
        </div>
        
        {loading ? (
          <Card>
            <Card.Body>
              <div className="text-center py-12">
                <p className="text-gray-600">Carregando conciliação...</p>
              </div>
            </Card.Body>
          </Card>
        ) : error ? (
          <Card>
            <Card.Body>
              <div className="text-center py-12">
                <XCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
                <p className="text-red-600 mb-4">{error}</p>
                <Button onClick={loadReconciliation}>Tentar Novamente</Button>
              </div>
            </Card.Body>
          </Card>
        ) : reconciliation ? (
          <div className="space-y-6">
            {/* Totais Anuais */}
            {reconciliation.totals && (
              <Card>
                <Card.Body>
                  <h2 className="text-xl font-bold text-gray-900 mb-6">Totais Anuais</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {['revenue', 'expense', 'cost', 'balance'].map((key) => {
                      const data = reconciliation.totals![key as keyof typeof reconciliation.totals];
                      const labels: Record<string, string> = {
                        revenue: 'Receita',
                        expense: 'Despesa',
                        cost: 'Custo',
                        balance: 'Saldo'
                      };
                      
                      // Verificar se data é um objeto com excel, system, diff
                      if (typeof data === 'number' || !('excel' in data)) {
                        return null;
                      }
                      
                      return (
                        <div key={key} className="p-4 bg-gray-50 rounded-lg">
                          <h3 className="text-sm font-medium text-gray-700 mb-3">{labels[key]}</h3>
                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span className="text-gray-600">Planilha:</span>
                              <span className="font-medium">{formatCurrency(data.excel)}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-gray-600">Sistema:</span>
                              <span className="font-medium">{formatCurrency(data.system)}</span>
                            </div>
                            <div className="flex items-center justify-between pt-2 border-t border-gray-200">
                              <span className="text-sm font-medium">Diferença:</span>
                              <div className="flex items-center gap-2">
                                {getDiffIcon(data.diff)}
                                <span className={`text-sm font-bold ${getDiffColor(data.diff)}`}>
                                  {formatCurrency(data.diff)}
                                </span>
                              </div>
                            </div>
                            {Math.abs(data.diff) < 0.01 && (
                              <div className="flex items-center gap-1 text-xs text-green-600 mt-1">
                                <CheckCircle className="w-4 h-4" />
                                <span>Conciliação OK</span>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </Card.Body>
              </Card>
            )}
            
            {/* Totais Mensais */}
            {reconciliation.monthly && reconciliation.monthly.length > 0 && (
              <Card>
                <Card.Body>
                  <h2 className="text-xl font-bold text-gray-900 mb-6">Totais Mensais</h2>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Mês
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Receita
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Despesa
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Custo
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Saldo
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {reconciliation.monthly.map((month, idx) => (
                          <tr key={idx}>
                            <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                              {monthNames[month.month - 1]}/2025
                            </td>
                            {['revenue', 'expense', 'cost', 'balance'].map((key) => {
                              const data = month[key as keyof typeof month];
                              if (!data) return <td key={key} className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">-</td>;
                              
                              // Verificar se data é um objeto com excel, system, diff
                              if (typeof data === 'number' || !('excel' in data)) {
                                return <td key={key} className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">-</td>;
                              }
                              
                              return (
                                <td key={key} className="px-4 py-3 whitespace-nowrap">
                                  <div className="text-sm">
                                    <div className="flex items-center justify-between">
                                      <span className="text-gray-600">Plan:</span>
                                      <span className="font-medium">{formatCurrency(data.excel)}</span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                      <span className="text-gray-600">Sist:</span>
                                      <span className="font-medium">{formatCurrency(data.system)}</span>
                                    </div>
                                    <div className="flex items-center justify-between pt-1 border-t border-gray-100">
                                      <span className="text-xs text-gray-500">Diff:</span>
                                      <div className="flex items-center gap-1">
                                        {getDiffIcon(data.diff)}
                                        <span className={`text-xs font-medium ${getDiffColor(data.diff)}`}>
                                          {formatCurrency(data.diff)}
                                        </span>
                                      </div>
                                    </div>
                                  </div>
                                </td>
                              );
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card.Body>
              </Card>
            )}
            
            {/* Resumo */}
            <Card>
              <Card.Body>
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 mb-2">Status da Conciliação</h3>
                    {reconciliation.totals && (
                      <p className="text-sm text-gray-600">
                        {Object.values(reconciliation.totals).every(t => Math.abs(t.diff) < 0.01) ? (
                          <span className="text-green-600 font-medium">✅ 100% Conciliação - Todos os valores estão corretos</span>
                        ) : (
                          <span className="text-orange-600 font-medium">⚠️ Há diferenças que precisam ser corrigidas</span>
                        )}
                      </p>
                    )}
                  </div>
                  <Button onClick={() => router.push('/admin/companies')} variant="secondary">
                    Voltar para Empresas
                  </Button>
                </div>
              </Card.Body>
            </Card>
          </div>
        ) : (
          <Card>
            <Card.Body>
              <div className="text-center py-12">
                <AlertTriangle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">Nenhum dado de conciliação disponível</p>
              </div>
            </Card.Body>
          </Card>
        )}
      </div>
    </Layout>
  );
};

export default ReconciliationPage;


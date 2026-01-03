import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../../context/AuthContext';
import Layout from '../../components/layout/Layout';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import { Upload, CheckCircle, XCircle, Loader, FileSpreadsheet, AlertCircle } from 'lucide-react';
import { getApiInstance } from '../../services/api';

interface OnboardingProps {
  tenantId?: string;
  businessUnitId?: string;
}

const OnboardingPage: React.FC<OnboardingProps> = () => {
  const { user, token } = useAuth();
  const router = useRouter();
  const { tenant_id, business_unit_id } = router.query;
  
  const [spreadsheetUrl, setSpreadsheetUrl] = useState('');
  const [validating, setValidating] = useState(false);
  const [importing, setImporting] = useState(false);
  const [validationResult, setValidationResult] = useState<any>(null);
  const [onboardingStatus, setOnboardingStatus] = useState<any>(null);
  const [error, setError] = useState('');
  const [step, setStep] = useState<'url' | 'validating' | 'importing' | 'reconciling' | 'completed'>('url');
  
  const api = getApiInstance();
  
  useEffect(() => {
    if (tenant_id && business_unit_id && importing) {
      // Polling do status do onboarding
      const interval = setInterval(async () => {
        try {
          const response = await api.get(`/api/v1/onboarding/status/${tenant_id}/${business_unit_id}`);
          const status = response.data;
          setOnboardingStatus(status);
          
          if (status.status === 'completed') {
            setStep('completed');
            setImporting(false);
            clearInterval(interval);
          } else if (status.status === 'error') {
            setError(status.message || 'Erro durante onboarding');
            setImporting(false);
            clearInterval(interval);
          } else if (status.status === 'reconciling') {
            setStep('reconciling');
          }
        } catch (err: any) {
          console.error('Erro ao buscar status:', err);
        }
      }, 2000);
      
      return () => clearInterval(interval);
    }
  }, [tenant_id, business_unit_id, importing]);
  
  const handleValidate = async () => {
    if (!spreadsheetUrl.trim()) {
      setError('Por favor, informe a URL da planilha');
      return;
    }
    
    if (!tenant_id || !business_unit_id) {
      setError('Tenant ID e Business Unit ID são obrigatórios');
      return;
    }
    
    setValidating(true);
    setError('');
    setValidationResult(null);
    
    try {
      const response = await api.post('/api/v1/onboarding/validate-spreadsheet', {
        url: spreadsheetUrl,
        tenant_id: tenant_id,
        business_unit_id: business_unit_id
      });
      
      setValidationResult(response.data);
      
      if (response.data.valid) {
        setStep('validating');
      } else {
        setError(response.data.error || 'Planilha inválida');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Erro ao validar planilha');
      setValidationResult(null);
    } finally {
      setValidating(false);
    }
  };
  
  const handleImport = async () => {
    if (!tenant_id || !business_unit_id) {
      setError('Tenant ID e Business Unit ID são obrigatórios');
      return;
    }
    
    setImporting(true);
    setError('');
    setStep('importing');
    
    try {
      const response = await api.post('/api/v1/onboarding/import', {
        tenant_id: tenant_id,
        business_unit_id: business_unit_id,
        spreadsheet_url: spreadsheetUrl,
        reset_data: false
      });
      
      if (response.data.success) {
        // Status será atualizado via polling
      } else {
        setError('Erro ao iniciar importação');
        setImporting(false);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Erro ao iniciar importação');
      setImporting(false);
    }
  };
  
  const handleViewReconciliation = async () => {
    if (!tenant_id || !business_unit_id) return;
    
    router.push(`/admin/reconciliation?tenant_id=${tenant_id}&business_unit_id=${business_unit_id}`);
  };
  
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
    <Layout title="Onboarding de Empresa">
      <div className="max-w-4xl mx-auto py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">🚀 Onboarding de Empresa</h1>
          <p className="text-gray-600">Importe dados financeiros da planilha Excel/Google Sheets</p>
        </div>
        
        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {['URL', 'Validação', 'Importação', 'Conciliação', 'Concluído'].map((stepName, index) => {
              const stepIndex = ['url', 'validating', 'importing', 'reconciling', 'completed'].indexOf(step);
              const isActive = index <= stepIndex;
              const isCurrent = index === stepIndex;
              
              return (
                <div key={index} className="flex items-center flex-1">
                  <div className={`flex items-center justify-center w-10 h-10 rounded-full ${
                    isActive ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
                  }`}>
                    {isActive && !isCurrent ? (
                      <CheckCircle className="w-6 h-6" />
                    ) : (
                      <span>{index + 1}</span>
                    )}
                  </div>
                  <div className="ml-2">
                    <p className={`text-sm font-medium ${isActive ? 'text-blue-600' : 'text-gray-500'}`}>
                      {stepName}
                    </p>
                  </div>
                  {index < 4 && (
                    <div className={`flex-1 h-1 mx-4 ${isActive ? 'bg-blue-600' : 'bg-gray-200'}`} />
                  )}
                </div>
              );
            })}
          </div>
        </div>
        
        {/* Error Message */}
        {error && (
          <Card className="mb-6 border-red-200 bg-red-50">
            <Card.Body>
              <div className="flex items-center">
                <XCircle className="w-5 h-5 text-red-600 mr-2" />
                <p className="text-red-600">{error}</p>
              </div>
            </Card.Body>
          </Card>
        )}
        
        {/* Step 1: URL Input */}
        {step === 'url' && (
          <Card>
            <Card.Body>
              <div className="space-y-6">
                <div>
                  <h2 className="text-xl font-bold text-gray-900 mb-4">1. Informe a URL da Planilha</h2>
                  <p className="text-gray-600 mb-4">
                    Cole a URL da planilha Excel ou Google Sheets que contém os dados financeiros.
                  </p>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        URL da Planilha
                      </label>
                      <Input
                        type="url"
                        value={spreadsheetUrl}
                        onChange={(e) => setSpreadsheetUrl(e.target.value)}
                        placeholder="https://docs.google.com/spreadsheets/d/..."
                        className="w-full"
                      />
                      <p className="mt-2 text-sm text-gray-500">
                        Suporta Google Sheets (compartilhado publicamente) ou arquivo Excel hospedado
                      </p>
                    </div>
                    
                    <Button
                      onClick={handleValidate}
                      disabled={validating || !spreadsheetUrl.trim()}
                      className="w-full"
                    >
                      {validating ? (
                        <>
                          <Loader className="w-5 h-5 mr-2 animate-spin" />
                          Validando...
                        </>
                      ) : (
                        <>
                          <FileSpreadsheet className="w-5 h-5 mr-2" />
                          Validar Planilha
                        </>
                      )}
                    </Button>
                  </div>
                </div>
                
                {validationResult && (
                  <div className={`p-4 rounded-lg ${
                    validationResult.valid ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
                  }`}>
                    <div className="flex items-start">
                      {validationResult.valid ? (
                        <CheckCircle className="w-5 h-5 text-green-600 mr-2 mt-0.5" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-600 mr-2 mt-0.5" />
                      )}
                      <div>
                        <p className={`font-medium ${validationResult.valid ? 'text-green-800' : 'text-red-800'}`}>
                          {validationResult.valid ? 'Planilha válida!' : 'Planilha inválida'}
                        </p>
                        {validationResult.message && (
                          <p className={`text-sm mt-1 ${validationResult.valid ? 'text-green-700' : 'text-red-700'}`}>
                            {validationResult.message}
                          </p>
                        )}
                        {validationResult.available_sheets && (
                          <div className="mt-2">
                            <p className="text-sm font-medium">Abas encontradas:</p>
                            <ul className="text-sm list-disc list-inside">
                              {validationResult.available_sheets.map((sheet: string) => (
                                <li key={sheet}>{sheet}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </Card.Body>
          </Card>
        )}
        
        {/* Step 2: Importing */}
        {(step === 'importing' || step === 'reconciling') && onboardingStatus && (
          <Card>
            <Card.Body>
              <div className="space-y-6">
                <div>
                  <h2 className="text-xl font-bold text-gray-900 mb-4">
                    {step === 'importing' ? '2. Importando Dados' : '3. Conciliação'}
                  </h2>
                  
                  <div className="space-y-4">
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700">
                          {onboardingStatus.current_step || 'Processando...'}
                        </span>
                        <span className="text-sm font-medium text-gray-700">
                          {onboardingStatus.progress}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${onboardingStatus.progress}%` }}
                        />
                      </div>
                    </div>
                    
                    {onboardingStatus.message && (
                      <p className="text-sm text-gray-600">{onboardingStatus.message}</p>
                    )}
                    
                    {onboardingStatus.errors && onboardingStatus.errors.length > 0 && (
                      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-sm font-medium text-red-800 mb-2">Erros encontrados:</p>
                        <ul className="text-sm text-red-700 list-disc list-inside">
                          {onboardingStatus.errors.map((err: string, idx: number) => (
                            <li key={idx}>{err}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {onboardingStatus.stats && (
                      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <p className="text-sm font-medium text-blue-800 mb-2">Estatísticas:</p>
                        <ul className="text-sm text-blue-700 space-y-1">
                          {Object.entries(onboardingStatus.stats).map(([key, value]) => (
                            <li key={key}>
                              <span className="font-medium">{key}:</span> {String(value)}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </Card.Body>
          </Card>
        )}
        
        {/* Step 3: Completed */}
        {step === 'completed' && (
          <Card>
            <Card.Body>
              <div className="text-center space-y-6">
                <CheckCircle className="w-16 h-16 text-green-600 mx-auto" />
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">Onboarding Concluído!</h2>
                  <p className="text-gray-600">
                    Os dados foram importados com sucesso. Verifique a conciliação abaixo.
                  </p>
                </div>
                
                <div className="flex gap-4 justify-center">
                  <Button onClick={handleViewReconciliation} variant="primary">
                    Ver Conciliação
                  </Button>
                  <Button onClick={() => router.push('/admin/companies')} variant="secondary">
                    Voltar para Empresas
                  </Button>
                </div>
              </div>
            </Card.Body>
          </Card>
        )}
        
        {/* Action Buttons */}
        {validationResult?.valid && step === 'validating' && (
          <div className="mt-6">
            <Button
              onClick={handleImport}
              disabled={importing}
              className="w-full"
              variant="primary"
            >
              {importing ? (
                <>
                  <Loader className="w-5 h-5 mr-2 animate-spin" />
                  Importando...
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5 mr-2" />
                  Carregar Dados
                </>
              )}
            </Button>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default OnboardingPage;


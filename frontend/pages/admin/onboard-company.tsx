import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../../context/AuthContext';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://finaflow-api.72.61.34.133.sslip.io';

const OnboardSimplePage: React.FC = () => {
  const { user, token, logout } = useAuth();
  const router = useRouter();
  
  const [tenantName, setTenantName] = useState('');
  const [tenantCnpj, setTenantCnpj] = useState('');
  const [businessUnitName, setBusinessUnitName] = useState('Matriz');
  const [businessUnitCode, setBusinessUnitCode] = useState('MAT');
  const [spreadsheetUrl, setSpreadsheetUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [onboardingStatus, setOnboardingStatus] = useState<any>(null);
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<any>(null);
  const [issueEdits, setIssueEdits] = useState<Record<string, any>>({});
  const [ignoredIssues, setIgnoredIssues] = useState<Record<string, boolean>>({});
  const [confirmCorrections, setConfirmCorrections] = useState(false);
  const [correctionNote, setCorrectionNote] = useState('');
  const [validationError, setValidationError] = useState('');
  const [validatedUrl, setValidatedUrl] = useState('');
  const isSuperAdmin = user?.role === 'super_admin';
  const hasAuth = Boolean(token);

  const runValidation = async () => {
    if (!spreadsheetUrl.trim()) {
      setValidationError('Informe a URL da planilha');
      return null;
    }
    setValidating(true);
    setValidationError('');
    setValidationResult(null);
    setIssueEdits({});
    setIgnoredIssues({});
    setConfirmCorrections(false);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/onboarding/validate-spreadsheet`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          url: spreadsheetUrl
        })
      });
      const data = await response.json();
      setValidationResult(data);
      setValidatedUrl(spreadsheetUrl);
      if (!data.valid) {
        setValidationError(data.error || 'Planilha inválida. Corrija as inconsistências.');
      }
      return data;
    } catch (error: any) {
      setValidationError(error.message || 'Erro ao validar planilha');
      return null;
    } finally {
      setValidating(false);
    }
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!hasAuth) {
      logout();
      router.push('/login');
      return;
    }
    const hasManualEdits = Object.keys(issueEdits).length > 0 || Object.keys(ignoredIssues).length > 0;
    const shouldRevalidate = !validationResult || (!hasManualEdits && spreadsheetUrl !== validatedUrl);
    const validation = shouldRevalidate ? (await runValidation()) : validationResult;
    if (!validation) {
      return;
    }
    if (!validation.valid && !confirmCorrections) {
      setValidationError('Confirme as correções manuais para continuar.');
      setLoading(false);
      return;
    }
    setLoading(true);
    setResult(null);
    setOnboardingStatus(null);
    
    try {
      const rowUpdates = Object.values(issueEdits)
        .filter((entry: any) => entry?.fields && Object.keys(entry.fields).length > 0)
        .map((entry: any) => ({
          sheet: entry.sheet,
          row: entry.row,
          fields: entry.fields
        }));
      const ignoreIssueIds = Object.entries(ignoredIssues)
        .filter(([, value]) => value)
        .map(([key]) => key);
      const correctionsPayload = rowUpdates.length || ignoreIssueIds.length
        ? {
            confirm: confirmCorrections,
            note: correctionNote,
            ignore_issue_ids: ignoreIssueIds,
            row_updates: rowUpdates
          }
        : null;

      const response = await fetch(`${API_BASE_URL}/api/v1/onboarding/start`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          tenant_name: tenantName,
          tenant_cnpj: tenantCnpj,
          business_unit_name: businessUnitName,
          business_unit_code: businessUnitCode || undefined,
          spreadsheet_url: spreadsheetUrl,
          reset_data: false,
          corrections: correctionsPayload
        })
      });

      const data = await response.json();
      setResult(data);
      
    } catch (error: any) {
      console.error('Erro:', error);
      setResult({ success: false, error: error.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!result?.success || !result.tenant_id || !result.business_unit_id) {
      return;
    }

    let cancelled = false;
    const interval = setInterval(async () => {
      try {
        const statusResponse = await fetch(
          `${API_BASE_URL}/api/v1/onboarding/status/${result.tenant_id}/${result.business_unit_id}`,
          {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          }
        );
        const statusData = await statusResponse.json();
        if (!cancelled) {
          setOnboardingStatus(statusData);
        }
        if (statusData?.status === 'completed' || statusData?.status === 'error') {
          clearInterval(interval);
        }
      } catch (error: any) {
        if (!cancelled) {
          console.error('Erro ao buscar status:', error);
        }
      }
    }, 3000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [result?.success, result?.tenant_id, result?.business_unit_id, token]);

  useEffect(() => {
    if (onboardingStatus?.status === 'completed') {
      const timer = setTimeout(() => {
        logout();
        router.push('/login');
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [onboardingStatus?.status, logout, router]);

  useEffect(() => {
    const fromLogin = router.query.from === 'login';
    if (!fromLogin) {
      return;
    }
    router.beforePopState(() => {
      router.replace('/login');
      return false;
    });
    return () => {
      router.beforePopState(() => true);
    };
  }, [router]);

  useEffect(() => {
    if (!hasAuth) {
      logout();
      router.push('/login');
    }
  }, [hasAuth, logout, router]);

  if (!isSuperAdmin) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow p-8 max-w-md w-full">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Acesso Negado</h2>
          <p className="text-gray-600 mb-6">Apenas super administradores podem acessar esta página.</p>
          <button
            onClick={() => router.push('/dashboard')}
            className="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Voltar ao Dashboard
          </button>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gray-100 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            🏢 Ativar Nova Empresa
          </h1>
          <p className="text-gray-600 mb-8">
            Processo completo de onboarding para SaaS
          </p>
          
          {!result ? (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Nome da Empresa *
                </label>
                <input
                  type="text"
                  value={tenantName}
                  onChange={(e) => setTenantName(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Ex: Acme Corporation"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  CNPJ *
                </label>
                <input
                  type="text"
                  value={tenantCnpj}
                  onChange={(e) => setTenantCnpj(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Ex: 12.345.678/0001-99"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Business Unit (BU) *
                </label>
                <input
                  type="text"
                  value={businessUnitName}
                  onChange={(e) => setBusinessUnitName(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Ex: Matriz, Filial SP"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Código da BU
                </label>
                <input
                  type="text"
                  value={businessUnitCode}
                  onChange={(e) => setBusinessUnitCode(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Ex: MAT, SP01"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  URL da Planilha Google Sheets *
                </label>
                <input
                  type="text"
                  value={spreadsheetUrl}
                  onChange={(e) => setSpreadsheetUrl(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                  placeholder="https://docs.google.com/spreadsheets/d/..."
                  required
                />
                <p className="mt-1 text-xs text-gray-500">
                  A planilha precisa estar compartilhada para leitura
                </p>
              </div>

              {validationError && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
                  {validationError}
                </div>
              )}

              {validationResult && (
                <div className={`p-4 rounded-lg ${
                  validationResult.valid ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
                }`}>
                  <div className="text-sm font-medium mb-2">
                    {validationResult.valid ? 'Planilha válida!' : 'Planilha inválida'}
                  </div>
                  {validationResult.summary && (
                    <div className="text-xs text-gray-700 mb-2">
                      Erros: {validationResult.summary.errors || 0} | Avisos: {validationResult.summary.warnings || 0}
                    </div>
                  )}
                  {validationResult.issues && validationResult.issues.length > 0 && (
                    <div className="max-h-64 overflow-auto border border-gray-200 rounded-lg bg-white">
                      <table className="w-full text-sm">
                        <thead className="bg-gray-50 sticky top-0">
                          <tr>
                            <th className="text-left p-2">Severidade</th>
                            <th className="text-left p-2">Aba</th>
                            <th className="text-left p-2">Linha</th>
                            <th className="text-left p-2">Detalhe</th>
                            <th className="text-left p-2">Correção</th>
                            <th className="text-left p-2">Ignorar</th>
                          </tr>
                        </thead>
                        <tbody>
                          {validationResult.issues.map((issue: any, idx: number) => {
                            const issueId = issue.id || `${issue.code}:${issue.sheet || 'sheet'}:${issue.row || 'na'}:${idx}`;
                            const editableFieldsMap: Record<string, string[]> = {
                              DIARIO_DATA_MISSING: ['data'],
                              DIARIO_VALOR_MISSING: ['valor'],
                              DIARIO_GRUPO_SUBGRUPO_MISSING: ['grupo', 'subgrupo'],
                              PREVISTO_DATA_MISSING: ['data'],
                              PREVISTO_VALOR_MISSING: ['valor'],
                              PREVISTO_CONTA_MISSING: ['conta'],
                              PREVISTO_GRUPO_SUBGRUPO_MISSING: ['grupo', 'subgrupo'],
                              PREVISTO_CONTA_FORA_PLANO: ['conta']
                            };
                            const editableFields = editableFieldsMap[issue.code] || [];
                            const currentEntry = issueEdits[issueId] || { sheet: issue.sheet, row: issue.row, fields: {} };

                            return (
                              <tr key={issueId} className="border-t">
                                <td className="p-2">
                                  <span className={`px-2 py-1 rounded text-xs ${
                                    issue.severity === 'error' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'
                                  }`}>
                                    {issue.severity === 'error' ? 'Erro' : 'Aviso'}
                                  </span>
                                </td>
                                <td className="p-2">{issue.sheet || '-'}</td>
                                <td className="p-2">{issue.row || '-'}</td>
                                <td className="p-2">{issue.message}</td>
                                <td className="p-2">
                                  {editableFields.length > 0 ? (
                                    <div className="flex flex-col gap-2 min-w-[180px]">
                                      {editableFields.map((field) => (
                                        <input
                                          key={`${issueId}-${field}`}
                                          value={currentEntry.fields?.[field] || ''}
                                          onChange={(e) => {
                                            setIssueEdits((prev) => ({
                                              ...prev,
                                              [issueId]: {
                                                sheet: issue.sheet,
                                                row: issue.row,
                                                fields: {
                                                  ...(prev[issueId]?.fields || {}),
                                                  [field]: e.target.value
                                                }
                                              }
                                            }));
                                          }}
                                          className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                                          placeholder={`Corrigir ${field}`}
                                        />
                                      ))}
                                    </div>
                                  ) : (
                                    <span className="text-xs text-gray-500">-</span>
                                  )}
                                </td>
                                <td className="p-2">
                                  <input
                                    type="checkbox"
                                    checked={!!ignoredIssues[issueId]}
                                    onChange={(e) =>
                                      setIgnoredIssues((prev) => ({
                                        ...prev,
                                        [issueId]: e.target.checked
                                      }))
                                    }
                                  />
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  )}
                  {!validationResult.valid && (
                    <div className="mt-3 space-y-2">
                      <textarea
                        className="w-full rounded-md border border-gray-300 p-2 text-sm"
                        rows={3}
                        value={correctionNote}
                        onChange={(e) => setCorrectionNote(e.target.value)}
                        placeholder="Justificativa (opcional)"
                      />
                      <label className="flex items-center gap-2 text-sm text-gray-700">
                        <input
                          type="checkbox"
                          checked={confirmCorrections}
                          onChange={(e) => setConfirmCorrections(e.target.checked)}
                        />
                        Confirmo que as correções são necessárias e serão auditadas.
                      </label>
                    </div>
                  )}
                </div>
              )}
              
              <button
                type="submit"
                disabled={!tenantName || !tenantCnpj || !businessUnitName || !spreadsheetUrl || loading || validating}
                className="w-full bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
              >
                {validating ? 'Validando planilha...' : (loading ? 'Iniciando onboarding...' : 'Iniciar Onboarding')}
              </button>
            </form>
          ) : (
            <div>
              {result.success ? (
                <div className="space-y-6">
                  <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                    <h2 className="text-xl font-bold text-green-900 mb-4">
                      ✅ Onboarding iniciado com sucesso!
                    </h2>
                    <p className="text-sm text-gray-700">
                      A importação está em andamento. Acompanhe o progresso abaixo.
                    </p>
                  </div>

                  {onboardingStatus && (
                    <div className="bg-white border border-gray-200 rounded-lg p-6">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700">
                          {onboardingStatus.current_step || 'Processando...'}
                        </span>
                        <span className="text-sm font-medium text-gray-700">
                          {onboardingStatus.progress || 0}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${onboardingStatus.progress || 0}%` }}
                        />
                      </div>

                      {onboardingStatus.message && (
                        <p className="text-sm text-gray-600 mt-2">{onboardingStatus.message}</p>
                      )}

                      {onboardingStatus.errors?.length > 0 && (
                        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                          {onboardingStatus.errors.map((err: string, index: number) => (
                            <div key={index}>{err}</div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Sem ações quando sucesso: logout automático no fim */}
                </div>
              ) : (
                <div>
                  <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-4">
                    <h2 className="text-xl font-bold text-red-900 mb-2">❌ Erro na Ativação</h2>
                    <p className="text-red-700">{result.error || 'Erro desconhecido'}</p>
                  </div>
                  
                  <button
                    onClick={() => setResult(null)}
                    className="w-full bg-gray-600 text-white px-6 py-3 rounded-lg hover:bg-gray-700"
                  >
                    Tentar Novamente
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default OnboardSimplePage;

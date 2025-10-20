import React, { useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../../context/AuthContext';

const OnboardSimplePage: React.FC = () => {
  const { user, token } = useAuth();
  const router = useRouter();
  
  const [tenantName, setTenantName] = useState('');
  const [tenantDomain, setTenantDomain] = useState('');
  const [adminEmail, setAdminEmail] = useState('');
  const [spreadsheetId, setSpreadsheetId] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  
  if (user?.role !== 'super_admin') {
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
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/admin/onboard-new-company`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            tenant_name: tenantName,
            tenant_domain: tenantDomain,
            admin_email: adminEmail,
            bu_name: 'Matriz',
            bu_code: 'MAT',
            spreadsheet_id: spreadsheetId,
            import_data: true
          })
        }
      );
      
      const data = await response.json();
      setResult(data);
      
    } catch (error: any) {
      console.error('Erro:', error);
      setResult({ success: false, error: error.message });
    } finally {
      setLoading(false);
    }
  };
  
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
                  Domínio *
                </label>
                <input
                  type="text"
                  value={tenantDomain}
                  onChange={(e) => setTenantDomain(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Ex: acme.com"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email do Administrador *
                </label>
                <input
                  type="email"
                  value={adminEmail}
                  onChange={(e) => setAdminEmail(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Ex: admin@acme.com"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  ID da Planilha Google Sheets *
                </label>
                <input
                  type="text"
                  value={spreadsheetId}
                  onChange={(e) => setSpreadsheetId(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                  placeholder="Ex: 1rWMdDhwiNoC7iMycmQGWWDIacrePr1gB7c_mbt1patQ"
                  required
                />
                <p className="mt-1 text-xs text-gray-500">
                  ID encontrado na URL da planilha: docs.google.com/spreadsheets/d/[ID]/edit
                </p>
              </div>
              
              <button
                type="submit"
                disabled={loading || !tenantName || !tenantDomain || !adminEmail || !spreadsheetId}
                className="w-full bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
              >
                {loading ? 'Criando empresa e importando dados...' : 'Ativar Empresa'}
              </button>
            </form>
          ) : (
            <div>
              {result.success ? (
                <div className="space-y-6">
                  <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                    <h2 className="text-xl font-bold text-green-900 mb-4">
                      ✅ Empresa Ativada com Sucesso!
                    </h2>
                    
                    {result.steps && (
                      <div className="mb-4">
                        {result.steps.map((step: string, index: number) => (
                          <div key={index} className="text-sm text-gray-700 mb-1">
                            {step}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  
                  {result.company_info && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                      <h3 className="font-bold text-blue-900 mb-4">🔑 Credenciais de Acesso</h3>
                      
                      <div className="space-y-3 bg-white p-4 rounded">
                        <div>
                          <span className="text-sm font-medium text-gray-600">Empresa:</span>
                          <p className="font-bold">{result.company_info.tenant_name}</p>
                        </div>
                        
                        <div>
                          <span className="text-sm font-medium text-gray-600">Username:</span>
                          <p className="font-mono bg-gray-100 px-2 py-1 rounded inline-block">
                            {result.company_info.admin_username}
                          </p>
                        </div>
                        
                        <div>
                          <span className="text-sm font-medium text-gray-600">Senha Temporária:</span>
                          <p className="font-mono bg-yellow-100 px-2 py-1 rounded inline-block font-bold">
                            {result.company_info.admin_password}
                          </p>
                        </div>
                        
                        <div>
                          <span className="text-sm font-medium text-gray-600">Email:</span>
                          <p>{result.company_info.admin_email}</p>
                        </div>
                        
                        <div>
                          <span className="text-sm font-medium text-gray-600">URL:</span>
                          <a href={result.company_info.login_url} className="text-blue-600 underline">
                            {result.company_info.login_url}
                          </a>
                        </div>
                      </div>
                      
                      <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded text-sm">
                        ⚠️ <strong>IMPORTANTE:</strong> Salve essas credenciais e envie para o cliente.
                      </div>
                    </div>
                  )}
                  
                  <div className="flex space-x-4">
                    <button
                      onClick={() => setResult(null)}
                      className="flex-1 bg-gray-200 text-gray-800 px-6 py-3 rounded-lg hover:bg-gray-300"
                    >
                      Ativar Outra Empresa
                    </button>
                    
                    <button
                      onClick={() => router.push('/admin/companies')}
                      className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
                    >
                      Ver Todas as Empresas
                    </button>
                  </div>
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


import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../../context/AuthContext';
import Layout from '../../components/layout/Layout';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import { Building2, Users, MapPin, Plus } from 'lucide-react';
import { getTenants, getBusinessUnits } from '../../services/api';

interface Tenant {
  id: string;
  name: string;
  domain: string;
  status: string;
  created_at: string;
}

interface BusinessUnit {
  id: string;
  tenant_id: string;
  name: string;
  code: string;
  status: string;
}

const CompaniesPage: React.FC = () => {
  const { user, token } = useAuth();
  const router = useRouter();
  
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [businessUnits, setBusinessUnits] = useState<BusinessUnit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Verificar se é super_admin
  if (user?.role !== 'super_admin') {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto py-8">
          <Card>
            <Card.Body>
              <div className="text-center py-12">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">
                  Acesso Negado
                </h2>
                <p className="text-gray-600 mb-6">
                  Apenas super administradores podem acessar esta página.
                </p>
                <Button onClick={() => router.push('/dashboard')}>
                  Voltar ao Dashboard
                </Button>
              </div>
            </Card.Body>
          </Card>
        </div>
      </Layout>
    );
  }
  
  useEffect(() => {
    loadData();
  }, []);
  
  const loadData = async () => {
    setLoading(true);
    setError('');
    
    try {
      const [tenantsData, busData] = await Promise.all([
        getTenants(token || undefined),
        getBusinessUnits(undefined, token || undefined)
      ]);
      
      setTenants(tenantsData);
      setBusinessUnits(busData);
    } catch (err: any) {
      console.error('Erro ao carregar dados:', err);
      setError(err.message || 'Erro ao carregar empresas');
    } finally {
      setLoading(false);
    }
  };
  
  const getBUsForTenant = (tenantId: string) => {
    return businessUnits.filter(bu => bu.tenant_id === tenantId);
  };
  
  return (
    <Layout title="Gerenciar Empresas">
      <div className="max-w-7xl mx-auto py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              🏢 Empresas do Sistema
            </h1>
            <p className="text-gray-600">
              Gerencie todas as empresas e suas filiais
            </p>
          </div>
          
          <Button
            onClick={() => router.push('/admin/onboard-company')}
            variant="primary"
            size="lg"
          >
            <Plus className="w-5 h-5 mr-2" />
            Ativar Nova Empresa
          </Button>
        </div>
        
        {/* Estatísticas */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card>
            <Card.Body>
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Building2 className="w-8 h-8 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Empresas</p>
                  <p className="text-2xl font-bold text-gray-900">{tenants.length}</p>
                </div>
              </div>
            </Card.Body>
          </Card>
          
          <Card>
            <Card.Body>
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <MapPin className="w-8 h-8 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Filiais</p>
                  <p className="text-2xl font-bold text-gray-900">{businessUnits.length}</p>
                </div>
              </div>
            </Card.Body>
          </Card>
          
          <Card>
            <Card.Body>
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Users className="w-8 h-8 text-purple-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Média Filiais/Empresa</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {tenants.length > 0 ? (businessUnits.length / tenants.length).toFixed(1) : 0}
                  </p>
                </div>
              </div>
            </Card.Body>
          </Card>
        </div>
        
        {/* Lista de Empresas */}
        {loading ? (
          <Card>
            <Card.Body>
              <div className="text-center py-12">
                <p className="text-gray-600">Carregando empresas...</p>
              </div>
            </Card.Body>
          </Card>
        ) : error ? (
          <Card>
            <Card.Body>
              <div className="text-center py-12">
                <p className="text-red-600">{error}</p>
                <Button onClick={loadData} className="mt-4">
                  Tentar Novamente
                </Button>
              </div>
            </Card.Body>
          </Card>
        ) : tenants.length === 0 ? (
          <Card>
            <Card.Body>
              <div className="text-center py-12">
                <Building2 className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Nenhuma empresa cadastrada
                </h3>
                <p className="text-gray-600 mb-6">
                  Comece ativando sua primeira empresa
                </p>
                <Button onClick={() => router.push('/admin/onboard-company')}>
                  <Plus className="w-5 h-5 mr-2" />
                  Ativar Primeira Empresa
                </Button>
              </div>
            </Card.Body>
          </Card>
        ) : (
          <div className="space-y-6">
            {tenants.map((tenant) => {
              const tenantBUs = getBUsForTenant(tenant.id);
              
              return (
                <Card key={tenant.id}>
                  <Card.Body>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center mb-2">
                          <Building2 className="w-6 h-6 text-blue-600 mr-3" />
                          <div>
                            <h3 className="text-xl font-bold text-gray-900">
                              {tenant.name}
                            </h3>
                            <p className="text-sm text-gray-500">
                              {tenant.domain}
                            </p>
                          </div>
                          
                          <span className={`ml-4 px-3 py-1 text-xs font-medium rounded-full ${
                            tenant.status === 'active' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-gray-100 text-gray-800'
                          }`}>
                            {tenant.status === 'active' ? 'Ativo' : tenant.status}
                          </span>
                        </div>
                        
                        {/* Business Units */}
                        <div className="mt-4 ml-9">
                          <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                            <MapPin className="w-4 h-4 mr-1" />
                            Filiais ({tenantBUs.length})
                          </h4>
                          
                          {tenantBUs.length === 0 ? (
                            <p className="text-sm text-gray-500">Nenhuma filial cadastrada</p>
                          ) : (
                            <div className="flex flex-wrap gap-2">
                              {tenantBUs.map((bu) => (
                                <span
                                  key={bu.id}
                                  className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-full"
                                >
                                  {bu.name} ({bu.code})
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                        
                        {/* Metadados */}
                        <div className="mt-4 ml-9 text-xs text-gray-500">
                          Criado em: {new Date(tenant.created_at).toLocaleDateString('pt-BR')}
                        </div>
                      </div>
                      
                      {/* Ações */}
                      <div className="ml-4">
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => router.push(`/admin/companies/${tenant.id}`)}
                        >
                          Ver Detalhes
                        </Button>
                      </div>
                    </div>
                  </Card.Body>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </Layout>
  );
};

export default CompaniesPage;


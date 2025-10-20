'use client';
import React, { useState, useEffect, useContext } from 'react';
import Head from 'next/head';
import { motion } from 'framer-motion';
import { AuthContext } from '../context/AuthContext';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import { Building2, Users, Shield, ArrowRight, Check, LogOut, User } from 'lucide-react';
import { getUserBusinessUnits, selectBusinessUnit } from '../services/api';

interface BusinessUnit {
  id: string;
  name: string;
  code: string;
  tenant_id: string;
  tenant_name: string;
  permissions: {
    can_read: boolean;
    can_write: boolean;
    can_delete: boolean;
    can_manage_users: boolean;
  };
}

export default function SelectBusinessUnit() {
  const { login, logout } = useContext(AuthContext);
  const [businessUnits, setBusinessUnits] = useState<BusinessUnit[]>([]);
  const [selectedBU, setSelectedBU] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    // Verificar se tem token antes de carregar
    const token = localStorage.getItem('token');
    if (!token) {
      console.warn('⚠️ Token não encontrado, redirecionando para login...');
      window.location.href = '/login';
      return;
    }
    
    loadBusinessUnits();
  }, []);

  const loadBusinessUnits = async () => {
    try {
      setLoading(true);
      const data = await getUserBusinessUnits();
      setBusinessUnits(data);
      
      // Se só tem uma BU, selecionar automaticamente
      if (data.length === 1) {
        setSelectedBU(data[0].id);
      }
    } catch (error) {
      console.error('Erro ao carregar BUs:', error);
      setError('Erro ao carregar empresas disponíveis');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedBU) {
      setError('Selecione uma empresa para continuar');
      return;
    }

    try {
      setSubmitting(true);
      setError('');
      
      const response = await selectBusinessUnit(selectedBU);
      
      // Atualizar o token no localStorage
      localStorage.setItem('token', response.access_token);
      
      // Redirecionar para o dashboard
      window.location.href = '/dashboard';
    } catch (error) {
      console.error('Erro ao selecionar BU:', error);
      setError('Erro ao selecionar empresa. Tente novamente.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleLogout = () => {
    logout(); // Usar função do AuthContext
  };

  const getPermissionText = (permissions: BusinessUnit['permissions']) => {
    const permissionsList = [];
    if (permissions.can_read) permissionsList.push('Visualizar');
    if (permissions.can_write) permissionsList.push('Editar');
    if (permissions.can_delete) permissionsList.push('Excluir');
    if (permissions.can_manage_users) permissionsList.push('Gerenciar Usuários');
    
    return permissionsList.join(', ');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Carregando empresas disponíveis...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50 flex items-center justify-center p-4">
      <Head>
        <title>FinaFlow - Selecionar Empresa</title>
        <meta name="description" content="Selecione a empresa que deseja acessar no FinaFlow" />
      </Head>

      {/* Background Pattern */}
      <div 
        className="absolute inset-0 opacity-5" 
        style={{
          backgroundImage: 'radial-gradient(circle, #e5e7eb 1px, transparent 1px)',
          backgroundSize: '20px 20px'
        }}
      />

      <div className="w-full max-w-2xl relative z-10">
        {/* Header com logout */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="flex justify-between items-center mb-6"
        >
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-blue-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">admin</p>
              <p className="text-xs text-gray-500">Super Admin</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center space-x-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
            title="Fazer logout"
          >
            <LogOut className="w-4 h-4" />
            <span>Logout</span>
          </button>
        </motion.div>

        {/* Logo and Brand */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-center mb-8"
        >
          <img src="/logo-finaflow.svg" alt="finaFlow" className="h-12 mx-auto mb-3" />
          <h1 className="text-2xl font-semibold text-gray-900 mb-2">
            Selecione sua Empresa
          </h1>
          <p className="text-gray-600">
            Escolha a empresa que deseja acessar
          </p>
        </motion.div>

        {/* Business Units Selection */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          <Card className="backdrop-blur-sm bg-white/80 border-white/20 shadow-xl">
            <Card.Body className="p-8">
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Business Units List */}
                <div className="space-y-4">
                  {businessUnits.length > 0 ? (
                    businessUnits.map((bu) => (
                    <motion.div
                      key={bu.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.3 }}
                      className={`relative p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 ${
                        selectedBU === bu.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                      onClick={() => setSelectedBU(bu.id)}
                    >
                      {/* Selection Indicator */}
                      {selectedBU === bu.id && (
                        <div className="absolute top-4 right-4 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                          <Check className="w-4 h-4 text-white" />
                        </div>
                      )}

                      <div className="flex items-start space-x-4">
                        <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                          <Building2 className="w-6 h-6 text-blue-600" />
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-2">
                            <h3 className="text-lg font-semibold text-gray-900 truncate">
                              {bu.name}
                            </h3>
                            <span className="text-sm font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded">
                              {bu.code}
                            </span>
                          </div>
                          
                          <p className="text-sm text-gray-600 mb-2">
                            Empresa: {bu.tenant_name}
                          </p>
                          
                          <div className="flex items-center space-x-4 text-xs text-gray-500">
                            <div className="flex items-center space-x-1">
                              <Shield className="w-3 h-3" />
                              <span>Permissões: {getPermissionText(bu.permissions)}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                    ))
                  ) : (
                    <div className="text-center py-8">
                      <Building2 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">
                        Nenhuma empresa disponível
                      </h3>
                      <p className="text-gray-600 mb-4">
                        Você não tem acesso a nenhuma empresa no momento.
                      </p>
                      <div className="space-y-2">
                        <button
                          onClick={handleLogout}
                          className="inline-flex items-center space-x-2 px-4 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
                        >
                          <LogOut className="w-4 h-4" />
                          <span>Fazer Logout</span>
                        </button>
                        <p className="text-xs text-gray-500">
                          Entre em contato com o administrador para obter acesso.
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Error Message */}
                {error && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <p className="text-red-600 text-sm">{error}</p>
                  </div>
                )}

                {/* Submit Button */}
                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  fullWidth
                  loading={submitting}
                  disabled={!selectedBU}
                >
                  {submitting ? 'Entrando...' : (
                    <>
                      Continuar
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </>
                  )}
                </Button>
              </form>

              {/* Navigation Options */}
              <div className="mt-6 space-y-3">
                <div className="flex justify-center space-x-4">
                  <button
                    onClick={handleLogout}
                    className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Fazer Logout</span>
                  </button>
                <button
                  onClick={() => window.location.href = '/login'}
                    className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
                >
                    <span>← Trocar Usuário</span>
                </button>
                </div>
                
                {/* Help text */}
                <div className="text-center">
                  <p className="text-xs text-gray-500">
                    Problemas de acesso? Entre em contato com o administrador.
                  </p>
                </div>
              </div>
            </Card.Body>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}

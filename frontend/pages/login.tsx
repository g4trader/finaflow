'use client';
import React, { useState, useContext } from 'react';
import Head from 'next/head';
import { motion } from 'framer-motion';
import { AuthContext } from '../context/AuthContext';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Card from '../components/ui/Card';
import { Mail, Lock, Eye, EyeOff, TrendingUp } from 'lucide-react';
import jwtDecode from 'jwt-decode';

export default function Login() {
  const { login, needsBusinessUnitSelection } = useContext(AuthContext);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      console.log('🔐 Iniciando login...', { username });
      await login(username, password);
      console.log('✅ Login bem-sucedido!');
      
      // Verificar se precisa selecionar BU
      if (needsBusinessUnitSelection) {
        console.log('📋 Redirecionando para seleção de BU');
        window.location.href = '/select-business-unit';
      } else {
        console.log('📊 Redirecionando para dashboard');
        window.location.href = '/dashboard';
      }
    } catch (err: any) {
      console.error('❌ Erro no login:', err);
      const message = err?.response?.data?.detail || err?.message || 'Username ou senha incorretos. Tente novamente.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50 flex items-center justify-center p-4">
      <Head>
        <title>FinaFlow - Login</title>
        <meta name="description" content="Faça login no FinaFlow - Sistema de gestão financeira" />
      </Head>

      {/* Background Pattern */}
      <div 
        className="absolute inset-0 opacity-5" 
        style={{
          backgroundImage: 'radial-gradient(circle, #e5e7eb 1px, transparent 1px)',
          backgroundSize: '20px 20px'
        }}
      />

      <div className="w-full max-w-md relative z-10">
        {/* Logo and Brand */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-8"
        >
          <img src="/logo-finaflow.svg" alt="finaFlow" className="h-12 mx-auto mb-3" />
          <p className="text-gray-600">Gestão financeira inteligente</p>
        </motion.div>

        {/* Login Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          <Card className="backdrop-blur-sm bg-white/80 border-white/20 shadow-xl">
            <Card.Body className="p-8">
              <div className="text-center mb-6">
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                  Bem-vindo de volta
                </h2>
                <p className="text-gray-600">
                  Entre na sua conta para continuar
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Username ou Email */}
                <div className="relative">
                  <div className="pointer-events-none absolute inset-y-0 left-0 pl-3 flex items-center">
                    <Mail className="w-5 h-5 text-gray-400" />
                  </div>
                  <Input
                    type="text"
                    name="username"
                    label="Username ou Email"
                    placeholder="admin ou seu@email.com"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    fullWidth
                    required
                    className="pl-10"
                  />
                </div>

                {/* Senha */}
                <div className="relative">
                  <div className="pointer-events-none absolute inset-y-0 left-0 pl-3 flex items-center">
                    <Lock className="w-5 h-5 text-gray-400" />
                  </div>
                  <Input
                    type={showPassword ? 'text' : 'password'}
                    name="password"
                    label="Senha"
                    placeholder="Digite sua senha"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    fullWidth
                    required
                    error={error}
                    className="pl-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                    aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'}
                  >
                    {showPassword ? (
                      <EyeOff className="w-5 h-5" />
                    ) : (
                      <Eye className="w-5 h-5" />
                    )}
                  </button>
                </div>

                <div className="flex items-center justify-between">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-600">
                      Lembrar de mim
                    </span>
                  </label>
                  <a
                    href="/forgot-password"
                    className="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
                  >
                    Esqueci minha senha
                  </a>
                </div>

                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  fullWidth
                  loading={loading}
                >
                  {loading ? 'Entrando...' : 'Entrar'}
                </Button>
              </form>

              <div className="mt-6 text-center">
                <p className="text-gray-600">
                  Não tem uma conta?{' '}
                  <a
                    href="/signup"
                    className="text-blue-600 hover:text-blue-700 font-medium transition-colors"
                  >
                    Cadastre-se gratuitamente
                  </a>
                </p>
              </div>
            </Card.Body>
          </Card>
        </motion.div>

        {/* Features */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mt-8 text-center"
        >
          <div className="grid grid-cols-3 gap-4 text-sm text-gray-600">
            <div className="flex flex-col items-center">
              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mb-2">
                <TrendingUp className="w-4 h-4 text-blue-600" />
              </div>
              <span>Relatórios</span>
            </div>
            <div className="flex flex-col items-center">
              <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center mb-2">
                <Lock className="w-4 h-4 text-green-600" />
              </div>
              <span>Seguro</span>
            </div>
            <div className="flex flex-col items-center">
              <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center mb-2">
                <Mail className="w-4 h-4 text-purple-600" />
              </div>
              <span>Suporte 24/7</span>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

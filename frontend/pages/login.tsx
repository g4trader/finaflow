import React, { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Card from '../components/ui/Card';
import { Mail, Lock, Eye, EyeOff, TrendingUp } from 'lucide-react';

export default function Login() {
  const { login } = useContext(AuthContext);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await login(email, password);
      window.location.href = '/dashboard';
    } catch {
      setError('Email ou senha incorretos. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50 flex items-center justify-center p-4">
      {/* Background Pattern */}
      <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
      
      <div className="w-full max-w-md relative z-10">
        {/* Logo and Brand */}
        <div className="text-center mb-8 animate-fade-in">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-600 to-blue-700 rounded-2xl mb-4 shadow-lg">
            <TrendingUp className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">FinaFlow</h1>
          <p className="text-gray-600">Gestão financeira inteligente</p>
        </div>

        {/* Login Card */}
        <div className="animate-fade-in">
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
                <Input
                  type="email"
                  label="Email"
                  placeholder="seu@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  icon={<Mail className="w-5 h-5" />}
                  fullWidth
                  required
                />

                <div className="relative">
                  <Input
                    type={showPassword ? 'text' : 'password'}
                    label="Senha"
                    placeholder="Digite sua senha"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    icon={<Lock className="w-5 h-5" />}
                    fullWidth
                    required
                    error={error}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-9 text-gray-400 hover:text-gray-600 transition-colors"
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
        </div>

        {/* Features */}
        <div className="mt-8 text-center animate-fade-in">
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
        </div>
      </div>

      <style jsx>{`
        .bg-grid-pattern {
          background-image: radial-gradient(circle, #e5e7eb 1px, transparent 1px);
          background-size: 20px 20px;
        }
      `}</style>
    </div>
  );
}


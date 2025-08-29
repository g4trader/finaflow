'use client';
import React, { useEffect, useRef, useState, useContext } from 'react';
import Head from 'next/head';
import Script from 'next/script';
import Link from 'next/link';
import { useRouter } from 'next/router';
import axios from 'axios';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import { AuthContext } from '../context/AuthContext';

declare global {
  interface Window { google?: any }
}

// Garantir HTTPS
const getApiUrl = () => {
  const url = process.env.NEXT_PUBLIC_API_URL;
  if (!url) {
    return 'https://finaflow-backend-609095880025.us-central1.run.app';
  }
  // Forçar HTTPS se for HTTP
  if (url.startsWith('http://')) {
    return url.replace('http://', 'https://');
  }
  return url;
};

const API_URL = getApiUrl();

export default function Signup() {
  const { token, role, signup } = useContext(AuthContext);
  const router = useRouter();
  const googleBtn = useRef<HTMLDivElement>(null);
  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    confirm: '',
    company: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (form.password !== form.confirm) {
      setError('As senhas não conferem.');
      return;
    }
    try {
      setLoading(true);
      await signup({
        username: form.name,
        email: form.email,
        password: form.password,
        role: 'tenant_user',
        tenant_id: form.company,
      });
      window.location.href = '/login';
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Não foi possível criar sua conta.');
    } finally {
      setLoading(false);
    }
  };

  // Verificar autenticação apenas no lado do cliente
  useEffect(() => {
    if (isClient && (!token || role !== 'super_admin')) {
      router.replace('/login');
    }
  }, [isClient, token, role, router]);

  // Renderizar loading enquanto verifica autenticação
  if (!isClient || !token || role !== 'super_admin') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Carregando...</p>
        </div>
      </div>
    );
  }

  const initGoogle = () => {
    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
    if (!clientId || !window.google || !googleBtn.current) return;
    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: async (response: any) => {
        try {
          const r = await axios.post(`${API_URL}/auth/google`, { credential: response.credential });
          const token = r.data?.access_token || r.data?.token;
          if (token) {
            localStorage.setItem('token', token);
            window.location.href = '/dashboard';
          } else {
            setError('Falha ao autenticar com Google.');
          }
        } catch (e: any) {
          setError(e?.response?.data?.detail || 'Falha ao autenticar com Google.');
        }
      },
    });
    window.google.accounts.id.renderButton(googleBtn.current, {
      theme: 'outline',
      size: 'large',
      text: 'continue_with',
      shape: 'pill',
      width: 320,
      logo_alignment: 'left',
    });
  };

  useEffect(() => {
    if (window.google) initGoogle();
  }, []);

  return (
    <>
      <Head>
        <title>finaFlow — Criar conta</title>
        <meta name="description" content="Crie sua conta finaFlow e comece a gerenciar finanças com previsões e relatórios claros." />
      </Head>

      <Script src="https://accounts.google.com/gsi/client" strategy="afterInteractive" onLoad={initGoogle} />

      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50 flex items-center justify-center p-6">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <img src="/logo-finaflow.svg" alt="finaFlow" className="h-10 mx-auto mb-4" />
            <h1 className="text-2xl font-semibold text-gray-900">Comece grátis</h1>
            <p className="text-gray-600">Crie sua conta em menos de 1 minuto</p>
          </div>

          <div className="bg-white/80 backdrop-blur-sm border border-white/20 shadow-xl rounded-xl p-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                name="name"
                label="Seu nome"
                placeholder="Nome e sobrenome"
                value={form.name}
                onChange={onChange}
                required
                fullWidth
              />
              <Input
                type="email"
                name="email"
                label="Email"
                placeholder="voce@empresa.com"
                value={form.email}
                onChange={onChange}
                required
                fullWidth
              />
              <Input
                name="company"
                label="Empresa / Unidade"
                placeholder="Nome da sua empresa"
                value={form.company}
                onChange={onChange}
                fullWidth
              />
              <Input
                type="password"
                name="password"
                label="Senha"
                placeholder="Crie uma senha"
                value={form.password}
                onChange={onChange}
                required
                fullWidth
              />
              <Input
                type="password"
                name="confirm"
                label="Confirmar senha"
                placeholder="Repita a senha"
                value={form.confirm}
                onChange={onChange}
                required
                fullWidth
              />

              {error && <p className="text-sm text-red-600">{error}</p>}

              <Button type="submit" size="lg" fullWidth loading={loading}>
                Criar conta
              </Button>
            </form>

            <div className="flex items-center my-6">
              <div className="flex-1 h-px bg-gray-200" />
              <span className="px-3 text-xs text-gray-400">ou</span>
              <div className="flex-1 h-px bg-gray-200" />
            </div>

            {/* Google Sign-In */}
            <div className="flex justify-center">
              <div ref={googleBtn} />
            </div>

            <p className="mt-6 text-center text-sm text-gray-600">
              Já tem conta?{' '}
              <Link href="/login" className="text-blue-600 hover:text-blue-700 font-medium">
                Entrar
              </Link>
            </p>
            <p className="mt-2 text-center text-xs text-gray-400">
              Ao continuar você concorda com nossos <a href="#" className="underline">Termos</a> e <a href="#" className="underline">Privacidade</a>.
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
